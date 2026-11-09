"""公开不可变提交验收不得被误记为已发布标签验收。"""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fixed_install_ref', ROOT/'scripts/acceptance/fixed_install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)
SHA = 'a'*40
URL = installer.GIT_URL


class FixedInstallReferenceTests(unittest.TestCase):
    def test_discovery_inventory_includes_source_and_plugin_local_skills(self):
        lock=json.loads((ROOT/'skills.lock.json').read_text())['sources'][0]
        local=json.loads((ROOT/'plugin-local-skills.json').read_text())
        names=installer.expected_skills(lock,local)
        self.assertEqual(len(names),25)
        self.assertIn('vectorcraft:vectorcraft-harness',names)
        self.assertIn('vectorcraft:vectorcraft-editor',names)
        with self.assertRaisesRegex(ValueError,'invalid_local_skill_inventory'):
            installer.expected_skills(lock,{**local,'skills':local['skills']+['vectorcraft-use']})
    def git(self, *args):
        if args == ('rev-parse', SHA+'^{commit}'): return SHA
        if args == ('rev-parse', 'v0.1.0-dev.64^{commit}'): return SHA
        if args == ('ls-remote', URL, 'refs/heads/main'): return SHA+'\trefs/heads/main'
        if args[0] == 'ls-remote': return SHA+'\trefs/tags/v0.1.0-dev.64^{}'
        raise AssertionError(args)

    def test_default_remains_public_tag(self):
        self.assertEqual(installer.resolve_reference('0.1.0-dev.64', None, self.git,public_verify=lambda commit:commit),
            {'ref':'v0.1.0-dev.64','commit':SHA,'kind':'public-tag'})

    def test_exact_remote_commit_is_candidate_not_published_tag(self):
        self.assertEqual(installer.resolve_reference('0.1.0-dev.64', SHA, self.git,public_verify=lambda commit:commit),
            {'ref':SHA,'commit':SHA,'kind':'public-commit'})

    def test_exact_remote_public_branch_commit_is_accepted_without_main(self):
        branch='fix/restore-release-gate-20261031'
        def git(*args):
            if args == ('rev-parse', SHA+'^{commit}'): return SHA
            if args == ('ls-remote',URL,'refs/heads/'+branch): return SHA+'\trefs/heads/'+branch
            raise AssertionError(args)
        self.assertEqual(installer.resolve_reference('0.1.0-dev.20261019.1',SHA,git,branch,lambda commit:commit),
            {'ref':SHA,'commit':SHA,'kind':'public-commit'})
        with self.assertRaisesRegex(ValueError,'remote_commit_mismatch'):
            installer.resolve_reference('0.1.0-dev.20261019.1',SHA,lambda *args: ('b'*40+'\trefs/heads/'+branch) if args[0]=='ls-remote' else SHA,branch,lambda commit:commit)
        with self.assertRaisesRegex(ValueError,'invalid_candidate_branch'):
            installer.resolve_reference('0.1.0-dev.20261019.1',SHA,lambda *args: SHA,'../main',lambda commit:commit)
        for public in (lambda commit:None,lambda commit:'b'*40):
            with self.assertRaisesRegex(ValueError,'public_commit_unverified'):
                installer.resolve_reference('0.1.0-dev.20261019.1',SHA,git,branch,public)
        with self.assertRaisesRegex(ValueError,'public_commit_unverified'):
            installer.resolve_reference('0.1.0-dev.20261019.1',SHA,git,branch,lambda commit: (_ for _ in ()).throw(OSError('offline')))

    def test_branch_abbreviated_commit_and_other_tag_are_rejected_before_git(self):
        def forbidden(*args): self.fail('invalid reference reached git')
        for ref in ('main','aaaaaaa','v0.1.0-dev.63','../main','A'*40):
            with self.subTest(ref=ref), self.assertRaisesRegex(ValueError,'invalid_fixed_reference'):
                installer.resolve_reference('0.1.0-dev.64',ref,forbidden,public_verify=lambda commit:commit)

    def test_unpushed_commit_is_rejected(self):
        def git(*args):
            if args[0]=='ls-remote': return 'b'*40+'\trefs/heads/main'
            return self.git(*args)
        with self.assertRaisesRegex(ValueError,'remote_commit_mismatch'):
            installer.resolve_reference('0.1.0-dev.64',SHA,git,public_verify=lambda commit:commit)

    def test_moved_tag_or_local_commit_alias_cannot_pass(self):
        def moved(*args):
            if args[0]=='ls-remote': return 'b'*40+'\trefs/tags/v0.1.0-dev.64^{}'
            return self.git(*args)
        with self.assertRaisesRegex(ValueError,'remote_release_mismatch'):
            installer.resolve_reference('0.1.0-dev.64',None,moved,public_verify=lambda commit:commit)
        def alias(*args):
            if args[0]=='rev-parse': return 'b'*40
            return self.git(*args)
        with self.assertRaisesRegex(ValueError,'fixed_commit_mismatch'):
            installer.resolve_reference('0.1.0-dev.64',SHA,alias,public_verify=lambda commit:commit)
