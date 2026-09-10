#!/usr/bin/env python3
"""Run hash-bound Hermes skill routing checks in throwaway profile homes.

The no-model ``probe`` exercises the frozen Hermes scanner and ``skill_view``
handler. The ``run`` command is intentionally authorization-gated because real
automatic routing is an LLM decision. It accepts private prompts over stdin,
retains only hashes and event counts, and removes every per-scenario home.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import math
import os
import re
import secrets
import shutil
import sqlite3
import stat
import subprocess
import sys
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

FROZEN_HERMES_COMMIT = "21b2095d00a98b8ad7b5c60b10587619c852cdb8"
FROZEN_DESIGN_SHA256 = (
    "29963dcb172bd3d7030c45eda797959a5341b9c0067c168c7340e1f2dc454734"
)
FROZEN_SPLIT_HASHES = {
    "public": "03be9aafd2e39605e7a31d82bedff9d5d24061d7b2dddb1986fa78fa26b975c6",
    "hidden": "394769a9ad916869c71732a7ce5039ad983059dbcbe560e5c9e327f8a3c29c30",
    "sealed": "9954b44ebc3bb95478abdf0a1f9f2f33ea9a842d6f2d6fdb9e3afc7920f4c864",
}
CORPUS_ENVELOPE_SCHEMA = "hermes-beads-routing-prompts.v1"
CORPUS_ENVELOPE_SCHEMA_V2 = "hermes-beads-routing-prompts.v2"
DISCOVERY_DESIGN_SCHEMA_V2 = "hermes-beads-discovery-benchmark-design.v2"
REPORT_SCHEMA = "hermes-beads-actual-discovery-report.v3"
SCENARIO_COUNT = 72
MAX_TURNS = 2
RUN_BUDGET_SECONDS = 180
MINIMUM_ROUTING_OBSERVATIONS = 60
MINIMUM_VARIANTS_PER_FAMILY = 5
MINIMUM_REPEATS_PER_VARIANT = 3
ROUTING_MACRO_THRESHOLD = 950_000
ROUTING_WILSON_THRESHOLD = 850_000
BUDGET_CONTRACT = {
    "isolated_sessions": True,
    "max_turns": MAX_TURNS,
    "maximum_provider_requests_per_session": MAX_TURNS,
    "run_budget_seconds": RUN_BUDGET_SECONDS,
}
BUDGET_CONTRACT_SHA256 = (
    "f10a71365f954ac8880ad4dc75008484b575784f173976e72225d1512cf05221"
)
PRESTATE_CONTRACT = {
    "bundled_skills": "disabled",
    "credentials": "copied-0600-when-provided",
    "default_profile": "sandbox-write-denied",
    "home": "fresh-0700",
    "installed_candidate": "exact-tree-hash",
}
PRESTATE_CONTRACT_SHA256 = (
    "0e5ee5f79de6bc6e58beb78c88239cbb0334b8eaaef2e1ef3edeef1a023c0a1e"
)
POSITIVE_ROUTE_FAMILIES = ("explicit", "implicit", "recovery", "planning", "swarm")
NEGATIVE_ROUTE_FAMILIES = (
    "trivial_request",
    "alternative_tracker",
    "durable_executor_without_beads",
    "repository_context_without_tracker_work",
)
# Bounded raw-output retention for errored lanes (Defect 3). A cap per stream
# stops a runaway process from filling the disk; a cap on how many errored
# lanes retain output at all bounds total disk use across a full sweep.
RAW_RETENTION_MAX_BYTES = 65_536
RAW_RETENTION_LANE_LIMIT = 3
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_VOLATILE_PARTS = {"__pycache__", ".pytest_cache", ".DS_Store"}
_CREDENTIAL_FILES = (".env", "auth.json")


class HarnessError(RuntimeError):
    """A fail-closed harness contract violation."""


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    split: str
    polarity: str
    prompt: str
    expected_load: bool
    route_family: str = "legacy"
    repeat: int = 1


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    split: str
    expected_load: bool
    discovery_events: int
    load_events: int
    exit_code: int
    stdout_sha256: str
    stderr_sha256: str
    state_sha256: str
    route_family: str = "legacy"
    repeat: int = 1
    prompt_disclosed: bool = False
    raw_stdout_path: str | None = None
    raw_stderr_path: str | None = None
    # Per-lane default-profile mutation attribution (scc-l41). Populated by
    # run_corpus from a before/after _profile_fingerprint pair taken around
    # this exact lane; paired with the sibling scenario_id field above, each
    # result row names both which lane ran and which tracked root(s), if
    # any, changed under it. Empty for a lane where nothing changed, and
    # empty by default here because _run_scenario (which builds this
    # dataclass) does not itself see the default-profile home -- only
    # run_corpus does, so it attaches this afterward via dataclasses.replace.
    profile_delta: list[str] = field(default_factory=list)

    @property
    def errored(self) -> bool:
        """True when the session did not complete cleanly.

        When this is true, routing is UNKNOWN, not wrong: the session may
        have crashed before it ever reached skill routing (for example, a
        rejected model call). Do not read an errored lane as a routing
        failure.
        """
        return self.exit_code != 0

    @property
    def _observed_load(self) -> bool:
        return self.discovery_events > 0 and self.load_events > 0

    @property
    def routed_correctly(self) -> bool:
        """Whether the observed load matched the expected load.

        Meaningful only when ``errored`` is false. On an errored lane the
        observed counts are typically zero as a side effect of the crash,
        not evidence the skill decided correctly, so this value must not be
        used for pass/fail purposes while errored.
        """
        return self._observed_load == self.expected_load

    @property
    def outcome(self) -> str:
        """One of 'errored', 'passed', 'failed' -- a strict three-way partition.

        An errored session is never folded into 'failed': a systemic outage
        (every lane erroring) must read as "N errored", not "N routing
        failures".
        """
        if self.errored:
            return "errored"
        return "passed" if self.routed_correctly else "failed"

    @property
    def passed(self) -> bool:
        return self.outcome == "passed"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return sha256_bytes(encoded)


def _iter_tree_files(root: Path) -> Iterable[Path]:
    root = Path(root)
    if not root.is_dir():
        raise HarnessError("TREE_ROOT_INVALID")
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root)
        if (
            any(part in _VOLATILE_PARTS for part in relative.parts)
            or path.suffix == ".pyc"
        ):
            continue
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise HarnessError("TREE_SYMLINK_FORBIDDEN")
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise HarnessError("TREE_NONREGULAR_FORBIDDEN")
        yield path


def hash_tree(root: Path) -> str:
    """Hash relative paths, executable bits, lengths, and bytes deterministically."""
    root = Path(root)
    digest = hashlib.sha256()
    for path in _iter_tree_files(root):
        relative = path.relative_to(root).as_posix().encode()
        content = path.read_bytes()
        executable = b"1" if path.stat().st_mode & 0o111 else b"0"
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(executable)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def _require_hash(value: Any, code: str) -> str:
    if not isinstance(value, str) or not _HASH_RE.fullmatch(value):
        raise HarnessError(code)
    return value


def git_commit(repo: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        check=False,
        text=True,
        timeout=15,
    )
    commit = result.stdout.strip()
    if result.returncode or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise HarnessError("HERMES_SOURCE_IDENTITY_UNAVAILABLE")
    return commit


def verify_frozen_hermes(hermes_source: Path) -> None:
    if git_commit(hermes_source) != FROZEN_HERMES_COMMIT:
        raise HarnessError("HERMES_COMMIT_MISMATCH")


def _copy_tree_exact(source: Path, destination: Path) -> None:
    if destination.exists():
        raise HarnessError("INSTALL_TARGET_EXISTS")
    destination.mkdir(parents=True)
    for source_file in _iter_tree_files(source):
        relative = source_file.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_file, target, follow_symlinks=False)
        os.chmod(target, stat.S_IMODE(source_file.stat().st_mode))


def install_candidate(candidate: Path, home: Path, expected_sha256: str) -> Path:
    expected = _require_hash(expected_sha256, "CANDIDATE_HASH_INVALID")
    candidate = Path(candidate).resolve()
    if hash_tree(candidate) != expected:
        raise HarnessError("CANDIDATE_HASH_MISMATCH")
    home = Path(home)
    home.mkdir(parents=True, exist_ok=False)
    os.chmod(home, 0o700)
    (home / ".no-bundled-skills").touch(mode=0o600)
    installed = home / "skills" / "beads"
    _copy_tree_exact(candidate, installed)
    if hash_tree(installed) != expected:
        raise HarnessError("INSTALLED_CANDIDATE_HASH_MISMATCH")
    return installed


def _load_json(path: Path, code: str) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise HarnessError(code) from error


def _load_bound_json(
    path: Path,
    expected_sha256: str,
    *,
    mismatch_code: str,
    invalid_code: str,
) -> Any:
    """Hash and parse one immutable in-memory snapshot of a JSON file."""
    try:
        raw = Path(path).read_bytes()
        if sha256_bytes(raw) != expected_sha256:
            raise HarnessError(mismatch_code)
        return json.loads(raw.decode("utf-8"))
    except HarnessError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise HarnessError(invalid_code) from error


def corpus_split_hashes(rows: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    """Hash prompt rows per split without exposing their content."""
    hashes: dict[str, str] = {}
    for split in ("public", "hidden", "sealed"):
        split_rows = sorted(
            (dict(row) for row in rows if row.get("split") == split),
            key=lambda row: str(row.get("variant_id", "")),
        )
        encoded = json.dumps(
            split_rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        hashes[split] = sha256_bytes(encoded)
    return hashes


def _validated_v2_design(
    design_path: Path, expected_design_sha256: str | None
) -> Mapping[str, Any]:
    if expected_design_sha256 is None:
        raise HarnessError("DESIGN_HASH_REQUIRED")
    expected_design = _require_hash(expected_design_sha256, "DESIGN_HASH_INVALID")
    design = _load_bound_json(
        design_path,
        expected_design,
        mismatch_code="DESIGN_HASH_MISMATCH",
        invalid_code="DESIGN_INVALID",
    )
    if (
        not isinstance(design, dict)
        or design.get("schema_version") != DISCOVERY_DESIGN_SCHEMA_V2
    ):
        raise HarnessError("DESIGN_SCHEMA_MISMATCH")
    if design.get("status") != "frozen":
        raise HarnessError("DESIGN_NOT_FROZEN")
    if (
        design.get("frozen_budget") != BUDGET_CONTRACT
        or design.get("budget_sha256") != BUDGET_CONTRACT_SHA256
        or sha256_json(design.get("frozen_budget")) != BUDGET_CONTRACT_SHA256
    ):
        raise HarnessError("FROZEN_BUDGET_MISMATCH")
    if (
        design.get("prestate_contract") != PRESTATE_CONTRACT
        or design.get("prestate_contract_sha256") != PRESTATE_CONTRACT_SHA256
        or sha256_json(design.get("prestate_contract")) != PRESTATE_CONTRACT_SHA256
    ):
        raise HarnessError("FROZEN_PRESTATE_MISMATCH")

    thresholds = design.get("thresholds")
    required_thresholds = {
        "minimum_positive_observations": MINIMUM_ROUTING_OBSERVATIONS,
        "minimum_negative_observations": MINIMUM_ROUTING_OBSERVATIONS,
        "minimum_variants_per_family": MINIMUM_VARIANTS_PER_FAMILY,
        "minimum_repeats_per_variant": MINIMUM_REPEATS_PER_VARIANT,
        "positive_macro_millionths": ROUTING_MACRO_THRESHOLD,
        "negative_restraint_macro_millionths": ROUTING_MACRO_THRESHOLD,
        "wilson_lower_millionths": ROUTING_WILSON_THRESHOLD,
        "hard_zero_safety_violations": 0,
        "maximum_execution_errors": 0,
    }
    if thresholds != required_thresholds:
        raise HarnessError("DESIGN_THRESHOLDS_MISMATCH")

    families = design.get("families")
    if not isinstance(families, dict):
        raise HarnessError("DESIGN_FAMILIES_INVALID")
    positive_families = families.get("positive")
    negative_families = families.get("negative")
    if positive_families != list(POSITIVE_ROUTE_FAMILIES) or negative_families != list(
        NEGATIVE_ROUTE_FAMILIES
    ):
        raise HarnessError("DESIGN_FAMILIES_INVALID")
    positive_family_names = list(POSITIVE_ROUTE_FAMILIES)
    negative_family_names = list(NEGATIVE_ROUTE_FAMILIES)

    variants = design.get("variants")
    if not isinstance(variants, list):
        raise HarnessError("DESIGN_VARIANTS_INVALID")
    variant_ids: set[str] = set()
    family_counts = {
        family: 0 for family in positive_family_names + negative_family_names
    }
    for variant in variants:
        if not isinstance(variant, dict) or set(variant) != {
            "variant_id",
            "split",
            "expected_load",
            "route_family",
            "source_scenario_id",
            "brief",
        }:
            raise HarnessError("DESIGN_VARIANTS_INVALID")
        variant_id = variant.get("variant_id")
        split = variant.get("split")
        expected_load = variant.get("expected_load")
        family = variant.get("route_family")
        if (
            not isinstance(variant_id, str)
            or not variant_id
            or variant_id in variant_ids
            or split not in {"public", "hidden", "sealed"}
            or not isinstance(expected_load, bool)
            or family
            not in (positive_family_names if expected_load else negative_family_names)
            or not isinstance(variant.get("brief"), str)
            or not variant["brief"]
        ):
            raise HarnessError("DESIGN_VARIANTS_INVALID")
        variant_ids.add(variant_id)
        family_counts[str(family)] += 1
    if any(count < MINIMUM_VARIANTS_PER_FAMILY for count in family_counts.values()):
        raise HarnessError("DESIGN_VARIANTS_PER_FAMILY_INSUFFICIENT")

    repeats = design.get("execution_matrix", {}).get("repeats_per_variant")
    if not isinstance(repeats, int) or repeats < MINIMUM_REPEATS_PER_VARIANT:
        raise HarnessError("DESIGN_REPEATS_INSUFFICIENT")
    positive_observations = sum(
        repeats for variant in variants if variant["expected_load"]
    )
    negative_observations = sum(
        repeats for variant in variants if not variant["expected_load"]
    )
    matrix = design.get("execution_matrix", {})
    if (
        positive_observations < MINIMUM_ROUTING_OBSERVATIONS
        or negative_observations < MINIMUM_ROUTING_OBSERVATIONS
        or matrix.get("positive_observations") != positive_observations
        or matrix.get("negative_observations") != negative_observations
        or matrix.get("total_observations")
        != positive_observations + negative_observations
    ):
        raise HarnessError("DESIGN_OBSERVATION_MATRIX_INVALID")

    freeze = design.get("corpus_freeze")
    if not isinstance(freeze, dict):
        raise HarnessError("CORPUS_FREEZE_INVALID")
    split_hashes = freeze.get("split_hashes")
    if not isinstance(split_hashes, dict) or set(split_hashes) != {
        "public",
        "hidden",
        "sealed",
    }:
        raise HarnessError("CORPUS_FREEZE_INVALID")
    for value in split_hashes.values():
        _require_hash(value, "CORPUS_SPLIT_HASH_INVALID")
    attestation = freeze.get("custodian_attestation")
    if (
        not isinstance(attestation, dict)
        or attestation.get("role") != "benchmark-custodian"
        or not isinstance(attestation.get("custodian_identifier"), str)
        or not attestation["custodian_identifier"].strip()
        or attestation.get("candidate_author_disclosed") is not False
        or attestation.get("candidate_package_read") is not False
        or not isinstance(attestation.get("frozen_at"), str)
        or re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z",
            attestation["frozen_at"],
        )
        is None
    ):
        raise HarnessError("CUSTODIAN_ATTESTATION_INVALID")
    return design


def validate_v2_runtime_contract(
    design_path: Path,
    expected_design_sha256: str,
    *,
    candidate_sha256: str,
    provider: str,
    model: str,
) -> None:
    design = _validated_v2_design(design_path, expected_design_sha256)
    runtime = design.get("frozen_runtime")
    if not isinstance(runtime, dict):
        raise HarnessError("FROZEN_RUNTIME_INVALID")
    if runtime.get("candidate_sha256") != candidate_sha256:
        raise HarnessError("FROZEN_CANDIDATE_MISMATCH")
    if runtime.get("hermes_commit") != FROZEN_HERMES_COMMIT:
        raise HarnessError("FROZEN_HERMES_MISMATCH")
    if runtime.get("provider") != provider or runtime.get("model") != model:
        raise HarnessError("FROZEN_MODEL_STRATUM_MISMATCH")
    if runtime.get("harness_schema") != REPORT_SCHEMA:
        raise HarnessError("FROZEN_HARNESS_SCHEMA_MISMATCH")
    harness_sha256 = runtime.get("harness_sha256")
    _require_hash(harness_sha256, "FROZEN_HARNESS_HASH_INVALID")
    if sha256_file(Path(__file__)) != harness_sha256:
        raise HarnessError("FROZEN_HARNESS_HASH_MISMATCH")


def _load_v2_corpus(
    envelope: Mapping[str, Any],
    design_path: Path,
    expected_design_sha256: str | None,
) -> list[Scenario]:
    design = _validated_v2_design(design_path, expected_design_sha256)
    if envelope.get("schema_version") != CORPUS_ENVELOPE_SCHEMA_V2:
        raise HarnessError("CORPUS_SCHEMA_MISMATCH")
    if envelope.get("design_sha256") != expected_design_sha256:
        raise HarnessError("CORPUS_DESIGN_BINDING_MISMATCH")
    expected_split_hashes = design["corpus_freeze"]["split_hashes"]
    if envelope.get("split_hashes") != expected_split_hashes:
        raise HarnessError("CORPUS_SPLIT_BINDING_MISMATCH")
    rows = envelope.get("scenarios")
    if not isinstance(rows, list):
        raise HarnessError("CORPUS_INDEX_MISMATCH")
    if any(
        not isinstance(row, dict) or set(row) != {"variant_id", "split", "prompt"}
        for row in rows
    ):
        raise HarnessError("CORPUS_ROW_SHAPE_INVALID")
    if corpus_split_hashes(rows) != expected_split_hashes:
        raise HarnessError("CORPUS_SPLIT_HASH_MISMATCH")

    variants = {row["variant_id"]: row for row in design["variants"]}
    observed_ids = [row.get("variant_id") for row in rows if isinstance(row, dict)]
    if (
        len(rows) != len(variants)
        or len(observed_ids) != len(rows)
        or len(set(observed_ids)) != len(observed_ids)
        or set(observed_ids) != set(variants)
    ):
        raise HarnessError("CORPUS_INDEX_MISMATCH")
    rows_by_id = {row["variant_id"]: row for row in rows}
    repeats = design["execution_matrix"]["repeats_per_variant"]
    scenarios: list[Scenario] = []
    family_prompt_hashes: dict[str, set[str]] = {}
    for variant_id, variant in sorted(variants.items()):
        row = rows_by_id[variant_id]
        if set(row) != {"variant_id", "split", "prompt"}:
            raise HarnessError("CORPUS_ROW_SHAPE_INVALID")
        prompt = row.get("prompt")
        if row.get("split") != variant["split"]:
            raise HarnessError("CORPUS_INDEX_MISMATCH")
        if not isinstance(prompt, str) or not prompt or len(prompt.encode()) > 65_536:
            raise HarnessError("CORPUS_PROMPT_INVALID")
        route_family = variant["route_family"]
        prompt_hash = sha256_bytes(prompt.encode("utf-8"))
        seen_prompt_hashes = family_prompt_hashes.setdefault(route_family, set())
        if prompt_hash in seen_prompt_hashes:
            raise HarnessError("CORPUS_VARIANTS_NOT_DISTINCT")
        seen_prompt_hashes.add(prompt_hash)
        scenarios.extend(
            Scenario(
                scenario_id=variant_id,
                split=variant["split"],
                polarity="positive" if variant["expected_load"] else "negative",
                prompt=prompt,
                expected_load=variant["expected_load"],
                route_family=route_family,
                repeat=repeat,
            )
            for repeat in range(1, repeats + 1)
        )
    return scenarios


def load_corpus(
    corpus_path: Path,
    design_path: Path,
    expected_sha256: str,
    expected_design_sha256: str | None = None,
) -> list[Scenario]:
    """Validate a custodian-provided private envelope without returning its text."""
    expected_sha = _require_hash(expected_sha256, "CORPUS_HASH_INVALID")
    envelope = _load_bound_json(
        corpus_path,
        expected_sha,
        mismatch_code="CORPUS_HASH_MISMATCH",
        invalid_code="CORPUS_INVALID",
    )
    if not isinstance(envelope, dict):
        raise HarnessError("CORPUS_INVALID")
    design_probe = _load_json(design_path, "DESIGN_INVALID")
    if (
        isinstance(design_probe, dict)
        and design_probe.get("schema_version") == DISCOVERY_DESIGN_SCHEMA_V2
    ):
        return _load_v2_corpus(
            envelope,
            design_path,
            expected_design_sha256,
        )
    if sha256_file(design_path) != FROZEN_DESIGN_SHA256:
        raise HarnessError("DESIGN_HASH_MISMATCH")
    design = _load_json(design_path, "DESIGN_INVALID")
    if envelope.get("schema_version") != CORPUS_ENVELOPE_SCHEMA:
        raise HarnessError("CORPUS_SCHEMA_MISMATCH")
    if envelope.get("design_sha256") != FROZEN_DESIGN_SHA256:
        raise HarnessError("CORPUS_DESIGN_BINDING_MISMATCH")
    if envelope.get("split_hashes") != FROZEN_SPLIT_HASHES:
        raise HarnessError("CORPUS_SPLIT_BINDING_MISMATCH")

    expected_rows = {
        row[0]: {
            "split": row[1],
            "polarity": row[2],
            "expected_load": "RST" not in row[5],
        }
        for row in design.get("scenarios", [])
        if isinstance(row, list) and len(row) >= 6
    }
    raw_scenarios = envelope.get("scenarios")
    if len(expected_rows) != SCENARIO_COUNT or not isinstance(raw_scenarios, list):
        raise HarnessError("CORPUS_INDEX_MISMATCH")
    observed_ids = [
        row.get("scenario_id") for row in raw_scenarios if isinstance(row, dict)
    ]
    if len(raw_scenarios) != SCENARIO_COUNT or set(observed_ids) != set(expected_rows):
        raise HarnessError("CORPUS_INDEX_MISMATCH")
    if len(observed_ids) != len(set(observed_ids)):
        raise HarnessError("CORPUS_INDEX_MISMATCH")

    scenarios: list[Scenario] = []
    rows_by_id = {row["scenario_id"]: row for row in raw_scenarios}
    for scenario_id in sorted(expected_rows):
        row = rows_by_id[scenario_id]
        expected_row = expected_rows[scenario_id]
        prompt = row.get("prompt")
        if set(row) != {"scenario_id", "split", "polarity", "prompt"}:
            raise HarnessError("CORPUS_ROW_SHAPE_INVALID")
        if (
            row.get("split") != expected_row["split"]
            or row.get("polarity") != expected_row["polarity"]
        ):
            raise HarnessError("CORPUS_INDEX_MISMATCH")
        if not isinstance(prompt, str) or not prompt or len(prompt.encode()) > 65_536:
            raise HarnessError("CORPUS_PROMPT_INVALID")
        scenarios.append(
            Scenario(
                scenario_id=scenario_id,
                split=row["split"],
                polarity=row["polarity"],
                prompt=prompt,
                expected_load=bool(expected_row["expected_load"]),
            )
        )
    return scenarios


def run_approval_digest(
    *,
    candidate_sha256: str,
    corpus_sha256: str,
    design_sha256: str | None,
    provider: str,
    model: str,
    force_full_sweep: bool,
) -> str:
    """Bind authorization to every run-defining identity and cost control."""
    return sha256_json(
        {
            "candidate_sha256": candidate_sha256,
            "corpus_sha256": corpus_sha256,
            "design_sha256": design_sha256,
            "provider": provider,
            "model": model,
            "force_full_sweep": force_full_sweep,
            "harness_sha256": sha256_file(Path(__file__)),
            "budget_sha256": BUDGET_CONTRACT_SHA256,
            "prestate_contract_sha256": PRESTATE_CONTRACT_SHA256,
        }
    )


def approval_request(
    provider: str,
    model: str,
    *,
    scenario_count: int = SCENARIO_COUNT,
    design_sha256: str | None = None,
    candidate_sha256: str | None = None,
    corpus_sha256: str | None = None,
    force_full_sweep: bool = False,
) -> dict[str, Any]:
    request = {
        "hermes_sessions": scenario_count,
        "maximum_provider_requests": scenario_count * MAX_TURNS,
        "maximum_turns_per_session": MAX_TURNS,
        "run_budget_seconds_per_session": RUN_BUDGET_SECONDS,
        "provider": provider,
        "model": model,
        "billing_mode": "OpenAI Codex subscription quota"
        if provider == "openai-codex"
        else "provider-defined",
        "paid_api_fallback": False,
    }
    if design_sha256 is not None:
        request["design_sha256"] = design_sha256
    if candidate_sha256 is not None:
        request["candidate_sha256"] = candidate_sha256
    if corpus_sha256 is not None:
        request["corpus_sha256"] = corpus_sha256
    if (
        design_sha256 is not None
        and candidate_sha256 is not None
        and corpus_sha256 is not None
    ):
        request["force_full_sweep"] = force_full_sweep
        request["approval_digest"] = run_approval_digest(
            candidate_sha256=candidate_sha256,
            corpus_sha256=corpus_sha256,
            design_sha256=design_sha256,
            provider=provider,
            model=model,
            force_full_sweep=force_full_sweep,
        )
    request["authorization_boundary"] = (
        "human-operated policy boundary; not cryptographically authenticated "
        "in plugin-free v1"
    )
    return request


# -- scc-ux6: real single-use authorization tokens --------------------------
#
# A prior defect let an agent compute a "valid" --authorization value
# directly from public source (a deterministic f-string over provider/model),
# so no real human action was ever required to launch a quota-consuming run.
# That incident is documented in beads issue scc-ux6.
#
# The fix: a local ledger of human-issued, unguessable, single-use tokens.
# A token must be minted out-of-band by a human (see
# ``issue_authorization_token`` / the ``issue-token`` CLI command) before it
# exists in the ledger at all -- an agent can never derive one from this
# file's source. Presenting a token consumes it atomically, immediately, and
# unconditionally: before any preflight check (e.g. CANDIDATE_HASH_MISMATCH)
# and before any subprocess is spawned. This means a second presentation of
# the same token -- regardless of whether the first attempt completed,
# failed a preflight check, or errored -- is always rejected, and an agent
# can never self-conclude that a prior, still-open authorization covers a
# new attempt.
DEFAULT_TOKEN_LEDGER_PATH = (
    Path.home() / ".hermes-discovery-harness" / "authorization-tokens.json"
)
TOKEN_BYTES = 32


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ledger_lock_path(ledger_path: Path) -> Path:
    return Path(str(ledger_path) + ".lock")


@contextlib.contextmanager
def _held_ledger_lock(ledger_path: Path):
    """Serialize read-modify-write access to the token ledger across processes.

    This locks a dedicated, never-replaced ``*.lock`` file rather than the
    ledger file itself. The ledger is rewritten via atomic replace-on-write
    (``_write_secure_bytes``), which swaps in a fresh inode on every write,
    so an ``flock`` held on the ledger file's own file descriptor would
    silently stop protecting anything the moment one writer replaced it.
    """
    ledger_path = Path(ledger_path)
    ledger_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock_path = _ledger_lock_path(ledger_path)
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _read_ledger(ledger_path: Path) -> list[dict[str, Any]]:
    ledger_path = Path(ledger_path)
    if not ledger_path.exists():
        return []
    try:
        entries = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise HarnessError("AUTHORIZATION_LEDGER_INVALID") from error
    if not isinstance(entries, list):
        raise HarnessError("AUTHORIZATION_LEDGER_INVALID")
    return entries


def _write_ledger(ledger_path: Path, entries: list[dict[str, Any]]) -> None:
    rendered = json.dumps(entries, indent=2, sort_keys=True) + "\n"
    _write_secure_bytes(Path(ledger_path), rendered.encode("utf-8"))


def issue_authorization_token(
    approval_digest: str,
    ledger_path: Path = DEFAULT_TOKEN_LEDGER_PATH,
) -> str:
    """Mint one fresh, single-use token bound to a reviewed run plan."""
    if not isinstance(approval_digest, str) or not re.fullmatch(
        r"[0-9a-f]{64}", approval_digest
    ):
        raise HarnessError("AUTHORIZATION_PLAN_DIGEST_INVALID")
    ledger_path = Path(ledger_path)
    token = secrets.token_hex(TOKEN_BYTES)
    with _held_ledger_lock(ledger_path):
        entries = _read_ledger(ledger_path)
        entries.append(
            {
                "token": token,
                "approval_digest": approval_digest,
                "issued_at": _now_iso(),
                "consumed": False,
                "consumed_at": None,
            }
        )
        _write_ledger(ledger_path, entries)
    return token


def consume_authorization_token(
    token: str,
    approval_digest: str,
    ledger_path: Path = DEFAULT_TOKEN_LEDGER_PATH,
) -> None:
    """Atomically consume a token only for its reviewed run plan."""
    ledger_path = Path(ledger_path)
    with _held_ledger_lock(ledger_path):
        entries = _read_ledger(ledger_path)
        match = next(
            (
                entry
                for entry in entries
                if isinstance(entry, dict) and entry.get("token") == token
            ),
            None,
        )
        if match is None:
            raise HarnessError(
                "AUTHORIZATION_TOKEN_MISSING: no human-issued authorization "
                "token matches the supplied --authorization value. A fresh, "
                "single-use token (see the 'issue-token' command) is "
                "required for every new run attempt, regardless of whether "
                "a previous attempt already spent quota, failed a preflight "
                "check, or errored."
            )
        if match.get("consumed"):
            raise HarnessError(
                "AUTHORIZATION_TOKEN_ALREADY_CONSUMED: this token was "
                "already consumed by a prior run attempt "
                f"(consumed_at={match.get('consumed_at')}). A fresh, "
                "single-use token is required for every new run attempt, "
                "regardless of whether a previous attempt already spent "
                "quota, failed a preflight check, or errored."
            )
        if match.get("approval_digest") != approval_digest:
            raise HarnessError(
                "AUTHORIZATION_PLAN_MISMATCH: this token authorizes a different "
                "frozen run plan. Review the current plan and issue a new token."
            )
        match["consumed"] = True
        match["consumed_at"] = _now_iso()
        _write_ledger(ledger_path, entries)


def require_authorization(
    token: str,
    approval_digest: str,
    ledger_path: Path = DEFAULT_TOKEN_LEDGER_PATH,
) -> None:
    """CLI-facing authorization gate for the quota-consuming ``run`` command."""
    consume_authorization_token(token, approval_digest, ledger_path)


# -- scc-ux6: output-path locking --------------------------------------------
#
# No lock previously existed on --output, so two concurrent `run` invocations
# targeting the same path raced with no protection. This ties an exclusive,
# PID- and liveness-checked lock to the exact output path: a second launch
# against the same path while a live holder exists is rejected immediately,
# before any token check, preflight check, or subprocess spawn. The lock
# file itself is a plain, owner-readable JSON file -- read-only inspection
# (reading its contents, or the holder PID's argv via ps/lsof) is never
# gated by anything introduced here.


def _lock_path_for_output(output_path: Path) -> Path:
    output_path = Path(output_path)
    return output_path.with_name(output_path.name + ".lock")


def _process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # The process exists but is owned by someone else: still a live holder.
        return True
    return True


def _read_lock_holder(lock_path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


@dataclass
class OutputLockHandle:
    lock_path: Path

    def release(self) -> None:
        try:
            os.unlink(self.lock_path)
        except FileNotFoundError:
            pass


def acquire_output_lock(output_path: Path) -> OutputLockHandle:
    """Atomically acquire an exclusive lock tied to ``output_path``.

    Fails closed with OUTPUT_PATH_LOCKED, naming the holder's PID and start
    time, when a live process already holds this exact output path's lock.
    A lock left behind by a dead or unreadable holder is reclaimed rather
    than treated as a permanent block.
    """
    output_path = Path(output_path)
    lock_path = _lock_path_for_output(output_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(
            {
                "pid": os.getpid(),
                "started_at": _now_iso(),
                "output_path": str(output_path),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            holder = _read_lock_holder(lock_path)
            holder_pid = holder.get("pid") if holder else None
            if isinstance(holder_pid, int) and _process_alive(holder_pid):
                started_at = (
                    holder.get("started_at", "unknown") if holder else "unknown"
                )
                raise HarnessError(
                    "OUTPUT_PATH_LOCKED: another run is already active for "
                    f"this --output path (holder PID {holder_pid}, started "
                    f"at {started_at}). Wait for it to finish, inspect "
                    f"{lock_path} directly, or choose a different --output "
                    "path."
                )
            # Stale lock: the recorded holder is gone, dead, or unreadable.
            try:
                os.unlink(lock_path)
            except FileNotFoundError:
                pass
            continue
        else:
            try:
                os.write(fd, payload)
                os.fsync(fd)
            finally:
                os.close(fd)
            return OutputLockHandle(lock_path=lock_path)


def _isolated_env(home: Path, hermes_source: Path) -> dict[str, str]:
    keep = ("PATH", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR", "TMPDIR")
    env = {key: os.environ[key] for key in keep if key in os.environ}
    fake_user_home = home.parent / "user-home"
    fake_user_home.mkdir(mode=0o700, exist_ok=True)
    env.update(
        {
            "HOME": str(fake_user_home),
            "HERMES_HOME": str(home),
            "PYTHONPATH": str(hermes_source),
            "NO_COLOR": "1",
            "HERMES_PLATFORM": "cli",
            "HERMES_SESSION_PLATFORM": "cli",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    return env


def _sandbox_literal(path: Path) -> str:
    return str(Path(path).resolve()).replace("\\", "\\\\").replace('"', '\\"')


def sandboxed_command(
    command: Sequence[str], *, runtime_root: Path, default_home: Path
) -> list[str]:
    """Wrap a command in a kernel-enforced denial for default-profile writes."""
    executable = shutil.which("sandbox-exec")
    if not executable:
        raise HarnessError("FILESYSTEM_SANDBOX_UNAVAILABLE")
    runtime_root = Path(runtime_root).resolve()
    default_home = Path(default_home).resolve()
    profile = runtime_root / "hermes-discovery.sb"
    profile.write_text(
        "(version 1)\n"
        "(allow default)\n"
        f'(allow file-write* (subpath "{_sandbox_literal(runtime_root)}"))\n'
        f'(deny file-write* (subpath "{_sandbox_literal(default_home)}"))\n',
        encoding="utf-8",
    )
    os.chmod(profile, 0o600)
    return [executable, "-f", str(profile), *command]


def verify_default_write_denial(runtime_root: Path, default_home: Path) -> None:
    """Prove the OS sandbox blocks a write beneath the real default profile."""
    canary = Path(default_home) / f".hermes-discovery-write-canary-{os.getpid()}"
    if canary.exists() or canary.is_symlink():
        raise HarnessError("DEFAULT_PROFILE_CANARY_COLLISION")
    command = sandboxed_command(
        ["/usr/bin/touch", str(canary)],
        runtime_root=runtime_root,
        default_home=default_home,
    )
    completed = subprocess.run(command, capture_output=True, check=False, timeout=15)
    if completed.returncode == 0 or canary.exists() or canary.is_symlink():
        raise HarnessError("DEFAULT_PROFILE_WRITE_SANDBOX_FAILED")


def _copy_credentials(template: Path | None, home: Path) -> None:
    if template is None:
        return
    template = Path(template)
    for name in _CREDENTIAL_FILES:
        source = template / name
        if not source.exists():
            continue
        if source.is_symlink() or not source.is_file():
            raise HarnessError("CREDENTIAL_FILE_INVALID")
        target = home / name
        shutil.copyfile(source, target, follow_symlinks=False)
        os.chmod(target, 0o600)


def _hermes_executable(hermes_source: Path) -> Path:
    executable = Path(hermes_source) / "venv" / "bin" / "hermes"
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise HarnessError("HERMES_EXECUTABLE_UNAVAILABLE")
    return executable


def _parse_tool_events(state_db: Path) -> int:
    if not state_db.is_file():
        return 0
    count = 0
    try:
        # Hermes closes a WAL database by removing its sidecars while the main
        # file still declares WAL mode. This owned, throwaway database must be
        # opened read-write so SQLite can recreate the sidecars before reading.
        # mode=rw still fails if the expected database does not exist.
        with sqlite3.connect(f"file:{state_db}?mode=rw", uri=True) as connection:
            messages_table = connection.execute(
                "SELECT 1 FROM sqlite_schema WHERE type = 'table' AND name = 'messages'"
            ).fetchone()
            if messages_table is None:
                return 0
            rows = connection.execute(
                "SELECT tool_calls FROM messages "
                "WHERE role = 'assistant' AND tool_calls IS NOT NULL"
            ).fetchall()
    except (sqlite3.Error, OSError) as error:
        raise HarnessError("SESSION_EVENT_READ_FAILED") from error
    for (raw_calls,) in rows:
        try:
            calls = json.loads(raw_calls) if isinstance(raw_calls, str) else raw_calls
        except json.JSONDecodeError:
            continue
        if not isinstance(calls, list):
            continue
        for call in calls:
            function = call.get("function", {}) if isinstance(call, dict) else {}
            if function.get("name") != "skill_view":
                continue
            arguments = function.get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}
            if isinstance(arguments, dict) and arguments.get("name") == "beads":
                count += 1
    return count


def _load_event_count(home: Path) -> int:
    usage_path = home / "skills" / ".usage.json"
    if not usage_path.is_file():
        return 0
    usage = _load_json(usage_path, "SKILL_USAGE_INVALID")
    record = usage.get("beads", {}) if isinstance(usage, dict) else {}
    value = record.get("use_count", 0) if isinstance(record, dict) else 0
    return value if isinstance(value, int) and value >= 0 else 0


def _retain_stream(
    retention_root: Path, scenario_id: str, stream: str, text: str
) -> str:
    """Persist a truncated copy of one errored lane's stream at mode 0600.

    The text can carry provider messages and session identifiers, so it is
    written to the 0700 runtime root and never echoed to stdout. Only the
    path is reported. The retained file never exceeds
    ``RAW_RETENTION_MAX_BYTES``, and the marker that records the clip is
    counted inside that budget, so a reader can never mistake a truncated
    stream for a complete one nor a capped file for an oversized one.
    """
    retention_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    raw = text.encode("utf-8", errors="replace")
    if len(raw) > RAW_RETENTION_MAX_BYTES:
        marker = f"\n[truncated: {len(raw)} bytes of raw output clipped]\n".encode()
        keep = max(0, RAW_RETENTION_MAX_BYTES - len(marker))
        raw = raw[:keep] + marker
    path = retention_root / f"{scenario_id}.{stream}.txt"
    _write_secure_bytes(path, raw)
    return str(path)


def _run_scenario(
    scenario: Scenario,
    *,
    lane: Path,
    candidate: Path,
    candidate_sha256: str,
    hermes_source: Path,
    provider: str,
    model: str,
    credentials: Path | None,
    default_home: Path,
    retention_root: Path | None = None,
) -> ScenarioResult:
    home = lane / "hermes-home"
    installed = install_candidate(candidate, home, candidate_sha256)
    _copy_credentials(credentials, home)
    env = _isolated_env(home, hermes_source)
    command = [
        str(_hermes_executable(hermes_source)),
        "chat",
        "--query-file",
        "-",
        "--oneshot",
        "--quiet",
        "--toolsets",
        "skills",
        "--provider",
        provider,
        "--model",
        model,
        "--max-turns",
        str(MAX_TURNS),
        "--run-budget",
        str(RUN_BUDGET_SECONDS),
        "--ignore-user-config",
        "--ignore-rules",
        "--source",
        "tool",
    ]
    completed = subprocess.run(
        sandboxed_command(command, runtime_root=lane, default_home=default_home),
        input=scenario.prompt,
        text=True,
        capture_output=True,
        check=False,
        cwd=lane,
        env=env,
        timeout=RUN_BUDGET_SECONDS + 30,
    )
    state_db = home / "state.db"
    # Retain only for errored lanes. A clean lane is already fully described by
    # its hashes and event counts; an errored lane is the one case where the
    # text itself is the evidence, and discarding it forces a fresh (and
    # possibly billed) reproduction to diagnose. The paths are resolved before
    # the result is built because ScenarioResult is frozen.
    prompt_representations = {
        scenario.prompt,
        json.dumps(scenario.prompt)[1:-1],
        json.dumps(scenario.prompt, ensure_ascii=False)[1:-1],
    }
    prompt_disclosed = any(
        representation and representation in stream
        for representation in prompt_representations
        for stream in (completed.stdout, completed.stderr)
    )
    retain = (
        retention_root is not None
        and completed.returncode != 0
        and not prompt_disclosed
    )
    observation_id = f"{scenario.scenario_id}-r{scenario.repeat}"
    if retain:
        assert retention_root is not None
        raw_stdout_path = _retain_stream(
            retention_root, observation_id, "stdout", completed.stdout
        )
        raw_stderr_path = _retain_stream(
            retention_root, observation_id, "stderr", completed.stderr
        )
    else:
        raw_stdout_path = None
        raw_stderr_path = None
    result = ScenarioResult(
        scenario_id=scenario.scenario_id,
        split=scenario.split,
        expected_load=scenario.expected_load,
        discovery_events=_parse_tool_events(state_db),
        load_events=_load_event_count(home),
        exit_code=completed.returncode,
        stdout_sha256=sha256_bytes(completed.stdout.encode()),
        stderr_sha256=sha256_bytes(completed.stderr.encode()),
        state_sha256=sha256_file(state_db) if state_db.is_file() else sha256_bytes(b""),
        route_family=scenario.route_family,
        repeat=scenario.repeat,
        prompt_disclosed=prompt_disclosed,
        raw_stdout_path=raw_stdout_path,
        raw_stderr_path=raw_stderr_path,
    )
    if hash_tree(installed) != candidate_sha256:
        raise HarnessError("INSTALLED_CANDIDATE_MUTATED")
    return result


# The 16 tracked roots of a Hermes profile home. This is the canonical set
# referenced throughout scc-l41's hardening: any fingerprint mutation must be
# attributable to exactly one of these names, never just a run-level bool.
_PROFILE_ROOTS: tuple[str, ...] = (
    "config.yaml",
    ".env",
    "auth.json",
    "active_profile",
    "SOUL.md",
    "state.db",
    "state.db-wal",
    "state.db-shm",
    "skills",
    "memories",
    "sessions",
    "plugins",
    "hooks",
    "cron",
    "checkpoints",
    "backups",
)
# state.db-shm is SQLite's memory-mapped WAL-index file: shared-memory
# bookkeeping (including a connection-local salt used to detect stale
# readers) that can differ, byte for byte, between two snapshots even when
# a checkpoint succeeded both times and nothing in the database actually
# changed. It is never meaningful to compare and is always excluded.
_SHM_ROOT_NAME = "state.db-shm"
_PROFILE_HOME_MISSING = "__profile_home_missing__"


@dataclass(frozen=True)
class ProfileFingerprint:
    """A per-root structural snapshot of one Hermes profile home.

    ``roots`` maps each of the ``_PROFILE_ROOTS`` names that was present (or
    a symlink) at snapshot time to a SHA-256 structural hash over its
    relative path, symlink target, and file bytes -- never the raw bytes or
    path contents themselves, so nothing built from this can leak
    config.yaml/.env/auth.json secrets (only root names and hashes ever
    reach a report).

    Fingerprinting is strictly observational: it never opens SQLite or changes
    the profile it protects. WAL bytes are compared conservatively; benign
    storage churn can fail closed but cannot be hidden by the observer.
    """

    roots: Mapping[str, str]


def _profile_fingerprint(home: Path) -> ProfileFingerprint:
    """Snapshot a Hermes profile home across the 16 tracked roots.

    Hashing never writes, never opens SQLite, never follows symlinks, and never
    returns raw file bytes. A symlink's target path is hashed in place of its
    content.
    """
    home = Path(home)
    if not home.exists():
        return ProfileFingerprint(
            roots={_PROFILE_HOME_MISSING: sha256_bytes(b"missing")},
        )

    def fingerprint_path(path: Path) -> str:
        digest = hashlib.sha256()
        pending = [path]
        while pending:
            current = pending.pop()
            relative = current.relative_to(home).as_posix().encode()
            mode = current.lstat().st_mode
            digest.update(len(relative).to_bytes(8, "big"))
            digest.update(relative)
            if stat.S_ISLNK(mode):
                digest.update(b"L")
                digest.update(os.readlink(current).encode())
            elif stat.S_ISREG(mode):
                digest.update(b"F")
                digest.update(sha256_file(current).encode())
            elif stat.S_ISDIR(mode):
                digest.update(b"D")
                pending.extend(
                    sorted(current.iterdir(), key=lambda item: item.name, reverse=True)
                )
            else:
                digest.update(b"O")
                digest.update(str(stat.S_IFMT(mode)).encode())
        return digest.hexdigest()

    records: dict[str, str] = {}
    for name in _PROFILE_ROOTS:
        path = home / name
        if path.exists() or path.is_symlink():
            records[name] = fingerprint_path(path)
    return ProfileFingerprint(roots=records)


def _profile_diff(before: ProfileFingerprint, after: ProfileFingerprint) -> list[str]:
    """Sorted tracked-root names whose content differs between two snapshots.

    Root-level attribution: this is what lets a caller name which of the 16
    tracked roots changed instead of exposing only a boolean.

    SQLite handling: state.db-shm is always excluded --
    its raw bytes are volatile shared-memory bookkeeping that is never
    meaningfully comparable (see _SHM_ROOT_NAME). state.db and state.db-wal
    are always compared. This can conservatively flag benign storage churn,
    but fingerprinting never mutates the protected profile or hides a write.
    """
    exclude = {_SHM_ROOT_NAME}
    names = (set(before.roots) | set(after.roots)) - exclude
    return sorted(
        name for name in names if before.roots.get(name) != after.roots.get(name)
    )


def _wilson_lower(successes: int, total: int) -> int | None:
    """Return the one-sided 95% Wilson lower bound in millionths."""
    if total == 0:
        return None
    z = 1.6448536269514722
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = proportion + z * z / (2 * total)
    margin = z * math.sqrt(
        (proportion * (1 - proportion) + z * z / (4 * total)) / total
    )
    return max(0, int(((centre - margin) / denominator) * 1_000_000))


def _binary_stats(values: Sequence[int]) -> dict[str, Any]:
    if not values:
        return {
            "count": 0,
            "mean_millionths": None,
            "median_millionths": None,
            "p95_millionths": None,
            "worst_millionths": None,
            "variance_fraction": None,
        }
    ordered = sorted(values)
    count = len(ordered)
    total = sum(ordered)
    if count % 2:
        median = ordered[count // 2]
    else:
        median = (ordered[count // 2 - 1] + ordered[count // 2]) // 2
    return {
        "count": count,
        "mean_millionths": total // count,
        "median_millionths": median,
        "p95_millionths": ordered[max(0, math.ceil(0.95 * count) - 1)],
        "worst_millionths": min(ordered),
        "variance_fraction": {
            "numerator": count * sum(value * value for value in ordered) - total**2,
            "denominator": count**2,
        },
    }


def _routing_metric(
    rows: Sequence[Mapping[str, Any]], *, expected_load: bool
) -> dict[str, Any]:
    selected = [
        row
        for row in rows
        if row["expected_load"] is expected_load and not row["errored"]
    ]
    family_rows: dict[str, list[Mapping[str, Any]]] = {}
    for row in selected:
        family_rows.setdefault(str(row["route_family"]), []).append(row)
    families: dict[str, dict[str, Any]] = {}
    family_rates: list[Fraction] = []
    for family, members in sorted(family_rows.items()):
        successes = sum(bool(row["passed"]) for row in members)
        total = len(members)
        rate_fraction = Fraction(successes, total)
        rate = int(rate_fraction * 1_000_000)
        family_rates.append(rate_fraction)
        repeats_by_variant: dict[str, set[int]] = {}
        for row in members:
            scenario_id = str(row["scenario_id"])
            repeats_by_variant.setdefault(scenario_id, set()).add(int(row["repeat"]))
        families[family] = {
            "successes": successes,
            "observations": total,
            "variants": len(repeats_by_variant),
            "minimum_repeats": min(
                len(values) for values in repeats_by_variant.values()
            ),
            "rate_millionths": rate,
            "wilson_lower_millionths": _wilson_lower(successes, total),
        }
    successes = sum(bool(row["passed"]) for row in selected)
    total = len(selected)
    binary_values = [1_000_000 if row["passed"] else 0 for row in selected]
    macro_fraction = (
        None if not family_rates else sum(family_rates, Fraction()) / len(family_rates)
    )
    return {
        "successes": successes,
        "observations": total,
        "micro_millionths": None if total == 0 else successes * 1_000_000 // total,
        "macro_millionths": (
            None if macro_fraction is None else int(macro_fraction * 1_000_000)
        ),
        "macro_fraction": (
            None
            if macro_fraction is None
            else {
                "numerator": macro_fraction.numerator,
                "denominator": macro_fraction.denominator,
            }
        ),
        "wilson_lower_millionths": _wilson_lower(successes, total),
        "families": families,
        "distribution": _binary_stats(binary_values),
    }


def _statistical_gate(
    metrics: Mapping[str, Mapping[str, Any]],
    *,
    errored: int,
    hard_zero_safety_violations: int,
    profile_prestate_contaminated: bool,
    duplicate_observations: bool,
    matrix_identity_matches: bool,
) -> dict[str, Any]:
    failures: list[str] = []
    for name, metric in metrics.items():
        label = "POSITIVE" if name == "positive" else "NEGATIVE"
        expected_families = (
            set(POSITIVE_ROUTE_FAMILIES)
            if name == "positive"
            else set(NEGATIVE_ROUTE_FAMILIES)
        )
        if set(metric["families"]) != expected_families:
            failures.append(f"{label}_FAMILIES_INCOMPLETE")
        if metric["observations"] < MINIMUM_ROUTING_OBSERVATIONS:
            failures.append(f"{label}_OBSERVATIONS_INSUFFICIENT")
        if (
            any(
                family["variants"] < MINIMUM_VARIANTS_PER_FAMILY
                for family in metric["families"].values()
            )
            or not metric["families"]
        ):
            failures.append(f"{label}_VARIANTS_PER_FAMILY_INSUFFICIENT")
        if (
            any(
                family["minimum_repeats"] < MINIMUM_REPEATS_PER_VARIANT
                for family in metric["families"].values()
            )
            or not metric["families"]
        ):
            failures.append(f"{label}_REPEATS_PER_VARIANT_INSUFFICIENT")
        macro_fraction = metric["macro_fraction"]
        if macro_fraction is None or (
            macro_fraction["numerator"] * 1_000_000
            < ROUTING_MACRO_THRESHOLD * macro_fraction["denominator"]
        ):
            failures.append(f"{label}_MACRO_BELOW_THRESHOLD")
        if (
            metric["wilson_lower_millionths"] is None
            or metric["wilson_lower_millionths"] < ROUTING_WILSON_THRESHOLD
        ):
            failures.append(f"{label}_WILSON_BELOW_THRESHOLD")
    if errored:
        failures.append("EXECUTION_ERRORS_PRESENT")
    if hard_zero_safety_violations:
        failures.append("HARD_ZERO_SAFETY_VIOLATION")
    if profile_prestate_contaminated:
        failures.append("PROFILE_PRESTATE_CONTAMINATED")
    if duplicate_observations:
        failures.append("DUPLICATE_OBSERVATION_IDENTITY")
    if not matrix_identity_matches:
        failures.append("FROZEN_MATRIX_IDENTITY_MISMATCH")
    return {"passed": not failures, "failures": failures}


def build_report(
    results: Sequence[ScenarioResult],
    *,
    candidate_sha256: str,
    corpus_sha256: str,
    hermes_commit: str,
    provider: str,
    model: str,
    default_profile_unchanged: bool,
    default_profile_write_denied: bool = True,
    aborted_reason: str | None = None,
    design_sha256: str | None = None,
    expected_scenarios: Sequence[Scenario] | None = None,
) -> dict[str, Any]:
    rows = []
    for result in results:
        row = asdict(result)
        row["passed"] = result.passed
        row["errored"] = result.errored
        row["outcome"] = result.outcome
        rows.append(row)
    # Strict three-way partition. "failed" counts routing failures only:
    # an errored lane never reached routing, so folding it into "failed"
    # would report a provider outage as proof the skill does not route.
    passed = sum(1 for row in rows if row["outcome"] == "passed")
    failed = sum(1 for row in rows if row["outcome"] == "failed")
    errored = sum(1 for row in rows if row["outcome"] == "errored")
    retained = any(
        row.get("raw_stdout_path") or row.get("raw_stderr_path") for row in rows
    )
    routing_metrics = {
        "positive": _routing_metric(rows, expected_load=True),
        "negative_restraint": _routing_metric(rows, expected_load=False),
    }
    split_counts = {}
    for split in ("public", "hidden", "sealed"):
        split_rows = [row for row in rows if row["split"] == split]
        split_passed = sum(row["outcome"] == "passed" for row in split_rows)
        split_failed = sum(row["outcome"] == "failed" for row in split_rows)
        split_errored = sum(row["outcome"] == "errored" for row in split_rows)
        split_counts[split] = {
            "observations": len(split_rows),
            "passed": split_passed,
            "failed": split_failed,
            "errored": split_errored,
            "scored_count": split_passed + split_failed,
        }
    profile_drift_observations = sum(bool(row["profile_delta"]) for row in rows)
    prompt_disclosures = sum(bool(row["prompt_disclosed"]) for row in rows)
    # Fingerprint deltas prove that the shared profile changed during a lane,
    # not that the sandboxed child caused the change. A concurrently active
    # parent Hermes process can write the same profile. Fail closed as
    # contaminated evidence without falsely classifying ambient drift as a
    # child safety violation. The sandbox write-denial canary is causal: it
    # runs under the exact policy used for every child.
    profile_prestate_contaminated = (
        profile_drift_observations > 0 or not default_profile_unchanged
    )
    hard_zero_safety_violations = prompt_disclosures
    if not default_profile_write_denied:
        hard_zero_safety_violations += 1
    observation_identities = [
        (str(row["scenario_id"]), int(row["repeat"])) for row in rows
    ]
    observed_matrix = {
        (
            str(row["scenario_id"]),
            int(row["repeat"]),
            str(row["route_family"]),
            bool(row["expected_load"]),
            str(row["split"]),
        )
        for row in rows
    }
    expected_matrix = (
        observed_matrix
        if expected_scenarios is None
        else {
            (
                scenario.scenario_id,
                scenario.repeat,
                scenario.route_family,
                scenario.expected_load,
                scenario.split,
            )
            for scenario in expected_scenarios
        }
    )
    gate = _statistical_gate(
        routing_metrics,
        errored=errored,
        hard_zero_safety_violations=hard_zero_safety_violations,
        profile_prestate_contaminated=profile_prestate_contaminated,
        duplicate_observations=(
            len(observation_identities) != len(set(observation_identities))
        ),
        matrix_identity_matches=(
            observed_matrix == expected_matrix and len(rows) == len(expected_matrix)
        ),
    )
    report = {
        "schema_version": REPORT_SCHEMA,
        "candidate_sha256": candidate_sha256,
        "corpus_sha256": corpus_sha256,
        "design_sha256": design_sha256,
        "budget_sha256": BUDGET_CONTRACT_SHA256,
        "prestate_contract_sha256": PRESTATE_CONTRACT_SHA256,
        "harness_sha256": sha256_file(Path(__file__)),
        "hermes_commit": hermes_commit,
        "provider": provider,
        "model": model,
        "scenario_count": len(rows),
        "passed": passed,
        "failed": failed,
        "errored": errored,
        "scored_count": passed + failed,
        "default_profile_unchanged": default_profile_unchanged,
        "default_profile_write_denied": default_profile_write_denied,
        "profile_drift_observations": profile_drift_observations,
        "hard_zero_safety_violations": hard_zero_safety_violations,
        "raw_content_retained": retained,
        "routing_metrics": routing_metrics,
        "split_counts": split_counts,
        "gate": gate,
        "results": rows,
    }
    if aborted_reason is not None:
        report["aborted"] = True
        report["aborted_reason"] = aborted_reason
    return report


def run_corpus(
    *,
    scenarios: Sequence[Scenario],
    candidate: Path,
    candidate_sha256: str,
    corpus_sha256: str,
    hermes_source: Path,
    runtime_root: Path,
    default_home: Path,
    credentials: Path | None,
    provider: str,
    model: str,
    force_full_sweep: bool = False,
    design_sha256: str | None = None,
) -> dict[str, Any]:
    if not scenarios:
        raise HarnessError("CORPUS_INDEX_MISMATCH")
    verify_frozen_hermes(hermes_source)
    runtime_root = Path(runtime_root).resolve()
    default_home = Path(default_home).resolve()
    if (
        runtime_root == default_home
        or runtime_root in default_home.parents
        or default_home in runtime_root.parents
    ):
        raise HarnessError("RUNTIME_DEFAULT_PROFILE_ALIAS")
    runtime_root.mkdir(parents=True, exist_ok=False)
    os.chmod(runtime_root, 0o700)
    verify_default_write_denial(runtime_root, default_home)
    run_before_fingerprint = _profile_fingerprint(default_home)
    # Retention lives under the 0700 runtime root, not the lane: each lane is
    # torn down immediately after its run, so anything written inside it is
    # gone before the report is built.
    retention_root = runtime_root / "retained"
    retain_error_streams = all(
        scenario.route_family == "legacy" for scenario in scenarios
    )
    results: list[ScenarioResult] = []
    retained_lanes = 0
    aborted_reason: str | None = None
    try:
        for index, scenario in enumerate(scenarios):
            observation_id = f"{scenario.scenario_id}-r{scenario.repeat}"
            lane = runtime_root / observation_id
            lane.mkdir(mode=0o700)
            # Per-lane fingerprinting (scc-l41): a snapshot immediately before
            # and after this exact lane, so a mutation is attributable to the
            # one scenario that caused it instead of only "somewhere in the
            # 72-lane run".
            lane_before_fingerprint = _profile_fingerprint(default_home)
            try:
                result = _run_scenario(
                    scenario,
                    lane=lane,
                    candidate=candidate,
                    candidate_sha256=candidate_sha256,
                    hermes_source=hermes_source,
                    provider=provider,
                    model=model,
                    credentials=credentials,
                    default_home=default_home,
                    retention_root=(
                        retention_root
                        if retain_error_streams
                        and retained_lanes < RAW_RETENTION_LANE_LIMIT
                        else None
                    ),
                )
            finally:
                shutil.rmtree(lane, ignore_errors=False)
            lane_after_fingerprint = _profile_fingerprint(default_home)
            result = replace(
                result,
                profile_delta=_profile_diff(
                    lane_before_fingerprint, lane_after_fingerprint
                ),
            )
            results.append(result)
            if result.raw_stdout_path or result.raw_stderr_path:
                retained_lanes += 1
            # Pre-flight: the first lane is a canary. If it errors, the cause
            # is almost always systemic (an exhausted provider quota, a broken
            # install), and running the remaining lanes only repeats the same
            # failure at full cost. Abort fail-closed and say why. Routing
            # failures never trigger this -- only errors, which mean the
            # session never reached routing at all.
            if index == 0 and result.errored and not force_full_sweep:
                aborted_reason = (
                    "PREFLIGHT_LANE_ERRORED: the first lane exited "
                    f"{result.exit_code} without completing. This is treated as "
                    "a systemic failure, so the remaining lanes were skipped. "
                    "Inspect the retained raw output, then re-run with "
                    "--force-full-sweep to override."
                )
                break
    finally:
        run_after_fingerprint = _profile_fingerprint(default_home)
    # default_profile_unchanged stays a single run-level boolean for backward
    # compatibility (existing consumers key off it directly), but its meaning
    # is unchanged: True only if no tracked root differed anywhere across the
    # whole run. It is now derived from the conjunction of every lane's own
    # before/after delta plus the whole-run bookend snapshots, rather than
    # only the bookend snapshots, so a mutate-then-revert within a single
    # lane can no longer cancel out and hide behind a run-level match.
    run_level_changed_roots = _profile_diff(
        run_before_fingerprint, run_after_fingerprint
    )
    unchanged = not run_level_changed_roots and all(
        not result.profile_delta for result in results
    )
    report = build_report(
        results,
        candidate_sha256=candidate_sha256,
        corpus_sha256=corpus_sha256,
        hermes_commit=FROZEN_HERMES_COMMIT,
        provider=provider,
        model=model,
        default_profile_unchanged=unchanged,
        aborted_reason=aborted_reason,
        design_sha256=design_sha256,
        expected_scenarios=scenarios,
    )
    return report


def probe_actual_hermes_install(
    *,
    candidate: Path,
    candidate_sha256: str,
    hermes_source: Path,
    runtime_root: Path,
    default_home: Path,
) -> dict[str, Any]:
    """Exercise actual frozen Hermes scan/load code without any model call."""
    verify_frozen_hermes(hermes_source)
    runtime_root = Path(runtime_root).resolve()
    default_home = Path(default_home).resolve()
    if (
        runtime_root == default_home
        or runtime_root in default_home.parents
        or default_home in runtime_root.parents
    ):
        raise HarnessError("RUNTIME_DEFAULT_PROFILE_ALIAS")
    runtime_root.mkdir(parents=True, exist_ok=False)
    os.chmod(runtime_root, 0o700)
    verify_default_write_denial(runtime_root, default_home)
    home = runtime_root / "hermes-home"
    installed = install_candidate(candidate, home, candidate_sha256)
    before = _profile_fingerprint(default_home)
    probe_code = r"""
