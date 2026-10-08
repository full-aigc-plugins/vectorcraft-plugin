"""插件协作控制：每次原生调用前核对状态、截止时间、源文件和持久意图。"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]

class ExecutionControlTests(unittest.TestCase):
    def load(self):
        spec=importlib.util.spec_from_file_location('execution_control',ROOT/'skills/vectorcraft-use/scripts/execution_control.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

    def fixture(self,root):
        source=root/'project.vectorcraft';source.write_bytes(b'original')
        plan=root/'plan.json';plan.write_text('{"operations":[]}')
        state=root/'state.json';state.write_text(json.dumps({'task':'test-task','epoch':1,'state':'running'}))
        events=root/'events.jsonl';events.touch();stat=events.stat()
        profile={'schema':'vectorcraft-execution-control/v1','task':'test-task','epoch':1,
          'stateFile':str(state),'eventFile':str(events),'eventDevice':stat.st_dev,'eventInode':stat.st_ino,
          'deadline':int(time.time()*1000)+60000,'maxBytes':1000000,'runtimeIdentity':'a'*64,
          'source':{'path':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()},
          'planFile':str(plan),'planHash':hashlib.sha256(plan.read_bytes()).hexdigest()}
        path=root/'control.json';path.write_text(json.dumps(profile));return path,profile,state,events,source

    def test_cancel_deadline_epoch_and_source_change_block_next_native_request(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path,profile,state,events,source=self.fixture(root);m=self.load();control=m.ExecutionControl(path)
            control.before_request('tools/call',{'arguments':{'command':'document.save','params':{'path':'unused'}}},7,42)
            self.assertEqual(json.loads(events.read_text().splitlines()[0])['requestId'],7)
            for replacement,error in [({'task':'test-task','epoch':1,'state':'cancel_requested'},'cancel_requested'),({'task':'test-task','epoch':2,'state':'running'},'stale_epoch')]:
                state.write_text(json.dumps(replacement))
                with self.assertRaisesRegex(RuntimeError,error):control.before_request('tools/call',{},8,42)
                self.assertEqual(len(events.read_text().splitlines()),1)
            state.write_text(json.dumps({'task':'test-task','epoch':1,'state':'running'}));source.write_bytes(b'GUI edit')
            with self.assertRaisesRegex(RuntimeError,'revision_conflict'):control.check()
            source.write_bytes(b'original');profile['deadline']=int(time.time()*1000)-1;path.write_text(json.dumps(profile))
            with self.assertRaisesRegex(RuntimeError,'deadline_exceeded'):m.ExecutionControl(path).check()

    def test_original_stage_identity_and_submitted_request_survive_reopen(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path,profile,state,events,source=self.fixture(root);m=self.load();control=m.ExecutionControl(path)
            stage=root/'native-stage';stage.mkdir();control.attach_stage(stage)
            control.before_request('tools/call',{'arguments':{'command':'document.save','params':{'path':str(stage/'project.vectorcraft')}}},2,313)
            control.after_request(2,313,{'content':[{'type':'text','text':'{"saved":true}'}]})
            records=[json.loads(line) for line in events.read_text().splitlines()]
            self.assertEqual([r['event'] for r in records],['stage_created','submitted','reply_received'])
            self.assertEqual(records[0]['inode'],stage.stat().st_ino)
            self.assertEqual(records[1]['params']['arguments']['params']['path'],str(stage/'project.vectorcraft'))
            self.assertEqual(m.ExecutionControl(path).profile['task'],'test-task')
            events.rename(events.with_suffix('.original'));events.write_text('replaced')
            with self.assertRaisesRegex(RuntimeError,'execution_event_identity_mismatch'):control.before_request('tools/call',{},4,313)

    def test_delivery_identity_is_durable_before_nested_stage_rename(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path,profile,state,events,source=self.fixture(root)
            control=self.load().ExecutionControl(path)
            stage=root/'stage';stage.mkdir();control.attach_stage(stage)
            delivery=stage/'delivery';delivery.mkdir();manifest=delivery/'manifest.json';manifest.write_text('{"fixture":true}')
            output=root/'output';control.prepare_delivery(delivery,output)
            record=json.loads(events.read_text().splitlines()[-1])
            self.assertEqual(record['event'],'delivery_prepared')
            self.assertEqual(record['path'],str(delivery.resolve()))
            self.assertEqual(record['output'],str(output.absolute()))
            self.assertEqual(record['inode'],delivery.stat().st_ino)
            self.assertEqual(record['manifestSha256'],hashlib.sha256(manifest.read_bytes()).hexdigest())
            self.assertFalse(output.exists())
            delivery.rename(output)
            self.assertEqual(output.stat().st_ino,record['inode'])

    def test_delivery_identity_refuses_unowned_stage_and_output_parent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path,profile,state,events,source=self.fixture(root)
            control=self.load().ExecutionControl(path)
            stage=root/'stage';stage.mkdir();control.attach_stage(stage)
            external=root/'other';external.mkdir();(external/'manifest.json').write_text('{}')
            with self.assertRaisesRegex(RuntimeError,'delivery_outside_stage'):
                control.prepare_delivery(external,root/'output')
            (stage/'manifest.json').write_text('{}')
            with self.assertRaisesRegex(RuntimeError,'delivery_outside_stage'):
                control.prepare_delivery(stage,external/'output')
            self.assertEqual(len(events.read_text().splitlines()),1)

    def test_revision_checks_actual_object_fields_and_all_global_swatch_consumers(self):
        import copy
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path,p,state,events,source=self.fixture(root)
            p['authorization']={'objects':[4],'fields':['appearance.items.0.paint.color']};path.write_text(json.dumps(p))
            m=self.load();control=m.ExecutionControl(path)
            color={'model':'rgb','r':0.1,'g':0.2,'b':0.3}
            obj=lambda i:{'id':i,'kind':{'type':'rectangle'},'x':0,'appearance':{'items':[{'paint':{'type':'solid','swatch':'Brand','color':color}}]}}
            before={'layers':[obj(4),obj(5)],'artboards':[],'swatches':[{'name':'Brand','paint':{'type':'solid','color':color}}]}
            with self.assertRaisesRegex(RuntimeError,'revision_outside_authorization'):
                control.authorize_operation('swatch.edit',{'name':'Brand','color':'#175cce'},before)
            p['authorization']['objects']=[4,5];path.write_text(json.dumps(p));control=m.ExecutionControl(path)
            control.authorize_operation('swatch.edit',{'name':'Brand','color':'#175cce'},before)
            after=copy.deepcopy(before)
            for obj in after['layers']:obj['appearance']['items'][0]['paint']['color']={'model':'rgb','r':0.2,'g':0.3,'b':0.4}
            after['swatches'][0]['paint']['color']={'model':'rgb','r':0.2,'g':0.3,'b':0.4}
            control.verify_revision(before,after,'swatch.edit',{'name':'Brand','color':'#175cce'})
            after['layers'][0]['x']=90
            with self.assertRaisesRegex(RuntimeError,'revision_field_violation'):control.verify_revision(before,after,'swatch.edit',{'name':'Brand','color':'#175cce'})
            after=copy.deepcopy(before);after['layers'].reverse()
            with self.assertRaisesRegex(RuntimeError,'revision_structure_violation'):control.verify_revision(before,after,'swatch.edit',{'name':'Brand','color':'#175cce'})
            with self.assertRaisesRegex(RuntimeError,'managed_revision_command_unclassified'):control.authorize_operation('object.delete',{'ids':[4]},before)

    def test_structural_selection_requires_explicit_structure_authorization(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path,p,state,events,source=self.fixture(root)
            p['authorization']={'objects':[2,3],'fields':['structure']};path.write_text(json.dumps(p))
            control=self.load().ExecutionControl(path)
            before={'artboards':[],'layers':[{'id':1,'kind':{'type':'layer','children':[
                {'id':i,'kind':{'type':'path','path':{'subpaths':[]}}} for i in [2,3,4]]}}]}
            control.authorize_operation('select.set',{'ids':[2,3]},before)
            control.verify_revision(before,before,'select.set',{'ids':[2,3]},after_selection=[2,3])
            with self.assertRaisesRegex(RuntimeError,'revision_outside_authorization'):
                control.authorize_operation('select.set',{'ids':[4]},before)

    def test_structural_permission_cannot_be_inferred_from_kind_field_or_parent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path,p,state,events,source=self.fixture(root)
            before={'layers':[{'id':1,'kind':{'type':'layer','children':[
                {'id':2,'kind':{'type':'group','children':[{'id':3,'kind':{'type':'path'}}]}}]}}]}
            for objects,fields,selection in [([2,3],['kind'],[2]),([2],['structure'],[2]),([2,3],['structure'],[99])]:
                with self.subTest(objects=objects,fields=fields):
                    p['authorization']={'objects':objects,'fields':fields};path.write_text(json.dumps(p))
                    control=self.load().ExecutionControl(path)
                    with self.assertRaisesRegex(RuntimeError,'revision_outside_authorization'):
                        control.authorize_operation('object.ungroup',{},before,selection=selection)
            p['authorization']={'objects':[2,3],'fields':['structure']};path.write_text(json.dumps(p))
            self.load().ExecutionControl(path).authorize_operation('object.ungroup',{},before,selection=[2])

    def test_boolean_verification_still_protects_unselected_tree_and_document(self):
        import copy
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path,p,state,events,source=self.fixture(root)
            p['authorization']={'objects':[2,3],'fields':['structure']};path.write_text(json.dumps(p))
            control=self.load().ExecutionControl(path)
            before={'units':'Points','layers':[{'id':1,'kind':{'type':'layer','children':[
                {'id':i,'name':str(i),'kind':{'type':'path'}} for i in [2,3,4]]}}]}
            after=copy.deepcopy(before);after['layers'][0]['kind']['children']=[{'id':5,'kind':{'type':'path'}},before['layers'][0]['kind']['children'][2]]
            control.authorize_operation('object.pathfinder.unite',{},before,selection=[2,3])
            control.verify_revision(before,after,'object.pathfinder.unite',{},result={'ids':[5]},selection=[2,3])
            for variant in ['unselected','units']:
                changed=copy.deepcopy(after)
                if variant=='unselected':changed['layers'][0]['kind']['children'][1]['name']='corrupt'
                else:changed['units']='Pixels'
                with self.assertRaisesRegex(RuntimeError,'boolean_unselected_violation'):
                    control.verify_revision(before,changed,'object.pathfinder.unite',{},result={'ids':[5]},selection=[2,3])
            with self.assertRaisesRegex(RuntimeError,'boolean_result_identity_mismatch'):
                control.verify_revision(before,after,'object.pathfinder.unite',{},result={'ids':[999]},selection=[2,3])

    def test_structural_selection_receipt_must_match_actual_selection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path,p,state,events,source=self.fixture(root)
            p['authorization']={'objects':[2,3],'fields':['structure']};path.write_text(json.dumps(p))
            control=self.load().ExecutionControl(path)
            before={'layers':[{'id':i,'kind':{'type':'path'}} for i in [2,3]]}
            with self.assertRaisesRegex(RuntimeError,'revision_selection_identity_mismatch'):
                control.verify_revision(before,before,'select.set',{'ids':[2,3]},after_selection=[2])
