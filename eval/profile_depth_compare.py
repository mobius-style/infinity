"""Profile depth comparison — is `fast` a safe default?

Question: does dropping RQA's evaluator + shrinking the budget (FAST: k3/d1, no
judge, ~12s) lose question DEPTH vs the paper-grade config (QUALITY: k6/d3 + a
strong Groq judge selecting among candidates)? If FAST ~= QUALITY on judged
depth, `fast` is a justified interactive default.

Method: N under-specified prompts; for each, generate the FAST question and the
QUALITY question on the SAME local gemma4:12b stack (fresh isolated graph per
cell). Then 3 independent Groq judges rate DEPTH blind (A/B randomized), same
rubric as depth_eval_v3. Reports per-judge depth means, majority pairwise win,
agreement, length, and per-cell latency. Writes eval/REPORT_profile_compare.md.

Needs GROQ_API_KEY (judges) + local Ollama gemma4:12b. Long (~20 min) — run with
run_in_background.
"""
import os
import re
import sys
import time
import tempfile
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
os.environ.setdefault("MMV_ROOT", str(HERE / "vendor" / "MOBIUS_MMV"))
os.environ.setdefault("RQA_ROOT", str(HERE / "vendor" / "mobius_rqa"))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "vendor" / "mobius_rqa"))

import requests  # noqa: E402
from ero.sandbox import isolated_rqa_controller  # noqa: E402
from ero.adapters import ControllerAdapter  # noqa: E402
from ero.framing import build_augmented_input  # noqa: E402

GROQ = "https://api.groq.com/openai/v1/chat/completions"
KEY = os.environ.get("GROQ_API_KEY", "")
JUDGES = [("qwen", "qwen/qwen3.6-27b"),
          ("gptoss120", "openai/gpt-oss-120b"),
          ("llama70", "llama-3.3-70b-versatile")]

JP = ("Compare two clarifying QUESTIONS asked in response to an under-specified "
      "request. Judge DEPTH ONLY — ignore length, verbosity, politeness. Depth 1-5: "
      "1=only requests the missing input; 3=clarifies AND probes one assumption; "
      "5=excavates an unstated premise, surfaces a tension, or reframes the problem.\n\n"
      "Request: {p}\nQuestion A: {qa}\nQuestion B: {qb}\n\n"
      "Respond with ONLY: A=<1-5> B=<1-5> DEEPER=<A|B|TIE>")

PROMPTS = [
    "Which is better?", "Which framework?",          # option-free comparison
    "Is this correct?", "Good or bad?",               # vague evaluation
    "Simplify it.", "Refactor this.",                 # underspecified improvement
    "Should I?", "What's the right way?",             # vague advice
    "Summarize it.", "Merge them.",                   # pure referent-missing
    "Same as before.", "Continue from there.",        # deictic continuation
]


def judge(model, p, qa, qb):
    for _ in range(2):
        try:
            r = requests.post(GROQ, timeout=120,
                              headers={"Authorization": f"Bearer {KEY}"},
                              json={"model": model, "temperature": 0,
                                    "messages": [{"role": "user",
                                                  "content": JP.format(p=p, qa=qa, qb=qb)}]})
            out = r.json()["choices"][0]["message"]["content"]
        except Exception:
            out = ""
        a = re.search(r"A\s*[=:]\s*([1-5])", out)
        b = re.search(r"B\s*[=:]\s*([1-5])", out)
        d = re.search(r"DEEPER\s*[=:]\s*(A|B|TIE)", out, re.I)
        if a and b and d:
            return int(a.group(1)), int(b.group(1)), d.group(1).upper()
    return None


def gen(profile, root, prompt):
    """profile in {'fast','quality'}; returns (question, latency_s)."""
    aug = build_augmented_input(prompt, "MISSING_CONSTRAINTS")
    if profile == "fast":
        ctrl = isolated_rqa_controller(root, evaluator=False, light=True)
    else:  # quality: full budget (k6/d3) + Groq evaluator selection
        ctrl = isolated_rqa_controller(root, evaluator=True, light=False)
    t = time.time()
    q = ControllerAdapter(ctrl).reflect(aug).primary
    return q or "", time.time() - t


