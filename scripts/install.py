#!/usr/bin/env python3
"""Install selected, hash-verified NeuralDeep skills without network access."""

import argparse
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile

from catalog import validate_bundle

ROOT = Path(__file__).resolve().parents[1]


def reject_symlinks(path):
    for candidate in (path, *path.parents):
        if candidate.is_symlink():
            raise ValueError("source or destination symlink is forbidden")


def install(root, destination, names):
    """Copy complete skills into a shared skills root, never replacing a skill."""
    root = Path(root).absolute()
    destination = Path(destination).expanduser().absolute()
    reject_symlinks(root / "catalog.json")
    reject_symlinks(destination)
    source_path, target_path = root.resolve(), destination.resolve()
    if target_path.is_relative_to(source_path) or source_path.is_relative_to(target_path):
        raise ValueError("source and destination overlap")
    document = validate_bundle(root)
    plugins = {plugin["name"]: plugin for plugin in document["plugins"]}
    if not names or len(set(names)) != len(names):
        raise ValueError("select one or more unique skill names")
    for name in names:
        if name not in plugins:
            raise ValueError(f"unknown skill name: {name}")
        target = destination / name
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"refusing to overwrite existing skill: {name}")
    if destination.exists() and not destination.is_dir():
        raise ValueError("destination must be a skills directory")

    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".neuraldeep-stage-", dir=destination) as temporary:
        staging = Path(temporary)
        for name in names:
            source = root / "plugins" / name / "skills" / name
            shutil.copytree(source, staging / name)
            for relative, expected in plugins[name]["files"].items():
                actual = hashlib.sha256((staging / name / relative).read_bytes()).hexdigest()
                if actual != expected:
                    raise ValueError(f"staged payload hash differs for {name}")
        for name in names:
            target = destination / name
            if target.exists() or target.is_symlink():
                raise FileExistsError(f"refusing to overwrite existing skill: {name}")
            (staging / name).rename(target)
    return list(names)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="list available skills without installing")
    group.add_argument("--skill", action="append", metavar="NAME", help="install one skill, repeatable")
    group.add_argument("--all", action="store_true", help="install all skills explicitly")
    parser.add_argument("--dest", type=Path, default=Path.home() / ".agents" / "skills",
                        help="shared skills directory, default ~/.agents/skills")
    args = parser.parse_args(argv)
    try:
        document = validate_bundle(ROOT)
        if args.list:
            for plugin in document["plugins"]:
                print(f"{plugin['name']}\t{plugin['version']}\t{plugin['description']}")
            return 0
        names = [plugin["name"] for plugin in document["plugins"]] if args.all else args.skill
        for name in install(ROOT, args.dest, names):
            print(f"Installed {name}")
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(f"Installation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
