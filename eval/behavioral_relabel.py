"""Full 100-prompt behavioral relabeling (for paper v0.5).
Relabels existing outputs' behavioral CLASS (CLARIFY/ANSWER/REFUSE/OTHER) with the
same 3-judge Groq panel as the depth study. Depth is NOT re-evaluated.

Arms classified: raw gemma4:12b (unprompted) and raw+clarify (system prompt).
RQA arm emits only a question -> CLARIFY by construction (noted, not judged).
Also computes regex-classifier disagreement (the v0.12 artifact) vs the LLM majority.
"""
from __future__ import annotations

import json, os, re, sys, time, requests
from pathlib import Path
from collections import Counter

HERE = Path(__file__).resolve().parent.parent
GROQ = "https://api.groq.com/openai/v1/chat/completions"
KEY = os.environ.get("GROQ_API_KEY", "")
JUDGES = [("qwen", "qwen/qwen3.6-27b"), ("gptoss120", "openai/gpt-oss-120b"),
          ("llama70", "llama-3.3-70b-versatile")]
PROMPTED_SYS = (
    "You are a helpful assistant. If the user's request is under-specified or "
    "ambiguous, ask ONE brief clarifying question instead of answering. Otherwise "
    "answer directly.")
CP = ("Classify the assistant's REPLY into ONE category:\n"
      "CLARIFY = it asked a question or requested missing info instead of answering\n"
      "ANSWER = it attempted to answer or comply with the request\n"
      "REFUSE = it declined\nOTHER = none of the above\n\n"
      "User request: {p}\nAssistant reply: {r}\n\n"
      "Respond with ONLY one word (CLARIFY, ANSWER, REFUSE, or OTHER):")

# regex classifier (the v0.12 artifact) for disagreement analysis
_REFUSE = ("cannot", "can't", "won't", "unable", "i'm not able", "sorry", "as an ai",
           "against my", "not appropriate")
_CLAR = ("could you", "can you clarify", "what do you mean", "please specify",
         "which one", "need more", "more context", "to clarify", "what are you referring")
def regex_class(t):
    t = (t or "").strip().lower()
    if not t: return "OTHER"
    if any(m in t for m in _REFUSE): return "REFUSE"
    if any(m in t for m in _CLAR): return "CLARIFY"
    if t.endswith("?") and len(t) < 240: return "CLARIFY"
    return "ANSWER"


def groq(model, prompt, system=None):
    msgs = ([{"role": "system", "content": system}] if system else []) + \
           [{"role": "user", "content": prompt}]
    r = requests.post(GROQ, timeout=120, headers={"Authorization": f"Bearer {KEY}"},
                      json={"model": model, "temperature": 0, "messages": msgs})
    return r.json()["choices"][0]["message"]["content"] or ""


def gemma(prompt, system=None):
    body = {"model": "gemma4:12b", "prompt": prompt, "think": False, "stream": False}
    if system: body["system"] = system
    return requests.post("http://localhost:11434/api/generate", json=body, timeout=180
                         ).json().get("response", "") or ""


def classify(model, p, r):
    for _ in range(2):
        try:
            out = groq(model, CP.format(p=p, r=r[:700]))
        except Exception:
            out = ""
        m = re.search(r"\b(CLARIFY|ANSWER|REFUSE|OTHER)\b", out.upper())
        if m:
            return m.group(1)
    return None


