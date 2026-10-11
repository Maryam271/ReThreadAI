"""
test_repair_pipeline.py
=======================
Regression tests for the ReThread AI repair pipeline.

Tests 8 required cases:
1. Tear on the left knee of jeans
2. Hole in the center of a shirt
3. Tear near a sleeve / cuff
4. Diagonal rip with an irregular mask
5. Garment with no clearly visible damage (clarification check)
6. Explicitly marked repair region (high-confidence mask)
7. Missing or invalid mask (graceful handling)
8. Provider failure / API timeout (auto-fallback to Free Preview)

Additional verifications:
- generate_redesign_free does NOT call Pollinations (no text-to-image)
- Pixel-preservation outside mask in render_procedural_repair
"""

import io
import sys
import json
import base64
import asyncio
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock

import httpx
from PIL import Image, ImageDraw
from fastapi import HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app
from app.image_utils import (
    analyze_garment_damage,
    render_procedural_repair,
    verify_pixel_preservation,
    normalize_mask,
)
from app.ai_service import generate_redesign_free, build_prompt

client = TestClient(app)


def make_image(size=(300, 300), color=(80, 120, 160), fmt="JPEG") -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color=color).save(buf, format=fmt)
    return buf.getvalue()


def make_mask(size=(300, 300), region=(100, 100, 200, 200)) -> bytes:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rectangle(region, fill=255)
    buf = io.BytesIO()
    mask.save(buf, format="PNG")
    return buf.getvalue()


def make_mask_b64(size=(300, 300), region=(100, 100, 200, 200)) -> str:
    return base64.b64encode(make_mask(size, region)).decode("utf-8")


# ---------------------------------------------------------------------------
# 1. Left knee tear of jeans
# ---------------------------------------------------------------------------
class TestLeftKneeTear(unittest.TestCase):

    def test_left_knee_damage_analysis(self):
        img = make_image(color=(35, 55, 90))
        analysis = analyze_garment_damage(
            file_bytes=img, filename="jeans.jpg",
            damage_hint="Auto-Detect", style="Patchwork",
            damage_coords={"x": 0.40, "y": 0.70, "radius": 0.15,
                          "locationName": "Left Knee / Thigh Tear"},
        )
        self.assertEqual(analysis["confidence"], "high")
        self.assertIn("Left Knee", analysis["damage_location"])

    def test_left_knee_demo_succeeds(self):
        img = make_image(color=(35, 55, 90))
        resp = client.post("/api/redesign",
            files={"image": ("jeans.jpg", img, "image/jpeg")},
            data={"style": "Patchwork", "provider": "demo",
                  "damage_coords": json.dumps({"x": 0.40, "y": 0.70, "radius": 0.15,
                                               "locationName": "Left Knee / Thigh Tear"})})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["is_demo"])
        self.assertIn("Left Knee", data["garment_analysis"]["damage_location"])


# ---------------------------------------------------------------------------
# 2. Center hole in a shirt
# ---------------------------------------------------------------------------
class TestCenterShirtHole(unittest.TestCase):

    def test_center_hole_analysis(self):
        img = make_image(color=(245, 245, 240))
        analysis = analyze_garment_damage(
            file_bytes=img, filename="shirt.jpg",
            damage_hint="Auto-Detect", style="Minimalist",
            damage_coords={"x": 0.50, "y": 0.50, "radius": 0.10,
                          "locationName": "Center Chest Placket / Seam"},
        )
        self.assertEqual(analysis["confidence"], "high")
        self.assertIn("Center Chest", analysis["damage_location"])

    def test_center_hole_procedural_repair(self):
        img = make_image(color=(245, 245, 240))
        out, mime = render_procedural_repair(
            image_bytes=img,
            damage_coords={"x": 0.50, "y": 0.50, "radius": 0.10},
            style="Minimalist",
        )
        self.assertEqual(mime, "image/png")
        self.assertGreater(len(out), 500)


