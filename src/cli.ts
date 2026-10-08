#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { strictJson } from './strict_json.ts';
import { Controller } from './harness/controller.ts';
import { ReviewStore } from './evaluation/review_store.ts';

/** 文件形式的显式请求入口；不安装依赖、不发起外部评审、不自动生成下一轮。 */
async function main(){
  const [action,database,file]=process.argv.slice(2);
  if(!action||!database||!file)throw new Error('usage: node src/cli.ts run|cancel|reconcile|review-request|review-import|revision DATABASE REQUEST.json');
  const input=strictJson(readFileSync(file,'utf8'));
  if(['run','cancel','reconcile'].includes(action)){
    const controller=new Controller(database);try{
      if(action==='cancel')return controller.requestCancel(input.taskId,input.epoch);
      if(action==='reconcile')return await controller.reconcileOriginal(input.taskId,input.epoch);
      return await controller.run(input);
    }finally{controller.close();}
  }
  const store=new ReviewStore(database,input.readRoots);
  try{
    if(action==='review-request')return store.request(input);
    if(action==='review-import')return store.importReceipt(input);
    if(action==='revision')return store.revision(input.requestId,input.changes);
    throw new Error('unknown_action');
  }finally{store.close();}
}
try{console.log(JSON.stringify(await main(),null,2));}catch(error){console.error(JSON.stringify({state:'failed',error:String(error)}));process.exitCode=1;}
