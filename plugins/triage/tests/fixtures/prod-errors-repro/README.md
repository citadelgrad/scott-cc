# Fixture: prod-errors-repro (AC4)

`app/checkout.py` carries a genuine bug: `process_payment` calls `.strip()` on
`payment["token"]` without a null guard. `error.log` contains the matching stack trace,
occurring 3 times (same exception type + same top frame → must collapse to **one** triage
item per `prod-errors/SKILL.md`'s "group by stack trace shape" rule), plus one distinct,
unrelated `KeyError` occurring once (a second, separate triage item).

This fixture exists to let a live dispatch actually reproduce the failure (not just parse the
log) — driving `process_payment({"token": None})` genuinely raises
`AttributeError: 'NoneType' object has no attribute 'strip'`, character-for-character matching
the log's trace.
