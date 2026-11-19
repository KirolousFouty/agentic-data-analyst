# Security policy and safeguards

This application is deliberately read-only. It is not a general database administration agent.

- The application connects with `analyst_reader`, which receives only `CONNECT`, schema `USAGE`, and table `SELECT` grants.
- The SQL executor sets each connection transaction to read-only, then applies a database statement timeout and hard result-row cap.
- SQLGlot parses every model-produced query. Exactly one statement must be a `SELECT`; writes, DDL, comments, `SELECT INTO`, unapproved tables, and dangerous functions are rejected.
- Validation is structural and allowlist based; a model assertion that a query is safe is irrelevant.
- Only the seven approved analytics tables are reachable. Database text and model output are untrusted input.
- The intent gate rejects prompt injection and write/admin requests before model invocation. Ambiguous questions request metric/timeframe clarification.
- Future write-capable features must be separately designed and require explicit user confirmation immediately before the write. They are out of scope for this release.

Operational guidance: put PostgreSQL on a private network, rotate the example credentials before any shared deployment, use TLS for remote connections, restrict API authentication at the edge, and monitor rejected-query metrics. Report vulnerabilities privately to the repository maintainers; do not include secrets or customer data in an issue.
