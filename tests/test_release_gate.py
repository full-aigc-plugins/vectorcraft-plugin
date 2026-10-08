"""发布门禁必须分别核验六层证据；文档、复算摘要和任务勾选都不能代替运行验收。"""
import contextlib,hashlib,importlib.util,io,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ReleaseGateTests(unittest.TestCase):
 def setUp(self):
  self.assertTrue((ROOT/'scripts/release_gate.py').is_file(),'release_gate_behavior_missing: no executable six-layer release readiness contract')
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.bundle=json.loads((ROOT/'docs/release-evidence.json').read_text());names=set(self.bundle['fingerprints'])|{'docs/release-evidence.json','docs/evidence-index.json','project-status.json','openspec/changes/establish-v1-plugin/tasks.md','scripts/release_gate.py','scripts/verify_revision_evidence.py'}
  for name in names:
   p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
  shutil.copytree(ROOT/'skills',self.root/'skills',dirs_exist_ok=True)
  spec=importlib.util.spec_from_file_location('release_gate',ROOT/'scripts/release_gate.py');self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
 def write(self,name,value):
  p=self.root/name;p.write_text(json.dumps(value));self.bundle['fingerprints'][name]=hashlib.sha256(p.read_bytes()).hexdigest();(self.root/'docs/release-evidence.json').write_text(json.dumps(self.bundle))
 def assess(self):
  with contextlib.redirect_stdout(io.StringIO()):return self.m.assess(self.root)
 def test_actual_snapshot_passes_six_layers_as_development_only(self):
  r=self.assess();self.assertEqual({k:v['status'] for k,v in r['layers'].items()},{k:'PASS' for k in ['structure','skills','runtime','host','task','native']});self.assertTrue(r['publishable']['development']);self.assertFalse(r['publishable']['marketplace'])
 def test_documents_only_do_not_promote_runtime_or_host(self):
  for name in [self.bundle['host'],self.bundle['technical']]: (self.root/name).unlink()
  r=self.assess();self.assertFalse(r['publishable']['development']);self.assertFalse(r['publishable']['marketplace']);self.assertNotEqual(r['layers']['host']['status'],'PASS');self.assertNotEqual(r['layers']['native']['status'],'PASS')
 def test_wrong_release_version_refused(self):
  p=self.root/'plugin.json';r=json.loads(p.read_text());r['version']='0.1.0-dev.999';p.write_text(json.dumps(r));self.assertFalse(self.assess()['publishable']['development'])
 def test_vendor_drift_refused(self):
  p=self.root/'skills/vectorcraft-use/SKILL.md';p.write_text(p.read_text()+'\nQA changed vendor\n');self.assertEqual(self.assess()['layers']['skills']['status'],'FAIL')
 def test_disabled_host_skill_refused_after_rehash(self):
  name=self.bundle['host'];r=json.loads((self.root/name).read_text());r['skills'][0]['enabled']=False;self.write(name,r);self.assertEqual(self.assess()['layers']['host']['status'],'FAIL')
 def test_document_pass_cannot_impersonate_native_acceptance(self):
  self.write(self.bundle['technical'],{'result':'PASS','schema':'documentation-check/v1','pluginVersion':self.bundle['pluginVersion']});self.assertFalse(self.assess()['publishable']['development'])
 def test_changed_installed_code_refused(self):
  p=self.root/'src/evaluation/revision_cycle.ts';p.write_text(p.read_text()+'\n// QA changed code\n');self.assertFalse(self.assess()['publishable']['development'])
 def test_rehashed_native_budget_violation_refused(self):
  technical=json.loads((self.root/self.bundle['technical']).read_text());name=technical['cases']['budget'];r=json.loads((self.root/name).read_text());r['sharedAttempts']=5;self.write(name,r);technical['fingerprints'][name]=self.bundle['fingerprints'][name];self.write(self.bundle['technical'],technical);self.assertEqual(self.assess()['layers']['native']['status'],'FAIL')
 def test_checkboxes_cannot_grant_marketplace_eligibility(self):
  p=self.root/'openspec/changes/establish-v1-plugin/tasks.md';p.write_text(p.read_text().replace('- [ ]','- [x]'))
  p=self.root/'project-status.json';r=json.loads(p.read_text());r.update(marketplaceEligible=True,implementation='complete',supportedPluginHosts=['codex']);p.write_text(json.dumps(r));self.assertFalse(self.assess()['publishable']['marketplace'])
 def test_metadata_path_escape_refused(self):
  self.bundle['host']='../outside.json';(self.root/'docs/release-evidence.json').write_text(json.dumps(self.bundle));self.assertFalse(self.assess()['publishable']['development'])
 def test_wrong_skill_source_in_host_refused(self):
  name=self.bundle['host'];r=json.loads((self.root/name).read_text());r['skillSourceCommit']='0'*40;self.write(name,r);self.assertEqual(self.assess()['layers']['host']['status'],'FAIL')
 def test_marketplace_cli_fails_closed_with_json(self):
  r=subprocess.run([sys.executable,'-I','-B',str(self.root/'scripts/release_gate.py'),'--require','marketplace'],capture_output=True,text=True)
  self.assertEqual(r.returncode,1);self.assertFalse(json.loads(r.stdout)['publishable']['marketplace'])
if __name__=='__main__':unittest.main()
