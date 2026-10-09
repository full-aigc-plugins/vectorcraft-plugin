"""全目录验收矩阵不能以单族通过代替全命令完成。"""
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class CommandMatrixTests(unittest.TestCase):
 def setUp(self):
  p=ROOT/'scripts/verify_command_evidence.py'
  self.assertTrue(p.is_file(),'command_matrix_verifier_missing')
  spec=importlib.util.spec_from_file_location('command_matrix',p);self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
 def catalog(self):return {'commands':[{'id':x,'params':[],'ownerSkill':'vectorcraft-use'} for x in ('paint.setFill','file.open')]}
 def test_unexecuted_rows_remain_not_run(self):
  rows=self.m.matrix_rows(self.catalog(),{'paint.setFill'})
  self.assertEqual([x['executionAcceptance'] for x in rows],['PASS','NOT_RUN'])
 def test_duplicate_catalog_is_rejected(self):
  c=self.catalog();c['commands'].append(c['commands'][0])
  with self.assertRaisesRegex(ValueError,'command_catalog_duplicate'):self.m.matrix_rows(c,set())
 def test_unknown_case_cannot_increase_coverage(self):
  with self.assertRaisesRegex(ValueError,'command_case_unknown'):self.m.matrix_rows(self.catalog(),{'paint.futureUnknown'})
 def fixed_fixture(self):
  import shutil,tempfile
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);root=Path(self.temp.name)
  for name in (self.m.REPORT,self.m.CATALOG,'docs/current-identity.json','docs/evidence/vectorcraft-public-tag64-install-20261009.json','scripts/qa/command_paint.py'):
   target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
  return root
 def test_current_fixed_report_validates_all_paint_cases(self):
  matrix=self.m.verify(self.fixed_fixture());self.assertEqual(matrix['coverage'],{'catalogCommands':585,'passed':22,'notRun':563,'stages':44});self.assertEqual(matrix['tasksClosed'],[])
 def test_forged_native_color_is_rejected_even_with_success_flags(self):
  import json
  root=self.fixed_fixture();path=root/self.m.REPORT;report=json.loads(path.read_text());stage=report['cases'][0]['stages'][0]
  stage['after']=stage['before'];stage['reopened']=stage['before'];path.write_text(json.dumps(report))
  with self.assertRaisesRegex(ValueError,'paint_color'):self.m.verify(root)
 def test_missing_executed_command_is_rejected(self):
  import json
  root=self.fixed_fixture();path=root/self.m.REPORT;report=json.loads(path.read_text());report['cases'].pop();path.write_text(json.dumps(report))
  with self.assertRaisesRegex(ValueError,'command_case_coverage'):self.m.verify(root)
