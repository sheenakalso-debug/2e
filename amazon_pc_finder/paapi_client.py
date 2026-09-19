"""Minimal client for Amazon's Product Advertising API 5.0 (SearchItems operation).

Implements AWS Signature Version 4 signing directly over `requests` so the
project has no dependency on the (unofficial) third-party PA-API wrappers.
Reference: https://webservices.amazon.com/paapi5/documentation/sending-request.html
"""
import datetime
import hashlib
import hmac
import json
from typing import Iterable, Optional

import requests

from .config import PaapiCredentials

SERVICE = "ProductAdvertisingAPI"
URI_PATH = "/paapi5/searchitems"
TARGET = "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems"

RESOURCES = [
    "ItemInfo.Title",
    "ItemInfo.Features",
    "ItemInfo.ProductInfo",
    "Offers.Listings.Price",
    "CustomerReviews.Count",
    "CustomerReviews.StarRating",
    "Images.Primary.Medium",
]


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _signing_key(secret_key: str, date_stamp: str, region: str, service: str) -> bytes:
    k_date = _sign(("AWS4" + secret_key).encode("utf-8"), date_stamp)
    k_region = _sign(k_date, region)
    k_service = _sign(k_region, service)
    return _sign(k_service, "aws4_request")


def _build_signed_headers(creds: PaapiCredentials, payload: str) -> dict:
    now = datetime.datetime.utcnow()
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")

    content_type = "application/json; charset=UTF-8"
    content_encoding = "amz-1.0"

    canonical_headers = (
        f"content-encoding:{content_encoding}\n"
        f"content-type:{content_type}\n"
        f"host:{creds.host}\n"
        f"x-amz-date:{amz_date}\n"
        f"x-amz-target:{TARGET}\n"
    )
    signed_headers = "content-encoding;content-type;host;x-amz-date;x-amz-target"
    payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    canonical_request = "\n".join([
        "POST",
        URI_PATH,
        "",
        canonical_headers,
        signed_headers,
        payload_hash,
    ])

    credential_scope = f"{date_stamp}/{creds.region}/{SERVICE}/aws4_request"
    string_to_sign = "\n".join([
        "AWS4-HMAC-SHA256",
        amz_date,
        credential_scope,
        hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
    ])

    signing_key = _signing_key(creds.secret_key, date_stamp, creds.region, SERVICE)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization = (
        f"AWS4-HMAC-SHA256 Credential={creds.access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    return {
        "content-encoding": content_encoding,
        "content-type": content_type,
        "host": creds.host,
        "x-amz-date": amz_date,
        "x-amz-target": TARGET,
        "Authorization": authorization,
    }


class PaapiError(RuntimeError):
    pass


def search_items(creds: PaapiCredentials, keywords: str, search_index: str = "Electronics",
                  item_page: int = 1, item_count: int = 10,
                  max_price_cents: Optional[int] = None,
                  min_reviews_rating: Optional[float] = None,
                  timeout: int = 15) -> list:
    """Call SearchItems and return the raw list of item dicts from the response."""
    body = {
        "Keywords": keywords,
        "SearchIndex": search_index,
        "ItemPage": item_page,
        "ItemCount": item_count,
        "Resources": RESOURCES,
        "PartnerTag": creds.partner_tag,
        "PartnerType": "Associates",
        "Marketplace": creds.marketplace,
    }
    if max_price_cents is not None:
        body["MaxPrice"] = max_price_cents

    payload = json.dumps(body)
    headers = _build_signed_headers(creds, payload)
    url = f"https://{creds.host}{URI_PATH}"

    response = requests.post(url, headers=headers, data=payload, timeout=timeout)
    if response.status_code != 200:
        raise PaapiError(f"PA-API request failed ({response.status_code}): {response.text}")

    data = response.json()
    if "Errors" in data:
        raise PaapiError(f"PA-API returned errors: {data['Errors']}")

    return data.get("SearchResult", {}).get("Items", [])


def search_multiple(creds: PaapiCredentials, keyword_queries: Iterable[str],
                     pages_per_query: int = 1, **kwargs) -> list:
    """Run several keyword queries (e.g. different CPU/GPU phrasing) and merge results."""
    all_items = []
    for query in keyword_queries:
        for page in range(1, pages_per_query + 1):
            try:
                items = search_items(creds, query, item_page=page, **kwargs)
            except PaapiError:
                break
            if not items:
                break
            all_items.extend(items)
    return all_items
