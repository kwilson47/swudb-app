# Environment

<!--
Project doc (.project/). Cite as `.project/environment.md#<section>`. Declares what the
project's runtime and production environment looks like — the facts downstream tools ground
their data, test, and caching decisions in. It does NOT provision anything; it records the
model so issues don't drift. Fill every [TBD]; a section left [TBD] is treated as "not
specified." Humans own this file; tools propose, never rewrite. Keep the ## headings stable
— they are citation anchors.
-->

## Environments
Which environments exist (production, staging, test, local) and how they differ.
> Two EB environments mapped 1:1 to GitHub branches, per `.elasticbeanstalk/config.yml`: `development` branch → `StarWarsUnlimitedDB-env-development`, `main` branch → `StarWarsUnlimitedDB-env-1` (prod). No separate test/staging environment found.

## Data stores
Databases and other persistent stores: the engine(s), and the **topology** — separate prod / staging / test databases, or a shared one. **Test-data isolation:** how tests get a clean, isolated database (a dedicated test DB, a per-worker DB suffix, transactional rollback, truncate-on-start). This is the single biggest drift source if left unstated.
> DynamoDB tables `Cards3` (cards) and `Sets` (set metadata) — no separate test/prod table naming convention found. MySQL (`MYSQL_HOST`/`MYSQL_PORT`/`MYSQL_USER`/`MYSQL_PASSWORD`/`MYSQL_DATABASE`/`MYSQL_SSL_CA` env vars) is a parallel/migration-target store — `scripts/` contains DynamoDB→MySQL migration/backfill tooling (`import_dynamodb_to_mysql.py`, `init_mysql_database.py`, `run_migration*.py`, `backfill_*.py`); the direction (parallel store vs. eventual cutover) is not yet decided.
>
> **Test-data isolation:** 🔴 none observed — no distinct test DB/table naming convention exists today; this is the biggest drift-risk per this file's own guidance.

## Caching
Whether caching exists and, if so, the layer and technology (in-memory, Redis, CDN), what is cached, and the invalidation policy. **"None" is a valid, drift-preventing answer** — record it explicitly.
> ElastiCache memcached cluster, populated by the DynamoDB-Streams-triggered Lambda (`swudb-get-leader-base-traits`) with leader/base/trait facet values (per README; not directly visible in `application.py`). 🔴 Invalidation/TTL policy unconfirmed.

## Async & messaging
Background jobs, queues, streams, schedulers — or "none."
> DynamoDB Streams → Lambda (`swudb-get-leader-base-traits`) is the only async pipeline. SNS is used for one-way feedback notification (not a queue/broker pattern). No other queues or brokers.

## External services & integrations
Third-party services the app depends on: auth / identity, payments, email / SMS, object storage, analytics, other APIs.
> SNS (site-feedback → email via `FEEDBACK_ARN` env var); tcgplayer.com (unofficial price scraping via the `populate-card-prices` Lambda, no API key found); Route 53 (`www.swu-db.com`, `api.swu-db.com`); CloudFront + S3 (card images); API Gateway (public REST API, 2 resources).

## Runtime & hosting
Where it runs and the runtime/version targets (hosting platform, language-runtime versions, regions). For mandated frameworks and packages, cross-reference `library-manifest.md`.
> AWS Elastic Beanstalk (EC2 auto-scaling group across multiple AZs behind an ALB), Python 3.11 / Amazon Linux 2023 platform; separate AWS Lambda deploys for 4 functions (`swudb-get-leader-base-traits`, `swudb-search`, `swudb-get-card`, `populate-card-prices`).

## Deployment targets
Where the app is **deployed** — the hosting vendor / platform / target (Cloudflare, AWS, Azure, Vercel, Netlify, Fly.io, a self-managed host). **Records** the deploy destination; it does **not** provision it. Boundary vs `## Runtime & hosting`: that anchor is the runtime/version targets and regions the app *needs*; this anchor is *where it is deployed to* and who hosts it.
> Today: CodeCommit → CodePipeline → CodeDeploy → the EB environments, on push to CodeCommit's `main`.
>
> 🔴 The GitHub remote (`kwilson47/swudb-app`) that milestone-suite branch/label/CI/protection provisioning targets is **not** wired into that CodeCommit deploy pipeline today — the GitHub Actions CI workflow this plan adds runs independently of the production deploy path unless connected later.
