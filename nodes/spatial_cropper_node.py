"""
[STOIQO] Spatial Cropper & Mask Generator Node
Uses Vision-Language visual grounding to detect objects/subjects by prompt,
producing a high-precision cropped IMAGE, a binary MASK, and JSON bounding box metadata.
"""

import json
import re
import torch
import numpy as np
from PIL import Image, ImageFilter

try:
    from ..core import tensor_to_pil, ModelManager
except (ImportError, ValueError):
    from core import tensor_to_pil, ModelManager


def parse_bounding_box(raw_text: str, fed_width: int = 1000, fed_height: int = 1000, is_qwen_standard: bool = True):
    """
    Robust extraction of 4 normalized coordinates from model output.
    Supports Qwen2.5-VL native pixel JSON format: {"bbox_2d": [x1, y1, x2, y2]},
    bracket lists [x1, y1, x2, y2], and legacy <box>(ymin, xmin), (ymax, xmax)</box> normalized to 1000.
    Returns (ymin_norm, xmin_norm, ymax_norm, xmax_norm) scaled to 0.0..1.0,
    or None if no valid bounding box could be parsed.
    """
    if not raw_text or not isinstance(raw_text, str):
        return None

    clean_text = raw_text.strip()
    # Remove markdown code fences if present
    if "```" in clean_text:
        clean_text = re.sub(r"```(?:json)?", "", clean_text).strip()

    # Pattern 1: Native Qwen2.5-VL JSON {"bbox_2d": [x1, y1, x2, y2]} or {"box_2d": [...]}
    p_json = re.search(
        r"[\"']?b(?:box|ox)_2d[\"']?\s*:\s*\[\s*(\d{1,5})\s*,\s*(\d{1,5})\s*,\s*(\d{1,5})\s*,\s*(\d{1,5})\s*\]",
        clean_text,
        re.IGNORECASE,
    )
    if p_json:
        x1, y1, x2, y2 = [int(p_json.group(i)) for i in range(1, 5)]
        xmin_px = min(x1, x2)
        xmax_px = max(x1, x2)
        ymin_px = min(y1, y2)
        ymax_px = max(y1, y2)

        # Scale by fed image dimensions (Qwen2.5-VL outputs coordinates in image pixels)
        w_scale = float(fed_width) if fed_width > 0 else 1000.0
        h_scale = float(fed_height) if fed_height > 0 else 1000.0

        # If model used 0..1000 normalization despite prompt
        if max(xmax_px, ymax_px) <= 1000 and max(w_scale, h_scale) > 1200:
            w_scale = 1000.0
            h_scale = 1000.0

        ymin_norm = max(0.0, min(1.0, ymin_px / h_scale))
        ymax_norm = max(0.0, min(1.0, ymax_px / h_scale))
        xmin_norm = max(0.0, min(1.0, xmin_px / w_scale))
        xmax_norm = max(0.0, min(1.0, xmax_px / w_scale))

        if ymax_norm > ymin_norm and xmax_norm > xmin_norm:
            return ymin_norm, xmin_norm, ymax_norm, xmax_norm

    # Pattern 2: Legacy <box>(y1, x1), (y2, x2)</box> or (y1, x1), (y2, x2)
    p1 = re.search(
        r"(?:<box>|\(|\[)?\s*\(?\s*(\d{1,4})\s*,\s*(\d{1,4})\s*\)?\s*,\s*\(?\s*(\d{1,4})\s*,\s*(\d{1,4})\s*\)?\s*(?:</box>|\)|\])?",
        clean_text,
    )
    coords = None
    if p1:
        coords = [int(p1.group(i)) for i in range(1, 5)]

    # Pattern 3: Array [v1, v2, v3, v4]
    if coords is None:
        p2 = re.search(
            r"\[\s*(\d{1,5})\s*,\s*(\d{1,5})\s*,\s*(\d{1,5})\s*,\s*(\d{1,5})\s*\]",
            clean_text,
        )
        if p2:
            coords = [int(p2.group(i)) for i in range(1, 5)]

    if coords is None or len(coords) != 4:
        return None

    v1, v2, v3, v4 = coords

    # Check whether order is (ymin, xmin, ymax, xmax) or (xmin, ymin, xmax, ymax)
    if is_qwen_standard and not p_json:
        # Legacy Qwen 0..1000: (ymin, xmin, ymax, xmax)
        ymin_val = min(v1, v3)
        ymax_val = max(v1, v3)
        xmin_val = min(v2, v4)
        xmax_val = max(v2, v4)
    else:
        # Cartesian (x1, y1, x2, y2)
        xmin_val = min(v1, v3)
        xmax_val = max(v1, v3)
        ymin_val = min(v2, v4)
        ymax_val = max(v2, v4)

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
    Dedicated Visual Grounding & Cropping node.
    Given an image and an object prompt (e.g. 'cat', 'vintage watch', 'face'),
    locates the subject using the connected VLM and outputs:
    1. Cropped IMAGE
    2. Binary MASK (ComfyUI standard)
    3. JSON bbox metadata string
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "stoiqo_model": (
                    "STOIQO_MODEL",
                    {
                        "tooltip": "Connect the [STOIQO] VLM Model Loader node here.",
                    },
                ),
                "image": (
                    "IMAGE",
                    {
                        "tooltip": "The input image to inspect, crop, or generate a mask for.",
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
                "invert_mask": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Invert mask colors (False = white subject on black background).",
                    },
                ),
            },
            "optional": {
                "crop_shape": (
                    [
                        "Tight Bounding Box",
                        "1:1 Square (Centered on Subject)",
                    ],
                    {
                        "default": "Tight Bounding Box",
                        "tooltip": "Shape of the cropped output: 'Tight Bounding Box' fits the subject closely; '1:1 Square (Centered)' expands symmetrically into a 1:1 aspect ratio around the subject center (ideal for LoRA & Avatar training).",
                    },
                ),
                "mask_feather": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 64,
                        "step": 1,
                        "tooltip": "Gaussian blur radius (in pixels) applied to mask edges. Softens boundaries for seamless inpainting.",
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

    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("cropped_image", "mask", "bbox_info")
    OUTPUT_IS_LIST = (False, False, False)
    FUNCTION = "crop_and_mask"
    CATEGORY = "STOIQO/Vision"

    def crop_and_mask(
        self,
        stoiqo_model,
        image,
        detect_prompt="main subject",
        padding_percent=0,
        target_megapixel=1.0,
        invert_mask=False,
        crop_shape="Tight Bounding Box",
        mask_feather=0,
        coord_order="ymin, xmin, ymax, xmax (Qwen Standard)",
    ):
        if stoiqo_model is None:
            raise RuntimeError(
                "[STOIQO] Spatial Cropper: No VLM model provided.\n"
                "Please connect the [STOIQO] VLM Model Loader node."
            )

        if getattr(stoiqo_model, "model", None) is None:
            if getattr(stoiqo_model, "last_load_params", None) is not None:
                print("[STOIQO] Spatial Cropper: Model was offloaded in Low VRAM mode. Reloading for detection pass...")
                stoiqo_model.load_model(**stoiqo_model.last_load_params)
            else:
                raise RuntimeError(
                    "[STOIQO] Spatial Cropper: No VLM model loaded and no previous load parameters found.\n"
                    "Please ensure a model is loaded in the connected [STOIQO] VLM Model Loader node."
                )

        if image is None:
            raise ValueError("[STOIQO] Spatial Cropper: No image provided.")

        B, H, W, C = image.shape
        clean_target = detect_prompt.strip() if detect_prompt else "main subject"

        if B > 1:
            print(f"[STOIQO] Spatial Cropper: Multi-image batch of {B} frames detected. Bounding box will be detected on reference frame and applied uniformly.")

        # 1. Convert first batch image for VLM detection
        pil_img, _ = tensor_to_pil(image[0:1], target_megapixel=target_megapixel)
        fed_w, fed_h = pil_img.size

        # 2. Formulate precision grounding prompt (native Qwen2.5-VL JSON bbox_2d)
        is_qwen = "Qwen" in coord_order
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
        raw_response = stoiqo_model.generate_single(
            pil_images=pil_img,
            task_prompt=task_prompt,
            system_prompt=system_prompt,
            max_new_tokens=128,
            temperature=0.1,
            top_p=0.9,
            repetition_penalty=1.05,
            is_multi_image=False,
        )

        # 3. Parse coordinates
        parsed = parse_bounding_box(raw_response, fed_width=fed_w, fed_height=fed_h, is_qwen_standard=is_qwen)

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
            return (crop_tensor, mask_tensor, json.dumps(bbox_metadata, indent=2))

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

        # Safety clamps
        xmin_px = max(0, min(W - 1, xmin_px))
        xmax_px = max(xmin_px + 1, min(W, xmax_px))
        ymin_px = max(0, min(H - 1, ymin_px))
        ymax_px = max(ymin_px + 1, min(H, ymax_px))

        # 6. Crop tensor and create binary mask
        crop_tensor = image[:, ymin_px:ymax_px, xmin_px:xmax_px, :]

        mask_tensor = torch.zeros((B, H, W), dtype=torch.float32, device=image.device)
        mask_tensor[:, ymin_px:ymax_px, xmin_px:xmax_px] = 1.0

        # Optional mask edge feathering (Gaussian Blur)
        if mask_feather > 0:
            feathered = []
            for b in range(B):
                m_np = (mask_tensor[b].cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
                m_pil = Image.fromarray(m_np).filter(ImageFilter.GaussianBlur(radius=mask_feather))
                feathered.append(torch.from_numpy(np.array(m_pil).astype(np.float32) / 255.0))
            mask_tensor = torch.stack(feathered, dim=0).to(image.device)

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

        return (crop_tensor, mask_tensor, json.dumps(bbox_metadata, indent=2))
