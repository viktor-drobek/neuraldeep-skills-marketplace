# NeuralDeep Skills Marketplace

## Scope

This repository owns plugin packaging, native marketplace manifests and an offline folder installer. It does not own NeuralDeep service behavior. Runtime payloads under `plugins/*/skills/*/` are pinned copies from public per-skill repositories.

## Delivery

- Work on a feature branch and use a PR for changes after initial publication. Do not push to main or merge without the owner's decision.
- Use RED-GREEN-REFACTOR for observable changes. Write a failing offline test, make the smallest passing change, then refactor.
- Keep Python tooling compatible with Python 3.10+ and the standard library only.
- Make helper behavior changes in the source skill repository first. Never bypass a guard in a vendored package.
- Record only checks actually run in TESTING.md. Never imply that offline validation proves provider availability or quotas.
- Commit as Viktor Drobek <viktor@drobek.online> for both author and committer.

## Packaging

`catalog.json` is the inventory for both native catalogs and every plugin manifest. Run `python3 -B scripts/catalog.py --write` after updating it. Do not hand-edit generated manifests or CATALOG.md.

Preserve the source skill's version, runtime bytes and license. Keep every plugin self-contained under its own directory. Do not use symlinks to files outside a plugin. Only publish reviewed public source commits. Do not export a parent repository or its Git history.

Portable plugins use root plugin.json and skills/. Claude compatibility metadata lives in .claude-plugin/plugin.json. No plugin hooks or MCP servers are part of these packages. The root CLAUDE.md symlink provides this same baseline for Claude Code development. Coddy and Codex read AGENTS.md. Cursor users can attach this contributor guide while editing the marketplace. Installing a runtime skill does not install source development rules.

## Safety

Never inspect, log or commit credentials, .env contents, runtime state, recordings or provider artifacts. The installer and catalog generator must not resolve service credentials or contact NeuralDeep. Keep unknown quotas and accounting fail-closed. Never retry uncertain submissions or weaken blocked outcomes. Preserve upstream instructions and provenance.

Reject path traversal, source or destination symlinks, hash mismatches and attempts to overwrite an existing skill. Test failure paths before changing installer behavior. Keep staging data in private temporary directories and set TMPDIR outside the checkout.

## Verification

Run these commands with credentials removed, a nonexistent CODDY_HOME and TMPDIR set to a private external directory.

```bash
python3 -B scripts/catalog.py
python3 -B -m unittest discover -s tests
LC_ALL=C PYTHONUTF8=0 python3 -B -m unittest discover -s tests
python3 -X warn_default_encoding -B -m unittest discover -s tests
for s in plugins/*/skills/*; do python3 -B "$s/scripts/client.py" --help; done
git diff --check
```

Validate native manifests with an isolated host configuration when a CLI is available. Do not change the operator's global settings. No live API submission is part of development verification. See docs/COMPATIBILITY.md for reference URLs and host-specific limits.
