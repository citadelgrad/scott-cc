SHELL := /bin/bash

SEENDIFF_BASE ?= origin/main
SEENDIFF_PORT ?= 48731
SEENDIFF_RUNTIME_DIR ?= $(TMPDIR)scott-cc-seendiff
SEENDIFF_PID_FILE := $(SEENDIFF_RUNTIME_DIR)/pid
SEENDIFF_LOG_FILE := $(SEENDIFF_RUNTIME_DIR)/seendiff.log

.PHONY: up down restart status logs

up:
	@mkdir -p "$(SEENDIFF_RUNTIME_DIR)"
	@if test -f "$(SEENDIFF_PID_FILE)" && kill -0 "$$(<"$(SEENDIFF_PID_FILE)")" 2>/dev/null; then \
		echo "seendiff is already running (pid $$(<"$(SEENDIFF_PID_FILE)"))"; \
		exit 0; \
	fi
	@nohup seendiff "$(SEENDIFF_BASE)" --port "$(SEENDIFF_PORT)" --no-browser >"$(SEENDIFF_LOG_FILE)" 2>&1 & echo $$! >"$(SEENDIFF_PID_FILE)"
	@for attempt in 1 2 3 4 5; do \
		curl --fail --silent --header 'Host: 127.0.0.1' "http://127.0.0.1:$(SEENDIFF_PORT)/" >/dev/null && exit 0; \
		sleep 0.2; \
	done; \
	echo "seendiff failed to become ready; see $(SEENDIFF_LOG_FILE)"; \
	exit 1
	@echo "started seendiff at http://127.0.0.1:$(SEENDIFF_PORT)/"

status:
	@if test -f "$(SEENDIFF_PID_FILE)" && kill -0 "$$(<"$(SEENDIFF_PID_FILE)")" 2>/dev/null; then \
		curl --fail --silent --show-error --header 'Host: 127.0.0.1' "http://127.0.0.1:$(SEENDIFF_PORT)/" >/dev/null && \
		echo "seendiff is healthy (pid $$(<"$(SEENDIFF_PID_FILE)"), port $(SEENDIFF_PORT))"; \
	else \
		echo "seendiff is not running"; \
		exit 1; \
	fi

down:
	@if test -f "$(SEENDIFF_PID_FILE)"; then \
		pid="$$(<"$(SEENDIFF_PID_FILE)")"; \
		if kill -0 "$$pid" 2>/dev/null; then kill "$$pid"; fi; \
		rm -f "$(SEENDIFF_PID_FILE)"; \
	fi
	@echo "seendiff stopped"

restart: down up

logs:
	@uu-tail -f "$(SEENDIFF_LOG_FILE)"

# Verification is foreground-only; existing service lifecycle targets are unchanged.
.PHONY: setup-verification verify-static verify-distribution verify
setup-verification:
	npm ci --ignore-scripts --no-audit --no-fund
	uv sync --frozen

verify-static:
	uv run --frozen python scripts/verify_skills_distribution.py
	uv run --frozen python scripts/verify_plugin.py
	uv run --frozen pytest -q scripts/tests/test_distribution_gate.py

verify-distribution:
	uv run --frozen pytest -q scripts/tests/test_distribution_gate.py scripts/tests/test_verify_skills_distribution.py scripts/tests/test_verify_plugin.py scripts/tests/test_skills_install_matrix.py scripts/tests/test_skills_lifecycle.py scripts/tests/test_adversarial_reviewer_contract.py scripts/tests/test_portable_package_payloads.py scripts/tests/test_skill_runtime_regressions.py

verify:
	uv run --frozen pytest
