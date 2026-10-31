# NeuralDeep Skills Marketplace

Public skill packages by **Viktor Drobek** for Coddy, Claude Code, Codex, Cursor and compatible folder-based agents.

This is an independent community marketplace, not an official OpenAI or Anthropic directory listing. It distributes 15 guarded NeuralDeep skills from their public source repositories. See [the catalog](CATALOG.md) for versions, capabilities and source commits.

## Install with Coddy

```bash
coddy plugin marketplace add viktor-drobek/neuraldeep-skills-marketplace
coddy plugin marketplace list neuraldeep-skills
coddy plugin install neuraldeep-search@neuraldeep-skills
```

Replace `neuraldeep-search` with another catalog entry to install it individually. Start a new session after installation. Installation does not configure a model provider, add an MCP server or authorize a billed API call.

## Install with Claude Code

Run these commands in a Claude Code session.

```text
/plugin marketplace add viktor-drobek/neuraldeep-skills-marketplace
/plugin install neuraldeep-search@neuraldeep-skills
```

Claude namespaces the skill as `/neuraldeep-search:neuraldeep-search`. Each plugin contains one skill. You can also use the shell commands `claude plugin marketplace add` and `claude plugin install`.

## Install with Codex

```bash
codex plugin marketplace add viktor-drobek/neuraldeep-skills-marketplace
codex plugin marketplace list
```

Then open `/plugins` in a supported Codex client and choose the **NeuralDeep Skills** marketplace. Each entry is available for explicit installation, not installed by default. The portable plugin manifest is `plugin.json`, and the Codex catalog is `.agents/plugins/marketplace.json`.

This GitHub publication does not submit packages to the universal ChatGPT and Codex Plugins Directory. That is a separate review process. See [compatibility and verification](docs/COMPATIBILITY.md) for the tested and untested surfaces.

## Install with Cursor

Open **Customize** and use **From GitHub Repository** when that option is available. Import `https://github.com/viktor-drobek/neuraldeep-skills-marketplace`, then choose a plugin to install. The repository includes `.cursor-plugin/marketplace.json` and portable Agent Plugin manifests. Teams and Enterprise users can also import it as a team marketplace.

This does not list the packages in the official Cursor Marketplace. That requires a separate review. If repository import is unavailable in your client or plan, use the folder-based installer below.

## Folder-based installation

Clone and inspect the repository before running the offline installer. Python 3.10+ with the standard library is sufficient.

```bash
git clone https://github.com/viktor-drobek/neuraldeep-skills-marketplace.git
cd neuraldeep-skills-marketplace
python3 -B scripts/install.py --list
python3 -B scripts/install.py --skill neuraldeep-search --dest ~/.agents/skills
```

The shared `~/.agents/skills` directory is read by Cursor and Codex. Choose `~/.cursor/skills`, `~/.claude/skills` or `~/.coddy/skills` for a host-specific installation. For Coddy with a custom `CODDY_HOME`, use its `skills` subdirectory. Restart the agent or reload its skill discovery after copying files.

```bash
python3 -B scripts/install.py --all --dest ~/.coddy/skills
```

The installer checks package hashes before copying, requires an explicit selection and refuses existing skill directories. It never overwrites a local skill or modifies agent configuration. Updates through this installer require moving the old directory aside first. Native plugin updates should use the agent's plugin manager instead.

## Safety and credentials

Every skill uses its own guarded `scripts/client.py`. Read the installed `SKILL.md` and `STARTER_RELAY.md` before use. The helper, not the marketplace or installer, resolves credentials from its documented environment variable or Coddy environment file. Never paste keys into chat, store them in this repository or pass them in marketplace configuration.

Some operations remain deliberately blocked because quotas or spending bounds are not verified. A manifest does not enable them, and `--wallet-limit` cannot override unknown accounting. Supported wallet operations require explicit approval of the quoted cost. Treat `blocked` and `reconciliation_required` as stop conditions. Keep input files, state and artifacts in a private runtime directory outside the repository and plugin cache.

The packages contain no plugin hooks, bundled MCP servers or automatic API submissions. Upstream documentation is included unchanged and may describe source development files that are not part of a runtime package.

## Provenance and maintenance

`catalog.json` is the canonical inventory. Every entry records a public source URL, a full Git commit, the skill version and SHA-256 hashes for every packaged runtime file. Runtime bytes come from those public commits, not from private repository history. Only skill contracts, licenses, helpers and allowlisted runtime resources are packaged. Source development rules, CI, tests and Git metadata are excluded.

Do not hand-edit a vendored helper to fix behavior. Make the change in its owning source repository first, run the source tests, and update the package from the reviewed commit. Preserve its license, update the inventory and regenerate the host manifests. When runtime content changes, bump the source skill version so host caches can receive it. Bump the marketplace version for catalog-only edits.

```bash
python3 -B scripts/catalog.py --write
python3 -B scripts/catalog.py
python3 -B -m unittest discover -s tests
```

See [the contributor guide](AGENTS.md) and [verification evidence](TESTING.md). The Python development suite is offline. Native install smoke tests fetch public GitHub repositories and never submit provider jobs. Publishing this catalog does not validate live provider quotas or authorize a live test.

## License

The marketplace tooling is MIT licensed. Every skill retains its upstream MIT license inside its skill directory. Attribution and source links are preserved.
