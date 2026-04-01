import unittest
from datetime import date

from src.predict import predict_purchase_timing


class PredictPurchaseTimingTests(unittest.TestCase):
    def test_recommends_buy_now_when_price_is_close_to_low(self):
        item = {
            "item_id": "demo",
            "item_name": "Demo Item",
            "category": "audio",
            "latest_price": 102.0,
            "current_price": 102.0,
            "avg_price": 130.0,
            "low_price": 100.0,
            "high_price": 170.0,
            "best_buy_months": [7, 11, 12],
            "monthly_price_profile": {"7": 104.0, "11": 101.0, "12": 106.0},
            "prices": [
                {"date": "2026-01-15", "price": 118.0},
                {"date": "2026-02-20", "price": 110.0},
                {"date": "2026-03-31", "price": 102.0},
            ],
        }

        prediction = predict_purchase_timing(item, as_of=date(2026, 3, 31))

        self.assertEqual(prediction["recommendation"], "Buy now")
        self.assertEqual(prediction["buy_window"], "Now")
        self.assertEqual(prediction["confidence"], "High")
        self.assertEqual(prediction["best_price_windows"]["30"]["price"], 102.0)
        self.assertIn("30", prediction["forecast_prices"])
        self.assertGreater(len(prediction["future_sale_forecasts"]), 0)

    def test_recommends_wait_when_better_month_is_soon(self):
        item = {
            "item_id": "demo",
            "item_name": "Demo Item",
            "category": "smart_home",
            "latest_price": 140.0,
            "current_price": 140.0,
            "avg_price": 118.0,
            "low_price": 95.0,
            "high_price": 150.0,
            "best_buy_months": [7, 11, 12],
            "monthly_price_profile": {"7": 99.0, "11": 96.0, "12": 101.0},
            "prices": [
                {"date": "2026-06-01", "price": 132.0},
                {"date": "2026-07-15", "price": 101.0},
                {"date": "2026-08-20", "price": 126.0},
                {"date": "2026-10-01", "price": 140.0},
            ],
        }

        prediction = predict_purchase_timing(item, as_of=date(2026, 10, 1))

        self.assertEqual(prediction["recommendation"], "Wait")
        self.assertEqual(prediction["buy_month"], 11)
        self.assertEqual(prediction["buy_window"], "November")
        self.assertLess(prediction["future_sale_forecasts"][0]["predicted_price"], prediction["current_price"])


if __name__ == "__main__":
    unittest.main()