# ---------------------------------------------------------------------------
# 3. Sleeve / cuff tear
# ---------------------------------------------------------------------------
class TestSleeveCuffTear(unittest.TestCase):

    def test_sleeve_hint_analysis(self):
        img = make_image(color=(52, 57, 63))
        analysis = analyze_garment_damage(
            file_bytes=img, filename="hoodie.jpg",
            damage_hint="Elbow / Sleeve Fray", style="Vintage",
        )
        self.assertEqual(analysis["confidence"], "high")
        self.assertIn("Elbow", analysis["damage_location"])

    def test_sleeve_demo_succeeds(self):
        img = make_image(color=(52, 57, 63))
        resp = client.post("/api/redesign",
            files={"image": ("hoodie.jpg", img, "image/jpeg")},
            data={"style": "Vintage", "provider": "demo",
                  "damage_location": "Elbow / Sleeve Fray"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["is_demo"])


# ---------------------------------------------------------------------------
# 4. Diagonal rip with irregular mask
# ---------------------------------------------------------------------------
class TestDiagonalRipMask(unittest.TestCase):

    def test_diagonal_mask_analysis(self):
        img = make_image(color=(100, 80, 60))
        mask_b = make_mask(region=(80, 50, 220, 100))
        analysis = analyze_garment_damage(
            file_bytes=img, filename="jacket.png",
            damage_hint="Auto-Detect", style="Streetwear",
            mask_bytes=mask_b,
        )
        self.assertEqual(analysis["confidence"], "high")
        self.assertTrue(analysis["user_specified"])

    def test_diagonal_mask_pixel_preservation(self):
        img = make_image(color=(100, 80, 60))
        mask_b = make_mask(region=(80, 50, 220, 100))
        out, mime = render_procedural_repair(
            image_bytes=img, mask_bytes=mask_b,
            style="Streetwear", feather_radius=0,
        )
        preserved, max_diff, count = verify_pixel_preservation(img, out, mask_b)
        self.assertTrue(preserved, f"Pixel changed outside mask: max_diff={max_diff}")

    def test_diagonal_mask_via_api(self):
        img = make_image(color=(100, 80, 60))
        resp = client.post("/api/redesign",
            files={"image": ("jacket.jpg", img, "image/jpeg")},
            data={"style": "Streetwear", "provider": "demo",
                  "mask": make_mask_b64(region=(80, 50, 220, 100))})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])


