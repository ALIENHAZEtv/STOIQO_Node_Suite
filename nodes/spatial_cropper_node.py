"""
[STOIQO] Spatial Cropper & Mask Generator Node
Uses Vision-Language visual grounding to detect objects/subjects by prompt or manual coordinates,
producing a high-precision cropped IMAGE, a binary MASK, JSON bounding box metadata,
and Impact-Pack compatible SEGS data structure with Low-VRAM management.
"""

import json
import re
import logging
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def _gpu_gaussian_blur(tensor: torch.Tensor, radius: int) -> torch.Tensor:
    """Hardware-accelerated 2D separable Gaussian blur directly on tensor [B, C, H, W]."""
    if radius <= 0:
        return tensor
    try:
        from torchvision.transforms.functional import gaussian_blur
        k_size = int(radius) * 2 + 1
        sigma = max(0.1, float(radius) / 2.0)
        return gaussian_blur(tensor, kernel_size=[k_size, k_size], sigma=[sigma, sigma])
    except Exception:
        sigma = max(0.1, float(radius) / 2.0)
        k_size = int(radius) * 2 + 1
        x = torch.arange(-k_size // 2 + 1, k_size // 2 + 1, dtype=torch.float32, device=tensor.device)
        kernel_1d = torch.exp(-0.5 * (x / sigma) ** 2)
        kernel_1d = kernel_1d / kernel_1d.sum()

        k_h = kernel_1d.view(1, 1, 1, -1).repeat(tensor.shape[1], 1, 1, 1)
        k_v = kernel_1d.view(1, 1, -1, 1).repeat(tensor.shape[1], 1, 1, 1)

        pad_size = k_size // 2
        blurred = F.conv2d(tensor, k_h, padding=(0, pad_size), groups=tensor.shape[1])
        blurred = F.conv2d(blurred, k_v, padding=(pad_size, 0), groups=tensor.shape[1])
        return blurred


def _detect_faces_fast(image: torch.Tensor, padding_percent: float = 0.25) -> list:
    """
    Fast zero-model CPU/GPU face localization fallback via OpenCV Haar Cascade.
    Falls back to golden-ratio upper-third framing if no face is recognized.
    Returns list of (x1, y1, x2, y2) pixel bounding boxes.
    """
    b, h, w, c = image.shape
    detected = []
    try:
        import cv2
        t = image[0].detach().cpu()
        uint8_img = (torch.clamp(t, 0.0, 1.0) * 255.0).numpy().astype(np.uint8)
        gray = cv2.cvtColor(uint8_img, cv2.COLOR_RGB2GRAY)
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        cascade = cv2.CascadeClassifier(cascade_path)
        if not cascade.empty():
            faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(28, 28))
            for (x, y, fw, fh) in faces:
                pad_x = int(fw * (padding_percent / 100.0 if padding_percent > 1 else padding_percent))
                pad_y = int(fh * (padding_percent / 100.0 if padding_percent > 1 else padding_percent))
                x1 = max(0, x - pad_x)
                y1 = max(0, y - pad_y)
                x2 = min(w, x + fw + pad_x)
                y2 = min(h, y + fh + pad_y)
                if (x2 - x1) > 20 and (y2 - y1) > 20:
                    detected.append((x1, y1, x2, y2))
    except Exception as e:
        logger.debug(f"[STOIQO Spatial Cropper] Fast face detect notice: {e}")

    if not detected:
        cx = w // 2
        cy = int(h * 0.38)
        box_size = int(min(w, h) * 0.50)
        half_s = box_size // 2
        x1 = max(0, cx - half_s)
        y1 = max(0, cy - half_s)
        x2 = min(w, cx + half_s)
        y2 = min(h, cy + half_s)
        detected.append((x1, y1, x2, y2))

    return detected


try:
    from ..core import tensor_to_pil, NodeTelemetryTimer, inject_telemetry
except (ImportError, ValueError):
    from core import tensor_to_pil, NodeTelemetryTimer, inject_telemetry

try:
    import impact.core
    SEGClass = getattr(impact.core, "SEG", None)
except Exception:
    SEGClass = None

