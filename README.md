# Blockhouse Software Marketplace

The Claude Code plugin catalog for [Blockhouse Software](https://github.com/BlockhouseSoftware). Each plugin is pulled from its own product repository at a release tag; nothing is vendored here.

## Add the catalog

```text
claude plugin marketplace add BlockhouseSoftware/claude-marketplace
```

## Plugins

| Plugin | Install | Source |
| --- | --- | --- |
| **Trojaino** — install gate: scans npm, PyPI, GitHub and plugin sources before Claude installs them. Needs Python 3.11+ as `python3`. | `claude plugin install trojaino@blockhouse-software` | [BlockhouseSoftware/trojaino](https://github.com/BlockhouseSoftware/trojaino) `plugins/trojaino` @ `v0.3.0` |

Trojaino's marketplace copy is inert by design: it ships without active hooks, and protection comes from the separately prepared personal plugin described in [its documentation](https://github.com/BlockhouseSoftware/trojaino/blob/main/docs/personal-plugin-delivery.md). Installing the catalog does not enable protection.

## Releasing a plugin update

1. Tag a release in the plugin's repository.
2. Bump `ref` for that plugin in `.claude-plugin/marketplace.json`.
3. Open a pull request. CI runs `scripts/check_catalog.py`, which fetches the pinned
   tag from the plugin's own repository and fails if the catalog advertises a version,
   licence, description, homepage or repository the release does not actually carry —
   including the case where `ref` points at the wrong release.
4. Merge to `main`. Users pick up the new pin with `claude plugin marketplace update blockhouse-software`
   followed by `claude plugin update <plugin>@blockhouse-software`.

Only release tags are accepted as `ref`; a branch name is rejected, because a branch is
not an immutable release. Run `python scripts/check_catalog.py` locally before pushing,
or `--offline` to skip the network fetch. `claude plugin validate .` remains a useful
extra check against the CLI's own schema.

## License

This catalog (the `marketplace.json` and this README) is MIT licensed; see `LICENSE`. Each plugin carries its own license, stated in its catalog entry — Trojaino is AGPL-3.0-only.
