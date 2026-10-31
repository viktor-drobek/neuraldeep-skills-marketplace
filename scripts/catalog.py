#!/usr/bin/env python3
"""Validate pinned skill packages and render native plugin catalogs offline."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
OWNER = {"name": "Viktor Drobek", "email": "viktor@drobek.online"}
SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
REQUIRED = {"SKILL.md", "README.md", "STARTER_RELAY.md", "TESTING.md", "LICENSE", "scripts/client.py"}
DIRECTORIES = {"scripts", "references", "examples", "assets", "templates", "resources"}
NAME = re.compile(r"neuraldeep-[a-z0-9]+(?:-[a-z0-9]+)*")
VERSION = re.compile(r"\d+\.\d+\.\d+")


def json_text(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def skill_metadata(text):
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError("missing skill frontmatter")
    head = text[4:text.index("\n---\n", 4)]
    name = re.search(r"^name:\s*([^\n]+)$", head, re.M)
    metadata = re.search(r"^metadata:\n((?:[ \t]+[^\n]*\n?)+)", head, re.M)
    version = re.search(r"^  version:\s*([^\n]+)$", metadata[1], re.M) if metadata else None
    if not name or not version:
        raise ValueError("missing skill name or metadata.version")
    return name[1].strip().strip("\"'"), version[1].strip().strip("\"'")


def safe_file_path(value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("invalid file path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in value.split("/")):
        raise ValueError("file path escapes bundle")
    if any(part.startswith(".") for part in path.parts):
        raise ValueError("hidden files are not runtime payloads")
    if value not in REQUIRED and (len(path.parts) < 2 or path.parts[0] not in DIRECTORIES):
        raise ValueError("file path is outside the runtime allowlist")
    return path


def validate_bundle(root):
    root = Path(root)
    document = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    if document.get("name") != "neuraldeep-skills" or not VERSION.fullmatch(document.get("version", "")):
        raise ValueError("invalid marketplace identity")
    plugins = document.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        raise ValueError("catalog needs plugins")
    seen = set()
    for plugin in plugins:
        name = plugin.get("name", "")
        if not NAME.fullmatch(name):
            raise ValueError("invalid plugin name")
        if name in seen:
            raise ValueError("duplicate plugin name")
        seen.add(name)
        if plugin.get("source") != f"https://github.com/viktor-drobek/{name}.git":
            raise ValueError("source must be the public per-skill GitHub repository")
        if not re.fullmatch(r"[a-f0-9]{40}", plugin.get("commit", "")):
            raise ValueError("source commit must be a full SHA")
        if not VERSION.fullmatch(plugin.get("version", "")):
            raise ValueError("invalid plugin version")
        if not isinstance(plugin.get("description"), str) or not plugin["description"].strip():
            raise ValueError("missing plugin description")
        files = plugin.get("files")
        if not isinstance(files, dict) or not REQUIRED.issubset(files):
            raise ValueError("missing required runtime contracts")
        skill = root / "plugins" / name / "skills" / name
        for parent in (root / "plugins", skill.parent.parent, skill.parent, skill):
            if parent.is_symlink():
                raise ValueError("bundle symlink is forbidden")
        actual = set()
        for path in skill.rglob("*"):
            if path.is_symlink():
                raise ValueError("payload symlink is forbidden")
            if path.is_file():
                actual.add(path.relative_to(skill).as_posix())
        if actual != set(files):
            raise ValueError(f"payload file set differs for {name}")
        for relative, expected in files.items():
            safe_file_path(relative)
            if not isinstance(expected, str) or not re.fullmatch(r"[a-f0-9]{64}", expected):
                raise ValueError("invalid payload hash")
            if hashlib.sha256((skill / relative).read_bytes()).hexdigest() != expected:
                raise ValueError(f"payload hash differs for {name}")
        declared_name, declared_version = skill_metadata((skill / "SKILL.md").read_text(encoding="utf-8"))
        if declared_name != name or declared_version != plugin["version"]:
            raise ValueError(f"skill name or version differs for {name}")
    return document


def render(root):
    document = validate_bundle(root)
    claude_plugins, codex_plugins, output = [], [], {}
    for plugin in document["plugins"]:
        name = plugin["name"]
        path = f"./plugins/{name}"
        metadata = {
            "name": name, "version": plugin["version"], "description": plugin["description"],
            "author": OWNER, "homepage": plugin["source"].removesuffix(".git"),
            "repository": plugin["source"], "license": "MIT", "keywords": ["neuraldeep", name],
        }
        output[f"plugins/{name}/plugin.json"] = json_text({"$schema": SCHEMA, **metadata})
        output[f"plugins/{name}/.claude-plugin/plugin.json"] = json_text(metadata)
        output[f"plugins/{name}/README.md"] = (
            f"# {name}\n\n{plugin['description']}\n\n"
            f"The skill and its guarded helper are in [skills/{name}/](skills/{name}/README.md).\n\n"
            f"Source commit [{plugin['commit']}]({plugin['source'].removesuffix('.git')}/commit/{plugin['commit']}).\n"
            "Runtime files are copied unchanged from that public source. See the root catalog.json for SHA-256 hashes.\n"
            "Installing this package does not authorize paid API calls or override blocked operations.\n"
            f"\n```text\n/plugin install {name} --marketplace viktor-drobek/neuraldeep-skills-marketplace\n```\n"
            f"\n```bash\ncoddy plugin install {name}@neuraldeep-skills\n```\n"
        )
        claude_plugins.append({
            "name": name, "source": path, "version": plugin["version"],
            "description": plugin["description"], "category": "productivity", "license": "MIT",
        })
        codex_plugins.append({
            "name": name, "source": {"source": "local", "path": path},
            "description": plugin["description"], "category": "Productivity",
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        })
    output[".claude-plugin/marketplace.json"] = json_text({
        "name": document["name"], "owner": OWNER,
        "metadata": {"version": document["version"], "description": "Guarded NeuralDeep skills by Viktor Drobek."},
        "plugins": claude_plugins,
    })
    output[".agents/plugins/marketplace.json"] = json_text({
        "name": document["name"], "interface": {"displayName": "NeuralDeep Skills"},
        "plugins": codex_plugins,
    })
    output[".cursor-plugin/marketplace.json"] = output[".claude-plugin/marketplace.json"]
    rows = ["# Skill catalog", "", "All runtime files are pinned to public source commits.", "",
            "| Skill | Version | Capabilities and limits | Source commit |",
            "|---|---|---|---|"]
    for plugin in document["plugins"]:
        source = plugin["source"].removesuffix(".git")
        commit = plugin["commit"]
        rows.append(f"| [{plugin['name']}](plugins/{plugin['name']}/README.md) | {plugin['version']} | "
                    f"{plugin['description']} | [{commit[:12]}]({source}/commit/{commit}) |")
    output["CATALOG.md"] = "\n".join(rows) + "\n"
    return output


def write_or_check(root, write=False):
    root = Path(root)
    clean = True
    generated = render(root)
    for relative in generated:
        path = root / relative
        for candidate in (path, *path.parents):
            if candidate.is_symlink():
                raise ValueError("generated file or parent symlink is forbidden")
            if candidate == root:
                break
    for relative, expected in generated.items():
        path = root / relative
        if path.is_file() and path.read_text(encoding="utf-8") == expected:
            continue
        clean = False
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
        else:
            print(f"Out of date: {relative}", file=sys.stderr)
    return clean or write


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="regenerate manifests after validating every bundle")
    args = parser.parse_args(argv)
    try:
        if not write_or_check(ROOT, write=args.write):
            return 1
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(f"Catalog validation failed: {exc}", file=sys.stderr)
        return 1
    print("Catalogs and pinned packages are consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
