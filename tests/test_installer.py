"""Offline installer tests using the actual marketplace package layout."""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("marketplace_installer", SCRIPTS / "install.py")
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "repo"
        self.root.mkdir()
        self.destination = self.base / "agent" / "skills"
        self.names = ["neuraldeep-alpha", "neuraldeep-beta"]
        self.document = {"name": "neuraldeep-skills", "version": "1.0.0", "plugins": []}
        for name in self.names:
            files = {
                "SKILL.md": f"---\nname: {name}\ndescription: Test fixture\nmetadata:\n  version: 1.0.0\n---\nGuarded fixture.\n",
                "README.md": "# Fixture\n", "STARTER_RELAY.md": "Stop on blocked.\n",
                "TESTING.md": "Offline fixture.\n", "LICENSE": "MIT fixture\n",
                "scripts/client.py": "print('fixture')\n",
            }
            entry = {"name": name, "version": "1.0.0", "description": "Test fixture",
                     "source": f"https://github.com/viktor-drobek/{name}.git", "commit": "a" * 40,
                     "files": {}}
            for relative, text in files.items():
                path = self.source(name) / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
                entry["files"][relative] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            self.document["plugins"].append(entry)
        self.save_catalog()

    def source(self, name):
        return self.root / "plugins" / name / "skills" / name

    def save_catalog(self):
        (self.root / "catalog.json").write_text(json.dumps(self.document), encoding="utf-8")

    def invoke(self, args):
        output, errors = io.StringIO(), io.StringIO()
        with patch.object(installer, "ROOT", self.root, create=True), redirect_stdout(output), redirect_stderr(errors):
            result = installer.main(args)
        return result, output.getvalue(), errors.getvalue()

    def test_single_skill_installs_directly_beneath_destination(self):
        self.assertEqual(installer.install(self.root, self.destination, self.names[:1]), self.names[:1])
        self.assertEqual((self.destination / self.names[0] / "SKILL.md").read_bytes(),
                         (self.source(self.names[0]) / "SKILL.md").read_bytes())
        self.assertFalse((self.destination / self.names[1]).exists())

    def test_existing_shared_root_and_unrelated_skills_are_preserved(self):
        existing = self.destination / "local-skill" / "SKILL.md"
        existing.parent.mkdir(parents=True)
        existing.write_text("local\n", encoding="utf-8")
        installer.install(self.root, self.destination, self.names)
        self.assertEqual(existing.read_text(encoding="utf-8"), "local\n")
        for name in self.names:
            self.assertTrue((self.destination / name / "scripts/client.py").is_file())

    def test_batch_collision_is_checked_before_any_install(self):
        existing = self.destination / self.names[1]
        existing.mkdir(parents=True)
        marker = existing / "local.txt"
        marker.write_text("keep\n", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            installer.install(self.root, self.destination, self.names)
        self.assertFalse((self.destination / self.names[0]).exists())
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep\n")

    def test_hash_failure_happens_before_destination_parent_creation(self):
        (self.source(self.names[1]) / "scripts/client.py").write_text("changed\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "hash"):
            installer.install(self.root, self.destination, self.names[:1])
        self.assertFalse(self.destination.parent.exists())

    def test_extra_files_fail_closed(self):
        (self.source(self.names[0]) / "unexpected.txt").write_text("extra\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            installer.install(self.root, self.destination, self.names)
        self.assertFalse(self.destination.exists())

    def test_source_payload_symlink_is_rejected(self):
        path = self.source(self.names[0]) / "README.md"
        path.unlink()
        path.symlink_to(self.source(self.names[1]) / "README.md")
        with self.assertRaisesRegex(ValueError, "symlink"):
            installer.install(self.root, self.destination, self.names)

    def test_source_root_symlink_is_rejected(self):
        alias = self.base / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            installer.install(alias, self.destination, self.names)

    def test_destination_and_ancestor_symlinks_are_rejected(self):
        real = self.base / "real"
        real.mkdir()
        alias = self.base / "alias"
        alias.symlink_to(real, target_is_directory=True)
        for destination in (alias, alias / "skills"):
            with self.subTest(destination=destination), self.assertRaisesRegex(ValueError, "symlink"):
                installer.install(self.root, destination, self.names)
        self.assertEqual(list(real.iterdir()), [])

    def test_broken_destination_skill_symlink_is_not_overwritten(self):
        self.destination.mkdir(parents=True)
        target = self.destination / self.names[0]
        target.symlink_to(self.base / "missing")
        with self.assertRaises(FileExistsError):
            installer.install(self.root, self.destination, self.names)
        self.assertTrue(target.is_symlink())

    def test_source_and_destination_must_not_overlap(self):
        for destination in (self.root, self.root / "install", self.base):
            with self.subTest(destination=destination), self.assertRaisesRegex(ValueError, "overlap"):
                installer.install(self.root, destination, self.names)

    def test_common_path_prefix_is_not_overlap(self):
        destination = self.base / "repo-skills"
        installer.install(self.root, destination, self.names[:1])
        self.assertTrue((destination / self.names[0] / "SKILL.md").is_file())

    def test_selection_must_be_nonempty_known_and_unique(self):
        for names in ([], ["unknown"], ["../escape"], [self.names[0], self.names[0]]):
            with self.subTest(names=names), self.assertRaises(ValueError):
                installer.install(self.root, self.destination, names)
        self.assertFalse(self.destination.parent.exists())

    def test_catalog_traversal_is_rejected(self):
        self.document["plugins"][0]["files"]["../escape"] = "0" * 64
        self.save_catalog()
        with self.assertRaises(ValueError):
            installer.install(self.root, self.destination, self.names)
        self.assertFalse(self.destination.exists())

    def test_copy_failure_leaves_no_installed_skill_or_staging(self):
        with patch.object(installer.shutil, "copytree", side_effect=OSError("copy failed")):
            with self.assertRaises(OSError):
                installer.install(self.root, self.destination, self.names)
        self.assertFalse((self.destination / self.names[0]).exists())
        self.assertFalse(list(self.base.rglob(".neuraldeep-stage-*")))

    def test_cli_list_needs_no_catalog_or_bundle_arguments(self):
        result, output, errors = self.invoke(["--list"])
        self.assertEqual(result, 0, errors)
        for name in self.names:
            self.assertIn(name, output)
        self.assertFalse(self.destination.exists())

    def test_cli_requires_explicit_selection(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            installer.main(["--dest", str(self.destination)])
        self.assertEqual(raised.exception.code, 2)

    def test_cli_all_uses_real_bundle_layout(self):
        result, _, errors = self.invoke(["--all", "--dest", str(self.destination)])
        self.assertEqual(result, 0, errors)
        for name in self.names:
            self.assertTrue((self.destination / name / "SKILL.md").is_file())

    def test_cli_reports_unknown_name_without_writes(self):
        result, _, errors = self.invoke(["--skill", "unknown", "--dest", str(self.destination)])
        self.assertNotEqual(result, 0)
        self.assertIn("unknown", errors)
        self.assertFalse(self.destination.parent.exists())

    def test_cli_default_destination_is_shared_agents_directory(self):
        home = self.base / "home"
        with patch.object(installer.Path, "home", return_value=home):
            result, _, errors = self.invoke(["--skill", self.names[0]])
        self.assertEqual(result, 0, errors)
        self.assertTrue((home / ".agents/skills" / self.names[0] / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
