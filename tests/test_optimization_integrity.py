"""当前版本与证据依赖校验，不把静态门禁视为原生验收。"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/(name+'.py'))
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


class OptimizationIntegrityTests(unittest.TestCase):
    def test_current_identity_is_a_checked_artifact(self):
        self.assertTrue((ROOT/'docs/current-identity.json').is_file(), 'missing current identity authority')
        p = subprocess.run([sys.executable, '-I', '-B', str(ROOT/'scripts/current_identity.py'), '--check'], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout+p.stderr)
        value = json.loads((ROOT/'docs/current-identity.json').read_text())
        self.assertEqual(value['pluginVersion'], json.loads((ROOT/'plugin.json').read_text())['version'])
        self.assertEqual(value['runtime']['version'], '0.2.0-craft.2')
        self.assertEqual(value['rootRuntimeRole'], 'historical-baseline')
        self.assertEqual(len(value['skills']), 13)

    def test_evidence_changed_dependencies_are_stale_but_unrelated_changes_reuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); (root/'source.py').write_text('original'); (root/'unrelated').write_text('other')
            (root/'report.json').write_text('{"result":"PASS"}')
            m=load('evidence_index')
            record=m.record(root, 'report.json', 'local-tests', 'PASS', ['source.py'], 'bounded local test')
            self.assertEqual(m.verify(root, record)['state'], 'current')
            (root/'unrelated').write_text('new')
            self.assertEqual(m.verify(root, record)['state'], 'current')
            (root/'source.py').write_text('changed')
            self.assertEqual(m.verify(root, record)['state'], 'stale')
            (root/'bound.json').write_text(json.dumps({'result':'PASS','fingerprints':record['dependencies']}))
            rebound=m.bound_report(root,'bound.json','local-tests','original execution fingerprints')
            self.assertEqual(m.verify(root,rebound)['state'],'stale')
            (root/'source.py').write_text('original'); (root/'report.json').write_text('{"result":"FAIL"}')
            self.assertEqual(m.verify(root, record)['state'], 'stale')

    def test_unknown_evidence_level_and_skip_promotion_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); (root/'report.json').write_text('{"result":"SKIP"}')
            m=load('evidence_index')
            with self.assertRaisesRegex(ValueError, 'evidence_status_mismatch'):
                m.record(root, 'report.json', 'local-tests', 'PASS', [], 'test')
            with self.assertRaisesRegex(ValueError, 'invalid_evidence_level'):
                m.record(root, 'report.json', 'product-complete', 'SKIP', [], 'test')
            with self.assertRaisesRegex(ValueError, 'invalid_evidence_path'):
                m.record(root, '../report.json', 'local-tests', 'SKIP', [], 'test')

    def test_current_report_identity_cannot_be_rebound_to_a_new_plugin(self):
        import shutil
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for name in ('docs/current-identity.json','docs/evidence/craft-vector37-gateway-export-fixed-first-use-20261008.json','docs/evidence/craft-full-command-fixed-first-use-20261007.json','docs/evidence/craft-fixed64-every-skill-cold-first-use-20261007.json','skills.lock.json','plugin.json'):
                destination=root/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,destination)
            m=load('evidence_index')
            observed=json.loads((root/'docs/evidence/craft-vector37-gateway-export-fixed-first-use-20261008.json').read_text())['hostLock']['plugins']['vectorcraft']
            manifest=json.loads((root/'plugin.json').read_text());manifest['version']=observed['version'];(root/'plugin.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
            lock=json.loads((root/'skills.lock.json').read_text());lock['sources'][0]['sha']=observed['skillSourceSha'];lock['sources'][0]['ref']=observed['skillSourceRef'];lock['sources'][0]['sha256']=observed['skills'];(root/'skills.lock.json').write_text(json.dumps(lock))
            self.assertFalse(m.build(root)['entries'][0]['historical'])
            manifest=json.loads((root/'plugin.json').read_text());manifest['version']='0.1.0-dev.999'
            (root/'plugin.json').write_text(json.dumps(manifest))
            self.assertTrue(m.build(root)['entries'][0]['historical'])

    def test_one_standalone_runtime_or_desktop_identity_drift_is_rejected(self):
        import shutil
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            paths=['plugin.json','skills.lock.json','runtime/vectorcraft-cli.lock.json','project-status.json','skills/vectorcraft-use/references/command-coverage.json']
            lock=json.loads((ROOT/'skills.lock.json').read_text())
            paths += [f'skills/{name}/scripts/{kind}.lock.json' for name in lock['sources'][0]['skills'] for kind in ('runtime','desktop')]
            for name in paths:
                dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
            identity=load('current_identity');identity.identity(root)
            for kind in ('runtime','desktop'):
                name=f'skills/vectorcraft-cli-text/scripts/{kind}.lock.json';path=root/name;original=path.read_text();data=json.loads(original)
                data['binarySha256']='0'*64
                if kind=='runtime':data['artifacts']['darwin-arm64']['binarySha256']='0'*64
                path.write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError,'standalone_runtime_identity_drift'):identity.identity(root)
                path.write_text(original)

    def test_previous_candidate_is_historical_after_plugin_release_version_changes(self):
        import shutil
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            names=('docs/current-identity.json','docs/evidence/craft-vector37-gateway-export-fixed-first-use-20261008.json','docs/evidence/craft-full-command-fixed-first-use-20261007.json','docs/evidence/craft-fixed64-every-skill-cold-first-use-20261007.json','docs/evidence/vectorcraft-optimization-local-20261008.json','docs/evidence/vectorcraft-optimization-single-round-native-20261008.json','skills.lock.json','plugin.json')
            for name in names:
                dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
            manifest=json.loads((root/'plugin.json').read_text());manifest['version']='0.1.0-dev.999'
            (root/'plugin.json').write_text(json.dumps(manifest))
            m=load('evidence_index');entries=m.build(root)['entries']
            candidate=next(entry for entry in entries if entry['path']=='docs/evidence/vectorcraft-optimization-local-20261008.json')
            self.assertTrue(candidate['historical'])
            self.assertEqual(candidate['dependencies'],{})
            self.assertEqual(m.verify(root,candidate)['state'],'historical')
            self.assertIn('fingerprints',json.loads((root/candidate['path']).read_text()))
