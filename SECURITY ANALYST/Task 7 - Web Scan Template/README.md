# Task 7 — Nikto local-lab scan

**Status: not performed.** Nikto and a locally authorized DVWA/Apache target were not
available. There are no scan results, screenshots, or vulnerabilities claimed in this
folder.

Nikto is a web-server scanner that checks for potentially risky server configuration,
known files, and outdated components. Its requests can be noisy and may trigger alerts;
it can produce false positives and does not replace manual review. Nmap focuses on host,
port, and service discovery; Nikto focuses on HTTP(S) server checks.

## Safe completion checklist

1. Install Nikto from its official repository inside an isolated VM.
2. Record written scope and use only a local test server that you control.
3. Run the required basic and (if applicable) TLS checks against that local target.
4. Save the actual tool output and screenshots. Redact secrets and unrelated host details.
5. Confirm each result manually, assign severity based on context, and record a fix.

See [nikto_scan_results.txt](./nikto_scan_results.txt) for an empty evidence template.
It intentionally contains no tool output or fabricated findings.

References: [Nikto project](https://github.com/sullo/nikto),
[OWASP Top 10](https://owasp.org/www-project-top-ten/).
