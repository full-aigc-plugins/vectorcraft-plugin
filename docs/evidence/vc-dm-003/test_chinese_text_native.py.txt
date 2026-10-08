"""中文矢量文字原生创建、定点修订与无关文字保留。"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(os.environ.get('CRAFT_LIVE_TEST')=='1','requires actual macOS native CLI and Pillow')
class ChineseTextNativeTests(unittest.TestCase):
 def test_single_text_skill_edits_chinese_header_without_touching_unrelated_text(self):
  from PIL import Image,ImageChops
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);skill=root/'.agents/skills/vectorcraft-cli-text'
   shutil.copytree(Path(os.environ.get('CRAFT_INSTALLED_TEXT_SKILL_ROOT',ROOT/'skills/vectorcraft-cli-text')),skill,ignore=shutil.ignore_patterns('__pycache__'))
   spec=importlib.util.spec_from_file_location('w',skill/'scripts/workflow.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
   plan=json.loads((skill/'examples/chinese-text.json').read_text());runtime=root/'fresh runtime';first=root/'v1';second=root/'v2'
   a=m.execute(plan,first,runtime_home=runtime)
   if os.environ.get('CRAFT_TEXT_EVIDENCE_DIR'):
    evidence=Path(os.environ['CRAFT_TEXT_EVIDENCE_DIR']);evidence.mkdir(parents=True,exist_ok=False);shutil.copytree(first,evidence/'v1')
   revision={'expectedProjectSha256':a['files']['project.vectorcraft'],'operations':[{'command':'text.setText','params':{'id':{'$ref':'headline.id'},'text':'品牌焕新'}}],'exports':plan['exports']}
   b=m.execute(revision,second,source=first,runtime_home=runtime)
   original=(first/'native.json').read_text();revised=(second/'native.json').read_text()
   self.assertIn('新品上市',original);self.assertIn('品牌焕新',revised);self.assertNotIn('新品上市',revised)
   self.assertIn('Songti SC',revised);self.assertIn('SAFE',revised)
   self.assertTrue(all(not item['missing'] for item in b['fontDependencies']));self.assertTrue(any(item['family']=='Songti SC' for item in b['fontDependencies']))
   def run(value,text):
    if isinstance(value,dict):
     if value.get('text')==text and 'style' in value:return value
     for child in value.values():
      found=run(child,text)
      if found is not None:return found
    elif isinstance(value,list):
     for child in value:
      found=run(child,text)
      if found is not None:return found
   old_native=json.loads(original);new_native=json.loads(revised)
   self.assertEqual(run(old_native,'新品上市')['style'],run(new_native,'品牌焕新')['style'])
   self.assertEqual(run(old_native,'SAFE'),run(new_native,'SAFE'))
   with Image.open(first/'artboard-1.png') as old,Image.open(second/'artboard-1.png') as new:
    old=old.convert('RGBA');new=new.convert('RGBA');self.assertIsNotNone(ImageChops.difference(old.convert('RGB'),new.convert('RGB')).getbbox(),'same-length Chinese phrases must not render as identical missing glyphs')
    self.assertEqual(old.crop((0,110,320,180)).tobytes(),new.crop((0,110,320,180)).tobytes(),'unrelated footer pixels')
   svg=(second/'artboard-1.svg').read_text();self.assertIn('品牌焕新',svg);self.assertIn('Songti SC',svg)
   self.assertEqual(m.sha(first/'project.vectorcraft'),a['files']['project.vectorcraft']);self.assertEqual(b['sourceProjectSha256'],a['files']['project.vectorcraft'])
   bad={**revision,'operations':[{'command':'text.setText','params':{'id':999999999,'text':'其他标题'}}]}
   with self.assertRaises(RuntimeError):m.execute(bad,root/'missing-text',source=first,runtime_home=runtime)
   # VC-TX-004：原生执行已开始的失败保留现场，但不得发布成功清单。
   self.assertFalse((root/'missing-text/manifest.json').exists())
   text_failure=json.loads((root/'missing-text/failure.json').read_text());self.assertFalse(text_failure['replayAllowed'])
   self.assertFalse(any(skill.rglob('*.pyc')))
   if os.environ.get('CRAFT_TEXT_EVIDENCE_DIR'):shutil.copytree(root/'missing-text',evidence/'unknown-target-failure')
   invalid_font=json.loads(json.dumps(plan));invalid_font['operations'][0]['params']['font']='Craft Missing CJK Family 72625'
   with self.assertRaisesRegex(ValueError,'missing_fonts'):m.execute(invalid_font,root/'missing-font',runtime_home=runtime)
   self.assertFalse((root/'missing-font/manifest.json').exists())
   font_failure=json.loads((root/'missing-font/failure.json').read_text());self.assertFalse(font_failure['replayAllowed'])
   self.assertIn('missing_fonts',json.dumps(font_failure));self.assertEqual(m.sha(first/'project.vectorcraft'),a['files']['project.vectorcraft'])
   if os.environ.get('CRAFT_TEXT_EVIDENCE_DIR'):shutil.copytree(root/'missing-font',evidence/'missing-font-failure')
   if os.environ.get('CRAFT_TEXT_EVIDENCE_DIR'):shutil.copytree(second,evidence/'v2')