if SEGClass is None:
    class SEGClass:
        """Impact-Pack standard Segment structure: cropped_image, cropped_mask, confidence, crop_region, bbox, label."""
        def __init__(self, cropped_image, cropped_mask, confidence, crop_region, bbox, label, control_net_wrapper=None):
            self.cropped_image = cropped_image
            self.cropped_mask = cropped_mask
            self.confidence = float(confidence)
            self.crop_region = crop_region
            self.bbox = bbox
            self.label = str(label)
            self.control_net_wrapper = control_net_wrapper

        def __iter__(self):
            return iter((
                self.cropped_image,
                self.cropped_mask,
                self.confidence,
                self.crop_region,
                self.bbox,
                self.label,
                self.control_net_wrapper,
            ))


def parse_bounding_box(
    raw_text: str,
    fed_width: int = 1000,
    fed_height: int = 1000,
    is_qwen_standard: bool = True,
    is_pixel_coords: bool = False,
):
    """
    Robust extraction of 4 normalized coordinates from model or manual text.
    Supports:
    1. Florence-2 token tags: <loc_100><loc_150><loc_400><loc_450>
    2. Qwen2.5-VL native pixel JSON: {"bbox_2d": [x1, y1, x2, y2]}
    3. Normalized float JSON: {"bbox_2d": [0.1, 0.15, 0.4, 0.45]}
    4. Key-value JSON: {"xmin": 100, "ymin": 150, "xmax": 400, "ymax": 450}
    5. Coordinate bracket lists [x1, y1, x2, y2]
    6. Legacy <box>(ymin, xmin), (ymax, xmax)</box>
    Returns (ymin_norm, xmin_norm, ymax_norm, xmax_norm) scaled to 0.0..1.0,
    or None if no valid bounding box could be parsed.
    """
    if not raw_text or not isinstance(raw_text, str):
        return None

    clean_text = raw_text.strip()
    if "```" in clean_text:
        clean_text = re.sub(r"```(?:json)?", "", clean_text).strip()

    # Pattern 0: Florence-2 format with <loc_DDD> tags (0..1000)
    loc_tags = re.findall(r"<loc_(\d{1,4})>", clean_text)
    if len(loc_tags) >= 4:
        v1, v2, v3, v4 = [int(x) for x in loc_tags[:4]]
        ymin_val, ymax_val = min(v1, v3), max(v1, v3)
        xmin_val, xmax_val = min(v2, v4), max(v2, v4)
        ymin_norm = max(0.0, min(1.0, ymin_val / 1000.0))
        ymax_norm = max(0.0, min(1.0, ymax_val / 1000.0))
        xmin_norm = max(0.0, min(1.0, xmin_val / 1000.0))
        xmax_norm = max(0.0, min(1.0, xmax_val / 1000.0))
        if ymax_norm > ymin_norm and xmax_norm > xmin_norm:
            return ymin_norm, xmin_norm, ymax_norm, xmax_norm

    # Pattern 1: JSON dictionary parsing
    p_dict = re.search(r"\{[^{}]*\}", clean_text)
    if p_dict:
        try:
            d = json.loads(p_dict.group(0))
            if isinstance(d, dict):
                # 1a. List under key
                b_list = d.get("bbox_2d") or d.get("box_2d") or d.get("bbox") or d.get("box")
                if isinstance(b_list, (list, tuple)) and len(b_list) == 4:
                    coords = [float(x) for x in b_list]
                    if max(coords) <= 1.0:
                        x1, y1, x2, y2 = coords
                        xmin_norm, xmax_norm = min(x1, x2), max(x1, x2)
                        ymin_norm, ymax_norm = min(y1, y2), max(y1, y2)
                        if ymax_norm > ymin_norm and xmax_norm > xmin_norm:
                            return ymin_norm, xmin_norm, ymax_norm, xmax_norm
                    else:
                        x1, y1, x2, y2 = coords
                        xmin_px, xmax_px = min(x1, x2), max(x1, x2)
                        ymin_px, ymax_px = min(y1, y2), max(y1, y2)
                        if is_pixel_coords:
                            w_scale = float(fed_width) if fed_width > 0 else 1.0
                            h_scale = float(fed_height) if fed_height > 0 else 1.0
                        else:
                            w_scale = float(fed_width) if fed_width > 0 else 1000.0
                            h_scale = float(fed_height) if fed_height > 0 else 1000.0
                            if max(xmax_px, ymax_px) <= 1000 and max(w_scale, h_scale) > 1200:
                                w_scale = 1000.0
                                h_scale = 1000.0
                        ymin_norm = max(0.0, min(1.0, ymin_px / h_scale))
                        ymax_norm = max(0.0, min(1.0, ymax_px / h_scale))
                        xmin_norm = max(0.0, min(1.0, xmin_px / w_scale))
                        xmax_norm = max(0.0, min(1.0, xmax_px / w_scale))
                        if ymax_norm > ymin_norm and xmax_norm > xmin_norm:
                            return ymin_norm, xmin_norm, ymax_norm, xmax_norm

                # 1b. Named keys: xmin/ymin/xmax/ymax or x1/y1/x2/y2
                named_key_combos = [
                    ("xmin", "ymin", "xmax", "ymax"),
                    ("x1", "y1", "x2", "y2"),
                ]
                for kx1, ky1, kx2, ky2 in named_key_combos:
                    if kx1 in d and ky1 in d and kx2 in d and ky2 in d:
                        x1, y1, x2, y2 = float(d[kx1]), float(d[ky1]), float(d[kx2]), float(d[ky2])
                        xmin_val, xmax_val = min(x1, x2), max(x1, x2)
                        ymin_val, ymax_val = min(y1, y2), max(y1, y2)
                        if max(xmax_val, ymax_val) <= 1.0:
                            return ymin_val, xmin_val, ymax_val, xmax_val
                        if is_pixel_coords:
                            w_scale = float(fed_width) if fed_width > 0 else 1.0
                            h_scale = float(fed_height) if fed_height > 0 else 1.0
                        else:
                            w_scale = float(fed_width) if fed_width > 0 else 1000.0
                            h_scale = float(fed_height) if fed_height > 0 else 1000.0
                        return (
                            max(0.0, min(1.0, ymin_val / h_scale)),
                            max(0.0, min(1.0, xmin_val / w_scale)),
                            max(0.0, min(1.0, ymax_val / h_scale)),
                            max(0.0, min(1.0, xmax_val / w_scale)),
                        )
        except Exception:
            pass

    # Pattern 2: Regex for bbox_2d with floats or ints
    p_json = re.search(
        r"[\"']?b(?:box|ox)_2d[\"']?\s*:\s*\[\s*([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)\s*\]",
        clean_text,
        re.IGNORECASE,
    )
    if p_json:
        x1, y1, x2, y2 = [float(p_json.group(i)) for i in range(1, 5)]
        if max(x1, y1, x2, y2) <= 1.0:
            return min(y1, y2), min(x1, x2), max(y1, y2), max(x1, x2)
        xmin_px = min(x1, x2)
        xmax_px = max(x1, x2)
        ymin_px = min(y1, y2)
        ymax_px = max(y1, y2)

        if is_pixel_coords:
            w_scale = float(fed_width) if fed_width > 0 else 1.0
            h_scale = float(fed_height) if fed_height > 0 else 1.0
        else:
            w_scale = float(fed_width) if fed_width > 0 else 1000.0
            h_scale = float(fed_height) if fed_height > 0 else 1000.0
            if max(xmax_px, ymax_px) <= 1000 and max(w_scale, h_scale) > 1200:
                w_scale = 1000.0
                h_scale = 1000.0

        ymin_norm = max(0.0, min(1.0, ymin_px / h_scale))
        ymax_norm = max(0.0, min(1.0, ymax_px / h_scale))
        xmin_norm = max(0.0, min(1.0, xmin_px / w_scale))
        xmax_norm = max(0.0, min(1.0, xmax_px / w_scale))
        if ymax_norm > ymin_norm and xmax_norm > xmin_norm:
            return ymin_norm, xmin_norm, ymax_norm, xmax_norm

    # Pattern 3: Legacy <box>(y1, x1), (y2, x2)</box>
    p1 = re.search(
        r"(?:<box>|\(|\[)?\s*\(?\s*([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)\s*\)?\s*,\s*\(?\s*([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)\s*\)?\s*(?:</box>|\)|\])?",
        clean_text,
    )
    coords = None
    if p1:
        coords = [float(p1.group(i)) for i in range(1, 5)]

    # Pattern 4: Bare Array [v1, v2, v3, v4]
    if coords is None:
        p2 = re.search(
            r"\[\s*([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)\s*\]",
            clean_text,
        )
        if p2:
            coords = [float(p2.group(i)) for i in range(1, 5)]

    if coords is None or len(coords) != 4:
        return None

    v1, v2, v3, v4 = coords

    # Float coordinates already normalized
    if max(coords) <= 1.0:
        if is_qwen_standard:
            ymin_norm, ymax_norm = min(v1, v3), max(v1, v3)
            xmin_norm, xmax_norm = min(v2, v4), max(v2, v4)
        else:
            xmin_norm, xmax_norm = min(v1, v3), max(v1, v3)
            ymin_norm, ymax_norm = min(v2, v4), max(v2, v4)
        if ymax_norm > ymin_norm and xmax_norm > xmin_norm:
            return ymin_norm, xmin_norm, ymax_norm, xmax_norm

    if is_qwen_standard and not p_json:
        ymin_val = min(v1, v3)
        ymax_val = max(v1, v3)
        xmin_val = min(v2, v4)
        xmax_val = max(v2, v4)
    else:
        xmin_val = min(v1, v3)
        xmax_val = max(v1, v3)
        ymin_val = min(v2, v4)
        ymax_val = max(v2, v4)

    if is_pixel_coords:
        w_scale = float(fed_width) if fed_width > 0 else 1.0
        h_scale = float(fed_height) if fed_height > 0 else 1.0
    else:
        w_scale = float(fed_width) if (fed_width > 0 and max(xmax_val, ymax_val) > 1000) else 1000.0
        h_scale = float(fed_height) if (fed_height > 0 and max(xmax_val, ymax_val) > 1000) else 1000.0

    ymin_norm = max(0.0, min(1.0, ymin_val / h_scale))
    ymax_norm = max(0.0, min(1.0, ymax_val / h_scale))
    xmin_norm = max(0.0, min(1.0, xmin_val / w_scale))
    xmax_norm = max(0.0, min(1.0, xmax_val / w_scale))

    if ymax_norm <= ymin_norm or xmax_norm <= xmin_norm:
        return None

    return ymin_norm, xmin_norm, ymax_norm, xmax_norm


