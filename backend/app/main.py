import base64
import json
import uuid
import time
from typing import Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse

from app.config import (
    MAX_IMAGE_SIZE_MB,
    ALLOWED_EXTENSIONS,
    get_active_provider,
    get_available_providers,
    get_stability_key,
    get_replicate_token,
    is_ai_configured,
)
from app.image_utils import validate_and_process_image, analyze_garment_damage
from app.ai_service import execute_redesign, STYLE_PROMPT_MAP

app = FastAPI(
    title="ReThread AI API",
    description="Backend API for ReThread AI - Smart Garment Repair & Fashion Intelligence Studio",
    version="1.1.0",
)

# CORS configuration to allow local frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",  # permissive for local hackathon demo
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary in-memory cache for recent generated results
# Maps image_id -> {"bytes": bytes, "mime": str, "timestamp": float}
IMAGE_CACHE: Dict[str, Dict[str, Any]] = {}

def cleanup_cache():
    """Removes cached images older than 1 hour to prevent memory leaks."""
    cutoff = time.time() - 3600
    expired = [k for k, v in IMAGE_CACHE.items() if v.get("timestamp", 0) < cutoff]
    for k in expired:
        IMAGE_CACHE.pop(k, None)


# Curated, verified knowledge base of real sustainable fashion repair resources
VERIFIED_FASHION_INTELLIGENCE = [
    {
        "id": "patagonia-worn-wear",
        "title": "Patagonia Worn Wear DIY Repair Program & Hand-Mending Guides",
        "source": "Patagonia & iFixit",
        "category": "Visible Mending & Gear Repair",
        "type": "verified_external",
        "url": "https://wornwear.patagonia.com",
        "publication_date": "2024–2026 Active Resource Directory",
        "summary": (
            "Over 100 free, step-by-step repair manuals covering hand-sewing, blanket stitching, woven darning for knits, "
            "and patch-repair techniques to keep garments in active use rather than landfills."
        ),
        "key_technique": "Hand sewing, woven darning, fabric patch kits",
        "relevance": "Denim jackets, fleece outerwear, woven pants, heavy workwear",
    },
    {
        "id": "fashion-revolution-loved-clothes",
        "title": "Fashion Revolution: 'Loved Clothes Last' & Mend in Public Movement",
        "source": "Fashion Revolution (Orsola de Castro)",
        "category": "Circular Fashion Philosophy",
        "type": "verified_external",
        "url": "https://www.fashionrevolution.org",
        "publication_date": "Annual Global Campaign (Established 2017)",
        "summary": (
            "The premier international circular fashion initiative advocating visible mending and upcycling. Emphasizes "
            "celebrating garment wear as personal memories and personal style rather than hiding repairs."
        ),
        "key_technique": "Visible mending, Sashiko stitching, decorative surface threadwork",
        "relevance": "Everyday cotton garments, artistic clothing redesigns, sustainable wardrobes",
    },
    {
        "id": "sashiko-story-boro",
        "title": "Traditional Japanese Sashiko & Boro Structural Textile Reinforcement",
        "source": "Atsushi Futatsuya / Sashiko Story Guild",
        "category": "Heritage Textile Repair",
        "type": "verified_external",
        "url": "https://sashikostory.com",
        "publication_date": "Historical Heritage & Modern Practice",
        "summary": (
            "Authentic historical Japanese mending methodology. Utilizes rhythmic geometric running stitches (Sashiko) "
            "and layered rag patching (Boro) to structurally reinforce torn denim and coarse weave textiles."
        ),
        "key_technique": "Geometric running stitch, Boro fabric layering, underlay tension anchoring",
        "relevance": "Denim twill, canvas jackets, knee and elbow stress tears",
    },
    {
        "id": "vam-textile-conservation",
        "title": "V&A Museum Textile Conservation: Fiber Stabilization & Support Patching",
        "source": "Victoria & Albert Museum Conservation Department",
        "category": "Textile Preservation",
        "type": "verified_external",
        "url": "https://www.vam.ac.uk",
        "publication_date": "Archival Conservation Reference",
        "summary": (
            "Professional textile stabilization standards. Focuses on underlay backing stabilization, low-tension couching, "
            "and preventing tear propagation along warp and weft lines without damaging surrounding fibers."
        ),
        "key_technique": "Underlay stabilization, grain alignment, low-tension hand stitching",
        "relevance": "Delicate fabrics, vintage heirloom clothing, fine woven cottons",
    },
    {
        "id": "eileen-fisher-renew",
        "title": "Eileen Fisher Renew: Remanufacturing & Visible Mending Design Standards",
        "source": "Eileen Fisher Renew Circular Initiative",
        "category": "Upcycling & Remanufacturing",
        "type": "verified_external",
        "url": "https://www.eileenfisherrenew.com",
        "publication_date": "Ongoing Circular Initiative",
        "summary": (
            "Leading circular fashion brand workflow transforming damaged customer returns into bespoke upcycled garments "
            "through visible sashiko stitching, color-blocked patching, and felted darning."
        ),
        "key_technique": "Sashiko hand-stitching, visible seam reinforcement, creative patchwork",
        "relevance": "Linen, knit sweaters, minimalist tailored clothing",
    },
]


