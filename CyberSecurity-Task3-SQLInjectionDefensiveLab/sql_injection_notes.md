# SQL injection analysis notes

## Activity record

- Target: **none — no local DVWA instance was available**
- Authorization/scope: **not applicable**
- Security level: **not tested**
- Inputs, responses, data exposure: **not tested**
- Screenshots: **not provided**
- Result: **no exploitation performed**

## What to inspect safely in a code review

Trace request input to every database call. Flag SQL assembled with string concatenation,
format strings, or interpolation. Verify that every value is bound through the database
driver's parameter API, and that the application account has only the required permissions.
Parameterized queries preserve the separation between SQL code and values.

## Remediation checklist

1. Replace dynamic SQL value interpolation with prepared/parameterized statements.
2. Keep identifiers (such as table/column names) in fixed allow-lists; value placeholders
   generally cannot parameterize identifiers.
3. Validate types, length, and allowed values at the boundary.
4. Use least-privilege database credentials; return generic errors to clients.
5. Add tests for legitimate input and malformed input; never test a system without written
   authorization.

No payload log is included because no local exercise was performed.
