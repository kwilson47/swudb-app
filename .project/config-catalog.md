# Config catalog

<!--
Project doc (.project/). Cite as `.project/config-catalog.md#<section>`. A norms file for the
project's configuration & secrets — the analog of `.env.example` / an `appsettings.template.*`.
It records the *shape* of every config/secret key so downstream tools build config, secrets, and
CORS correctly the first time. For each entry record: **key name · source bucket · format/shape ·
environment(s) · required?** — and NEVER a secret value. Non-secret config facts a builder needs
verbatim (CORS origin URLs, the sender/from address, the JWT issuer/audience) ARE recorded here as
norms; secret material (signing keys, passwords, API-key strings) is NEVER recorded — name the
bucket it lives in and leave the value out. Fill every [TBD]; a section left [TBD] is treated as
"not specified." Humans own this file; tools propose, never rewrite. Keep the ## headings stable —
they are citation anchors. Add rows to a table; never rename a heading.
-->

## Connection strings
DB and service connection strings the app needs, **including the local-dev DB engine** — SQL Server LocalDB, a Docker SQL container, or a dev cloud DB. The F5/local-dev target is the single most-missed entry. Record the key name and its shape; **never the value** (a connection string's password is secret).
| Key | Source bucket | Format / shape | Environment(s) | Required? |
|---|---|---|---|---|
| Key | Source bucket | Format / shape | Environment(s) | Required? |
|---|---|---|---|---|
| DynamoDB access | IAM role (prod, EB instance profile) / named AWS profile `swu-admin` (local dev) | boto3-managed, no explicit connection string; region via `AWS_REGION` env | prod, local | yes |
| `MYSQL_HOST` / `MYSQL_PORT` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DATABASE` / `MYSQL_SSL_CA` | Environment variables (source bucket not further specified in repo) | host/port/user/password/db-name strings + optional SSL CA path | prod, local (🔴 local-dev target unspecified) | host required; rest optional with defaults |

## Auth / JWT
The **full** auth/JWT key set — signing key, issuer, AND audience — not just the signing key. Issuer and audience are non-secret identifiers and ARE recorded; the signing key's value is secret and is NEVER recorded.
| Key | Source bucket | Format / shape | Environment(s) | Required? |
|---|---|---|---|---|
| Key | Source bucket | Format / shape | Environment(s) | Required? |
|---|---|---|---|---|
| None | — | No auth/JWT system exists — Flask session cookie only, keyed by `FLASK_SECRET_KEY` (env var; hardcoded fallback literal in source, flagged separately as a hygiene item) | — | — |

## Third-party API keys
API keys / tokens for third-party services (payments, storage, external APIs). Record the key name and where it is sourced; **never the key value**.
| Key | Source bucket | Format / shape | Environment(s) | Required? |
|---|---|---|---|---|
| Key | Source bucket | Format / shape | Environment(s) | Required? |
|---|---|---|---|---|
| None found | — | tcgplayer.com scraping is keyless; AWS access is via IAM role/profile, not a stored key | — | — |

## Notification targets
Email / SMS / push configuration, **including the sender / from address** — not only the recipient. From/sender and recipient addresses are non-secret and ARE recorded.
| Key | Source bucket | Format / shape | Environment(s) | Required? |
|---|---|---|---|---|
| Key | Source bucket | Format / shape | Environment(s) | Required? |
|---|---|---|---|---|
| `FEEDBACK_ARN` | Environment variable | SNS topic ARN → email subscription (site owner); no separate from-address (SNS→email, not direct SMTP) | prod, local | yes |

## CORS origins
The **complete** set of allowed CORS origins across every environment — localhost dev origin(s), the apex domain, the `www` origin, and any API origin. Origins are non-secret and ARE recorded in full; an incomplete list is a common first-try bug.
| Key | Source bucket | Format / shape | Environment(s) | Required? |
|---|---|---|---|---|
| [TBD] — e.g. `Cors:AllowedOrigins` | [TBD] — e.g. appsettings per env | [TBD] — e.g. list of origin URLs (`https://www.example.com`, …) | [TBD] — e.g. all | [TBD] — e.g. yes | 🔴

## App config (per-environment)
Non-secret per-environment application settings — API base URLs (`apiUrl`), feature flags, timeouts, log levels — that differ across environments.
| Key | Source bucket | Format / shape | Environment(s) | Required? |
|---|---|---|---|---|
| Key | Source bucket | Format / shape | Environment(s) | Required? |
|---|---|---|---|---|
| `FLASK_SECRET_KEY` | Environment variable (EB per-environment config) | secret string | prod, local | yes |
| `AWS_REGION` | Environment variable | AWS region string (default `us-east-1`) | prod, local | no |
| `SWU_DB_TABLE` | Environment variable | DynamoDB table name (default `Cards3`) | prod, local | no |
| `FEEDBACK_ARN` | Environment variable | SNS topic ARN | prod, local | yes |

## Build outputs
Build / publish output locations and artifact paths a deploy consumes — the publish directory, the bundle output dir, the artifact name.
| Key | Source bucket | Format / shape | Environment(s) | Required? |
|---|---|---|---|---|
| Key | Source bucket | Format / shape | Environment(s) | Required? |
|---|---|---|---|---|
| None | — | Flask app deployed as source, no build/bundle step; Lambda packaging mechanism not visible in this repo | — | — |
