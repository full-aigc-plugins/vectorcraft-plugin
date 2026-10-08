/** 真实保存完成、协调进程回执丢失：恢复核验原输出，不重放未知编辑。 */
import assert from 'node:assert/strict';
import {mkdirSync,readFileSync,writeFileSync,existsSync,openSync,closeSync,lstatSync} from 'node:fs';
import {join,resolve,dirname} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {executionIdentity} from './execution_identity.ts';
const fingerprints=executionIdentity(),config=JSON.parse(readFileSync(process.argv[2],'utf8'));
const root=resolve(config.output),implementationRoot=resolve(config.implementationRoot??join(dirname(fileURLToPath(import.meta.url)),'../..'));
const {Controller,skillDigest}=await import(pathToFileURL(join(implementationRoot,'src/harness/controller.ts')).href);
const hash=(p:string)=>createHash('sha256').update(readFileSync(p)).digest('hex');
assert.equal(existsSync(root),false,'fresh root required');mkdirSync(root,{recursive:true});
const source=resolve(config.source),skill=resolve(config.skill),runtime=resolve(config.runtimeHome),project=join(source,'project.vectorcraft');
const originalSourceDigest=skillDigest(source),projectSha256=hash(project);
const plan=join(root,'plan.json');writeFileSync(plan,JSON.stringify({expectedProjectSha256:projectSha256,operations:[{command:'swatch.edit',params:{name:'Brand Primary',color:config.targetColor}}]}));
const request={key:'saved-receipt-lost',skill,expectedSkillSha256:skillDigest(skill),plan,source,output:join(root,'original-output'),runtimeHome:runtime,python:config.python,estimatedBytes:10000000,
 authorization:{...config.authorization,deadline:Date.now()+180000,maxAttempts:1,maxBytes:10000000,readRoots:[root,source],writeRoots:[root,runtime]}};
