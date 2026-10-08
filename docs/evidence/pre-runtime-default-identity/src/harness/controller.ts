import { createHash } from 'node:crypto';
import { existsSync, lstatSync, readdirSync, readFileSync, mkdirSync, writeFileSync, cpSync, statSync, openSync, closeSync, fsyncSync, renameSync } from 'node:fs';
import { relative, resolve, join, isAbsolute, dirname } from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { RuntimeGate,validateCapabilities } from '../runtime/runtime_gate.ts';
import { ProcessRegistry } from './process_registry.ts';
import { Recovery } from './recovery.ts';
import { Ledger, resourcePath } from './ledger.ts';
import type { Authorization } from './ledger.ts';
import { strictJson, canonical } from '../strict_json.ts';
import { validateGeometryContract,verifyGeometry } from '../planning/geometry.ts';
import type { GeometryContract } from '../planning/geometry.ts';

const sha=(value:string|Buffer)=>createHash('sha256').update(value).digest('hex');
const inside=(root:string,path:string)=>{const sub=relative(resourcePath(root),resourcePath(path));return !isAbsolute(sub)&&sub!=='..'&&!sub.startsWith('../');};

/** 与固定快照工具一致的整技能摘要，不读取目录链接或额外文件类型。 */
export function skillDigest(root:string):string {
  const files:string[]=[];
  const walk=(path:string)=>{
    if(lstatSync(path).isSymbolicLink())throw new Error('skill_snapshot_symlink');
    for(const name of readdirSync(path).sort()){
      const entry=join(path,name),stat=lstatSync(entry);
      if(stat.isSymbolicLink())throw new Error('skill_snapshot_symlink');
      if(stat.isDirectory())walk(entry);else if(stat.isFile())files.push(entry);else throw new Error('skill_snapshot_entry');
    }
  };
  walk(root);const hash=createHash('sha256');
  for(const file of files.sort((a,b)=>relative(root,a)<relative(root,b)?-1:1))hash.update(relative(root,file)+'\0'+sha(readFileSync(file))+'\n');
  return hash.digest('hex');
}

type RunRequest={key:string,skill:string,expectedSkillSha256:string,plan:string,output:string,source?:string,
  runtimeHome:string,python?:string,estimatedBytes:number,inputFingerprints?:Record<string,string>,geometryContract?:GeometryContract,authorization:Authorization&{readRoots:string[],writeRoots:string[]}};

