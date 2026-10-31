"""Offline contracts for generated marketplace catalogs and skill packages."""

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("marketplace_catalog", ROOT / "scripts" / "catalog.py")
catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def fixture(root):
    skill = root / "plugins" / "neuraldeep-example" / "skills" / "neuraldeep-example"
    skill.mkdir(parents=True)
    files = {
        "SKILL.md": "---\nname: neuraldeep-example\ndescription: Safe fixture\nmetadata:\n  version: 1.2.3\n---\n\nUse the guarded helper.\n",
        "scripts/client.py": "print('offline fixture')\n",
        "README.md": "# Fixture\n",
        "STARTER_RELAY.md": "Stop on blocked.\n",
        "TESTING.md": "Synthetic test only.\n",
        "LICENSE": "MIT fixture\n",
    }
    for name, text in files.items():
        path = skill / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    entry = {
        "name": "neuraldeep-example", "version": "1.2.3", "description": "Safe fixture",
        "source": "https://github.com/viktor-drobek/neuraldeep-example.git",
        "commit": "a" * 40,
        "files": {name: hashlib.sha256(text.encode("utf-8")).hexdigest() for name, text in files.items()},
    }
    document = {"name": "neuraldeep-skills", "version": "1.0.0", "plugins": [entry]}
    write_json(root / "catalog.json", document)
    return document, skill


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.document, self.skill = fixture(self.root)

    def save(self):
        write_json(self.root / "catalog.json", self.document)

    def test_valid_bundle_has_matching_source_version_and_hashes(self):
        self.assertEqual(catalog.validate_bundle(self.root), self.document)

    def test_generated_catalogs_have_same_local_sources_and_available_policy(self):
        generated = catalog.render(self.root)
        claude = json.loads(generated[".claude-plugin/marketplace.json"])
        codex = json.loads(generated[".agents/plugins/marketplace.json"])
        self.assertEqual(claude["name"], codex["name"])
        self.assertEqual(claude["plugins"][0]["source"], "./plugins/neuraldeep-example")
        self.assertEqual(codex["plugins"][0]["source"], {
            "source": "local", "path": "./plugins/neuraldeep-example"})
        self.assertEqual(codex["plugins"][0]["policy"], {
            "installation": "AVAILABLE", "authentication": "ON_INSTALL"})
        self.assertEqual(claude["owner"]["name"], "Viktor Drobek")
        cursor = json.loads(generated[".cursor-plugin/marketplace.json"])
        self.assertEqual(cursor, claude)
        self.assertIn("neuraldeep-example", generated["CATALOG.md"])
        self.assertIn("/plugin install neuraldeep-example --marketplace viktor-drobek/neuraldeep-skills-marketplace",
                      generated["plugins/neuraldeep-example/README.md"])

    def test_portable_and_claude_manifests_share_identity_and_no_hooks_or_mcp(self):
        generated = catalog.render(self.root)
        portable = json.loads(generated["plugins/neuraldeep-example/plugin.json"])
        claude = json.loads(generated["plugins/neuraldeep-example/.claude-plugin/plugin.json"])
        self.assertEqual(portable["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")
        for key in ("name", "version", "description", "author", "license"):
            self.assertEqual(portable[key], claude[key])
        for manifest in (portable, claude):
            self.assertNotIn("hooks", manifest)
            self.assertNotIn("mcpServers", manifest)
        self.assertNotIn("skills", portable)

    def test_changed_payload_fails_before_rendering(self):
        (self.skill / "scripts/client.py").write_text("changed\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "hash"):
            catalog.render(self.root)

    def test_unlisted_payload_is_rejected(self):
        (self.skill / "unexpected.txt").write_text("not tracked\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "file set"):
            catalog.validate_bundle(self.root)

    def test_missing_required_runtime_contract_is_rejected(self):
        del self.document["plugins"][0]["files"]["STARTER_RELAY.md"]
        (self.skill / "STARTER_RELAY.md").unlink()
        self.save()
        with self.assertRaisesRegex(ValueError, "required"):
            catalog.validate_bundle(self.root)

    def test_source_must_be_public_owner_github_url(self):
        for source in ("file:///private/repo", "https://user:token@github.com/viktor-drobek/neuraldeep-example.git",
                       "https://github.com/other/neuraldeep-example.git"):
            with self.subTest(source=source):
                self.document["plugins"][0]["source"] = source
                self.save()
                with self.assertRaises(ValueError):
                    catalog.validate_bundle(self.root)

    def test_traversal_or_duplicate_names_are_rejected(self):
        self.document["plugins"][0]["name"] = "../escape"
        self.save()
        with self.assertRaises(ValueError):
            catalog.validate_bundle(self.root)
        self.document["plugins"][0]["name"] = "neuraldeep-example"
        self.document["plugins"].append(dict(self.document["plugins"][0]))
        self.save()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            catalog.validate_bundle(self.root)

    def test_file_paths_stay_inside_bundle(self):
        self.document["plugins"][0]["files"]["../outside"] = "0" * 64
        self.save()
        with self.assertRaises(ValueError):
            catalog.validate_bundle(self.root)

    def test_payload_symlink_is_rejected(self):
        path = self.skill / "README.md"
        content = path.read_text(encoding="utf-8")
        path.unlink()
        outside = self.root / "outside.md"
        outside.write_text(content, encoding="utf-8")
        path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlink"):
            catalog.validate_bundle(self.root)

    def test_invalid_sha_or_version_is_rejected(self):
        self.document["plugins"][0]["commit"] = "main"
        self.save()
        with self.assertRaises(ValueError):
            catalog.validate_bundle(self.root)
        self.document["plugins"][0]["commit"] = "a" * 40
        self.document["plugins"][0]["version"] = "2.0.0"
        self.save()
        with self.assertRaisesRegex(ValueError, "version"):
            catalog.validate_bundle(self.root)

    def test_generated_files_are_checked_without_rewriting(self):
        self.assertTrue(catalog.write_or_check(self.root, write=True))
        self.assertTrue(catalog.write_or_check(self.root, write=False))
        path = self.root / ".claude-plugin/marketplace.json"
        path.write_text("{}\n", encoding="utf-8")
        self.assertFalse(catalog.write_or_check(self.root, write=False))
        self.assertEqual(path.read_text(encoding="utf-8"), "{}\n")


class PublishedBundleTests(unittest.TestCase):
    def test_all_fifteen_bundles_validate_and_generated_files_are_current(self):
        document = catalog.validate_bundle(ROOT)
        self.assertEqual(len(document["plugins"]), 15)
        self.assertTrue(catalog.write_or_check(ROOT, write=False))


if __name__ == "__main__":
    unittest.main()
