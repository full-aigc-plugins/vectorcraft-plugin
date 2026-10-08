"""从原生对象而非 RGB 相等性核验色板依赖更新。"""
import hashlib
import json


def snapshot(document):
    """提取对象自身属性；容器子对象独立编号，保留原有子对象顺序。"""
    if not isinstance(document, dict) or not isinstance(document.get('layers'), list) or not isinstance(document.get('artboards'), list):
        raise ValueError('invalid_brand_snapshot')
    result = {}

    def visit(obj):
        if not isinstance(obj, dict) or type(obj.get('id')) is not int or obj['id'] <= 0 or not isinstance(obj.get('kind'), dict) or obj['id'] in result:
            raise ValueError('invalid_brand_snapshot')
        kind = obj['kind']
        own = {**obj, 'kind': {key: value for key, value in kind.items() if key != 'children'}}
        if 'children' in kind:
            if not isinstance(kind['children'], list):
                raise ValueError('invalid_brand_snapshot')
            own['kind']['children'] = [child.get('id') if isinstance(child, dict) else None for child in kind['children']]
        result[obj['id']] = own
        for child in kind.get('children', []):
            visit(child)

    for obj in document['layers']:
        visit(obj)
    return result


def uses_token(value, token):
    """仅原生显式 swatch 引用构成消费关系，颜色相同不构成依赖。"""
    if isinstance(value, dict):
        return value.get('swatch') == token or any(uses_token(child, token) for child in value.values())
    if isinstance(value, list):
        return any(uses_token(child, token) for child in value)
    return False


def inspect_update(before, after, token):
    """返回依赖检查报告；未知模型拒绝检查，不伪造成功结论。"""
    if not isinstance(token, str) or not token:
        raise ValueError('invalid_brand_token')
    original, updated = snapshot(before), snapshot(after)
    consumers = {key for key, value in original.items() if uses_token(value, token)}
    # 子对象增删会同时改变父容器的顺序引用，报告实际对象和受影响容器。
    affected = set(original) ^ set(updated)
    shared = set(original) & set(updated)
    changed = {key for key in shared - consumers if original[key] != updated[key]}
    structural = {key for key in shared if original[key]['kind'].get('children') != updated[key]['kind'].get('children')}
    root_order_changed = [obj['id'] for obj in before['layers']] != [obj['id'] for obj in after['layers']]
    if root_order_changed:
        structural.update(obj['id'] for obj in before['layers'])
        structural.update(obj['id'] for obj in after['layers'])
    affected |= changed
    affected |= structural
    edges = [{'token': token, 'objectId': key,
              'reason': 'object_structure_changed' if key in structural else
                        'unbound_object_changed' if key in changed else 'object_identity_changed'}
             for key in sorted(affected)]
    artboards_changed = before['artboards'] != after['artboards']
    digest = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return {'schema': 'vectorcraft-brand-dependency-check/v1',
            'status': 'failed' if affected or artboards_changed else 'passed', 'token': token,
            'consumerIds': sorted(consumers), 'affectedObjectIds': sorted(affected),
            'unexpectedDependencies': edges, 'artboardsChanged': artboards_changed,
            'beforeSha256': digest(before), 'afterSha256': digest(after),
            'scope': 'native explicit swatch consumers; unbound own properties, identities and artboards'}