/** 仅协调已固定的独立技能；原生命令语义与失败工程保留由源技能负责。 */
export class Controller {
  ledger:Ledger;snapshotRoot:string;processes:ProcessRegistry;
  constructor(database:string){this.ledger=new Ledger(database);this.processes=new ProcessRegistry(this.ledger.db);this.snapshotRoot=join(dirname(resolve(database)),'plan-snapshots');}
  /** 原子公布撤销状态；这里只请求取消，停止和原文件核验之前不释放资源。 */
  requestCancel(id:string,epoch:number):any {
    const registered=this.ledger.db.prepare('SELECT task FROM native_processes WHERE task=? AND epoch=?').get(id,epoch);
    if(registered)this.processes.observe(id,epoch);
    const task=this.ledger.cancel(id,epoch,false);
    this.publishState(id,epoch,'cancel_requested');
    if(registered){
      try{this.processes.signal(id,epoch,'SIGTERM');}
      catch(error){return this.ledger.unknown(id,epoch,'native_stop_unconfirmed: '+String(error));}
    }
    return task;
  }
  publishState(id:string,epoch:number,state:string){
    const path=join(this.snapshotRoot,id+'-state.json'),temporary=path+'.next';
    writeFileSync(temporary,canonical({task:id,epoch,state}),{mode:0o600});
    const fd=openSync(temporary,'r');try{fsyncSync(fd);}finally{closeSync(fd);}
    renameSync(temporary,path);
  }
  async reconcileOriginal(id:string,epoch:number){
    const recovery=new Recovery(this.ledger,this.processes);
    const proof=await recovery.inspect(id,epoch);
    return {proof,task:recovery.settle(id,epoch,proof.checkId)};
  }
  verifyDelivery(output:string,runtime:string,geometryContract?:GeometryContract):any {
    const manifest=strictJson(readFileSync(join(output,'manifest.json'),'utf8'));
    if(manifest.schema!=='vectorcraft-delivery/v1'||manifest.runtimeSha256!==runtime)throw new Error('runtime_identity_mismatch');
    if(!manifest.files||typeof manifest.files!=='object'||!manifest.files['project.vectorcraft'])throw new Error('invalid_delivery_manifest');
    for(const [path,digest] of Object.entries(manifest.files)){
      if(isAbsolute(path)||path.split('/').some(p=>['','..','.'].includes(p))||path.includes('\\'))throw new Error('invalid_artifact_path');
      const file=join(output,path);
      if(!inside(output,file)||lstatSync(file).isSymbolicLink()||!lstatSync(file).isFile()||sha(readFileSync(file))!==digest)throw new Error('artifact_digest_mismatch');
    }
    if(geometryContract){
      if(!manifest.files['native.json'])throw new Error('geometry_native_snapshot_missing');
      const report=verifyGeometry(strictJson(readFileSync(join(output,'native.json'),'utf8')),manifest.bindings??{},geometryContract);
      const bound={...report,nativeSha256:manifest.files['native.json'],projectRevision:manifest.files['project.vectorcraft'],runtimeIdentity:runtime,contractSha256:sha(canonical(geometryContract))};
      if(report.status!=='PASS')throw new Error('geometry_acceptance_failed: '+canonical(bound));
      manifest.geometryVerification=bound;
    }
    return manifest;
  }
  async run(request:RunRequest):Promise<any> {
    const geometryContract=request.geometryContract===undefined?undefined:strictJson(canonical(request.geometryContract));
    if(geometryContract!==undefined)validateGeometryContract(geometryContract);
    const auth=request.authorization;
    if(!Array.isArray(auth?.readRoots)||!Array.isArray(auth?.writeRoots))throw new Error('authorization_roots_required');
    for(const path of [request.plan,...(request.source?[request.source]:[])])if(!auth.readRoots.some(root=>inside(root,path)))throw new Error('outside_authorized_roots');
    for(const path of [request.output,request.runtimeHome])if(!auth.writeRoots.some(root=>inside(root,path)))throw new Error('outside_authorized_roots');
    if(skillDigest(request.skill)!==request.expectedSkillSha256)throw new Error('skill_snapshot_mismatch');
    if(!existsSync(join(request.skill,'scripts/execution_control.py')))throw new Error('managed_execution_control_required');
    const plan=strictJson(readFileSync(request.plan,'utf8'));
    if(plan.schema)throw new Error('workflow_plan_required; complete-command plans use the independent commands entry');
    const lock=strictJson(readFileSync(join(request.skill,'scripts/runtime.lock.json'),'utf8'));
    let projectRevision:string|null=null;
    if(request.source){
      if(!auth.readRoots.some(root=>inside(root,join(request.source!,'project.vectorcraft'))))throw new Error('outside_authorized_roots');
      projectRevision=sha(readFileSync(join(request.source,'project.vectorcraft')));
      if(projectRevision!==plan.expectedProjectSha256)throw new Error('revision_conflict');
    }
    const inputHashes:Record<string,string>={};
    const guards=request.inputFingerprints??{};
    if(!guards||typeof guards!=='object'||Array.isArray(guards)||Object.keys(guards).length>4096)throw new Error('invalid_input_fingerprints');
    const checkInputs=()=>{
      for(const [path,expected] of Object.entries(guards)){
        if(!/^[a-f0-9]{64}$/.test(expected)||!auth.readRoots.some(root=>inside(root,path)))throw new Error('outside_authorized_roots');
        if(sha(readFileSync(path))!==expected)throw new Error('stale_execution_inputs');
      }
    };
    checkInputs();
    for(const [path,expected] of Object.entries(guards))inputHashes['guard:'+path]=expected;
    for(const [name,asset] of Object.entries(plan.assets??{}) as [string,any][]){
      if(!auth.readRoots.some(root=>inside(root,asset.path)))throw new Error('outside_authorized_roots');
      const hash=sha(readFileSync(asset.path));if(hash!==asset.sha256)throw new Error('asset_digest_mismatch');inputHashes[name]=hash;
    }
    if(geometryContract)inputHashes['contract:geometry']=sha(canonical(geometryContract));
    const runtimeIdentity=lock.artifacts['darwin-arm64'].binarySha256;
    const selected=new RuntimeGate(this.ledger).current();
    if(selected){
      const catalog=strictJson(readFileSync(join(request.skill,'references/command-coverage.json'),'utf8'));
      validateCapabilities(selected.active,{mode:'headless',commands:Object.fromEntries(catalog.commands.map((r:any)=>[r.id,r.params])),tools:{}});
      inputHashes['runtime:capabilities']=sha(canonical({commands:selected.active.commands,tools:selected.active.tools,mode:selected.active.mode}));
    }

    const binding={skillSha256:request.expectedSkillSha256,planHash:sha(canonical(plan)),inputHashes,projectRevision,runtimeIdentity,authorization:auth};
    const task=this.ledger.claim(request.key,request.source?join(request.source,'project.vectorcraft'):join(request.output,'project.vectorcraft'),request.output,binding);
    if(task.state!=='ready'){
      let geometryVerification:any;
      if(task.state==='review_ready'||task.state==='completed'){
        geometryVerification=this.verifyDelivery(request.output,runtimeIdentity,geometryContract).geometryVerification;
        const received=this.ledger.db.prepare('SELECT result FROM steps WHERE task=? AND n=0').get(task.id) as any;
        if(!received?.result||strictJson(received.result).manifestSha256!==sha(readFileSync(join(request.output,'manifest.json'))))throw new Error('receipt_manifest_mismatch');
      }
      return {...task,...(geometryContract&&geometryVerification?{geometryVerification}:{}),resumePolicy:'inspect original files and request; no automatic replay'};
    }
    if(existsSync(request.output))throw new Error('output_exists');
    mkdirSync(this.snapshotRoot,{recursive:true,mode:0o700});
    const skillSnapshot=join(this.snapshotRoot,task.id+'-skill');
    cpSync(request.skill,skillSnapshot,{recursive:true,errorOnExist:true,force:false});
    if(skillDigest(skillSnapshot)!==request.expectedSkillSha256)throw new Error('skill_snapshot_mismatch');
    const planSnapshot=join(this.snapshotRoot,task.id+'.json');
    writeFileSync(planSnapshot,canonical(plan),{flag:'wx',mode:0o400});
    const eventFile=join(this.snapshotRoot,task.id+'-events.jsonl');
    writeFileSync(eventFile,'',{flag:'wx',mode:0o600});const eventStat=statSync(eventFile);
    this.publishState(task.id,task.epoch,'running');
    const controlFile=join(this.snapshotRoot,task.id+'-control.json');
    writeFileSync(controlFile,canonical({schema:'vectorcraft-execution-control/v1',task:task.id,epoch:task.epoch,
      deadline:auth.deadline,maxBytes:Math.min(auth.maxBytes,request.estimatedBytes),runtimeIdentity,authorization:auth,
      planFile:planSnapshot,planHash:binding.planHash,stateFile:join(this.snapshotRoot,task.id+'-state.json'),
      eventFile,eventDevice:eventStat.dev,eventInode:eventStat.ino,
      ...(request.source?{source:{path:join(resourcePath(request.source),'project.vectorcraft'),sha256:projectRevision}}:{})}),{flag:'wx',mode:0o400});
    for(const file of [planSnapshot,controlFile,eventFile]){const fd=openSync(file,'r');try{fsyncSync(fd);}finally{closeSync(fd);}}
    this.ledger.intent(task.id,task.epoch,0,{skillSha256:request.expectedSkillSha256,planHash:binding.planHash,plan,planSnapshot,skillSnapshot,output:resourcePath(request.output),controlFile,runtimeHome:resourcePath(request.runtimeHome),source:request.source?resourcePath(request.source):null,python:request.python??'python3',...(geometryContract?{geometryContract}:{})},request.estimatedBytes);
    const args=['-I','-B',join(skillSnapshot,'scripts/workflow.py'),planSnapshot,'--output',request.output,'--runtime-home',request.runtimeHome,'--control',controlFile];
    if(request.source)args.push('--source',request.source);
    let stdout='',stderr='';
    try {
      await new Promise<void>((accept,reject)=>{
        const launcher=fileURLToPath(new URL('./process_runner.py',import.meta.url));
        const child=spawn(request.python??'python3',['-I','-B',launcher,task.id,...args],{detached:true,stdio:['pipe','pipe','pipe']});
        let interrupted=false,stopping:Promise<any>|undefined,observationError:unknown;
        const interrupt=()=>{
          if(interrupted)return;interrupted=true;
          try{if(this.ledger.get(task.id).state!=='cancel_requested')this.requestCancel(task.id,task.epoch);
            else this.publishState(task.id,task.epoch,'cancel_requested');}
          catch(error){observationError=error;}
          stopping=this.processes.stop(task.id,task.epoch).catch(error=>{observationError=error;});
        };
        const timer=setInterval(()=>{
          try{
            checkInputs();
            const state=this.ledger.get(task.id).state;
            this.processes.observe(task.id,task.epoch);
            if(Date.now()>=auth.deadline||state==='cancel_requested'||state==='cancelled')interrupt();
          }catch(error){observationError=error;interrupt();}
        },50);
        const capture=(kind:'out'|'err',data:Buffer)=>{
          const remaining=8*1024*1024-Buffer.byteLength(stdout)-Buffer.byteLength(stderr);
          const chunk=data.subarray(0,Math.max(0,remaining)).toString();
          if(kind==='out')stdout+=chunk;else stderr+=chunk;
          if(data.length>=remaining)interrupt();
        };
        child.stdout.on('data',data=>capture('out',data));child.stderr.on('data',data=>capture('err',data));
        child.on('error',error=>{clearInterval(timer);reject(error);});
        child.on('spawn',()=>{
          try{this.processes.register(task.id,task.epoch,child.pid!,task.id);checkInputs();
            child.stdin.end(canonical({task:task.id,go:true})+'\n');}
          catch(error){observationError=error;child.kill('SIGKILL');child.stdin.destroy();}
        });
        child.stdin.on('error',()=>{});
        child.on('exit',()=>{
          // 父进程退出后仍要终止已经确认归属的后代，否则 pipe 和工程占用都可能持续。
          try{if(!this.processes.observe(task.id,task.epoch).stopped)interrupt();}
          catch(error){observationError=error;}
        });
        child.on('close',async code=>{
          clearInterval(timer);await stopping;
          try{if(!this.processes.observe(task.id,task.epoch).stopped)throw new Error('native_stop_unconfirmed');}
          catch(error){observationError=error;}
          if(code===0&&!interrupted&&!observationError)accept();
          else reject(new Error('outcome_unknown: original native workflow needs reconciliation; '+String(observationError??'')+stderr.slice(0,2048)+stdout.slice(0,2048)));
        });
      });
      if(['cancel_requested','cancelled'].includes(this.ledger.get(task.id).state))return {id:task.id,state:'quarantined',output:request.output};
      const manifest=this.verifyDelivery(request.output,runtimeIdentity,geometryContract);
      checkInputs();
      const bytes=Object.keys(manifest.files).reduce((total,path)=>total+lstatSync(join(request.output,path)).size,0);
      if(bytes>request.estimatedBytes||bytes>auth.maxBytes)throw new Error('budget_exceeded: output exceeds reservation');
      if(request.source&&sha(readFileSync(join(request.source,'project.vectorcraft')))!==projectRevision)throw new Error('revision_conflict');
      this.ledger.receipt(task.id,task.epoch,0,{manifestSha256:sha(readFileSync(join(request.output,'manifest.json'))),runtimeIdentity,...(geometryContract?{geometryVerification:manifest.geometryVerification}:{})});
      const verified=this.ledger.verified(task.id,task.epoch,{path:join(request.output,'project.vectorcraft'),sha256:manifest.files['project.vectorcraft']});
      return {...verified,...(geometryContract?{geometryVerification:manifest.geometryVerification}:{})};
    }catch(error){this.ledger.unknown(task.id,task.epoch,String(error));throw error;}
  }
  close(){this.ledger.close();}
}
