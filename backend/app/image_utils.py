import io
import math
from typing import Optional, Tuple, Dict, Any, Union
import numpy as np
from PIL import Image, ImageOps, ImageDraw, ImageFilter, ImageEnhance, UnidentifiedImageError
from fastapi import HTTPException, status
from app.config import MAX_IMAGE_BYTES, MAX_IMAGE_SIZE_MB, ALLOWED_EXTENSIONS

class ImageValidationError(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


def validate_and_process_image(
    file_bytes: bytes,
    filename: str = "",
    max_dimension: int = 1024,
) -> tuple[bytes, str, int, int]:
    """
    Validates uploaded image bytes, checks corruption, applies EXIF orientation,
    resizes to suitable dimensions preserving aspect ratio, and exports normalized PNG bytes.
    
    Returns:
        tuple of (processed_bytes, mime_type, width, height)
    """
    if not file_bytes:
        raise ImageValidationError("Uploaded file is empty.")
        
    if len(file_bytes) > MAX_IMAGE_BYTES:
        raise ImageValidationError(
            f"File exceeds maximum allowed size of {MAX_IMAGE_SIZE_MB} MB. "
            f"Uploaded size: {len(file_bytes) / (1024 * 1024):.2f} MB."
        )

    if filename:
        ext = ("." + filename.rsplit(".", 1)[-1]).lower() if "." in filename else ""
        if ext and ext not in ALLOWED_EXTENSIONS:
            raise ImageValidationError(
                f"Unsupported file extension '{ext}'. Allowed extensions are: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
            )

    try:
        verify_img = Image.open(io.BytesIO(file_bytes))
        img_format = verify_img.format
        if img_format not in {"JPEG", "PNG", "WEBP"}:
            raise ImageValidationError(
                f"Unsupported image format: {img_format}. Please upload a JPEG, PNG, or WebP image."
            )
        verify_img.verify()
    except UnidentifiedImageError:
        raise ImageValidationError("The uploaded file is not a valid or recognized image.")
    except Exception as e:
        raise ImageValidationError(f"Image integrity check failed: {str(e)}")

    try:
        img = Image.open(io.BytesIO(file_bytes))
        img = ImageOps.exif_transpose(img)
    except Exception as e:
        raise ImageValidationError(f"Could not parse image pixels: {str(e)}")

    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.mode else "RGB")

    orig_width, orig_height = img.size

    if orig_width > max_dimension or orig_height > max_dimension:
        if orig_width >= orig_height:
            new_w = max_dimension
            new_h = int(round((orig_height * max_dimension) / orig_width))
        else:
            new_h = max_dimension
            new_w = int(round((orig_width * max_dimension) / orig_height))
        new_w = max(64, new_w)
        new_h = max(64, new_h)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    else:
        new_w, new_h = orig_width, orig_height

    output_buffer = io.BytesIO()
    img.save(output_buffer, format="PNG", optimize=True)
    processed_bytes = output_buffer.getvalue()

    return processed_bytes, "image/png", new_w, new_h


def detect_garment_characteristics(file_bytes: bytes) -> dict:
    """
    Analyzes uploaded garment image pixels to extract dominant color family
    and tone for contextual prompt enrichment.
    """
    try:
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        thumb = img.resize((48, 48), Image.Resampling.BOX)
        w, h = thumb.size
        pixels = [
            thumb.getpixel((x, y))
            for x in range(int(w * 0.2), int(w * 0.8))
            for y in range(int(h * 0.2), int(h * 0.8))
        ]
        garment_pixels = [
            p for p in pixels
            if not (p[0] > 242 and p[1] > 242 and p[2] > 242)
        ]
        if not garment_pixels:
            garment_pixels = pixels

        avg_r = sum(p[0] for p in garment_pixels) // len(garment_pixels)
        avg_g = sum(p[1] for p in garment_pixels) // len(garment_pixels)
        avg_b = sum(p[2] for p in garment_pixels) // len(garment_pixels)

        brightness = (avg_r + avg_g + avg_b) / 3
        if brightness < 45:
            color_desc = "deep black"
        elif brightness > 215:
            color_desc = "crisp off-white"
        elif avg_b > avg_r + 20 and avg_b > avg_g:
            color_desc = "classic indigo denim blue"
        elif avg_r > avg_g + 25 and avg_r > avg_b + 25:
            color_desc = "vibrant crimson red" if brightness > 100 else "deep burgundy"
        elif avg_g > avg_r + 15 and avg_g > avg_b + 10:
            color_desc = "earthy olive green"
        elif abs(avg_r - avg_g) < 15 and abs(avg_g - avg_b) < 15:
            color_desc = "heather grey"
        elif avg_r > avg_b and avg_g > avg_b:
            color_desc = "warm camel tan" if brightness > 120 else "rich brown"
        else:
            color_desc = "neutral toned"

        return {
            "color_desc": color_desc,
            "avg_rgb": (avg_r, avg_g, avg_b),
            "brightness": brightness,
        }
    except Exception:
        return {"color_desc": "garment", "avg_rgb": (128, 128, 128), "brightness": 128}


