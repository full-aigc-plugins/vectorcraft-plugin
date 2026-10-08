"""公开单技能原生品牌返工，省略导出清单仍须生成全部变体。"""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--skill',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--runtime-home',type=Path);a=p.parse_args();a.skill=a.skill.resolve();root=a.output.resolve();root.mkdir(parents=True,exist_ok=False);skill=root/'.agents/skills'/a.skill.name;shutil.copytree(a.skill,skill,ignore=shutil.ignore_patterns('__pycache__'))
def hashes(path):return {str(f.relative_to(path)):hashlib.sha256(f.read_bytes()).hexdigest() for f in path.rglob('*') if f.is_file()}
identity=hashes(skill);runtime=a.runtime_home.resolve() if a.runtime_home else root/'runtime';cold=not runtime.exists()
env=dict(os.environ,PATH='/usr/bin:/bin')
for key in ('CRAFT_RUNTIME_HOME','CRAFT_NODE_ARCHIVE','CRAFT_BUNDLE_DIRECTORY','CRAFT_NATIVE_ARCHIVE_DIRECTORY'):env.pop(key,None)
def run(name,plan,source=None,success=True):
 f=root/(name+'.json');f.write_text(json.dumps(plan));args=[sys.executable,'-I','-B',str(skill/'scripts/workflow.py'),str(f),'--output',str(root/name),'--runtime-home',str(runtime)]
 if source:args+=['--source',str(source)]
 r=subprocess.run(args,capture_output=True,text=True,env=env,timeout=240);(root/(name+'.stdout')).write_text(r.stdout);(root/(name+'.stderr')).write_text(r.stderr)
 if success:assert r.returncode==0,r.stdout+r.stderr
 return json.loads(r.stdout),r.returncode
setup=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts/bootstrap.py'),'--runtime-home',str(runtime)],capture_output=True,text=True,env=env,timeout=180)
(root/'setup.stdout').write_text(setup.stdout);(root/'setup.stderr').write_text(setup.stderr);assert setup.returncode==0,setup.stdout+setup.stderr
installation=json.loads(setup.stdout)
if cold:assert installation['reused'] is False
cli=installation['executable']
version=subprocess.run([cli,'--version'],capture_output=True,text=True,env=env,timeout=30);(root/'version.stdout').write_text(version.stdout);assert version.returncode==0 and '0.2.0-craft.2' in version.stdout
catalog=subprocess.run([cli,'commands','--json'],capture_output=True,text=True,env=env,timeout=30);(root/'discovery.stdout').write_text(catalog.stdout);assert catalog.returncode==0 and len(json.loads(catalog.stdout))==585
plan=json.loads((skill/'examples/brand-token-assets.json').read_text());plan['exports']=[{'format':fmt,'artboard':board} for board in range(3) for fmt in ('svg','png','pdf')]
manifest,_=run('source',plan);source=root/'source';original=hashes(source);results=[]
for mode in ('native-gateway','direct'):
 edit={'command':'swatch.edit','params':{'name':{'$ref':'primary.name'},'color':'#175cce'}};revision={'expectedProjectSha256':manifest['files']['project.vectorcraft'],'operations':[edit if mode=='direct' else {'command':'native.command','params':edit}]}
 result,_=run(mode,revision,source);expected={v['path'] for v in manifest['outputs']};actual={v['path'] for v in result['outputs']};(root/(mode+'-outputs.json')).write_text(json.dumps({'expected':sorted(expected),'actual':sorted(actual)},indent=2)+'\n');assert actual==expected,(mode,'missing inherited variants',sorted(expected-actual))
 from PIL import Image
 for board in (1,3):
  with Image.open(source/f'artboard-{board}.png') as before,Image.open(root/mode/f'artboard-{board}.png') as after:
   assert before.tobytes()!=after.tobytes();colors={v for count,v in after.convert('RGBA').getcolors(after.width*after.height)};assert (23,92,206,255) in colors
 for suffix in ('svg','png','pdf'):assert (source/f'artboard-2.{suffix}').read_bytes()==(root/mode/f'artboard-2.{suffix}').read_bytes()
 assert original==hashes(source);saved=json.loads((root/mode/'plan.json').read_text());assert saved['exports']==plan['exports'];report=json.loads((root/mode/'brand-dependencies.json').read_text());assert report['checks'][0]['status']=='passed';assert not report['checks'][0]['checkpointRetained']
 results.append({'mode':mode,'inheritedOutputs':len(actual),'boundPreviewChanged':True,'unrelatedSVGPNGPDFFilesUnchanged':True,'sourcePreserved':True,'guardPassed':True})
# 两入口均保留显式空清单，并在原计划篡改时于安装前拒绝。
for mode in ('direct','native-gateway'):
 edit={'command':'swatch.edit','params':{'name':{'$ref':'primary.name'},'color':'#175cce'}}
 revision={'expectedProjectSha256':manifest['files']['project.vectorcraft'],'operations':[edit if mode=='direct' else {'command':'native.command','params':edit}],'exports':[]}
 empty,_=run('explicit-empty-'+mode,revision,source);assert empty['outputs']==[]
 tampered=root/('tampered-source-'+mode);shutil.copytree(source,tampered);(tampered/'plan.json').write_text('{}');bad=dict(revision);bad.pop('exports');fresh=root/('negative-runtime-'+mode);oldruntime=runtime;runtime=fresh;reply,code=run('tampered-'+mode,bad,tampered,False);runtime=oldruntime
 assert code!=0 and 'brand_source_plan_digest_mismatch' in reply['error'];assert not fresh.exists();assert not (root/('tampered-'+mode)).exists()
assert original==hashes(source);assert identity==hashes(skill)
proof={'result':'PASS','skill':a.skill.name,'originSkillName':a.skill.name,'scope':'single copied skill, actual native create/reopen/brand edit, inherited9 variants and preserved controls; not exhaustive commands or GUI','coldNativeRuntime':cold,'cases':results,'explicitEmptyExportsRespected':True,'tamperedPlanRefusedBeforeInstallation':True,'skillFilesUnchanged':True,'skillFiles':identity,'nativeRuntimeSha256':manifest['runtimeSha256']};(root/'proof.json').write_text(json.dumps(proof,indent=2)+'\n');print('PASS',a.skill.name)
