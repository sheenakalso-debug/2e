"""Fabricated sample PA-API responses for demoing/testing the pipeline offline.

None of this is real Amazon data — it exists so `--demo` can exercise the
full parse -> spec-match -> filter -> rank pipeline without live credentials.
"""

SAMPLE_ITEMS = [
    {
        "ASIN": "DEMO0001",
        "DetailPageURL": "https://www.amazon.com/dp/DEMO0001",
        "ItemInfo": {
            "Title": {"DisplayValue": "Example Gaming Desktop PC, AMD Ryzen 5 3600, 16GB RAM, GTX 1660 Super, 500GB SSD"},
            "Features": {"DisplayValues": ["6-Core Ryzen 5 3600", "16GB DDR4 RAM", "NVIDIA GTX 1660 Super 6GB", "Windows 11"]},
        },
        "Offers": {"Listings": [{"Price": {"Amount": 519.99}}]},
        "CustomerReviews": {"StarRating": {"Value": 4.5}, "Count": {"Value": 1230}},
    },
    {
        "ASIN": "DEMO0002",
        "DetailPageURL": "https://www.amazon.com/dp/DEMO0002",
        "ItemInfo": {
            "Title": {"DisplayValue": "Budget Desktop PC, Intel Core i5-8400, 8GB RAM, No Dedicated GPU"},
            "Features": {"DisplayValues": ["Intel i5-8400", "8GB RAM", "Integrated Graphics"]},
        },
        "Offers": {"Listings": [{"Price": {"Amount": 349.00}}]},
        "CustomerReviews": {"StarRating": {"Value": 4.2}, "Count": {"Value": 340}},
    },
    {
        "ASIN": "DEMO0003",
        "DetailPageURL": "https://www.amazon.com/dp/DEMO0003",
        "ItemInfo": {
            "Title": {"DisplayValue": "Premium Gaming Tower, Intel Core i7-10700, 32GB RAM, RTX 3060, 1TB SSD"},
            "Features": {"DisplayValues": ["Intel i7-10700", "32GB DDR4 RAM", "NVIDIA RTX 3060 12GB"]},
        },
        "Offers": {"Listings": [{"Price": {"Amount": 899.99}}]},
        "CustomerReviews": {"StarRating": {"Value": 4.7}, "Count": {"Value": 512}},
    },
    {
        "ASIN": "DEMO0004",
        "DetailPageURL": "https://www.amazon.com/dp/DEMO0004",
        "ItemInfo": {
            "Title": {"DisplayValue": "Value Gaming PC, AMD Ryzen 5 2600, 12GB RAM, RX 5500 XT, 256GB SSD"},
            "Features": {"DisplayValues": ["AMD Ryzen 5 2600", "12GB RAM", "AMD Radeon RX 5500 XT 8GB"]},
        },
        "Offers": {"Listings": [{"Price": {"Amount": 479.50}}]},
        "CustomerReviews": {"StarRating": {"Value": 4.0}, "Count": {"Value": 88}},
    },
    {
        "ASIN": "DEMO0005",
        "DetailPageURL": "https://www.amazon.com/dp/DEMO0005",
        "ItemInfo": {
            "Title": {"DisplayValue": "Compact Gaming PC, Intel Core i5-10400F, 16GB RAM, GTX 1660 Ti, 512GB SSD"},
            "Features": {"DisplayValues": ["Intel i5-10400F 6-Core", "16GB RAM", "NVIDIA GTX 1660 Ti 6GB"]},
        },
        "Offers": {"Listings": [{"Price": {"Amount": 539.00}}]},
        "CustomerReviews": {"StarRating": {"Value": 4.6}, "Count": {"Value": 2104}},
    },
    {
        "ASIN": "DEMO0006",
        "DetailPageURL": "https://www.amazon.com/dp/DEMO0006",
        "ItemInfo": {
            "Title": {"DisplayValue": "Overpriced Gaming PC, Ryzen 5 3600, 16GB RAM, GTX 1660 Super"},
            "Features": {"DisplayValues": ["Ryzen 5 3600", "16GB RAM", "GTX 1660 Super"]},
        },
        "Offers": {"Listings": [{"Price": {"Amount": 649.00}}]},
        "CustomerReviews": {"StarRating": {"Value": 4.8}, "Count": {"Value": 5000}},
    },
]