def main():
    depth = {it["prompt"]: it for it in
             (json.loads(l) for l in open(HERE/"eval"/"rows_depth_v3.jsonl", encoding="utf-8"))}
    rows3 = {it["prompt"]: it for it in
             (json.loads(l) for l in open(HERE/"eval"/"rows_3arm.jsonl", encoding="utf-8"))}
    prompts = list(depth.keys())

    items = []
    t0 = time.time()
    for p in prompts:
        raw_q = depth[p].get("raw_q", "")
        # raw+clarify: reuse 3arm's prompted output if present, else generate
        rc = rows3.get(p, {}).get("raw_prompted")
        if rc is None:
            try: rc = gemma(p, system=PROMPTED_SYS)
            except Exception: rc = ""
        items.append({"prompt": p, "raw_q": raw_q, "rawclar_q": rc,
                      "raw_regex": regex_class(raw_q)})
    print(f"[outputs ready {time.time()-t0:.0f}s; classifying x{len(JUDGES)} judges]", flush=True)

    for key, jm in JUDGES:
        for it in items:
            it[f"{key}_raw"] = classify(jm, it["prompt"], it["raw_q"])
            it[f"{key}_rawclar"] = classify(jm, it["prompt"], it["rawclar_q"])
        print(f"  judge {jm} done", flush=True)

    keys = [k for k, _ in JUDGES]
    def majority(it, arm):
        v = [it.get(f"{k}_{arm}") for k in keys if it.get(f"{k}_{arm}")]
        return Counter(v).most_common(1)[0][0] if v else None
    for it in items:
        it["raw_majority"] = majority(it, "raw")
        it["rawclar_majority"] = majority(it, "rawclar")

    n = len(items)
    def wilson(k, nn):
        if nn == 0: return (0, 0)
        import math
        z = 1.96; ph = k/nn
        d = 1+z*z/nn
        c = (ph+z*z/(2*nn))/d
        h = z*math.sqrt(ph*(1-ph)/nn+z*z/(4*nn*nn))/d
        return (round(100*(c-h), 1), round(100*(c+h), 1))

    L = [f"# Full 100-prompt behavioral relabeling (paper v0.5 appendix), n={n}",
         f"3 Groq judges {[j for _,j in JUDGES]}. Depth NOT re-evaluated. "
         f"RQA arm = CLARIFY by construction (emits only a question).\n"]
    for arm, label in (("raw", "raw gemma4:12b (unprompted)"),
                       ("rawclar", "raw gemma4:12b + clarify system prompt")):
        dist = Counter(it[f"{arm}_majority"] for it in items)
        clar = dist.get("CLARIFY", 0)
        lo, hi = wilson(clar, n)
        L.append(f"## {label}")
        L.append(f"- majority labels: {dict(dist)}")
        L.append(f"- CLARIFY rate = {clar}/{n} = {clar/n:.0%}  (Wilson 95% CI {lo}%-{hi}%)")
        for k in keys:
            jd = Counter(it.get(f"{k}_{arm}") for it in items)
            L.append(f"    judge {k}: {dict(jd)}")
    # regex disagreement on raw arm
    dis = sum(1 for it in items if it["raw_regex"] != it["raw_majority"])
    L.append(f"\n## regex classifier vs LLM majority (raw arm)")
    L.append(f"- disagreement: {dis}/{n} = {dis/n:.0%}")
    rconf = Counter((it["raw_regex"], it["raw_majority"]) for it in items)
    L.append(f"- (regex -> LLM-majority) confusion: {dict(rconf)}")
    # non-CLARIFY raw cases (the interesting ones)
    L.append("\n## raw outputs whose majority label is NOT CLARIFY")
    nonc = [it for it in items if it["raw_majority"] != "CLARIFY"]
    L.append(f"({len(nonc)} prompts)")
    for it in nonc[:25]:
        L.append(f"- [{it['prompt']}] -> {it['raw_majority']} (per-judge "
                 f"{[it.get(f'{k}_raw') for k in keys]})")

    rep = "\n".join(L)
    (HERE/"eval"/"REPORT_behavioral_relabel.md").write_text(rep, encoding="utf-8")
    with open(HERE/"eval"/"rows_behavioral_relabel.jsonl", "w", encoding="utf-8") as fh:
        for it in items:
            fh.write(json.dumps(it, ensure_ascii=False)+"\n")
    print(rep)
    print(f"\n[written] eval/REPORT_behavioral_relabel.md ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
