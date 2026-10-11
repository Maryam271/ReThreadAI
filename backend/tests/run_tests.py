import io
import os
import sys
from pathlib import Path
import unittest
from unittest.mock import patch, AsyncMock
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app.image_utils import validate_and_process_image, ImageValidationError

def create_sample_image(format="JPEG", size=(200, 200), color=(100, 150, 200)) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format=format)
    return buf.getvalue()

class TestReThreadAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["ai_configured"])
        self.assertIn("max_upload_size_mb", data)
        self.assertIn("Streetwear", data["supported_styles"])
        self.assertIn("available_providers", data)

    def test_image_utils_valid(self):
        img_bytes = create_sample_image("PNG", size=(300, 300))
        processed, mime, w, h = validate_and_process_image(img_bytes, "test.png")
        self.assertEqual(mime, "image/png")
        self.assertEqual(w, 300)
        self.assertEqual(h, 300)

    def test_image_utils_unsupported_format(self):
        with self.assertRaises(ImageValidationError):
            validate_and_process_image(b"not an image", "test.txt")

    def test_image_utils_oversized(self):
        dummy_huge = b"0" * (11 * 1024 * 1024)
        with self.assertRaises(ImageValidationError):
            validate_and_process_image(dummy_huge, "huge.jpg")

    def test_redesign_invalid_style(self):
        img_bytes = create_sample_image()
        response = self.client.post(
            "/api/redesign",
            files={"image": ("shirt.jpg", img_bytes, "image/jpeg")},
            data={"style": "NonExistentStyle"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid style", response.json()["detail"])

    def test_redesign_missing_api_key(self):
        img_bytes = create_sample_image()
        with patch.dict(os.environ, {"STABILITY_API_KEY": "", "REPLICATE_API_TOKEN": ""}):
            with patch("app.ai_service.STABILITY_API_KEY", ""):
                with patch("app.config.STABILITY_API_KEY", ""):
                    response = self.client.post(
                        "/api/redesign",
                        files={"image": ("shirt.jpg", img_bytes, "image/jpeg")},
                        data={"style": "Floral Embroidery", "provider": "stability"},
                    )
                    self.assertIn(response.status_code, (400, 401))
                    self.assertIn("STABILITY_API_KEY", response.json()["detail"])

    def test_redesign_demo_mode(self):
        img_bytes = create_sample_image("JPEG", color=(80, 120, 160))
        response = self.client.post(
            "/api/redesign",
            files={"image": ("jacket.jpg", img_bytes, "image/jpeg")},
            data={"style": "Vintage", "provider": "demo"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["is_demo"])
        self.assertIn("image_data", data)
        self.assertEqual(data["style"], "Vintage")

    def test_redesign_caching(self):
        img_bytes = create_sample_image("JPEG", color=(200, 100, 50))
        # First call
        res1 = self.client.post(
            "/api/redesign",
            files={"image": ("caching_test.jpg", img_bytes, "image/jpeg")},
            data={"style": "Minimalist", "provider": "demo"},
        )
        self.assertEqual(res1.status_code, 200)
        
        # Second identical call should hit cache
        res2 = self.client.post(
            "/api/redesign",
            files={"image": ("caching_test.jpg", img_bytes, "image/jpeg")},
            data={"style": "Minimalist", "provider": "demo"},
        )
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertTrue(data2["is_cached"])

    def test_redesign_and_download_flow_mocked(self):
        mock_out_bytes = create_sample_image("PNG", color=(50, 200, 50))
        with patch(
            "app.main.execute_redesign",
            new=AsyncMock(return_value=(mock_out_bytes, "image/png", "stability", "Mocked prompt", 1.25)),
        ):
            img_bytes = create_sample_image("JPEG")
            response = self.client.post(
                "/api/redesign",
                files={"image": ("hoodie.jpg", img_bytes, "image/jpeg")},
                data={"style": "Streetwear", "custom_prompt": "Add subtle distressed accents"},
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["success"])
            self.assertIn("image_data", data)
            self.assertEqual(data["style"], "Streetwear")
            self.assertIn("download_url", data)

            dl_response = self.client.get(data["download_url"])
            self.assertEqual(dl_response.status_code, 200)
            self.assertEqual(dl_response.headers["content-type"], "image/png")
            self.assertEqual(dl_response.content, mock_out_bytes)
            self.assertIn("garment_analysis", data)
            self.assertIn("repair_plan", data)

    def test_fashion_intelligence_endpoint(self):
        response = self.client.get("/api/fashion-intelligence")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("data_origin", data)
        self.assertGreaterEqual(len(data["resources"]), 4)

    def test_garment_damage_analysis_and_repair_plan(self):
        from app.image_utils import analyze_garment_damage
        img_bytes = create_sample_image("JPEG")
        analysis = analyze_garment_damage(
            file_bytes=img_bytes,
            filename="denim-jacket.jpg",
            damage_hint="Elbow Fray",
            style="Vintage",
        )
        self.assertIn("Denim", analysis["garment_type"])
        self.assertEqual(analysis["confidence"], "high")
        self.assertTrue(analysis["user_specified"])
        self.assertIn("repair_plan", analysis)
        self.assertIn("tools_and_materials", analysis["repair_plan"])
        self.assertIn("when_to_seek_tailor", analysis["repair_plan"])

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestReThreadAPI)
    try:
        try:
            import tests.test_repair_pipeline as trp
        except ImportError:
            import test_repair_pipeline as trp
        for cls in (trp.TestLeftKneeTear, trp.TestCenterShirtHole, trp.TestSleeveCuffTear,
                    trp.TestDiagonalRipMask, trp.TestNoDamageDetected, trp.TestExplicitlyMarkedRegion,
                    trp.TestMissingOrInvalidMask, trp.TestProviderFailureFallback,
                    trp.TestFreeProviderNoPollinations, trp.TestBuildPrompt):
            suite.addTests(loader.loadTestsFromTestCase(cls))
    except Exception as e:
        print("Warning loading repair pipeline tests:", e)
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)

