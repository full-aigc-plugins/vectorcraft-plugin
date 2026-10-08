"""计划边界和对象引用测试，不需要安装原生 CLI。"""
import importlib.util
from pathlib import Path
import unittest
import json
import tempfile

SOURCE = Path(__file__).resolve().parents[1] / 'skills/vectorcraft-use/scripts/workflow.py'

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('workflow', SOURCE)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_resolve_only_explicit_references(self):
        value = {'ids': [{'$ref': 'logo.id'}], 'text': 'logo.id'}
        self.assertEqual(self.module.resolve(value, {'logo': {'id': 12}}), {'ids': [12], 'text': 'logo.id'})

    def test_unknown_reference_is_an_error(self):
        with self.assertRaisesRegex(ValueError, 'unresolved_reference'):
            self.module.resolve({'$ref': 'missing.id'}, {})

    def test_file_side_effect_commands_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unsupported_command'):
            self.module.validate({'operations': [{'command': 'document.save', 'params': {'path': '/outside'}}]})

    def test_brand_revision_rejects_untrusted_export_plan_before_runtime(self):
        for mode in ('modified', 'symlink'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = root / 'source'
                source.mkdir()
                project = source / 'project.vectorcraft'
                project.write_bytes(b'project fixture')
                original = json.dumps({'exports': [{'format': 'png', 'artboard': 0}]})
                plan_path = source / 'plan.json'
                plan_path.write_text(original)
                manifest = {'files': {'project.vectorcraft': self.module.sha(project), 'plan.json': self.module.sha(plan_path)}, 'bindings': {}}
                (source / 'manifest.json').write_text(json.dumps(manifest))
                if mode == 'modified':
                    plan_path.write_text('{}')
                else:
                    external = root / 'external.json'
                    external.write_text(original)
                    plan_path.unlink()
                    plan_path.symlink_to(external)
                revision = {'expectedProjectSha256': manifest['files']['project.vectorcraft'], 'operations': [{'command': 'swatch.edit', 'params': {'name': 'Brand Primary', 'color': '#175cce'}}]}
                output = root / 'revision'
                runtime = root / 'runtime'
                with self.assertRaisesRegex(ValueError, 'brand_source_plan_digest_mismatch'):
                    self.module.execute(revision, output, source=source, runtime_home=runtime)
                self.assertFalse(output.exists())
                self.assertFalse(runtime.exists())
                self.assertEqual(project.read_bytes(), b'project fixture')

    def test_text_edit_requires_explicit_valid_target(self):
        invalid = [{'text': '新标题'}, {'id': 1, 'ids': [2], 'text': '新标题'}, {'ids': [], 'text': '新标题'}, {'id': True, 'text': '新标题'}, {'id': 1, 'text': 42}, {'id': 1, 'text': '新标题', 'font': 'Other'}]
        for params in invalid:
            with self.subTest(params=params), self.assertRaisesRegex(ValueError, 'invalid_text_edit'):
                self.module.validate({'operations': [{'command': 'text.setText', 'params': params}]})

    def test_text_edit_gateway_and_complete_entry_require_explicit_targets(self):
        invalid = [{'text':'新标题'}, {'id':1,'ids':[2],'text':'新标题'}, {'ids':[],'text':'新标题'}, {'id':True,'text':'新标题'}, {'id':1,'text':42}, {'id':1,'text':'新标题','font':'Other'}]
        commands=self.module.native_module().commands
        for params in invalid:
            with self.subTest(route='gateway',params=params), self.assertRaisesRegex(ValueError,'invalid_text_edit'):
                self.module.validate({'operations':[{'command':'native.command','params':{'command':'text.setText','params':params}}]})
            with self.subTest(route='complete',params=params), self.assertRaisesRegex(ValueError,'invalid_text_edit'):
                commands.validate({'schema':'craft-command-plan/v1','operations':[{'command':'text.setText','params':params}]})
        self.module.validate({'operations':[{'command':'native.command','params':{'command':'text.setText','params':{'id':1,'text':'新标题'}}}]})
        commands.validate({'schema':'craft-command-plan/v1','operations':[{'command':'text.setText','params':{'id':1,'text':'新标题'}}]})

    def test_duplicate_alias_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate_alias'):
            self.module.validate({'operations': [{'command': 'shape.rectangle', 'as': 'logo'}, {'command': 'shape.ellipse', 'as': 'logo'}]})

    def test_registered_asset_operations_and_path_rejection(self):
        self.module.validate({'operations': [{'command': 'asset.place', 'params': {'asset': 'product', 'rect': [0, 0, 80, 50]}}, {'command': 'asset.replace', 'params': {'asset': 'product', 'replacement': 'updated'}}]})
        for params in ({'asset': 'product', 'path': '/outside'}, {'asset': '../evil'}, {'asset': 'product', 'rect': [0, 0, -1, 5]}, {'asset': 'product', 'link': 'true'}):
            with self.subTest(params=params), self.assertRaisesRegex(ValueError, 'invalid_asset_operation'):
                self.module.validate({'operations': [{'command': 'asset.place', 'params': params}]})

    def test_asset_digest_and_unused_input_fail_before_installation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            asset = root / 'product.png'
            asset.write_bytes(b'synthetic invalid pixels')
            for digest, operations, error in [('0'*64, [{'command': 'asset.place', 'params': {'asset': 'product'}}], 'asset_digest_mismatch'), (self.module.sha(asset), [], 'asset_not_consumed')]:
                plan = {'document': {'width': 80, 'height': 50}, 'assets': {'product': {'path': str(asset), 'sha256': digest}}, 'operations': operations}
                with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                    self.module.execute(plan, root/'delivery', runtime_home=root/'runtime')
                self.assertFalse((root/'runtime').exists())
                self.assertFalse((root/'delivery').exists())

    def test_svg_external_dependency_and_inherited_asset_corruption_preflight(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = root/'logo.svg'
            image.write_text('<svg xmlns="http://www.w3.org/2000/svg"><image href="file:///outside.png"/></svg>')
            plan = {'document': {'width': 80, 'height': 50}, 'assets': {'logo': {'path': str(image), 'sha256': self.module.sha(image)}}, 'operations': [{'command': 'asset.place', 'params': {'asset': 'logo'}}]}
            with self.assertRaisesRegex(ValueError, 'asset_svg_external_dependency'):
                self.module.execute(plan, root/'delivery', runtime_home=root/'runtime')
            source = root/'source';source.mkdir()
            project = source/'project.vectorcraft';project.write_bytes(b'project fixture')
            dependency = source/'image.png';dependency.write_bytes(b'old asset')
            prior = {'files': {'project.vectorcraft': self.module.sha(project), 'image.png': self.module.sha(dependency)}, 'bindings': {}, 'assets': {'product': {'path': 'image.png', 'sha256': self.module.sha(dependency), 'ids': [4], 'linked': True}}}
            (source/'manifest.json').write_text(json.dumps(prior));dependency.write_bytes(b'corrupted asset')
            with self.assertRaisesRegex(ValueError, 'asset_digest_mismatch'):
                self.module.execute({'expectedProjectSha256': prior['files']['project.vectorcraft'], 'operations': []}, root/'revision', source=source, runtime_home=root/'runtime')
            self.assertFalse((root/'runtime').exists());self.assertFalse((root/'revision').exists())

    def test_export_range_and_format_rejected(self):
        for output in [{'format': 'exe', 'artboard': 0}, {'format': 'png', 'artboard': -1}]:
            with self.assertRaises(ValueError):
                self.module.validate({'operations': [], 'exports': [output]})

if __name__ == '__main__':
    unittest.main()
