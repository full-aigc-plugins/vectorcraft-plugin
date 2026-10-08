"""从实际导出与重开记录生成交换损失报告；不把格式能力推断当成保真验证。"""
import hashlib
import base64
import binascii
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

PLUGIN = 'vectorcraft'
NATIVE = 'project.vectorcraft'

def embedded_image(value):
 """只解析有界内嵌数据，不联网；媒体类型和签名分别保留。"""
 match=re.fullmatch(r'data:([^;,]+);base64,(.*)',value,re.I|re.S)
 if not match:return None
 if len(match[2])>24*1024*1024:raise ValueError('loss_svg_image_data_too_large')
 try:data=base64.b64decode(match[2],validate=True)
 except (binascii.Error,ValueError):raise ValueError('loss_svg_image_data_invalid') from None
 return match[1].lower(),data

def svg_image_scope(xml):
 """记录SVG图像元素局部范围；不推断可见绘制边界、栅格来源或往返保真。"""
 elements=[];foreign=False
 def visit(node,path,ancestors,transforms):
  nonlocal foreign
  tag=node.tag.rsplit('}',1)[-1]
  if tag=='foreignObject':foreign=True
  if tag in ('image','feImage'):
   href=node.get('href',node.get('{http://www.w3.org/1999/xlink}href',''))
   embedded=embedded_image(href);kind='unresolved-reference'
   row={'elementPath':path,'tag':tag,'id':node.get('id'),'geometry':{k:node.get(k) for k in ('x','y','width','height') if k in node.attrib},
        'transform':node.get('transform'),'ancestorTransforms':transforms,'ancestorElements':ancestors,
        'referenceSha256':hashlib.sha256(href.encode()).hexdigest()}
   if embedded:
    mime,data=embedded;row.update(mediaType=mime,payloadSha256=hashlib.sha256(data).hexdigest(),payloadBytes=len(data))
    signatures={'image/png':data.startswith(b'\x89PNG\r\n\x1a\n'),'image/jpeg':data.startswith(b'\xff\xd8\xff'),
                'image/gif':data.startswith((b'GIF87a',b'GIF89a')),'image/webp':data.startswith(b'RIFF') and data[8:12]==b'WEBP'}
    if mime in signatures:
     if not signatures[mime]:raise ValueError('loss_svg_image_signature_mismatch')
     kind='embedded-raster'
    elif mime=='image/svg+xml':kind='embedded-vector-reference'
    else:kind='embedded-unknown'
   row['classification']=kind;elements.append(row)
  chain=transforms+([node.get('transform')] if node.get('transform') else [])
  for i,child in enumerate(node):visit(child,path+'/'+str(i),ancestors+[tag],chain)
 visit(xml,'0',[],[])
 return {'elements':elements,'vectorOnly':not elements and not foreign,'losslessVectorClaimAllowed':False,
         'coordinateSpace':'element-local geometry plus ancestor transforms','completePaintBounds':False,
         'rasterOrigin':'unknown; image elements may be source assets or expanded effects','foreignObjectPresent':foreign}

def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def safe_file(root,location):
 if not isinstance(location,str) or not location or '\\' in location or ':' in location or Path(location).is_absolute() or any(p in ('..','') for p in location.split('/')):raise ValueError('loss_location_invalid')
 path=root/location
 if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):raise ValueError('loss_file_missing_or_escaping')
 return path

