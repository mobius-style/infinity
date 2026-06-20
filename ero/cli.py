"""`mobius-infinity` console entry — make ERO feel like a local LLM.

    mobius-infinity preflight     # check Ollama / models / repos before serving
    mobius-infinity serve         # OpenAI-compatible API (defaults to LOCAL: no key)
    mobius-infinity version       # show version + evaluator binding

Design: the CLI is the only place that assembles host backends. Argument parsing
and the preflight checks are pure / injectable, so they are network-free tested
(`tests/test_cli.py`); the Ollama probe degrades gracefully when offline.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from .wiring import RQA_PROFILE_NAMES as PROFILE_NAMES

__version__ = "1.0.0-rc1"

_MOBIUS_AI = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# Preflight (pure logic + injectable probes)
# --------------------------------------------------------------------------- #
def _ollama_tags(ollama_url, opener=urllib.request.urlopen, timeout=3):
    """Return the set of locally-available Ollama model tags, or None if the
    daemon is unreachable. Network probe is injectable for testing."""
    try:
        with opener(f"{ollama_url.rstrip('/')}/api/tags", timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        return {m.get("name", "") for m in data.get("models", [])}
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return None


def preflight_report(*, ollama_url, models, mmv_root, rqa_root, tags,
                     profile, groq_key_present):
    """Build a list of (level, name, detail) checks. Pure — `tags` is the result
    of the Ollama probe (a set, or None when the daemon is down)."""
    checks = []

    if tags is None:
        checks.append(("FAIL", "ollama", f"not reachable at {ollama_url} "
                       "(start it: `ollama serve`)"))
    else:
        checks.append(("PASS", "ollama", f"reachable at {ollama_url}"))
        for m in models:
            present = m in tags or any(t.split(":")[0] == m.split(":")[0] for t in tags)
            checks.append(("PASS" if present else "WARN", f"model:{m}",
                           "present" if present else f"missing (`ollama pull {m}`)"))

    for label, root in (("MMV_ROOT", mmv_root), ("RQA_ROOT", rqa_root)):
        p = Path(root)
        ok = p.is_dir() and (p / "src").is_dir() if label == "MMV_ROOT" \
            else p.is_dir() and (p / "rqa").is_dir()
        checks.append(("PASS" if ok else "FAIL", label,
                       f"{root}" if ok else f"not found / not a repo: {root}"))

    if profile != "cloud":
        checks.append(("PASS", "profile", f"{profile} (fully local, no cloud key)"))
    elif groq_key_present:
        checks.append(("PASS", "profile", "cloud (Groq evaluator; GROQ_API_KEY set)"))
    else:
        checks.append(("WARN", "profile", "cloud profile needs GROQ_API_KEY (not "
                       "set) — use `--profile fast` for key-free operation"))
    return checks


def _print_report(checks):
    icon = {"PASS": "✓", "WARN": "!", "FAIL": "✗"}
    for level, name, detail in checks:
        print(f"  [{icon.get(level, '?')}] {name:<16} {detail}")
    worst = "FAIL" if any(c[0] == "FAIL" for c in checks) else \
            ("WARN" if any(c[0] == "WARN" for c in checks) else "PASS")
    print(f"\npreflight: {worst}")
    return 1 if worst == "FAIL" else 0


# --------------------------------------------------------------------------- #
# Argument parsing (pure)
# --------------------------------------------------------------------------- #
def build_parser():
    p = argparse.ArgumentParser(prog="mobius-infinity",
                                description="MOBIUS INFINITY / ERO — governed "
                                            "answer-entitlement + reflective questioning")
    p.add_argument("--version", action="version", version=f"mobius-infinity {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--ollama-url", default="http://localhost:11434")
    common.add_argument("--model", default="gemma4:12b",
                        help="base generation model (Ollama tag)")
    common.add_argument("--profile", choices=PROFILE_NAMES, default="fast",
                        help="reflection speed/quality tier (default: fast ~12s, "
                             "fully local; cloud needs GROQ_API_KEY)")
    # convenience aliases for the two common cases
    grp = common.add_mutually_exclusive_group()
    grp.add_argument("--local", dest="profile", action="store_const", const="fast",
                     help="alias for --profile fast (fully local, no key)")
    grp.add_argument("--cloud", dest="profile", action="store_const", const="cloud",
                     help="alias for --profile cloud (Groq evaluator; needs GROQ_API_KEY)")
    common.add_argument("--mmv-root", default=os.environ.get("MMV_ROOT",
                        str(_MOBIUS_AI / "MOBIUS_MMV")))
    common.add_argument("--rqa-root", default=os.environ.get("RQA_ROOT",
                        str(_MOBIUS_AI / "mobius_rqa")))

    sp = sub.add_parser("serve", parents=[common],
                        help="run the OpenAI-compatible API")
    sp.add_argument("--host", default="127.0.0.1")
    sp.add_argument("--port", type=int, default=8000)
    sp.add_argument("--audit", default=None, help="JSONL audit path")
    sp.add_argument("--advertised-model", default=None,
                    help="model id reported on /v1/models (default: mobius-infinity)")
    sp.add_argument("--no-multiturn", action="store_true",
                    help="route only on the latest user message (ignore history)")
    sp.add_argument("--api-key", default=os.environ.get("ERO_API_KEY"),
                    help="require Authorization: Bearer <key> on /v1/* "
                         "(default: $ERO_API_KEY, else open)")
    sp.add_argument("--timeout", type=float, default=120.0,
                    help="per-request timeout in seconds (504 if exceeded)")

    sub.add_parser("preflight", parents=[common],
                   help="check Ollama / models / repos")
    sub.add_parser("version", help="print version")
    return p


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def _apply_roots(args):
    os.environ["MMV_ROOT"] = args.mmv_root
    os.environ["RQA_ROOT"] = args.rqa_root


def cmd_preflight(args):
    _apply_roots(args)
    tags = _ollama_tags(args.ollama_url)
    checks = preflight_report(
        ollama_url=args.ollama_url, models=[args.model], mmv_root=args.mmv_root,
        rqa_root=args.rqa_root, tags=tags, profile=args.profile,
        groq_key_present=bool(os.environ.get("GROQ_API_KEY")),
    )
    return _print_report(checks)


def cmd_serve(args):
    _apply_roots(args)
    from .openai_api import serve, DEFAULT_MODEL_ID
    from .wiring import (build_orchestrator, BackendConfig,
                         new_mmv_session_from_messages)

    backend = BackendConfig(kind="ollama", model=args.model,
                            base_url=args.ollama_url)
    orch = build_orchestrator(audit_path=args.audit, profile=args.profile,
                              backend=backend, generator_model=args.model,
                              ollama_url=args.ollama_url)
    session_factory = None if args.no_multiturn else new_mmv_session_from_messages
    advertised = args.advertised_model or DEFAULT_MODEL_ID
    auth = "on (Bearer)" if args.api_key else "off"
    print(f"[mobius-infinity] serving OpenAI-compatible API on "
          f"http://{args.host}:{args.port}  (model={advertised}, profile={args.profile}, "
          f"auth={auth}, timeout={args.timeout:g}s)")
    print(f"[mobius-infinity] NOTE: this assistant asks a clarifying question or "
          f"abstains when a request is under-specified — by design.")
    serve(orch, host=args.host, port=args.port, model=advertised,
          session_factory=session_factory, api_key=args.api_key,
          request_timeout=args.timeout)
    return 0


def cmd_version(_args):
    print(f"mobius-infinity {__version__}")
    return 0


def main(argv=None):
    args = build_parser().parse_args(argv)
    return {"preflight": cmd_preflight, "serve": cmd_serve,
            "version": cmd_version}[args.command](args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