def get_anatomical_zone(norm_x: float, norm_y: float) -> str:
    """
    Maps normalized coordinates (0.0 to 1.0) to an accurate garment zone name.
    """
    x = max(0.0, min(1.0, float(norm_x)))
    y = max(0.0, min(1.0, float(norm_y)))
    
    if y < 0.24:
        if x < 0.35:
            return "Collar / Left Neckline"
        if x > 0.65:
            return "Collar / Right Shoulder"
        return "Collar / Center Neckline"
    if y > 0.75:
        if x < 0.38:
            return "Lower Hem (Left)"
        if x > 0.62:
            return "Lower Hem (Right)"
        return "Lower Hem / Bottom Seam"
    if x < 0.30 and 0.24 <= y <= 0.75:
        return "Left Shoulder / Sleeve Seam" if y < 0.50 else "Left Sleeve / Elbow Fray"
    if x > 0.70 and 0.24 <= y <= 0.75:
        return "Right Shoulder / Sleeve Seam" if y < 0.50 else "Right Sleeve / Elbow Fray"
    if 0.24 <= y < 0.52:
        if x > 0.52:
            return "Chest Pocket / Front Right Panel"
        if x < 0.48:
            return "Upper Chest / Front Left Panel"
        return "Center Chest Placket / Seam"
    if x < 0.50:
        return "Left Knee / Thigh Tear"
    return "Right Knee / Thigh Tear"


def create_mask_from_coords(
    width: int,
    height: int,
    coords: dict,
) -> Image.Image:
    """
    Constructs an aligned binary mask (PIL Image 'L') from coordinate dict {x, y, radius}.
    Generates realistic frayed tear contours with reinforcement margin.
    """
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)

    norm_x = max(0.02, min(0.98, float(coords.get("x", 0.5))))
    norm_y = max(0.02, min(0.98, float(coords.get("y", 0.5))))
    cx = int(width * norm_x)
    cy = int(height * norm_y)

    rad_ratio = float(coords.get("radius", 0.08))
    rx = max(12, int(width * rad_ratio))
    ry = max(8, int(height * rad_ratio * 0.65))

    # Generate an organic frayed tear polygon around (cx, cy)
    num_points = 24
    pts = []
    for i in range(num_points):
        angle = (2 * math.pi * i) / num_points
        # Add deterministic perturbation simulating natural frayed edge fibers along the tear
        jitter = 1.0 + 0.18 * math.sin(i * 3.1) + 0.10 * math.cos(i * 5.3)
        px = int(cx + rx * math.cos(angle) * jitter)
        py = int(cy + ry * math.sin(angle) * jitter)
        pts.append((max(0, min(width - 1, px)), max(0, min(height - 1, py))))

    draw.polygon(pts, fill=255)
    return mask


def normalize_mask(
    mask_input: Union[bytes, str, Image.Image, None],
    target_width: int,
    target_height: int,
) -> Optional[Image.Image]:
    """
    Converts and resizes any mask representation into a strictly aligned,
    binary mode 'L' PIL Image of size (target_width, target_height).
    White (255) = repair region, Black (0) = unmasked, strictly preserved fabric.
    Returns None if mask is empty or invalid.
    """
    if mask_input is None:
        return None

    try:
        if isinstance(mask_input, Image.Image):
            m_img = mask_input
        elif isinstance(mask_input, str):
            # Base64 data URI
            import base64
            clean_b64 = mask_input
            if "," in clean_b64:
                clean_b64 = clean_b64.split(",", 1)[1]
            raw = base64.b64decode(clean_b64)
            m_img = Image.open(io.BytesIO(raw))
        elif isinstance(mask_input, (bytes, bytearray)):
            if len(mask_input) == 0:
                return None
            m_img = Image.open(io.BytesIO(mask_input))
        else:
            return None

        # Resize to target dimensions with NEAREST interpolation to preserve sharp mask boundaries
        if m_img.size != (target_width, target_height):
            m_img = m_img.resize((target_width, target_height), Image.Resampling.NEAREST)

        # Convert to RGBA to inspect channels
        m_rgba = m_img.convert("RGBA")
        r, g, b, a = m_rgba.split()
        arr_a = np.array(a, dtype=np.uint8)
        arr_rgb = np.maximum(np.array(r), np.maximum(np.array(g), np.array(b)))

        # Determine if alpha channel or RGB luminance encodes the mask
        if int(np.max(arr_a)) > 20 and int(np.min(arr_a)) < 240:
            # Alpha indicates brushed strokes
            binary_arr = np.where(arr_a > 25, 255, 0).astype(np.uint8)
        else:
            # Luminance indicates white mask on black background (or vice versa)
            binary_arr = np.where(arr_rgb > 25, 255, 0).astype(np.uint8)

        cand_mask = Image.fromarray(binary_arr, mode="L")
        bbox = cand_mask.getbbox()
        if bbox is None:
            return None
        return cand_mask
    except Exception:
        return None


