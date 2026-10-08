"""四场景证据重新散列后仍须满足原生身份、预算、谱系及最佳候选契约。"""
import contextlib,importlib.util,io,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];REPORT='docs/evidence/vectorcraft-revision-fixed63-20261009.json'
class RevisionEvidenceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.report=json.loads((ROOT/REPORT).read_text());names=set(self.report['fingerprints'])|{REPORT,'docs/evidence-index.json'}
  for entry in json.loads((ROOT/'docs/evidence-index.json').read_text())['entries']:
   if entry['path']==REPORT:names.update(entry['dependencies'])
  for name in names:
   p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
  spec=importlib.util.spec_from_file_location('revision_verifier',ROOT/'scripts/verify_revision_evidence.py');self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
 def case(self,name):return json.loads((self.root/self.report['cases'][name]).read_text())
 def write(self,name,value):
  p=self.root/name;p.write_text(json.dumps(value));self.report['fingerprints'][name]=self.m.sha(p);(self.root/REPORT).write_text(json.dumps(self.report))
 def rewrite(self,key,value):self.write(self.report['cases'][key],value)
 def verify(self):
  with contextlib.redirect_stdout(io.StringIO()):self.m.verify(self.root)
 def test_actual_fixed_four_scenarios_pass(self):self.verify()
 def test_missing_scenario_refused(self):
  name=self.report['scenarioMatrix'];r=json.loads((self.root/name).read_text());r['entries'].pop();self.write(name,r)
  with self.assertRaisesRegex(ValueError,'scenarios'):self.verify()
 def test_unchecked_candidate_refused(self):
  r=self.case('budget');r['nextRequest']['input']['technicalEvidenceOrigin']='caller_unverified';self.rewrite('budget',r)
  with self.assertRaisesRegex(ValueError,'decode'):self.verify()
 def test_exhausted_budget_cannot_charge_fifth_attempt(self):
  r=self.case('budget');r['sharedAttempts']=5;self.rewrite('budget',r)
  with self.assertRaisesRegex(ValueError,'budget'):self.verify()
 def test_small_improvement_must_retain_new_best(self):
  r=self.case('small-improvement');r['best']['requestId']=r['initialRequest']['id'];self.rewrite('small-improvement',r)
  with self.assertRaisesRegex(ValueError,'best'):self.verify()
 def test_changed_goal_must_report_latest_issues(self):
  r=self.case('goal-change');r['best']['unresolvedIssues']=[{'message':'old issues'}];self.rewrite('goal-change',r)
  with self.assertRaisesRegex(ValueError,'latest_goal'):self.verify()
 def test_missing_lineage_guard_refused(self):
  r=self.case('guards');r['records']=[x for x in r['records'] if x['case']!='wrong-output-lineage'];self.rewrite('guards',r)
  with self.assertRaisesRegex(ValueError,'coverage'):self.verify()
 def test_forged_lineage_refusal_refused(self):
  r=self.case('guards');next(x for x in r['records'] if x['case']=='wrong-output-lineage')['error']='accepted';self.rewrite('guards',r)
  with self.assertRaisesRegex(ValueError,'guard_refusal'):self.verify()
 def test_score_must_use_all_five_dimensions(self):
  r=self.case('guards');r['nextReceipt']['scores']['structure']=4;self.rewrite('guards',r)
  with self.assertRaisesRegex(ValueError,'mean_feedback'):self.verify()
 def test_gui_owned_process_stop_required(self):
  r=self.case('stale-gui');r['gui']['ownedProcessesStopped']=False;self.rewrite('stale-gui',r)
  with self.assertRaisesRegex(ValueError,'gui'):self.verify()
 def test_engineering_not_run_cannot_be_accepted(self):
  r=self.case('round-limit');r['best']['acceptanceStatus']='accepted';self.rewrite('round-limit',r)
  with self.assertRaisesRegex(ValueError,'claim'):self.verify()
 def test_best_dependencies_must_match_checked_candidate(self):
  r=self.case('lower-score');r['best']['fingerprints']['project.vectorcraft']='0'*64;self.rewrite('lower-score',r)
  with self.assertRaisesRegex(ValueError,'best_dependencies'):self.verify()
 def test_authority_must_narrow_to_assessed_object(self):
  r=self.case('round-limit');r['proposal']['authorization']['objects']=[2,3];self.rewrite('round-limit',r)
  with self.assertRaisesRegex(ValueError,'authority'):self.verify()
 def test_effects_before_stale_refusal_forbidden(self):
  r=self.case('guards');next(x for x in r['records'] if x['case']=='stale-target')['outputAbsent']=False;self.rewrite('guards',r)
  with self.assertRaisesRegex(ValueError,'guard_effects'):self.verify()
 def test_next_candidate_requires_actual_output_directory(self):
  r=self.case('budget');r['execution']['output']='QA_ROOT/unrelated';self.rewrite('budget',r)
  with self.assertRaisesRegex(ValueError,'lineage'):self.verify()
if __name__=='__main__':unittest.main()
