"""3-arm restraint comparison on English under-specified prompts (paper-grade):
  A) raw gemma4:12b, no system prompt
  B) raw gemma4:12b WITH a clarify-when-ambiguous system prompt
  C) the ERO composite (appraiser route == ask)

Behavior of A/B is classified by an INDEPENDENT judge (qwen3.6:27b) into
CLARIFY / ANSWER / REFUSE — neutral cross-family, more reliable than regex.
Two model loads only (all gemma gens first, then all qwen judgments).
"""
from __future__ import annotations

import json
import re
import sys
import time
import requests
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "vendor" / "MOBIUS_MMV"))
from src.kernel.appraisal import Appraiser          # noqa: E402
from src.kernel.route_decision import select_route   # noqa: E402

OLLAMA = "http://localhost:11434"
GEN = "gemma4:12b"
JUDGE = "qwen3.6:27b"
CJK = re.compile(r'[぀-ヿ㐀-鿿＀-￯]')

PROMPTED_SYS = (
    "You are a helpful assistant. If the user's request is under-specified or "
    "ambiguous — missing what to act on, which options to compare, or key "
    "constraints — ask ONE brief clarifying question instead of answering. "
    "Otherwise, answer directly."
)


def gen(prompt, system=None):
    body = {"model": GEN, "prompt": prompt, "think": False, "stream": False}
    if system:
        body["system"] = system
    try:
        return requests.post(f"{OLLAMA}/api/generate", json=body, timeout=180).json().get("response", "") or ""
    except Exception as e:
        return f"[ERR {e}]"


def judge(prompt, reply):
    j = (f"Classify the assistant's reply to a user request. Answer with EXACTLY one word: "
         f"CLARIFY (it asked a clarifying question instead of answering), "
         f"ANSWER (it attempted to answer or comply), or REFUSE (it declined).\n\n"
         f"User request: {prompt}\nAssistant reply: {reply[:600]}\n\nOne word:")
    try:
        out = requests.post(f"{OLLAMA}/api/generate",
                            json={"model": JUDGE, "prompt": j, "think": False, "stream": False},
                            timeout=180).json().get("response", "") or ""
    except Exception as e:
        return "ERR"
    u = out.upper()
    for k in ("CLARIFY", "REFUSE", "ANSWER"):
        if k in u:
            return k
    return "ANSWER"


def main():
    src = open(HERE / "eval" / "run_quality_eval.py", encoding="utf-8").read()
    ask = re.findall(r'"((?:[^"\\]|\\.)*)"',
                     re.search(r"\n\s*ask\s*=\s*\[(.*?)\n\s*\]", src, re.S).group(1))
    prompts = [t for t in ask if not CJK.search(t)]   # English under-specified only
    ap = Appraiser()

    rows = []
    t0 = time.time()
    # pass 1: gemma generations (both arms)
    for p in prompts:
        rows.append({"prompt": p,
                     "composite_asks": select_route(ap.evaluate(p), query=p).route == "ask",
                     "raw_unprompted": gen(p),
                     "raw_prompted": gen(p, system=PROMPTED_SYS)})
    print(f"[gemma gens done in {time.time()-t0:.0f}s] judging with {JUDGE}...", flush=True)
    # pass 2: judge
    for r in rows:
        r["unprompted_class"] = judge(r["prompt"], r["raw_unprompted"])
        r["prompted_class"] = judge(r["prompt"], r["raw_prompted"])

    n = len(rows)
    comp = sum(r["composite_asks"] for r in rows)
    up = sum(r["unprompted_class"] == "CLARIFY" for r in rows)
    pr = sum(r["prompted_class"] == "CLARIFY" for r in rows)
    L = [f"# 3-arm restraint comparison — English under-specified (n={n})",
         f"Judge = {JUDGE} (independent). CLARIFY = asked back instead of answering.\n",
         f"- C) ERO composite asks back:        {comp}/{n} = {comp/n:.0%}",
         f"- B) raw + clarify-system-prompt:    {pr}/{n} = {pr/n:.0%}",
         f"- A) raw, no system prompt:          {up}/{n} = {up/n:.0%}\n",
         "## interpretation",
         f"- composite vs prompted-raw gap: {comp/n:.0%} - {pr/n:.0%} = {(comp-pr)/n:+.0%}",
         f"- prompted-raw lift over unprompted: {(pr-up)/n:+.0%}"]
    L.append("\n## per-prompt")
    for r in rows:
        L.append(f"- {'ASK ' if r['composite_asks'] else 'ans '}|raw={r['unprompted_class'][:5]:5}"
                 f"|prompted={r['prompted_class'][:5]:5}| {r['prompt']!r}")
    rep = "\n".join(L)
    (HERE / "eval" / "REPORT_3arm_english.md").write_text(rep, encoding="utf-8")
    with open(HERE / "eval" / "rows_3arm.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(rep)
    print(f"\n[written] eval/REPORT_3arm_english.md  (total {time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