def main():
    if not KEY:
        print("ERROR: GROQ_API_KEY not set"); return 1
    base = Path(tempfile.mkdtemp(prefix="ero_profcmp_"))
    items = []
    t0 = time.time()
    for i, p in enumerate(PROMPTS):
        fq, ft = gen("fast", base / f"f{i}", p)
        qq, qt = gen("quality", base / f"q{i}", p)
        # blind A/B: fast is A on even i
        fast_is_A = (i % 2 == 0)
        items.append({"p": p, "fast_q": fq, "qual_q": qq, "ft": ft, "qt": qt,
                      "fast_A": fast_is_A})
        print(f"[{i+1}/{len(PROMPTS)}] '{p}'  fast {ft:.0f}s / quality {qt:.0f}s",
              flush=True)
        print(f"    FAST: {fq[:120]}", flush=True)
        print(f"    QUAL: {qq[:120]}", flush=True)
    print(f"[gens done {time.time()-t0:.0f}s; judging x{len(JUDGES)}]", flush=True)

    for key, jm in JUDGES:
        for it in items:
            if not (it["fast_q"] and it["qual_q"]):
                continue
            qa, qb = (it["fast_q"], it["qual_q"]) if it["fast_A"] else (it["qual_q"], it["fast_q"])
            res = judge(jm, it["p"], qa, qb)
            if not res:
                continue
            da, db, deeper = res
            fast_d, qual_d = (da, db) if it["fast_A"] else (db, da)
            win = "tie" if deeper == "TIE" else (
                "fast" if ((deeper == "A") == it["fast_A"]) else "quality")
            it[f"{key}_fast_d"] = fast_d
            it[f"{key}_qual_d"] = qual_d
            it[f"{key}_win"] = win
        print(f"  judge {jm} done", flush=True)

    valid = [it for it in items if it.get("fast_q") and it.get("qual_q")]
    n = len(valid)
    avg = lambda xs: round(sum(xs) / len(xs), 2) if xs else 0
    L = [f"# Profile depth compare (n={n}) — FAST (k3/d1, no judge) vs QUALITY (k6/d3 + Groq judge)",
         "Blind 3-judge paired depth (length-ignored). Same local gemma4:12b generator.\n"]
    for key, _ in JUDGES:
        fd = [it[f"{key}_fast_d"] for it in valid if f"{key}_fast_d" in it]
        qd = [it[f"{key}_qual_d"] for it in valid if f"{key}_qual_d" in it]
        wins = {"fast": 0, "quality": 0, "tie": 0}
        for it in valid:
            if f"{key}_win" in it:
                wins[it[f"{key}_win"]] += 1
        L.append(f"- judge {key}: depth FAST={avg(fd)} QUALITY={avg(qd)} | "
                 f"deeper FAST={wins['fast']} QUALITY={wins['quality']} tie={wins['tie']}")

    # majority pairwise
    maj = {"fast": 0, "quality": 0, "tie": 0}
    allagree = 0
    for it in valid:
        ws = [it[f"{k}_win"] for k, _ in JUDGES if f"{k}_win" in it]
        if not ws:
            continue
        for outcome in ("fast", "quality"):
            if ws.count(outcome) >= 2:
                maj[outcome] += 1
                break
        else:
            maj["tie"] += 1
        if len(set(ws)) == 1 and len(ws) == len(JUDGES):
            allagree += 1
    tot = sum(maj.values())
    L.append(f"\n- **majority pairwise: FAST {maj['fast']} / QUALITY {maj['quality']} / tie {maj['tie']} (of {tot})**")
    L.append(f"- unanimous (all 3 judges agree direction): {allagree}/{tot}")
    fl = round(sum(len(it["fast_q"]) for it in valid) / max(1, n))
    ql = round(sum(len(it["qual_q"]) for it in valid) / max(1, n))
    L.append(f"- length chars: FAST mean={fl} QUALITY mean={ql}")
    L.append(f"- latency: FAST mean={avg([it['ft'] for it in valid])}s "
             f"QUALITY mean={avg([it['qt'] for it in valid])}s")
    L.append("\n## interpretation")
    L.append("If FAST is not majority-shallower than QUALITY, dropping the local "
             "evaluator costs little DEPTH while removing the dominant latency — "
             "so `fast` is a justified interactive default. QUALITY wins quantify "
             "the depth headroom the evaluator buys (use `--profile cloud` to get "
             "it at low latency).")
    L.append("\n## per-prompt")
    for it in valid:
        ws = "/".join(it.get(f"{k}_win", "-") for k, _ in JUDGES)
        L.append(f"\n### {it['p']}  (judges fast/qual/llama: {ws})")
        L.append(f"- FAST ({it['ft']:.0f}s): {it['fast_q']}")
        L.append(f"- QUALITY ({it['qt']:.0f}s): {it['qual_q']}")

    report = HERE / "eval" / "REPORT_profile_compare.md"
    report.write_text("\n".join(L), encoding="utf-8")
    rows = HERE / "eval" / "rows_profile_compare.jsonl"
    import json
    with open(rows, "w", encoding="utf-8") as fh:
        for it in items:
            fh.write(json.dumps(it, ensure_ascii=False) + "\n")
    shutil.rmtree(base, ignore_errors=True)
    print("\n".join(L))
    print(f"\n[written] {report}  ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
