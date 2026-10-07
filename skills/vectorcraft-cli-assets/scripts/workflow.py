#!/usr/bin/env python3
"""原生矢量计划执行器：临时工程内编辑，成功后发布新的交付目录。"""
import argparse
import sys
sys.dont_write_bytecode = True
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

def exchange_report(root,outputs,warnings):
    spec=importlib.util.spec_from_file_location('craft_exchange_loss',Path(__file__).with_name('exchange_loss.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.write_report(root,outputs,warnings)

ALLOWED = {'native.command', 
    'asset.place', 'asset.replace',
    'shape.rectangle', 'shape.ellipse', 'shape.polygon', 'shape.star', 'shape.line',
    'path.create', 'path.setAnchors', 'path.close', 'text.create', 'text.setText',
    'paint.setFill', 'paint.setStroke', 'select.set', 'select.none',
    'object.group', 'object.transform', 'object.pathfinder.unite',
    'object.pathfinder.minusFront', 'object.pathfinder.intersect', 'object.pathfinder.exclude',
    'artboard.new', 'artboard.setProps',
    'swatch.new', 'swatch.edit', 'swatch.list',
}


def asset_module():
    spec = importlib.util.spec_from_file_location('craft_asset_inputs', Path(__file__).with_name('asset_inputs.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inputs_name(value):
    return isinstance(value, str) and bool(asset_module().NAME.fullmatch(value))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def pdf_export_date(native, source=None, prior=None):
    """PDF 日期绑定原生创建时间；旧记录缺少该时间时保留首次交付时间。"""
    valid = lambda value: type(value) is int and -(2**63) <= value < 2**63
    created = native.get('metadata', {}).get('created')
    if created is not None and not valid(created):
        raise ValueError('invalid_native_pdf_created')
    if source:
        record = Path(source) / 'pdf-export-date.json'
        if record.exists() or record.is_symlink() or record.name in (prior or {}).get('files', {}):
            if record.is_symlink() or not record.is_file() or sha(record) != (prior or {}).get('files', {}).get(record.name):
                raise ValueError('pdf_date_digest_mismatch')
            previous = json.loads(record.read_text())
            if (previous.get('schema') != 'vectorcraft-pdf-date/v1' or not valid(previous.get('created'))
                    or previous.get('binding') not in ('native-document-created', 'initial-delivery-time')):
                raise ValueError('invalid_pdf_date_record')
            if previous['binding'] == 'native-document-created' and previous['created'] != created:
                raise ValueError('pdf_date_binding_mismatch')
            return previous
    return {'schema': 'vectorcraft-pdf-date/v1', 'created': created if created is not None else int(time.time()),
            'binding': 'native-document-created' if created is not None else 'initial-delivery-time'}


def resolve(value, bindings):
    if isinstance(value, dict):
        if set(value) == {'$ref'}:
            try:
                parts = value['$ref'].split('.')
                result = bindings[parts[0]]
                for field in parts[1:]:
                    result = result[int(field)] if isinstance(result, list) else result[field]
                return result
            except (KeyError, IndexError, TypeError, ValueError, AttributeError):
                raise ValueError('unresolved_reference: ' + str(value['$ref'])) from None
        return {key: resolve(item, bindings) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve(item, bindings) for item in value]
    return value


def native_module():
    spec = importlib.util.spec_from_file_location('craft_native_workflow', Path(__file__).with_name('native_workflow.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def validate(plan):
    if not isinstance(plan, dict) or not isinstance(plan.get('operations'), list):
        raise ValueError('operations_required')
    aliases = set()
    for operation in plan['operations']:
        if operation.get('command') == 'native.command':
            native_module().validate(operation.get('params'))
        if operation.get('command') not in ALLOWED:
            raise ValueError('unsupported_command: ' + str(operation.get('command')))
        alias = operation.get('as')
        if alias is not None:
            if alias in aliases:
                raise ValueError('duplicate_alias: ' + alias)
            if not isinstance(alias, str) or not re.fullmatch(r'[a-zA-Z][\w-]*', alias):
                raise ValueError('invalid_alias')
            aliases.add(alias)
        if not isinstance(operation.get('params', {}), dict):
            raise ValueError('invalid_params')
        if operation['command'] in ('asset.place', 'asset.replace'):
            asset_module().validate_operation(operation['command'], operation.get('params', {}))
        if operation['command'] == 'text.setText':
            params = operation.get('params', {})
            valid_ref = lambda value: isinstance(value, dict) and set(value) == {'$ref'} and isinstance(value['$ref'], str) and bool(value['$ref'])
            valid_id = lambda value: (type(value) is int and value > 0) or valid_ref(value)
            # 禁止沿用隐式选择，整段替换只保留原生首段样式。
            if set(params) - {'id', 'ids', 'text'} or not isinstance(params.get('text'), str) or ('id' in params) == ('ids' in params):
                raise ValueError('invalid_text_edit: explicit id or ids and string text required')
            if 'id' in params:
                valid = valid_id(params['id'])
            else:
                ids = params['ids']
                valid = valid_ref(ids) or (isinstance(ids, list) and bool(ids) and all(valid_id(value) for value in ids))
            if not valid:
                raise ValueError('invalid_text_edit: invalid target')
    seen = set()
    for output in plan.get('exports', []):
        fmt, artboard = output.get('format'), output.get('artboard', 0)
        if fmt not in ('svg', 'png', 'pdf') or type(artboard) is not int or artboard < 0:
            raise ValueError('invalid_export')
        if (fmt, artboard) in seen:
            raise ValueError('duplicate_export')
        seen.add((fmt, artboard))
    if 'document' in plan:
        document = plan['document']
        if set(document) - {'name', 'width', 'height', 'units'}:
            raise ValueError('unsupported_document_setting')
        if document.get('units', 'Pixels') not in ('Pixels', 'Points'):
            raise ValueError('unsupported_document_units')
        for key in ('width', 'height'):
            if type(document.get(key)) not in (int, float) or not 0 < document[key] <= 16384:
                raise ValueError('invalid_document_size')


def execute(plan, output, runtime_home=None, source=None):
    validate(plan)
    output = Path(output).absolute()
    output = output.parent.resolve()/output.name
    if output.exists() or output.is_symlink():
        raise ValueError('output_exists; choose a new revision directory')
    source_project = None
    bindings = {}
    source_hash = None
    prior = {}
    if source:
        source = Path(source).resolve()
        source_project = source / 'project.vectorcraft'
        if source_project.is_symlink():
            raise ValueError('invalid_source_path')
        prior = json.loads((source / 'manifest.json').read_text())
        source_hash = sha(source_project)
        if source_hash != prior['files']['project.vectorcraft'] or source_hash != plan.get('expectedProjectSha256'):
            raise ValueError('revision_conflict')
        if 'document' in plan:
            raise ValueError('revision_cannot_recreate_document')
        bindings = prior['bindings']
        # 全局色板修改默认沿用已核验的变体导出清单。
        if 'exports' not in plan and any(op['command'] == 'swatch.edit' for op in plan['operations']):
            source_plan = source / 'plan.json'
            if source_plan.is_symlink() or not source_plan.is_file() or sha(source_plan) != prior['files'].get('plan.json'):
                raise ValueError('brand_source_plan_digest_mismatch')
            previous = json.loads(source_plan.read_text())
            plan = {**plan, 'exports': previous.get('exports', [])}
            validate(plan)
    elif 'document' not in plan:
        raise ValueError('document_required')
    inputs_module = asset_module()
    input_assets = inputs_module.preflight(plan, source, prior)
    # 安装器与本脚本同目录，单技能安装不需要访问其他包。
    spec = importlib.util.spec_from_file_location('craft_bootstrap', Path(__file__).with_name('bootstrap.py'))
    bootstrap = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bootstrap)
    lock = json.loads(Path(__file__).with_name('runtime.lock.json').read_text())
    installed = bootstrap.install(lock, runtime_home or os.environ.get('CRAFT_RUNTIME_HOME', str(Path.home() / '.local/share/craft-runtimes')))
    cli = installed['executable']
    catalog = json.loads(subprocess.check_output([cli, 'commands'], text=True, timeout=30))
    available = {entry['id'] for entry in catalog}
    required = {entry['params']['command'] if entry['command']=='native.command' else entry['command'] for entry in plan['operations']} - {'asset.place', 'asset.replace'} | {'text.fonts'}
    if input_assets:
        required |= {'file.place', 'links.relink', 'links.embed', 'links.placementOptions', 'links.list', 'links.check', 'file.package'}
    if required - available:
        raise ValueError('capability_missing: ' + ','.join(sorted(required - available)))
    output.parent.mkdir(parents=True, exist_ok=True)
    session_spec = importlib.util.spec_from_file_location('craft_mcp', Path(__file__).with_name('mcp_session.py'))
    session_module = importlib.util.module_from_spec(session_spec)
    session_spec.loader.exec_module(session_module)
    recovery_spec = importlib.util.spec_from_file_location('craft_recovery', Path(__file__).with_name('preserved_stage.py'))
    recovery_module = importlib.util.module_from_spec(recovery_spec)
    recovery_spec.loader.exec_module(recovery_module)
    recovery_state = {}
    guard_spec = importlib.util.spec_from_file_location('craft_output_guard', Path(__file__).with_name('output_guard.py'))
    guard_module = importlib.util.module_from_spec(guard_spec)
    guard_spec.loader.exec_module(guard_module)
    execution_identity = {'planHash': hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest(),
                         'inputHashes': {name: asset['sha256'] for name, asset in input_assets.items()},
                         'projectRevision': source_hash, 'runtimeSha256': installed['binarySha256']}
    with guard_module.claim(output, execution_identity), recovery_module.preserved_stage(output, '.vectorcraft-', recovery_state) as temporary, session_module.Session([cli, 'mcp', '--headless']) as session:
        stage = Path(temporary)
        project = stage / 'project.vectorcraft'
        assets = inputs_module.collect(input_assets, stage)
        receipts = []
        recovery_state['operations'] = receipts
        def command(identifier, params=None, save=True):
            recovery_state['lastAttempt'] = {'command': identifier, 'params': params or {}, 'phase': 'submitted'}
            value = session.command(identifier, params or {})
            recovery_state['lastAttempt']['phase'] = 'reply_received'
            receipts.append({'command': identifier, 'params': params or {}, 'result': value})
            return value
        if source_project:
            command('document.open', {'path': str(source_project)}, save=False)
            for entry in assets.values():
                if entry.get('linked'):
                    result = command('links.relink', {'ids': entry['ids'], 'path': str(stage / entry['path'])})
                    if result.get('notFound') or set(result.get('relinked', [])) != set(entry['ids']):
                        raise ValueError('asset_relink_failed')
        else:
            command('file.new', plan['document'])
        for operation in plan['operations']:
            params = resolve(operation.get('params', {}), bindings)
            if operation['command'] == 'native.command':
                value = native_module().execute(session, params, recovery_state, receipts, stage)
            elif operation['command'] == 'asset.place':
                entry = assets[params['asset']]
                value = command('file.place', {k: v for k, v in params.items() if k != 'asset'} | {'path': str(stage / entry['path'])})
                if 'linked' in entry and entry['linked'] != value['linked']:
                    raise ValueError('asset_mixed_link_modes')
                entry.update({'ids': entry.get('ids', []) + value['ids'], 'linked': value['linked'], 'warnings': value.get('warnings', [])})
            elif operation['command'] == 'asset.replace':
                old = assets[params['asset']]
                new = assets[params['replacement']]
                if old['format'] != 'svg' and new['format'] != 'svg':
                    command('links.placementOptions', {'ids': old['ids'], 'preserve': 'bounds'})
                    value = command('links.relink', {'ids': old['ids'], 'path': str(stage / new['path'])})
                    if value.get('notFound') or set(value.get('relinked', [])) != set(old['ids']):
                        raise ValueError('asset_relink_failed')
                    if not old['linked']:
                        command('links.embed', {'ids': old['ids']})
                    value = {'ids': old['ids'], 'linked': old['linked'], 'identity': 'retained'}
                else:
                    replaced = {};warnings = []
                    for old_id in old['ids']:
                        command('select.set', {'ids': [old_id]})
                        placed = command('file.place', {'path': str(stage / new['path']), 'replace': True, 'link': old['linked']})
                        replaced[old_id] = placed['ids'];warnings += placed.get('warnings', [])
                    value = {'ids': [i for ids in replaced.values() for i in ids], 'linked': placed['linked'], 'identity': 'replaced', 'warnings': warnings}
                    # 所有已登记实例分别保留位置；既有回执更新新身份。
                    for binding in bindings.values():
                        if isinstance(binding, dict) and isinstance(binding.get('ids'), list):
                            binding['ids'] = [i for old_id in binding['ids'] for i in replaced.get(old_id, [old_id])]
                new.update({'ids': value['ids'], 'linked': value['linked'], 'warnings': value.get('warnings', [])})
                assets[params['asset']] = new
                del assets[params['replacement']]
            else:
                value = command(operation['command'], params)
            if operation.get('as'):
                bindings[operation['as']] = value
        fonts = command('text.fonts', {}, save=False)
        if not isinstance(fonts, list) or any(not isinstance(font, dict) or type(font.get('missing')) is not bool for font in fonts):
            raise ValueError('invalid_font_dependencies')
        missing = [font for font in fonts if font['missing']]
        if missing:
            raise ValueError('missing_fonts: ' + json.dumps(missing, ensure_ascii=False))
        command('document.save', {'path': str(project)}, save=False)
        if assets:
            links = command('links.list')
            registered = {i for entry in assets.values() if entry['linked'] for i in entry['ids']}
            if any(row['linked'] and row['id'] not in registered for row in links['links']):
                raise ValueError('unregistered_dependency')
            if links['missing'] or links['modified']:
                raise ValueError('asset_link_invalid')
            packaged = command('file.package', {'folder': str(stage), 'name': 'delivery', 'report': False})
            if packaged['missingLinks']:
                raise ValueError('asset_collection_failed')
            delivery = stage / 'delivery'
            for entry in assets.values():
                filename = Path(entry['path']).name
                if entry['linked']:
                    collected = delivery / 'Links' / filename
                else:
                    collected = delivery / 'Assets' / filename
                    collected.parent.mkdir(exist_ok=True)
                    shutil.copyfile(stage / entry['path'], collected)
                if not collected.is_file() or sha(collected) != entry['sha256']:
                    raise ValueError('asset_collection_digest_mismatch')
                entry['path'] = str(collected.relative_to(delivery))
            # 原生 package 不修改原会话；所有导出改从收集后的工程进行。
            stage = delivery
            project = stage / 'project.vectorcraft'
            command('document.open', {'path': str(project)}, save=False)
        reopened = session_module.Session([cli, 'mcp', '--headless'])
        with reopened:
            reopened.command('document.open', {'path': str(project)})
            native = reopened.command('document.json', {})
            if assets:
                checked = reopened.command('links.check', {})
                if checked['missing'] or checked['modified']:
                    raise ValueError('asset_link_invalid')
        # 由独立会话重新打开工程取得模型；导出前检查真实画板范围。
        outputs = []
        pdf_date = pdf_export_date(native, source, prior if source else None) if any(item['format'] == 'pdf' for item in plan.get('exports', [])) else None
        if pdf_date:
            (stage / 'pdf-export-date.json').write_text(json.dumps(pdf_date, indent=2) + '\n')
        for item in plan.get('exports', []):
            index = item.get('artboard', 0)
            if index >= len(native['artboards']):
                raise ValueError('artboard_out_of_range')
            destination = stage / f'artboard-{index + 1}.{item["format"]}'
            params = {'path': str(destination), 'format': item['format'], 'artboard': index, 'artboards': [index]}
            if item['format'] == 'svg':
                params['artboardContentOnly'] = True
            if item['format'] == 'pdf':
                params['created'] = pdf_date['created']
            value = command('document.export', params, save=False)
            if not destination.is_file() or destination.stat().st_size == 0:
                raise ValueError('export_missing')
            outputs.append({'path': destination.name, 'artboardId': native['artboards'][index]['id'], 'warnings': value.get('warnings', []),
                            **({'isolationPolicy': 'native-paint-bounds; whole-dependent-containers-and-unknown-bounds-retained'} if item['format'] == 'svg' else {}),
                            **({'pdfCreated': pdf_date['created'], 'pdfDateBinding': pdf_date['binding']} if item['format'] == 'pdf' else {})})
        if source_project and sha(source_project) != source_hash:
            raise ValueError('revision_conflict')
        for entry in input_assets.values():
            if sha(entry['inputPath']) != entry['sha256']:
                raise ValueError('asset_digest_mismatch')
        # 不把暂存绝对路径写入可分发记录。
        for receipt in receipts:
            if receipt['command'] in ('document.export', 'document.save', 'document.open'):
                receipt['params']['path'] = Path(receipt['params']['path']).name
                if isinstance(receipt['result'], dict) and 'path' in receipt['result']:
                    receipt['result']['path'] = Path(receipt['result']['path']).name
        def portable(value):
            if isinstance(value, dict):
                return {k: portable(v) for k, v in value.items()}
            if isinstance(value, list):
                return [portable(v) for v in value]
            if isinstance(value, str):
                for name, entry in input_assets.items():
                    value = value.replace(str(entry['inputPath']), 'input:' + name)
                return value.replace(str(stage), '.').replace(str(temporary), '.').replace(str(source) if source else '\x00', 'source')
            return value
        saved_plan = {**plan, **({'assets': {name: {'path': entry['path'], 'sha256': entry['sha256']} for name, entry in assets.items()}} if assets else {})}
        (stage / 'native.json').write_text(json.dumps(portable(native), ensure_ascii=False, indent=2) + '\n')
        (stage / 'plan.json').write_text(json.dumps(portable(saved_plan), ensure_ascii=False, indent=2) + '\n')
        (stage / 'operations.json').write_text(json.dumps(portable(receipts), ensure_ascii=False, indent=2) + '\n')
        exchange_report(stage,[item['path'] for item in outputs],{item['path']:item['warnings'] for item in outputs})
        manifest = {'schema': 'vectorcraft-delivery/v1', 'sourceProjectSha256': source_hash,
                    'runtimeSha256': installed['binarySha256'], 'bindings': bindings, 'outputs': outputs, 'fontDependencies': fonts,
                    'assets': assets,
                    **({'collection': {'links': packaged['links'], 'fonts': packaged['fonts'], 'skippedFonts': packaged['skippedFonts']}} if assets else {}),
                    'files': {str(f.relative_to(stage)): sha(f) for f in stage.rglob('*') if f.is_file()},
                    'lossReport': {'path':'exchange-loss.json','sha256':sha(stage/'exchange-loss.json')}, 'acceptance': 'requires-domain-and-visual-review'}
        (stage / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        if output.exists() or output.is_symlink():
            raise ValueError('output_exists')
        stage.rename(output)
        return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--runtime-home', type=Path)
    parser.add_argument('--asset', action='append', default=[], metavar='NAME=PATH', help='登记输入素材并计算摘要')
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text())
        for assignment in args.asset:
            name, separator, path = assignment.partition('=')
            if not separator or not inputs_name(name) or name in plan.get('assets', {}):
                raise ValueError('asset_binding_invalid')
            plan.setdefault('assets', {})[name] = {'path': path, 'sha256': sha(path)}
        result = execute(plan, args.output, args.runtime_home, args.source)
        print(json.dumps(result, ensure_ascii=False))
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False))
        raise SystemExit(1)

if __name__ == '__main__':
    main()
