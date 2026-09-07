"""Real-repository and bounded-process helpers for T16 conformance tests."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "scripts" / "tests" / "fixtures" / "beads_swarm"
INTEGRATION_COMMON = ROOT / "scripts" / "tests" / "beads_integration" / "_common.py"
WORKER = Path(__file__).with_name("worker_process.py")
PYTHON = sys.executable
RUN_ID = "run-0123456789abcdef-20260906T120000.000000Z-AAAAAAAD"
DEFAULT_OUTPUT_LIMIT = 4096


def _drain_bounded(stream: Any, sink: bytearray, limit: int) -> None:
    """Continuously drain a child pipe while retaining at most ``limit`` bytes."""
    while chunk := stream.read(65536):
        remaining = limit - len(sink)
        if remaining > 0:
            sink.extend(chunk[:remaining])


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


integration = _load(INTEGRATION_COMMON, "beads_swarm_integration_common")


def fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def git(cwd: Path, *args: str) -> str:
    return integration.run_git(cwd, *args).stdout.decode().strip()


def setup_swarm(tmp_path: Path, lane_specs: list[dict[str, Any]]) -> dict[str, Any]:
    """Create one primary plus one distinct linked worktree per lane."""
    modules = integration.modules()
    factory = integration.factory()
    repo, first_lane, _old_head = factory._git_lane(tmp_path)
    (repo / ".gitignore").write_text(
        ".hermes/\nlane/\nlane-*/\nsensitive-values.json\nsnapshot.json\n",
        encoding="utf-8",
    )
    integration.run_git(repo, "add", ".gitignore")
    integration.run_git(repo, "commit", "-m", "ignore conformance artifacts")
    integration.run_git(first_lane, "merge", "--ff-only", "main")
    head = git(repo, "rev-parse", "HEAD")
    run = integration.make_run(
        modules,
        repo,
        RUN_ID,
        [spec["issue_id"] for spec in lane_specs],
    )
    lanes: dict[str, dict[str, Any]] = {}
    for index, spec in enumerate(lane_specs):
        worktree = first_lane if index == 0 else repo / f"lane-{index}"
        if index:
            integration.run_git(
                repo,
                "worktree",
                "add",
                "-q",
                str(worktree),
                "-b",
                f"lane-{index}",
            )
        outbox = worktree / "outbox"
        packet = integration.lane_packet(
            factory,
            tmp_path,
            issue_id=spec["issue_id"],
            run_id=RUN_ID,
            worktree=worktree,
            outbox=outbox,
            head=head,
            allowed=[spec.get("allowed", "src/**")],
        )
        packet["delegation"] = {"allowed": False, "max_child_depth": 0}
        packet_path = tmp_path / f"packet-{index}.json"
        raw = json.dumps(packet, sort_keys=True, separators=(",", ":")).encode()
        packet_path.write_bytes(raw)
        sensitive = tmp_path / f"sensitive-{index}.json"
        sensitive.write_text("[]", encoding="utf-8")
        sensitive.chmod(0o600)
        lanes[spec["issue_id"]] = {
            "spec": spec,
            "worktree": worktree,
            "outbox": outbox,
            "packet": packet,
            "packet_path": packet_path,
            "packet_sha256": hashlib.sha256(raw).hexdigest(),
            "epoch": run["epochs"][spec["issue_id"]],
            "sensitive": sensitive,
        }
    return {
        "modules": modules,
        "repo": repo,
        "head": head,
        "run": run,
        "lanes": lanes,
    }


def run_children(
    swarm: dict[str, Any],
    *,
    behaviors: dict[str, str] | None = None,
    epoch_offsets: dict[str, int] | None = None,
    timeout: int = 30,
    output_limit: int = DEFAULT_OUTPUT_LIMIT,
) -> dict[str, subprocess.CompletedProcess[str]]:
    """Launch all lanes under one deadline and bounded file-backed output."""
    behaviors = behaviors or {}
    epoch_offsets = epoch_offsets or {}
    processes: dict[str, subprocess.Popen[bytes]] = {}
    outputs: dict[str, tuple[bytearray, bytearray]] = {}
    readers: dict[str, tuple[threading.Thread, threading.Thread]] = {}
    deadline = time.monotonic() + timeout
    results: dict[str, subprocess.CompletedProcess[str]] = {}
    try:
        for issue_id, lane in swarm["lanes"].items():
            spec = lane["spec"]
            job = {
                "packet_path": str(lane["packet_path"]),
                "ownership_epoch": lane["epoch"] + epoch_offsets.get(issue_id, 0),
                "sensitive_values_file": str(lane["sensitive"]),
                "changed_path": spec.get("path", f"src/{issue_id}.py"),
                "content": spec.get("content", f"VALUE = {issue_id!r}\n"),
                "behavior": behaviors.get(issue_id, spec.get("outcome", "completed")),
            }
            job_path = lane["packet_path"].with_name(f"job-{issue_id}.json")
            job_path.write_text(json.dumps(job), encoding="utf-8")
            process = subprocess.Popen(
                [PYTHON, str(WORKER), str(job_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            assert process.stdout is not None and process.stderr is not None
            stdout = bytearray()
            stderr = bytearray()
            stdout_reader = threading.Thread(
                target=_drain_bounded,
                args=(process.stdout, stdout, output_limit),
                daemon=True,
            )
            stderr_reader = threading.Thread(
                target=_drain_bounded,
                args=(process.stderr, stderr, output_limit),
                daemon=True,
            )
            outputs[issue_id] = (stdout, stderr)
            readers[issue_id] = (stdout_reader, stderr_reader)
            processes[issue_id] = process
            stdout_reader.start()
            stderr_reader.start()
        for issue_id, process in processes.items():
            remaining = max(0.0, deadline - time.monotonic())
            process.wait(timeout=remaining)
            for reader in readers[issue_id]:
                reader.join(timeout=max(0.0, deadline + 0.5 - time.monotonic()))
            stdout_bytes, stderr_bytes = outputs[issue_id]
            stdout = bytes(stdout_bytes).decode("utf-8", errors="replace")
            stderr = bytes(stderr_bytes).decode("utf-8", errors="replace")
            results[issue_id] = subprocess.CompletedProcess(
                process.args, process.returncode, stdout, stderr
            )
    finally:
        cleanup_deadline = deadline + 0.5
        terminate_deadline = min(cleanup_deadline, time.monotonic() + 0.25)
        live = [process for process in processes.values() if process.poll() is None]
        for process in live:
            try:
                process.terminate()
            except ProcessLookupError:
                pass
        for process in live:
            try:
                process.wait(timeout=max(0.0, terminate_deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
        for process in live:
            if process.poll() is None:
                remaining = max(0.0, cleanup_deadline - time.monotonic())
                try:
                    process.wait(timeout=remaining)
                except subprocess.TimeoutExpired:
                    pass
        for pair in readers.values():
            for reader in pair:
                reader.join(timeout=max(0.0, cleanup_deadline - time.monotonic()))
        for process in processes.values():
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()
    return results


def import_lane(swarm: dict[str, Any], issue_id: str) -> str:
    """Copy an untrusted outbox into the parent import boundary."""
    lane = swarm["lanes"][issue_id]
    outbox = lane["outbox"]
    imports = (
        swarm["run"]["run_directory"]
        / "imports"
        / swarm["modules"].coordinator_state.issue_key(issue_id)
    )
    swarm["modules"].coordinator_state.ensure_owner_directory(
        imports, root=swarm["run"]["run_directory"]
    )
    for name, source in (
        ("packet.json", lane["packet_path"]),
        ("result.json", outbox / "result.json"),
        ("receipt.json", outbox / "receipt.json"),
    ):
        target = imports / name
        shutil.copyfile(source, target)
        target.chmod(0o600)
    return hashlib.sha256((outbox / "result.json").read_bytes()).hexdigest()


def checkpoint(swarm: dict[str, Any], result_shas: Mapping[str, str | None]) -> None:
    entries = {
        issue_id: integration.issue_entry(
            swarm["modules"],
            epoch=lane["epoch"],
            result_sha=result_shas.get(issue_id),
            packet_sha=lane["packet_sha256"],
        )
        for issue_id, lane in swarm["lanes"].items()
    }
    swarm["run"]["finish"](entries)
    swarm["context"] = swarm["modules"].coordinator_integration.open_run(
        swarm["run"]["run_directory"]
    )


def freeze_and_verify(swarm: dict[str, Any], issue_id: str, result_sha: str) -> str:
    ci = swarm["modules"].coordinator_integration
    frozen = ci.freeze_lane(
        swarm["context"], issue_id, expected_result_sha256=result_sha
    )
    assert frozen["status"] == "success"
    verified = ci.verify_lane(swarm["context"], issue_id)
    assert verified["status"] in {"success", "partial"}
    if verified["status"] == "partial":
        review = integration.reviewer_record(
            run_id=RUN_ID,
            target_kind="lane_freeze",
            target_sha256=frozen["freeze_sha256"],
            reviewer_id=f"reviewer-{issue_id}",
            implementer_ids=[f"worker-{issue_id}"],
        )
        review_path = integration.write_review(
            swarm["modules"], swarm["run"]["run_directory"], review
        )
        reviewed = ci.record_review(swarm["context"], issue_id, review_path)
        assert reviewed["status"] == "success"
    return frozen["freeze_sha256"]
