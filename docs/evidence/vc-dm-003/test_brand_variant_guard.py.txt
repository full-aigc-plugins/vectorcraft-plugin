"""品牌依赖守卫：以原生对象关系识别错误更新，不按颜色推断依赖。"""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    paint = {'color': '#2366e8', 'swatch': 'Brand Primary', 'type': 'solid'}
    return {'layers': [{'id': 1, 'kind': {'type': 'layer', 'children': [
        {'id': 2, 'kind': {'type': 'path', 'path': {'closed': True}}, 'paint': paint},
        {'id': 3, 'kind': {'type': 'path'}, 'paint': {'color': '#2366e8', 'type': 'solid'}},
        {'id': 4, 'kind': {'type': 'text', 'runs': [{'style': {'fill': copy.deepcopy(paint)}, 'text': 'NOVA'}]}}
    ]}}], 'artboards': [{'id': 10, 'rect': [0, 0, 256, 256]}]}


class BrandVariantGuardTests(unittest.TestCase):
    def setUp(self):
        path = ROOT/'skills/vectorcraft-use/scripts/brand_variants.py'
        spec = importlib.util.spec_from_file_location('brand_variants_test', path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_linked_shapes_and_text_only_change(self):
        before = fixture(); after = copy.deepcopy(before)
        after['layers'][0]['kind']['children'][0]['paint']['color'] = '#175cce'
        after['layers'][0]['kind']['children'][2]['kind']['runs'][0]['style']['fill']['color'] = '#175cce'
        report = self.module.inspect_update(before, after, 'Brand Primary')
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['consumerIds'], [2, 4])
        self.assertEqual(report['affectedObjectIds'], [])

    def test_same_rgb_nonconsumer_changes_report_wrong_edge(self):
        before = fixture(); after = copy.deepcopy(before)
        after['layers'][0]['kind']['children'][1]['paint']['color'] = '#175cce'
        report = self.module.inspect_update(before, after, 'Brand Primary')
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['affectedObjectIds'], [3])
        self.assertEqual(report['unexpectedDependencies'], [{'token': 'Brand Primary', 'objectId': 3,
                                                            'reason': 'unbound_object_changed'}])

    def test_new_deleted_objects_and_container_property_changes_rejected(self):
        before = fixture()
        for mode, expected in [('new', [1, 8]), ('delete', [1, 3]), ('container', [1])]:
            with self.subTest(mode=mode):
                after = copy.deepcopy(before)
                children = after['layers'][0]['kind']['children']
                if mode == 'new': children.append({'id': 8, 'kind': {'type': 'path'}})
                if mode == 'delete': children.pop(1)
                if mode == 'container': after['layers'][0]['name'] = 'Unexpected rename'
                report = self.module.inspect_update(before, after, 'Brand Primary')
                self.assertEqual(report['status'], 'failed')
                self.assertEqual(report['affectedObjectIds'], expected)

    def test_artboard_change_rejected(self):
        before = fixture(); after = copy.deepcopy(before)
        after['artboards'][0]['rect'] = [0, 0, 512, 512]
        report = self.module.inspect_update(before, after, 'Brand Primary')
        self.assertEqual(report['status'], 'failed')
        self.assertTrue(report['artboardsChanged'])

    def test_consumer_container_cannot_reorder_children(self):
        before = fixture(); before['layers'][0]['paint'] = {'swatch': 'Brand Primary'}
        after = copy.deepcopy(before)
        after['layers'][0]['kind']['children'].reverse()
        report = self.module.inspect_update(before, after, 'Brand Primary')
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['affectedObjectIds'], [1])

    def test_duplicate_or_invalid_native_id_fails_closed(self):
        for invalid in [True, 2, None]:
            before = fixture(); before['layers'][0]['kind']['children'][1]['id'] = invalid
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, 'invalid_brand_snapshot'):
                self.module.inspect_update(before, before, 'Brand Primary')

    def test_consumer_deleted_is_not_a_legal_color_update(self):
        before = fixture(); after = copy.deepcopy(before)
        after['layers'][0]['kind']['children'].pop(0)
        report = self.module.inspect_update(before, after, 'Brand Primary')
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['affectedObjectIds'], [1, 2])

    def test_consumer_noncolor_fields_cannot_change(self):
        before = fixture()
        for field in ('closed', 'text', 'transform', 'appearance'):
            with self.subTest(field=field):
                after = copy.deepcopy(before)
                children = after['layers'][0]['kind']['children']
                if field == 'closed': children[0]['kind']['path']['closed'] = False
                if field == 'text': children[2]['kind']['runs'][0]['text'] = 'UNEXPECTED'
                if field == 'transform': children[0]['transform'] = [1, 0, 0, 1, 100, 0]
                if field == 'appearance': children[0]['paint']['opacity'] = .1
                report = self.module.inspect_update(before, after, 'Brand Primary')
                self.assertEqual(report['status'], 'failed')
                self.assertTrue(report['affectedObjectIds'])

    def test_expected_color_requires_every_bound_field_to_reach_target(self):
        before = fixture(); after = copy.deepcopy(before)
        after['layers'][0]['kind']['children'][0]['paint']['color'] = '#175cce'
        # 路径更新不能掩盖文字消费者未更新。
        report = self.module.inspect_update(before, after, 'Brand Primary', '#175cce')
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['targetMismatchObjectIds'], [4])

    def test_valid_noop_and_missing_consumers_are_explicit(self):
        before = fixture()
        report = self.module.inspect_update(before, before, 'Brand Primary', '#2366e8')
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['effect'], 'verified_noop')
        unchanged = self.module.inspect_update(before, before, 'Brand Primary', '#175cce')
        self.assertEqual(unchanged['status'], 'failed')
        missing = self.module.inspect_update(before, before, 'Missing Token', '#175cce')
        self.assertEqual(missing['status'], 'failed')
        self.assertEqual(missing['effect'], 'no_effect')

    def test_target_swatch_and_unrelated_palette_entries_are_checked(self):
        before = fixture()
        before['swatches'] = [{'name':'Brand Primary', 'paint':{'color':'#2366e8'}},
                              {'name':'Other', 'paint':{'color':'#000000'}}]
        after = copy.deepcopy(before)
        after['layers'][0]['kind']['children'][0]['paint']['color'] = '#175cce'
        after['layers'][0]['kind']['children'][2]['kind']['runs'][0]['style']['fill']['color'] = '#175cce'
        report = self.module.inspect_update(before, after, 'Brand Primary', '#175cce')
        self.assertEqual(report['status'], 'failed', 'consumers cannot mask a swatch still at the old value')
        after['swatches'][0]['paint']['color'] = '#175cce'
        report = self.module.inspect_update(before, after, 'Brand Primary', '#175cce')
        self.assertEqual(report['status'], 'passed')
        after['swatches'][1]['paint']['color'] = '#ffffff'
        report = self.module.inspect_update(before, after, 'Brand Primary', '#175cce')
        self.assertEqual(report['status'], 'failed')

    def test_authoring_models_and_tints_preserve_their_native_semantics(self):
        cases = [({'model':'cmyk','c':.2,'m':.4,'y':.6,'k':.8}, {'model':'cmyk','c':.1,'m':.2,'y':.3,'k':.4}),
                 ({'model':'gray','k':.6}, {'model':'gray','k':.3}),
                 ({'model':'lab','l':40.,'a':20.,'b':-30.}, {'model':'lab','l':70.,'a':10.,'b':-15.})]
        for target, tinted in cases:
            with self.subTest(model=target['model']):
                before=fixture();after=copy.deepcopy(before)
                for child in after['layers'][0]['kind']['children']:
                    if child['id']==2: child['paint'].update(color=target)
                    if child['id']==4: child['kind']['runs'][0]['style']['fill'].update(color=tinted,tint=.5)
                before['layers'][0]['kind']['children'][2]['kind']['runs'][0]['style']['fill']['tint']=.5
                report=self.module.inspect_update(before,after,'Brand Primary',target)
                self.assertEqual(report['status'],'passed')


if __name__ == '__main__':
    unittest.main()
