# Security Policy

## Reporting a vulnerability
Please report security issues privately via GitHub's **Report a vulnerability**
(Security tab → Advisories) rather than a public issue. We aim to acknowledge
within a few days.

## Scope & operational notes
ERO is a local-first orchestration layer. Keep these in mind when deploying:

- **Bind address.** `serve` defaults to `127.0.0.1`. Only bind `0.0.0.0` /
  expose the port behind a network you trust.
- **Authentication.** The OpenAI-compatible API is unauthenticated by default
  (local use). For any shared/exposed deployment set an API key:
  `mobius-infinity serve --api-key <key>` (or `ERO_API_KEY`) — requests then
  need `Authorization: Bearer <key>` on `/v1/*`.
- **No rate limiting / multi-tenant isolation** is built in. Put it behind a
  reverse proxy for public exposure.
- **Backends.** Generation/judging run on whatever Ollama / OpenAI-compatible
  endpoint you configure. With the `cloud` profile, candidate questions are sent
  to the configured cloud judge (e.g. Groq) — do not use it for data that may not
  leave your machine. `fast` / `balanced` / `quality` / `turbo` are fully local.
- **Memory/state.** RQA writes a local graph store under its state dir; treat it
  as user data.

## Supported versions
The latest released version receives fixes. Pin a release tag for stability.
