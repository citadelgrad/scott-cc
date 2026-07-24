#!/usr/bin/env python3
"""Redaction for failure transcripts entering the SkillOpt-Sleep corpus.

scc-ncs.24: SkillOpt-Sleep previously mined only successful session
transcripts to propose "Learned preferences & procedures" entries, which is
survivorship-biased toward wins. Widening the input corpus to include
circuit-breaker escalations and bd (beads) human-flagged failures means raw
failure transcripts (command output, error text, pasted logs) can now reach
the pipeline that ultimately writes a derived summary into this repo's
committed CLAUDE.md "Learned preferences & procedures" block. Those
transcripts have not been through the interactive PreToolUse confirm gate
that ``secret_scan.py`` provides for Write/Edit/Bash content, so any secret
sitting in a failure transcript would otherwise flow straight into a
committed file with no human in the loop.

This module is the redact-before-persist gate for that path: it reuses
secret_scan.py's detection rules (RULES) and its "show a bit, hide the
rest" masking convention (redact()) rather than re-implementing pattern
matching, and adds ``redact_transcript()`` to replace every matched secret
*in place* within a block of text — not just report that one was found.

Contract for callers (e.g. a SkillOpt-Sleep failure-summary writer):
    text = read_failure_transcript(...)
    safe_text, findings = redact_transcript(text)
    # `safe_text` is safe to summarize/persist; `findings` is a list of
    # (rule_name, redacted_sample) pairs for logging/audit, never raw values.
    # A transcript with no findings is returned byte-for-byte unchanged, so
    # it remains eligible for inclusion untouched (scc-ncs.24 AC #3).
"""

from __future__ import annotations

import sys
from pathlib import Path

# secret_scan.py lives alongside this file and is not part of a package
# (hooks/ has no __init__.py, matching Claude Code's hook-as-script
# contract) — import it as a sibling module rather than duplicating RULES.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from secret_scan import RULES, redact  # noqa: E402


def has_secret(text: str) -> bool:
    """True if any known secret pattern appears anywhere in ``text``."""
    return any(pattern.search(text) for _, pattern in RULES)


def redact_transcript(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Replace every detected secret in ``text`` with a redacted placeholder.

    Returns ``(safe_text, findings)`` where ``findings`` is a list of
    ``(rule_name, redacted_sample)`` pairs — never the raw matched value.
    A clean transcript (no matches) is returned unchanged, so it remains
    eligible for inclusion as-is (scc-ncs.24 AC #3).
    """
    matches: list[tuple[int, int, str, str]] = []  # start, end, rule, raw

    for rule_name, pattern in RULES:
        for m in pattern.finditer(text):
            span = m.span()
            # Skip overlaps with an already-matched (more specific) rule,
            # same precedence convention as secret_scan.find_matches.
            if any(span[0] < e and span[1] > s for s, e, _, _ in matches):
                continue
            matches.append((span[0], span[1], rule_name, m.group(0)))

    if not matches:
        return text, []

    matches.sort(key=lambda t: t[0])

    out_parts: list[str] = []
    findings: list[tuple[str, str]] = []
    cursor = 0
    for start, end, rule_name, raw in matches:
        out_parts.append(text[cursor:start])
        placeholder = f"[REDACTED:{rule_name}]"
        out_parts.append(placeholder)
        findings.append((rule_name, redact(raw)))
        cursor = end
    out_parts.append(text[cursor:])

    return "".join(out_parts), findings


def main() -> None:  # pragma: no cover - manual/CLI convenience only
    """CLI convenience: redact stdin, print safe text to stdout."""
    text = sys.stdin.read()
    safe_text, findings = redact_transcript(text)
    sys.stdout.write(safe_text)
    if findings:
        rule_names = sorted({name for name, _ in findings})
        print(
            f"\n[redacted {len(findings)} match(es): {', '.join(rule_names)}]",
            file=sys.stderr,
        )


if __name__ == "__main__":  # pragma: no cover
    main()
