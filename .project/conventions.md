# Conventions

<!--
Project doc (.project/). Cite as `.project/conventions.md#<section>`. This is the file the
implementer and coherence-reviewer lean on hardest — "reuse conventions" and
"does this fit the app?" both resolve here. Prefer pointing at a canonical
exemplar in the codebase (path:line) over prose. Keep ## headings stable — they
are citation anchors.
-->

## Naming
Files, types, functions, tests, branches.
> [TBD] — e.g. "PascalCase types; `*ViewModel` suffix; tests mirror the unit name + `Tests`; branches `issue/<n>-<slug>`." 🔴

## File & folder layout
Where things go, and the shape of a feature.
> Flask single-module app (`application.py` at repo root, ~86K — no blueprint/package split); `templates/` (Jinja2 pages), `static/` (css/images/js); `lambda/` (standalone Lambda function sources); `scripts/` (one-off migration/maintenance tooling, not part of the deployed app).

## Test patterns
Where tests live, how they're named, fixtures/factories, and what a good test looks like.
> [TBD] 🔴

## Canonical exemplars (mirror these)
The reference implementations to copy when building something similar. Point at real code.

| For… | Mirror | Notes |
|---|---|---|
| [TBD] (e.g. a new list page) | [TBD path:line] | [TBD] | 🔴
| [TBD] (e.g. a service call) | [TBD path:line] | [TBD] | 🔴

## Commits & PRs
Message format and PR expectations.
> [TBD] 🔴

## Versioning
Does the project follow semantic versioning? If so, **where the version lives** (e.g. `pyproject.toml`, `package.json`, `*.csproj`, a `VERSION` file) and the **bump cadence** (per feature / milestone). When semver is on, `milestone-driver` applies the bump per PR and `milestone-feeder` names milestones as versions so the driver can derive the target.
> None — the project is not versioned; no VERSION file, package version field, or CHANGELOG found.