# ---------------------------------------------------------------------------
# 5. No clearly visible damage
# ---------------------------------------------------------------------------
class TestNoDamageDetected(unittest.TestCase):

    def test_uniform_image_flags_low_confidence(self):
        img = make_image(color=(180, 180, 180))
        analysis = analyze_garment_damage(
            file_bytes=img, filename="plain.jpg",
            damage_hint="Auto-Detect", style="Streetwear",
        )
        self.assertIn(analysis["confidence"], ("low", "medium"))

    def test_no_damage_demo_still_returns_200(self):
        img = make_image(color=(180, 180, 180))
        resp = client.post("/api/redesign",
            files={"image": ("plain.jpg", img, "image/jpeg")},
            data={"style": "Streetwear", "provider": "demo"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["is_demo"])


# ---------------------------------------------------------------------------
# 6. Explicitly marked repair region (high-confidence mask)
# ---------------------------------------------------------------------------
class TestExplicitlyMarkedRegion(unittest.TestCase):

    def test_mask_gives_high_confidence(self):
        img = make_image()
        mask_b = make_mask(region=(60, 120, 140, 200))
        analysis = analyze_garment_damage(
            file_bytes=img, filename="garment.jpg",
            damage_hint="Auto-Detect", style="Floral Embroidery",
            mask_bytes=mask_b,
        )
        self.assertEqual(analysis["confidence"], "high")
        self.assertFalse(analysis.get("clarification_needed", True))

    def test_mask_pixel_preservation(self):
        img = make_image()
        mask_b = make_mask(region=(60, 120, 140, 200))
        out, _ = render_procedural_repair(
            image_bytes=img, mask_bytes=mask_b,
            style="Floral Embroidery", feather_radius=0,
        )
        preserved, max_diff, _ = verify_pixel_preservation(img, out, mask_b)
        self.assertTrue(preserved, f"Non-zero diff outside mask: {max_diff}")

    def test_mask_api_uses_high_confidence(self):
        img = make_image()
        resp = client.post("/api/redesign",
            files={"image": ("garment.jpg", img, "image/jpeg")},
            data={"style": "Floral Embroidery", "provider": "demo",
                  "mask": make_mask_b64(region=(60, 120, 140, 200))})
        self.assertEqual(resp.status_code, 200)
        ga = resp.json()["garment_analysis"]
        self.assertEqual(ga["confidence"], "high")


# ---------------------------------------------------------------------------
# 7. Missing or invalid mask
# ---------------------------------------------------------------------------
class TestMissingOrInvalidMask(unittest.TestCase):

    def test_strict_mode_no_mask_raises_400(self):
        img = make_image()
        with self.assertRaises(HTTPException) as ctx:
            render_procedural_repair(
                image_bytes=img, mask_bytes=None,
                damage_coords=None, damage_location=None,
                center_fallback=False,
            )
        self.assertEqual(ctx.exception.status_code, 400)

    def test_invalid_mask_bytes_normalize_returns_none(self):
        result = normalize_mask(b"not-an-image", 300, 300)
        self.assertIsNone(result)

    def test_garbage_mask_api_gracefully_falls_back(self):
        img = make_image()
        resp = client.post("/api/redesign",
            files={"image": ("garment.jpg", img, "image/jpeg")},
            data={"style": "Streetwear", "provider": "demo",
                  "mask": "NOTVALIDBASE64!!!@#$"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["is_demo"])


# ---------------------------------------------------------------------------
# 8. Provider failure / timeout ? auto-fallback
# ---------------------------------------------------------------------------
class TestProviderFailureFallback(unittest.TestCase):

    def test_stability_timeout_triggers_auto_fallback(self):
        img = make_image()
        with patch("app.ai_service.generate_redesign_stability",
                   new=AsyncMock(side_effect=HTTPException(status_code=504, detail="Timed out"))):
            resp = client.post("/api/redesign",
                files={"image": ("shirt.jpg", img, "image/jpeg")},
                data={"style": "Streetwear", "provider": "auto"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["fallback_used"])
        self.assertTrue(data["is_demo"])

    def test_stability_402_no_credits_fallback(self):
        img = make_image()
        with patch("app.ai_service.generate_redesign_stability",
                   new=AsyncMock(side_effect=HTTPException(
                       status_code=402, detail="Insufficient credits"))):
            resp = client.post("/api/redesign",
                files={"image": ("shirt.jpg", img, "image/jpeg")},
                data={"style": "Floral Embroidery", "provider": "auto"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["fallback_used"])

    def test_stability_key_missing_returns_401(self):
        img = make_image()
        with patch("app.ai_service.get_current_stability_key", return_value=""):
            resp = client.post("/api/redesign",
                files={"image": ("shirt.jpg", img, "image/jpeg")},
                data={"style": "Streetwear", "provider": "stability"})
        self.assertIn(resp.status_code, (400, 401))


# ---------------------------------------------------------------------------
# Extra: generate_redesign_free must NOT call Pollinations
# ---------------------------------------------------------------------------
class TestFreeProviderNoPollinations(unittest.TestCase):

    def test_no_pollinations_request(self):
        img = make_image()
        requests_made = []

        async def mock_get(self, url, **kw):
            requests_made.append(url)
            raise RuntimeError("Should not make HTTP requests")

        async def run():
            with patch.object(httpx.AsyncClient, "get", mock_get):
                return await generate_redesign_free(
                    image_bytes=img,
                    prompt="repair the tear",
                    style="Streetwear",
                    garment_analysis={"damage_location": "Left Knee", "mask_bytes": None,
                                      "damage_coords": {"x": 0.4, "y": 0.7}},
                )

        out, mime, is_demo, pname, reason = asyncio.run(run())
        pollinations_calls = [u for u in requests_made if "pollinations" in str(u)]
        self.assertEqual(pollinations_calls, [], "generate_redesign_free called Pollinations!")
        self.assertGreater(len(out), 500)
        self.assertTrue(is_demo)


# ---------------------------------------------------------------------------
# Prompt quality
# ---------------------------------------------------------------------------
class TestBuildPrompt(unittest.TestCase):

    def test_prompt_says_edit_not_generate(self):
        prompt = build_prompt("Floral Embroidery", garment_analysis={
            "garment_type": "blue denim jeans",
            "damage_location": "Left Knee",
            "recommended_technique": "botanical embroidery",
        })
        self.assertIn("Edit the supplied photograph", prompt)
        self.assertIn("Repair ONLY", prompt)
        self.assertIn("Do NOT generate", prompt)
        self.assertIn("ALL undamaged areas", prompt)

    def test_custom_prompt_included(self):
        prompt = build_prompt("Custom", custom_prompt="Use gold thread", garment_analysis={})
        self.assertIn("gold thread", prompt)


if __name__ == "__main__":
    unittest.main()