class StoiqoSpatialCropperNode:
    """
    [STOIQO] Spatial Cropper & Mask Generator Node
    Dedicated visual grounding, object detection, and cropping engine.
    Locates subjects by prompt or manual coordinates, outputting:
    1. Cropped IMAGE
    2. Binary MASK (with optional GPU edge feathering)
    3. JSON bbox metadata string
    4. SEGS data structure (100% Impact-Pack compatible)
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": (
                    "IMAGE",
                    {
                        "tooltip": "The input image to inspect, crop, or generate a mask for.",
                    },
                ),
            },
            "optional": {
                "model": (
                    "*",
                    {
                        "tooltip": "Connect [STOIQO] Universal Model Loader or VLM loader node here.",
                    },
                ),
                "detect_prompt": (
                    "STRING",
                    {
                        "default": "main subject",
                        "multiline": False,
                        "placeholder": "e.g. cat, person, face, car, sneakers...",
                        "tooltip": "Object, subject, or detail to locate and detect in the image.",
                    },
                ),
                "manual_bbox": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                        "placeholder": "e.g. [100, 100, 300, 300] or [0.1, 0.1, 0.8, 0.8]",
                        "tooltip": "Optional manual bounding box override (JSON or coordinate list). If provided and valid, skips VLM inference.",
                    },
                ),
                "padding_percent": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 50,
                        "step": 1,
                        "tooltip": "Safety margin percentage added around the detected bounding box.",
                    },
                ),
                "crop_shape": (
                    [
                        "Tight Bounding Box",
                        "1:1 Square (Centered on Subject)",
                    ],
                    {
                        "default": "Tight Bounding Box",
                        "tooltip": "Shape of the cropped output: 'Tight Bounding Box' fits closely; '1:1 Square (Centered)' expands symmetrically around subject center for LoRA/Avatar training.",
                    },
                ),
                "mask_feather": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 64,
                        "step": 1,
                        "tooltip": "Gaussian blur radius (in pixels) applied to mask edges on GPU. Softens boundaries for seamless inpainting.",
                    },
                ),
                "invert_mask": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Invert mask colors (False = white subject on black background).",
                    },
                ),
                "target_megapixel": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.1,
                        "max": 4.0,
                        "step": 0.1,
                        "round": 0.01,
                        "tooltip": "Visual resolution budget for the detection pass (~1.0 Mpx = ~1024x1024).",
                    },
                ),
                "coord_order": (
                    [
                        "ymin, xmin, ymax, xmax (Qwen Standard)",
                        "xmin, ymin, xmax, ymax",
                    ],
                    {
                        "default": "ymin, xmin, ymax, xmax (Qwen Standard)",
                        "tooltip": "Bounding box coordinate interpretation order.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "SEGS")
    RETURN_NAMES = ("cropped_image", "mask", "bbox_info", "segs")
    OUTPUT_IS_LIST = (False, False, False, False)
    FUNCTION = "crop_and_mask"
    OUTPUT_NODE = True
    CATEGORY = "STOIQO"

    def crop_and_mask(
        self,
        image,
        model=None,
        stoiqo_model=None,
        detect_prompt="main subject",
        manual_bbox="",
        padding_percent=0,
        target_megapixel=1.0,
        invert_mask=False,
        crop_shape="Tight Bounding Box",
        mask_feather=0,
        coord_order="ymin, xmin, ymax, xmax (Qwen Standard)",
        **kwargs,
    ):
        if image is None:
            raise ValueError("[STOIQO] Spatial Cropper: No image provided.")

        with NodeTelemetryTimer(node_name="SpatialCropper") as timer:
            B, H, W, C = image.shape
            clean_target = detect_prompt.strip() if detect_prompt else "main subject"
            is_qwen = "Qwen" in coord_order
            parsed = None
            raw_response = ""

            # 1. Check for manual bounding box override first
            if manual_bbox and manual_bbox.strip():
                clean_manual = manual_bbox.strip()
                parsed = parse_bounding_box(clean_manual, fed_width=W, fed_height=H, is_qwen_standard=False, is_pixel_coords=True)
                if parsed is not None:
                    raw_response = f"Manual override: {clean_manual}"
                    print(f"[STOIQO] Spatial Cropper: Using manual bounding box override '{clean_manual}'.")

            # 2. If no manual box, perform VLM Visual Grounding or Fast Face Detect
            active_model = model if model is not None else stoiqo_model
            if parsed is None:
                is_portrait_prompt = any(kw in clean_target.lower() for kw in ["face", "portrait", "head", "person", "eyes", "visage"])
                if active_model is None and is_portrait_prompt:
                    # Fast zero-model OpenCV Face Detection
                    boxes = _detect_faces_fast(image, padding_percent=padding_percent)
                    if boxes:
                        x1, y1, x2, y2 = boxes[0]
                        ymin_norm = max(0.0, min(1.0, y1 / float(H)))
                        xmin_norm = max(0.0, min(1.0, x1 / float(W)))
                        ymax_norm = max(0.0, min(1.0, y2 / float(H)))
                        xmax_norm = max(0.0, min(1.0, x2 / float(W)))
                        parsed = (ymin_norm, xmin_norm, ymax_norm, xmax_norm)
                        raw_response = f"Fast Face Detection: [{x1}, {y1}, {x2}, {y2}]"
                        print(f"[STOIQO] Spatial Cropper: Fast Face Detection used for '{clean_target}'.")

            if parsed is None:
                if active_model is None:
                    raise RuntimeError(
                        "[STOIQO] Spatial Cropper: No model or manual_bbox provided.\n"
                        "Please connect the [STOIQO] Universal Model Loader or supply a manual_bbox."
                    )

                if getattr(active_model, "model", None) is None:
                    if getattr(active_model, "last_load_params", None) is not None:
                        print("[STOIQO] Spatial Cropper: Model was offloaded in Low VRAM mode. Reloading for detection pass...")
                        active_model.load_model(**active_model.last_load_params)
                    else:
                        raise RuntimeError(
                            "[STOIQO] Spatial Cropper: No model loaded and no previous load parameters found.\n"
                            "Please ensure a model is loaded in the connected model loader node."
                        )

                # Convert first batch image for VLM detection
                pil_img, _ = tensor_to_pil(image[0:1], target_megapixel=target_megapixel)
                fed_w, fed_h = pil_img.size

                system_prompt = (
                    "You are an expert computer vision object localization assistant. "
                    "Locate the requested subject with high spatial precision. "
                    'Output ONLY a valid JSON object with the bounding box coordinates in the format: '
                    '{"bbox_2d": [x1, y1, x2, y2], "label": "' + clean_target + '"} '
                    "where [x1, y1] is the top-left corner and [x2, y2] is the bottom-right corner in image pixel coordinates. "
                    "Do not write explanations, comments, or markdown fences."
                )
                task_prompt = f"Locate '{clean_target}' in the image and output its bounding box coordinates in JSON format: {{\"bbox_2d\": [x1, y1, x2, y2], \"label\": \"{clean_target}\"}}."

                print(f"[STOIQO] Spatial Cropper: Detecting '{clean_target}' (resolution: {fed_w}x{fed_h})...")
                try:
                    raw_response = active_model.generate_single(
                        pil_images=pil_img,
                        task_prompt=task_prompt,
                        system_prompt=system_prompt,
                        max_new_tokens=128,
                        temperature=0.1,
                        top_p=0.9,
                        repetition_penalty=1.05,
                        is_multi_image=False,
                    )
                finally:
                    # Low-VRAM offloading: free VRAM if keep_in_vram is False
                    if active_model and not getattr(active_model, "keep_in_vram", True):
                        if hasattr(active_model, "unload_model"):
                            active_model.unload_model()

                # Parse coordinates
                parsed = parse_bounding_box(raw_response, fed_width=fed_w, fed_height=fed_h, is_qwen_standard=is_qwen)

            # 3. Fallback if detection failed completely
            if parsed is None:
                print(f"[STOIQO] Spatial Cropper: Warning — could not parse bounding box from response '{raw_response}'. Returning full image.")
                crop_tensor = image.clone()
                mask_tensor = torch.zeros((B, H, W), dtype=torch.float32, device=image.device)
                if invert_mask:
                    mask_tensor = 1.0 - mask_tensor
                bbox_metadata = {
                    "target": clean_target,
                    "detected": False,
                    "raw_response": raw_response,
                    "x": 0,
                    "y": 0,
                    "width": int(W),
                    "height": int(H),
                }
                segs_empty = ((int(H), int(W)), [])
                ui_payload = {
                    "bbox": [0, 0, int(W), int(H)],
                    "crop_shape": [crop_shape],
                    "text": [f"⚠️ Bbox Fallback: '{clean_target}' (Full image)"],
                }
                return inject_telemetry({
                    "ui": ui_payload,
                    "result": (crop_tensor, mask_tensor, json.dumps(bbox_metadata, indent=2), segs_empty),
                }, timer.get_stats())

            ymin_norm, xmin_norm, ymax_norm, xmax_norm = parsed

            # Convert normalized coordinates to original pixel space
            ymin_px = int(ymin_norm * H)
            ymax_px = int(ymax_norm * H)
            xmin_px = int(xmin_norm * W)
            xmax_px = int(xmax_norm * W)

            # 4. Apply padding margin if requested
            if padding_percent > 0:
                box_w = xmax_px - xmin_px
                box_h = ymax_px - ymin_px
                pad_x = int(box_w * (padding_percent / 100.0))
                pad_y = int(box_h * (padding_percent / 100.0))

                xmin_px = max(0, xmin_px - pad_x)
                xmax_px = min(W, xmax_px + pad_x)
                ymin_px = max(0, ymin_px - pad_y)
                ymax_px = min(H, ymax_px + pad_y)

            # 5. Handle Square (1:1 Centered) crop mode if selected
            if "Square" in crop_shape:
                center_x = (xmin_px + xmax_px) / 2.0
                center_y = (ymin_px + ymax_px) / 2.0
                side = max(xmax_px - xmin_px, ymax_px - ymin_px)
                half = side / 2.0

                sq_x1 = int(round(center_x - half))
                sq_x2 = int(round(center_x + half))
                sq_y1 = int(round(center_y - half))
                sq_y2 = int(round(center_y + half))

                # Shift into image boundaries
                if sq_x1 < 0:
                    sq_x2 = min(W, sq_x2 - sq_x1)
                    sq_x1 = 0
                if sq_x2 > W:
                    sq_x1 = max(0, sq_x1 - (sq_x2 - W))
                    sq_x2 = W
                if sq_y1 < 0:
                    sq_y2 = min(H, sq_y2 - sq_y1)
                    sq_y1 = 0
                if sq_y2 > H:
                    sq_y1 = max(0, sq_y1 - (sq_y2 - H))
                    sq_y2 = H

                xmin_px, xmax_px = sq_x1, sq_x2
                ymin_px, ymax_px = sq_y1, sq_y2

            # Safety clamps: ensure at least 1 pixel width and height
            xmin_px = max(0, min(W - 1, xmin_px))
            xmax_px = max(xmin_px + 1, min(W, xmax_px))
            ymin_px = max(0, min(H - 1, ymin_px))
            ymax_px = max(ymin_px + 1, min(H, ymax_px))

            # 6. Crop tensor and create binary mask
            crop_tensor = image[:, ymin_px:ymax_px, xmin_px:xmax_px, :]

            mask_tensor = torch.zeros((B, H, W), dtype=torch.float32, device=image.device)
            mask_tensor[:, ymin_px:ymax_px, xmin_px:xmax_px] = 1.0

            # Optional mask edge feathering (Hardware-accelerated Gaussian Blur directly on GPU)
            if mask_feather > 0:
                m4d = mask_tensor.unsqueeze(1)  # [B, 1, H, W]
                mask_tensor = _gpu_gaussian_blur(m4d, mask_feather).squeeze(1).clamp(0.0, 1.0)

            if invert_mask:
                mask_tensor = 1.0 - mask_tensor

            crop_w = xmax_px - xmin_px
            crop_h = ymax_px - ymin_px

            print(
                f"[STOIQO] Spatial Cropper: Detected '{clean_target}' at "
                f"[{xmin_px}, {ymin_px}, {xmax_px}, {ymax_px}] ({crop_w}x{crop_h}px) [Shape: {crop_shape}]"
            )

            bbox_metadata = {
                "target": clean_target,
                "detected": True,
                "x": int(xmin_px),
                "y": int(ymin_px),
                "width": int(crop_w),
                "height": int(crop_h),
                "crop_shape": crop_shape,
                "crop_box": [int(xmin_px), int(ymin_px), int(xmax_px), int(ymax_px)],
                "normalized_box": [round(xmin_norm, 4), round(ymin_norm, 4), round(xmax_norm, 4), round(ymax_norm, 4)],
                "raw_response": raw_response,
            }

            # Construct Impact-Pack compatible SEGS output
            cropped_img_np = crop_tensor[0].cpu().numpy()
            cropped_mask_np = mask_tensor[0, ymin_px:ymax_px, xmin_px:xmax_px].cpu().numpy()
            seg_box = (int(xmin_px), int(ymin_px), int(xmax_px), int(ymax_px))

            seg_item = SEGClass(
                cropped_image=cropped_img_np,
                cropped_mask=cropped_mask_np,
                confidence=0.99,
                crop_region=seg_box,
                bbox=seg_box,
                label=str(clean_target),
                control_net_wrapper=None,
            )
            segs_output = ((int(H), int(W)), [seg_item])

            ui_payload = {
                "bbox": [int(xmin_px), int(ymin_px), int(xmax_px), int(ymax_px)],
                "crop_shape": [crop_shape],
                "text": [f"🎯 Grounding: '{clean_target}' at [{xmin_px}, {ymin_px}, {xmax_px}, {ymax_px}] ({crop_w}x{crop_h}px)"],
            }

            return inject_telemetry({
                "ui": ui_payload,
                "result": (crop_tensor, mask_tensor, json.dumps(bbox_metadata, indent=2), segs_output),
            }, timer.get_stats())