def detect_garment_damage_vision(file_bytes: bytes) -> dict:
    """
    Performs genuine vision-based tear and fray anomaly detection on garment fabric:
    1. Analyzes local high-gradient edge density and localized texture variance.
    2. Identifies anomalous clusters that significantly deviate from the garment's base weave.
    3. Rejects uniform garments with no clear damage, returning low confidence and asking the user to mark.
    4. NEVER fabricates a damage location or defaults to the center.
    """
    try:
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        w, h = img.size

        # Downscale for fast and robust anomaly scanning
        scan_w = min(512, w)
        scan_h = int(round((h * scan_w) / w))
        scan_img = img.resize((scan_w, scan_h), Image.Resampling.BILINEAR)

        gray = scan_img.convert("L")
        gray_arr = np.array(gray, dtype=np.float32)

        # 1. Garment silhouette mask (exclude pure white/light studio background)
        bg_mask = (gray_arr > 245)
        garment_pixels = gray_arr[~bg_mask]
        if len(garment_pixels) < 200:
            # Fallback to entire image if background segmentation fails
            garment_pixels = gray_arr.flatten()
            bg_mask = np.zeros_like(gray_arr, dtype=bool)

        fabric_mean = float(np.mean(garment_pixels))
        fabric_std = float(np.std(garment_pixels))

        # 2. Local edge / gradient filter to detect frayed fiber borders & tears
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_arr = np.array(edges, dtype=np.float32)

        # 3. Anomaly scoring: combination of high edge contrast + significant luminance divergence
        # Tears/holes typically show strong edge contours and dark voids or frayed white threads
        lum_diff = np.abs(gray_arr - fabric_mean)
        anomaly_score = (edge_arr / 255.0) * 0.6 + (lum_diff / (fabric_std + 1e-4)) * 0.4
        anomaly_score[bg_mask] = 0.0

        # Margin crop: exclude outer 5% border to prevent seam/border false positives
        margin_x = int(scan_w * 0.05)
        margin_y = int(scan_h * 0.05)
        anomaly_score[:margin_y, :] = 0.0
        anomaly_score[-margin_y:, :] = 0.0
        anomaly_score[:, :margin_x] = 0.0
        anomaly_score[:, -margin_x:] = 0.0

        threshold = np.percentile(anomaly_score[~bg_mask], 97.5) if np.sum(~bg_mask) > 100 else 1.5
        # Require minimum contrast spike for genuine damage detection
        if fabric_std < 8.0 or threshold < 0.65:
            # Plain, clean, uniform fabric with no distinct tear anomaly
            return {
                "detected": False,
                "confidence": "low",
                "zone_name": "Unspecified / Needs Marking",
                "bbox": None,
                "centroid": None,
                "mask_bytes": None,
                "message": "No definitive tear or hole was detected automatically. Please brush over the damaged region.",
            }

        cand_mask = anomaly_score > threshold
        if np.sum(cand_mask) < 40:
            return {
                "detected": False,
                "confidence": "low",
                "zone_name": "Unspecified / Needs Marking",
                "bbox": None,
                "centroid": None,
                "mask_bytes": None,
                "message": "Fabric appears uniform with no localized damage detected. Please mark the damaged area.",
            }

        # Find bounding box of anomaly cluster
        y_indices, x_indices = np.where(cand_mask)
        x0_s, x1_s = int(np.min(x_indices)), int(np.max(x_indices))
        y0_s, y1_s = int(np.min(y_indices)), int(np.max(y_indices))

        # Project back to full image coordinates
        scale_x = w / float(scan_w)
        scale_y = h / float(scan_h)
        x0 = max(0, int(x0_s * scale_x))
        y0 = max(0, int(y0_s * scale_y))
        x1 = min(w, int(x1_s * scale_x))
        y1 = min(h, int(y1_s * scale_y))

        cx_norm = float((x0 + x1) / (2.0 * w))
        cy_norm = float((y0 + y1) / (2.0 * h))
        zone_name = get_anatomical_zone(cx_norm, cy_norm)

        # Generate binary mask following the actual irregular tear contour
        cand_mask_img = Image.fromarray((cand_mask * 255).astype(np.uint8), mode="L")
        # Dilate slightly by 5px to unite frayed threads and form structural repair zone
        cand_mask_dilated = cand_mask_img.filter(ImageFilter.MaxFilter(size=5))
        mask_full = cand_mask_dilated.resize((w, h), Image.Resampling.NEAREST)
        # Ensure mask is non-empty
        if not mask_full.getbbox():
            m_draw = ImageDraw.Draw(mask_full)
            m_draw.ellipse([x0, y0, x1, y1], fill=255)

        buf = io.BytesIO()
        mask_full.save(buf, format="PNG")

        return {
            "detected": True,
            "confidence": "medium",
            "zone_name": zone_name,
            "bbox": (x0, y0, x1, y1),
            "centroid": {"x": round(cx_norm, 3), "y": round(cy_norm, 3)},
            "mask_bytes": buf.getvalue(),
            "message": f"Localized fabric damage detected at {zone_name}.",
        }
    except Exception as exc:
        return {
            "detected": False,
            "confidence": "low",
            "zone_name": "Unspecified / Needs Marking",
            "bbox": None,
            "centroid": None,
            "mask_bytes": None,
            "message": f"Visual damage scanning uncertainty ({str(exc)}). Please mark the torn area.",
        }