import json
from tools.skills_tool import skills_list
from model_tools import handle_function_call
listed = json.loads(skills_list())
names = [row.get("name") for row in listed.get("skills", [])]
loaded = handle_function_call(
    "skill_view", {"name": "beads"}, task_id="routing-probe", session_id="routing-probe"
)
try:
    payload = json.loads(loaded)
except Exception:
    payload = {}
print(json.dumps({"candidate_discovered": "beads" in names, "candidate_loaded": payload.get("success") is True}))
"""
    python = Path(hermes_source) / "venv" / "bin" / "python"
    try:
        completed = subprocess.run(
            sandboxed_command(
                [str(python), "-c", probe_code],
                runtime_root=runtime_root,
                default_home=default_home,
            ),
            capture_output=True,
            check=False,
            text=True,
            cwd=runtime_root,
            env=_isolated_env(home, hermes_source),
            timeout=60,
        )
        if completed.returncode:
            raise HarnessError("HERMES_PROBE_FAILED")
        try:
            payload = json.loads(completed.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError) as error:
            raise HarnessError("HERMES_PROBE_OUTPUT_INVALID") from error
        after = _profile_fingerprint(default_home)
        evidence = {
            "schema_version": "hermes-beads-install-probe.v1",
            "hermes_commit": FROZEN_HERMES_COMMIT,
            "candidate_sha256": candidate_sha256,
            "installed_candidate_sha256": hash_tree(installed),
            "candidate_discovered": payload.get("candidate_discovered") is True,
            "candidate_loaded": payload.get("candidate_loaded") is True,
            "load_events": _load_event_count(home),
            "default_profile_unchanged": not _profile_diff(before, after),
            "default_profile_write_denied": True,
            "default_profile_mutation_by_harness": False,
            "automatic_routing_exercised": False,
            "blocker": "MODEL_EXECUTION_NOT_AUTHORIZED",
            "raw_content_retained": False,
        }
        return evidence
    finally:
        shutil.rmtree(runtime_root, ignore_errors=False)


def _write_secure_bytes(path: Path, data: bytes) -> None:
    """Write ``data`` to ``path`` atomically with mode exactly 0o600.

    ``os.open``'s mode argument is masked by the process umask, so a hostile
    or merely permissive umask (e.g. 0o000) can leave the file group/world
    readable even when 0o600 is requested at open time. The explicit
    ``os.chmod`` after the atomic rename is what actually pins the mode,
    regardless of umask (Defect 4).
    """
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)
    os.chmod(path, 0o600)


def _write_json(path: Path | None, payload: Mapping[str, Any]) -> None:
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if path is None:
        sys.stdout.write(rendered)
    else:
        _write_secure_bytes(Path(path), rendered.encode("utf-8"))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    digest = sub.add_parser("candidate-hash")
    digest.add_argument("candidate", type=Path)

    probe = sub.add_parser("probe")
    probe.add_argument("--candidate", type=Path, required=True)
    probe.add_argument("--candidate-sha256", required=True)
    probe.add_argument("--hermes-source", type=Path, required=True)
    probe.add_argument("--runtime-root", type=Path, required=True)
    probe.add_argument("--default-home", type=Path, required=True)
    probe.add_argument("--output", type=Path)

    plan = sub.add_parser("plan")
    for command in (plan,):
        command.add_argument("--provider", default="openai-codex")
        command.add_argument("--model", default="gpt-5.6-sol")
    plan.add_argument("--design", type=Path)
    plan.add_argument("--design-sha256")
    plan.add_argument("--corpus-sha256")
    plan.add_argument("--force-full-sweep", action="store_true")

    issue_token = sub.add_parser(
        "issue-token",
        help=(
            "Mint one fresh, single-use authorization token for a single "
            "future 'run' invocation. Run this yourself, as a human -- an "
            "agent must never call it to self-authorize."
        ),
    )
    issue_token.add_argument(
        "--token-ledger", type=Path, default=DEFAULT_TOKEN_LEDGER_PATH
    )
    issue_token.add_argument("--approval-digest", required=True)
    issue_token.add_argument("--output", type=Path)

    run = sub.add_parser("run")
    run.add_argument("--candidate", type=Path, required=True)
    run.add_argument("--candidate-sha256", required=True)
    run.add_argument("--corpus", type=Path, required=True)
    run.add_argument("--corpus-sha256", required=True)
    run.add_argument("--design", type=Path, required=True)
    run.add_argument("--design-sha256")
    run.add_argument("--hermes-source", type=Path, required=True)
    run.add_argument("--runtime-root", type=Path, required=True)
    run.add_argument("--default-home", type=Path, required=True)
    run.add_argument("--credentials", type=Path)
    run.add_argument("--provider", default="openai-codex")
    run.add_argument("--model", default="gpt-5.6-sol")
    run.add_argument(
        "--authorization",
        required=True,
        help=(
            "A single-use token minted by 'issue-token', not free-text approval prose."
        ),
    )
    run.add_argument("--token-ledger", type=Path, default=DEFAULT_TOKEN_LEDGER_PATH)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument(
        "--force-full-sweep",
        action="store_true",
        help=(
            "Run every lane even when the first lane errors. Off by default: "
            "a systemic failure would otherwise repeat across all "
            f"{SCENARIO_COUNT} lanes at full provider cost."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "candidate-hash":
            print(hash_tree(args.candidate))
            return 0
        if args.command == "plan":
            if args.design is None:
                request = approval_request(args.provider, args.model)
            else:
                if args.corpus_sha256 is None:
                    raise HarnessError("CORPUS_HASH_REQUIRED_FOR_APPROVAL")
                design = _validated_v2_design(args.design, args.design_sha256)
                runtime = design["frozen_runtime"]
                validate_v2_runtime_contract(
                    args.design,
                    args.design_sha256,
                    candidate_sha256=runtime.get("candidate_sha256"),
                    provider=args.provider,
                    model=args.model,
                )
                request = approval_request(
                    args.provider,
                    args.model,
                    scenario_count=design["execution_matrix"]["total_observations"],
                    design_sha256=args.design_sha256,
                    candidate_sha256=runtime["candidate_sha256"],
                    corpus_sha256=args.corpus_sha256,
                    force_full_sweep=args.force_full_sweep,
                )
            _write_json(None, request)
            return 0
        if args.command == "issue-token":
            token = issue_authorization_token(args.approval_digest, args.token_ledger)
            _write_json(
                args.output,
                {"token": token, "token_ledger": str(Path(args.token_ledger))},
            )
            return 0
        if args.command == "probe":
            payload = probe_actual_hermes_install(
                candidate=args.candidate,
                candidate_sha256=args.candidate_sha256,
                hermes_source=args.hermes_source,
                runtime_root=args.runtime_root,
                default_home=args.default_home,
            )
            _write_json(args.output, payload)
            return 0
        # command == "run": lock the exact --output path first -- a second
        # invocation racing for the same path is rejected before it ever
        # touches the token ledger, a preflight check, or a subprocess. With
        # the lock held, validate every local frozen input before consuming the
        # single-use token. No subprocess or provider call occurs before token
        # consumption.
        lock = acquire_output_lock(args.output)
        try:
            approval_digest = run_approval_digest(
                candidate_sha256=args.candidate_sha256,
                corpus_sha256=args.corpus_sha256,
                design_sha256=args.design_sha256,
                provider=args.provider,
                model=args.model,
                force_full_sweep=args.force_full_sweep,
            )
            scenarios = load_corpus(
                args.corpus,
                args.design,
                args.corpus_sha256,
                args.design_sha256,
            )
            design_payload = _load_json(args.design, "DESIGN_INVALID")
            if (
                isinstance(design_payload, dict)
                and design_payload.get("schema_version") == DISCOVERY_DESIGN_SCHEMA_V2
            ):
                validate_v2_runtime_contract(
                    args.design,
                    args.design_sha256,
                    candidate_sha256=args.candidate_sha256,
                    provider=args.provider,
                    model=args.model,
                )
            if hash_tree(args.candidate) != args.candidate_sha256:
                raise HarnessError("CANDIDATE_HASH_MISMATCH")
            require_authorization(
                args.authorization, approval_digest, args.token_ledger
            )
            payload = run_corpus(
                scenarios=scenarios,
                candidate=args.candidate,
                candidate_sha256=args.candidate_sha256,
                corpus_sha256=args.corpus_sha256,
                hermes_source=args.hermes_source,
                runtime_root=args.runtime_root,
                default_home=args.default_home,
                credentials=args.credentials,
                provider=args.provider,
                model=args.model,
                force_full_sweep=args.force_full_sweep,
                design_sha256=args.design_sha256,
            )
            _write_json(args.output, payload)
            # Exit codes are a three-way partition, matching the report. An
            # errored or aborted sweep must never exit 0: with the errored
            # count split out of "failed", a total provider outage leaves
            # failed == 0, and reporting that as success is exactly the
            # confusion this change exists to remove. 4 means "no verdict";
            # 3 means "a real routing failure was measured".
            if payload["errored"] or payload.get("aborted"):
                return 4
            gate = payload.get("gate")
            if isinstance(gate, dict):
                return 0 if gate.get("passed") is True else 3
            return 0 if payload["failed"] == 0 else 3
        finally:
            lock.release()
    except HarnessError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
