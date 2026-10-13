# agent-evidence-check

Before marking an agent task complete, check that its required files exist, match their recorded SHA-256 digests and have unexpired passing checks.

Python 3.10+, standard library only. No network, model calls, private accounts or executor. MIT.

## Run

```sh
python3 -m unittest -v
python3 demo.py
python3 evidence.py receipt.json --root ./outputs
```

Exit 0 means the receipt meets this contract; exit 1 means it does not. Output is JSON with `ready` and `errors`.

## Receipt format

```json
{
  "version": 1,
  "required": ["report"],
  "artifacts": [
    {"name": "report", "path": "report.txt", "sha256": "ACTUAL_FILE_SHA256"}
  ],
  "checks": [
    {"name": "source-check", "status": "passed", "observed_at": "2026-10-13T11:00:00Z", "expires_at": "2026-10-13T13:00:00Z"}
  ]
}
```

A trusted controller should produce checks and timestamps. Set expiry from the evidence's real validity window, not a convenient arbitrary date. To compute a file digest:

```sh
python3 -c 'import hashlib; print(hashlib.sha256(open("outputs/report.txt", "rb").read()).hexdigest())'
```

## What is checked

- Exact top-level and entry schemas, unique nonempty required output names.
- Required artifact presence, readable bytes and exact digest match.
- Relative paths only, with parent traversal and symlink escapes rejected.
- At least one passing check; timezone-aware observation and expiry times.
- Observation cannot be in the future; expiry is exclusive.

12 synthetic tests include stale/future dates, path traversal, symlink escapes, missing artifacts and changed hashes.

## Limits

This does not establish that a report is true, an external action succeeded or a source is trustworthy. A dishonest agent can invent passing checks, so keep the controller and receipt authorship outside the proposing agent's control. A passing check is only as meaningful as the test that produced it. No signatures, authorization gate, cross-process locking or artifact-size limit. Local files can change after validation; consumers must avoid that race or recheck just before use. Receipts may contain sensitive paths; do not publish real ones.

This complements action-boundary: that tool checks proposed actions; this one checks local completion evidence. It is not a substitute for either human review or live source verification.