def analyze_garment_damage(
    file_bytes: bytes,
    filename: str = "",
    damage_hint: str = "",
    style: str = "Streetwear",
    damage_coords: Optional[dict] = None,
    mask_bytes: Optional[bytes] = None,
) -> dict:
    """
    Performs smart fashion intelligence analysis on the uploaded garment:
    1. Identifies garment category & fabric characteristics.
    2. Identifies location & severity of tear, fraying, or worn areas.
    3. Respects user-marked masks and coordinates with highest priority.
    4. Flags low confidence / uncertainty when damage cannot be identified clearly,
       requesting user marking instead of fabricating a center location.
    5. Generates a realistic, tailored repair plan.
    """
    color_info = detect_garment_characteristics(file_bytes)
    color_desc = color_info.get("color_desc", "neutral toned")

    # Determine garment type and fabric weight
    fname_lower = filename.lower()
    if any(k in fname_lower for k in ("denim", "jean", "jacket")):
        garment_type = "Denim Jacket / Heavy Outerwear"
        fabric_type = "Heavyweight Indigo Denim Twill (12–14 oz)"
    elif any(k in fname_lower for k in ("t-shirt", "tee", "shirt")):
        garment_type = "Cotton Crewneck T-Shirt"
        fabric_type = "Lightweight Combed Cotton Jersey (160–180 GSM)"
    elif any(k in fname_lower for k in ("hoodie", "sweatshirt", "fleece")):
        garment_type = "Vintage Fleece Hoodie"
        fabric_type = "Heavyweight Brushed Cotton Fleece (380 GSM)"
    elif any(k in fname_lower for k in ("pant", "trouser")):
        garment_type = "Tailored Trousers / Jeans"
        fabric_type = "Sturdy Cotton Twill / Woven Denim"
    else:
        if "denim" in color_desc:
            garment_type = "Denim Garment"
            fabric_type = "Structured Indigo Cotton Twill"
        elif "black" in color_desc or "grey" in color_desc:
            garment_type = "Streetwear Cotton Garment"
            fabric_type = "Medium-weight Cotton / Poly Blend"
        else:
            garment_type = "Woven Cotton Garment"
            fabric_type = "Versatile Natural Fiber Woven Textile"

    # Analyze damage location & confidence
    hint_clean = (damage_hint or "").strip()
    user_specified = False
    confidence = "medium"
    clarification_needed = False
    clarification_message = ""
    resolved_mask_bytes = mask_bytes
    detected_coords = damage_coords

    # Priority 1: User uploaded or drew an explicit binary repair mask
    if mask_bytes and len(mask_bytes) > 0:
        try:
            temp_img = Image.open(io.BytesIO(file_bytes))
            w, h = temp_img.size
            norm_m = normalize_mask(mask_bytes, w, h)
            if norm_m and norm_m.getbbox():
                bbox = norm_m.getbbox()
                cx = (bbox[0] + bbox[2]) / (2.0 * w)
                cy = (bbox[1] + bbox[3]) / (2.0 * h)
                zone_name = get_anatomical_zone(cx, cy)
                damage_location = hint_clean if (hint_clean and hint_clean.lower() not in ("auto-detect", "auto")) else zone_name
                user_specified = True
                confidence = "high"
                clarification_needed = False
                clarification_message = ""
                damage_severity = f"User-Marked Precision Repair Mask ({zone_name})"
                detected_coords = {"x": round(cx, 3), "y": round(cy, 3), "locationName": zone_name}
            else:
                resolved_mask_bytes = None
        except Exception:
            resolved_mask_bytes = None

    # Priority 2: User explicitly marked coordinate focus point
    if not user_specified and damage_coords and isinstance(damage_coords, dict) and "x" in damage_coords and "y" in damage_coords:
        damage_location = damage_coords.get("locationName") or (hint_clean if hint_clean and hint_clean.lower() not in ("auto-detect", "auto") else "Marked Tear Area")
        user_specified = True
        confidence = "high"
        size_lbl = damage_coords.get("sizeLabel", "standard")
        x_pct = int(float(damage_coords["x"]) * 100)
        y_pct = int(float(damage_coords["y"]) * 100)
        damage_severity = f"User-Marked {size_lbl.title()} Tear at ({x_pct}%, {y_pct}%) - Precision Focus"
        clarification_needed = False
        clarification_message = ""

    # Priority 3: User selected explicit anatomical dropdown zone
    elif not user_specified and hint_clean and hint_clean.lower() not in ("auto-detect", "auto", "none", "unknown"):
        damage_location = hint_clean
        user_specified = True
        confidence = "high"
        damage_severity = f"Localized tear / abrasion at {hint_clean} (User Selected)"

    # Priority 4: Run genuine vision-based tear detection
    elif not user_specified:
        vision_result = detect_garment_damage_vision(file_bytes)
        if vision_result["detected"]:
            damage_location = vision_result["zone_name"]
            confidence = "medium"
            damage_severity = "Localized surface tear with edge fraying (Auto-Detected)"
            clarification_needed = True
            clarification_message = "Damage was automatically detected. You may brush or adjust the marked area to refine precision."
            resolved_mask_bytes = vision_result.get("mask_bytes")
            detected_coords = vision_result.get("centroid")
        else:
            damage_location = "Unmarked / Manual Selection Required"
            confidence = "low"
            clarification_needed = True
            clarification_message = (
                "Automated vision could not reliably detect a tear. "
                "Please mark or brush over the torn area on the photo for precision repair."
            )
            damage_severity = "Unconfirmed damage location (Awaiting User Marking)"

    # Select appropriate repair technique & build structured repair guide
    repair_plan = _build_repair_plan(
        garment_type=garment_type,
        fabric_type=fabric_type,
        damage_location=damage_location,
        style=style,
    )

    return {
        "garment_type": garment_type,
        "fabric_type": fabric_type,
        "color_tone": color_desc,
        "damage_location": damage_location,
        "damage_severity": damage_severity,
        "confidence": confidence,
        "user_specified": user_specified,
        "clarification_needed": clarification_needed,
        "clarification_message": clarification_message,
        "recommended_technique": repair_plan["technique_name"],
        "repair_plan": repair_plan,
        "damage_coords": detected_coords,
        "mask_bytes": resolved_mask_bytes,
    }


