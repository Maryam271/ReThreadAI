"""
ReThread AI — AI Service Layer
=======================================================================
IMPORTANT: PROVIDER CAPABILITIES AND LIMITATIONS
-------------------------------------------------
Pollinations.ai (free tier):
  Only offers TEXT-TO-IMAGE generation via a GET URL.  There is NO public
  image-conditioning, inpainting, or image-to-image endpoint.  Using
  Pollinations would generate a completely unrelated image.  IT IS NOT USED.

  The "free" engine uses render_procedural_repair() which genuinely edits
  the uploaded garment image with a mask-conditioned repair overlay.
  This is clearly labelled as a procedural preview, not AI inpainting.

Stability AI (v2beta):
  • Inpaint: /v2beta/stable-image/edit/inpaint — image + mask, localised.
  • Img2img: /v2beta/stable-image/generate/sd3 mode=image-to-image — global.

Replicate (instruct-pix2pix):
  Image-conditioned editing.  Does NOT support inpainting/masked editing
  natively; mask location is encoded in the prompt instead.
"""

import base64
import time
import asyncio
import hashlib
from typing import Optional
import httpx
from fastapi import HTTPException, status

from app.config import (
    STABILITY_API_KEY,
    REPLICATE_API_TOKEN,
    BACKEND_DIR,
    get_stability_key,
    get_replicate_token,
)
from app.image_utils import (
    detect_garment_characteristics,
    apply_artisanal_demo_filter,
    render_procedural_repair,
)

# In-memory cache: eliminates duplicate API calls & saves credits
REDESIGN_CACHE: dict[str, dict] = {}


def get_current_stability_key() -> str:
    return get_stability_key()


def get_current_replicate_token() -> str:
    return get_replicate_token()


# ---------------------------------------------------------------------------
# Style prompts (modify repair treatment, not garment identity)
# ---------------------------------------------------------------------------

STYLE_PROMPT_MAP = {
    "Streetwear": (
        "Apply authentic Sashiko running stitches and urban utility reinforcement patches "
        "directly over the damaged area, with tasteful distressed edge stabilization. "
        "High-end contemporary streetwear visible mending craftsmanship."
    ),
    "Floral Embroidery": (
        "Apply intricate colorful botanical wildflower and leaf embroidery threadwork "
        "stitched across the tear boundary. Realistic artisanal needlework with satin-stitch "
        "petals, stem stitches, and French knots."
    ),
    "Minimalist": (
        "Apply precision tone-on-tone re-weaving and subtle architectural bar-tack "
        "reinforcement at the tear. Quiet-luxury craftsmanship with invisible mending."
    ),
    "Vintage": (
        "Apply heritage sashiko running stitches in ecru thread over a durable underlay patch. "
        "Subtle sun-fade finish with nostalgic artisanal character."
    ),
    "Patchwork": (
        "Apply upcycled Japanese Boro-inspired patchwork: layered contrasting textile patches "
        "spanning the damaged area with visible sashiko reinforcement stitches."
    ),
    "Artistic": (
        "Apply expressive wearable-art embroidery: painterly textile motifs and decorative "
        "stitching bridging the damaged section in an avant-garde visible mending style."
    ),
    "Custom": (
        "Apply bespoke visible mending directly over the damaged area, "
        "preserving the garment structure with realistic textile repair."
    ),
}


