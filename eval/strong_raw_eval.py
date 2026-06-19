"""Decisive robustness test: is the depth advantage the METHOD or just model-scale?
Compare RQA(gemma-12B-based) questions vs a STRONG raw baseline — gpt-oss-120b's
own unprompted clarification — on the same n=100 under-specified prompts.

RQA questions reused from rows_depth_v3.jsonl (no regen). Strong-raw generated
fresh via Groq. Judges = qwen3.6-27b + llama-3.3-70b (BOTH != the generator
gpt-oss-120b, to avoid self-judging). Blind A/B, depth rubric, length covariate.
"""
from __future__ import annotations

import json, os, re, sys, time, requests
from pathlib import Path
from collections import Counter

HERE = Path(__file__).resolve().parent.parent
GROQ = "https://api.groq.com/openai/v1/chat/completions"
KEY = os.environ.get("GROQ_API_KEY", "")
STRONG_RAW = "openai/gpt-oss-120b"
JUDGES = [("qwen", "qwen/qwen3.6-27b"), ("llama70", "llama-3.3-70b-versatile")]
JP = ("Compare two clarifying QUESTIONS asked in response to an under-specified "
      "request. Judge DEPTH ONLY — ignore length, verbosity, politeness. Depth 1-5: "
      "1=only requests the missing input; 3=clarifies AND probes one assumption; "
      "5=excavates an unstated premise, surfaces a tension, or reframes the problem.\n\n"
      "Request: {p}\nQuestion A: {qa}\nQuestion B: {qb}\n\n"
      "Respond with ONLY: A=<1-5> B=<1-5> DEEPER=<A|B|TIE>")


def groq(model, prompt):
    r = requests.post(GROQ, timeout=120, headers={"Authorization": f"Bearer {KEY}"},
                      json={"model": model, "temperature": 0,
                            "messages": [{"role": "user", "content": prompt}]})
    return r.json()["choices"][0]["message"]["content"] or ""


def judge(model, p, qa, qb):
    for _ in range(2):
        try:
            out = groq(model, JP.format(p=p, qa=qa, qb=qb))
        except Exception:
            out = ""
        a = re.search(r"A\s*[=:]\s*([1-5])", out); b = re.search(r"B\s*[=:]\s*([1-5])", out)
        d = re.search(r"DEEPER\s*[=:]\s*(A|B|TIE)", out, re.I)
        if a and b and d:
            return int(a.group(1)), int(b.group(1)), d.group(1).upper()
    return None


def main():
    rqa = {it["prompt"]: it["rqa_q"]
           for it in (json.loads(l) for l in open(HERE / "eval" / "rows_depth_v3.jsonl", encoding="utf-8"))
           if it.get("rqa_q")}
    items = []
    t0 = time.time()
    for i, (p, rqa_q) in enumerate(rqa.items()):
        try:
            sraw = groq(STRONG_RAW, p)        # strong raw clarification, no system prompt
        except Exception:
            sraw = ""
        items.append({"prompt": p, "rqa_q": rqa_q, "strong_raw_q": sraw, "rqa_A": (i % 2 == 0)})
    print(f"[strong-raw gens done {time.time()-t0:.0f}s; judging]", flush=True)

    for key, jm in JUDGES:
        for it in items:
            if not it["strong_raw_q"]:
                continue
            qa, qb = (it["rqa_q"], it["strong_raw_q"]) if it["rqa_A"] else (it["strong_raw_q"], it["rqa_q"])
            r = judge(jm, it["prompt"], qa, qb)
            if not r:
                continue
            da, db, deeper = r
            it[f"{key}_rqa_d"], it[f"{key}_sraw_d"] = (da, db) if it["rqa_A"] else (db, da)
            it[f"{key}_win"] = "tie" if deeper == "TIE" else \
                ("rqa" if ((deeper == "A") == it["rqa_A"]) else "sraw")
        print(f"  judge {jm} done", flush=True)

    valid = [it for it in items if it["strong_raw_q"]]
    n = len(valid)
    keys = [k for k, _ in JUDGES]
    avg = lambda x: round(sum(x) / len(x), 2) if x else 0
    L = [f"# RQA(gemma-12B) vs STRONG raw (gpt-oss-120b) — depth, n={n}",
         f"Tests: is depth the METHOD or model-scale? Judges={[j for _,j in JUDGES]} (!= generator).\n"]
    for k in keys:
        rd = [it[f"{k}_rqa_d"] for it in valid if f"{k}_rqa_d" in it]
        sd = [it[f"{k}_sraw_d"] for it in valid if f"{k}_sraw_d" in it]
        w = Counter(it.get(f"{k}_win") for it in valid)
        L.append(f"- judge {k}: depth RQA={avg(rd)} strongRaw={avg(sd)} | deeper RQA={w['rqa']} sraw={w['sraw']} tie={w['tie']} (parsed {len(rd)})")
    both = Counter()
    for it in valid:
        v = [it.get(f"{k}_win") for k in keys if f"{k}_win" in it]
        if len(v) == 2 and v[0] == v[1]:
            both[v[0]] += 1
        elif v:
            both["split"] += 1
    L.append(f"\n- **both judges agree: RQA {both['rqa']} / strongRaw {both['sraw']} / tie {both['tie']} / split {both['split']} (of {n})**")
    L.append(f"- LENGTH: RQA mean={round(sum(len(it['rqa_q']) for it in valid)/n)} "
             f"strongRaw mean={round(sum(len(it['strong_raw_q']) for it in valid)/n)}")
    L.append("\n## samples")
    for it in valid[:8]:
        L.append(f"- [{it['prompt']}] {it.get('qwen_win','?')}/{it.get('llama70_win','?')}")
        L.append(f"    RQA : {it['rqa_q'][:90]!r}")
        L.append(f"    s-raw: {it['strong_raw_q'][:90]!r}")
    rep = "\n".join(L)
    (HERE / "eval" / "REPORT_strong_raw.md").write_text(rep, encoding="utf-8")
    with open(HERE / "eval" / "rows_strong_raw.jsonl", "w", encoding="utf-8") as fh:
        for it in items:
            fh.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(rep)
    print(f"\n[written] eval/REPORT_strong_raw.md ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
