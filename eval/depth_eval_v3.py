"""Depth eval v3 — toward publishable. n=40 EN under-specified prompts,
RQA(fresh graph/prompt) vs raw gemma4 clarification, judged BLIND by THREE
independent judges (qwen3.6:27b, llama3.1:8b, gpt-oss:20b) for inter-rater.
Reports per-judge depth, majority pairwise, agreement, and a loss analysis.

Deferred (stated): generator model-independence (RQA on a non-gemma base) is a
separate larger study; here the generator is fixed (gemma-based RQA).
"""
from __future__ import annotations

import json, os, re, sys, time, requests
from pathlib import Path
from collections import Counter

HERE = Path(__file__).resolve().parent.parent
os.environ.setdefault("MMV_ROOT", str(HERE / "vendor" / "MOBIUS_MMV"))
os.environ.setdefault("RQA_ROOT", str(HERE / "vendor" / "mobius_rqa"))
for p in ("vendor/mobius_rqa", "."):
    sys.path.insert(0, str(HERE / p))
from ero.framing import build_augmented_input        # noqa: E402
from ero.sandbox import isolated_rqa_controller       # noqa: E402

OLLAMA = "http://localhost:11434"
GROQ = "https://api.groq.com/openai/v1/chat/completions"
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
# 3 independent judges (label, model), different families; groq: -> Groq.
JUDGES = [
    ("qwen", "groq:qwen/qwen3.6-27b"),             # Groq, Qwen
    ("gptoss120", "groq:openai/gpt-oss-120b"),     # Groq, OpenAI-oss 120B
    ("llama70", "groq:llama-3.3-70b-versatile"),   # Groq, Llama 70B
]

NEW = [
    # bare imperatives (verb + deictic / no object)
    "Summarize it.", "Translate this.", "Explain.", "Review it.", "Check this.",
    "Rank them.", "Simplify it.", "Rewrite it.", "Analyze this.", "Estimate it.",
    "Schedule it.", "Update it.", "Merge them.", "Split it.", "Tune it.",
    "Validate it.", "Refactor this.", "Debug it.", "Plan it.", "Draft it.",
    "Finish it.", "Wrap it up.", "Clean it up.", "Format it.", "Test it.",
    "Deploy it.", "Document it.", "Approve it.", "Escalate it.", "Archive it.",
    "Cancel it.", "Forward it.", "Flag it.", "Tag it.", "Filter them.",
    "Combine these.", "Prioritize these.", "Scale it.", "Migrate it.", "Back it up.",
    "Compress it.", "Convert it.",
    # vague choice / decision (no options given)
    "Which approach?", "Which framework?", "Which option works?", "Pick a strategy.",
    "Choose the format.", "Decide for me.", "Recommend one.", "Suggest something.",
    "Give me the best.", "How should I proceed?", "What's the right way?",
    "Help me decide.", "Where do I start?", "What now?", "Make a decision.",
    "Choose wisely.", "Go with the best.", "Which is right?",
    # vague evaluation / opinion
    "Is this correct?", "Does this work?", "What do you think?", "Any ideas?",
    "Is it good enough?", "Should I?", "Is this fine?", "Does it make sense?",
    "Worth it?", "Good or bad?",
    # deictic continuation / context-dependent
    "Same as before.", "Like last time.", "The usual.", "As discussed.",
    "Following that.", "Based on this.", "Continue from there.",
    "Pick up where we left off.", "Do the rest.", "Take it from here.",
    "Handle the rest.", "Carry on.",
]

JP = ("Compare two clarifying QUESTIONS asked in response to an under-specified "
      "request. Judge DEPTH ONLY — ignore length, verbosity, politeness. Depth 1-5: "
      "1=only requests the missing input; 3=clarifies AND probes one assumption; "
      "5=excavates an unstated premise, surfaces a tension, or reframes the problem.\n\n"
      "Request: {p}\nQuestion A: {qa}\nQuestion B: {qb}\n\n"
      "Respond with ONLY: A=<1-5> B=<1-5> DEEPER=<A|B|TIE>")


def gen_raw(prompt):
    try:
        return requests.post(f"{OLLAMA}/api/generate",
                             json={"model": "gemma4:12b", "prompt": prompt, "think": False,
                                   "stream": False}, timeout=180).json().get("response", "") or ""
    except Exception:
        return ""


def _gen(model, prompt):
    """Route to Groq (groq:<id>) or local Ollama."""
    if model.startswith("groq:"):
        r = requests.post(GROQ, timeout=120,
                          headers={"Authorization": f"Bearer {GROQ_KEY}"},
                          json={"model": model[5:], "temperature": 0,
                                "messages": [{"role": "user", "content": prompt}]})
        return r.json()["choices"][0]["message"]["content"] or ""
    return requests.post(f"{OLLAMA}/api/generate", timeout=180,
                         json={"model": model, "prompt": prompt, "think": False,
                               "stream": False}).json().get("response", "") or ""


