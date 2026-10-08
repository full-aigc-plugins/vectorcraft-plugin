"""公开工作流的真实原生依赖误改注入；候选与固定安装独立记录。"""
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
PROXY = '''
# QA-only fault proxy: the actual native engine completes the swatch edit,
# then an extra real command simulates an erroneous update of a non-consumer.
class _BrandFaultSession(Session):
    def request(self, method, params):
        result = super().request(method, params)
        arguments = params.get('arguments', {}) if isinstance(params, dict) else {}
        target = os.environ.get('CRAFT_BRAND_FAULT_OBJECT')
        if target and method == 'tools/call' and arguments.get('command') == 'swatch.edit':
            injected = super().request('tools/call', {'name': 'run_command', 'arguments': {
                **json.loads(os.environ.get('CRAFT_BRAND_FAULT_COMMAND', json.dumps({'command': 'paint.setFill', 'params': {'ids': [int(target)], 'color': '#175cce'}})))}})
            with open(os.environ['CRAFT_BRAND_FAULT_LOG'], 'a') as stream:
                stream.write(json.dumps({'objectId': int(target), 'nativeReply': injected})+'\\n')
        return result
Session = _BrandFaultSession
'''


def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}


@unittest.skipUnless(os.environ.get('CRAFT_VECTOR_BRAND_GUARD_NATIVE') == '1',
                     'explicit native opt-in; source candidate or fixed installed skill')
