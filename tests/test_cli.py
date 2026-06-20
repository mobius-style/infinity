"""CLI + preflight tests (ero/cli.py). Network-free (Ollama probe injected).

    python3 tests/test_cli.py        # no pytest needed
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ero.cli import (  # noqa: E402
    build_parser, preflight_report, _ollama_tags, __version__,
)


# --- argument parsing ------------------------------------------------------
def test_serve_defaults_to_fast():
    args = build_parser().parse_args(["serve"])
    assert args.command == "serve" and args.profile == "fast"
    assert args.host == "127.0.0.1" and args.port == 8000


def test_profile_choice_and_aliases():
    assert build_parser().parse_args(["serve", "--profile", "quality"]).profile == "quality"
    assert build_parser().parse_args(["serve", "--cloud"]).profile == "cloud"
    assert build_parser().parse_args(["serve", "--local"]).profile == "fast"


def test_serve_options_parse():
    args = build_parser().parse_args(
        ["serve", "--port", "9001", "--model", "gemma4:12b",
         "--audit", "a.jsonl", "--no-multiturn"])
    assert args.port == 9001 and args.model == "gemma4:12b"
    assert args.audit == "a.jsonl" and args.no_multiturn is True


def test_preflight_subcommand():
    args = build_parser().parse_args(["preflight", "--ollama-url", "http://x:1"])
    assert args.command == "preflight" and args.ollama_url == "http://x:1"


# --- preflight logic -------------------------------------------------------
def _roots(tmpok=True):
    # point at the real sibling repos if present, else dummy (test only asserts level logic)
    return "/nonexistent/MOBIUS_MMV", "/nonexistent/mobius_rqa"


def test_preflight_ollama_down_is_fail():
    mmv, rqa = _roots()
    checks = preflight_report(ollama_url="http://localhost:11434",
                              models=["gemma4:12b"], mmv_root=mmv, rqa_root=rqa,
                              tags=None, profile="fast", groq_key_present=False)
    levels = {name: lvl for lvl, name, _ in checks}
    assert levels["ollama"] == "FAIL"


def test_preflight_missing_model_is_warn():
    mmv, rqa = _roots()
    checks = preflight_report(ollama_url="http://localhost:11434",
                              models=["gemma4:12b"], mmv_root=mmv, rqa_root=rqa,
                              tags={"llama3:8b"}, profile="fast", groq_key_present=False)
    levels = {name: lvl for lvl, name, _ in checks}
    assert levels["ollama"] == "PASS"
    assert levels["model:gemma4:12b"] == "WARN"


def test_preflight_model_present_by_prefix():
    mmv, rqa = _roots()
    checks = preflight_report(ollama_url="http://localhost:11434",
                              models=["gemma4:12b"], mmv_root=mmv, rqa_root=rqa,
                              tags={"gemma4:12b"}, profile="fast", groq_key_present=False)
    levels = {name: lvl for lvl, name, _ in checks}
    assert levels["model:gemma4:12b"] == "PASS"


def test_preflight_missing_repos_fail():
    checks = preflight_report(ollama_url="http://localhost:11434",
                              models=["gemma4:12b"], mmv_root="/nope/MOBIUS_MMV",
                              rqa_root="/nope/mobius_rqa", tags={"gemma4:12b"},
                              profile="fast", groq_key_present=False)
    levels = {name: lvl for lvl, name, _ in checks}
    assert levels["MMV_ROOT"] == "FAIL" and levels["RQA_ROOT"] == "FAIL"


def test_preflight_cloud_without_key_warns():
    checks = preflight_report(ollama_url="http://localhost:11434", models=[],
                              mmv_root="/x", rqa_root="/y", tags=set(),
                              profile="cloud", groq_key_present=False)
    levels = {name: lvl for lvl, name, _ in checks}
    assert levels["profile"] == "WARN"


# --- injected Ollama probe -------------------------------------------------
class _FakeResp:
    def __init__(self, body): self._body = body
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read(self): return self._body.encode()


def test_ollama_tags_parses_models():
    def opener(url, timeout=3):
        assert url.endswith("/api/tags")
        return _FakeResp('{"models":[{"name":"gemma4:12b"},{"name":"llama3:8b"}]}')
    tags = _ollama_tags("http://localhost:11434", opener=opener)
    assert tags == {"gemma4:12b", "llama3:8b"}


def test_ollama_tags_returns_none_when_down():
    def opener(url, timeout=3):
        raise OSError("connection refused")
    assert _ollama_tags("http://localhost:11434", opener=opener) is None


def test_version_string():
    assert __version__ == "1.0.0-rc1"


# --- plain-python runner ---------------------------------------------------
if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {t.__name__}: {e!r}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  ERROR {t.__name__}: {e!r}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
