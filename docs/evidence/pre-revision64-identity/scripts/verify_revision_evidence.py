#!/usr/bin/env python3
"""逐场景核验固定63受限修订；注入QA回执只证明控制机制，不升级创作验收。"""
import builtins,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT='docs/evidence/vectorcraft-revision-fixed63-20261009.json'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def verify(root=ROOT):
 root=Path(root)
 def local(name):
  if not isinstance(name,str) or Path(name).is_absolute() or '\\' in name or any(p in ('','.','..') for p in name.split('/')):raise ValueError('revision_path')
  p=root/name
  if not p.is_file() or not p.resolve().is_relative_to(root.resolve()) or any(x.is_symlink() for x in [p,*p.parents] if x.is_relative_to(root)):raise ValueError('revision_path')
  return p
 r=json.loads(local(REPORT).read_text());index=json.loads((root/'docs/evidence-index.json').read_text()) if (root/'docs/evidence-index.json').is_file() else {'entries':[]};known=builtins.next((x['dependencies'] for x in index['entries'] if x['path']==REPORT),{})
 def bound(name):
  expected=r['fingerprints'][name];p=local(name)
  if sha(p)==expected:return p
  candidates=[n for n,h in known.items() if h==expected and n.endswith('/'+name)]
  if len(candidates)!=1 or sha(local(candidates[0]))!=expected:raise ValueError('revision_fingerprint')
  return local(candidates[0])
 for name in r['fingerprints']:bound(name)
 def read(name):return json.loads(bound(name).read_text())
 if r['result']!='PASS' or r['tasksClosed']!=['6.6']:raise ValueError('revision_closure')
 spec=local('openspec/changes/establish-v1-plugin/specs/quality-review/spec.md').read_text().split('### Requirement: VC-QA-002 ',1)[1].split('### Requirement:',1)[0];contracts={s.splitlines()[0]:hashlib.sha256(s.strip().encode()).hexdigest() for s in spec.split('#### Scenario: ')[1:]};matrix=read(r['scenarioMatrix'])
 expectedCoverage={'VC-QA-002-P':{'guards','goal-change','round-limit'},'VC-QA-002-N':{'budget','small-improvement','lower-score','round-limit'},'VC-QA-002-FRESH':{'guards','stale-gui'},'VC-QA-002-CYCLE':{'budget','small-improvement','lower-score','round-limit','guards','goal-change','stale-gui'}}
 if matrix['scenarioContracts']!=contracts or len(matrix['entries'])!=4 or {x['scenario'] for x in matrix['entries']}!=set(contracts):raise ValueError('revision_scenarios')
 for row in matrix['entries']:
  if row['result']!='PASS' or row['level']!='native-fixed-install' or set(row['evidence'])!={r['cases'][x] for x in expectedCoverage[row['scenario'].split()[0]]}:raise ValueError('revision_scenarios')
 lock=read('skills.lock.json')['sources'][0];host=read(r['host']);integrity=read(r['integrity']);ids={x['name']:x['sha256'] for x in host['skills']}
 if host['result']!='PASS' or len(host['skills'])!=13 or ids!=lock['sha256'] or integrity['digests']!=ids or integrity['skillsUnchanged']!=13 or integrity['result']!='PASS' or any(x['enabled'] is not True for x in host['skills']):raise ValueError('revision_host')
 for source,target in [('pluginVersion','pluginVersion'),('pluginCommit','pluginCommit'),('skillSourceRef','sourceRef'),('skillSourceCommit','sourceCommit'),('hostVersion','hostVersion')]:
  if host[source]!=r[target]:raise ValueError('revision_identity')
 if read('plugin.json')['version']!=r['pluginVersion'] or lock['ref']!=r['sourceRef'] or lock['sha']!=r['sourceCommit'] or any(digest!=sha(bound(name)) for name,digest in integrity['installedCodeDigests'].items()):raise ValueError('revision_identity')
 provenance=read(r['nativeInput']['provenance'])
 if provenance['result']!='PASS' or provenance['manifest']['files']['project.vectorcraft']!=r['nativeInput']['projectRevision'] or provenance['runtimeSha256']!=r['runtimeSha256']:raise ValueError('revision_input_provenance')
 checker={p:sha(bound(p)) for p in ['src/evaluation/delivery_quality.py','src/harness/process_runner.py','skills/vectorcraft-use/scripts/exchange_loss.py']};field='appearance.items.0.paint';value={'type':'solid','color':{'model':'rgb','r':0,'g':1,'b':0}}
 def checked(request):
  i=request['input'];e=i['technicalEvidence']
  if i['technicalEvidenceOrigin']!='checked-decoder' or i['technicalStatus']!='PASS' or e['technicalStatus']!='PASS' or e['artifactIntegrityStatus']!='PASS' or e['runtimeIdentity']!=r['runtimeSha256'] or e['projectRevision']!=i['projectRevision'] or e['checkerFiles']!=checker or len(e['outputs'])!=3 or {Path(o['path']).suffix for o in e['outputs']}!={'.svg','.pdf','.png'} or any(o['status']!='PASS' or e['files'][o['path']]!=o['sha256'] for o in e['outputs']):raise ValueError('revision_decode')
  if any(e[k]!='NOT_RUN' for k in ['engineeringStatus','nativeReopenStatus','creativeStatus']) or e['acceptanceStatus']!='pending':raise ValueError('revision_claim')
 def common(n,driver):
  if n['result']!='PASS' or n['pluginVersion']!=r['pluginVersion'] or n['sourceRef']!=r['sourceRef'] or n['platform']!=r['platform'] or n.get('level','fixed-install')!='fixed-install' or n['driverSha256']!=sha(bound('scripts/qa/'+driver)):raise ValueError('revision_execution')
  checked(n['initialRequest'])
  if n['initialRequest']['input']['projectRevision']!=r['nativeInput']['projectRevision']:raise ValueError('revision_input_provenance')
  p=n['proposal'];first=n['initialRequest'];auth=first['input']['authorization']
  if p['requestId']!=first['id'] or p['bindingHash']!=first['bindingHash'] or p['expectedProjectRevision']!=first['input']['projectRevision'] or p['changes']!=[{'objectId':2,'field':field,'value':value}] or p['authorization']!={**auth,'objects':[2],'fields':[field]}:raise ValueError('revision_authority')
  b=n['best'];chosen=n['initialRequest'] if b['requestId']==first['id'] else n.get('nextRequest')
  if not chosen or b['requestId']!=chosen['id'] or b['projectRevision']!=chosen['input']['projectRevision'] or b['technicalStatus']!='PASS' or b['engineeringStatus']!='NOT_RUN' or b['acceptanceStatus']!='pending':raise ValueError('revision_best_claim')
  e=chosen['input']['technicalEvidence'];expected={'manifest.json':e['manifestSha256'],**e['files']}
  if any(b['fingerprints'].get(k)!=v for k,v in expected.items()):raise ValueError('revision_best_dependencies')
  if n.get('allGroupsStopped') is not True:raise ValueError('revision_process_stop')
  return first,b
 def obj(model,id):
  found=[]
  def walk(x):
   if isinstance(x,dict):
    if x.get('id')==id:found.append(x)
    for child in x.values():walk(child)
   elif isinstance(x,list):
    for child in x:walk(child)
  walk(model['layers'])
  if len(found)!=1:raise ValueError('revision_control')
  return found[0]
 for mode,score,reason in [('budget',3,'budget_exceeded'),('small-improvement',2.05,'stagnation'),('lower-score',1.9,'stagnation'),('round-limit',3,'round_limit'),('goal-change',3,'goal_changed')]:
  n=read(r['cases'][mode]);first,best=common(n,'revision_budget.ts' if mode=='budget' else 'revision_goal.ts' if mode=='goal-change' else 'revision_stops.ts');next=n['nextRequest'];checked(next);cycle=n['cycle'];chosen=first if mode in ('lower-score','goal-change') else next
  if cycle['state']!='stopped' or cycle['reason']!=reason or cycle['latest']!=next['id'] or best['latestRequestId']!=next['id'] or best['requestId']!=chosen['id'] or best['score']!=(2 if chosen is first else score) or not best['unresolvedIssues'] or best['reason']!=reason:raise ValueError('revision_stop_best')
  expectedPolicy={'maxRounds':1 if mode=='round-limit' else 2,'stagnationLimit':1,'minImprovement':.1}
  if cycle['policy']!=expectedPolicy or cycle['rounds']!=1 or cycle['stagnation']!=(1 if mode in ('small-improvement','lower-score') else 0):raise ValueError('revision_policy')
  if n['sharedAttempts']!=(4 if mode in ('budget','lower-score','goal-change') else 5) or best['sharedBudget']['attempts']!=n['sharedAttempts'] or best['sharedBudget']['id']!=n['proposal']['authorization']['budgetId']:raise ValueError('revision_budget')
  if obj(n['sourceModel'],3)!=obj(n['revisedModel'],3) or obj(n['revisedModel'],2)['appearance']['items'][0]['paint']!=value or n['sourceModel']['artboards']!=n['revisedModel']['artboards'] or n['sourcePreserved'] is not True or n['controlTextPreserved'] is not True:raise ValueError('revision_control')
  m=n['manifest'];execution=n['execution']
  if m['files']!=next['input']['technicalEvidence']['files'] or m['sourceProjectSha256']!=first['input']['projectRevision'] or next['input']['native']!=execution['output']+'/project.vectorcraft' or execution['state']!='awaiting_review':raise ValueError('revision_lineage')
  if mode=='budget' and not best['path'].startswith('QA_ROOT/.technical-checks/'):raise ValueError('revision_budget_snapshot')
  if mode=='goal-change' and (best['unresolvedIssues']!=n['latestIssues'] or first['fingerprints'][first['input']['targets'][0]['path']]==next['fingerprints'][next['input']['targets'][0]['path']]):raise ValueError('revision_latest_goal')
 n=read(r['cases']['stale-gui']);common(n,'revision_stale_gui.ts');g=n['gui'];snapshots=read(r['cases']['gui-snapshots'])
 if n['guiDriverSha256']!=sha(bound('scripts/qa/revision_gui_edit.py')) or g['snapshotsSha256']!=sha(bound(r['cases']['gui-snapshots'])) or any(g[k] is not True for k in ['listenerOwnedByPID','ownedProcessesStopped','nativeDocumentChanged','nativeReopened','persistedContentMatches']) or g['sourceBeforeSha256']!=n['initialRequest']['input']['projectRevision'] or g['sourceBeforeSha256']==g['sourceAfterSha256']:raise ValueError('revision_gui')
 if 'stale_review_binding' not in n['refusal'] or n['sharedAttempts']!=2 or n['registeredGroupsBefore']!=n['registeredGroupsAfter'] or n['newOutputAbsent'] is not True or n['originalSourcePreserved'] is not True:raise ValueError('revision_stale_source')
 modified=snapshots['modified'];reopened=snapshots['reopened']
 if obj(snapshots['original'],2)==obj(modified,2) or obj(snapshots['original'],3)!=obj(modified,3) or reopened!={**modified,'metadata':{**modified['metadata'],'modified':reopened['metadata']['modified']}}:raise ValueError('revision_gui_content')
 n=read(r['cases']['guards']);first,best=common(n,'revision_guards.ts');checked(n['nextRequest']);checked(n['wrongDirectoryRequest']);rows={x['case']:x for x in n['records']}
 errors={'unassessed-object':'revision_not_assessed','outside-authority':'revision_outside_authorization','duplicate-field':'invalid_revision_targets','legacy-bypass':'revision_cycle_required','overlapping-round':'revision_round_pending','stale-target':'stale_review_binding','stale-rubric':'stale_review_binding','wrong-source':'revision_source_mismatch','wrong-runtime':'revision_runtime_mismatch','await-explicit-feedback':'revision_round_pending','wrong-output-lineage':'revision_lineage_mismatch','pending-review-is-not-feedback':'checked_review_required','best-dependency-tamper':'best_candidate_changed','best-native-tamper':'best_candidate_changed'}
 if len(n['records'])!=15 or set(rows)!=set(errors)|{'idempotent-proposal'}:raise ValueError('revision_guards_coverage')
 for name,error in errors.items():
  row=rows[name]
  if row['result']!='PASS' or error not in row['error'] or row['attemptsBefore']!=row['attemptsAfter']:raise ValueError('revision_guard_refusal')
  if name in ('stale-target','stale-rubric','wrong-source','wrong-runtime') and row['outputAbsent'] is not True:raise ValueError('revision_guard_effects')
 response=n['nextReceipt'];next=n['nextRequest'];mean=sum(response['scores'].values())/5
 if set(response['scores'])!={'structure','text','brand','layout','legibility'} or mean!=2.5 or best['score']!=mean or best['requestId']!=next['id'] or best['unresolvedIssues']!=response['issues'] or 'explicit QA' not in response['reviewer']['identity'] or response['reviewer']['independenceEvidence'] is not None:raise ValueError('revision_mean_feedback')
 m=read(r['cases']['guards-manifest'])
 if sha(bound(r['cases']['guards-manifest']))!=next['input']['technicalEvidence']['manifestSha256'] or m['sourceProjectSha256']!=first['input']['projectRevision'] or m['files']!=next['input']['technicalEvidence']['files'] or next['input']['native']!=n['execution']['output']+'/project.vectorcraft' or n['wrongDirectoryRequest']['input']['native']==next['input']['native']:raise ValueError('revision_lineage')
 if n['sharedAttempts']!=6 or n['nextProposal']['round']!=2 or n['nextProposal']['requestId']!=next['id'] or n['nextProposal']['authorization']!=n['proposal']['authorization'] or rows['idempotent-proposal']['rounds']!=1 or n['originalSourcePreserved'] is not True:raise ValueError('revision_explicit_round')
 print(json.dumps({'result':'PASS','scenarios':4,'nativeRevisions':6,'guardCases':15,'ownedDesktopStaleCases':1,'taskClosed':'6.6','scope':'public63/source43 on actual Codex macOS arm64; QA feedback only, creative judgment separate'}))
if __name__=='__main__':verify()
