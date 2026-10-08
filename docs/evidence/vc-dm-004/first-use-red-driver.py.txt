"""固定单导出技能冷启动：不同画幅、偏移、品牌修订与独立 PDF 解码。"""
import hashlib
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET
sys.dont_write_bytecode = True

@unittest.skipUnless(os.environ.get('CRAFT_VECTOR_ARTBOARD_FIRST_USE') == '1', 'requires fixed installed skill, public CLI, existing Pillow and PyMuPDF')
class ArtboardExportFirstUseTests(unittest.TestCase):
    def test_three_distinct_artboards_keep_output_identity_and_selective_brand_update(self):
        from PIL import Image
        import fitz
        with tempfile.TemporaryDirectory(prefix='craft-vector-artboards-') as temporary:
            root = Path(temporary); skill = root / '.agents/skills/vectorcraft-cli-export'
            shutil.copytree(os.environ['CRAFT_INSTALLED_VECTOR_EXPORT_SKILL'], skill, ignore=shutil.ignore_patterns('__pycache__'))
            def hashes(directory):
                return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.rglob('*') if p.is_file()}
            skill_before = hashes(skill)
            spec = importlib.util.spec_from_file_location('isolated_artboards', skill/'scripts/workflow.py')
            workflow = importlib.util.module_from_spec(spec); spec.loader.exec_module(workflow)
            runtime = root/'empty-runtime'; self.assertFalse(runtime.exists())
            boards = [(0,0,128,96,'Logo'), (200,20,80,64,'Icon'), (400,-40,96,128,'Portrait variant')]
            operations = []
            for i,(x,y,w,h,name) in enumerate(boards):
                if i: operations.append({'command':'artboard.new','params':{'x':x,'y':y,'width':w,'height':h,'name':name}})
                operations += [{'command':'shape.rectangle','params':{'x':x+w/4,'y':y+h/4,'width':w/2,'height':h/2},'as':'shape'+str(i)}, {'command':'paint.setFill','params':{'color':'#22aa66' if i==1 else '#2366e8'}}, {'command':'paint.setStroke','params':{'none':True}}]
            operations += [{'command':'swatch.new','params':{'name':'Brand Primary','color':'#2366e8','global':True},'as':'primary'}, {'command':'paint.setFill','params':{'ids':[{'$ref':'shape0.id'},{'$ref':'shape2.id'}],'swatch':{'$ref':'primary.name'}}}]
            exports = [{'format':fmt,'artboard':i} for i in range(3) for fmt in ('svg','png','pdf')]
            plan = {'document':{'name':'Different artboards','width':128,'height':96,'units':'Pixels'},'operations':operations,'exports':exports}
            first, second = root/'v1', root/'v2'
            original = workflow.execute(plan,first,runtime_home=runtime)
            first_files = hashes(first)
            time.sleep(2.1)
            revised = workflow.execute({'expectedProjectSha256':original['files']['project.vectorcraft'],'operations':[{'command':'swatch.edit','params':{'name':{'$ref':'primary.name'},'color':'#175cce'}}]},second,runtime_home=runtime,source=first)
            a = json.loads((first/'native.json').read_text()); b = json.loads((second/'native.json').read_text())
            self.assertEqual(a['artboards'],b['artboards']); self.assertEqual(len(a['artboards']),3)
            samples = []
            for directory, manifest, primary in [(first,original,(35,102,232)),(second,revised,(23,92,206))]:
                self.assertEqual(len(manifest['outputs']),9)
                pdf_date=json.loads((directory/'pdf-export-date.json').read_text())
                self.assertEqual(pdf_date,json.loads((first/'pdf-export-date.json').read_text()))
                self.assertEqual(pdf_date['created'],a['metadata']['created'])
                for i,(x,y,w,h,name) in enumerate(boards):
                    rect = a['artboards'][i]['rect']; self.assertEqual([rect[k] for k in ('x0','y0','x1','y1')],[x,y,x+w,y+h])
                    expected = (34,170,102) if i==1 else primary
                    for fmt in ('svg','png','pdf'):
                        filename=f'artboard-{i+1}.{fmt}'; output=next(o for o in manifest['outputs'] if o['path']==filename)
                        self.assertEqual(output['artboardId'],a['artboards'][i]['id']); self.assertEqual(hashes(directory)[filename],manifest['files'][filename])
                        if fmt=='pdf':self.assertEqual(output['pdfCreated'],pdf_date['created']);self.assertEqual(output['pdfDateBinding'],pdf_date['binding'])
                    svg=ET.parse(directory/f'artboard-{i+1}.svg').getroot()
                    self.assertEqual(list(map(float,svg.attrib['viewBox'].split())),[0,0,w,h]); self.assertFalse(svg.findall('.//{http://www.w3.org/2000/svg}image'))
                    with Image.open(directory/f'artboard-{i+1}.png') as png:
                        image=png.convert('RGBA'); self.assertEqual(image.size,(w,h)); self.assertEqual(image.getpixel((w//2,h//2)),(*expected,255)); self.assertEqual(image.getpixel((2,2))[3],0)
                    with fitz.open(directory/f'artboard-{i+1}.pdf') as pdf:
                        self.assertEqual(pdf.metadata['creationDate'],datetime.fromtimestamp(pdf_date['created'],timezone.utc).strftime('D:%Y%m%d%H%M%SZ'))
                        self.assertEqual(len(pdf),1); page=pdf[0]; self.assertAlmostEqual(page.rect.width,w); self.assertAlmostEqual(page.rect.height,h)
                        self.assertEqual(len(page.get_images()),0)
                        pix=page.get_pixmap(matrix=fitz.Matrix(1,1),alpha=False); decoded=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
                        self.assertEqual(decoded.getpixel((w//2,h//2)),expected); self.assertEqual(decoded.getpixel((2,2)),(255,255,255))
                    samples.append({'revision':directory.name,'artboard':i,'size':[w,h],'centerRgb':list(expected),'pdfVectorOnly':True})
            unaffected = {fmt: {'before':first_files[f'artboard-2.{fmt}'],'after':hashes(second)[f'artboard-2.{fmt}']} for fmt in ('svg','png','pdf')}
            if os.environ.get('CRAFT_VECTOR_ARTBOARD_FAILURE_EVIDENCE'):
                proof={'schema':'vectorcraft-artboard-unaffected-export-regression/v1','status':'failed' if any(v['before']!=v['after'] for v in unaffected.values()) else 'passed','scope':'fixed installed export skill copied alone, empty public native runtime; actual different-size artboards; independent PNG/PDF dimensions and visible color checks completed before export identity gate','unaffectedExports':unaffected,'samples':samples,'initialSvg':(first/'artboard-2.svg').read_text(),'revisedSvg':(second/'artboard-2.svg').read_text(),'runtimeLockSha256':hashlib.sha256((skill/'scripts/runtime.lock.json').read_bytes()).hexdigest(),'driverSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
                with Path(os.environ['CRAFT_VECTOR_ARTBOARD_FAILURE_EVIDENCE']).open('x') as stream: json.dump(proof,stream,indent=2)
            for fmt in ('svg','png','pdf'): self.assertEqual((first/f'artboard-2.{fmt}').read_bytes(),(second/f'artboard-2.{fmt}').read_bytes())
            self.assertEqual(hashes(first),first_files)
            invalid={'expectedProjectSha256':original['files']['project.vectorcraft'],'operations':[],'exports':[{'format':'png','artboard':3}]}
            with self.assertRaisesRegex(ValueError,'artboard_out_of_range'): workflow.execute(invalid,root/'invalid-board',runtime_home=runtime,source=first)
            self.assertFalse((root/'invalid-board').exists())
            with self.assertRaisesRegex(ValueError,'output_exists'): workflow.execute(plan,first,runtime_home=runtime)
            self.assertEqual(hashes(first),first_files); self.assertEqual(hashes(skill),skill_before); self.assertFalse(list(skill.rglob('*.pyc')))
            if os.environ.get('CRAFT_VECTOR_ARTBOARD_EVIDENCE'):
                proof={'schema':'vectorcraft-artboard-exports-first-use/v1','scope':'fixed installed export skill copied alone; empty default public native runtime install; distinct rectangles and global RGB token; independent Pillow/PyMuPDF output checks','samples':samples,'pdfExportDate':pdf_date,'originalFiles':first_files,'revisedFiles':hashes(second),'artboards':a['artboards'],'unrelatedIconAllFormatsUnchanged':True,'invalidBoardRejected':True,'sourceAndSkillFilesPreserved':True,'runtimeLockSha256':hashlib.sha256((skill/'scripts/runtime.lock.json').read_bytes()).hexdigest()}
                with Path(os.environ['CRAFT_VECTOR_ARTBOARD_EVIDENCE']).open('x') as stream: json.dump(proof,stream,indent=2)

if __name__=='__main__': unittest.main()
