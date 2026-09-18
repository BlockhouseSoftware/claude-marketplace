# Blockhouse Software Marketplace

The Claude Code plugin catalog for [Blockhouse Software](https://github.com/BlockhouseSoftware). Each plugin is pulled from its own product repository at a release tag; nothing is vendored here.

## Add the catalog

```text
claude plugin marketplace add BlockhouseSoftware/claude-marketplace
```

## Plugins

| Plugin | Install | Source |
| --- | --- | --- |
| **Trojaino** — experimental Claude Code inspection-session preflight. Installs disabled; requires explicit local runtime setup. | `claude plugin install trojaino@blockhouse-software` | [BlockhouseSoftware/trojaino](https://github.com/BlockhouseSoftware/trojaino) `plugins/trojaino` @ `v0.2.0` |

Trojaino's marketplace copy is inert by design: it ships without active hooks, and protection comes from the separately prepared personal plugin described in [its documentation](https://github.com/BlockhouseSoftware/trojaino/blob/main/docs/personal-plugin-delivery.md). Installing the catalog does not enable protection.

## Releasing a plugin update

1. Tag a release in the plugin's repository.
2. Bump `ref` for that plugin in `.claude-plugin/marketplace.json` and run `claude plugin validate .`.
3. Merge to `main`. Users pick up the new pin with `claude plugin marketplace update blockhouse-software` followed by `claude plugin update <plugin>@blockhouse-software`.

Only tags are used as `ref`; branches are never release artifacts.

## License

This catalog is licensed under the terms in `LICENSE`. Each plugin carries its own license, stated in its catalog entry.
