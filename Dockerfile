# MOBIUS INFINITY — full-stack image (consumes a separate Ollama service).
# The MMV + RQA dependencies are cloned at build time (they are separate public
# repos, not vendored). This image is heavy: MMV/RQA pull ML deps. The model
# itself lives in the `ollama` service (see docker-compose.yml), not here.
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies (separate public repos, consumed via MMV_ROOT / RQA_ROOT).
RUN git clone --depth 1 https://github.com/mobius-style/mmv /app/deps/mmv \
 && git clone --depth 1 https://github.com/mobius-style/rqa /app/deps/rqa

# ERO source + install (core is stdlib; [serve] adds FastAPI/uvicorn).
COPY . /app/infinity
RUN pip install --no-cache-dir -e "/app/infinity[serve]" \
 && pip install --no-cache-dir -r /app/deps/mmv/requirements.txt \
 && pip install --no-cache-dir -r /app/deps/rqa/requirements.txt

ENV MMV_ROOT=/app/deps/mmv \
    RQA_ROOT=/app/deps/rqa \
    PYTHONUNBUFFERED=1

EXPOSE 8000
# OLLAMA_URL points at the compose `ollama` service.
CMD ["mobius-infinity", "serve", "--host", "0.0.0.0", "--port", "8000", \
     "--ollama-url", "http://ollama:11434"]
