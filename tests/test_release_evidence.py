"""发布证据重签后仍不能掩盖文档越级、缺失场景或固定身份漂移。"""
import contextlib,hashlib,importlib.util,io,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];REPORT='docs/evidence/vectorcraft-release-gate-20261009.json'
class ReleaseEvidenceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.report=json.loads((ROOT/REPORT).read_text());names=set(self.report['fingerprints'])|{REPORT,'project-status.json','openspec/changes/establish-v1-plugin/tasks.md','docs/evidence-index.json'}
  for entry in json.loads((ROOT/'docs/evidence-index.json').read_text())['entries']:
   if entry['path']==REPORT:names.update(entry['dependencies'])
  for name in names:
   p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
  shutil.copytree(ROOT/'skills',self.root/'skills',dirs_exist_ok=True)
  s=importlib.util.spec_from_file_location('release_evidence_verifier',ROOT/'scripts/verify_release_evidence.py');self.m=importlib.util.module_from_spec(s);s.loader.exec_module(self.m);self.m.ROOT=self.root
 def rewrite(self,key,value):
  name=self.report[key];p=self.root/name;p.write_text(json.dumps(value));self.report['fingerprints'][name]=hashlib.sha256(p.read_bytes()).hexdigest();(self.root/REPORT).write_text(json.dumps(self.report))
 def verify(self):
  with contextlib.redirect_stdout(io.StringIO()):self.m.main()
 def test_current_release_evidence_passes(self):self.verify()
 def test_missing_scenario_refused(self):
  r=json.loads((self.root/self.report['scenarioMatrix']).read_text());r['entries'].pop();self.rewrite('scenarioMatrix',r)
  with self.assertRaisesRegex(ValueError,'scenarios'):self.verify()
 def test_document_only_native_promotion_refused(self):
  r=json.loads((self.root/self.report['documentationOnly']).read_text());r['gate']['layers']['native']['status']='PASS';self.rewrite('documentationOnly',r)
  with self.assertRaisesRegex(ValueError,'docs_only'):self.verify()
 def test_fixed_commit_cannot_be_replaced(self):
  self.report['pluginCommit']='0'*40;(self.root/REPORT).write_text(json.dumps(self.report))
  with self.assertRaisesRegex(ValueError,'identity'):self.verify()
if __name__=='__main__':unittest.main()
