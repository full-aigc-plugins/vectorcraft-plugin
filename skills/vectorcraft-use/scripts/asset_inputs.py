"""登记输入预检与收集；不允许计划直接选择原生命令文件路径。"""
import hashlib
import math
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET

NAME = re.compile(r'[A-Za-z][A-Za-z0-9_-]{0,63}')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_operation(command, params):
    allowed = {'asset', 'at', 'rect', 'link'} if command == 'asset.place' else {'asset', 'replacement'}
    if set(params) - allowed or not isinstance(params.get('asset'), str) or not NAME.fullmatch(params['asset']):
        raise ValueError('invalid_asset_operation')
    if command == 'asset.replace':
        replacement = params.get('replacement')
        if not isinstance(replacement, str) or not NAME.fullmatch(replacement) or replacement == params['asset']:
            raise ValueError('invalid_asset_operation')
    if 'link' in params and type(params['link']) is not bool:
        raise ValueError('invalid_asset_operation')
    if 'at' in params and 'rect' in params:
        raise ValueError('invalid_asset_operation')
    for key, length in [('at', 2), ('rect', 4)]:
        if key in params:
            value = params[key]
            if not isinstance(value, list) or len(value) != length or any(type(n) not in (int, float) or not math.isfinite(n) or abs(n) > 1e6 for n in value):
                raise ValueError('invalid_asset_operation')
            if key == 'rect' and any(n <= 0 for n in value[2:]):
                raise ValueError('invalid_asset_operation')


def source_file(root, location):
    if not isinstance(location, str) or not location or '\\' in location or ':' in location or Path(location).is_absolute() or any(p in ('', '.', '..') for p in location.split('/')):
        raise ValueError('asset_path_invalid')
    path = Path(root) / location
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('asset_path_invalid')
    return path


def preflight(plan, source=None, prior=None):
    """输入先验摘要及消费检查必须在 CLI 安装与输出目录创建之前完成。"""
    entries = {}
    previous = (prior or {}).get('assets', {})
    if not isinstance(previous, dict):
        raise ValueError('asset_record_invalid')
    for name, value in previous.items():
        if not NAME.fullmatch(name) or not isinstance(value, dict):
            raise ValueError('asset_record_invalid')
        path = source_file(source, value.get('path'))
        if (prior or {}).get('files', {}).get(value['path']) != value.get('sha256'):
            raise ValueError('asset_digest_mismatch')
        ids = value.get('ids')
        if not isinstance(ids, list) or not ids or any(type(i) is not int or i <= 0 for i in ids) or len(ids) != len(set(ids)) or type(value.get('linked')) is not bool:
            raise ValueError('asset_record_invalid')
        entries[name] = {**value, 'inputPath': path}
    inputs = plan.get('assets', {})
    if not isinstance(inputs, dict):
        raise ValueError('asset_record_invalid')
    for name, value in inputs.items():
        if not isinstance(name, str) or not NAME.fullmatch(name) or name in entries or not isinstance(value, dict) or set(value) != {'path', 'sha256'}:
            raise ValueError('asset_record_invalid')
        if not isinstance(value['path'], str):
            raise ValueError('asset_path_invalid')
        path = Path(value['path'])
        if not path.is_absolute() or path.is_symlink() or not path.is_file():
            raise ValueError('asset_path_invalid')
        entries[name] = {**value, 'inputPath': path}
    for entry in entries.values():
        path = entry['inputPath']
        if path.stat().st_size > 64*1024*1024 or not isinstance(entry.get('sha256'), str) or not re.fullmatch(r'[a-f0-9]{64}', entry['sha256']) or sha(path) != entry['sha256']:
            raise ValueError('asset_digest_mismatch')
    consumed = set()
    live = {name for name in entries if 'ids' in entries[name]}
    for op in plan['operations']:
        if op['command'] not in ('asset.place', 'asset.replace'):
            continue
        params = op['params']; name = params['asset']
        if name not in entries or (op['command'] == 'asset.replace' and name not in live):
            raise ValueError('asset_binding_invalid')
        if op['command'] == 'asset.replace':
            name = params['replacement']
            if name not in entries or name in live or name in consumed:
                raise ValueError('asset_binding_invalid')
        else:
            live.add(name)
        if name in inputs:
            consumed.add(name)
    if set(inputs) != consumed:
        raise ValueError('asset_not_consumed')
    for entry in entries.values():
        data = entry['inputPath'].read_bytes()
        if data.startswith(b'\x89PNG\r\n\x1a\n'):
            fmt = 'png'
        elif data.startswith(b'\xff\xd8'):
            fmt = 'jpg'
        else:
            if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
                raise ValueError('asset_svg_external_dependency')
            try:
                xml = ET.fromstring(data)
            except ET.ParseError:
                raise ValueError('asset_format_unsupported') from None
            if xml.tag.split('}')[-1] != 'svg':
                raise ValueError('asset_format_unsupported')
            for node in xml.iter():
                if node.tag.split('}')[-1] in ('script', 'foreignObject'):
                    raise ValueError('asset_svg_external_dependency')
                for key, value in node.attrib.items():
                    if key.split('}')[-1] in ('href', 'src') and value and not value.startswith('#'):
                        raise ValueError('asset_svg_external_dependency')
                styles = ' '.join(node.attrib.values()) + (node.text or '')
                if '@import' in styles or any(not match.strip().strip('\"\'').startswith('#') for match in re.findall(r'url\(([^)]*)\)', styles)):
                    raise ValueError('asset_svg_external_dependency')
            fmt = 'svg'
        entry['format'] = fmt
    return entries


def collect(entries, root):
    assets = {}
    for name, entry in entries.items():
        source = entry['inputPath']
        if sha(source) != entry['sha256']:
            raise ValueError('asset_digest_mismatch')
        target = Path(root) / 'Assets' / (name + '.' + entry['format'])
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(source, target)
        if sha(target) != entry['sha256'] or sha(source) != entry['sha256']:
            raise ValueError('asset_digest_mismatch')
        assets[name] = {k: v for k, v in entry.items() if k not in ('inputPath', 'path')}
        assets[name]['path'] = str(target.relative_to(root))
    return assets
