# Acceptance Criteria: Deliberately Unsatisfiable Fixture

1. **AC1**: `paradox()` is a pure function (no randomness, no I/O, no hidden state) that takes no
   arguments and, called twice in the same process, returns `True` on the first call and `False`
   on the second call to the exact same expression `paradox()`.
