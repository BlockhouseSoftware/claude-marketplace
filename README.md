# Blockhouse Software Marketplace

The Claude Code plugin catalog for [Blockhouse Software](https://github.com/BlockhouseSoftware). Each plugin is pulled from its own product repository at a release tag; nothing is vendored here.

## Install Trojaino

Inside **Claude Code 2.1.274 or newer**, run:

```text
/plugin marketplace add BlockhouseSoftware/claude-marketplace
/plugin install trojaino@blockhouse-software
```

Trojaino needs **Python 3.11+ available as `python3`**. No pip installation or prepared personal plugin is needed. The plugin ships active SessionStart and PreToolUse hooks.

The current catalog release is 0.3.0. For that release, restart Claude and check for hook errors; `/hooks` alone does not prove Python can run. Starting with **0.3.1**, restart Claude and run **`/trojaino:doctor`**. It reports **Ready** or explains what needs attention, including old prepared-plugin hooks. See [installation, prerequisites and migration](https://github.com/BlockhouseSoftware/trojaino/blob/main/docs/plugin-installation.md).

Trojaino checks named npm, Python, GitHub and plugin sources before Claude installs them. Unscannable sources require your approval. Only named packages are scanned, not dependencies. A clean static scan is not a safety guarantee.

From a terminal, use `claude plugin` instead of `/plugin` for these commands.

## Update

Inside Claude Code:

```text
/plugin marketplace update blockhouse-software
/plugin update trojaino@blockhouse-software
```

Restart Claude. On 0.3.1 or newer, run `/trojaino:doctor` again. This replaces the obsolete prepared-plugin delivery workflow.

## Releasing a plugin update

1. Tag a release in the plugin's repository.
2. Run `python scripts/promote_release.py v0.3.1` (substitute the new release tag). It verifies the tag, prepares its full commit SHA and mirrored metadata, and refuses a mismatched or missing release before writing. Never move an existing release tag.
3. Open a pull request. CI runs `scripts/check_catalog.py`, which fetches the pinned
   tag from the plugin's own repository, requires it to resolve to `sha`, and reads that exact commit. It fails if the catalog advertises a version,
   licence, description, homepage or repository the release does not actually carry —
   including the case where `ref` points at the wrong release.
4. Merge to `main`. Users pick up the new pin with `claude plugin marketplace update blockhouse-software`
   followed by `claude plugin update <plugin>@blockhouse-software`.

Only release tags are accepted as `ref`. Tags name versions; `sha` binds installation to an immutable commit. Run `python scripts/check_catalog.py` locally before pushing,
or `--offline` to skip the network fetch. `claude plugin validate .` remains a useful
extra check against the CLI's own schema.

After publishing a product release and promoting its catalog pin, run the product's **Install gate** workflow with **public_install** enabled. It exercises the real public installation on the supported Claude versions. Candidate CI also verifies the refresh/update sequence using a local marketplace.

## License

This catalog (the `marketplace.json` and this README) is MIT licensed; see `LICENSE`. Each plugin carries its own license, stated in its catalog entry — Trojaino is AGPL-3.0-only.
