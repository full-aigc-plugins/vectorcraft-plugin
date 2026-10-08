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
    data, _ = reader.read_authorized(request['path'], roots)
    import hashlib
    print(json.dumps({'sha256': hashlib.sha256(data).hexdigest()}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        allowed = {'asset_read_outside_root', 'asset_read_roots_invalid', 'asset_path_invalid',
                   'asset_digest_mismatch', 'asset_input_identity_changed'}
        code = str(error) if isinstance(error, ValueError) and str(error) in allowed else 'asset_input_invalid'
        print(json.dumps({'error': code}))
        raise SystemExit(1)
