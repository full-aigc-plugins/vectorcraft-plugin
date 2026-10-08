#!/usr/bin/env python3
"""真实原生创建、移动重开、修订及篡改拒绝；不声称视觉或外部编辑器保真。"""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

c=json.loads(Path(sys.argv[1]).read_text());out=Path(c['output']);out.mkdir(parents=True,exist_ok=False)
skill=Path(c['skill']);runtime=Path(c['runtime']);binary=runtime/'vectorcraft/0.2.0-craft.2/vectorcraft-cli'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree(p):return {f.relative_to(p).as_posix():sha(f) for f in sorted(p.rglob('*')) if f.is_file() and '__pycache__' not in f.parts}
w=load('lineage_workflow',skill/'scripts/workflow.py');loss=load('lineage_loss',skill/'scripts/exchange_loss.py');session=load('lineage_session',skill/'scripts/mcp_session.py')
identity=tree(skill)
asset=out/'logo.svg';asset.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="16"><path fill="#ee5533" d="M0 0H24V16H0Z"/></svg>')
plan={'document':{'name':'Lineage acceptance','width':96,'height':80,'units':'Pixels'},'assets':{'logo':{'path':str(asset.resolve()),'sha256':sha(asset)}},'operations':[
 {'command':'asset.place','params':{'asset':'logo','rect':[12,16,36,24]}},
 {'command':'shape.rectangle','params':{'x':60,'y':10,'width':15,'height':15}},
 {'command':'paint.setFill','params':{'color':'#2266ee'}}], 'exports':[{'format':f,'artboard':0} for f in ('svg','pdf','png')]}
first=out/'initial';manifest=w.execute(plan,first,runtime_home=runtime);record=loss.verify_lineage(first,manifest)
assert len(record['outputs'])==3 and len(record['assets'])==1 and record['parent']['status']=='creation'
before=tree(first);moved=out/'moved package with spaces';shutil.move(first,moved)
assert tree(moved)==before and loss.verify_lineage(moved,manifest)==record
with session.Session([str(binary),'mcp','--headless']) as native:
 native.command('document.open',{'path':str(moved/'project.vectorcraft')})
 model=native.command('document.json',{})
assert model==json.loads((moved/'native.json').read_text())
second=out/'revised';revised=w.execute({'expectedProjectSha256':manifest['files']['project.vectorcraft'],'operations':[
 {'command':'shape.ellipse','params':{'x':20,'y':50,'width':10,'height':10}}], 'exports':[{'format':'png','artboard':0}]},second,source=moved,runtime_home=runtime)
r=loss.verify_lineage(second,revised)
assert r['logicalId']==record['logicalId'] and r['parent']['version']==record['version'] and r['version']!=record['version']
assert tree(moved)==before
refusals=[]
for fault in ('same-name-replacement','asset-deletion','lineage-task-rebind','lineage-native-rebind','parent-version-rebind'):
 target=out/fault;shutil.copytree(moved,target);m=json.loads((target/'manifest.json').read_text())
 if fault=='same-name-replacement':(target/'artboard-1.png').write_bytes(b'replaced')
 elif fault=='asset-deletion':(target/next(iter(record['assets'].values()))['path']).unlink()
 else:
  data=json.loads((target/'lineage.json').read_text())
  if fault=='lineage-task-rebind':data['sourceTask']['id']='different-execution'
  elif fault=='lineage-native-rebind':data['native']['sha256']='0'*64
  else:data['parent']['version']='0'*64
  (target/'lineage.json').write_text(json.dumps(data));m['files']['lineage.json']=sha(target/'lineage.json');m['lineage']['sha256']=sha(target/'lineage.json')
  (target/'manifest.json').write_text(json.dumps(m))
 try:loss.verify_lineage(target,m)
 except ValueError as error:refusals.append({'case':fault,'result':'PASS','reason':str(error)})
 else:raise AssertionError(fault)
# 失配来源血缘必须在运行时安装和交付目录创建前拒绝。
bad=out/'lineage-task-rebind';empty=out/'unused runtime';refused=out/'must not deliver'
try:w.execute({'expectedProjectSha256':manifest['files']['project.vectorcraft'],'operations':[],'exports':[]},refused,source=bad,runtime_home=empty)
except ValueError as error:
 assert 'lineage' in str(error) and not empty.exists() and not refused.exists()
else:raise AssertionError('source preflight accepted')
assert tree(skill)==identity and tree(moved)==before
proof={'schema':'vectorcraft-lineage-native-acceptance/v1','result':'PASS','runtimeSha256':sha(binary),'driverSha256':sha(__file__),
 'skillFiles':identity,'creation':{'manifest':manifest,'lineage':record},'revision':{'manifest':revised,'lineage':r},'movedFiles':before,
 'movedNativeReopened':True,'sourceUnchanged':True,'preflightRefusedBeforeInstall':True,'refusals':refusals,
 'scope':'actual native create/move/reopen/revise and integrity refusals; no creative, external editor, other platform or full V1 claim'}
(out/'proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'result':'PASS','refusals':len(refusals),'movedNativeReopened':True}))
