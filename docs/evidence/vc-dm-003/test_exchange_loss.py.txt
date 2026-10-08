"""交换报告的来源绑定、格式损失与路径拒绝；原生保真另由实际 CLI 验收。"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SOURCE=Path(__file__).resolve().parents[1]/'skills/vectorcraft-use/scripts/exchange_loss.py'
class ExchangeLossTests(unittest.TestCase):
 def module(self):
  spec=importlib.util.spec_from_file_location('exchange_loss',SOURCE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def test_report_binds_native_and_exports_and_never_claims_unknown_fidelity(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/m.NATIVE).write_bytes(b'editable native');(root/'native.json').write_text(json.dumps({'layers':[{'id':1}]}))
   (root/'preview.png').write_bytes(bytes.fromhex('89504e470d0a1a0a')+b'\x00'*17+b'\x06'+b'\x00'*8)
   result=m.write_report(root,['preview.png'],{})
   self.assertEqual(result['native']['location'],m.NATIVE);self.assertEqual(result['native']['sha256'],m.sha(root/m.NATIVE))
   self.assertTrue(any(x['status']=='lost' for x in result['outputs'][0]['changes']))
   self.assertFalse(result['outputs'][0]['nativeSubstitute']);self.assertEqual(result['outputs'][0]['role'],'derivative')
   self.assertEqual(json.loads((root/'exchange-loss.json').read_text()),result)
 def test_missing_native_and_escaping_export_are_rejected(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   with self.assertRaises(ValueError):m.write_report(root,[],{})
   (root/m.NATIVE).write_bytes(b'native');(root/'native.json').write_text('{}')
   with self.assertRaises(ValueError):m.write_report(root,['../outside.png'],{})
 def test_svg_font_and_effect_fidelity_remain_explicitly_unknown(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/m.NATIVE).write_bytes(b'native');(root/'native.json').write_text('{}')
   (root/'graphic.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0L1 1"/><text>Logo</text></svg>')
   report=m.write_report(root,['graphic.svg'],{})
   changes={x['code']:x['status'] for x in report['outputs'][0]['changes']}
   self.assertEqual(changes['font-portability'],'unknown');self.assertEqual(changes['effect-fidelity'],'unknown')
   self.assertEqual(report['outputs'][0]['observations']['svg']['text'],1)
 def test_observed_appearance_mode_reports_loss_of_live_text_editing(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/m.NATIVE).write_bytes(b'native fixture');(root/'native.json').write_text(json.dumps({'layers':[{'id':7,'kind':{'type':'text','runs':[{'text':'Logo'}]}}]}))
   (root/'graphic.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0L1 1"/></svg>')
   report=m.write_report(root,['graphic.svg'],{}, {'graphic.svg':'appearance'})
   output=report['outputs'][0];changes={x['code']:x['status'] for x in output['changes']}
   self.assertEqual(changes['live-text-editability'],'lost');self.assertEqual(output['observations']['svgTextExportMode'],'appearance')
   self.assertEqual(output['observations']['nativeTextObjectIds'],[7]);self.assertFalse(output['nativeSubstitute'])
 def test_paths_alone_do_not_prove_text_was_outlined(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/m.NATIVE).write_bytes(b'native fixture');(root/'native.json').write_text(json.dumps({'layers':[{'id':7,'kind':{'type':'text'}}]}))
   (root/'graphic.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0L1 1"/></svg>')
   report=m.write_report(root,['graphic.svg'],{})
   self.assertEqual(next(x['status'] for x in report['outputs'][0]['changes'] if x['code']=='live-text-editability'),'unknown')
 def test_editable_svg_text_remains_an_observation_not_roundtrip_fidelity(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/m.NATIVE).write_bytes(b'native fixture');(root/'native.json').write_text('{}');(root/'graphic.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><text>Logo</text></svg>')
   report=m.write_report(root,['graphic.svg'],{}, {'graphic.svg':'editable'})
   changes={x['code']:x['status'] for x in report['outputs'][0]['changes']}
   self.assertEqual(changes['live-text-editability'],'observed');self.assertEqual(changes['font-portability'],'unknown')
 def test_invalid_text_mode_or_nonoutput_metadata_is_refused(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/m.NATIVE).write_bytes(b'native fixture');(root/'native.json').write_text('{}');(root/'graphic.svg').write_text('<svg/>')
   for metadata in [{'graphic.svg':'outlined'}, {'other.svg':'appearance'}, {'graphic.svg':True}]:
    with self.subTest(metadata=metadata),self.assertRaisesRegex(ValueError,'loss_text_mode_invalid'):m.write_report(root,['graphic.svg'],{},metadata)

if __name__=='__main__':unittest.main()
