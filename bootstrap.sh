#!/usr/bin/env bash
# Turnkey local setup for MOBIUS INFINITY:
#   1) clone the MMV + RQA dependencies, 2) install Python deps,
#   3) pull the Ollama model, 4) preflight.
# Re-runnable (idempotent). Env overrides: PYTHON, OLLAMA_MODEL, DEPS.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPS="${DEPS:-$HERE/deps}"
PY="${PYTHON:-python3}"
MODEL="${OLLAMA_MODEL:-gemma4:12b}"

echo "[1/4] Cloning MMV + RQA into $DEPS ..."
mkdir -p "$DEPS"
[ -d "$DEPS/mmv/.git" ] || git clone --depth 1 https://github.com/mobius-style/mmv "$DEPS/mmv"
[ -d "$DEPS/rqa/.git" ] || git clone --depth 1 https://github.com/mobius-style/rqa "$DEPS/rqa"

echo "[2/4] Installing Python deps ..."
"$PY" -m pip install -e "$HERE[serve]"
[ -f "$DEPS/mmv/requirements.txt" ] && "$PY" -m pip install -r "$DEPS/mmv/requirements.txt"
[ -f "$DEPS/rqa/requirements.txt" ] && "$PY" -m pip install -r "$DEPS/rqa/requirements.txt"

echo "[3/4] Pulling Ollama model: $MODEL ..."
if command -v ollama >/dev/null 2>&1; then
  ollama pull "$MODEL"
else
  echo "  ! ollama not found — install from https://ollama.com then: ollama pull $MODEL"
fi

echo "[4/4] Preflight ..."
export MMV_ROOT="$DEPS/mmv" RQA_ROOT="$DEPS/rqa"
mobius-infinity preflight --model "$MODEL" || true

cat <<EOF

✓ Setup complete. To serve (fully local, no API key):

  export MMV_ROOT="$DEPS/mmv" RQA_ROOT="$DEPS/rqa"
  mobius-infinity serve

Then point any OpenAI client at  http://127.0.0.1:8000/v1
(or just run:  make serve)
EOF
