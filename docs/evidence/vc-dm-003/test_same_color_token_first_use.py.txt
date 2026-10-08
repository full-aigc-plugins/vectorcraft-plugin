"""已安装外观技能：同色非消费者不得随品牌 token 修改。"""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True


def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}


def objects(value):
    result = {}
    if isinstance(value, dict):
        if 'id' in value and 'kind' in value:
            # 容器属性独立比较；子对象按自己的稳定 ID 比较，避免把合法子对象修改误报为容器修改。
            result[value['id']] = {**value, 'kind': {
                key: child for key, child in value['kind'].items() if key != 'children'}}
        for child in value.values():
            result.update(objects(child))
    elif isinstance(value, list):
        for child in value:
            result.update(objects(child))
    return result


@unittest.skipUnless(os.environ.get('CRAFT_VECTOR_SAME_COLOR_FIRST_USE') == '1',
                     'requires fixed installed appearance skill and native runtime')
class SameColorTokenFirstUseTests(unittest.TestCase):
    def test_public_revision_changes_consumers_only_even_when_rgb_matches(self):
        from PIL import Image
        retained = os.environ.get('CRAFT_VECTOR_SAME_COLOR_RETAINED')
        if retained:
            root = Path(retained)
            self.assertTrue(root.is_absolute())
            root.mkdir(parents=True, exist_ok=False)
            context = contextlib.nullcontext(str(root))
        else:
            context = tempfile.TemporaryDirectory(prefix='craft-vector-same-color-')
        with context as temporary:
            root = Path(temporary)
            skill = root / '.agents/skills/vectorcraft-cli-appearance'
            installed = Path(os.environ['CRAFT_INSTALLED_TOKEN_SKILL_ROOT'])
            shutil.copytree(installed, skill, ignore=shutil.ignore_patterns('__pycache__'))
            self.assertEqual(len(list(skill.parent.iterdir())), 1)
            identity = hashes(skill)
            runtime = Path(os.environ.get('CRAFT_VECTOR_SAME_COLOR_RUNTIME', root/'runtime'))
            reused = runtime.exists()
            environment = dict(os.environ, PATH='/usr/bin:/bin')
            for key in ('CRAFT_NODE_ARCHIVE', 'CRAFT_BUNDLE_DIRECTORY',
                        'CRAFT_NATIVE_ARCHIVE_DIRECTORY', 'CRAFT_RUNTIME_HOME'):
                environment.pop(key, None)
            plan = json.loads((skill/'examples/brand-token-assets.json').read_text())
            for alias, x in [('sameBoardUnbound', 8), ('otherBoardUnbound', 304)]:
                plan['operations'] += [
                    {'command': 'shape.rectangle', 'params': {'x': x, 'y': 220,
                     'width': 24, 'height': 24}, 'as': alias},
                    {'command': 'paint.setFill', 'params': {'ids': [{'$ref': alias+'.id'}],
                     'color': '#2366e8'}},
                    {'command': 'paint.setStroke', 'params': {'ids': [{'$ref': alias+'.id'}],
                     'none': True}}]

            def run(name, value, source=None):
                plan_file = root/(name+'.json')
                plan_file.write_text(json.dumps(value), encoding='utf-8')
                output = root/name
                argv = [sys.executable, '-I', '-B', str(skill/'scripts/workflow.py'),
                        str(plan_file), '--output', str(output), '--runtime-home', str(runtime)]
                if source:
                    argv += ['--source', str(source)]
                completed = subprocess.run(argv, env=environment, capture_output=True,
                                           text=True, timeout=180)
                (root/(name+'.log')).write_text(completed.stdout+completed.stderr, encoding='utf-8')
                self.assertEqual(completed.returncode, 0, completed.stdout+completed.stderr)
                manifest = json.loads((output/'manifest.json').read_text())
                actual = hashes(output)
                for filename, digest in manifest['files'].items():
                    self.assertEqual(actual[filename], digest)
                return output, manifest

            source, original = run('original', plan)
            source_hashes = hashes(source)
            revision = {'expectedProjectSha256': original['files']['project.vectorcraft'],
                        'operations': [{'command': 'swatch.edit', 'params': {
                            'name': {'$ref': 'primary.name'}, 'color': '#175cce'}}]}
            revised, updated = run('revised', revision, source)
            before = objects(json.loads((source/'native.json').read_text())['layers'])
            after = objects(json.loads((revised/'native.json').read_text())['layers'])
            self.assertEqual(set(before), set(after))
            consumers = [original['bindings']['logo']['ids'][0],
                         original['bindings']['wordmark']['id'], original['bindings']['variant']['id']]
            controls = [original['bindings'][key]['id'] for key in
                        ('sameBoardUnbound', 'otherBoardUnbound', 'icon')]
            for object_id in consumers:
                self.assertNotEqual(before[object_id], after[object_id], object_id)
            for object_id in set(before)-set(consumers):
                self.assertEqual(before[object_id], after[object_id], object_id)
            for index, position in [(1, (12, 224)), (2, (20, 224))]:
                for directory in (source, revised):
                    with Image.open(directory/f'artboard-{index}.png') as image:
                        self.assertEqual(image.convert('RGBA').getpixel(position), (35, 102, 232, 255))
            for index in (1, 3):
                with Image.open(source/f'artboard-{index}.png') as a, Image.open(revised/f'artboard-{index}.png') as b:
                    self.assertNotEqual(a.tobytes(), b.tobytes())
                self.assertIn('#175cce', (revised/f'artboard-{index}.svg').read_text().lower())
            for fmt in ('svg', 'png', 'pdf'):
                self.assertEqual((source/f'artboard-2.{fmt}').read_bytes(),
                                 (revised/f'artboard-2.{fmt}').read_bytes())
            self.assertEqual(original['bindings'], updated['bindings'])
            self.assertEqual(updated['sourceProjectSha256'], original['files']['project.vectorcraft'])
            self.assertEqual(source_hashes, hashes(source))
            self.assertEqual(identity, hashes(skill))
            self.assertFalse(list(skill.rglob('*.pyc')))
            proof = {'schema': 'vectorcraft-same-color-token-acceptance/v1', 'result': 'passed',
                     'scope': 'single supplied skill; fixed host installation recorded separately; public workflow create/revision; RGB token only',
                     'runtimeInitiallyPresent': reused, 'coldInstallClaimed': not reused,
                     'runtimeBinarySha256': original['runtimeSha256'],
                     'skillFiles': identity, 'sourceFiles': source_hashes, 'revisedFiles': hashes(revised),
                     'boundConsumerIds': consumers, 'unboundControlIds': controls,
                     'sameRgbUnboundPixelsPreserved': True, 'allUnboundObjectPropertiesPreserved': True,
                     'unrelatedBoardAllFormatsPreserved': True, 'sourceAndSkillPreserved': True,
                     'driverSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                     'excluded': ['full VC-DM-006 contract', 'asset replacement', 'all color models',
                                  'all commands', 'GUI', 'generic Skills CLI installation']}
            (root/'acceptance.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
