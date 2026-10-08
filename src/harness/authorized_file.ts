import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {strictJson} from '../strict_json.ts';
import {nativeEnvironment} from './native_environment.ts';

/** 可信宿主读取入口：固定技能读取器持有描述符，冻结根不会随目录替换扩张。 */
function inspect(path:string,roots:string[],operation:'file-read'|'file-digest'):any {
 const helper=fileURLToPath(new URL('./asset_digest.py',import.meta.url));
 const reader=fileURLToPath(new URL('../../skills/vectorcraft-use/scripts/asset_reader.py',import.meta.url));
 const result=spawnSync('python3',['-I','-B',helper,reader],{input:JSON.stringify({path,roots,operation}),encoding:'utf8',env:nativeEnvironment(),timeout:30000,maxBuffer:operation==='file-read'?96*1024*1024:4096});
 if(result.error)throw new Error('authorized_read_process_failed');
 let reply:any;try{reply=strictJson(result.stdout);}catch{throw new Error('authorized_read_reply_invalid');}
 if(result.status!==0){
  const reasons=new Set(['asset_read_outside_root','asset_read_roots_invalid','asset_path_invalid','asset_digest_mismatch','asset_input_identity_changed']);
  throw new Error(reasons.has(reply?.error)?reply.error:'authorized_read_failed');
 }
 if(!reply||!/^[a-f0-9]{64}$/.test(reply.sha256??''))throw new Error('authorized_read_reply_invalid');
 return reply;
}

/** 读取不超过既有64MiB上限的授权文件；返回字节前核对传输摘要。 */
export function authorizedRead(path:string,roots:string[]):Buffer {
 const reply=inspect(path,roots,'file-read');
 if(typeof reply.base64!=='string'||reply.base64.length>Math.ceil(64*1024*1024/3)*4)throw new Error('authorized_read_reply_invalid');
 const bytes=Buffer.from(reply.base64,'base64');
 if(bytes.toString('base64')!==reply.base64||createHash('sha256').update(bytes).digest('hex')!==reply.sha256)throw new Error('authorized_read_reply_invalid');
 return bytes;
}

/** 流式计算授权文件摘要，不额外限制已有评审输入的大小。 */
export function authorizedDigest(path:string,roots:string[]):string {
 return inspect(path,roots,'file-digest').sha256;
}
