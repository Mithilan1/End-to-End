import unittest
from pathlib import Path

from src.data_store import load_processed_items, search_item_by_name


class DataStoreSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = load_processed_items(Path("data/gold/items.json"))

    def test_alias_query_matches_echo_dot(self):
        match, score = search_item_by_name("alexa speaker", self.items)

        self.assertIsNotNone(match)
        self.assertEqual(match["item_id"], "amazon_echo_dot")
        self.assertGreaterEqual(score, 0.6)

    def test_semantic_query_matches_airpods(self):
        match, score = search_item_by_name("wireless earbuds", self.items)

        self.assertIsNotNone(match)
        self.assertEqual(match["item_id"], "apple_airpods_pro")
        self.assertGreaterEqual(score, 0.6)

    def test_shopper_language_matches_fire_tv_stick(self):
        match, score = search_item_by_name("amazon streaming device", self.items)

        self.assertIsNotNone(match)
        self.assertEqual(match["item_id"], "fire_tv_stick")
        self.assertGreaterEqual(score, 0.45)

    def test_unsupported_brand_query_is_rejected(self):
        match, score = search_item_by_name("samsung earbuds", self.items)

        self.assertIsNone(match)
        self.assertEqual(score, 0.0)


if __name__ == "__main__":
    unittest.main()
