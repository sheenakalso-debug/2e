# Amazon PC Finder

Finds prebuilt desktop computers on Amazon that meet a minimum spec bar —
**Intel Core i5-8400 or AMD Ryzen 5 2600 (or better) CPU, 12GB+ RAM, and
NVIDIA GTX 1660 or AMD RX 5500 XT (or better) GPU** — under **$540**, ranked
by star rating and review count.

## Why this doesn't scrape Amazon's website

Scraping Amazon's HTML pages violates Amazon's Conditions of Use, and Amazon
actively blocks automated browsing anyway. Instead, this tool calls Amazon's
official **Product Advertising API (PA-API) 5.0**, which is the sanctioned
way to programmatically search products, prices, and customer review data
(star rating + review count) as an Amazon Associate.

## Getting API credentials

1. Join the [Amazon Associates Program](https://affiliate-program.amazon.com/).
2. Once approved, request Product Advertising API access from the
   Associates Central dashboard (Tools > Product Advertising API).
3. Generate an access key / secret key pair.
4. Note: PA-API access requires your Associates account to have made
   qualifying sales; Amazon can revoke access if it goes unused.

Set these environment variables:

```bash
export AMAZON_PAAPI_ACCESS_KEY="..."
export AMAZON_PAAPI_SECRET_KEY="..."
export AMAZON_PAAPI_PARTNER_TAG="your-associate-tag-20"
```

## Install

```bash
pip install -r requirements.txt
```

## Usage

Try it instantly with bundled fake data (no credentials needed) to see the
output format and confirm the spec-matching logic works:

```bash
python -m amazon_pc_finder --demo
```

Run against the live API once credentials are set:

```bash
python -m amazon_pc_finder --max-price 540 --min-ram 12 --limit 10
```

Options:

- `--max-price` — price cap in USD (default 540)
- `--min-ram` — minimum RAM in GB (default 12)
- `--query` — repeatable custom search phrase (overrides the built-in query set)
- `--pages` — result pages to fetch per query (PA-API: up to 10/page, 10 pages max)
- `--limit` — how many ranked results to print
- `--demo` — use bundled sample data instead of calling the live API

## How spec matching works

`amazon_pc_finder/specs.py` extracts the CPU model, RAM size, and GPU model
from each listing's title and bullet-point features, then compares them
against hand-curated relative-performance tables (`CPU_SCORES`, `GPU_SCORES`).
The two baseline chips in each table (`i5-8400`/`ryzen 5 2600` for CPU,
`gtx 1660`/`rx 5500 xt` for GPU) are pinned to a score of 100; any detected
chip scoring >= 100 satisfies "or better". These tables are an approximation
based on general performance tiers — extend them in `specs.py` if a listing
uses a chip that isn't recognized.

A listing where the CPU, RAM, or GPU can't be confidently detected in the
text is excluded rather than guessed at.

## Running tests

```bash
pytest tests/
```

The tests cover the CPU/GPU/RAM matching logic directly and don't require
network access or API credentials.

## Limitations

- Spec detection relies on the seller's listing title/bullets mentioning the
  exact chip model; some listings are vague ("powerful gaming PC") and will
  be skipped.
- The CPU/GPU performance tables are a manually curated approximation, not a
  benchmark database — double-check a borderline match before buying.
- PA-API rate limits apply (initially ~1 request/second, scaling with sales
  volume).
