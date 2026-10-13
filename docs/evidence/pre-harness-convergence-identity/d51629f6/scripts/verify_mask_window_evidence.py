#!/usr/bin/env python3
"""核对拥有的窗口蒙版验收身份及实际像素样本，不提升全部GUI资格。"""
import hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT='docs/evidence/vectorcraft-mask-window-fixed64-20261009.json'
def verify(root=ROOT):
    r=json.loads((root/REPORT).read_text());identity=json.loads((root/'docs/current-identity.json').read_text());host=json.loads((root/'docs/evidence/vectorcraft-public-tag64-install-20261009.json').read_text())
    if r['schema']!='vectorcraft-mask-window/v1' or r['result']!='PASS' or r['command']!='transparency.viewOpacityMask' or r['tasksClosed']!=[]:raise ValueError('mask_window_report')
    for k in ('pluginVersion','pluginCommit','sourceRef','sourceCommit','hostVersion','platform'):
        if r[k]!=host[k]:raise ValueError('mask_window_fixed_identity')
    if r['installedSkillsBefore']!=identity['skills'] or r['installedSkillsAfter']!=identity['skills'] or r['runtimeSha256']!=identity['runtime']['binarySha256'] or r['desktopBinarySha256']!=identity['desktop']['binarySha256']:raise ValueError('mask_window_identity')
    if any(r[k] is not True for k in ('sourcePreserved','maskArtPreserved','listenerOwnedByPID','allOwnedProcessesStopped')):raise ValueError('mask_window_ownership')
    family=json.loads((root/'docs/evidence/vectorcraft-command-transparency-fixed64-20261009.json').read_text())
    source=next(c for c in family['cases'] if c['command']=='transparency.viewOpacityMask')['stages'][0]['nativeProjectSha256']
    if r['sourceProjectSha256']!=source:raise ValueError('mask_window_source_binding')
    path=root/'scripts/qa/command_mask_window.py';spec=importlib.util.spec_from_file_location('mask_window_samples',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    if r['driverSha256']!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('mask_window_driver')
    if [s['on'] for s in r['stages']]!=[True,False]:raise ValueError('mask_window_stages')
    for s in r['stages']:
        if (s['width'],s['height'])!=(1440,900) or s['sampleCoordinates']!=[[250,270],[310,340],[380,410]] or s['returned']!={'id':2,'on':s['on']} or s['info']['editingMask']!=2 or s['ui']['activeDocument'] is None:raise ValueError('mask_window_native_state')
        w=s['window'];digest=w['sha256']
        if w['mimeType']!='image/png' or w['bytes']<=0 or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise ValueError('mask_window_image')
        m.sample_check(s['samples'],s['on'])
    if r['stages'][0]['window']['sha256']==r['stages'][1]['window']['sha256']:raise ValueError('mask_window_unchanged')
    for name,digest in r['fingerprints'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('mask_window_dependency')
    return {'result':'PASS','windows':2,'tasksClosed':[],'scope':'viewOpacityMask owned desktop window only'}
if __name__=='__main__':print(json.dumps(verify()))
