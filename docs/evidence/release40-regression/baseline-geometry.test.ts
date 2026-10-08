import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync,mkdirSync,writeFileSync,rmSync,existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { Controller,skillDigest } from '../src/harness/controller.ts';

// 合成协调器fixture，不充当真实原生或像素验收。
function fixture(){
 const root=mkdtempSync(join(tmpdir(),'vector geometry ')),skill=join(root,'skill');mkdirSync(join(skill,'scripts'),{recursive:true});
 writeFileSync(join(skill,'scripts/workflow.py'),`import argparse,pathlib,json,hashlib\np=argparse.ArgumentParser();p.add_argument('plan');p.add_argument('--output');p.add_argument('--runtime-home');p.add_argument('--control');a=p.parse_args();o=pathlib.Path(a.output);o.mkdir();(o/'project.vectorcraft').write_bytes(b'native');m={'schema':'vectorcraft-delivery/v1','runtimeSha256':'${'a'.repeat(64)}','files':{'project.vectorcraft':hashlib.sha256(b'native').hexdigest()}};(o/'manifest.json').write_text(json.dumps(m))\n`);
 writeFileSync(join(skill,'scripts/execution_control.py'),'# synthetic control fixture\n');writeFileSync(join(skill,'scripts/runtime.lock.json'),JSON.stringify({artifacts:{'darwin-arm64':{binarySha256:'a'.repeat(64)}}}));
 const plan=join(root,'plan.json');writeFileSync(plan,'{"operations":[]}');const controller=new Controller(join(root,'state.sqlite'));
 const request={key:'geometry',skill,expectedSkillSha256:skillDigest(skill),plan,output:join(root,'output'),runtimeHome:join(root,'runtime'),estimatedBytes:10000,authorization:{objects:[2],fields:['kind.path'],deadline:Date.now()+10000,maxAttempts:2,maxBytes:100000,readRoots:[root],writeRoots:[root]}};
 return {root,controller,request,close:()=>{controller.close();rmSync(root,{recursive:true,force:true});}};
}

test('preview pixel geometry and unspecified units are refused before effects',async()=>{
 const f=fixture();try{
  await assert.rejects(()=>f.controller.run({...f.request,geometryContract:{schema:'vectorcraft-geometry-contract/v1',coordinateSpace:'preview-pixels',units:'Millimeters'}} as any),/invalid_geometry_contract/);
  assert.equal(existsSync(f.request.output),false);assert.equal((f.controller.ledger.db.prepare('SELECT COUNT(*) AS n FROM tasks').get() as any).n,0);
 }finally{f.close();}
});
