import argparse
import sys

from .config import Criteria, MissingCredentialsError, load_credentials_from_env
from .finder import DEFAULT_QUERIES, find_best_computers
from .paapi_client import PaapiError, search_multiple
from .sample_data import SAMPLE_ITEMS


def _print_results(results, limit):
    if not results:
        print("No qualifying computers found.")
        return

    for rank, candidate in enumerate(results[:limit], start=1):
        rating = f"{candidate.rating:.1f}" if candidate.rating is not None else "N/A"
        reviews = candidate.review_count if candidate.review_count is not None else "N/A"
        price = f"${candidate.price_usd:.2f}" if candidate.price_usd is not None else "N/A"
        sm = candidate.spec_match
        print(f"{rank}. {candidate.title}")
        print(f"   Price: {price}   Rating: {rating} ({reviews} reviews)")
        print(f"   CPU: {sm.cpu_found}   RAM: {sm.ram_found}GB   GPU: {sm.gpu_found}")
        print(f"   ASIN: {candidate.asin}   URL: {candidate.url}")
        print()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Find the best-reviewed Amazon prebuilt computers meeting a minimum "
            "CPU/RAM/GPU spec, under a price cap. Uses Amazon's Product Advertising API."
        )
    )
    parser.add_argument("--max-price", type=float, default=540.0, help="Maximum price in USD (default: 540)")
    parser.add_argument("--min-ram", type=int, default=12, help="Minimum RAM in GB (default: 12)")
    parser.add_argument("--limit", type=int, default=10, help="Number of results to show (default: 10)")
    parser.add_argument(
        "--query", action="append", dest="queries",
        help="Search keyword phrase to use (repeatable). Defaults to a built-in set covering both CPU/GPU families.",
    )
    parser.add_argument(
        "--pages", type=int, default=1,
        help="Number of result pages to fetch per query (PA-API returns up to 10 items/page, max 10 pages).",
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Run against bundled fake sample data instead of calling the live API (no credentials needed).",
    )
    args = parser.parse_args(argv)

    criteria = Criteria(max_price_usd=args.max_price, min_ram_gb=args.min_ram)

    if args.demo:
        raw_items = SAMPLE_ITEMS
    else:
        try:
            creds = load_credentials_from_env()
        except MissingCredentialsError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

        queries = args.queries or DEFAULT_QUERIES
        try:
            raw_items = search_multiple(
                creds,
                queries,
                pages_per_query=args.pages,
                max_price_cents=int(criteria.max_price_usd * 100),
            )
        except PaapiError as exc:
            print(f"Error calling Amazon Product Advertising API: {exc}", file=sys.stderr)
            return 1

    results = find_best_computers(raw_items, criteria)
    _print_results(results, args.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
