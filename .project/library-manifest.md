# Library manifest

<!--
Project doc (.project/). Cite as `.project/library-manifest.md#<section>`. The
implementer's "new dependency = PAUSE" gate reads this; the coherence-reviewer
flags a new library that duplicates one listed here. Keep it current. Keep ##
headings stable — they are citation anchors.
-->

## Runtime & frameworks
The platform/runtime and primary frameworks, with versions. (Mirror these into milestone-driver `nonNegotiables` where they're hard constraints.)
> Python 3.11 (pinned via `.elasticbeanstalk/config.yml` platform: "Python 3.11 running on 64bit Amazon Linux 2023"; no `pyproject.toml`/`.python-version` in repo). Flask 2.3.2 + Flask-Bootstrap 3.3.7.1 (web UI). boto3/botocore (all AWS access). mysql-connector-python (direct MySQL queries, no ORM).

## Approved libraries (by purpose)
One approved choice per purpose, so a redundant alternative is easy to spot.

| Purpose | Library | Notes |
|---|---|---|
| Purpose | Library | Notes |
|---|---|---|
| AWS SDK | boto3 / botocore | All AWS access (DynamoDB, SNS, S3, ElastiCache clients) |
| Web framework | Flask 2.3.2 | Web app + local dev server |
| UI / Bootstrap | Flask-Bootstrap 3.3.7.1 | Bootstrap 3-era styling |
| Templating | Jinja2 3.1.2 | Flask's default templating engine |
| MySQL driver | mysql-connector-python | Direct queries, no ORM |
| HTTP | requests 2.31.0 | Outbound HTTP calls |

## Adding a dependency (the gate)
A new dependency is a PAUSE, not an autonomous call. Record what it buys, its license / OSS status, and why nothing approved suffices; a human approves before it's added.
> None — no formal dependency-addition process defined; add to `requirements.txt` as needed.

## Avoid / banned
Libraries explicitly not to use, and why.
> None — nothing explicitly banned.
