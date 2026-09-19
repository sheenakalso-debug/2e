import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Criteria:
    max_price_usd: float = 540.0
    min_ram_gb: int = 12
    min_cpu_score: int = 100  # baseline: Intel Core i5-8400 / AMD Ryzen 5 2600
    min_gpu_score: int = 100  # baseline: GTX 1660 / RX 5500 XT


@dataclass(frozen=True)
class PaapiCredentials:
    access_key: str
    secret_key: str
    partner_tag: str
    host: str = "webservices.amazon.com"
    region: str = "us-east-1"
    marketplace: str = "www.amazon.com"


class MissingCredentialsError(RuntimeError):
    pass


def load_credentials_from_env() -> PaapiCredentials:
    access_key = os.environ.get("AMAZON_PAAPI_ACCESS_KEY")
    secret_key = os.environ.get("AMAZON_PAAPI_SECRET_KEY")
    partner_tag = os.environ.get("AMAZON_PAAPI_PARTNER_TAG")

    missing = [
        name
        for name, val in (
            ("AMAZON_PAAPI_ACCESS_KEY", access_key),
            ("AMAZON_PAAPI_SECRET_KEY", secret_key),
            ("AMAZON_PAAPI_PARTNER_TAG", partner_tag),
        )
        if not val
    ]
    if missing:
        raise MissingCredentialsError(
            "Missing required environment variable(s): "
            + ", ".join(missing)
            + ". See README.md for how to obtain Amazon Product Advertising API credentials."
        )

    return PaapiCredentials(
        access_key=access_key,
        secret_key=secret_key,
        partner_tag=partner_tag,
        host=os.environ.get("AMAZON_PAAPI_HOST", "webservices.amazon.com"),
        region=os.environ.get("AMAZON_PAAPI_REGION", "us-east-1"),
        marketplace=os.environ.get("AMAZON_PAAPI_MARKETPLACE", "www.amazon.com"),
    )
