import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync,writeFileSync,rmSync,readFileSync,mkdirSync,chmodSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { canonical } from '../src/strict_json.ts';
import { ReviewStore } from '../src/evaluation/review_store.ts';

const hash=(v:string)=>createHash('sha256').update(v).digest('hex');
function fixture(){
 const root=mkdtempSync(join(tmpdir(),'bounded vector review ')),native=join(root,'project.vectorcraft'),preview=join(root,'preview.png'),brief=join(root,'brief.txt'),rubric=join(root,'rubric.json');
 for(const [p,v] of [[native,'native'],[preview,'pixels'],[brief,'brand'],[rubric,'{}']])writeFileSync(p,v);
 const store=new ReviewStore(join(root,'reviews.sqlite'),[root]);
 const input={native,projectRevision:hash('native'),runtimeIdentity:'a'.repeat(64),candidates:[preview],targets:[{path:brief,role:'target'}],rubric,exchangeLoss:rubric,technicalStatus:'PASS',authorization:{objects:[2],fields:['paint.color'],deadline:Date.now()+60000,maxAttempts:20,maxBytes:16*1024*1024,budgetId:'bounded-test',readRoots:[root],writeRoots:[root]}};
 const request=store.request(input);store.importReceipt({schema:'vectorcraft-review-receipt/v1',requestId:request.id,bindingHash:request.bindingHash,reviewer:{kind:'human',identity:'fixture only',contextOrigin:'test',independenceEvidence:null},verdict:'revise',issues:[{objectId:2,field:'paint.color',message:'fixture',evidence:['preview.png']}],scores:{structure:2,text:2,brand:2,layout:2,legibility:2}});
 return {root,store,input,request,close:()=>{try{store.close();}catch{}rmSync(root,{recursive:true,force:true});}};
}

test('a review assigned to a durable bounded cycle cannot bypass it through legacy revision',()=>{
 const f=fixture();try{
  f.store.db.exec('CREATE TABLE revision_members(review TEXT PRIMARY KEY,cycle TEXT NOT NULL);');
  f.store.db.prepare('INSERT INTO revision_members(review,cycle) VALUES(?,?)').run(f.request.id,'round-limit-reached');
  assert.throws(()=>f.store.revision(f.request.id,[{objectId:2,field:'paint.color',value:'#fff'}]),/revision_cycle_required/);
 }finally{f.close();}
});
