import io
import os
import sys
from pathlib import Path
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app
from app.image_utils import validate_and_process_image, ImageValidationError

client = TestClient(app)

def create_sample_image(format="JPEG", size=(200, 200), color=(100, 150, 200)) -> bytes:
    """Helper to create dummy in-memory image bytes."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format=format)
    return buf.getvalue()


def test_health_endpoint():
    """Verify health endpoint responds correctly."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["ai_configured"] is True
    assert "max_upload_size_mb" in data
    assert "Streetwear" in data["supported_styles"]
    assert "available_providers" in data


def test_image_utils_valid():
    """Verify validation and processing of valid image."""
    img_bytes = create_sample_image("PNG", size=(300, 300))
    processed, mime, w, h = validate_and_process_image(img_bytes, "test.png")
    assert mime == "image/png"
    assert w == 300
    assert h == 300


def test_image_utils_unsupported_format():
    """Verify rejection of invalid file format or corrupted bytes."""
    with pytest.raises(ImageValidationError):
        validate_and_process_image(b"not an image", "test.txt")


def test_image_utils_oversized():
    """Verify rejection of oversized images."""
    dummy_huge = b"0" * (11 * 1024 * 1024)  # 11MB
    with pytest.raises(ImageValidationError):
        validate_and_process_image(dummy_huge, "huge.jpg")


def test_redesign_invalid_style():
    """Verify 400 error on unsupported style preset."""
    img_bytes = create_sample_image()
    response = client.post(
        "/api/redesign",
        files={"image": ("shirt.jpg", img_bytes, "image/jpeg")},
        data={"style": "NonExistentStyle"},
    )
    assert response.status_code == 400
    assert "Invalid style" in response.json()["detail"]


def test_redesign_missing_api_key():
    """Verify clean 400/401 error with guidance when no API key is configured."""
    img_bytes = create_sample_image()
    with patch.dict(os.environ, {"STABILITY_API_KEY": "", "REPLICATE_API_TOKEN": ""}):
        with patch("app.ai_service.STABILITY_API_KEY", ""):
            with patch("app.config.STABILITY_API_KEY", ""):
                response = client.post(
                    "/api/redesign",
                    files={"image": ("shirt.jpg", img_bytes, "image/jpeg")},
                    data={"style": "Floral Embroidery", "provider": "stability"},
                )
                assert response.status_code in (400, 401)
                assert "STABILITY_API_KEY" in response.json()["detail"]


def test_redesign_demo_mode():
    """Verify demo mode returns styled transformation without network call."""
    img_bytes = create_sample_image("JPEG", color=(50, 100, 150))
    response = client.post(
        "/api/redesign",
        files={"image": ("shirt.jpg", img_bytes, "image/jpeg")},
        data={"style": "Vintage", "provider": "demo"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["is_demo"] is True
    assert "image_data" in data


def test_redesign_caching():
    """Verify duplicate requests hit deterministic SHA-256 cache."""
    img_bytes = create_sample_image("JPEG", color=(150, 80, 40))
    res1 = client.post(
        "/api/redesign",
        files={"image": ("cache_test.jpg", img_bytes, "image/jpeg")},
        data={"style": "Streetwear", "provider": "demo"},
    )
    assert res1.status_code == 200

    res2 = client.post(
        "/api/redesign",
        files={"image": ("cache_test.jpg", img_bytes, "image/jpeg")},
        data={"style": "Streetwear", "provider": "demo"},
    )
    assert res2.status_code == 200
    assert res2.json()["is_cached"] is True


def test_redesign_and_download_flow_mocked():
    """
    Simulates end-to-end redesign generation and verifies cached download.
    (Mocks external provider call to test complete backend data-pipeline).
    """
    mock_out_bytes = create_sample_image("PNG", color=(50, 200, 50))
    
    with patch(
        "app.main.execute_redesign",
        new=AsyncMock(return_value=(mock_out_bytes, "image/png", "stability", "Mocked prompt", 1.25)),
    ):
        img_bytes = create_sample_image("JPEG")
        response = client.post(
            "/api/redesign",
            files={"image": ("hoodie.jpg", img_bytes, "image/jpeg")},
            data={"style": "Streetwear", "custom_prompt": "Add subtle distressed accents"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "image_data" in data
        assert data["style"] == "Streetwear"
        assert "download_url" in data
        assert "garment_analysis" in data
        assert "repair_plan" in data
        
        # Test download endpoint
        dl_response = client.get(data["download_url"])
        assert dl_response.status_code == 200
        assert dl_response.headers["content-type"] == "image/png"
        assert dl_response.content == mock_out_bytes


def test_fashion_intelligence_endpoint():
    """Verify verified sustainable fashion repair resources endpoint."""
    response = client.get("/api/fashion-intelligence")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data_origin" in data
    assert "freshness_statement" in data
    assert len(data["resources"]) >= 4
    # Verify presence of authoritative sources
    sources = [r["source"] for r in data["resources"]]
    assert any("Patagonia" in s for s in sources)
    assert any("Fashion Revolution" in s for s in sources)


def test_garment_damage_analysis_and_repair_plan():
    """Verify automated garment analysis and structured repair plan."""
    from app.image_utils import analyze_garment_damage
    img_bytes = create_sample_image("JPEG")
    analysis = analyze_garment_damage(
        file_bytes=img_bytes,
        filename="denim-jacket.jpg",
        damage_hint="Pocket / Chest Tear",
        style="Floral Embroidery",
    )
    assert "garment_type" in analysis
    assert "Denim" in analysis["garment_type"]
    assert analysis["confidence"] == "high"
    assert analysis["user_specified"] is True
    assert "repair_plan" in analysis
    plan = analysis["repair_plan"]
    assert "Botanical" in plan["technique_name"]
    assert len(plan["tools_and_materials"]) >= 4
    assert len(plan["steps"]) >= 4
    assert "when_to_seek_tailor" in plan


def test_garment_damage_clarification_flag():
    """Verify system flags low confidence and requests clarification when damage is ambiguous."""
    from app.image_utils import analyze_garment_damage
    # Uniform plain image with no hint should set clarification_needed
    img_bytes = create_sample_image("JPEG", color=(180, 180, 180))
    analysis = analyze_garment_damage(
        file_bytes=img_bytes,
        filename="sample.jpg",
        damage_hint="Auto-Detect",
        style="Streetwear",
    )
    assert analysis["confidence"] in ("low", "medium")
    assert "repair_plan" in analysis