@app.get("/api/health")
async def health_check():
    """Health check endpoint exposing configuration status and available engines."""
    return {
        "status": "healthy",
        "ai_configured": is_ai_configured(),
        "active_provider": get_active_provider(),
        "available_providers": get_available_providers(),
        "has_stability_key": bool(get_stability_key()),
        "has_replicate_token": bool(get_replicate_token()),
        "max_upload_size_mb": MAX_IMAGE_SIZE_MB,
        "allowed_formats": sorted(list(ALLOWED_EXTENSIONS)),
        "supported_styles": list(STYLE_PROMPT_MAP.keys()),
        "fashion_intelligence_available": True,
    }


@app.get("/api/fashion-intelligence")
async def get_fashion_intelligence(
    garment_type: Optional[str] = None,
    style: Optional[str] = None,
):
    """
    Returns verified external fashion repair and visible mending references.
    Strictly distinguishes between verified external documentation, general atelier techniques,
    and AI-generated concepts. Transparently discloses source origin without claiming live scraping.
    """
    return {
        "success": True,
        "data_origin": "curated_verified_knowledge_base",
        "freshness_statement": (
            "Verified external references are curated from official active circular fashion and repair programs "
            "(Patagonia Worn Wear / iFixit, Fashion Revolution, Sashiko Story, V&A Museum Conservation, Eileen Fisher Renew). "
            "All links and publication references are verified authentic sources."
        ),
        "sources_count": len(VERIFIED_FASHION_INTELLIGENCE),
        "resources": VERIFIED_FASHION_INTELLIGENCE,
    }


