"""Hardened question-depth eval (v2). Fixes the v1 confounds:
  - FRESH RQA graph per prompt (unique state_dir) -> no cross-prompt bleed.
  - Robust judge parsing + 1 retry + strict format -> recover all n.
  - Length measured as a covariate; judge told to ignore length.
RQA question taken from a fresh controller per prompt (bypasses MMV routing;
these prompts are all under-specified by construction). Raw arm reused from
rows_3arm.jsonl (raw is per-prompt independent).
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import requests
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
os.environ.setdefault("MMV_ROOT", str(HERE / "vendor" / "MOBIUS_MMV"))
os.environ.setdefault("RQA_ROOT", str(HERE / "vendor" / "mobius_rqa"))
for p in ("vendor/mobius_rqa", "."):
    sys.path.insert(0, str(HERE / p))

from ero.framing import build_augmented_input          # noqa: E402
from ero.sandbox import isolated_rqa_controller         # noqa: E402

OLLAMA = "http://localhost:11434"
JUDGE = "qwen3.6:27b"
JPROMPT = (
    "Compare two clarifying QUESTIONS asked in response to an under-specified "
    "request. Judge DEPTH ONLY — ignore length, verbosity, and politeness. "
    "Depth 1-5: 1=only requests the missing input ('what is it?'); 3=clarifies "
    "AND probes one assumption; 5=excavates an unstated premise, surfaces a "
    "tension/conflict, or reframes the problem.\n\n"
    "Request: {p}\nQuestion A: {qa}\nQuestion B: {qb}\n\n"
    "Respond with ONLY this line, nothing else:\nA=<1-5> B=<1-5> DEEPER=<A|B|TIE>")


def judge(p, qa, qb):
    for _ in range(2):
        try:
            out = requests.post(f"{OLLAMA}/api/generate",
                                json={"model": JUDGE, "prompt": JPROMPT.format(p=p, qa=qa, qb=qb),
                                      "think": False, "stream": False}, timeout=180
                                ).json().get("response", "") or ""
        except Exception:
            out = ""
        a = re.search(r"A\s*[=:]\s*([1-5])", out)
        b = re.search(r"B\s*[=:]\s*([1-5])", out)
        d = re.search(r"DEEPER\s*[=:]\s*(A|B|TIE)", out, re.I)
        if a and b and d:
            return int(a.group(1)), int(b.group(1)), d.group(1).upper()
    return None


def main():
    raw = {r["prompt"]: r["raw_unprompted"]
           for r in (json.loads(l) for l in open(HERE / "eval" / "rows_3arm.jsonl", encoding="utf-8"))}
    prompts = list(raw.keys())

    items = []
    base = HERE / "sandbox_depth2"
    for i, p in enumerate(prompts):
        ctrl = isolated_rqa_controller(base / f"p{i}")     # FRESH graph per prompt
        rr = ctrl.run(build_augmented_input(p, "MISSING_CONSTRAINTS"))
        chosen = getattr(rr, "chosen", None)
        rqa_q = (getattr(chosen, "question", "") if chosen else "") or ""
        fr = getattr(rr, "final_round", None)
        cands = [c.question for c in (getattr(fr, "shortlist", []) if fr else [])]
        items.append({"prompt": p, "rqa_q": rqa_q, "rqa_angles": len(set(cands)),
                      "raw_q": raw[p], "rqa_len": len(rqa_q), "raw_len": len(raw[p])})
    print(f"[fresh-graph RQA done; judging {JUDGE}]", flush=True)

    rqa_d, raw_d, w = [], [], {"rqa": 0, "raw": 0, "tie": 0}
    parsed = 0
    for i, it in enumerate(items):
        if not it["rqa_q"]:
            it["deeper"] = "rqa_empty"; continue
        rqa_A = (i % 2 == 0)
        qa, qb = (it["rqa_q"], it["raw_q"]) if rqa_A else (it["raw_q"], it["rqa_q"])
        r = judge(it["prompt"], qa, qb)
        if not r:
            it["deeper"] = "parse_fail"; continue
        parsed += 1
        da, db, deeper = r
        it["rqa_depth"], it["raw_depth"] = (da, db) if rqa_A else (db, da)
        rqa_d.append(it["rqa_depth"]); raw_d.append(it["raw_depth"])
        win = "tie" if deeper == "TIE" else ("rqa" if ((deeper == "A") == rqa_A) else "raw")
        it["deeper"] = win; w[win] += 1

    avg = lambda x: round(sum(x) / len(x), 2) if x else 0
    L = [f"# Hardened depth eval v2 — RQA(fresh graph/prompt) vs raw (EN under-spec)",
         f"n_prompts={len(items)}  parsed_judgements={parsed}  judge={JUDGE} (blind, length-ignored)\n",
         f"- mean DEPTH: RQA={avg(rqa_d)}  raw={avg(raw_d)}",
         f"- pairwise deeper: RQA {w['rqa']}, raw {w['raw']}, tie {w['tie']} (of {parsed})",
         f"- mean ANGLES (RQA candidates): {avg([it['rqa_angles'] for it in items])}  (raw=1)",
         f"- LENGTH covariate (chars): RQA mean={avg([it['rqa_len'] for it in items])} "
         f"raw mean={avg([it['raw_len'] for it in items])}",
         "\n## per-prompt (depth RQA/raw, winner) + texts"]
    for it in items:
        L.append(f"- [{it['prompt']}] RQA={it.get('rqa_depth','?')} raw={it.get('raw_depth','?')} "
                 f"{it.get('deeper','?')}")
        L.append(f"    RQA: {it['rqa_q'][:120]!r}")
        L.append(f"    raw: {it['raw_q'][:100]!r}")
    rep = "\n".join(L)
    (HERE / "eval" / "REPORT_depth_v2.md").write_text(rep, encoding="utf-8")
    with open(HERE / "eval" / "rows_depth_v2.jsonl", "w", encoding="utf-8") as fh:
        for it in items:
            fh.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(rep)
    print("\n[written] eval/REPORT_depth_v2.md")


if __name__ == "__main__":
    main()
