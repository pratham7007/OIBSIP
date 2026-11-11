# Task 3 — SQL injection: defensive lab notes

**Status: no DVWA instance was present and no injection was attempted.** No payload, data
exposure, screenshot, or exploitation result is claimed. This deliverable explains the
vulnerability and provides secure query patterns for review.

SQL injection occurs when an application joins untrusted input into SQL text and the
database interprets that input as query syntax. The primary defense is a parameterized
query/prepared statement: SQL structure is fixed, and user values are sent separately as
data. Validate expected formats and apply least privilege as additional controls; escaping
alone is not a substitute.

See [sql_injection_notes.md](./sql_injection_notes.md) for a safe analysis checklist and
[secure_query_examples.py](./secure_query_examples.py) for parameterized examples. To
complete the hands-on portion, create an isolated DVWA VM under your own control, follow
DVWA's official setup guidance, and capture only your own results. Do not copy test inputs
to a real service.
