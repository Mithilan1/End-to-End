import unittest
from io import BytesIO

from PIL import Image

from index import app


class VercelAppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_endpoint_reports_ready_catalog(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["status"], "ready")
        self.assertGreaterEqual(payload["catalog_size"], 1)

    def test_search_endpoint_returns_item_payload(self):
        response = self.client.get("/api/search?q=echo")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["result"]["item"]["item_id"], "amazon_echo_dot")
        self.assertIn("trend_6m", payload["result"])
        self.assertIn("forecast_prices", payload["result"]["prediction"])

    def test_image_endpoint_supports_filename_hint_fallback(self):
        image = Image.new("RGB", (120, 120), color=(240, 240, 240))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        response = self.client.post(
            "/api/identify-image",
            data={"image": (buffer, "echo-device.png")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["result"]["item"]["item_id"], "amazon_echo_dot")
        self.assertIn("Image matched via", payload["source"])


if __name__ == "__main__":
    unittest.main()