def build_prompt(
    style: str,
    custom_prompt: str = "",
    garment_analysis: dict = None,
) -> str:
    """
    Builds a repair-specific, image-conditioned editing prompt.
    Explicitly instructs the model to EDIT the supplied photo rather than
    generate a new garment.  The mask is the primary spatial constraint.
    """
    ga = garment_analysis or {}
    gtype = ga.get("garment_type", "garment")
    loc = ga.get("damage_location", "damaged region")
    tech = ga.get("recommended_technique", "visible mending")
    coords = ga.get("damage_coords")

    if coords and isinstance(coords, dict) and "x" in coords and "y" in coords:
        x_pct = int(float(coords["x"]) * 100)
        y_pct = int(float(coords["y"]) * 100)
        loc_detail = f"{loc} (approximately {x_pct}% from left, {y_pct}% from top)"
    else:
        loc_detail = loc

    style_instruction = STYLE_PROMPT_MAP.get(style, STYLE_PROMPT_MAP["Custom"])

    base_repair = (
        f"Edit the supplied photograph of this exact {gtype}. "
        f"Repair ONLY the damaged fabric region indicated by the mask at the {loc_detail}. "
        f"Apply realistic {tech}: {style_instruction} "
        "Preserve the garment's identity, original silhouette, base fabric color, texture, "
        "weave pattern, seams, pockets, buttons, collar, and ALL undamaged areas exactly. "
        "The repair must follow the actual geometry of the torn area."
    )

    custom_part = ""
    if custom_prompt and custom_prompt.strip():
        custom_part = (
            f"Additional design instruction: {custom_prompt.strip()}. "
            "Integrate these details into the repair area only, without altering undamaged fabric."
        )

    no_gen = (
        "CRITICAL: Do NOT generate a person, human model, mannequin, new outfit, "
        "replacement garment, fashion photograph, or unrelated scene. "
        "Do NOT redesign or modify undamaged parts of the garment."
    )

    photo_note = (
        "Maintain consistent studio lighting, focus, and background from the original photo. "
        "No text, watermarks, or logos."
    )

    parts = [base_repair]
    if custom_part:
        parts.append(custom_part)
    parts.extend([no_gen, photo_note])
    return " ".join(parts)


def compute_cache_key(
    image_bytes: bytes,
    style: str,
    custom_prompt: str,
    strength: float,
    provider: str,
    damage_location: str = "",
    mask_bytes: Optional[bytes] = None,
) -> str:
    """Deterministic SHA-256 hash for deduplication and instant caching."""
    h = hashlib.sha256()
    h.update(image_bytes)
    h.update(style.encode("utf-8"))
    h.update(custom_prompt.strip().encode("utf-8"))
    h.update(f"{strength:.2f}".encode("utf-8"))
    h.update(provider.lower().strip().encode("utf-8"))
    h.update(damage_location.lower().strip().encode("utf-8"))
    if mask_bytes:
        if isinstance(mask_bytes, str):
            h.update(mask_bytes.encode("utf-8"))
        else:
            h.update(mask_bytes)
    return h.hexdigest()


class RedesignResult:
    """
    Standardised result container supporting both attribute access and
    9-tuple backward-compatible unpacking for tests and API routes.
    """
    def __init__(
        self,
        out_bytes: bytes,
        mime: str,
        provider: str,
        prompt: str,
        duration: float,
        fallback_used: bool = False,
        fallback_reason: str = "",
        is_demo: bool = False,
        is_cached: bool = False,
        garment_analysis: dict = None,
        repair_plan: dict = None,
    ):
        self.out_bytes = out_bytes
        self.mime = mime
        self.provider = provider
        self.prompt = prompt
        self.duration = duration
        self.fallback_used = fallback_used
        self.fallback_reason = fallback_reason
        self.is_demo = is_demo
        self.is_cached = is_cached
        self.garment_analysis = garment_analysis or {}
        self.repair_plan = repair_plan or {}

    def __iter__(self):
        return iter((
            self.out_bytes, self.mime, self.provider, self.prompt,
            self.duration, self.fallback_used, self.fallback_reason,
            self.is_demo, self.is_cached,
        ))

    def __getitem__(self, index):
        return tuple(self)[index]

    def __len__(self):
        return 9


# ---------------------------------------------------------------------------
# Free provider — procedural repair (image-conditioned, no API credits)
# ---------------------------------------------------------------------------

