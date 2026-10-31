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

Public Coddy marketplace add, list and install checks require the GitHub repository to exist. They had not run at the time this initial publication snapshot was prepared. They must use a private temporary HOME and CODDY_HOME and must not modify an operator's real skill installation.

Codex and Cursor CLIs were unavailable. Their catalogs and package layouts were checked against the official references in docs/COMPATIBILITY.md, not tested end to end in their UIs. No vendor directory submission or approval is claimed. Live provider quotas, billing and service availability were not tested.
