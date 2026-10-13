"""Synthetic, temporary receipt demo. Leaves no files behind."""
import hashlib
import tempfile
from pathlib import Path
from datetime import datetime, timedelta, timezone
from evidence import validate

with tempfile.TemporaryDirectory() as folder:
    root = Path(folder)
    data = b'synthetic output'
    (root/'report.txt').write_bytes(data)
    now = datetime.now(timezone.utc)
    receipt = {'version':1, 'required':['report'],
               'artifacts':[{'name':'report','path':'report.txt','sha256':hashlib.sha256(data).hexdigest()}],
               'checks':[{'name':'fixture','status':'passed','observed_at':now.isoformat(),'expires_at':(now+timedelta(minutes=1)).isoformat()}]}
    assert validate(receipt,root,now) == []
    print('PASS: unchanged synthetic artifact')
    (root/'report.txt').write_text('changed')
    assert 'artifact digest mismatch' in validate(receipt,root,now)
    print('BLOCK: changed artifact')