async def generate_redesign_free(
    image_bytes: bytes,
    prompt: str,
    style: str,
    custom_prompt: str = "",
    garment_analysis: dict = None,
    mask_bytes: Optional[bytes] = None,
) -> tuple[bytes, str, bool, str, str]:
    """
    Free image-conditioned garment repair preview.

    CRITICAL: Pollinations.ai only provides TEXT-TO-IMAGE via GET URL.
    There is no public image-conditioning or inpainting endpoint.
    Sending only a text prompt would generate a completely unrelated image,
    NOT an edit of the uploaded garment.  This would silently violate the
    garment-preservation requirement.  Pollinations is NOT called here.

    Instead, render_procedural_repair() is used — it genuinely edits the
    uploaded garment pixels with a mask-conditioned repair overlay.
    Every pixel outside the mask remains unchanged (feather_radius=0).

    Returns: (output_bytes, mime_type, is_demo, provider_name, fallback_reason)
    """
    ga = garment_analysis or {}
    effective_mask = mask_bytes or ga.get("mask_bytes")
    damage_coords = ga.get("damage_coords")
    damage_location = ga.get("damage_location", "")

    try:
        out_bytes, out_mime = render_procedural_repair(
            image_bytes=image_bytes,
            mask_bytes=effective_mask,
            style=style,
            damage_coords=damage_coords,
            damage_location=damage_location,
            garment_analysis=garment_analysis,
            feather_radius=0,
            center_fallback=True,
        )
        return (
            out_bytes,
            out_mime,
            True,
            "Free Procedural Repair Preview",
            (
                "The Free engine applies a procedural repair overlay directly to your "
                "garment photo (image-conditioned, not text-to-image). "
                "Add a Stability AI key in backend/.env for AI inpainting."
            ),
        )
    except Exception as exc:
        return (
            image_bytes, "image/png", True,
            "Passthrough (Preview failed)",
            f"Procedural preview failed: {str(exc)}. Original image returned.",
        )


def generate_redesign_demo(
    image_bytes: bytes,
    style: str,
    custom_prompt: str = "",
    garment_analysis: dict = None,
    mask_bytes: Optional[bytes] = None,
) -> tuple[bytes, str]:
    """
    Demo mode: artisanal PIL-based visible mending applied directly to the
    uploaded garment.  Instant, zero network, always succeeds.
    Clearly marked as Demo Mode in the response.
    """
    return apply_artisanal_demo_filter(
        file_bytes=image_bytes,
        style=style,
        custom_prompt=custom_prompt,
        garment_analysis=garment_analysis,
        damage_coords=(garment_analysis or {}).get("damage_coords"),
    )


# ---------------------------------------------------------------------------
# Stability AI provider
# ---------------------------------------------------------------------------

async def generate_redesign_stability(
    image_bytes: bytes,
    prompt: str,
    strength: float = 0.68,
    mask_bytes: Optional[bytes] = None,
) -> tuple[bytes, str]:
    """
    Calls Stability AI API.

    WITH mask_bytes  → /v2beta/stable-image/edit/inpaint
      image + mask (white=repair area, black=preserve).
      Best-effort unmasked region preservation by the model.

    WITHOUT mask_bytes → /v2beta/stable-image/generate/sd3 (img2img)
      Applies prompt globally at `strength`. Still image-conditioned on the
      uploaded garment, but less spatially precise.
    """
    api_key = get_current_stability_key()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Stability AI API key is not configured. "
                "Add STABILITY_API_KEY to backend/.env, "
                "or switch to Free Repair Preview."
            ),
        )

    if mask_bytes and len(mask_bytes) > 0:
        url = "https://api.stability.ai/v2beta/stable-image/edit/inpaint"
        headers = {"Authorization": f"Bearer {api_key}", "Accept": "image/*"}
        files = {
            "image": ("garment.png", image_bytes, "image/png"),
            "mask":  ("mask.png",    mask_bytes,  "image/png"),
        }
        data = {"prompt": prompt, "output_format": "png"}
    else:
        url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"
        headers = {"Authorization": f"Bearer {api_key}", "Accept": "image/*"}
        files = {"image": ("garment.png", image_bytes, "image/png")}
        data = {
            "prompt": prompt,
            "mode": "image-to-image",
            "strength": str(strength),
            "model": "sd3.5-large",
            "output_format": "png",
        }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, headers=headers, data=data, files=files)
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Stability AI timed out. Please retry or switch to Free Repair Preview.",
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Network error communicating with Stability AI: {str(exc)}",
            )

    if response.status_code == 200:
        return response.content, response.headers.get("content-type", "image/png")

    try:
        err_json = response.json()
        error_msg = (
            err_json.get("errors", [response.text])[0]
            if isinstance(err_json.get("errors"), list)
            else str(err_json)
        )
    except Exception:
        error_msg = response.text or f"HTTP {response.status_code}"

    if response.status_code == 401:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Invalid Stability AI credentials: {error_msg}. "
                                   "Verify STABILITY_API_KEY in backend/.env.")
    elif response.status_code == 402:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED,
                            detail="Stability AI account has insufficient credits. "
                                   "Top up at https://platform.stability.ai/account/credits "
                                   "or select 'Free Repair Preview'.")
    elif response.status_code == 429:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Rate limit reached with Stability AI. Please wait and retry.")
    else:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"Stability AI failed ({response.status_code}): {error_msg}")


