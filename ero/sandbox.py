"""Isolation sandbox (v0.4) — run ERO against real MMV/RQA WITHOUT touching them.

The two systems write state differently:
  - MMV: cwd-relative ("data/memory/capsules.db", box_p.json, traces, ...).
          => contained by running with cwd = the sandbox root.
  - RQA: repo-relative (Config.state_dir = mobius_rqa/state).  <-- the real leak
          => redirected by overriding cfg.state_dir into the sandbox.

Both repos' source is imported read-only (importing .py never mutates them).
Use the `Sandbox` context manager so MMV's cwd-relative writes land in the
sandbox, and `isolated_rqa_controller` so RQA's state is redirected too. A
mutation guard (scripts/smoke_isolated.py) proves both repos stay clean.

Disposable: delete the sandbox dir to reset — that is the "redo" safety net.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .wiring import _ensure_path, _RQA_ROOT, build_mmv_engine
from .adapters import RoutingEngineAdapter, ControllerAdapter


class Sandbox:
    """cwd jail: chdir into `root` for the duration so cwd-relative writes
    (all of MMV's state) are contained. Restores the prior cwd on exit."""

    def __init__(self, root: str | os.PathLike) -> None:
        self.root = Path(root).resolve()
        self._old_cwd: str | None = None

    def setup(self) -> "Sandbox":
        (self.root / "data" / "memory").mkdir(parents=True, exist_ok=True)
        (self.root / "rqa_state").mkdir(parents=True, exist_ok=True)
        return self

    def __enter__(self) -> "Sandbox":
        self.setup()
        self._old_cwd = os.getcwd()
        os.chdir(self.root)
        return self

    def __exit__(self, *exc: Any) -> bool:
        if self._old_cwd:
            os.chdir(self._old_cwd)
        return False


def isolated_rqa_controller(sandbox_root: str | os.PathLike, *,
                            evaluator: bool = False, light: bool = True):
    """RQA Controller whose state_dir is redirected into the sandbox.

    This is the fix for the repo-relative leak: RQA's graph.db / logs / runs go
    to `<sandbox>/rqa_state`, never to mobius_rqa/state.
    """
    _ensure_path(_RQA_ROOT)
    from rqa.config import Config
    from rqa.controller import Controller
    cfg = Config()
    cfg.state_dir = Path(sandbox_root).resolve() / "rqa_state"   # <-- redirect
    cfg.evaluator_enabled = evaluator
    if light:
        cfg.k_candidates = 3
        cfg.max_reflection_depth = 1
        cfg.max_regen_per_round = 0
        cfg.shortlist_s = min(getattr(cfg, "shortlist_s", 3), cfg.k_candidates)
    return Controller(cfg)


def build_isolated_orchestrator(sandbox_root: str | os.PathLike, *,
                                audit_path: str | None = None,
                                evaluator: bool = False, light: bool = True,
                                **mmv_kwargs):
    """Wire an Orchestrator over sandboxed MMV + RQA.

    MUST be called with cwd == sandbox_root (use inside `with Sandbox(root):`)
    so MMV's cwd-relative writes are contained.
    """
    from .orchestrator import Orchestrator
    from .audit import JsonlAudit, MemoryAudit
    mmv = RoutingEngineAdapter(build_mmv_engine(**mmv_kwargs))
    rqa = ControllerAdapter(isolated_rqa_controller(sandbox_root,
                                                    evaluator=evaluator, light=light))
    audit = JsonlAudit(audit_path) if audit_path else MemoryAudit()
    return Orchestrator(mmv, rqa, audit=audit)