class BrandGuardNativeTests(unittest.TestCase):
    def test_public_token_guard_rejects_wrong_dependency_and_retains_checkpoint(self):
        retained = os.environ.get('CRAFT_BRAND_GUARD_RETAINED')
        if retained:
            root = Path(retained); self.assertTrue(root.is_absolute())
            root.mkdir(parents=True, exist_ok=False)
            context = contextlib.nullcontext(str(root))
        else:
            context = tempfile.TemporaryDirectory(prefix='vector-brand-guard-')
        with context as temporary:
            root = Path(temporary).resolve()
            origin = Path(os.environ.get('CRAFT_INSTALLED_BRAND_GUARD_SKILL', ROOT/'skills/vectorcraft-cli-appearance'))
            fixed_installed = False
            if os.environ.get('CRAFT_BRAND_GUARD_HOST_PROOF'):
                host=json.loads(Path(os.environ['CRAFT_BRAND_GUARD_HOST_PROOF']).read_text())
                entry=next(row for row in host['skills'] if row['name']=='vectorcraft-cli-appearance')
                self.assertEqual(host['result'],'PASS');self.assertEqual(origin.resolve(),Path(entry['path']).resolve())
                actual=hashes(origin)
                identity=hashlib.sha256(''.join(name+'\0'+actual[name]+'\n' for name in sorted(actual)).encode()).hexdigest()
                self.assertEqual(identity,entry['sha256']);fixed_installed=True
            skill = root/'.agents/skills'/origin.name
            shutil.copytree(origin, skill, ignore=shutil.ignore_patterns('__pycache__'))
            self.assertEqual(len(list(skill.parent.iterdir())), 1)
            baseline = os.environ.get('CRAFT_BRAND_GUARD_BASELINE_WORKFLOW')
            if baseline:
                shutil.copyfile(baseline, skill/'scripts/workflow.py')
            runtime = Path(os.environ['CRAFT_BRAND_GUARD_RUNTIME'])
            self.assertTrue(runtime.is_dir())
            environment = dict(os.environ, PATH='/usr/bin:/bin')
            for key in ('CRAFT_NODE_ARCHIVE', 'CRAFT_BUNDLE_DIRECTORY', 'CRAFT_NATIVE_ARCHIVE_DIRECTORY', 'CRAFT_RUNTIME_HOME', 'CRAFT_BRAND_FAULT_OBJECT'):
                environment.pop(key, None)
            plan = {'document': {'name': 'Same RGB different dependencies', 'width': 128, 'height': 128, 'units': 'Pixels'},
                    'operations': [
                        {'command': 'shape.rectangle', 'params': {'x': 8, 'y': 8, 'width': 32, 'height': 32}, 'as': 'bound'},
                        {'command': 'swatch.new', 'params': {'name': 'Brand Primary', 'color': '#2366e8', 'global': True}, 'as': 'primary'},
                        {'command': 'paint.setFill', 'params': {'ids': [{'$ref': 'bound.id'}], 'swatch': {'$ref': 'primary.name'}}},
                        {'command': 'shape.rectangle', 'params': {'x': 80, 'y': 8, 'width': 32, 'height': 32}, 'as': 'control'},
                        {'command': 'paint.setFill', 'params': {'ids': [{'$ref': 'control.id'}], 'color': '#2366e8'}},
                        {'command': 'text.create', 'params': {'x': 8, 'y': 64, 'text': 'NOVA',
                         'size': 12, 'font': 'Source Sans 3'}, 'as': 'wordmark'},
                        {'command': 'paint.setFill', 'params': {'ids': [{'$ref': 'wordmark.id'}],
                         'swatch': {'$ref': 'primary.name'}}}],
                    'exports': [{'format': 'svg', 'artboard': 0}, {'format': 'png', 'artboard': 0}]}
            if os.environ.get('CRAFT_BRAND_GUARD_WITH_ASSET') == '1':
                from PIL import Image
                image = root/'input.png'; Image.new('RGBA', (16, 16), (239, 91, 54, 255)).save(image)
                plan['assets'] = {'badge': {'path': str(image), 'sha256': hashlib.sha256(image.read_bytes()).hexdigest()}}
                plan['operations'].append({'command': 'asset.place', 'params': {'asset': 'badge', 'rect': [8, 80, 16, 16], 'link': True}})

            def run(name, value, source=None, fault=None, fault_command=None):
                p = root/(name+'.json'); p.write_text(json.dumps(value))
                argv = [sys.executable, '-I', '-B', str(skill/'scripts/workflow.py'), str(p), '--output', str(root/name), '--runtime-home', str(runtime)]
                if source: argv += ['--source', str(source)]
                env = dict(environment)
                if fault:
                    env.update(CRAFT_BRAND_FAULT_OBJECT=str(fault), CRAFT_BRAND_FAULT_LOG=str(root/(name+'-injection.jsonl')))
                    if fault_command: env['CRAFT_BRAND_FAULT_COMMAND']=json.dumps(fault_command)
                result = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=180)
                (root/(name+'.log')).write_text(result.stdout+result.stderr)
                return result

            created = run('source', plan)
            self.assertEqual(created.returncode, 0, created.stdout+created.stderr)
            source = root/'source'; manifest = json.loads((source/'manifest.json').read_text())
            original = hashes(source); target = manifest['bindings']['control']['id']
            revision = {'expectedProjectSha256': manifest['files']['project.vectorcraft'],
                        'operations': [{'command': 'swatch.edit', 'params': {'name': 'Brand Primary', 'color': '#175cce'}}],
                        'exports': plan['exports']}
            # Instrument only the isolated QA copy; preserve and bind this exact change.
            session_path = skill/'scripts/mcp_session.py'
            with session_path.open('a') as stream: stream.write('\nimport os\n'+PROXY)
            instrumented_identity = hashes(skill)
            def module(name):
                spec = importlib.util.spec_from_file_location('guard_native_'+name, skill/('scripts/'+name+'.py'))
                value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
                return value
            cli = module('bootstrap').install(json.loads((skill/'scripts/runtime.lock.json').read_text()), runtime)['executable']
            sessions = module('mcp_session')
            failures = []
            faults=[('nonconsumer',target,None),
                    ('consumer-geometry',manifest['bindings']['bound']['id'],{'command':'object.transform','params':{'ids':[manifest['bindings']['bound']['id']],'matrix':[1,0,0,1,9,0]}}),
                    ('consumer-text',manifest['bindings']['wordmark']['id'],{'command':'text.setText','params':{'id':manifest['bindings']['wordmark']['id'],'text':'WRONG'}}),
                    ('consumer-stroke',manifest['bindings']['bound']['id'],{'command':'paint.setStroke','params':{'ids':[manifest['bindings']['bound']['id']],'color':'#ff0000'}})]
            for route,kind,target,fault_command in [(mode,kind,target,command) for mode in ('direct','native-gateway') for kind,target,command in faults]:
                mode=route+'-'+kind
                value = json.loads(json.dumps(revision))
                if route == 'native-gateway':
                    value['operations'] = [{'command': 'native.command', 'params': value['operations'][0]}]
                result = run(mode, value, source, target, fault_command)
                self.assertNotEqual(result.returncode, 0, 'unguarded workflow accepted a real native non-consumer mutation')
                self.assertIn('brand_dependency_violation', result.stdout)
                output = root/mode
                self.assertFalse((output/'manifest.json').exists())
                failure = json.loads((output/'failure.json').read_text())
                self.assertFalse(failure['replayAllowed'])
                stage = (output/failure['stage']).resolve()
                self.assertTrue(stage.is_relative_to(root))
                report = json.loads((stage/'brand-dependencies.json').read_text())['checks'][0]
                self.assertEqual(report['status'], 'failed')
                self.assertEqual(report['affectedObjectIds'], [target])
                self.assertTrue(report['checkpointRetained'])
                self.assertTrue((stage/report['checkpoint']).is_file())
                with sessions.Session([cli, 'mcp', '--headless']) as reopened:
                    reopened.command('document.open', {'path': str(stage/report['checkpoint'])})
                    checkpoint_native = reopened.command('document.json', {})
                    if plan.get('assets'):
                        links = reopened.command('links.check', {})
                        self.assertFalse(links['missing']); self.assertFalse(links['modified'])
                source_native = json.loads((source/'native.json').read_text())
                # 链接会在暂存中重定位，路径与文件时间戳可合法变化；核对品牌对象原状态及真实依赖可读性。
                model = module('brand_variants')
                checkpoint_objects = model.snapshot(checkpoint_native)
                source_objects = model.snapshot(source_native)
                for object_id in [manifest['bindings']['bound']['id'], target]:
                    self.assertEqual(checkpoint_objects[object_id], source_objects[object_id])
                self.assertEqual(checkpoint_native['artboards'], source_native['artboards'])
                for name, record in failure['files'].items():
                    self.assertEqual(hashlib.sha256((stage/name).read_bytes()).hexdigest(), record['sha256'])
                injected = [json.loads(line) for line in (root/(mode+'-injection.jsonl')).read_text().splitlines()]
                self.assertEqual(len(injected), 1)
                self.assertFalse(injected[0]['nativeReply'].get('isError', False))
                failures.append({'mode': mode, 'report': report, 'retainedFileHashesVerified': True,
                                 'checkpointIndependentlyReopened': True, 'injectionCount': 1})
                self.assertEqual(hashes(source), original)
            healthy = run('healthy', revision, source)
            self.assertEqual(healthy.returncode, 0, healthy.stdout+healthy.stderr)
            healthy_manifest = json.loads((root/'healthy/manifest.json').read_text())
            report_path = healthy_manifest['brandDependencyReport']['path']
            report = json.loads((root/'healthy'/report_path).read_text())
            self.assertEqual(report['checks'][0]['status'], 'passed')
            self.assertEqual(report['checks'][0]['consumerIds'], sorted([
                manifest['bindings']['bound']['id'], manifest['bindings']['wordmark']['id']]))
            self.assertFalse(report['checks'][0]['checkpointRetained'])
            self.assertFalse((root/'healthy'/report['checks'][0]['checkpoint']).exists())
            self.assertEqual(hashlib.sha256((root/'healthy'/report_path).read_bytes()).hexdigest(), healthy_manifest['brandDependencyReport']['sha256'])
            from PIL import Image
            for directory in (source, root/'healthy'):
                with Image.open(directory/'artboard-1.png') as image:
                    self.assertEqual(image.convert('RGBA').getpixel((90, 20)), (35, 102, 232, 255))
            self.assertEqual(hashes(skill), instrumented_identity)
            self.assertEqual(hashes(source), original)
            self.assertFalse(list(skill.rglob('*.pyc')))
            (root/'acceptance.json').write_text(json.dumps({'schema': 'vectorcraft-brand-guard-native/v1',
                'status': 'passed', 'fixedInstalled': fixed_installed,
                'runtimeReused': True, 'nativeRuntimeSha256': manifest['runtimeSha256'],
                'faultInjection': 'QA-only extra real native consumer text/geometry/stroke and non-consumer fill after swatch.edit reply',
                'failures': failures, 'healthyReport': report, 'sourceFiles': original,
                'healthyFiles': hashes(root/'healthy'), 'instrumentedSkillFiles': instrumented_identity,
                'driverSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, indent=2)+'\n')


if __name__ == '__main__':
    unittest.main()
