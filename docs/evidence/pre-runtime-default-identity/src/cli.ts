#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { RuntimeGate,validateCapabilities } from './runtime/runtime_gate.ts';
import { strictJson } from './strict_json.ts';
import { Controller,skillDigest } from './harness/controller.ts';
import { ReviewStore } from './evaluation/review_store.ts';
import { TechnicalReview } from './evaluation/technical_review.ts';
import { RevisionCycle } from './evaluation/revision_cycle.ts';

/** 文件形式的显式请求入口；不安装依赖、不发起外部评审、不自动生成下一轮。 */
async function main(){
  const [action,database,file]=process.argv.slice(2);
  if(!action||!database||!file)throw new Error('usage: node src/cli.ts run|cancel|reconcile|review-request|review-checked|review-import|revision|revision-cycle-open|revision-cycle-observe|revision-cycle-propose|revision-cycle-run|revision-cycle-best DATABASE REQUEST.json');
  const input=strictJson(readFileSync(file,'utf8'));
  if(['runtime-probe','runtime-activate','runtime-status'].includes(action)){
    const controller=new Controller(database);try{
      const gate=new RuntimeGate(controller.ledger);
      if(action==='runtime-status')return gate.current();
      if(skillDigest(input.skill)!==input.expectedSkillSha256)throw new Error('skill_snapshot_mismatch');
      const output=execFileSync(input.python??'python3',['-I','-B',fileURLToPath(new URL('./runtime/runtime_probe.py',import.meta.url))],
        {input:JSON.stringify(input),encoding:'utf8',timeout:40000,maxBuffer:8*1024*1024});
      if(skillDigest(input.skill)!==input.expectedSkillSha256)throw new Error('skill_snapshot_mismatch');
      const report=strictJson(output);validateCapabilities(report,input.requirements);
      return action==='runtime-probe'?report:gate.activate(report,input.requirements,input.stateSchemas);
    }finally{controller.close();}
  }
  if(['run','cancel','reconcile'].includes(action)){
    const controller=new Controller(database);try{
      if(action==='cancel')return controller.requestCancel(input.taskId,input.epoch);
      if(action==='reconcile')return await controller.reconcileOriginal(input.taskId,input.epoch);
      return await controller.run(input);
    }finally{controller.close();}
  }
  const store=new ReviewStore(database,input.readRoots);
  try{
    if(action.startsWith('revision-cycle-')){
      const cycle=new RevisionCycle(store);try{
        if(action==='revision-cycle-open')return cycle.open(input);
        if(action==='revision-cycle-observe')return cycle.observe(input.cycleId,input.requestId,input.proposalId);
        if(action==='revision-cycle-propose')return cycle.propose(input.cycleId,input.requestId,input.changes,input.key);
        if(action==='revision-cycle-run')return await cycle.execute(input.cycleId,input.proposalId,input.run);
        if(action==='revision-cycle-best')return cycle.best(input.cycleId);
        throw new Error('unknown_action');
      }finally{cycle.close();}
    }
    if(action==='review-request')return store.request(input);
    if(action==='review-checked')return await new TechnicalReview(store).request(input);
    if(action==='review-import')return store.importReceipt(input);
    if(action==='revision')return store.revision(input.requestId,input.changes);
    throw new Error('unknown_action');
  }finally{store.close();}
}
try{console.log(JSON.stringify(await main(),null,2));}catch(error){console.error(JSON.stringify({state:'failed',error:String(error)}));process.exitCode=1;}
