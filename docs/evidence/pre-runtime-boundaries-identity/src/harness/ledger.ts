import { DatabaseSync } from 'node:sqlite';
import { createHash, randomUUID } from 'node:crypto';
import { existsSync, realpathSync, readFileSync } from 'node:fs';
import { resolve, dirname, basename } from 'node:path';
import { canonical, strictJson } from '../strict_json.ts';

export type Authorization={objects:number[],fields:string[],deadline:number,maxAttempts:number,maxBytes:number,budgetId?:string};
export type Binding={skillSha256?:string,planHash:string,inputHashes:Record<string,string>,projectRevision:string|null,runtimeIdentity:string,authorization:Authorization};
const digest=(v:any)=>createHash('sha256').update(canonical(v)).digest('hex');

/** 规范化资源身份；符号链接别名不能取得第二份工程占用。 */
export function resourcePath(path:string):string {
  const absolute=resolve(path);
  return existsSync(absolute)?realpathSync(absolute):resolve(resourcePath(dirname(absolute)),basename(absolute));
}

/** SQLite 持久账本：事务提交意图后才允许调用原生端。 */
export class Ledger {
  db:DatabaseSync;closed=false;
  constructor(path:string) {
    this.db=new DatabaseSync(path);this.db.exec('PRAGMA busy_timeout=3000; PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;');
    const version=this.db.prepare('PRAGMA user_version').get() as any;
    if(version.user_version!==0&&version.user_version!==1&&version.user_version!==2){this.db.close();throw new Error('incompatible_state_schema');}
    this.db.exec(`CREATE TABLE IF NOT EXISTS tasks (
      id TEXT PRIMARY KEY, key TEXT UNIQUE NOT NULL, resource TEXT NOT NULL, output TEXT NOT NULL,
      binding_hash TEXT NOT NULL, binding TEXT NOT NULL, epoch INTEGER NOT NULL DEFAULT 1,
      state TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, bytes INTEGER NOT NULL DEFAULT 0, reason TEXT);
      CREATE UNIQUE INDEX IF NOT EXISTS single_writer ON tasks(resource)
        WHERE state IN ('ready','running','reconciling','cancel_requested');
      CREATE TABLE IF NOT EXISTS steps(task TEXT REFERENCES tasks(id), n INTEGER, intent TEXT NOT NULL,
        state TEXT NOT NULL, result TEXT, PRIMARY KEY(task,n));
      CREATE TABLE IF NOT EXISTS budgets(id TEXT PRIMARY KEY,policy TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,bytes INTEGER NOT NULL DEFAULT 0);
      CREATE TABLE IF NOT EXISTS late_receipts(id INTEGER PRIMARY KEY,task TEXT NOT NULL,epoch INTEGER NOT NULL,n INTEGER NOT NULL,result TEXT NOT NULL,received_at INTEGER NOT NULL);
      PRAGMA user_version=2;`);
  }
  transaction<T>(fn:()=>T):T {
    this.db.exec('BEGIN IMMEDIATE');try{const result=fn();this.db.exec('COMMIT');return result;}
    catch(error){this.db.exec('ROLLBACK');throw error;}
  }
  get(id:string):any {
    const row=this.db.prepare('SELECT * FROM tasks WHERE id=?').get(id) as any;
    if(!row)throw new Error('unknown_task');
    return {...row,binding:strictJson(row.binding),bytesReserved:row.bytes};
  }
  checked(id:string,epoch:number):any {
    const row=this.get(id);if(row.epoch!==epoch)throw new Error('stale_epoch');return row;
  }
  claim(key:string,resource:string,output:string,binding:Binding):any {
    const auth=binding.authorization;
    if((binding.skillSha256!==undefined&&!/^[a-f0-9]{64}$/.test(binding.skillSha256))||!key||![binding.planHash,binding.runtimeIdentity,...Object.values(binding.inputHashes)].every(h=>/^[a-f0-9]{64}$/.test(h))
      ||(auth.budgetId!==undefined&&(typeof auth.budgetId!=='string'||!auth.budgetId))
      ||!Array.isArray(auth.objects)||auth.objects.some(x=>!Number.isSafeInteger(x)||x<=0)
      ||!Array.isArray(auth.fields)||auth.fields.some(x=>typeof x!=='string'||!x)
      ||![auth.deadline,auth.maxAttempts,auth.maxBytes].every(x=>Number.isSafeInteger(x)&&x>0)) throw new Error('invalid_task_binding');
    const owner=resourcePath(resource), destination=resourcePath(output),fingerprint=digest({owner,destination,binding});
    return this.transaction(()=>{
      const previous=this.db.prepare('SELECT id,binding_hash FROM tasks WHERE key=?').get(key) as any;
      if(previous){if(previous.binding_hash!==fingerprint)throw new Error('idempotency_conflict');return this.get(previous.id);}
      // 与升级激活共用BEGIN IMMEDIATE，阻止排空检查和新任务占用之间的竞争。
      if(this.db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='runtime_selection'").get()){
        const selected=this.db.prepare('SELECT active FROM runtime_selection WHERE id=1').get() as any;
        if(selected){const active=strictJson(selected.active);
          if(active.mode!=='headless')throw new Error('runtime_mode_mismatch');
          if(active.binarySha256!==binding.runtimeIdentity)throw new Error('runtime_selection_mismatch');
        }
      }
      if(auth.deadline<=Date.now())throw new Error('budget_exceeded');
      if(this.db.prepare("SELECT id FROM tasks WHERE resource=? AND state IN ('ready','running','reconciling','cancel_requested')").get(owner))throw new Error('resource_busy');
      const id=randomUUID(),budgetId=auth.budgetId??id;
      const policy=canonical({deadline:auth.deadline,maxAttempts:auth.maxAttempts,maxBytes:auth.maxBytes});
      const previousBudget=this.db.prepare('SELECT policy FROM budgets WHERE id=?').get(budgetId) as any;
      if(previousBudget&&previousBudget.policy!==policy)throw new Error('shared_budget_conflict');
      this.db.prepare('INSERT OR IGNORE INTO budgets(id,policy) VALUES(?,?)').run(budgetId,policy);
      this.db.prepare('INSERT INTO tasks(id,key,resource,output,binding_hash,binding,state) VALUES(?,?,?,?,?,?,?)')
        .run(id,key,owner,destination,fingerprint,canonical(binding),'ready');
      return this.get(id);
    });
  }
  intent(id:string,epoch:number,step:number,request:any,bytes:number):any {
    return this.transaction(()=>{
      const task=this.checked(id,epoch);
      if(task.state==='reconciling')throw new Error('reconcile_required');
      if(task.state==='cancel_requested'||task.state==='cancelled')throw new Error(task.state);
      if(!['ready','running'].includes(task.state))throw new Error('task_not_running');
      if(!Number.isSafeInteger(step)||step<0||!Number.isSafeInteger(bytes)||bytes<0)throw new Error('invalid_step_budget');
      if(this.db.prepare('SELECT n FROM steps WHERE task=? AND n=?').get(id,step))throw new Error('step_already_submitted');
      const auth=task.binding.authorization;
      const budgetId=auth.budgetId??task.id;
      // 旧 v1 账本的任务在首次继续时迁入私有预算，不能重置已经消耗的额度。
      this.db.prepare('INSERT OR IGNORE INTO budgets(id,policy,attempts,bytes) VALUES(?,?,?,?)').run(budgetId,canonical({deadline:auth.deadline,maxAttempts:auth.maxAttempts,maxBytes:auth.maxBytes}),task.attempts,task.bytes);
      const budget=this.db.prepare('SELECT attempts,bytes FROM budgets WHERE id=?').get(budgetId) as any;
      if(Date.now()>=auth.deadline||budget.attempts+1>auth.maxAttempts||budget.bytes+bytes>auth.maxBytes)throw new Error('budget_exceeded');
      this.db.prepare('UPDATE budgets SET attempts=attempts+1,bytes=bytes+? WHERE id=?').run(bytes,budgetId);
      this.db.prepare("INSERT INTO steps(task,n,intent,state) VALUES(?,?,?,'submitted')").run(id,step,canonical(request));
      this.db.prepare("UPDATE tasks SET state='running',attempts=attempts+1,bytes=bytes+? WHERE id=?").run(bytes,id);
      return this.get(id);
    });
  }
  receipt(id:string,epoch:number,step:number,result:any):any {
    const current=this.get(id);
    if(current.epoch!==epoch){
      this.db.prepare('INSERT INTO late_receipts(task,epoch,n,result,received_at) VALUES(?,?,?,?,?)').run(id,epoch,step,canonical(result),Date.now());
      throw new Error('stale_epoch: receipt quarantined');
    }
    return this.transaction(()=>{
      const task=this.checked(id,epoch);
      if(task.state==='cancel_requested'||task.state==='cancelled'){
        this.db.prepare("UPDATE steps SET state='quarantined',result=? WHERE task=? AND n=? AND state='submitted'").run(canonical(result),id,step);
        return {state:'quarantined',result};
      }
      if(task.state!=='running')throw new Error('task_not_running');
      const updated=this.db.prepare("UPDATE steps SET state='received',result=? WHERE task=? AND n=? AND state='submitted'").run(canonical(result),id,step);
      if(updated.changes!==1)throw new Error('unexpected_step_receipt');return this.get(id);
    });
  }
  unknown(id:string,epoch:number,reason:string):any {
    return this.transaction(()=>{const task=this.checked(id,epoch);
      if(!['running','reconciling','cancel_requested'].includes(task.state))throw new Error('task_not_running');
      this.db.prepare("UPDATE tasks SET state=CASE WHEN state='cancel_requested' THEN state ELSE 'reconciling' END,reason=? WHERE id=?").run(reason,id);
      return this.get(id);
    });
  }
  reconcile(id:string,epoch:number,observation:{stopped:boolean,verified:boolean}):any {
    return this.transaction(()=>{
      const task=this.checked(id,epoch);
      if(task.state!=='reconciling')throw new Error('task_not_reconciling');
      if(observation.stopped!==true)throw new Error('native_stop_unconfirmed');
      if(observation.verified!==true)throw new Error('original_artifact_unverified');
      throw new Error('native_observation_required: booleans cannot prove process stop or original artifact verification');
    });
  }
  cancel(id:string,epoch:number,confirmed:boolean):any {
    return this.transaction(()=>{
      const task=this.checked(id,epoch);
      if(!['ready','running','reconciling','cancel_requested'].includes(task.state))throw new Error('task_not_cancellable');
      if(confirmed)throw new Error('native_observation_required: cancellation cannot release a writer using a boolean');
      this.db.prepare("UPDATE tasks SET state='cancel_requested' WHERE id=?").run(id);
      return this.get(id);
    });
  }
  complete(id:string,epoch:number,proof?:{technical:boolean,accepted:boolean}):any {
    return this.transaction(()=>{
      const task=this.checked(id,epoch);
      if(task.state!=='review_ready'||proof?.technical!==true||proof?.accepted!==true)throw new Error('acceptance_required');
      this.db.prepare("UPDATE tasks SET state='completed' WHERE id=?").run(id);return this.get(id);
    });
  }
  verified(id:string,epoch:number,artifact:{path:string,sha256:string}):any {
    return this.transaction(()=>{
      const task=this.checked(id,epoch);
      if(task.state!=='running')throw new Error('task_not_running');
      if(this.db.prepare("SELECT n FROM steps WHERE task=? AND state!='received'").get(id))throw new Error('unresolved_native_step');
      if(createHash('sha256').update(readFileSync(artifact.path)).digest('hex')!==artifact.sha256)throw new Error('artifact_revision_conflict');
      this.db.prepare("UPDATE tasks SET state='review_ready' WHERE id=?").run(id);return this.get(id);
    });
  }
  close(){if(!this.closed){this.db.close();this.closed=true;}}
}
