import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root=fileURLToPath(new URL('../../',import.meta.url));
const paths=['src/evaluation/delivery_quality.py','src/harness/process_runner.py','skills/vectorcraft-use/scripts/exchange_loss.py'];

/** 捕获检查器及直接本地依赖的执行字节；来源路径相对安装根目录。 */
export function captureChecker():{files:Record<string,string>,contents:Map<string,Buffer>}{
  const contents=new Map(paths.map(path=>[path,readFileSync(join(root,path))]));
  return {contents,files:Object.fromEntries([...contents].map(([path,value])=>[path,createHash('sha256').update(value).digest('hex')]))};
}

/** 重新读取当前安装的检查器身份；用于阻止陈旧结果及首次交接时的依赖漂移。 */
export function checkerFiles():Record<string,string>{return captureChecker().files;}
