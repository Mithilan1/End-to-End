import os
import unittest
from unittest.mock import patch

from src.amazon_affiliate import build_affiliate_product_url, extract_asin, fetch_current_snapshot_from_api


class _MockResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class AmazonAffiliateTests(unittest.TestCase):
    def test_extract_asin_from_url(self):
        self.assertEqual(extract_asin("https://www.amazon.ca/dp/B012345678"), "B012345678")

    def test_build_affiliate_product_url_appends_partner_tag(self):
        url = build_affiliate_product_url(
            "B012345678",
            marketplace="www.amazon.ca",
            partner_tag="demo-tag-20",
        )

        self.assertEqual(url, "https://www.amazon.ca/dp/B012345678?tag=demo-tag-20")

    @patch("src.amazon_affiliate.requests.get")
    def test_fetch_current_snapshot_parses_price_payload(self, mock_get):
        mock_get.return_value = _MockResponse(
            {
                "items": [
                    {
                        "asin": "B012345678",
                        "title": "Echo Dot",
                        "detailPageURL": "https://www.amazon.ca/dp/B012345678",
                        "offersV2": {"price": {"amount": 49.99}},
                        "currencyCode": "CAD",
                        "merchant": "Amazon",
                    }
                ]
            }
        )

        with patch.dict(
            os.environ,
            {
                "AMAZON_CREATOR_API_URL": "https://example.com/creators/items",
                "AMAZON_CREATOR_PARTNER_TAG": "demo-tag-20",
                "AMAZON_CREATOR_MARKETPLACE": "www.amazon.ca",
            },
            clear=False,
        ):
            snapshot = fetch_current_snapshot_from_api(
                "Echo Dot",
                amazon_asin="B012345678",
            )

        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot["amazon_asin"], "B012345678")
        self.assertEqual(snapshot["item_name"], "Echo Dot")
        self.assertEqual(snapshot["price"], 49.99)
        self.assertEqual(snapshot["currency"], "CAD")
        self.assertIn("tag=demo-tag-20", snapshot["amazon_url"])


if __name__ == "__main__":
    unittest.main()
