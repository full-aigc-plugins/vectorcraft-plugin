import { DatabaseSync } from 'node:sqlite';
import { createHash, randomUUID } from 'node:crypto';
import { readFileSync, realpathSync } from 'node:fs';
import { dirname, resolve, relative, isAbsolute } from 'node:path';
import { canonical, strictJson } from '../strict_json.ts';

const hash=(value:string|Buffer)=>createHash('sha256').update(value).digest('hex');
const keys=(value:any,names:string[])=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).sort().join(',')===names.sort().join(',');
const dimensions=['structure','text','brand','layout','legibility'];

/** 单轮评审交换存储；所有文件读取限制在调用方声明的工作根目录。 */
export class ReviewStore {
  db:DatabaseSync;roots:string[];
  constructor(path:string,roots=[dirname(path)]) {
    this.roots=roots.map(r=>realpathSync(r));
    this.db=new DatabaseSync(path);this.db.exec(`PRAGMA busy_timeout=3000;PRAGMA journal_mode=WAL;
      CREATE TABLE IF NOT EXISTS reviews(id TEXT PRIMARY KEY,binding_hash TEXT,input TEXT,fingerprints TEXT,state TEXT,receipt TEXT);
      CREATE TABLE IF NOT EXISTS review_events(n INTEGER PRIMARY KEY,request TEXT,reason TEXT,receipt TEXT);`);
  }
  fingerprint(path:string):string {
    const file=realpathSync(path);
    if(!this.roots.some(root=>{const sub=relative(root,file);return !isAbsolute(sub)&&sub!=='..'&&!sub.startsWith('../');}))throw new Error('review_path_outside_roots');
    return hash(readFileSync(file));
  }
  request(input:any):any {
    if(!input||typeof input.projectRevision!=='string'||!input.projectRevision||!/^[a-f0-9]{64}$/.test(input.runtimeIdentity??'')
      ||!['PASS','FAIL','NOT_RUN'].includes(input.technicalStatus)||!Array.isArray(input.candidates)||!input.candidates.length
      ||!Array.isArray(input.targets)||!input.targets.some((t:any)=>t.role==='target')
      ||input.targets.some((t:any)=>!keys(t,['path','role'])||typeof t.path!=='string'||!t.path||!['target','judge-reference'].includes(t.role))
      ||typeof input.exchangeLoss!=='string'||!input.exchangeLoss
      ||!input.authorization||!Array.isArray(input.authorization.objects)||input.authorization.objects.some((v:any)=>!Number.isSafeInteger(v)||v<=0)
      ||!Array.isArray(input.authorization.fields)||input.authorization.fields.some((v:any)=>typeof v!=='string'||!v)
      ||input.candidates.some((v:any)=>typeof v!=='string'||!v)
      ||!['deadline','maxAttempts','maxBytes'].every(k=>Number.isSafeInteger(input.authorization[k])&&input.authorization[k]>0)
      ||input.authorization.deadline<=Date.now())throw new Error('invalid_review_request');
    const paths=[input.native,...input.candidates,...input.targets.map((t:any)=>t.path),input.rubric,input.exchangeLoss];
    const fingerprints=Object.fromEntries(paths.map(path=>[path,this.fingerprint(path)]));
    if(fingerprints[input.native]!==input.projectRevision)throw new Error('project_revision_mismatch');
    const bindingHash=hash(canonical({input,fingerprints})),id=randomUUID();
    this.db.prepare("INSERT INTO reviews(id,binding_hash,input,fingerprints,state) VALUES(?,?,?,?,'pending')")
      .run(id,bindingHash,canonical(input),canonical(fingerprints));
    return {schema:'vectorcraft-review-request/v1',id,bindingHash,input,fingerprints,state:'pending'};
  }
  current(id:string):any {
    const row=this.db.prepare('SELECT * FROM reviews WHERE id=?').get(id) as any;
    if(!row)throw new Error('unknown_review_request');
    const input=strictJson(row.input),fingerprints=strictJson(row.fingerprints);
    for(const [path,expected] of Object.entries(fingerprints)) {
      try{if(this.fingerprint(path)!==expected)throw new Error('stale');}
      catch{throw new Error('stale_review_binding');}
    }
    if(hash(canonical({input,fingerprints}))!==row.binding_hash)throw new Error('stale_review_binding');
    return {...row,input,fingerprints};
  }
  importReceipt(value:string|any):any {
    try{return this.receiveReceipt(value);}catch(error){
      const raw=typeof value==='string'?value:JSON.stringify(value);
      const id=typeof value==='object'&&typeof value?.requestId==='string'?value.requestId:null;
      this.db.prepare('INSERT INTO review_events(request,reason,receipt) VALUES(?,?,?)').run(id,String(error),raw??'unserializable');
      throw error;
    }
  }
  receiveReceipt(value:string|any):any {
    const receipt=typeof value==='string'?strictJson(value):strictJson(canonical(value));
    if(!keys(receipt,['schema','requestId','bindingHash','reviewer','verdict','issues','scores'])
      ||receipt.schema!=='vectorcraft-review-receipt/v1'||!['accept','revise','reject'].includes(receipt.verdict)
      ||!keys(receipt.reviewer,['kind','identity','contextOrigin','independenceEvidence'])
      ||!['human','host-model'].includes(receipt.reviewer.kind)||typeof receipt.reviewer.identity!=='string'||!receipt.reviewer.identity||typeof receipt.reviewer.contextOrigin!=='string'||!receipt.reviewer.contextOrigin
      ||(receipt.reviewer.independenceEvidence!==null&&typeof receipt.reviewer.independenceEvidence!=='string')
      ||!Array.isArray(receipt.issues)||!keys(receipt.scores,[...dimensions])
      ||dimensions.some(k=>typeof receipt.scores[k]!=='number'||!Number.isFinite(receipt.scores[k])||receipt.scores[k]<0||receipt.scores[k]>4))throw new Error('invalid_review_receipt');
    for(const issue of receipt.issues)if(!keys(issue,['objectId','field','message','evidence'])||!Number.isSafeInteger(issue.objectId)||issue.objectId<=0
      ||typeof issue.field!=='string'||!issue.field||typeof issue.message!=='string'||!issue.message||!Array.isArray(issue.evidence)
      ||issue.evidence.some((v:any)=>typeof v!=='string'||!v))throw new Error('invalid_review_issue');
    this.db.exec('BEGIN IMMEDIATE');
    try {
      const row=this.current(receipt.requestId);
      if(row.state!=='pending')throw new Error('duplicate_review_receipt');
      if(row.binding_hash!==receipt.bindingHash)throw new Error('stale_review_binding');
      const state=row.input.technicalStatus!=='PASS'?'technical_failed':receipt.verdict==='revise'?'revision_proposed':receipt.verdict==='accept'?'review_ready':'rejected';
      this.db.prepare('UPDATE reviews SET state=?,receipt=? WHERE id=?').run(state,canonical(receipt),row.id);
      this.db.exec('COMMIT');return {state,requestId:row.id,issues:receipt.issues,independent:false,
        independenceStatus:receipt.reviewer.independenceEvidence===null?'not_claimed':'unverified',
        independenceEvidence:receipt.reviewer.independenceEvidence,technicalStatus:row.input.technicalStatus,creativeVerdict:receipt.verdict,
        scores:receipt.scores,exchangeLossSha256:row.fingerprints[row.input.exchangeLoss],acceptanceStatus:'pending'};
    }catch(error){this.db.exec('ROLLBACK');throw error;}
  }
  revision(id:string,changes:{objectId:number,field:string,value:any}[]):any {
    const row=this.current(id),auth=row.input.authorization;
    if(auth.deadline<=Date.now())throw new Error('budget_exceeded');
    if(row.state!=='revision_proposed')throw new Error('revision_not_proposed');
    if(!Array.isArray(changes)||!changes.length||changes.some(c=>!auth.objects.includes(c.objectId)||!auth.fields.includes(c.field)))throw new Error('revision_outside_authorization');
    const assessed=strictJson(row.receipt).issues;
    if(changes.some(c=>!assessed.some((issue:any)=>issue.objectId===c.objectId&&issue.field===c.field)))throw new Error('revision_not_assessed');
    return {schema:'vectorcraft-local-revision-proposal/v1',requestId:id,bindingHash:row.binding_hash,
      expectedProjectRevision:row.input.projectRevision,changes:strictJson(canonical(changes)),authorization:auth,state:'proposed'};
  }
  close(){this.db.close();}
}
