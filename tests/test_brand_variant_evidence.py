"""完整品牌验收拒绝摘要重算后的缺失场景和伪造保全／身份。"""
import contextlib,importlib.util,io,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT='docs/evidence/vectorcraft-brand-variants-fixed56-20261009.json'
class BrandVariantEvidenceTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  self.report=json.loads((ROOT/REPORT).read_text())
  for name in set(self.report['fingerprints'])|{REPORT,'docs/evidence-index.json'}:
   p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
  s=importlib.util.spec_from_file_location('brand_verify_fixture',ROOT/'scripts/verify_brand_variant_evidence.py');self.m=importlib.util.module_from_spec(s);s.loader.exec_module(self.m);self.m.ROOT=self.root
  for entry in json.loads((ROOT/'docs/evidence-index.json').read_text())['entries']:
   for name in entry['dependencies']:
    p=self.root/name
    if not p.exists():p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
 def write(self,name,value):
  p=self.root/name;p.write_text(json.dumps(value));self.report['fingerprints'][name]=self.m.sha(p);(self.root/REPORT).write_text(json.dumps(self.report))
 def verify(self):
  with contextlib.redirect_stdout(io.StringIO()):self.m.main()
 def test_complete_current_evidence_passes(self):self.verify()
 def test_missing_scenario_rejected_after_rehash(self):
  n=self.report['scenarioMatrix'];j=json.loads((self.root/n).read_text());j['entries'].pop();self.write(n,j)
  with self.assertRaisesRegex(ValueError,'scenario_coverage'):self.verify()
 def test_changed_unrelated_export_rejected_after_rehash(self):
  n=self.report['native']['assets'];j=json.loads((self.root/n).read_text());j['decoded'][-1]['unrelatedUnchanged']=False;self.write(n,j)
  with self.assertRaisesRegex(ValueError,'unrelated_exports'):self.verify()
 def test_missing_native_fault_rejected_after_rehash(self):
  n=self.report['native']['guard'];j=json.loads((self.root/n).read_text());j['failures'].pop();self.write(n,j)
  with self.assertRaisesRegex(ValueError,'guard_coverage'):self.verify()
 def test_changed_instance_bounds_rejected_after_rehash(self):
  n=self.report['native']['assets'];j=json.loads((self.root/n).read_text());j['checks'][0]['boundsMismatchObjectIds']=[j['checks'][0]['consumerIds'][0]];self.write(n,j)
  with self.assertRaisesRegex(ValueError,'asset_dependency'):self.verify()
 def test_forged_installed_digest_rejected_after_rehash(self):
  n=self.report['host'];j=json.loads((self.root/n).read_text());j['skills'][0]['sha256']='0'*64;self.write(n,j)
  with self.assertRaisesRegex(ValueError,'installed_identity'):self.verify()
 def test_unknown_token_replay_rejected_after_rehash(self):
  n=self.report['native']['unknown'];j=json.loads((self.root/n).read_text());j['replayAllowed']=True;self.write(n,j)
  with self.assertRaisesRegex(ValueError,'unknown_refusal'):self.verify()
if __name__=='__main__':unittest.main()
