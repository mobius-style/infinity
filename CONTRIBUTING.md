# Contributing to MOBIUS INFINITY

Thanks for your interest. ERO is a thin, well-tested orchestration layer over
[MMV](https://github.com/mobius-style/mmv) and [RQA](https://github.com/mobius-style/rqa).

## Ground rules
- **The `ero/` core imports neither MMV nor RQA.** It depends on injected,
  duck-typed surfaces (`EntitlementSource` / `ReflectionSource`). Keep it that
  way — backends belong behind `ero/wiring.py` only.
- **Tests are network-free and pytest-free-runnable.** Every suite runs as
  `python tests/<file>.py` and also under `pytest`. New behavior needs a test.
- Match the surrounding style; keep changes small and focused.

## Dev loop
```bash
# run the whole suite (no backends, no network needed)
for t in tests/*.py; do python "$t" || break; done
# or:  make test   /   python -m pytest tests/
```
CI (`.github/workflows/ci.yml`) runs the suite on 3.10–3.13 and builds the package.

## Running against real backends
See the README quickstart (`make install` / `mobius-infinity serve`, or Docker).
Live/backed runs are **not** part of the network-free suite — verify on a host
with Ollama and the two dependency repos, and report results honestly.

## Pull requests
- One logical change per PR; describe what and why.
- Run the suite locally; note any live verification you did.
- By contributing you agree your contribution is licensed under AGPL-3.0-or-later
  (see `LICENSE` / `LICENSE_NOTICE.md`). Note the methods are patent pending
  (`PATENTS.md`); the AGPL §11 grant applies to contributed code.

## Scope
ERO is orchestration + the OpenAI-compatible surface. Changes to answer
entitlement or question generation usually belong upstream in `mmv` / `rqa`.
