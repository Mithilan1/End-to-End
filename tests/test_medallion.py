import unittest
from pathlib import Path

from src.medallion import build_gold_items, build_gold_recommendations, build_silver_dataset, run_medallion_pipeline


class MedallionPipelineTests(unittest.TestCase):
    def test_silver_layer_keeps_lowest_price_per_item_per_day(self):
        bronze_records = [
            {
                "item_id": "echo",
                "item_name": "Echo Dot",
                "category": "smart_home",
                "date": "2025-03-20",
                "price": 34.99,
                "currency": "USD",
                "source": "sample_seed",
                "source_ref": "sample_price_history.csv",
                "camel_url": "",
                "shopbot_url": "",
                "merchant": "",
                "ingested_at": "2026-03-31T00:00:00Z",
            },
            {
                "item_id": "echo",
                "item_name": "Echo Dot",
                "category": "smart_home",
                "date": "2025-03-20",
                "price": 27.99,
                "currency": "USD",
                "source": "camelcamelcamel_injection",
                "source_ref": "camelcamelcamel_injection.csv",
                "camel_url": "https://camelcamelcamel.com/product/example",
                "shopbot_url": "",
                "merchant": "",
                "ingested_at": "2026-03-31T00:00:00Z",
            },
        ]

        silver = build_silver_dataset(bronze_records)

        self.assertEqual(len(silver), 1)
        self.assertEqual(float(silver.iloc[0]["price"]), 27.99)

    def test_gold_layer_publishes_item_features_and_recommendations(self):
        bronze_records = [
            {
                "item_id": "echo",
                "item_name": "Echo Dot",
                "category": "smart_home",
                "date": "2025-01-10",
                "price": 39.99,
                "currency": "USD",
                "source": "sample_seed",
                "source_ref": "sample_price_history.csv",
                "camel_url": "",
                "shopbot_url": "",
                "merchant": "",
                "ingested_at": "2026-03-31T00:00:00Z",
            },
            {
                "item_id": "echo",
                "item_name": "Echo Dot",
                "category": "smart_home",
                "date": "2025-03-20",
                "price": 27.99,
                "currency": "USD",
                "source": "camelcamelcamel_injection",
                "source_ref": "camelcamelcamel_injection.csv",
                "camel_url": "https://camelcamelcamel.com/product/example",
                "shopbot_url": "",
                "merchant": "",
                "ingested_at": "2026-03-31T00:00:00Z",
            },
            {
                "item_id": "echo",
                "item_name": "Echo Dot",
                "category": "smart_home",
                "date": "2025-07-15",
                "price": 24.99,
                "currency": "USD",
                "source": "sample_seed",
                "source_ref": "sample_price_history.csv",
                "camel_url": "",
                "shopbot_url": "",
                "merchant": "",
                "ingested_at": "2026-03-31T00:00:00Z",
            },
            {
                "item_id": "echo",
                "item_name": "Echo Dot",
                "category": "smart_home",
                "date": "2026-03-31",
                "price": 26.99,
                "currency": "USD",
                "source": "shopbot_injection",
                "source_ref": "shopbot_injection.csv",
                "camel_url": "",
                "shopbot_url": "https://www.shopbot.ca/",
                "merchant": "Amazon",
                "ingested_at": "2026-03-31T00:00:00Z",
            },
        ]

        silver = build_silver_dataset(bronze_records)
        items = build_gold_items(silver)
        recommendations = build_gold_recommendations(items)

        self.assertIn("echo", items)
        self.assertIn("best_buy_months", items["echo"])
        self.assertEqual(items["echo"]["current_price"], 26.99)
        self.assertIn("echo", recommendations)
        self.assertIn("buy_window", recommendations["echo"])
        self.assertIn("forecast_prices", recommendations["echo"])

    def test_gold_layer_prefers_amazon_live_price_for_current_snapshot(self):
        bronze_records = [
            {
                "item_id": "echo",
                "item_name": "Echo Dot",
                "category": "smart_home",
                "date": "2025-01-10",
                "price": 39.99,
                "currency": "USD",
                "source": "sample_seed",
                "source_ref": "sample_price_history.csv",
                "amazon_asin": "B012345678",
                "amazon_url": "https://www.amazon.ca/dp/B012345678?tag=demo-tag-20",
                "camel_url": "",
                "shopbot_url": "",
                "merchant": "",
                "ingested_at": "2026-03-31T00:00:00Z",
            },
            {
                "item_id": "echo",
                "item_name": "Echo Dot",
                "category": "smart_home",
                "date": "2026-03-31",
                "price": 26.49,
                "currency": "CAD",
                "source": "amazon_creators_api",
                "source_ref": "https://www.amazon.ca/dp/B012345678?tag=demo-tag-20",
                "amazon_asin": "B012345678",
                "amazon_url": "https://www.amazon.ca/dp/B012345678?tag=demo-tag-20",
                "camel_url": "",
                "shopbot_url": "",
                "merchant": "Amazon",
                "ingested_at": "2026-03-31T00:00:00Z",
            },
        ]

        silver = build_silver_dataset(bronze_records)
        items = build_gold_items(silver)

        self.assertEqual(items["echo"]["current_price"], 26.49)
        self.assertEqual(items["echo"]["current_price_source"], "amazon_creators_api")
        self.assertEqual(items["echo"]["amazon_asin"], "B012345678")
        self.assertIn("amazon.ca", items["echo"]["amazon_url"])

    def test_top_level_pipeline_writes_medallion_outputs(self):
        temp_root = Path(__file__).resolve().parent / "_tmp" / "integration_case"
        temp_root.mkdir(parents=True, exist_ok=True)
        manifest_path = temp_root / "track_items.csv"
        sample_path = temp_root / "sample_price_history.csv"
        injection_path = temp_root / "camelcamelcamel_injection.csv"
        shopbot_injection_path = temp_root / "shopbot_injection.csv"
        output_root = temp_root / "data"

        manifest_path.write_text(
            "item_id,item_name,category,camel_url,shopbot_query,shopbot_url\n"
            "amazon_echo_dot,Amazon Echo Dot (5th Gen),smart_home,https://camelcamelcamel.com/product/B0XXXXX1,Amazon Echo Dot 5th Gen,\n",
            encoding="utf-8",
        )
        sample_path.write_text(
            "item_id,item_name,category,date,price\n"
            "amazon_echo_dot,Amazon Echo Dot (5th Gen),smart_home,2025-01-10,33.99\n",
            encoding="utf-8",
        )
        injection_path.write_text(
            "item_id,item_name,category,camel_url,date,price\n"
            "amazon_echo_dot,Amazon Echo Dot (5th Gen),smart_home,https://camelcamelcamel.com/product/B0XXXXX1,2025-03-20,27.99\n",
            encoding="utf-8",
        )
        shopbot_injection_path.write_text(
            "item_id,item_name,category,shopbot_url,merchant,date,price,currency\n"
            "amazon_echo_dot,Amazon Echo Dot (5th Gen),smart_home,,Amazon,2026-03-31,26.99,USD\n",
            encoding="utf-8",
        )

        outputs = run_medallion_pipeline(
            manifest_path=manifest_path,
            sample_path=sample_path,
            injection_path=injection_path,
            shopbot_injection_path=shopbot_injection_path,
            output_root=output_root,
            enable_camel_scrape=False,
        )

        self.assertTrue(outputs["bronze"].exists())
        self.assertTrue(outputs["silver"].exists())
        self.assertTrue(outputs["gold_items"].exists())
        self.assertTrue(outputs["gold_recommendations"].exists())


if __name__ == "__main__":
    unittest.main()