@app.post("/api/redesign")
async def create_redesign(
    image: UploadFile = File(..., description="Uploaded garment image file"),
    style: str = Form("Streetwear", description="Selected redesign style preset"),
    custom_prompt: Optional[str] = Form(None, description="Optional custom vision text instruction"),
    strength: Optional[float] = Form(0.68, description="Transformation strength (0.3 to 0.85)"),
    provider: Optional[str] = Form("auto", description="Engine mode: auto, free, demo, stability, replicate"),
    damage_location: Optional[str] = Form("Auto-Detect", description="Identified or user-specified damage location"),
    damage_coords: Optional[str] = Form(None, description="User-marked tear coordinates JSON string"),
    mask: Optional[str] = Form(None, description="Base64 PNG mask data URL from canvas brush tool (white=repair, black=preserve)"),
):
    """
    Accepts one garment image, validates it, performs fashion damage diagnostic,
    generates a realistic visible mending redesign, and constructs a structured repair guide.
    """
    cleanup_cache()

    # 1. Validate style preset
    valid_styles = set(STYLE_PROMPT_MAP.keys())
    if style not in valid_styles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid style '{style}'. Must be one of: {', '.join(sorted(valid_styles))}",
        )

    # 2. Read and validate raw image bytes
    try:
        raw_bytes = await image.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}",
        )

    processed_bytes, mime, width, height = validate_and_process_image(
        file_bytes=raw_bytes,
        filename=image.filename or "",
    )

    # Parse optional user-marked tear coordinates
    coords_dict = None
    if damage_coords and isinstance(damage_coords, str):
        try:
            coords_dict = json.loads(damage_coords)
        except Exception:
            coords_dict = None

    # Parse optional canvas-drawn mask (base64 PNG data URL)
    mask_bytes = None
    if mask and isinstance(mask, str) and len(mask) > 50:
        try:
            mask_clean = mask
            if "," in mask_clean:
                mask_clean = mask_clean.split(",", 1)[1]
            mask_bytes = base64.b64decode(mask_clean)
        except Exception:
            mask_bytes = None

    # 3. Perform Garment & Damage Analysis
    garment_analysis = analyze_garment_damage(
        file_bytes=processed_bytes,
        filename=image.filename or "",
        damage_hint=damage_location or "Auto-Detect",
        style=style,
        damage_coords=coords_dict,
        mask_bytes=mask_bytes,
    )

    # 4. Constrain strength parameter
    clamped_strength = max(0.3, min(0.85, float(strength or 0.68)))

    # 5. Generate the redesign through AI service
    res = await execute_redesign(
        image_bytes=processed_bytes,
        style=style,
        custom_prompt=custom_prompt or "",
        strength=clamped_strength,
        provider=provider or "auto",
        garment_analysis=garment_analysis,
        mask_bytes=mask_bytes,
    )

    if hasattr(res, "out_bytes"):
        out_bytes = res.out_bytes
        out_mime = res.mime
        provider_name = res.provider
        prompt_used = res.prompt
        elapsed = res.duration
        fallback_used = res.fallback_used
        fallback_reason = res.fallback_reason
        is_demo = res.is_demo
        is_cached = res.is_cached
        res_analysis = getattr(res, "garment_analysis", garment_analysis) or garment_analysis
        res_repair_plan = getattr(res, "repair_plan", garment_analysis.get("repair_plan")) or garment_analysis.get("repair_plan")
    elif isinstance(res, tuple):
        out_bytes, out_mime, provider_name, prompt_used, elapsed = res[:5]
        fallback_used = res[5] if len(res) > 5 else False
        fallback_reason = res[6] if len(res) > 6 else ""
        is_demo = res[7] if len(res) > 7 else False
        is_cached = res[8] if len(res) > 8 else False
        res_analysis = garment_analysis
        res_repair_plan = garment_analysis.get("repair_plan")
    else:
        out_bytes, out_mime = res, "image/png"
        provider_name, prompt_used, elapsed = "unknown", "", 0.0
        fallback_used, fallback_reason, is_demo, is_cached = False, "", False, False
        res_analysis = garment_analysis
        res_repair_plan = garment_analysis.get("repair_plan")

    # 6. Cache result for direct downloads
    image_id = str(uuid.uuid4())
    IMAGE_CACHE[image_id] = {
        "bytes": out_bytes,
        "mime": out_mime,
        "timestamp": time.time(),
    }

    # 7. Format base64 data uri for instant frontend rendering
    b64_output = base64.b64encode(out_bytes).decode("utf-8")
    data_uri = f"data:{out_mime};base64,{b64_output}"

    safe_analysis = dict(res_analysis) if isinstance(res_analysis, dict) else {}
    if "mask_bytes" in safe_analysis:
        mask_raw = safe_analysis.pop("mask_bytes", None)
        if mask_raw and isinstance(mask_raw, (bytes, bytearray)):
            safe_analysis["mask_b64"] = base64.b64encode(mask_raw).decode("ascii")

    return {
        "success": True,
        "id": image_id,
        "image_data": data_uri,
        "style": style,
        "provider": provider_name,
        "prompt_used": prompt_used,
        "duration_seconds": elapsed,
        "download_url": f"/api/download/{image_id}",
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "is_demo": is_demo,
        "is_cached": is_cached,
        "garment_analysis": safe_analysis,
        "repair_plan": res_repair_plan,
    }


@app.get("/api/download/{image_id}")
async def download_image(image_id: str):
    """
    Safely serves the generated redesign image as a downloadable attachment.
    """
    if image_id not in IMAGE_CACHE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested generated image has expired or was not found.",
        )

    item = IMAGE_CACHE[image_id]
    ext = "png" if "png" in item["mime"] else "jpg"
    filename = f"rethread-redesign-{image_id[:8]}.{ext}"

    return Response(
        content=item["bytes"],
        media_type=item["mime"],
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "public, max-age=3600",
        },
    )
