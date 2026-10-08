#!/usr/bin/env python3
"""分层索引既有证据；只复用依赖未变化的结论，不提升 NOT_RUN 或 SKIP。"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEVELS={'static','local-tests','native-candidate','fixed-install','host-load','gui','model','command-execution'}
STATUSES={'PASS','FAIL','SKIP','NOT_RUN'}


def safe_file(root, value):
    """只接受仓内普通相对文件；父目录链接也不允许。"""
    if not isinstance(value,str) or not value or '\\' in value or Path(value).is_absolute() or any(p in ('', '.', '..') for p in value.split('/')):
        raise ValueError('invalid_evidence_path')
    path=root/value
    if any(p.is_symlink() for p in [path,*path.parents] if p.is_relative_to(root)) or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('invalid_evidence_path')
    return path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(root, path, level, status, dependencies, scope, requirement=None, tasks=(), historical=False):
    """登记报告与输入摘要；证据层级必须由调用方明确声明。"""
    if level not in LEVELS: raise ValueError('invalid_evidence_level')
    if status not in STATUSES or not scope: raise ValueError('invalid_evidence_status_or_scope')
    report=safe_file(root,path)
    if report.suffix=='.json':
        data=json.loads(report.read_text())
        observed=data.get('result',data.get('status','')).upper()
        observed={'PASSED':'PASS','FAILED':'FAIL','SKIPPED':'SKIP'}.get(observed,observed)
        if observed and observed!=status: raise ValueError('evidence_status_mismatch')
    return {'path':path,'sha256':sha(report),'level':level,'status':status,'scope':scope,
            'requirement':requirement,'tasks':list(tasks),'historical':historical,
            'dependencies':{p:sha(safe_file(root,p)) for p in dependencies}}


def verify(root, entry):
    """依赖或报告内容失配即过期；不根据文件名判定通过。"""
    if entry.get('level') not in LEVELS or entry.get('status') not in STATUSES:
        raise ValueError('invalid_evidence_record')
    stale=[]
    for path, expected in {entry['path']:entry['sha256'],**entry['dependencies']}.items():
        try:
            if sha(safe_file(root,path))!=expected: stale.append(path)
        except ValueError:
            stale.append(path)
    return {'path':entry['path'],'state':'stale' if stale else 'historical' if entry.get('historical') else 'current',
            'status':entry['status'],'level':entry['level'],'staleDependencies':stale,'scope':entry['scope']}


def bound_report(root,path,level,scope,requirement=None,tasks=()):
    """读取执行时登记的摘要，不重新采样当前文件来洗白旧结论。"""
    data=json.loads(safe_file(root,path).read_text())
    dependencies=data.get('fingerprints',{})
    if not dependencies:raise ValueError('missing_execution_fingerprints')
    entry=record(root,path,level,'PASS',[],scope,requirement,tasks)
    entry['dependencies']=dependencies
    for name,digest in dependencies.items():
        safe_file(root,name)
        if not isinstance(digest,str) or len(digest)!=64:raise ValueError('invalid_execution_fingerprint')
    return entry


def build(root=ROOT):
    """将当前固定安装与历史报告并列索引，不声称本轮重新执行。"""
    current='docs/evidence/craft-vector37-gateway-export-fixed-first-use-20261008.json'
    historical='docs/evidence/craft-full-command-fixed-first-use-20261007.json'
    observed=json.loads(safe_file(root,current).read_text())['hostLock']['plugins']['vectorcraft']
    plugin=json.loads(safe_file(root,'plugin.json').read_text())
    source=json.loads(safe_file(root,'skills.lock.json').read_text())['sources'][0]
    matching=(observed['version']==plugin['version'] and observed['skillSourceSha']==source['sha']
              and observed['skillSourceRef']==source['ref'] and observed['skills']==source['sha256']
              and observed['pluginManifestSha256']==sha(safe_file(root,'plugin.json')))
    entries=[
                record(root,current,'fixed-install','PASS',['skills.lock.json','plugin.json'] if matching else [],'published plugin37/source33; 13 standalone cold starts and two brand export routes; retained historical proof, not newly run', 'VC-DM-006',['4.30'],historical=not matching),
                record(root,historical,'host-load','PASS',[],'historical 58-skill matrix; does not describe later 64-skill inventories or this source candidate', historical=True),
                record(root,'docs/evidence/craft-fixed64-every-skill-cold-first-use-20261007.json','fixed-install','PASS',[],'64-skill cold matrix at its recorded versions (vectorcraft plugin30); not latest plugin37 or source34 acceptance', historical=True)]
    local='docs/evidence/vectorcraft-optimization-local-20261008.json'
    candidate_current=True
    if (root/local).is_file():
        candidate=json.loads(safe_file(root,local).read_text())
        old_version=candidate.get('fixedPluginVersion',candidate.get('pluginFixedVersion'))
        candidate_current=(old_version==plugin['version'])
        if candidate_current:
            entries.append(bound_report(root,local,'local-tests','current plugin Harness and review tests; source candidate code checked in its independent repository','VC-AR-003',['9.13','9.14','9.15']))
            entries.append(bound_report(root,'docs/evidence/vectorcraft-optimization-single-round-native-20261008.json','native-candidate','supplied receipt and native brand revision; not full sections3/6 acceptance','VC-QA-003'))
        else:
            for path,level in [(local,'local-tests'),('docs/evidence/vectorcraft-optimization-single-round-native-20261008.json','native-candidate')]:
                entries.append(record(root,path,level,'PASS',[],'pre-release candidate at its recorded version; execution fingerprints retained in report; not acceptance of this release',historical=True))
    control='docs/evidence/vectorcraft-execution-control-20261008.json'
    if (root/control).is_file():
        if candidate_current:
            entries.append(bound_report(root,control,'native-candidate','owned process supervision, readonly original-file recovery, cancellation epoch fence; full task acceptance remains open','VC-TX-003',['3.1','3.2','3.4','3.5','3.7','3.8']))
        else:
            entries.append(record(root,control,'native-candidate','PASS',[],'pre-release execution control at its original fingerprints; fixed release acceptance remains separate','VC-TX-003',['3.1','3.2','3.4','3.5','3.7','3.8'],historical=True))
    fixed='docs/evidence/vectorcraft-fixed38-optimization-20261008.json'
    if (root/fixed).is_file():
        proof=json.loads(safe_file(root,fixed).read_text())
        if proof['pluginVersion']==plugin['version'] and proof['sourceCommit']==source['sha']:
            entries.append(bound_report(root,fixed,'fixed-install','actual isolated host installation, 13 cold starts and protocol/brand technical tasks only',tasks=['9.3','9.6']))
        else:
            entries.append(record(root,fixed,'fixed-install','PASS',[],'fixed plugin38/source35; retained at original execution identity',tasks=['9.3','9.6'],historical=True))
    quality='docs/evidence/vectorcraft-technical-quality-candidate-20261008.json'
    if (root/quality).is_file():
        entries.append(bound_report(root,quality,'native-candidate','standalone technical decoder and negative tests at their recorded identity; coordinator evidence is separate and complete native engineering acceptance remains open',tasks=['6.1']))
    previous='docs/evidence/vectorcraft-optimization-local-before-execution-control-20261008.json'
    checked='docs/evidence/vectorcraft-checked-review-candidate-20261008.json'
    if (root/checked).is_file():
        entries.append(bound_report(root,checked,'native-candidate','persisted decoder checks of existing native export copies; fixture receipts only; native reopening and real creative acceptance remain open',tasks=['6.2']))
    cycle='docs/evidence/vectorcraft-revision-cycle-candidate-20261008.json'
    if (root/cycle).is_file():
        entries.append(bound_report(root,cycle,'native-candidate','bounded revision minimum: two actual native color revisions with injected scores; full6.6 and real creative acceptance remain open',tasks=['6.4','6.5']))
    geometry='docs/evidence/vectorcraft-geometry-candidate-20261008.json'
    if (root/geometry).is_file():
        entries.append(bound_report(root,geometry,'native-candidate','explicit units, offset artboard controls and retained closure failure; full4.3 remains open','VC-DM-001',['4.1','4.2']))
    boolean='docs/evidence/vectorcraft-boolean-transactions-source-candidate-20261008.json'
    if (root/boolean).is_file():
        entries.append(bound_report(root,boolean,'native-candidate','source37 candidate at recorded commit is consumed by plugin41; full4.6 remains open','VC-DM-002',['4.4','4.5']))
    managed='docs/evidence/vectorcraft-managed-boolean-pinned37-20261008.json'
    if (root/managed).is_file():
        entries.append(bound_report(root,managed,'native-candidate','actual supplied pinned source37 in Harness; structure scope checks; not host installation or full4.6','VC-DM-002'))
    for old in ['vectorcraft-geometry-before-source37-20261008.json','vectorcraft-revision-cycle-before-source37-20261008.json','vectorcraft-boolean-transactions-before-source37-20261008.json']:
        if (root/'docs/evidence'/old).is_file():
            entries.append(record(root,'docs/evidence/'+old,'native-candidate','PASS',[],'source36 or earlier independent candidate at original execution identity; not rebound',historical=True))
    fixed41='docs/evidence/vectorcraft-fixed41-structural-20261008.json'
    if (root/fixed41).is_file():
        data=json.loads(safe_file(root,fixed41).read_text())
        if data['pluginVersion']==plugin['version'] and data['sourceCommit']==source['sha']:
            entries.append(bound_report(root,fixed41,'fixed-install','13 actual installed cold skills,12 declared create/revise pairs and8 managed structural cases; full4.6 and model/GUI/creative gates remain open','VC-DM-002'))
        else:
            entries.append(record(root,fixed41,'fixed-install','PASS',[],'plugin41/source37 installed structural proof at original execution identity',historical=True))
    old_cycle='docs/evidence/vectorcraft-revision-cycle-before-geometry-20261008.json'
    if (root/old_cycle).is_file():
        entries.append(record(root,old_cycle,'native-candidate','PASS',[],'original pre-geometry execution fingerprints preserved; not rebound',historical=True))
    old_checked='docs/evidence/vectorcraft-checked-review-before-cycles-20261008.json'
    if (root/old_checked).is_file():
        entries.append(record(root,old_checked,'native-candidate','PASS',[],'original pre-cycle review coordinator proof; execution fingerprints preserved, not rebound',historical=True))
    if (root/previous).is_file():
        entries.append(record(root,previous,'local-tests','PASS',[],'original execution fingerprints retained inside historical report; never rebound to changed source',historical=True))
    runtime_gate='docs/evidence/vectorcraft-runtime-gate-candidate-20261008.json'
    if (root/runtime_gate).is_file():
        entries.append(bound_report(root,runtime_gate,'native-candidate','live 585-command and25-tool headless probe, drain guard and managed native creation; different-version upgrades, rollback and desktop acceptance remain open','VC-RT-002',['2.4']))
    runtime_default='docs/evidence/vectorcraft-runtime-default-candidate-20261008.json'
    if (root/runtime_default).is_file():
        entries.append(bound_report(root,runtime_default,'native-candidate','default cold fixed install and headless schemas, parallel creation, readonly resume, pre-edit refusal and8 managed structural cases; complete2.6 remains open','VC-RT-002',['2.5']))
    runtime_artifacts='docs/evidence/vectorcraft-runtime-default-artifacts-candidate-20261008.json'
    if (root/runtime_artifacts).is_file():
        entries.append(bound_report(root,runtime_artifacts,'native-candidate','fresh default headless cold/concurrent/refusal cases with all three delivery manifest and file digests; unchanged managed structural regression reused by exact fingerprints; full2.6 remains open','VC-RT-002',['2.5']))
    boundaries='docs/evidence/vectorcraft-runtime-boundaries-candidate-20261008.json'
    if (root/boundaries).is_file():
        entries.append(bound_report(root,boundaries,'native-candidate','Two real CLI versions,11 native cases, schema3 backup and old-reader refusal; complete2.6 remains open','VC-RT-002'))
    open_reader='docs/evidence/vectorcraft-open-reader-candidate-20261008.json'
    if (root/open_reader).is_file():
        entries.append(bound_report(root,open_reader,'native-candidate','Candidate database guard with open-reader red, WAL preservation and native/race/default cases; full2.6 awaits fixed43','VC-RT-002'))
    upgrade='docs/evidence/vectorcraft-runtime-upgrade-fixed43-20261008.json'
    if (root/upgrade).is_file():
        entries.append(bound_report(root,upgrade,'fixed-install','Public plugin43/source37; all seven RT-002 scenarios including real bridge/version drain and open-reader budget rollback on macOS arm64; complete V1 remains open','VC-RT-002',['2.6']))
    authorization='docs/evidence/vectorcraft-authorization-snapshot-local44-20261008.json'
    if (root/authorization).is_file():
        entries.append(bound_report(root,authorization,'local-tests','Three synthetic coordinator authorization regressions; 57 Node and43 Python tests; full3.3 and V1 remain open','VC-TX-001'))
    authorization_fixed='docs/evidence/vectorcraft-authorization-fixed44-20261008.json'
    if (root/authorization_fixed).is_file():
        entries.append(bound_report(root,authorization_fixed,'fixed-install','Public plugin44/source37 installed in isolated Codex host; 13 unchanged enabled skills,57 Node and43 Python regressions; full3.3 remains open','VC-TX-001'))
    recovery_candidate='docs/evidence/vectorcraft-recovery-binding-candidate45-20261008.json'
    if (root/recovery_candidate).is_file():
        entries.append(bound_report(root,recovery_candidate,'native-candidate','Recovery snapshot refusals and real coordinator crash/restart/native group stop/handoff; full3.3,3.6,3.9 and V1 remain open','VC-TX-002'))
    recovery_fixed='docs/evidence/vectorcraft-recovery-fixed45-20261008.json'
    if (root/recovery_fixed).is_file():
        entries.append(bound_report(root,recovery_fixed,'fixed-install','Public plugin45/source37 installed host and real cancellation/crash recovery subset; 13 unchanged skills,63 Node and43 Python regressions; full3.3,3.6,3.9 remain open','VC-TX-002'))
    writer_candidate='docs/evidence/vectorcraft-single-writer-candidate46-20261008.json'
    if (root/writer_candidate).is_file():
        entries.append(bound_report(root,writer_candidate,'native-candidate','Seven VC-TX-001 candidate scenarios with immutable native branches, signed GUI conflict and real crash/handoff; fixed46 acceptance remains separate','VC-TX-001'))
    writer_fixed='docs/evidence/vectorcraft-single-writer-fixed46-20261008.json'
    if (root/writer_fixed).is_file():
        entries.append(bound_report(root,writer_fixed,'fixed-install','Recorded installed plugin46 native single-writer cases; physical root replacement not covered, so full3.3 remains open; 75 Node and43 Python tests','VC-TX-001'))
    writer47_candidate='docs/evidence/vectorcraft-single-writer-candidate47-20261008.json'
    if (root/writer47_candidate).is_file():
        entries.append(bound_report(root,writer47_candidate,'native-candidate','VC-TX-001 candidate including physical namespace replacement,77 Node and43 Python tests; fixed47 remains separate','VC-TX-001'))
    writer47_fixed='docs/evidence/vectorcraft-single-writer-fixed47-20261008.json'
    if (root/writer47_fixed).is_file():
        entries.append(bound_report(root,writer47_fixed,'fixed-install','All seven VC-TX-001 scenarios including physical namespace replacement at public installed plugin47/source37 on macOS arm64; 77 Node and43 Python tests','VC-TX-001',['3.3']))
    recovery48='docs/evidence/vectorcraft-source-recovery-candidate48-20261008.json'
    if (root/recovery48).is_file():
        entries.append(bound_report(root,recovery48,'native-candidate','Source snapshot gate, actual post-save receipt loss and readonly original-output recovery;84 Node and43 Python tests; full3.6 remains open','VC-TX-002'))
    source_recovery_fixed='docs/evidence/vectorcraft-source-recovery-fixed48-20261008.json'
    if (root/source_recovery_fixed).is_file():
        entries.append(bound_report(root,source_recovery_fixed,'fixed-install','Public plugin48/source37 actual host installation, source snapshot refusal and post-save receipt loss;84 Node and43 Python tests; complete3.6 remains open','VC-TX-002'))
    linked_recovery='docs/evidence/vectorcraft-linked-recovery-fixed48-20261009.json'
    if (root/linked_recovery).is_file():
        entries.append(bound_report(root,linked_recovery,'fixed-install','External current QA against installed public plugin48/source37: original-stage nonempty linked dependency missing/modified refusal and post-inspection mutation refusal;15 recovery regressions; full3.6 remains open','VC-TX-002'))
    receipt_recovery='docs/evidence/vectorcraft-receipt-recovery-candidate49-20261009.json'
    if (root/receipt_recovery).is_file():
        entries.append(bound_report(root,receipt_recovery,'native-candidate','Receipt/manifest/artifact and post-inspection receipt binding; actual prepared directory identity for plain/linked before/after receipt crashes;97 Node and43 Python tests; full3.6 remains open','VC-TX-002'))
    receipt_fixed='docs/evidence/vectorcraft-receipt-recovery-fixed49-20261009.json'
    if (root/receipt_fixed).is_file():
        entries.append(bound_report(root,receipt_fixed,'fixed-install','Public installed plugin49/source38: four plain/linked crashes before/after receipt, receipt/artifact and post-inspection binding refusal;97 Node and43 Python tests; full3.6 remains open','VC-TX-002'))
    launch='docs/evidence/vectorcraft-launch-recovery-candidate50-20261009.json'
    if (root/launch).is_file():
        entries.append(bound_report(root,launch,'native-candidate','Six real GO-boundary crashes, source readonly inspection and post-inspection change refusal; four receipt regressions;109 Node and43 Python tests; fixed50 and full3.6 remain open','VC-TX-002'))
    task_recovery='docs/evidence/vectorcraft-task-recovery-fixed50-20261009.json'
    if (root/task_recovery).is_file():
        entries.append(bound_report(root,task_recovery,'fixed-install','All seven current VC-TX-002 scenarios in public installed50/source38 macOS arm64;13 actual cases,109 Node and43 Python tests,13 unchanged skills and30 stopped groups; only3.6 closes','VC-TX-002',['3.6']))
    budget_cancel='docs/evidence/vectorcraft-budget-cancel-candidate51-20261009.json'
    if (root/budget_cancel).is_file():
        entries.append(bound_report(root,budget_cancel,'native-candidate','Five real native cases: shared cancellation, original deadline restart, actual completed late receipt, shared attempt/reserved-byte denial;115 Node and43 Python tests; fixed51 and full3.9 remain open','VC-TX-003'))
    budget_fixed='docs/evidence/vectorcraft-budget-cancel-fixed51-20261009.json'
    if (root/budget_fixed).is_file():
        entries.append(bound_report(root,budget_fixed,'fixed-install','All five current VC-TX-003 scenarios on public installed51/source38 macOS arm64;five native cases,115 Node and43 Python tests,13 unchanged skills and13 stopped groups;only3.9 closes','VC-TX-003',['3.9']))
    geometry_fixed='docs/evidence/vectorcraft-geometry-fixed51-20261009.json'
    if (root/geometry_fixed).is_file():
        entries.append(bound_report(root,geometry_fixed,'fixed-install','All two current VC-DM-001 scenarios against installed public51/source38 macOS arm64;external QA driver,six native cases,18 exports,seven geometry tests,13 unchanged skills and6 stopped groups;only4.3 closes','VC-DM-001',['4.3']))
    boolean_fixed='docs/evidence/vectorcraft-boolean-fixed51-20261009.json'
    if (root/boolean_fixed).is_file():
        entries.append(bound_report(root,boolean_fixed,'fixed-install','All four current VC-DM-002 scenarios against installed public51/source38 macOS arm64;24 native workflow/Harness/SDK cases,17 source unit tests,13 unchanged skills and9 stopped registered groups;explicit failure injection;only4.6 closes','VC-DM-002',['4.6']))
    brand_text='docs/evidence/vectorcraft-brand-text-fixed53-20261009.json'
    if (root/brand_text).is_file():
        entries.append(bound_report(root,brand_text,'fixed-install','All four current VC-DM-003 scenarios on public installed53/source39 macOS arm64; explicit brand faults, same-RGB nonconsumers, Chinese revision/reopen and native SVG modes; only4.7/4.8/4.9 close','VC-DM-003',['4.7','4.8','4.9']))
    artboard_mapping='docs/evidence/vectorcraft-artboard-mapping-candidate54-20261009.json'
    if (root/artboard_mapping).is_file():
        entries.append(bound_report(root,artboard_mapping,'native-candidate','Source40 stable artboard-ID mapping and native receipt binding, three successful mappings/four refusals;9 mapping tests,49 Python and115 Node regressions;minimum4.10/4.11 only, complete4.12 remains open','VC-DM-004',['4.10','4.11']))
    artboard_mapping_fixed='docs/evidence/vectorcraft-artboard-mapping-fixed54-20261009.json'
    if (root/artboard_mapping_fixed).is_file():
        entries.append(bound_report(root,artboard_mapping_fixed,'fixed-install','Actual public54/source40 isolated host installation, three successful native mappings/four refusals/14 decoded outputs;13 skills unchanged;complete4.12 remains open','VC-DM-004'))
    artboards='docs/evidence/vectorcraft-artboards-fixed54-20261009.json'
    if (root/artboards).is_file():
        entries.append(bound_report(root,artboards,'fixed-install','All four current VC-DM-004 scenarios on installed54/source40 macOS arm64;31 native boundary cases, standalone export cold first use, stable-ID mapping and pinned renderer unknown-bounds semantics;only4.12 closes','VC-DM-004',['4.12']))
    exchange='docs/evidence/vectorcraft-exchange-candidate55-20261009.json'
    if (root/exchange).is_file():
        entries.append(bound_report(root,exchange,'native-candidate','Source41 raster scope and plugin55 technical disclosure guard; fixed54 gap, three native reopen/nine decode/four explicit disclosure refusals;minimum4.13/4.14 only,4.15 remains open','VC-DM-005',['4.13','4.14']))
    automatic='docs/evidence/vectorcraft-exchange-automatic55-20261009.json'
    if (root/automatic).is_file():
        entries.append(bound_report(root,automatic,'fixed-install','Installed55 automatic freeform SVG fallback, independent native edit preservation, three export decodes and seven refusals; supplementary scope,4.15 formal closure pending','VC-DM-005'))
    exchange_fixed='docs/evidence/vectorcraft-exchange-fixed55-20261009.json'
    if (root/exchange_fixed).is_file():
        entries.append(bound_report(root,exchange_fixed,'fixed-install','Actual public55/source41 installation/discovery and installed-copy three native reopen/nine decode/four disclosure refusals;13 skills unchanged;explicit expansion only,complete4.15 remains open','VC-DM-005'))
    # 明确归档变更前执行字节；保留报告原摘要，不能把旧运行重绑定到新实现。
    for entry in entries:
        archived={}
        for name,digest in entry['dependencies'].items():
            if sha(safe_file(root,name))==digest:continue
            for prefix in ['docs/evidence/pre-runtime-gate-identity/','docs/evidence/pre-runtime-default-identity/','docs/evidence/pre-runtime-artifacts-identity/','docs/evidence/pre-runtime-boundaries-identity/','docs/evidence/pre-open-reader-identity/','docs/evidence/pre-download-test-cache-identity/','docs/evidence/pre-authorization-identity/','docs/evidence/pre-recovery-binding-identity/','docs/evidence/pre-source-dependencies-identity/','docs/evidence/pre-task3-closure-identity/','docs/evidence/pre-path-identity/','docs/evidence/pre-source-recovery-identity/','docs/evidence/pre-receipt-recovery-identity/','docs/evidence/pre-launch-recovery-identity/','docs/evidence/pre-task3-6-closure-identity/','docs/evidence/pre-budget-cancel-identity/','docs/evidence/pre-budget-cancel-closure-identity/','docs/evidence/pre-brand-text-identity/','docs/evidence/pre-artboard-mapping-identity/','docs/evidence/pre-exchange-identity/']:
                old=prefix+name
                if (root/old).is_file() and sha(safe_file(root,old))==digest:
                    archived[name]=old
                    break
        if archived:
            entry['dependencies']={archived.get(name,name):digest for name,digest in entry['dependencies'].items()}
            entry['historical']=True
            entry['scope']='historical at original execution identity; '+entry['scope']
    return {'schema':'vectorcraft-evidence-index/v1',
            'identitySha256':sha(safe_file(root,'docs/current-identity.json')),
            'entries':entries,
            'commandAcceptance':'Use version-bound command catalog executionAcceptance; directory discovery never promotes NOT_RUN',
            'excluded':['complete V1','all commands','all GUI','model dispatch','source candidate fixed-install acceptance']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    path=ROOT/'docs/evidence-index.json'
    data=build()
    if args.check:
        if not path.is_file() or json.loads(path.read_text())!=data: raise SystemExit('evidence_index_drift')
        if any(verify(ROOT,entry)['state']=='stale' for entry in data['entries']): raise SystemExit('stale_evidence')
    else:
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'result':'PASS','scope':'evidence integrity only; original levels preserved','entries':len(data['entries'])}))
