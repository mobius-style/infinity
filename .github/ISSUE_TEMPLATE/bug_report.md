---
name: Bug report
about: Something doesn't work as expected
labels: bug
---

**What happened**
A clear description of the bug.

**Expected**
What you expected instead.

**Repro**
Steps / the exact request. For the API, include the `curl` and the response
(redact any keys). Note the route in `x-ero-route` / the `ero` body field.

**Environment**
- ERO version (`mobius-infinity version`) / commit:
- Profile (`--profile`) and model (`--model`):
- Ollama version + model tag; OS:
- MMV / RQA commit (the repos at `MMV_ROOT` / `RQA_ROOT`):

**Logs**
Relevant server output (with secrets removed).
