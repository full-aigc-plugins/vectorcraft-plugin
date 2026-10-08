import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,rmSync,lstatSync,unlinkSync,symlinkSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {Ledger} from '../src/harness/ledger.ts';
import {Recovery} from '../src/harness/recovery.ts';
import {skillDigest} from '../src/harness/controller.ts';
import {canonical} from '../src/strict_json.ts';
// 仅核验恢复启动前的快照门禁；不把合成事件当作原生重开证据。
const sha=(s:string|Buffer)=>createHash('sha256').update(s).digest('hex');
function fixture(change:string){
 const root=mkdtempSync(join(tmpdir(),'vector-recovery-binding-')),skill=join(root,'skill');mkdirSync(join(skill,'scripts'),{recursive:true});
 writeFileSync(join(skill,'scripts/mcp_session.py'),'# bound session fixture\n');
 const plan={operations:[]},planSnapshot=join(root,'plan.json');writeFileSync(planSnapshot,canonical(plan));
 const ledger=new Ledger(join(root,'state.sqlite')),authorization={objects:[3],fields:['paint.color'],deadline:Date.now()+60000,maxAttempts:1,maxBytes:10000};
 const binding={skillSha256:skillDigest(skill),planHash:sha(canonical(plan)),inputHashes:{},projectRevision:null,runtimeIdentity:'b'.repeat(64),authorization};
 const task=ledger.claim('interrupted',join(root,'source.vectorcraft'),join(root,'output'),binding);
 const eventFile=join(root,'events.jsonl');writeFileSync(eventFile,'');const stat=lstatSync(eventFile),controlFile=join(root,'control.json');
 const profile={task:task.id,epoch:task.epoch,planHash:binding.planHash,planFile:planSnapshot,eventFile,eventInode:stat.ino,eventDevice:stat.dev,runtimeIdentity:binding.runtimeIdentity,authorization};
 writeFileSync(controlFile,canonical(profile));const controlSha256=sha(readFileSync(controlFile));
 ledger.intent(task.id,task.epoch,0,{skillSha256:binding.skillSha256,skillSnapshot:skill,planHash:binding.planHash,plan,planSnapshot,controlFile,...(change==='missing-control-hash'?{}:{controlSha256}),runtimeHome:join(root,'runtime'),python:'python3'},1000);
 ledger.cancel(task.id,task.epoch,false);
 if(change==='skill')writeFileSync(join(skill,'scripts/mcp_session.py'),'# replaced executable\n');
 if(change==='plan')writeFileSync(planSnapshot,'{"operations":[{"command":"changed"}]}');
 if(change==='control')writeFileSync(controlFile,canonical({...profile,authorization:{...authorization,fields:['structure']}}));
 if(change==='symlink-plan'){const other=join(root,'other.json');writeFileSync(other,canonical(plan));unlinkSync(planSnapshot);symlinkSync(other,planSnapshot);}
 return {root,ledger,task,recovery:new Recovery(ledger,{observe:()=>({stopped:true})} as any),close(){ledger.close();rmSync(root,{recursive:true,force:true});}};
}
for(const [change,error] of [['skill','skill_snapshot_mismatch'],['plan','recovery_plan_mismatch'],['control','recovery_control_mismatch'],['missing-control-hash','recovery_identity_missing'],['symlink-plan','recovery_snapshot_symlink'],['unchanged','original_stage_identity_missing']]){
 test('recovery refuses '+change+' before any inspection process or proof',async()=>{
  const f=fixture(change);try{
   await assert.rejects(()=>f.recovery.inspect(f.task.id,f.task.epoch),new RegExp(error));
   assert.equal(f.ledger.get(f.task.id).state,'cancel_requested');assert.equal(f.ledger.get(f.task.id).attempts,1);
   assert.equal((f.ledger.db.prepare('SELECT COUNT(*) AS n FROM recovery_checks').get() as any).n,0);
  }finally{f.close();}
 });
}
