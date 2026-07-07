# Design philosophy

<!--
Part of your project docs (.project/). Tools read and cite this file as
`.project/design-philosophy.md#<section>`. Fill every [TBD]. A section left as
[TBD] is treated as "not specified" — tools fall back to inferred repo
convention rather than ground on a placeholder. Humans own this file; tools may
*propose* changes but never rewrite it. Keep the ## headings stable — they are
citation anchors. Add new sections by appending, not renaming.
-->

## Architectural stance
What kind of system is this, and what does it fundamentally optimize for?
> Flask monolith (Elastic Beanstalk/EC2) serves the web UI + admin flows; a separate API Gateway + Lambda pair (`swudb-search`, `swudb-get-card`) serves the public REST API; DynamoDB (tables `Cards3`, `Sets`) is the system of record for card data; a DynamoDB-Streams-triggered Lambda (`swudb-get-leader-base-traits`) precomputes leader/base/trait facets into an ElastiCache memcached cluster; a daily Lambda (`populate-card-prices`) refreshes card prices scraped from tcgplayer.com.

## Layering & boundaries
The layers and the allowed dependency directions — what may depend on what, and what must never.
> Presentation (Jinja2 templates/static) → `application.py` route handlers → boto3 DynamoDB client / mysql-connector-python (no ORM/repository layer) → AWS services. The public API is a parallel boundary via API Gateway + Lambda, independent of the Flask app's own routes.

## What we optimize for
Ranked priorities, and the explicit non-goals that follow from them.
> Fast, low-latency card lookups and search (DynamoDB + ElastiCache); public API parity with the website's own search semantics; easy self-service deck building.
>
> 🔴 Explicit non-goals were not defined during bootstrap — revisit once priorities firm up.

## One-way doors
Decisions that require human sign-off *before* they're made — irreversible or expensive-to-reverse choices.
> The DynamoDB table shape/keys (`Cards3`, `Sets`) — changing keys requires a data migration; the public API URL contract (`/Cards/Search`, `/Cards/{Set}/{Card}`) is documented and externally consumed, so its shape is effectively frozen; the MySQL migration direction (parallel store vs. eventual DynamoDB replacement) is unresolved and worth a deliberate decision before more migration scripts are built on it.

## Error & failure philosophy
How the system handles and surfaces failure: fail-open vs fail-closed, the user-facing error policy, logging expectations.
> [TBD] 🔴

## Testing philosophy
What we test, at what level, and what "verified" means before a change is done.
> [TBD] — e.g. "Unit-test all logic; one E2E per user-visible flow; a bug fix starts with a failing test." 🔴
