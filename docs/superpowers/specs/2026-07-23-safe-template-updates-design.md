# Safe Template Updates Design

## Goal

Let projects installed through `scripts/install.py` preview and apply template
updates without overwriting user changes silently.

## State Contract

Each successful unified installation writes
`.agent-template-kits/install-state.json` in the target project. The file
contains a schema version, the template source version, selected profiles and
components, and SHA-256 fingerprints for files changed by the installer. The
state directory is updater-owned and is never included in managed-file scans.

## Update Contract

`python3 scripts/install.py update --target TARGET` is read-only by default.
It copies the target to a temporary directory, runs the same component
installers there with explicit overwrite/force options, and compares the
candidate with the real target.

For every candidate change, the updater classifies the real target path as:

- safe: recorded by the last installation and its hash is unchanged, or the
  path is newly created;
- conflict: a recorded path has changed or disappeared, or an unrecorded path
  would be replaced or deleted.

The default command reports the plan and exits non-zero when conflicts exist.
`--accept PATH` may be repeated to approve precise conflicting paths.
`--apply --yes` creates a timestamped backup under
`.agent-template-kits/backups/`, executes the real update, compares changed
files with the temporary candidate, and writes fresh state only after that
comparison succeeds.

## Component Compatibility

The unified installer keeps its existing option-based interface. Its new
`update` command is detected before normal argument parsing, so old commands
remain valid. Prompt-cache installation gains an explicit `--overwrite` option
for updater use; normal installation continues to preserve existing rules,
assets, and skills by default.

## Source Version

The source version is `git describe --tags --always --dirty` from the template
checkout. The updater never runs `git pull`, fetches a remote, or changes a
target project's Git state. Users select a trusted release tag before running
the updater.

## Success Criteria

- A new unified install writes state with managed file fingerprints.
- Update dry-runs never write the target project.
- User-modified managed files block update unless individually accepted.
- Accepted files are backed up before replacement.
- Existing install commands and default prompt-cache preservation behavior
  remain unchanged.
