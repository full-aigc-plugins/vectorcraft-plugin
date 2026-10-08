"""可信宿主的素材摘要入口：复用固定技能的安全读取，不自行扩大冻结根。"""
import importlib.util
import json
from pathlib import Path
import sys


def main():
    """从标准输入接收宿主绑定的路径／根，只输出摘要或固定错误码。"""
    request = json.load(sys.stdin)
    roots = request['roots']
    if (not isinstance(roots, list) or len(roots) > 256
            or any(not isinstance(value, str) or not Path(value).is_absolute()
                   or any(ord(c) < 32 for c in value) for value in roots)):
        raise ValueError('asset_read_roots_invalid')
    spec = importlib.util.spec_from_file_location('craft_parent_asset_reader', sys.argv[1])
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    # 根已由Controller冻结为物理路径；不能再次resolve根来跟随后续替换。
    operation = request.get('operation', 'asset-digest')
    if operation == 'file-digests':
        paths = request.get('paths')
        if (not isinstance(paths, list) or len(paths) > 4096
                or any(not isinstance(path, str) or not Path(path).is_absolute() for path in paths)):
            raise ValueError('asset_input_invalid')
        digests = {}
        for path in paths:
            digests[path], _ = reader.digest_authorized(path, roots)
        print(json.dumps({'digests': digests}))
        return
    if operation == 'file-digest':
        digest, _ = reader.digest_authorized(request['path'], roots)
        print(json.dumps({'sha256': digest}))
        return
    if operation not in {'asset-digest', 'file-read'}:
        raise ValueError('asset_input_invalid')
    data, _ = reader.read_authorized(request['path'], roots)
    import hashlib
    reply = {'sha256': hashlib.sha256(data).hexdigest()}
    if operation == 'file-read':
        import base64
        reply['base64'] = base64.b64encode(data).decode('ascii')
    print(json.dumps(reply))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        allowed = {'asset_read_outside_root', 'asset_read_roots_invalid', 'asset_path_invalid',
                   'asset_digest_mismatch', 'asset_input_identity_changed'}
        code = str(error) if isinstance(error, ValueError) and str(error) in allowed else 'asset_input_invalid'
        print(json.dumps({'error': code}))
        raise SystemExit(1)