# ---------------------------------------------------------------------------
# Replicate provider
# ---------------------------------------------------------------------------

async def generate_redesign_replicate(
    image_bytes: bytes,
    prompt: str,
    mask_bytes: Optional[bytes] = None,
) -> tuple[bytes, str]:
    """
    Calls Replicate API (instruct-pix2pix — image-conditioned editing).

    LIMITATION: This model does NOT support masked inpainting natively.
    The mask location is encoded in the prompt text as a spatial instruction.
    For precise masked repair use the Stability AI inpaint endpoint instead.
    """
    token = get_current_replicate_token()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Replicate API token is not configured.",
        )

    b64_img = base64.b64encode(image_bytes).decode("utf-8")
    data_uri = f"data:image/png;base64,{b64_img}"

    url = "https://api.replicate.com/v1/predictions"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "version": "30c1d0b916a6f8efce20493f5d61ee27491ab2a60437c13c588468b9810ec23f",
        "input": {
            "image": data_uri,
            "prompt": prompt,
            "image_guidance_scale": 1.5,
            "guidance_scale": 7.5,
        },
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code not in (200, 201):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Replicate API error: {resp.text}",
            )
        pred = resp.json()
        poll_url = pred["urls"]["get"]

        for _ in range(40):
            await asyncio.sleep(1.5)
            poll_resp = await client.get(poll_url, headers=headers)
            poll_data = poll_resp.json()
            status_str = poll_data.get("status")
            if status_str == "succeeded":
                output_url = poll_data["output"]
                if isinstance(output_url, list):
                    output_url = output_url[0]
                img_resp = await client.get(output_url)
                return img_resp.content, "image/png"
            elif status_str in ("failed", "canceled"):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Replicate generation failed: {poll_data.get('error')}",
                )

        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Replicate generation timed out.",
        )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

