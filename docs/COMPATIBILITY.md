# Compatibility and reference contracts

## Host formats

| Host | Marketplace catalog | Package manifest | Skill discovery |
|---|---|---|---|
| Coddy | Claude-compatible marketplace catalog | Claude-compatible plugin manifest | Packaged skills directory |
| Claude Code | `.claude-plugin/marketplace.json` | `.claude-plugin/plugin.json` | `skills/<name>/SKILL.md` |
| Codex | `.agents/plugins/marketplace.json` | Root `plugin.json` | `skills/<name>/SKILL.md` |
| Cursor | `.cursor-plugin/marketplace.json` | Root `plugin.json` | Portable Agent Plugin or folder-based skill |
| Folder-based agents | No marketplace protocol assumed | Not required | Copy the complete skill directory into the host's documented skills root |

The root portable manifests target Agent Plugins 1.0.0. They contain only common metadata and use the default `skills/` layout. Claude compatibility manifests are separate, without the portable `$schema` field. The Cursor catalog follows the documented multi-plugin repository format and points at the same local package directories. No absolute paths, paths outside a plugin, plugin hooks or MCP configuration are needed.

Native catalogs have identical package names and relative sources. The Codex policy is `AVAILABLE` with `ON_INSTALL` authentication, following its documented marketplace schema. There are no MCP servers requiring marketplace authentication. Service keys remain the guarded helper's responsibility, not the plugin installer's responsibility.

## Codex and Cursor UI flows

For Codex, add the GitHub marketplace with `codex plugin marketplace add`, then use `/plugins` to choose packages. This repository is not automatically listed in the universal ChatGPT and Codex Plugins Directory. The offline folder installer is an alternative for Codex clients that use `~/.agents/skills`.

For Cursor, use **Customize**, import a GitHub repository when that option is available, and supply `https://github.com/viktor-drobek/neuraldeep-skills-marketplace`. Teams and Enterprise users can use the documented team-marketplace import. Official public Cursor Marketplace listing requires a separate manual submission and review. The folder installer works independently of those listing and team features.

## Verification boundary

Manifest validation, package hash checks and helper CLI checks are offline. Native catalog and install smoke tests use private temporary agent homes and perform no model inference or NeuralDeep API operations. See TESTING.md for commands and outcomes actually observed.

Codex and Cursor runtime behavior is not claimed verified when their CLIs or UIs are unavailable. Conformance with the documented package layout does not prove end-to-end skill activation in every version. Review the installed skill before giving it credentials or approving any spending.

The original SKILL.md files and runtime helpers are preserved byte-for-byte. They retain upstream metadata extensions and safety instructions. Portable plugin-manifest validation is not a claim of strict validation by every third-party Agent Skills linter. No package is submitted to a vendor directory as part of publishing this GitHub repository.

## References

The following public references were read during initial packaging on 2026-10-31.

- [OpenAI plugin packaging and local marketplaces](https://developers.openai.com/plugins/build/plugins)
- [Agent Plugins 1.0.0 manifest schema](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json)
- [Claude marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference)
- [Claude manifest reference](https://code.claude.com/docs/en/plugins/manifest-reference)
- [Cursor plugins](https://cursor.com/docs/plugins)
- [Cursor plugin reference](https://cursor.com/docs/reference/plugins)
- [Cursor's official marketplace template](https://github.com/cursor/plugin-template/blob/main/.cursor-plugin/marketplace.json)
- [Cursor skill directories](https://cursor.com/docs/skills)
- [Agent Skills specification](https://agentskills.io/specification)

Coddy command syntax is verified against the installed CLI, not inferred from another agent's format. Its `plugin --help` lists marketplace add, list, update and remove, and per-plugin installation. See the tested version and outcomes in TESTING.md.
