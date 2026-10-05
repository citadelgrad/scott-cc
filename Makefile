SHELL := /bin/bash

# Verification is foreground-only and never starts a background service.
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
