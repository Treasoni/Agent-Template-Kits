# Quality and Governance Improvements Design

## Goal

Make the template repository safer to publish and easier to maintain without
changing its existing installation interfaces or supported profile layouts.

## Scope

1. Keep `.env.example` limited to actual environment inputs.
2. Add an MIT license and a documented tag-based release procedure.
3. Make public-document coverage derive from the available component catalog.
4. Validate every built-in profile contract before installers run.
5. Add regression coverage for the documentation, profile, and secret-quality
   guards.

## Design

### Public governance

`LICENSE` is the authoritative MIT license. `RELEASING.md` defines the
repository release contract: update `CHANGELOG.md`, run the full validation
chain, create a signed-or-annotated `vX.Y.Z` tag, then publish it. No current
version number or retrospective tag is invented by this change.

### Documentation contract

The README remains the quick-start entry point and the detailed Markdown guide
is the sole long-form guide. The unreferenced static HTML copy is removed so it
cannot drift independently. `scripts/check-docs.py` discovers canonical
component identifiers from `scripts/install.py` and verifies that both public
documents mention each one. This removes the manually maintained two-item list
and the third duplicate document.

### Profile contract

`scripts/validate-profiles.py` reads the scalar profile files using the same
format that installers accept. It verifies required keys, permitted keys,
unique names, cross-platform-safe relative paths, profile-file-name/name agreement, and
cross-field path consistency. Scripts, hooks, and hook configuration belong to
`agent_dir`; registry and prompt-cache rules belong to `rules_dir`. Both rules
and skills are deliberately independent because Cline uses root-level
`.clinerules` and Codex uses `.agents/skills` alongside `.codex`. It
intentionally validates rather than replaces the independent Python and shell
parsers, so standalone copies keep working.

### Tests and validation

A new quality-guard test module exercises the documentation checker, profile
validator, and secret detector with a synthetic safe fixture and a synthetic
credential fixture. `scripts/validate.sh` compiles and runs the new profile
validator before the full test suite.

## Error Handling

The profile validator reports every invalid file and exits non-zero. The
documentation checker reports each missing component-document pair. Secret
tests assert only a rule identifier and never print a simulated credential.

## Compatibility

No existing installer options, profile field names, supported platforms, or
default component selections change. The profile validator accepts the current
built-in profile schema, including empty hook-related fields for agents that do
not support hooks.

## Success Criteria

- `bash scripts/validate.sh` passes.
- The working-tree secret scan passes.
- Invalid profiles and missing public component references fail their focused
  checks.
- Current public documents and all shipped profile contracts validate.