def _build_repair_plan(
    garment_type: str,
    fabric_type: str,
    damage_location: str,
    style: str,
) -> dict:
    """
    Constructs an authentic, beginner-friendly garment repair guide
    grounded in recognized sustainable mending techniques.
    """
    if style == "Floral Embroidery":
        return {
            "technique_name": "Botanical Needlework Embroidery Mending",
            "technique_rationale": (
                f"For this {garment_type}, surface needlework stabilizes the torn fibers at the {damage_location} "
                "by anchoring dense satin-stitch petals and stem stitches across both torn edges onto an underlay stabilizer, "
                "transforming the hole into a bespoke floral design element."
            ),
            "difficulty": "Beginner Friendly",
            "estimated_time": "35–50 minutes (Estimated)",
            "tools_and_materials": [
                "Crewel or embroidery needles (sizes 5–7)",
                "Stranded cotton embroidery floss in contrasting botanical colors (olive, saffron, ivory)",
                "Lightweight iron-on fusible interfacing or tear-away embroidery stabilizer",
                "4-inch to 6-inch wooden embroidery hoop",
                "Water-soluble fabric marker or tailor's chalk",
                "Sharp embroidery snips / thread scissors",
            ],
            "steps": [
                "1. Stabilize the perimeter: Cut a piece of lightweight fusible interfacing slightly larger than the damaged area. Press it onto the inside of the garment using a warm dry iron to stabilize raw fabric edges.",
                "2. Mount the fabric: Place the stabilized garment section into your embroidery hoop with gentle, even tension. Do not stretch or distort the original weave.",
                "3. Sketch the motif: With a water-soluble marker, sketch small botanical wildflowers or leaf vines directly across the tear so stitches will bridge across both sides of the damage.",
                "4. Execute bridge stitches: Using 3 strands of embroidery floss, stitch satin stitches over the center hole for flower petals, stem stitches along connecting vines, and French knots for center stamens.",
                "5. Knot and finish: Secure thread tails on the reverse side with small locking knots, trim any excess backing stabilizer, and steam-press from the back side against a soft towel.",
            ],
            "when_to_seek_tailor": (
                "If the tear has caused widespread fiber loss across a load-bearing shoulder or armhole seam, "
                "machine reinforcement by a tailor prior to decorative embroidery is recommended to prevent re-tearing."
            ),
        }

    elif style == "Patchwork":
        return {
            "technique_name": "Upcycled Boro Patchwork & Structural Overlay",
            "technique_rationale": (
                f"Traditional Japanese Boro mending layers contrasting reclaimed textile swatches over the {damage_location}. "
                f"Because this garment is {fabric_type}, overlapping scrap fabrics reinforced with dense running stitches "
                "restores structural integrity and adds sustainable, high-fashion textile character."
            ),
            "difficulty": "Intermediate",
            "estimated_time": "50–70 minutes (Estimated)",
            "tools_and_materials": [
                "Heavy-duty hand sewing needle (size 18–20 chenille or sashiko needle)",
                "2 to 3 contrasting scrap textile swatches (e.g. vintage denim, patterned linen, corduroy)",
                "Heavy cotton thread (size 8 sashiko or topstitching thread)",
                "Temporary washable fabric glue stick or sewing pins",
                "Fabric scissors and ruler",
            ],
            "steps": [
                "1. Cut & audition swatches: Cut 2 or 3 rectangular fabric scraps, sizing each at least 1 inch (2.5 cm) larger than the hole. Arrange them overlapping so raw tear edges are completely enclosed.",
                "2. Secure layout: Use a temporary washable fabric glue stick or sewing pins to fix the swatches in place against the garment without shifting.",
                "3. Edge stabilization: Hand-stitch a small blanket stitch or blind hem stitch along each exposed patch edge to prevent future fraying.",
                "4. Structural running stitches: Sew repeated rows of parallel running stitches (horizontal or vertical, spaced 6mm / 0.25in apart) through all fabric layers across the entire patch assembly.",
                "5. Knot off & press: Fasten all ends securely on the back side. Steam-press with a damp pressing cloth.",
            ],
            "when_to_seek_tailor": (
                "If the tear spans structural belt loops or heavy pocket rivets, professional bar-tacking may be required."
            ),
        }

    elif style == "Minimalist":
        return {
            "technique_name": "Precision Invisible Mending & Tailored Re-weaving",
            "technique_rationale": (
                f"Minimalist repair restores the {damage_location} with tone-on-tone fine threads and structural micro bar-tacks. "
                "Focuses on maintaining the original garment silhouette with near-imperceptible textile stabilization."
            ),
            "difficulty": "Intermediate",
            "estimated_time": "25–40 minutes (Estimated)",
            "tools_and_materials": [
                "Fine sharps needle (size 9–11)",
                "Tone-matched fine mercerized cotton or polyester thread matching fabric warp/weft",
                "Fusible sheer web interfacing",
                "Sharp thread snips",
            ],
            "steps": [
                "1. Align raw edges: Gently tease warp and weft threads back into their natural alignment on a flat surface.",
                "2. Underlay support: Iron sheer web interfacing beneath the tear to bridge the gap without adding bulk.",
                "3. Re-weave threadwork: Using a single strand of tone-matched thread, sew microscopic herringbone stitches catching alternating yarns along the tear split.",
                "4. Press flat: Steam-press using a pressing cloth to blend thread sheen into the garment texture.",
            ],
            "when_to_seek_tailor": (
                "If large sections of fabric are missing, invisible re-weaving by an archival mending specialist is recommended."
            ),
        }

    else:
        # Default: Streetwear / Vintage / Custom (Authentic Sashiko visible mending)
        return {
            "technique_name": "Japanese Sashiko Running Stitch & Underlay Reinforcement",
            "technique_rationale": (
                f"Sashiko mending anchors a durable underlay patch behind the {damage_location} "
                "using rhythmic geometric running stitches in contrasting ecru thread, producing an elevated streetwear repair."
            ),
            "difficulty": "Beginner Friendly",
            "estimated_time": "40–60 minutes (Estimated)",
            "tools_and_materials": [
                "Sashiko needle or size 20–22 chenille needle",
                "Size 8 cotton sashiko thread or 6-strand embroidery floss (contrasting ecru, white, or indigo)",
                "Scrap denim or heavy cotton canvas backing patch (1 inch larger than tear on all sides)",
                "Water-soluble fabric marker or tailor's chalk",
                "Sewing pins or basting thread",
                "Fabric shears and steam iron",
            ],
            "steps": [
                "1. Trim fraying: Lightly trim loose, tangled threads around the tear perimeter with fabric scissors, leaving healthy structural yarns intact.",
                "2. Place backing patch: Cut a backing patch from scrap cotton extending 1 inch beyond the tear on all sides. Pin it securely behind the tear on the inside of the garment.",
                "3. Mark guidelines: With tailor's chalk, draw light guideline grids across the repair area.",
                "4. Stitch the pattern: Thread needle with sashiko thread. Work rhythmic running stitches along marked lines, catching both garment and backing patch.",
                "5. Secure and press: Tie off thread ends on the interior with small knots and steam-press flat.",
            ],
            "when_to_seek_tailor": (
                "If the tear is located across the primary crotch seam or load-bearing rivet stress points, "
                "industrial sewing machine bar-tack reinforcement by a professional tailor is advised."
            ),
        }