def ask_judge(model, p, qa, qb):
    for _ in range(2):
        try:
            out = _gen(model, JP.format(p=p, qa=qa, qb=qb))
        except Exception:
            out = ""
        a = re.search(r"A\s*[=:]\s*([1-5])", out); b = re.search(r"B\s*[=:]\s*([1-5])", out)
        d = re.search(r"DEEPER\s*[=:]\s*(A|B|TIE)", out, re.I)
        if a and b and d:
            return int(a.group(1)), int(b.group(1)), d.group(1).upper()
    return None


def main():
    existing = {r["prompt"]: r["raw_unprompted"]
                for r in (json.loads(l) for l in open(HERE / "eval" / "rows_3arm.jsonl", encoding="utf-8"))}
    prompts = list(existing.keys()) + NEW
    base = HERE / "sandbox_depth3"

    items = []
    t0 = time.time()
    for i, p in enumerate(prompts):
        ctrl = isolated_rqa_controller(base / f"p{i}")
        rr = ctrl.run(build_augmented_input(p, "MISSING_CONSTRAINTS"))
        ch = getattr(rr, "chosen", None)
        rqa_q = (getattr(ch, "question", "") if ch else "") or ""
        raw_q = existing.get(p) or gen_raw(p)
        items.append({"prompt": p, "rqa_q": rqa_q, "raw_q": raw_q,
                      "rqa_A": (i % 2 == 0)})
    print(f"[gens done {time.time()-t0:.0f}s; judging x{len(JUDGES)}]", flush=True)

    # judge per model (load each judge once)
    for key, jm in JUDGES:
        for it in items:
            if not it["rqa_q"]:
                continue
            qa, qb = (it["rqa_q"], it["raw_q"]) if it["rqa_A"] else (it["raw_q"], it["rqa_q"])
            r = ask_judge(jm, it["prompt"], qa, qb)
            if not r:
                continue
            da, db, deeper = r
            rqa_d, raw_d = (da, db) if it["rqa_A"] else (db, da)
            win = "tie" if deeper == "TIE" else ("rqa" if ((deeper == "A") == it["rqa_A"]) else "raw")
            it[f"{key}_rqa_d"] = rqa_d; it[f"{key}_raw_d"] = raw_d; it[f"{key}_win"] = win
        print(f"  judge {jm} done", flush=True)

    # aggregate
    valid = [it for it in items if it["rqa_q"]]
    n = len(valid)
    L = [f"# Depth eval v3 (n={n} valid of {len(items)}) — RQA(fresh graph) vs raw gemma4",
         f"3 blind judges, length-ignored. Generator = gemma-based RQA (model-independence deferred).\n"]
    keys = [lbl for lbl, _ in JUDGES]
    for k in keys:
        rd = [it[f"{k}_rqa_d"] for it in valid if f"{k}_rqa_d" in it]
        wd = [it[f"{k}_raw_d"] for it in valid if f"{k}_raw_d" in it]
        wins = Counter(it.get(f"{k}_win") for it in valid)
        avg = lambda x: round(sum(x)/len(x), 2) if x else 0
        L.append(f"- judge {k}: depth RQA={avg(rd)} raw={avg(wd)} | deeper RQA={wins['rqa']} raw={wins['raw']} tie={wins['tie']} (parsed {len(rd)})")
    # majority pairwise
    maj = Counter()
    allagree = 0
    for it in valid:
        votes = [it.get(f"{k}_win") for k in keys if f"{k}_win" in it]
        if not votes:
            continue
        c = Counter(votes); top = c.most_common(1)[0][0]
        maj[top] += 1
        if len(set(votes)) == 1:
            allagree += 1
    L.append(f"\n- **majority pairwise: RQA {maj['rqa']} / raw {maj['raw']} / tie {maj['tie']} (of {sum(maj.values())})**")
    L.append(f"- unanimous (all 3 judges agree direction): {allagree}/{sum(maj.values())} = {allagree/max(1,sum(maj.values())):.0%}")
    L.append(f"- LENGTH chars: RQA mean={round(sum(len(it['rqa_q']) for it in valid)/n)} raw mean={round(sum(len(it['raw_q']) for it in valid)/n)}")
    # loss analysis
    L.append("\n## where RQA does NOT win (majority raw or tie) — texts")
    for it in valid:
        votes = [it.get(f"{k}_win") for k in keys if f"{k}_win" in it]
        if votes and Counter(votes).most_common(1)[0][0] != "rqa":
            L.append(f"- [{it['prompt']}] votes={votes}")
            L.append(f"    RQA: {it['rqa_q'][:110]!r}")
            L.append(f"    raw: {it['raw_q'][:90]!r}")
    rep = "\n".join(L)
    (HERE / "eval" / "REPORT_depth_v3.md").write_text(rep, encoding="utf-8")
    with open(HERE / "eval" / "rows_depth_v3.jsonl", "w", encoding="utf-8") as fh:
        for it in items:
            fh.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(rep)
    print(f"\n[written] eval/REPORT_depth_v3.md  ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