def write_report(root,outputs,warnings,text_modes=None):
 root=Path(root)
 text_modes={} if text_modes is None else text_modes
 if not isinstance(text_modes,dict) or any(k not in outputs or not isinstance(k,str) or not k.endswith('.svg') or v not in ('appearance','editable',None) or type(v) not in (str,type(None)) for k,v in text_modes.items()):raise ValueError('loss_text_mode_invalid')
 native=safe_file(root,NATIVE);inspection=safe_file(root,'native.json')
 model=json.loads(inspection.read_text())
 def native_text_ids(value):
  result=[]
  if isinstance(value,dict):
   if type(value.get('id')) is int and value['id']>0 and isinstance(value.get('kind'),dict) and value['kind'].get('type')=='text':result.append(value['id'])
   for child in value.values():result.extend(native_text_ids(child))
  elif isinstance(value,list):
   for child in value:result.extend(native_text_ids(child))
  return sorted(set(result))
 text_ids=native_text_ids(model.get('layers',[]))
 report={'schema':'craft-exchange-loss/v1','pluginId':PLUGIN,'native':{'location':NATIVE,'sha256':sha(native)},'inspection':{'location':'native.json','sha256':sha(inspection)},'outputs':[],'acceptance':'technical-observations-only'}
 if len(outputs)!=len(set(outputs)):raise ValueError('loss_duplicate_output')
 for location in outputs:
  path=safe_file(root,location);fmt=path.suffix[1:].lower();observations={};changes=[]
  def change(code,status,reason):changes.append({'code':code,'status':status,'reason':reason})
  change('native-editing-model','lost','Derivative formats do not retain the complete application-native project model; the native project is delivered separately.')
  if fmt in ('png','jpg','jpeg','webp','mp4'):
   change('editable-layers-paths-text','lost','Layer, path and live text editing are rendered into pixels; edit the retained native project.')
   change('effect-keyframe-parameters','lost','Rendered pixels do not carry editable native effects, masks or keyframes.')
   change('font-appearance','unknown','Rendered appearance has not been compared with an approved visual reference.')
  if fmt=='png':
   with path.open('rb') as stream:header=stream.read(26)
   if len(header)!=26 or header[:8]!=bytes.fromhex('89504e470d0a1a0a'):raise ValueError('loss_png_invalid')
   observations['pngColorType']=header[25]
   change('alpha-channel','observed' if header[25] in (4,6) else 'unknown','PNG IHDR records channel representation; indexed transparency and visual alpha fidelity are not inferred.')
  elif fmt=='mp4':
   change('alpha-channel','lost','The supported H.264 export does not retain native composition transparency.')
   change('editable-timeline','lost','MP4 contains rendered streams rather than editable clips, tracks and subtitle style parameters.')
   if PLUGIN=='effectcraft':change('audio-output','lost','This public export explicitly renders with audio off; native media remains in the project.')
   if (root/'export-probe.json').is_file():
    probe=json.loads((root/'export-probe.json').read_text());observations['audioStreamPresent']=bool(probe.get('audio'))
  elif fmt=='svg':
   if path.stat().st_size>16*1024*1024:raise ValueError('loss_svg_too_large')
   xml=ET.fromstring(path.read_bytes())
   if xml.tag.split('}')[-1]!='svg':raise ValueError('loss_svg_invalid')
   tags=[element.tag.split('}')[-1] for element in xml.iter()];observations['svg']={name:tags.count(name) for name in ('path','text','image','filter','mask','clipPath')}
   observations['rasterizationScope']=svg_image_scope(xml)
   change('raster-content','observed' if observations['rasterizationScope']['elements'] else 'unknown','Actual image/feImage elements and their local geometry are listed; references, effect attribution, visible clipping and complete paint bounds are not inferred.')
   change('lossless-vector-claim','blocked','Derivative structure and unknown effect/font fidelity do not establish a lossless vector round-trip; retain the native project.')
   mode=text_modes.get(location);observations['svgTextExportMode']=mode;observations['nativeTextObjectIds']=text_ids
   observations['textScope']='Native text IDs are document dependencies, not a visibility or per-outline object mapping.'
   if mode=='appearance' and text_ids:
    change('live-text-editability','lost','Observed appearance export mode converts any emitted native live text to outlines; edit the separately retained native project. Native IDs do not prove which objects intersect this artboard.')
   elif observations['svg']['text']:
    change('live-text-editability','observed','SVG contains live text elements; per-object editing equivalence, omitted or partially outlined text and font portability remain unverified.')
   else:
    change('live-text-editability','unknown','No live SVG text elements observed. Paths alone do not prove text outlining; export mode, visibility or per-object provenance is not established.')
   change('vector-structure','observed','XML element counts record actual vector/text/raster structure, not semantic round-trip equivalence.')
   change('font-portability','unknown','Font embedding, substitution and text layout across consumers are not verified.')
   change('effect-fidelity','unknown','Native effects, masks and grouping are not proven equivalent in SVG consumers.')
  elif fmt=='psd':
   change('font-portability','unknown','PSD font availability and substitution in other editors are not verified.')
   change('effect-fidelity','unknown','Native adjustment, mask, blend and effect equivalence is not proven by layer count.')
   change('editable-layer-roundtrip','unknown','A reopened PSD inspection is evidence of observed structure, not complete editability equivalence.')
   if (root/'psd-inspection.json').is_file():
    psd=json.loads((root/'psd-inspection.json').read_text());observations['nativeLayerCount']=len(model.get('layers',[]));observations['psdLayerCount']=len(psd.get('layers',[]))
    report['psdInspection']={'location':'psd-inspection.json','sha256':sha(root/'psd-inspection.json')}
  elif fmt=='pdf':
   change('font-portability','unknown','PDF font embedding and substitution are not verified.')
   change('effect-fidelity','unknown','Native effect/mask appearance in PDF consumers is not verified.')
   change('vector-structure','unknown','PDF output does not prove editable vector-path round-trip.')
  elif fmt=='srt':
   change('subtitle-styling','lost','SRT exchanges timing and text; native font, position, color and animation styling is not retained.')
  elif fmt=='tif':
   change('editable-layer-roundtrip','unknown','TIFF layer extensions and native mask/effect fidelity are not verified.')
   change('font-portability','unknown','Native live-text portability is not verified.')
  elif fmt not in ('jpg','jpeg','webp'):raise ValueError('loss_format_unsupported')
  report['outputs'].append({'location':location,'sha256':sha(path),'format':fmt,'role':'derivative','nativeSubstitute':False,'changes':changes,'observations':observations,'warnings':warnings.get(location,[])})
 (root/'exchange-loss.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 return report
