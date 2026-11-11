# Task 9 — SQL injection remediation

**Status: defensive review only.** No DVWA medium-security lab, sqlmap, Burp Suite
interception, database enumeration, injection test, or exploit script was run or created.
The requested exploit payloads and extraction procedures are intentionally omitted.

## Executive summary

SQL injection is a high-impact class of software defect when untrusted input is interpreted
as SQL syntax. In a vulnerable application this may expose or alter data, bypass intended
authorization, or affect service availability. This workspace has not tested an
application, so no asset-specific risk rating or data exposure is asserted.

## Root cause and safe remediation

The root cause is mixing query structure with untrusted values. Use parameterized
statements, validate expected types and ranges, keep dynamic identifiers in a fixed
allow-list, and grant database accounts only the permissions they need. Do not rely on
escaping user input as the primary control.

Python (SQLite):

```python
cursor.execute(
    "SELECT id, display_name FROM accounts WHERE id = ?",
    (account_id,),
)
```

PHP (PDO):

```php
$statement = $pdo->prepare(
    'SELECT id, display_name FROM accounts WHERE id = :id'
);
$statement->execute(['id' => $accountId]);
$account = $statement->fetch(PDO::FETCH_ASSOC);
```

In both cases, the statement is fixed and the parameter is bound as a value. Review
authorization separately: a safe query must still enforce access controls.

## Evidence and scope

No exploit findings or screenshots exist. A real lab exercise requires an isolated,
authorized DVWA instance and a human operator; do not run tools against a third-party
service. See the [OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
and [PortSwigger SQL injection overview](https://portswigger.net/web-security/sql-injection)
for defensive background.
