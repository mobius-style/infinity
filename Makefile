PYTHON ?= python3
DEPS   := $(CURDIR)/deps
OLLAMA_MODEL ?= gemma4:12b
export MMV_ROOT ?= $(DEPS)/mmv
export RQA_ROOT ?= $(DEPS)/rqa

.DEFAULT_GOAL := help

help: ## show targets
	@grep -hE '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/' | sort

install: ## clone deps, install Python packages, pull the model, preflight
	./bootstrap.sh

preflight: ## check Ollama / model / dep repos
	mobius-infinity preflight --model $(OLLAMA_MODEL)

serve: ## run the OpenAI-compatible API (fully local, profile=fast)
	mobius-infinity serve --model $(OLLAMA_MODEL)

test: ## run the network-free test suite (no backends needed)
	@fail=0; for t in tests/*.py; do $(PYTHON) $$t || fail=1; done; exit $$fail

up: ## full stack via Docker (ollama + infinity); pulls the model on first run
	docker compose up --build

down: ## stop the Docker stack
	docker compose down

.PHONY: help install preflight serve test up down
