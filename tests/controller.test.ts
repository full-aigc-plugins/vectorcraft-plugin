import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, mkdirSync, rmSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { Controller, skillDigest } from '../src/harness/controller.ts';

test('controller binds a supplied standalone snapshot, records intent and verifies actual files', async()=>{
  const root=mkdtempSync(join(tmpdir(),'vectorcraft-controller-'));
  // 这是流程协调单元 fixture，不充当 Vector 原生验收。
  const skill=join(root,'skill');mkdirSync(join(skill,'scripts'),{recursive:true});
  writeFileSync(join(skill,'scripts','workflow.py'),`import argparse,hashlib,json,pathlib\np=argparse.ArgumentParser();p.add_argument('plan');p.add_argument('--output');p.add_argument('--runtime-home');p.add_argument('--source');p.add_argument('--control');a=p.parse_args();o=pathlib.Path(a.output);o.mkdir();(o/'project.vectorcraft').write_bytes(b'fixture');h=hashlib.sha256(b'fixture').hexdigest();m={'schema':'vectorcraft-delivery/v1','runtimeSha256':'${'c'.repeat(64)}','files':{'project.vectorcraft':h},'outputs':[],'fontDependencies':[]};(o/'manifest.json').write_text(json.dumps(m));print(json.dumps(m))\n`);
  writeFileSync(join(skill,'scripts','execution_control.py'),'# synthetic coordinator fixture; no native acceptance\n');
  writeFileSync(join(skill,'scripts','runtime.lock.json'),JSON.stringify({artifacts:{'darwin-arm64':{binarySha256:'c'.repeat(64)}}}));
  const plan=join(root,'plan.json');writeFileSync(plan,'{"operations":[]}');
  const authorization={objects:[2],fields:['paint.color'],deadline:Date.now()+60000,maxAttempts:1,maxBytes:100000,readRoots:[root],writeRoots:[root]};
  const controller=new Controller(join(root,'state.sqlite'));
  try {
    const request={key:'one',skill,expectedSkillSha256:skillDigest(skill),plan,output:join(root,'output'),
      runtimeHome:join(root,'runtime'),python:'python3',authorization,estimatedBytes:10000};
    const value=await controller.run(request);
    assert.equal(value.state,'review_ready');
    assert.equal(controller.ledger.get(value.id).attempts,1);
    assert.equal((await controller.run(request)).id,value.id);
    const submitted=controller.ledger.db.prepare('SELECT intent FROM steps WHERE task=?').get(value.id) as any;
    const intent=JSON.parse(submitted.intent);
    assert.deepEqual(intent.plan,{operations:[]});
    assert.notEqual(intent.skillSnapshot,skill);
    assert.equal(skillDigest(intent.skillSnapshot),request.expectedSkillSha256);
    assert.equal(readFileSync(intent.planSnapshot,'utf8'),'{"operations":[]}');
    const originalManifest=readFileSync(join(request.output,'manifest.json'),'utf8');
    const rewritten=JSON.parse(originalManifest);rewritten.audit='rewritten';
    writeFileSync(join(request.output,'manifest.json'),JSON.stringify(rewritten));
    await assert.rejects(()=>controller.run(request),/receipt_manifest_mismatch/);
    writeFileSync(join(request.output,'manifest.json'),originalManifest);
    assert.throws(()=>controller.verifyDelivery(request.output,'d'.repeat(64)),/runtime_identity_mismatch/);
    writeFileSync(join(request.output,'project.vectorcraft'),'tampered');
    assert.throws(()=>controller.verifyDelivery(request.output,'c'.repeat(64)),/artifact_digest_mismatch/);
    await assert.rejects(()=>controller.run(request),/artifact_digest_mismatch/);
    const changed={...request,key:'two',output:join(root,'other'),expectedSkillSha256:'0'.repeat(64)};
    await assert.rejects(()=>controller.run(changed),/skill_snapshot_mismatch/);
    await assert.rejects(()=>controller.run({...request,key:'three',output:join(tmpdir(),'escape')}),/outside_authorized_roots/);
    const workflow=join(skill,'scripts','workflow.py');writeFileSync(workflow,readFileSync(workflow,'utf8')+'# changed source identity\n');
    await assert.rejects(()=>controller.run({...request,expectedSkillSha256:skillDigest(skill)}),/idempotency_conflict/);
  } finally {controller.close();rmSync(root,{recursive:true,force:true});}
});
