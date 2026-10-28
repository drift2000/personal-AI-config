"""Isolated integration tests; never read or mutate the real Codex/Claude profiles."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "adapters"))
from codex import adapter as a


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="pac-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = self.base / "projects/.private"
        shutil.copytree(ROOT / "global", self.repo / "global", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "adapters", self.repo / "adapters", ignore=shutil.ignore_patterns("__pycache__"))
        self.home = self.base / "user home"
        self.codex = self.home / ".codex"
        self.codex.mkdir(parents=True)
        self.config = self.codex / "config.toml"
        self.config.write_text('model = "existing-model"\n')
        self.claude = self.home / ".claude/settings.json"
        self.claude.parent.mkdir()
        self.claude.write_text('{"existing": true}\n')

    def plan(self, replacements=()):
        return a.plan(self.repo, self.codex, self.home, sys.executable, replacements)

    def activate(self, replacements=()):
        return a.activate(self.plan(replacements), self.repo)

    def project(self, name="Joomla new name", git=False):
        root = self.repo.parent / name
        root.mkdir()
        (root / "src").mkdir()
        pdir = self.repo / name
        pdir.mkdir()
        (pdir / "context.md").write_text("PRIVATE_CONTENT_SENTINEL")
        if git:
            subprocess.run(["git", "init", "-q", str(root)], check=True)
        return root, pdir

    def hook(self, cwd, event="SessionStart", raw=None):
        result = subprocess.run([sys.executable, "-B", str(self.repo / "adapters/codex/context_hook.py"),
                                 "--private-root", str(self.repo)],
                                input=raw if raw is not None else json.dumps({"cwd": str(cwd), "hook_event_name": event}),
                                text=True, capture_output=True, check=True)
        return json.loads(result.stdout)

    def test_prepare_and_check_have_no_profile_side_effects(self):
        before = a.snapshot(self.home)
        prepared = self.plan()
        path = self.base / "plan.json"
        a.save_new(path, prepared)
        self.assertEqual(a.snapshot(self.home), before)
        with self.assertRaises(FileExistsError):
            a.save_new(path, prepared)

    def test_activation_links_wrappers_and_preserves_configuration(self):
        manifest = self.activate()
        self.assertTrue(manifest.is_file())
        self.assertEqual((self.codex / "AGENTS.md").resolve(), self.repo / "global/AGENTS.md")
        roles = sorted((self.codex / "agents").glob("*.toml"))
        self.assertEqual(len(roles), 5)
        for path in roles:
            role = {key: json.loads(value) for key, value in
                    (line.split(" = ", 1) for line in path.read_text().splitlines() if " = " in line)}
            self.assertTrue(role["name"].startswith("personal-ai-"))
            self.assertIn("global/agents/", role["developer_instructions"])
            self.assertNotIn("Порядок роботи:", role["developer_instructions"])
        self.assertTrue((self.home / ".agents/skills/private-project-memory").is_symlink())
        self.assertEqual(self.config.read_text(), 'model = "existing-model"\n')
        self.assertEqual(self.claude.read_text(), '{"existing": true}\n')

    def test_cli_codex_only_never_calls_claude_or_git_configuration(self):
        prepared = self.base / "cli-plan.json"
        config_before = a.snapshot(self.repo / ".git")
        subprocess.run([sys.executable, "-B", str(self.repo / "adapters/install.py"), "--codex-only",
                        "--home", str(self.home), "--prepare", str(prepared)], check=True, capture_output=True)
        subprocess.run([sys.executable, "-B", str(self.repo / "adapters/install.py"), "--codex-only",
                        "--activate", str(prepared)], check=True, capture_output=True)
        self.assertEqual(self.claude.read_text(), '{"existing": true}\n')
        self.assertEqual(a.snapshot(self.repo / ".git"), config_before)

    def test_codex_home_environment_and_isolated_home_precedence(self):
        import argparse
        custom = self.base / "custom-profile"
        args = argparse.Namespace(activate=None, rollback=None, home=None, codex_home=None,
                                  python=sys.executable, replace=[], prepare=None, check=False)
        with patch.dict(os.environ, {"CODEX_HOME": str(custom)}), patch.object(Path, "home", return_value=self.home):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                a.run(args, self.repo)
            self.assertIn(str(custom / "AGENTS.md"), output.getvalue())
            args.home = str(self.home)
            with contextlib.redirect_stdout(io.StringIO()) as output:
                a.run(args, self.repo)
            self.assertIn(str(self.codex / "AGENTS.md"), output.getvalue())
        self.assertFalse(custom.exists())

    def test_late_conflict_prevents_all_activation(self):
        (self.codex / "hooks.json").write_text('{"foreign": true}')
        before = a.snapshot(self.home)
        prepared = self.plan()
        self.assertTrue(prepared["conflicts"])
        with self.assertRaises(a.Conflict):
            a.activate(prepared, self.repo)
        self.assertEqual(a.snapshot(self.home), before)

    def test_foreign_and_dangling_links_are_not_overwritten(self):
        target = self.codex / "AGENTS.md"
        target.symlink_to(self.base / "missing")
        self.assertTrue(self.plan()["conflicts"])
        self.assertEqual(os.readlink(target), str(self.base / "missing"))

    def test_symlink_destination_parent_is_rejected(self):
        external = self.base / "external"
        external.mkdir()
        (self.codex / "agents").symlink_to(external)
        with self.assertRaises(a.Conflict):
            self.plan()
        self.assertEqual(list(external.iterdir()), [])

    def test_stale_and_edited_plans_are_rejected_before_writing(self):
        prepared = self.plan()
        (self.codex / "AGENTS.md").write_text("new user change")
        before = a.snapshot(self.home)
        with self.assertRaises(a.Conflict):
            a.activate(prepared, self.repo)
        self.assertEqual(a.snapshot(self.home), before)
        prepared = self.plan(["AGENTS.md"])
        prepared["entries"][1]["path"] = str(self.config)
        with self.assertRaises(a.Conflict):
            a.activate(prepared, self.repo)

    def test_explicit_migration_and_rollback_restore_old_objects(self):
        agents = self.codex / "AGENTS.md"
        agents.write_text("old private rules")
        skill = self.home / ".agents/skills/private-project-memory"
        shutil.copytree(self.repo / "global/skills/private-project-memory", skill)
        original_agents, original_skill = a.snapshot(agents), a.snapshot(skill)
        self.assertEqual(len(self.plan()["conflicts"]), 2)
        manifest = self.activate(["AGENTS.md", "skill:private-project-memory"])
        self.assertTrue(skill.is_symlink())
        backed_up = json.loads(manifest.read_text())
        self.assertFalse(any(e["path"].endswith("config.toml") for e in backed_up["entries"]))
        a.rollback(manifest, self.repo)
        self.assertEqual(a.snapshot(agents), original_agents)
        self.assertEqual(a.snapshot(skill), original_skill)
        self.assertFalse((self.codex / "hooks.json").exists())
        self.assertFalse((self.codex / "agents").exists())
        a.rollback(manifest, self.repo)

    def test_migration_refuses_unreviewed_skill_payload(self):
        skill = self.home / ".agents/skills/private-project-memory"
        shutil.copytree(self.repo / "global/skills/private-project-memory", skill)
        (skill / "auth.json").write_text("synthetic forbidden fixture")
        self.assertTrue(self.plan(["skill:private-project-memory"])["conflicts"])

    def test_migration_refuses_modified_skill_manifest(self):
        skill = self.home / ".agents/skills/private-project-memory"
        shutil.copytree(self.repo / "global/skills/private-project-memory", skill)
        manifest = skill / "SKILL.md"
        manifest.write_text(manifest.read_text() + "\nUser-specific instruction\n")
        before = a.snapshot(skill)
        prepared = self.plan(["skill:private-project-memory"])
        self.assertTrue(prepared["conflicts"])
        with self.assertRaises(a.Conflict):
            a.activate(prepared, self.repo)
        self.assertEqual(a.snapshot(skill), before)

    def test_skill_manifest_change_after_prepare_is_detected(self):
        skill = self.home / ".agents/skills/private-project-memory"
        shutil.copytree(self.repo / "global/skills/private-project-memory", skill)
        prepared = self.plan(["skill:private-project-memory"])
        self.assertFalse(prepared["conflicts"])
        manifest = skill / "SKILL.md"
        manifest.write_text(manifest.read_text() + "\nChanged after prepare\n")
        before = a.snapshot(self.home)
        with self.assertRaisesRegex(a.Conflict, "stale or edited"):
            a.activate(prepared, self.repo)
        self.assertEqual(a.snapshot(self.home), before)

    def test_idempotence_and_live_methodology(self):
        self.activate()
        before = a.snapshot(self.home)
        self.assertIsNone(self.activate())
        self.assertEqual(a.snapshot(self.home), before)
        source = self.repo / "global/AGENTS.md"
        source.write_text(source.read_text() + "\nNew source rule\n")
        self.assertIn("New source rule", (self.codex / "AGENTS.md").read_text())
        self.assertIsNone(self.activate())

    def test_profile_inside_source_repository_is_rejected(self):
        with self.assertRaises(a.Conflict):
            a.plan(self.repo, self.repo / "global", self.home, sys.executable, ["AGENTS.md"])

    def test_codex_adapter_refuses_non_posix_without_profile_changes(self):
        before = a.snapshot(self.home)
        with patch.object(a.os, "name", "nt"):
            with self.assertRaisesRegex(a.Conflict, "POSIX only"):
                self.plan()
        self.assertEqual(a.snapshot(self.home), before)

    def test_rollback_does_not_require_live_sources(self):
        manifest = self.activate()
        shutil.rmtree(self.repo / "global")
        a.rollback(manifest, self.repo)
        self.assertFalse(os.path.lexists(self.codex / "AGENTS.md"))

    def test_directory_migration_failure_restores_original(self):
        skill = self.home / ".agents/skills/private-project-memory"
        shutil.copytree(self.repo / "global/skills/private-project-memory", skill)
        before = a.snapshot(skill)
        actual = os.replace
        def fail(source, target):
            if Path(target) == skill and Path(source).is_symlink():
                raise OSError("injected link installation failure")
            return actual(source, target)
        with patch.object(a.os, "replace", side_effect=fail):
            with self.assertRaises(OSError):
                self.activate(["skill:private-project-memory"])
        self.assertEqual(a.snapshot(skill), before)
        self.assertFalse(list(skill.parent.glob(".personal-ai-displaced-*")))

    def test_rollback_refuses_modified_installed_objects(self):
        manifest = self.activate()
        path = self.codex / "agents/personal-ai-qa.toml"
        path.write_text("user changes")
        before = a.snapshot(self.home)
        with self.assertRaises(a.Conflict):
            a.rollback(manifest, self.repo)
        self.assertEqual(a.snapshot(self.home), before)

    def test_rollback_refuses_tampered_backup(self):
        (self.codex / "AGENTS.md").write_text("old")
        manifest = self.activate(["AGENTS.md"])
        (manifest.parent / "original-0").write_text("modified backup")
        with self.assertRaises(a.Conflict):
            a.rollback(manifest, self.repo)
        self.assertTrue((self.codex / "AGENTS.md").is_symlink())

    def test_failed_activation_restores_applied_objects(self):
        actual = a.install_object
        count = [0]
        def fail(entry):
            count[0] += 1
            if count[0] == 3:
                raise OSError("simulated disk error")
            actual(entry)
        with patch.object(a, "install_object", side_effect=fail):
            with self.assertRaises(OSError):
                self.activate()
        self.assertFalse(os.path.lexists(self.codex / "AGENTS.md"))
        self.assertFalse((self.codex / "agents").exists())

    def test_duplicate_user_skill_and_global_override_block(self):
        alias = self.home / ".agents/skills/another-name"
        alias.mkdir(parents=True)
        (alias / "SKILL.md").write_text("---\nname: private-project-memory\n---\n")
        (self.codex / "AGENTS.override.md").write_text("override")
        self.assertEqual(len(self.plan()["conflicts"]), 2)

    def test_project_roles_and_skills_survive_activation(self):
        project, _ = self.project()
        (project / ".codex/agents").mkdir(parents=True)
        for role in ["architect", "qa", "security", "review"]:
            (project / ".codex/agents" / (role + ".toml")).write_text('developer_instructions = "project specialist"')
        for skill in ["catalog-domain", "code-verification", "database-change", "joomla-development"]:
            folder = project / ".agents/skills" / skill
            folder.mkdir(parents=True)
            (folder / "SKILL.md").write_text("---\nname: " + skill + "\n---\n")
        before = a.snapshot(project)
        self.activate()
        self.assertEqual(a.snapshot(project), before)

    def test_hook_root_subdirectory_and_subagent(self):
        project, private = self.project(git=True)
        for cwd in (project, project / "src"):
            for event in ("SessionStart", "SubagentStart"):
                result = self.hook(cwd, event)
                self.assertNotIn("systemMessage", result)
                self.assertEqual(result["hookSpecificOutput"]["hookEventName"], event)
                message = result["hookSpecificOutput"]["additionalContext"]
                self.assertIn(str(private), message)
                self.assertNotIn("PRIVATE_CONTENT_SENTINEL", message)

    def test_hook_real_linked_worktree_without_commits(self):
        project, private = self.project(git=True)
        wt = self.base / "different-worktree-name"
        subprocess.run(["git", "-C", str(project), "worktree", "add", "--orphan", "-b", "test-worktree", str(wt)],
                       check=True, capture_output=True)
        message = self.hook(wt)["hookSpecificOutput"]["additionalContext"]
        self.assertIn(str(private), message)
        self.assertNotIn("hook error", message)

    def test_hook_no_cross_project_context_for_foreign_clone_or_nested_repo(self):
        project, private = self.project(git=True)
        foreign = self.base / "elsewhere" / project.name
        foreign.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(foreign)], check=True)
        for cwd in (foreign, project / "src"):
            subprocess.run(["git", "init", "-q", str(cwd)], check=True)
            result = self.hook(cwd)
            self.assertIn("systemMessage", result)
            self.assertNotIn(str(private), result["hookSpecificOutput"]["additionalContext"])

    def test_hook_missing_context_unknown_cwd_and_invalid_input(self):
        empty = self.repo.parent / "without-memory"
        empty.mkdir()
        message = self.hook(empty)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Приватного каталогу немає", message)
        self.assertFalse((self.repo / empty.name).exists())
        self.assertIn("systemMessage", self.hook(self.base))
        for raw in ("{broken", "{}", "[]"):
            self.assertIn("hook error", self.hook(self.base, raw=raw)["systemMessage"])

    def test_hook_private_repository_self_context(self):
        folder = self.repo / self.repo.name
        folder.mkdir()
        (folder / "context.md").write_text("private configuration memory")
        result = self.hook(self.repo)["hookSpecificOutput"]["additionalContext"]
        self.assertIn(str(folder / "context.md"), result)
        self.assertNotIn("private configuration memory", result)

    def test_existing_claude_hook_contract_is_unchanged(self):
        project, private = self.project()
        result = subprocess.run([sys.executable, "-B", str(self.repo / "global/hooks/private_context.py"),
                                 "--private-root", str(self.repo), "--cwd", str(project)],
                                text=True, capture_output=True, check=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn(str(private), payload["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
