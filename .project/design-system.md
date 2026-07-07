# Design system

<!--
Project doc (.project/). Cite as `.project/design-system.md#<section>`. Machine-readable
design tokens live in `tokens.json` alongside this file. Absent or all-[TBD] →
no design-lens grounding (design-reviewer / coherence-reviewer / wireframing
skip it). Skip this file entirely for repos with no UI surface. Keep ## headings
stable — they are citation anchors.
-->

## Design tokens
Canonical color, type, spacing, and radius scales. Source of truth is `tokens.json`; describe intent and usage here.
> No documented token scale (color/type/spacing/radius) — inherited from Flask-Bootstrap 3.3.7.1 (Bootstrap 3-era) defaults plus ad-hoc overrides in `static/css`. 🔴 No source-of-truth token scale exists; `tokens.json` is left [TBD].

## Component inventory
The canonical components and where they live. New UI reuses these before introducing a one-off.

| Component | Location | Use for |
|---|---|---|
| Component | Location | Use for |
|---|---|---|
| index | templates/index.html | Home / landing page |
| search_results | templates/search_results.html | Card search results |
| advanced | templates/advanced.html | Advanced search form |
| card | templates/card.html | Single card detail view |
| sets | templates/sets.html | Card sets listing |
| deck_builder | templates/deck_builder.html | Deck building UI |
| decks | templates/decks.html | Saved decks listing |
| api | templates/api.html | Public API documentation page |
| resources | templates/resources.html | Community resources page |
| feedback | templates/feedback.html | User feedback form |
| syntax | templates/syntax.html | Search syntax help |
| navbar | templates/navbar.html | Shared navigation partial |
| base | templates/base.html | Shared page layout/base template |

## Layout & responsive rules
Grid, breakpoints, spacing rhythm, density.
> Bootstrap 3's 12-column responsive grid; no documented custom breakpoints or density rules found in `static/css`.

## Required states
Every interactive surface must handle these explicitly.
- **Empty:** [TBD] 🔴
- **Loading:** [TBD] 🔴
- **Error:** [TBD] 🔴
- **Disabled:** [TBD] 🔴

## Accessibility baseline
The standard you hold, plus contrast, focus, target size, and semantics expectations.
> [TBD] — e.g. "WCAG 2.2 AA; visible focus on all interactive elements; min 44px touch targets." 🔴

## Voice & microcopy
Tone for labels, errors, and empty states.
> [TBD] 🔴