async def execute_redesign(
    image_bytes: bytes,
    style: str,
    custom_prompt: str = "",
    strength: float = 0.68,
    provider: str = "auto",
    garment_analysis: dict = None,
    mask_bytes: Optional[bytes] = None,
) -> RedesignResult:
    """
    Orchestrates the repair redesign with caching, multi-engine routing,
    and automatic fail-safe fallback.

    mask_bytes takes precedence over garment_analysis["mask_bytes"].
    Both are threaded through to the selected provider.
    """
    start_time = time.time()
    req_provider = (provider or "auto").strip().lower()
    damage_loc = (garment_analysis or {}).get("damage_location", "")

    # Resolve effective mask: explicit param wins over analysis-derived mask
    effective_mask = mask_bytes or (garment_analysis or {}).get("mask_bytes")

    cache_key = compute_cache_key(
        image_bytes, style, custom_prompt, strength, req_provider, damage_loc, effective_mask
    )
    if cache_key in REDESIGN_CACHE:
        cached = REDESIGN_CACHE[cache_key]
        return RedesignResult(
            out_bytes=cached["bytes"],
            mime=cached["mime"],
            provider=cached["provider"],
            prompt=cached["prompt"],
            duration=0.01,
            fallback_used=cached.get("fallback_used", False),
            fallback_reason=cached.get("fallback_reason", ""),
            is_demo=cached.get("is_demo", False),
            is_cached=True,
            garment_analysis=cached.get("garment_analysis", garment_analysis),
            repair_plan=cached.get("repair_plan", (garment_analysis or {}).get("repair_plan")),
        )

    prompt = build_prompt(style, custom_prompt, garment_analysis)
    fallback_used = False
    fallback_reason = ""
    is_demo = False

    # Route by provider
    if req_provider == "demo":
        out_bytes, mime = generate_redesign_demo(
            image_bytes, style, custom_prompt, garment_analysis, effective_mask
        )
        provider_name = "Studio Demo Engine"
        is_demo = True

    elif req_provider == "free":
        out_bytes, mime, is_demo, provider_name, fallback_reason = await generate_redesign_free(
            image_bytes, prompt, style, custom_prompt, garment_analysis, effective_mask
        )
        if is_demo:
            fallback_used = True

    elif req_provider == "stability":
        out_bytes, mime = await generate_redesign_stability(
            image_bytes, prompt, strength, effective_mask
        )
        provider_name = "Stability AI"

    elif req_provider == "replicate":
        out_bytes, mime = await generate_redesign_replicate(
            image_bytes, prompt, effective_mask
        )
        provider_name = "Replicate"

    else:
        # auto mode
        stab_key = get_current_stability_key()
        if stab_key:
            try:
                out_bytes, mime = await generate_redesign_stability(
                    image_bytes, prompt, strength, effective_mask
                )
                provider_name = "Stability AI"
            except HTTPException as e:
                if e.status_code in (401, 402, 429, 502, 503, 504):
                    fallback_used = True
                    if e.status_code == 402:
                        credit_msg = "Stability AI has 0 credits. Switched to Free Repair Preview."
                    elif e.status_code == 401:
                        credit_msg = "Stability AI key invalid. Switched to Free Repair Preview."
                    else:
                        credit_msg = f"Stability AI unavailable (HTTP {e.status_code}). Switched to Free Repair Preview."
                    out_bytes, mime, _, provider_name, free_err = await generate_redesign_free(
                        image_bytes, prompt, style, custom_prompt, garment_analysis, effective_mask
                    )
                    is_demo = True
                    fallback_reason = f"{credit_msg} {free_err}".strip()
                else:
                    raise
            except Exception as exc:
                fallback_used = True
                out_bytes, mime, _, provider_name, free_err = await generate_redesign_free(
                    image_bytes, prompt, style, custom_prompt, garment_analysis, effective_mask
                )
                is_demo = True
                fallback_reason = f"Stability AI error ({str(exc)}). {free_err}".strip()
        else:
            out_bytes, mime, is_demo, provider_name, fallback_reason = await generate_redesign_free(
                image_bytes, prompt, style, custom_prompt, garment_analysis, effective_mask
            )
            if is_demo:
                fallback_used = True

    elapsed = round(time.time() - start_time, 2)
    repair_plan_data = (garment_analysis or {}).get("repair_plan", {})

    REDESIGN_CACHE[cache_key] = {
        "bytes": out_bytes,
        "mime": mime,
        "provider": provider_name,
        "prompt": prompt,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "is_demo": is_demo,
        "garment_analysis": garment_analysis,
        "repair_plan": repair_plan_data,
    }

    return RedesignResult(
        out_bytes=out_bytes,
        mime=mime,
        provider=provider_name,
        prompt=prompt,
        duration=elapsed,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        is_demo=is_demo,
        is_cached=False,
        garment_analysis=garment_analysis,
        repair_plan=repair_plan_data,
    )


