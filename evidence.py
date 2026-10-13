"""Validate local agent completion receipts. Not a factual-truth checker."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def validate(receipt, root, now=None):
    now = now or datetime.now(timezone.utc)
    errors = []
    if not isinstance(receipt, dict) or set(receipt) != {'version', 'required', 'artifacts', 'checks'}:
        return ['invalid receipt schema']
    if receipt['version'] != 1 or type(receipt['version']) is not int:
        errors.append('unsupported version')
    required, artifacts, checks = receipt['required'], receipt['artifacts'], receipt['checks']
    if not isinstance(required, list) or not required or any(type(x) is not str or not x for x in required) or len(set(required)) != len(required):
        return errors + ['required must be unique nonempty names']
    if not isinstance(artifacts, list) or not isinstance(checks, list) or not checks:
        return errors + ['artifacts and nonempty checks must be lists']
    root = Path(root).resolve()
    names = set()
    for item in artifacts:
        if not isinstance(item, dict) or set(item) != {'name', 'path', 'sha256'} or any(type(v) is not str for v in item.values()):
            errors.append('invalid artifact schema'); continue
        name = item['name']
        if not name or name in names:
            errors.append('duplicate or empty artifact name')
        names.add(name)
        p = Path(item['path'])
        if p.is_absolute() or '..' in p.parts:
            errors.append('unsafe artifact path'); continue
        p = (root / p).resolve()
        if not p.is_relative_to(root):
            errors.append('artifact escapes root'); continue
        try:
            actual = hashlib.sha256(p.read_bytes()).hexdigest()
            if actual != item['sha256']:
                errors.append('artifact digest mismatch')
        except OSError:
            errors.append('artifact unreadable')
    if set(required) - names:
        errors.append('required artifact missing')
    check_names = set()
    for check in checks:
        if not isinstance(check, dict) or set(check) != {'name', 'status', 'observed_at', 'expires_at'}:
            errors.append('invalid check schema'); continue
        if type(check['name']) is not str or not check['name'] or check['name'] in check_names:
            errors.append('duplicate or invalid check name')
        check_names.add(str(check['name']))
        if check['status'] != 'passed':
            errors.append('check did not pass')
        try:
            observed = datetime.fromisoformat(check['observed_at'].replace('Z', '+00:00'))
            expiry = datetime.fromisoformat(check['expires_at'].replace('Z', '+00:00'))
            if observed.tzinfo is None or expiry.tzinfo is None or not observed <= now < expiry:
                errors.append('check stale, future-dated or timezone missing')
        except (ValueError, TypeError, AttributeError):
            errors.append('invalid check timestamp')
    return errors


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('receipt'); ap.add_argument('--root', required=True)
    args = ap.parse_args()
    try:
        with open(args.receipt) as f: receipt = json.load(f)
        errors = validate(receipt, args.root)
    except (OSError, ValueError, TypeError):
        errors = ['receipt unreadable or invalid']
    print(json.dumps({'ready': not errors, 'errors': errors}))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
