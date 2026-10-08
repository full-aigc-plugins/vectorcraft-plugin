"""重签摘要不能掩盖缺失场景、错误替代、不可编辑原源或伪造安装。"""
import contextlib,importlib.util,io,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT='docs/evidence/vectorcraft-native-exchange-fixed59-20261009.json'
class NativeExchangeEvidenceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.report=json.loads((ROOT/REPORT).read_text())
  for n in set(self.report['fingerprints'])|{REPORT}:
   p=self.root/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,p)
  spec=importlib.util.spec_from_file_location('native_exchange_verifier',ROOT/'scripts/verify_native_exchange_evidence.py');self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m);self.m.ROOT=self.root
 def write(self,n,r):
  p=self.root/n;p.write_text(json.dumps(r));self.report['fingerprints'][n]=self.m.sha(p);(self.root/REPORT).write_text(json.dumps(self.report))
 def verify(self):
  with contextlib.redirect_stdout(io.StringIO()):self.m.main()
 def test_real_fixed_evidence_passes(self):self.verify()
 def test_missing_scene_refused(self):
  n=self.report['scenarioMatrix'];r=json.loads((self.root/n).read_text());r['entries'].pop();self.write(n,r)
  with self.assertRaisesRegex(ValueError,'scenario'):self.verify()
 def test_false_font_fidelity_refused(self):
  n=self.report['native'];r=json.loads((self.root/n).read_text());next(x for x in r['lossReport']['outputs'][1]['changes'] if x['code']=='font-portability')['status']='observed';self.write(n,r)
  with self.assertRaisesRegex(ValueError,'loss'):self.verify()
 def test_missing_native_substitute_refusal_refused(self):
  n=self.report['native'];r=json.loads((self.root/n).read_text());r['refusals']=[x for x in r['refusals'] if x['case']!='native-substitute-pdf'];self.write(n,r)
  with self.assertRaisesRegex(ValueError,'refusal'):self.verify()
 def test_forged_installed_skill_refused(self):
  n=self.report['host'];r=json.loads((self.root/n).read_text());r['skills'][0]['sha256']='0'*64;self.write(n,r)
  with self.assertRaisesRegex(ValueError,'installed'):self.verify()
 def test_changed_reopened_model_refused(self):
  n=self.report['native'];r=json.loads((self.root/n).read_text());r['independentReopens'][1]['model']['layers']=[];self.write(n,r)
  with self.assertRaisesRegex(ValueError,'native'):self.verify()
 def test_missing_decoded_export_refused(self):
  n=self.report['native'];r=json.loads((self.root/n).read_text());r['quality']['outputs'].pop();self.write(n,r)
  with self.assertRaisesRegex(ValueError,'decode'):self.verify()
if __name__=='__main__':unittest.main()
