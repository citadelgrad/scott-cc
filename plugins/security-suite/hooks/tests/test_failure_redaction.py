"""Tests for plugins/security-suite/hooks/failure_redaction.py.

scc-ncs.24: SkillOpt-Sleep's input corpus now includes failure transcripts
(circuit-breaker escalations, bd human-flagged failures), not just
successful sessions. Before any derived summary of a failure transcript is
persisted into the committed learned-preferences file, it must pass through
redact_transcript(). These tests cover the two required behaviors:

  * a clean failure transcript (no detectable secret) is returned byte-for-
    byte unchanged, so it remains eligible for inclusion (AC #3).
  * a failure transcript containing a detected secret pattern is redacted
    such that the persisted/returned text contains zero occurrences of the
    raw matched value (AC #4).

Imported directly (unlike the subprocess-based test_secret_scan.py) since
failure_redaction exposes a plain function contract for library callers,
not a stdin/stdout hook contract.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from failure_redaction import has_secret, redact_transcript  # noqa: E402

# Synthetic/fake secret-shaped values only — never real credentials.
# Built from parts so this fixture doesn't itself trip gitleaks at commit
# time, matching the convention in test_secret_scan.py.
FAKE_AWS_KEY = "AKIA" + "QWERTYUIOPASDFGH"
FAKE_GITHUB_TOKEN = "ghp_" + "a" * 40
FAKE_GENERIC_SECRET = "sup3rSecretTokenValue1234567890"

CLEAN_FAILURE_TRANSCRIPT = """\
circuit-breaker: escalation after 3 consecutive gate failures
gate: cargo-test
run: cargo test --workspace
exit_code: 101
stderr: thread 'main' panicked at 'assertion failed: left == right'
decision: needs_human
"""


def test_clean_failure_transcript_has_no_secret():
    assert has_secret(CLEAN_FAILURE_TRANSCRIPT) is False


def test_clean_failure_transcript_is_returned_unchanged():
    safe_text, findings = redact_transcript(CLEAN_FAILURE_TRANSCRIPT)

    assert safe_text == CLEAN_FAILURE_TRANSCRIPT
    assert findings == []


def test_bd_human_flagged_failure_with_aws_key_is_detected():
    transcript = (
        "bd: issue scc-ncs.99 flagged needs_human\n"
        f"agent transcript excerpt: export AWS_ACCESS_KEY_ID={FAKE_AWS_KEY}\n"
        "human note: rotate the leaked key before retrying\n"
    )

    assert has_secret(transcript) is True


def test_aws_key_is_redacted_with_zero_occurrences_of_raw_value():
    transcript = f"circuit-breaker escalation log:\nAWS_KEY = '{FAKE_AWS_KEY}'\n"

    safe_text, findings = redact_transcript(transcript)

    assert FAKE_AWS_KEY not in safe_text
    assert len(findings) == 1
    assert findings[0][0] == "aws-access-key-id"
    assert "[REDACTED:aws-access-key-id]" in safe_text


def test_github_token_is_redacted_with_zero_occurrences_of_raw_value():
    transcript = f"failed gh api call using token {FAKE_GITHUB_TOKEN}\n"

    safe_text, findings = redact_transcript(transcript)

    assert FAKE_GITHUB_TOKEN not in safe_text
    assert any(name == "github-token" for name, _ in findings)


def test_generic_secret_assignment_is_redacted_with_zero_occurrences():
    transcript = f"config dump during failure:\napi_key = '{FAKE_GENERIC_SECRET}'\n"

    safe_text, findings = redact_transcript(transcript)

    assert FAKE_GENERIC_SECRET not in safe_text
    assert any(name == "generic-api-key-assignment" for name, _ in findings)


def test_findings_never_carry_the_raw_matched_value():
    transcript = f"AWS_KEY = '{FAKE_AWS_KEY}'"

    _, findings = redact_transcript(transcript)

    for _rule_name, redacted_sample in findings:
        assert FAKE_AWS_KEY not in redacted_sample


def test_multiple_secrets_in_one_transcript_are_all_redacted():
    transcript = f"AWS_KEY = '{FAKE_AWS_KEY}'\nGITHUB_TOKEN = '{FAKE_GITHUB_TOKEN}'\n"

    safe_text, findings = redact_transcript(transcript)

    assert FAKE_AWS_KEY not in safe_text
    assert FAKE_GITHUB_TOKEN not in safe_text
    assert len(findings) == 2


def test_non_secret_surrounding_text_is_preserved():
    transcript = f"before-context AWS_KEY = '{FAKE_AWS_KEY}' after-context"

    safe_text, _ = redact_transcript(transcript)

    assert safe_text.startswith("before-context ")
    assert safe_text.endswith(" after-context")
