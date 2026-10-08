"""布尔事务行为：会话替身仅用于故障注入，不替代真实原生验收。"""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT/'skills/vectorcraft-use/scripts'


def load(name):
    spec = importlib.util.spec_from_file_location('boolean_test_'+name, SCRIPTS/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def document():
    return {'next_id': 10, 'metadata': {'modified': 1}, 'units': 'Points',
            'layers': [{'id': 1, 'kind': {'type': 'layer', 'children': [
                {'id': i, 'kind': {'type': 'path', 'path': {'subpaths': []}}, 'name': str(i)}
                for i in [2, 3, 4]]}}]}


class Session:
    def __init__(self, mode):
        self.mode = mode
        self.doc = document()
        self.selected = [2, 3]
        self.calls = []
        self.before = copy.deepcopy(self.doc)

    def command(self, command, params=None):
        self.calls.append(command)
        if command == 'document.inspect':
            return {'selection': list(self.selected)}
        if command == 'document.json':
            return copy.deepcopy(self.doc)
        if command == 'document.save':
            Path(params['path']).write_text(json.dumps(self.doc))
            return {'saved': True}
        if command == 'document.open':
            if self.mode == 'restore-fails':
                raise RuntimeError('semantic_error: reopen failed')
            self.doc = json.loads(Path(params['path']).read_text())
            return {'opened': True}
        if command == 'select.set':
            self.selected = params['ids']
            return {}
        raise AssertionError(command)

    def request(self, method, params):
        self.calls.append('mutation')
        children = self.doc['layers'][0]['kind']['children']
        self.doc['layers'][0]['kind']['children'] = [v for v in children if v['id'] not in self.selected]
        if self.mode in ('known-failure', 'restore-fails'):
            raise RuntimeError('semantic_error: deleted then failed')
        if self.mode == 'unknown':
            raise RuntimeError('outcome_unknown: lost reply')
        if self.mode == 'group':
            self.doc['layers'][0]['kind']['children'].insert(0, {'id': 10, 'kind': {'type':'group', 'children': children[:2]}})
            result = {'id': 10}
        elif self.mode == 'empty':
            result = {'ids': []}
        else:
            self.doc['layers'][0]['kind']['children'].insert(0, {'id': 10, 'kind': {'type':'path','path':{'subpaths':[]}}})
            result = {'ids': [10]}
        if self.mode == 'bad-result':
            result = {'ids': [999]}
        if self.mode == 'unselected-drift':
            self.doc['layers'][0]['kind']['children'][-1]['name'] = 'corrupt'
        return {'content':[{'type':'text','text':json.dumps(result)}]}


class BooleanTransactionTests(unittest.TestCase):
    def execute(self, session, stage, command='object.pathfinder.unite'):
        module = load('native_workflow')
        rows = [{**row, 'enabled': True} for row in module.commands.catalog()['commands']]
        with patch.object(module.commands, 'runtime_rows', return_value=rows):
            return module.execute(session, {'command':command,'params':{}}, {}, [], stage)

    def test_known_partial_delete_restores_original_objects_without_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = Session('known-failure')
            with self.assertRaisesRegex(RuntimeError, 'non_atomic_operation_defect'):
                self.execute(session, Path(temporary))
            self.assertEqual(session.doc, session.before)
            self.assertEqual(session.calls.count('mutation'), 1)
            self.assertEqual(session.calls.count('document.open'), 1)
            proof = json.loads((Path(temporary)/'boolean-transactions.json').read_text())['operations'][0]
            self.assertEqual(proof['participantIds'], [2,3])
            self.assertEqual(proof['status'], 'restored_after_failure')
            self.assertTrue((Path(temporary)/proof['checkpoint']).is_file())

    def test_success_records_result_identity_and_keeps_unselected_objects(self):
        for mode, command, expected in [('normal','object.pathfinder.unite',[10]),
                                        ('group','object.group',[10]),
                                        ('empty','object.pathfinder.intersect',[])]:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                session = Session(mode)
                self.execute(session, Path(temporary), command)
                proof = json.loads((Path(temporary)/'boolean-transactions.json').read_text())['operations'][0]
                self.assertEqual(proof['status'], 'verified')
                self.assertEqual(proof['resultIds'], expected)
                self.assertEqual(session.calls.count('mutation'), 1)
                self.assertTrue((Path(temporary)/proof['checkpoint']).is_file())

    def test_bad_result_or_unselected_mutation_restores_checkpoint(self):
        for mode in ['bad-result','unselected-drift']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                session = Session(mode)
                with self.assertRaisesRegex(RuntimeError, 'non_atomic_operation_defect'):
                    self.execute(session, Path(temporary))
                self.assertEqual(session.doc, session.before)
                self.assertEqual(session.calls.count('mutation'), 1)

    def test_unknown_reply_keeps_stage_without_restore_or_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = Session('unknown')
            with self.assertRaisesRegex(RuntimeError, 'outcome_unknown'):
                self.execute(session, Path(temporary))
            self.assertNotEqual(session.doc, session.before)
            self.assertNotIn('document.open',session.calls)
            self.assertEqual(session.calls.count('mutation'), 1)
            proof = json.loads((Path(temporary)/'boolean-transactions.json').read_text())['operations'][0]
            self.assertEqual(proof['status'], 'unknown')
            self.assertFalse(proof['replayAllowed'])

    def test_restore_failure_is_unknown_and_original_checkpoint_remains(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = Session('restore-fails')
            with self.assertRaisesRegex(RuntimeError, 'outcome_unknown: boolean_restore_unconfirmed'):
                self.execute(session, Path(temporary))
            proof = json.loads((Path(temporary)/'boolean-transactions.json').read_text())['operations'][0]
            self.assertEqual(proof['status'], 'restore_unconfirmed')
            self.assertTrue((Path(temporary)/proof['checkpoint']).is_file())

    def test_invalid_selection_never_executes_or_creates_checkpoint(self):
        for ids in [[],[2,2],[True],[999],[{}]]:
            with self.subTest(ids=ids), tempfile.TemporaryDirectory() as temporary:
                session = Session('normal'); session.selected = ids
                with self.assertRaisesRegex(ValueError, 'boolean_selection_identity_mismatch'):
                    self.execute(session, Path(temporary))
                self.assertNotIn('mutation',session.calls)
                self.assertEqual(list(Path(temporary).iterdir()),[])

    def test_existing_checkpoint_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary)/'boolean-checkpoint-0.vectorcraft'
            checkpoint.write_text('user checkpoint')
            session = Session('normal')
            with self.assertRaisesRegex(ValueError, 'boolean_checkpoint_exists'):
                self.execute(session, Path(temporary))
            self.assertEqual(checkpoint.read_text(),'user checkpoint')
            self.assertNotIn('mutation',session.calls)

    def test_checkpoint_collection_compares_geometry_and_link_contents(self):
        guard = load('boolean_transactions')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); first = root/'first';second = root/'second'
            first.mkdir();second.mkdir();(first/'image.png').write_bytes(b'pixels');(second/'image.png').write_bytes(b'pixels')
            old = document();new = document()
            old['layers'][0]['kind']['children'][0]['kind'] = {'type':'image','link':{'path':'image.png','modified':1,'hash':'same'}}
            new['layers'][0]['kind']['children'][0]['kind'] = {'type':'image','link':{'path':'image.png','modified':2,'hash':'same'}}
            self.assertEqual(guard.checkpoint_model(old,first/'project.vectorcraft'),guard.checkpoint_model(new,second/'project.vectorcraft'))
            new['layers'][0]['kind']['children'][1]['name'] = 'corrupt geometry identity'
            self.assertNotEqual(guard.checkpoint_model(old,first/'project.vectorcraft'),guard.checkpoint_model(new,second/'project.vectorcraft'))
            new = copy.deepcopy(old);(second/'image.png').write_bytes(b'other pixels')
            self.assertNotEqual(guard.checkpoint_model(old,first/'project.vectorcraft'),guard.checkpoint_model(new,second/'project.vectorcraft'))
