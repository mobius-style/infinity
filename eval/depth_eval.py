"""Question DEPTH/ANGLE comparison (the RQA raison-d'etre test):
composite RQA question vs raw gemma4 clarification, on EN under-specified prompts.

Independent judge (qwen3.6:27b), BLIND (A/B randomized per prompt), rates each
question depth 1-5 and picks the deeper one. Also records RQA's candidate-set
angle count (structural). Two model loads (gemma composite, then qwen judge).

Depth rubric: 1 = merely requests the missing input/slot ("what do you mean?");
3 = clarifies AND probes one assumption; 5 = excavates an unstated premise,
surfaces a tension/conflict, or reframes the problem space.
"""
from __future__ import annotations

import json
import re
import sys
import time
import requests
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
for p in ("vendor/MOBIUS_MMV", "vendor/mobius_rqa", "."):
    sys.path.insert(0, str(HERE / p))
import os
os.environ.setdefault("MMV_ROOT", str(HERE / "vendor" / "MOBIUS_MMV"))
os.environ.setdefault("RQA_ROOT", str(HERE / "vendor" / "mobius_rqa"))
from ero.sandbox import Sandbox, build_isolated_orchestrator  # noqa: E402
from ero.wiring import new_mmv_session  # noqa: E402

OLLAMA = "http://localhost:11434"
JUDGE = "qwen3.6:27b"


def judge_pair(prompt, qa, qb):
    j = (f"Two assistants each replied to an under-specified user request with a QUESTION. "
         f"Rate each question's DEPTH 1-5: 1=merely requests the missing input/slot "
         f"('what do you mean?'); 3=clarifies AND probes one assumption; 5=excavates an "
         f"unstated premise, surfaces a tension/conflict, or reframes the problem space.\n\n"
         f"User request: {prompt}\nQuestion A: {qa}\nQuestion B: {qb}\n\n"
         f"Reply EXACTLY as: A=<1-5> B=<1-5> DEEPER=<A|B|TIE>")
    try:
        out = requests.post(f"{OLLAMA}/api/generate",
                            json={"model": JUDGE, "prompt": j, "think": False, "stream": False},
                            timeout=180).json().get("response", "") or ""
    except Exception as e:
        return None
    a = re.search(r"A\s*=\s*([1-5])", out); b = re.search(r"B\s*=\s*([1-5])", out)
    d = re.search(r"DEEPER\s*=\s*(A|B|TIE)", out, re.I)
    if not (a and b and d):
        return None
    return int(a.group(1)), int(b.group(1)), d.group(1).upper()


def main():
    raw = {r["prompt"]: r["raw_unprompted"]
           for r in (json.loads(l) for l in open(HERE / "eval" / "rows_3arm.jsonl", encoding="utf-8"))}
    prompts = list(raw.keys())  # the 18 EN under-specified prompts

    items = []
    ws = HERE / "sandbox_depth"
    with Sandbox(ws):
        ero = build_isolated_orchestrator(ws)
        for p in prompts:
            res = ero.handle(p, session_state=new_mmv_session())
            rqa_q = res.text or ""
            cands = getattr(res.result, "questions", []) or []
            items.append({"prompt": p, "rqa_q": rqa_q, "rqa_angles": len(set(cands)),
                          "raw_q": raw[p]})
    print(f"[composite done; judging with {JUDGE}]", flush=True)

    # judge, blind: even idx -> A=rqa,B=raw ; odd idx -> A=raw,B=rqa
    rqa_depths, raw_depths, rqa_wins, raw_wins, ties = [], [], 0, 0, 0
    for i, it in enumerate(items):
        rqa_is_A = (i % 2 == 0)
        qa, qb = (it["rqa_q"], it["raw_q"]) if rqa_is_A else (it["raw_q"], it["rqa_q"])
        r = judge_pair(it["prompt"], qa, qb)
        if not r:
            continue
        da, db, deeper = r
        rqa_d, raw_d = (da, db) if rqa_is_A else (db, da)
        rqa_depths.append(rqa_d); raw_depths.append(raw_d)
        winner = ("rqa" if ((deeper == "A") == rqa_is_A) else "raw") if deeper != "TIE" else "tie"
        it.update({"rqa_depth": rqa_d, "raw_depth": raw_d, "deeper": winner})
        if winner == "rqa": rqa_wins += 1
        elif winner == "raw": raw_wins += 1
        else: ties += 1

    n = len(rqa_depths)
    avg = lambda x: round(sum(x) / len(x), 2) if x else 0
    L = [f"# Question depth/angle — composite RQA vs raw gemma4 (EN under-spec, n={n})",
         f"Independent blind judge = {JUDGE}. Depth 1-5 (5=excavates premise/reframes).\n",
         f"- mean DEPTH: composite(RQA) = {avg(rqa_depths)}  |  raw = {avg(raw_depths)}",
         f"- pairwise 'deeper': RQA {rqa_wins}/{n}, raw {raw_wins}/{n}, tie {ties}/{n}",
         f"- mean ANGLES in RQA candidate set: {avg([it['rqa_angles'] for it in items])} (raw = 1 by construction)",
         "\n## samples"]
    for it in items[:8]:
        L.append(f"- depth RQA={it.get('rqa_depth','?')} raw={it.get('raw_depth','?')} ({it.get('deeper','?')}) | {it['prompt']!r}")
        L.append(f"    RQA: {it['rqa_q'][:90]!r}")
        L.append(f"    raw: {it['raw_q'][:90]!r}")
    rep = "\n".join(L)
    (HERE / "eval" / "REPORT_depth.md").write_text(rep, encoding="utf-8")
    with open(HERE / "eval" / "rows_depth.jsonl", "w", encoding="utf-8") as fh:
        for it in items:
            fh.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(rep)
    print("\n[written] eval/REPORT_depth.md")


if __name__ == "__main__":
    main()
