import copy
import hashlib
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from evidence import validate

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        (self.root/'report.txt').write_text('synthetic fixture')
        self.now=datetime(2026,10,13,12,tzinfo=timezone.utc)
        self.r={'version':1,'required':['report'],'artifacts':[{'name':'report','path':'report.txt','sha256':hashlib.sha256(b'synthetic fixture').hexdigest()}],
                'checks':[{'name':'test','status':'passed','observed_at':'2026-10-13T11:00:00Z','expires_at':'2026-10-13T13:00:00Z'}]}
    def tearDown(self): self.tmp.cleanup()
    def test_valid(self): self.assertEqual(validate(self.r,self.root,self.now),[])
    def test_hash(self): self.r['artifacts'][0]['sha256']='0'*64; self.assertTrue(validate(self.r,self.root,self.now))
    def test_missing(self): self.r['artifacts']=[]; self.assertTrue(validate(self.r,self.root,self.now))
    def test_traversal(self): self.r['artifacts'][0]['path']='../report.txt'; self.assertTrue(validate(self.r,self.root,self.now))
    def test_symlink_escape(self):
        (self.root/'escape').symlink_to('/etc/hosts'); self.r['artifacts'][0]['path']='escape'; self.assertTrue(validate(self.r,self.root,self.now))
    def test_stale(self): self.r['checks'][0]['expires_at']='2026-10-13T12:00:00Z'; self.assertTrue(validate(self.r,self.root,self.now))
    def test_future(self): self.r['checks'][0]['observed_at']='2026-10-13T13:00:00Z'; self.assertTrue(validate(self.r,self.root,self.now))
    def test_failed(self): self.r['checks'][0]['status']='failed'; self.assertTrue(validate(self.r,self.root,self.now))
    def test_naive(self): self.r['checks'][0]['expires_at']='2026-10-13T13:00:00'; self.assertTrue(validate(self.r,self.root,self.now))
    def test_no_checks(self): self.r['checks']=[]; self.assertTrue(validate(self.r,self.root,self.now))
    def test_duplicate(self): self.r['artifacts']*=2; self.assertTrue(validate(self.r,self.root,self.now))
    def test_schema(self): self.assertTrue(validate({},self.root,self.now))

if __name__=='__main__': unittest.main()