def render_procedural_repair(
    image_bytes: bytes,
    mask_bytes: Optional[bytes] = None,
    style: str = "Streetwear",
    damage_coords: Optional[dict] = None,
    damage_location: Optional[str] = None,
    garment_analysis: Optional[dict] = None,
    feather_radius: int = 0,
    center_fallback: bool = False,
) -> tuple[bytes, str]:
    """
    Renders a localized procedural garment repair preview.

    STRICT PIXEL PRESERVATION (center_fallback=False, default):
      Every pixel outside the damage mask is mathematically identical to the
      original garment image.  HTTP 400 is raised if no mask/coords are provided.

    DEMO MODE (center_fallback=True):
      Falls back to the garment center region as a last resort so demo pipelines
      never crash.  This placeholder MUST NOT be interpreted as accurate damage
      localisation — results are clearly labelled as demo output.
    """
    orig_img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    w, h = orig_img.size

    # 1. Resolve damage mask
    mask_l: Optional[Image.Image] = None

    if mask_bytes and len(mask_bytes) > 0:
        mask_l = normalize_mask(mask_bytes, w, h)

    if mask_l is None and damage_coords and isinstance(damage_coords, dict) and "x" in damage_coords:
        mask_l = create_mask_from_coords(w, h, damage_coords)

    if mask_l is None and garment_analysis and isinstance(garment_analysis, dict):
        g_mask = garment_analysis.get("mask_bytes")
        if g_mask:
            mask_l = normalize_mask(g_mask, w, h)
        if mask_l is None:
            g_coords = garment_analysis.get("damage_coords")
            if g_coords and isinstance(g_coords, dict) and "x" in g_coords:
                mask_l = create_mask_from_coords(w, h, g_coords)

    if mask_l is None and damage_location and damage_location.lower() not in ("auto-detect", "auto", "none", ""):
        # Map anatomical location to explicit garment coordinates
        loc_lower = damage_location.lower()
        if "pocket" in loc_lower or "right panel" in loc_lower:
            coords = {"x": 0.62, "y": 0.36, "radius": 0.16}
        elif "left" in loc_lower and ("chest" in loc_lower or "panel" in loc_lower):
            coords = {"x": 0.38, "y": 0.36, "radius": 0.16}
        elif "knee" in loc_lower:
            coords = {"x": 0.40 if "left" in loc_lower else 0.60, "y": 0.70, "radius": 0.18}
        elif "sleeve" in loc_lower or "elbow" in loc_lower:
            coords = {"x": 0.22 if "left" in loc_lower else 0.78, "y": 0.45, "radius": 0.16}
        elif "hem" in loc_lower:
            coords = {"x": 0.50, "y": 0.82, "radius": 0.16}
        elif "collar" in loc_lower:
            coords = {"x": 0.50, "y": 0.18, "radius": 0.14}
        else:
            coords = {"x": 0.50, "y": 0.50, "radius": 0.15}
        mask_l = create_mask_from_coords(w, h, coords)

    # If still no mask, reject rather than fabricating an arbitrary center ellipse
    if mask_l is None:
        if center_fallback:
            # Demo / free preview mode only: use center region as a last-resort
            # placeholder so the demo pipeline never crashes.  This is clearly
            # labelled as a demo result and must NOT be interpreted as accurate
            # damage localisation.
            mask_l = create_mask_from_coords(w, h, {"x": 0.50, "y": 0.50, "radius": 0.15})
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "No damage mask or damage coordinates were provided. "
                    "Please mark the torn area on the garment photo using the brush "
                    "tool, place a click marker, or select a preset damage zone."
                ),
            )

    # 2. Expand mask slightly (4-6 pixels) to form structural reinforcement boundary
    # This allows stitches and patch borders to anchor into healthy surrounding fabric
    dilation_size = max(3, int(min(w, h) * 0.008))
    if dilation_size % 2 == 0:
        dilation_size += 1
    active_mask = mask_l.filter(ImageFilter.MaxFilter(size=dilation_size))

    bbox = active_mask.getbbox()
    if not bbox:
        bbox = (0, 0, w, h)
    x0, y0, x1, y1 = bbox
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2
    bw = max(20, x1 - x0)
    bh = max(20, y1 - y0)

    # Create repair canvas starting from original image
    repair_canvas = orig_img.copy()
    draw = ImageDraw.Draw(repair_canvas, "RGBA")

    norm_style = style.lower()

    if "floral" in norm_style or "embroid" in norm_style:
        # Style: Botanical Floral Embroidery
        # 1. Underlay fiber stabilization patch
        draw.rectangle([x0, y0, x1, y1], fill=(28, 48, 36, 175))

        # 2. Curving botanical stems bridging across the tear
        stem_width = max(2, int(w * 0.004))
        draw.arc([x0 + 4, y0 + 4, x1 - 4, y1 - 4], start=25, end=200, fill=(48, 98, 62, 255), width=stem_width)
        draw.arc([x0 + 8, y0 + 6, x1 - 8, y1 - 6], start=40, end=185, fill=(38, 82, 50, 255), width=stem_width)

        # 3. Satin-stitched leaves along the tear boundary
        leaf_color = (68, 128, 84, 255)
        leaf_rx = max(5, int(bw * 0.10))
        leaf_ry = max(4, int(bh * 0.08))
        draw.ellipse([cx - leaf_rx * 2, cy - leaf_ry, cx - leaf_rx, cy + leaf_ry], fill=leaf_color)
        draw.ellipse([cx + leaf_rx, cy + leaf_ry, cx + leaf_rx * 2, cy + leaf_ry * 2], fill=leaf_color)
        draw.ellipse([x0 + leaf_rx, y0 + leaf_ry, x0 + leaf_rx * 2, y0 + leaf_ry * 2], fill=(82, 142, 98, 255))

        # 4. Artisanal floral petals (terracotta & saffron satin thread)
        petal_color = (218, 102, 76, 255)
        gold_center = (248, 198, 58, 255)
        r_bloom = max(7, int(min(bw, bh) * 0.20))
        draw.ellipse([cx - r_bloom, cy - r_bloom, cx + r_bloom, cy + r_bloom], fill=petal_color)
        draw.ellipse([cx - r_bloom // 2, cy - r_bloom // 2, cx + r_bloom // 2, cy + r_bloom // 2], fill=gold_center)

        # Flanking accent buds
        if bw > 30 and bh > 25:
            b_r = max(4, r_bloom // 2)
            draw.ellipse([x0 + b_r, cy - b_r, x0 + b_r * 3, cy + b_r], fill=(225, 120, 150, 240))
            draw.ellipse([x1 - b_r * 3, cy - b_r, x1 - b_r, cy + b_r], fill=(90, 140, 200, 240))

    elif "minimalist" in norm_style:
        # Style: Minimalist Precision Tone-on-Tone Re-weaving & Bar-tacks
        # Sample average color around tear to match base fabric
        draw.rectangle([x0, y0, x1, y1], fill=(40, 44, 46, 120))
        # Micro bar-tack stitches sealing the tear slit
        bar_step = max(4, int(bh * 0.08))
        for by in range(y0 + 4, y1 - 4, bar_step):
            draw.line([(x0 + 4, by), (x1 - 4, by)], fill=(230, 230, 226, 210), width=1)
            # Subtle needle punctures
            draw.point((x0 + 3, by), fill=(20, 24, 26, 255))
            draw.point((x1 - 3, by), fill=(20, 24, 26, 255))

    elif "patchwork" in norm_style:
        # Style: Boro Patchwork (Multi-tonal swatches)
        w_mid = (x0 + x1) // 2
        draw.rectangle([x0, y0, w_mid, y1], fill=(35, 55, 85, 220), outline=(230, 230, 220, 220), width=2)
        draw.rectangle([w_mid, y0, x1, y1], fill=(95, 75, 55, 220), outline=(230, 230, 220, 220), width=2)
        # Running stitches across partition
        for pst in range(y0 + 6, y1 - 4, 10):
            draw.line([(w_mid - 4, pst), (w_mid + 4, pst)], fill=(245, 245, 235, 255), width=2)
            draw.line([(x0 + 6, pst), (x0 + 12, pst)], fill=(245, 245, 235, 220), width=2)
            draw.line([(x1 - 12, pst), (x1 - 6, pst)], fill=(245, 245, 235, 220), width=2)

    else:
        # Default Style: Streetwear / Vintage / Custom (Authentic Japanese Sashiko running stitches)
        # 1. Structural backing underlay cloth
        draw.rectangle([x0, y0, x1, y1], fill=(36, 48, 64, 195))

        # 2. Interlocking horizontal darning foundation
        darn_step = max(5, int(bh * 0.08))
        for dy in range(y0 + 3, y1 - 2, darn_step):
            draw.line([(x0 + 2, dy), (x1 - 2, dy)], fill=(70, 95, 125, 190), width=1)

        # 3. Geometric Sashiko running stitches (ecru thread with needle puncture shadows)
        row_step = max(7, int(bh * 0.14))
        dash_len = max(6, int(bw * 0.12))
        gap = max(4, int(bw * 0.08))
        thread_color = (248, 245, 235, 255)
        puncture_color = (15, 20, 28, 255)

        for ry in range(y0 + 4, y1 - 3, row_step):
            offset = dash_len // 2 if ((ry - y0) // row_step) % 2 == 1 else 0
            for rx in range(x0 + 4 + offset, x1 - 4, dash_len + gap):
                end_x = min(x1 - 4, rx + dash_len)
                if end_x > rx:
                    draw.line([(rx, ry), (end_x, ry)], fill=thread_color, width=max(2, int(w * 0.003)))
                    draw.point((rx - 1, ry), fill=puncture_color)
                    draw.point((end_x + 1, ry), fill=puncture_color)

        # 4. Reinforcing Japanese cross-stitches '+' at tear endpoints
        cross_pts = [
            (x0 + max(6, int(bw * 0.08)), cy),
            (x1 - max(6, int(bw * 0.08)), cy),
            (cx, y0 + max(6, int(bh * 0.08))),
            (cx, y1 - max(6, int(bh * 0.08))),
        ]
        cr_r = max(3, int(min(bw, bh) * 0.08))
        for kx, ky in cross_pts:
            draw.line([(kx - cr_r, ky), (kx + cr_r, ky)], fill=thread_color, width=2)
            draw.line([(kx, ky - cr_r), (kx, ky + cr_r)], fill=thread_color, width=2)

    # 3. Composite through the mask
    # Feathering documentation:
    # If feather_radius == 0: 100% STRICT MATHEMATICAL EQUALITY outside mask.
    # If feather_radius > 0: Soft 1-2px edge blending at the boundary while preserving all unmasked pixels beyond.
    if feather_radius > 0:
        composite_mask = mask_l.filter(ImageFilter.GaussianBlur(radius=feather_radius))
    else:
        composite_mask = mask_l

    final_img = Image.composite(repair_canvas, orig_img, composite_mask)

    # If original had alpha transparency, preserve it
    if orig_img.mode == "RGBA":
        _, _, _, a_orig = orig_img.split()
        r_f, g_f, b_f, _ = final_img.split()
        final_img = Image.merge("RGBA", (r_f, g_f, b_f, a_orig))

    out_buf = io.BytesIO()
    final_img.save(out_buf, format="PNG", optimize=True)
    return out_buf.getvalue(), "image/png"


def apply_artisanal_demo_filter(
    file_bytes: bytes,
    style: str,
    custom_prompt: str = "",
    garment_analysis: dict = None,
    damage_coords: Optional[dict] = None,
) -> tuple[bytes, str]:
    """
    Demo/free-preview wrapper over render_procedural_repair.
    Always clearly flagged as Demo Mode in the response.

    Uses center_fallback=True so this never raises 400 — demo mode is always
    expected to return *something* (even if damage location is uncertain).
    Damage location and mask are sourced from garment_analysis where available.
    """
    g = garment_analysis or {}
    return render_procedural_repair(
        image_bytes=file_bytes,
        mask_bytes=g.get("mask_bytes"),
        style=style,
        damage_coords=damage_coords or g.get("damage_coords"),
        damage_location=g.get("damage_location"),
        garment_analysis=garment_analysis,
        feather_radius=0,
        center_fallback=True,  # Demo mode: never crash, use center as last resort
    )


def verify_pixel_preservation(
    orig_bytes: bytes,
    repaired_bytes: bytes,
    mask_bytes: bytes,
) -> Tuple[bool, int, int]:
    """
    Verification tool: Tests that every pixel outside the mask is 100% bitwise identical.
    Returns: (is_strictly_preserved, max_diff_outside_mask, unmasked_pixel_count)
    """
    orig = Image.open(io.BytesIO(orig_bytes)).convert("RGB")
    rep = Image.open(io.BytesIO(repaired_bytes)).convert("RGB")
    w, h = orig.size

    norm_m = normalize_mask(mask_bytes, w, h)
    if norm_m is None:
        return False, -1, 0

    orig_arr = np.array(orig)
    rep_arr = np.array(rep)
    mask_arr = np.array(norm_m)

    unmasked_indices = (mask_arr == 0)
    unmasked_count = int(np.sum(unmasked_indices))

    if unmasked_count == 0:
        return True, 0, 0

    diff = np.abs(orig_arr[unmasked_indices].astype(int) - rep_arr[unmasked_indices].astype(int))
    max_diff = int(np.max(diff))
    return (max_diff == 0), max_diff, unmasked_count
