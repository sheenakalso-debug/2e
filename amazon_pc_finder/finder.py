"""Turn raw PA-API SearchItems results into a ranked list of qualifying computers."""
from dataclasses import dataclass
from typing import Optional

from .config import Criteria
from .specs import SpecMatch, evaluate_specs

DEFAULT_QUERIES = [
    "prebuilt gaming desktop computer i5",
    "prebuilt gaming desktop computer ryzen 5",
    "gaming desktop GTX 1660",
    "gaming desktop RX 5500 XT",
    "gaming pc tower 16GB",
]


@dataclass
class Candidate:
    asin: str
    title: str
    price_usd: Optional[float]
    rating: Optional[float]
    review_count: Optional[int]
    url: str
    spec_match: SpecMatch

    @property
    def qualifies(self) -> bool:
        return self.spec_match.meets_all and self.price_usd is not None


def _text_from_item(item: dict) -> str:
    parts = []
    title = item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue")
    if title:
        parts.append(title)
    features = item.get("ItemInfo", {}).get("Features", {}).get("DisplayValues", [])
    parts.extend(features)
    return " \n".join(parts)


def _price_from_item(item: dict) -> Optional[float]:
    listings = item.get("Offers", {}).get("Listings", [])
    if not listings:
        return None
    amount = listings[0].get("Price", {}).get("Amount")
    return float(amount) if amount is not None else None


def parse_item(item: dict, criteria: Criteria) -> Candidate:
    text = _text_from_item(item)
    title = item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue", "(no title)")
    price = _price_from_item(item)
    reviews = item.get("CustomerReviews", {})
    rating = reviews.get("StarRating", {}).get("Value")
    review_count = reviews.get("Count", {}).get("Value")

    spec_match = evaluate_specs(
        text,
        min_cpu_score=criteria.min_cpu_score,
        min_ram_gb=criteria.min_ram_gb,
        min_gpu_score=criteria.min_gpu_score,
    )

    return Candidate(
        asin=item.get("ASIN", ""),
        title=title,
        price_usd=price,
        rating=float(rating) if rating is not None else None,
        review_count=int(review_count) if review_count is not None else None,
        url=item.get("DetailPageURL", ""),
        spec_match=spec_match,
    )


def dedupe_by_asin(items: list) -> list:
    seen = set()
    unique = []
    for item in items:
        asin = item.get("ASIN")
        if asin and asin not in seen:
            seen.add(asin)
            unique.append(item)
    return unique


def rank_candidates(candidates: list, criteria: Criteria) -> list:
    qualifying = [
        c for c in candidates
        if c.spec_match.meets_all
        and c.price_usd is not None
        and c.price_usd <= criteria.max_price_usd
    ]
    qualifying.sort(
        key=lambda c: (
            -(c.rating or 0),
            -(c.review_count or 0),
            c.price_usd or float("inf"),
        )
    )
    return qualifying


def find_best_computers(raw_items: list, criteria: Criteria) -> list:
    deduped = dedupe_by_asin(raw_items)
    candidates = [parse_item(item, criteria) for item in deduped]
    return rank_candidates(candidates, criteria)