const database=join(root,'tasks.sqlite'),actorConfig=join(root,'actor.json'),lossMarker=join(root,'receipt-loss.json');
writeFileSync(actorConfig,JSON.stringify({database,implementationRoot,request,lossMarker}));
const log=openSync(join(root,'actor.log'),'wx');
const actor=spawn(process.execPath,[join(dirname(fileURLToPath(import.meta.url)),'task_receipt_loss_child.ts'),actorConfig],{detached:true,stdio:['ignore',log,log]});closeSync(log);
let exited=false;
const exit=new Promise<any>((accept,reject)=>{actor.on('error',reject);actor.on('exit',(code,signal)=>{exited=true;accept({code,signal});});});
let controller:any;
try{
 const parentExit=await Promise.race([exit,new Promise((_,reject)=>{const timer=setTimeout(()=>reject(new Error('receipt_loss_actor_timeout')),45000);timer.unref();})]);
 assert.equal(parentExit.signal,'SIGKILL');assert.ok(existsSync(lossMarker));
 controller=new Controller(database);
 const task=controller.ledger.db.prepare("SELECT id,epoch FROM tasks WHERE key='saved-receipt-lost'").get() as any;assert.ok(task);
 const before=controller.ledger.get(task.id),step=controller.ledger.db.prepare('SELECT state,result FROM steps WHERE task=? AND n=0').get(task.id) as any;
 assert.equal(before.state,'running');assert.equal(step.state,'submitted');assert.equal(step.result,null);
 assert.equal(controller.processes.observe(task.id,task.epoch).stopped,true);
 const manifest=controller.verifyDelivery(request.output,before.binding.runtimeIdentity),manifestHash=hash(join(request.output,'manifest.json'));
 const originalOutputDigest=skillDigest(request.output),outputInode=lstatSync(request.output).ino;
 const actualLostReceipt=JSON.parse(readFileSync(lossMarker,'utf8'));
 assert.equal(actualLostReceipt.result.manifestSha256,manifestHash);
 assert.equal(actualLostReceipt.result.runtimeIdentity,before.binding.runtimeIdentity);
 const eventsFile=join(controller.snapshotRoot,task.id+'-events.jsonl'),eventsHash=hash(eventsFile);
 const events=readFileSync(eventsFile,'utf8').split('\n').filter(Boolean).map(line=>JSON.parse(line));
 const originalStage=events.find(event=>event.event==='stage_created');assert.ok(originalStage);
 assert.equal(existsSync(originalStage.path),false);assert.equal(originalStage.inode,outputInode);
 const resumed=await controller.run(request);assert.equal(resumed.state,'running');assert.match(resumed.resumePolicy,/no automatic replay/);
 assert.equal(resumed.attempts,1);assert.equal(resumed.bytes,before.bytes);assert.equal(hash(eventsFile),eventsHash);
 await assert.rejects(()=>controller.run({...request,output:join(root,'changed-output')}),/idempotency_conflict/);
 await assert.rejects(()=>controller.run({...request,key:'duplicate',output:join(root,'duplicate-output')}),/resource_busy/);
 assert.equal((controller.ledger.db.prepare('SELECT COUNT(*) AS n FROM tasks').get() as any).n,1);
 controller.ledger.unknown(task.id,task.epoch,'QA: coordinator killed before actual saved manifest receipt persisted');
 const recovered=await controller.reconcileOriginal(task.id,task.epoch);
 assert.equal(recovered.proof.stage,request.output);assert.equal(recovered.proof.stageInode,outputInode);
 assert.ok(recovered.proof.reopened.some((item:any)=>item.path===join(request.output,'project.vectorcraft')));
 assert.equal(recovered.task.state,'interrupted_verified');assert.equal(recovered.task.epoch,task.epoch+1);
 assert.equal(skillDigest(request.output),originalOutputDigest);assert.equal(skillDigest(source),originalSourceDigest);assert.equal(hash(eventsFile),eventsHash);
 assert.throws(()=>controller.ledger.receipt(task.id,task.epoch,0,actualLostReceipt.result),/stale_epoch/);
 const late=controller.ledger.db.prepare('SELECT result FROM late_receipts WHERE task=?').get(task.id) as any;
 assert.deepEqual(JSON.parse(late.result),actualLostReceipt.result);
 assert.equal(controller.ledger.get(task.id).state,'interrupted_verified');assert.equal(hash(join(request.output,'manifest.json')),manifestHash);
 const proof={result:'PASS',fingerprints,scope:'real native save/export verified, then QA SIGKILL before ledger receipt; original completed directory readonly reopened, no replay or automatic success; not fixed-install or complete VC-TX-002 acceptance',
  skillSha256:skillDigest(skill),runtimeIdentity:before.binding.runtimeIdentity,sourceProjectSha256:projectSha256,
  parentExit,taskId:task.id,originalEpoch:task.epoch,crashPoint:actualLostReceipt.point,receiptMissingOnRestart:true,originalState:before.state,
  sourceUnchanged:true,outputUnchanged:true,outputInodePreserved:true,noAutomaticReplay:true,attemptsAfterRestart:resumed.attempts,bytesAfterRestart:resumed.bytes,
  changedOutputRejected:true,competingSourceRejected:true,duplicateTaskNotRegistered:true,nativeGroupStopped:true,
  manifestSha256:manifestHash,projectSha256:manifest.files['project.vectorcraft'],exportCount:manifest.outputs.length,
  recovery:recovered.proof,settledState:recovered.task.state,settledEpoch:recovered.task.epoch,actualLateReceiptQuarantined:true};
 writeFileSync(join(root,'proof.json'),JSON.stringify(proof,null,2)+'\n');
 console.log(JSON.stringify({result:'PASS',settledState:recovered.task.state,exportCount:manifest.outputs.length,noAutomaticReplay:true}));
}finally{
 if(!exited){try{process.kill(actor.pid!,'SIGKILL');}catch{}await exit;}
 if(!controller)controller=new Controller(database);
 for(const task of controller.ledger.db.prepare('SELECT task,epoch FROM native_processes').all() as any[]){
  if(!controller.processes.observe(task.task,task.epoch).stopped)await controller.processes.stop(task.task,task.epoch,50);
 }
 controller.close();
}
