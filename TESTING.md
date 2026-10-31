# Verification evidence

## Initial packaging on 2026-10-31

Local Python is 3.14.4. Tests use the standard library and synthetic package fixtures. No NeuralDeep credentials were loaded and no provider API calls or billed operations were made.

| Check | Observed result |
|---|---|
| Installer focused suite | 19 tests passed |
| Full marketplace suite | 32 tests passed |
| Full suite with `LC_ALL=C PYTHONUTF8=0` | 32 tests passed |
| Full suite with `-X warn_default_encoding` | 32 tests passed |
| Public-source provenance comparison | All 108 runtime files matched their pinned public Git commits byte-for-byte |
| Packaged helper `--help` | All 15 passed |
| Folder installer against real packages | All 15 installed with matching hashes. A repeat installation was refused without overwriting |
| Parent distribution regression suite | 11 tests passed, no source mirrors changed |
| Claude Code 2.1.312 strict manifest validation | Marketplace and all 15 plugin manifests passed without errors, warnings or advice |
| Coddy 1.3.68 local-path marketplace import | Rejected as unsupported. This CLI requires a Git or HTTP source |

The source TESTING.md included inside each skill records upstream evidence. It is not a claim that all upstream suites were rerun during marketplace packaging. Runtime packages intentionally omit source development tests and rules.

## Test-first record

The initial catalog contract failed because scripts/catalog.py did not exist. After implementation, its 13 tests passed. The Cursor catalog extension first failed on the missing .cursor-plugin/marketplace.json entry, then passed after generation was added.

The installer was checked against the actual package layout before its final implementation. The 19-test suite rejected a prior implementation with incompatible arguments and path handling. After replacement, all 19 tests passed. Coverage includes package hashes before destination creation, unknown or duplicate selections, symlink and path traversal rejection, shared skills roots, no overwrite, batch collision preflight and staging cleanup after copy failure.

## Reproduce offline checks

Set TMPDIR to a private directory outside the checkout. The following POSIX commands clear inherited service credentials and make the Coddy environment file unavailable.

```bash
env -i PATH="$PATH" TMPDIR="$TMPDIR" CODDY_HOME=/nonexistent python3 -B scripts/catalog.py
env -i PATH="$PATH" TMPDIR="$TMPDIR" CODDY_HOME=/nonexistent python3 -B -m unittest discover -s tests
env -i PATH="$PATH" TMPDIR="$TMPDIR" CODDY_HOME=/nonexistent LC_ALL=C PYTHONUTF8=0 python3 -B -m unittest discover -s tests
env -i PATH="$PATH" TMPDIR="$TMPDIR" CODDY_HOME=/nonexistent python3 -X warn_default_encoding -B -m unittest discover -s tests
for skill in plugins/*/skills/*; do
  env -i PATH="$PATH" TMPDIR="$TMPDIR" CODDY_HOME=/nonexistent python3 -B "$skill/scripts/client.py" --help
done
git diff --check
```

The stale-file test intentionally emits an `Out of date` diagnostic while asserting that check mode does not rewrite files. This is expected output in a passing suite.

GitHub Actions runs the same offline checks on Python 3.10 and the latest 3.x. Local results above are not evidence of remote CI success before a workflow run completes.

## Native validation and limits

Claude validation used an isolated HOME and CLAUDE_CONFIG_DIR. The command was `claude plugin validate --strict --json` against the root marketplace and each plugin directory. It validates manifests. It does not by itself prove interactive skill activation or execute the service helper.

After publication, Claude Code added the public GitHub marketplace and installed neuraldeep-search@neuraldeep-skills successfully in a fresh temporary configuration. The enabled plugin's runtime files matched the pinned hashes. No interactive model session was started.

The initial public Coddy add and list checks succeeded and showed all 15 entries. Installation exposed an interoperability defect in marketplace 1.0.0. Coddy 1.3.68 rejects the explicit Codex source object with `{"source":"local","path":"..."}`. The regression test now requires bare relative string paths, a documented Codex form that Coddy classifies as an in-repository path. It failed against the old object form before the renderer was changed. Marketplace 1.0.1 changes only catalog representation, not skill versions or runtime bytes.

## Public Coddy correction checks

Coddy 1.3.68 fetched `viktor-drobek/neuraldeep-skills-marketplace@fix/coddy-marketplace-source` at code commit `ef5edff3a6a18a1f4bb9214e7f0100a7f58f57c2` with a fresh temporary HOME and CODDY_HOME.

- Marketplace add and list exposed all 15 entries.
- Native plugin installation succeeded for all 15 skills.
- `coddy skills list` discovered all 15 as enabled.
- All 108 installed runtime files matched the canonical hashes.
- All 15 installed helpers passed `--help`.
- Marketplace update listed all 15 and reported every installed skill up to date.

The first verification script stopped after installation because a plain substring check could not find a skill name wrapped across two table lines. The follow-up verifier reconstructed the name column, checked the already installed files and completed successfully. Installation was not repeated. No provider operations or interactive model sessions were used.

## Public CI

Both the initial publication and the source-form correction passed GitHub Actions on Python 3.10 and the latest 3.x. Each job ran the 32-test suite in three modes, catalog checks, all helper help commands and whitespace checks.

- [Initial publication run](https://github.com/viktor-drobek/neuraldeep-skills-marketplace/actions/runs/41237781139)
- [Coddy source correction run](https://github.com/viktor-drobek/neuraldeep-skills-marketplace/actions/runs/41238592125)

## Untested surfaces

Codex and Cursor CLIs were unavailable. Their catalogs and package layouts were checked against the official references in docs/COMPATIBILITY.md, not tested end to end in their UIs. No vendor directory submission or approval is claimed. Live provider quotas, billing and service availability were not tested.
