"""全局原生色板作为品牌 token：跨画板更新、独立原生重开和无关输出保留。"""
import importlib.util
import sys
sys.dont_write_bytecode=True
import json
import os
from pathlib import Path
import tempfile
import shutil
import unittest
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(os.environ.get('CRAFT_LIVE_TEST')=='1','requires actual native CLI and Pillow')
class BrandTokenNativeTests(unittest.TestCase):
 def test_native_global_swatch_updates_registered_variants_and_preserves_accent(self):
  from PIL import Image
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);single=root/'single appearance skill';installed=os.environ.get('CRAFT_INSTALLED_TOKEN_SKILL_ROOT')
   shutil.copytree(Path(installed) if installed else ROOT/'skills/vectorcraft-cli-appearance',single,ignore=shutil.ignore_patterns('__pycache__'))
   spec=importlib.util.spec_from_file_location('isolated_token_workflow',single/'scripts/workflow.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
   plan=json.loads((single/'examples/brand-token-assets.json').read_text())
   first=root/'v1';second=root/'v2';runtime=Path(os.environ['CRAFT_BRAND_TOKEN_RUNTIME']) if os.environ.get('CRAFT_BRAND_TOKEN_RUNTIME') else root/'fresh runtime';a=m.execute(plan,first,runtime_home=runtime)
   revision={'expectedProjectSha256':a['files']['project.vectorcraft'],'operations':[{'command':'swatch.edit','params':{'name':{'$ref':'primary.name'},'color':'#175cce'}}]}
   b=m.execute(revision,second,source=first,runtime_home=runtime)
   for index in [1,3]:
    with Image.open(first/f'artboard-{index}.png') as old,Image.open(second/f'artboard-{index}.png') as new:
     old_colors={color for count,color in old.convert('RGBA').getcolors(old.width*old.height)};new_colors={color for count,color in new.convert('RGBA').getcolors(new.width*new.height)}
     self.assertIn((35,102,232,255),old_colors);self.assertIn((23,92,206,255),new_colors);self.assertNotEqual(old.tobytes(),new.tobytes())
    svg=(second/f'artboard-{index}.svg').read_text().lower().replace(' ','');self.assertTrue('#175cce' in svg or 'rgb(23,92,206)' in svg)
   self.assertEqual((first/'artboard-2.png').read_bytes(),(second/'artboard-2.png').read_bytes())
   self.assertEqual(m.sha(first/'project.vectorcraft'),a['files']['project.vectorcraft'])
   native=json.loads((second/'native.json').read_text());self.assertEqual(len(native['artboards']),3)
   receipts=json.loads((second/'operations.json').read_text());edit=next(r for r in receipts if r['command']=='swatch.edit');self.assertGreaterEqual(edit['result']['relinked'],3)
   self.assertEqual(b['sourceProjectSha256'],a['files']['project.vectorcraft'])
   bad=dict(revision,operations=[{'command':'swatch.edit','params':{'name':'MissingBrandToken-72625','color':'#ffffff'}}])
   with self.assertRaises((ValueError,RuntimeError)):m.execute(bad,root/'unknown-token',source=first,runtime_home=runtime)
   # 已进入原生操作的失败保留原位置现场；不得用目录不存在误判安全拒绝。
   failure=json.loads((root/'unknown-token/failure.json').read_text())
   self.assertFalse(failure['replayAllowed']);self.assertFalse((root/'unknown-token/manifest.json').exists())
   stage=(root/'unknown-token'/failure['stage']).resolve()
   for name,row in failure['files'].items():self.assertEqual(m.sha(stage/name),row['sha256'])
   self.assertEqual({o['path'] for o in a['outputs']},{o['path'] for o in b['outputs']})
   (first/'plan.json').write_text('{}')
   with self.assertRaisesRegex(ValueError,'brand_source_plan_digest_mismatch'):m.execute(revision,root/'tampered-plan',source=first,runtime_home=runtime)
   self.assertFalse((root/'tampered-plan').exists())
   self.assertFalse(any(single.rglob('*.pyc')))
if __name__=='__main__':unittest.main()
