"""
[STOIQO] Inpaint Stitcher & Spatial Re-Roll Node
Composites edited, inpainted, or upscaled cropped subjects back into the original image,
or isolates a region of interest (ROI) via BBox JSON, manual coordinates, or MASK for selective re-rolling.
Applies GPU-accelerated edge feathering, aspect-ratio protected fitting, and color profile harmonization.
"""

import json
import re
import torch
import torch.nn.functional as F

try:
    from ..core.telemetry import NodeTelemetryTimer, inject_telemetry
except (ImportError, ValueError):
    from core.telemetry import NodeTelemetryTimer, inject_telemetry


def _match_color_distribution(source: torch.Tensor, target: torch.Tensor, strength: float = 0.8) -> torch.Tensor:
    """
    Transfers mean and standard deviation color profile from target to source.
    Expects tensors [H, W, C] in range 0.0..1.0.
    """
    if strength <= 0.0:
        return source
    src = source.clone()
    for c in range(min(src.shape[-1], target.shape[-1])):
        s_chan = src[..., c]
        t_chan = target[..., c]

        s_mean, s_std = s_chan.mean(), s_chan.std() + 1e-6
        t_mean, t_std = t_chan.mean(), t_chan.std()

        normalized = (s_chan - s_mean) / s_std
        adjusted = (normalized * t_std) + t_mean
        adjusted_clamped = torch.clamp(adjusted, 0.0, 1.0)
        src[..., c] = (1.0 - strength) * s_chan + strength * adjusted_clamped
    return src


def _apply_beauty_polish(
    patch: torch.Tensor,
    skin_smoothing: float = 0.0,
    detail_clarity: float = 0.0,
) -> torch.Tensor:
    """
    Fast GPU-vectorized skin smoothing & detail sharpening (preserves pores and hair).
    patch shape [H, W, C] in range 0.0..1.0.
    """
    if skin_smoothing <= 0.0 and detail_clarity <= 0.0:
        return patch

    p_4d = patch.unsqueeze(0).permute(0, 3, 1, 2)  # [1, C, H, W]
    c = p_4d.shape[1]

    # Separable Gaussian blur for low-frequency skin tones
    k_size = 7
    sigma = 1.8
    x = torch.arange(-k_size // 2 + 1, k_size // 2 + 1, dtype=torch.float32, device=patch.device)
    k1d = torch.exp(-0.5 * (x / sigma) ** 2)
    k1d = k1d / k1d.sum()
    kh = k1d.view(1, 1, 1, -1).repeat(c, 1, 1, 1)
    kv = k1d.view(1, 1, -1, 1).repeat(c, 1, 1, 1)
    pad = k_size // 2

    smoothed = F.conv2d(F.conv2d(p_4d, kh, padding=(0, pad), groups=c), kv, padding=(pad, 0), groups=c)

    # High-pass micro-detail mask
    diff = torch.abs(p_4d - smoothed)
    detail_mask = torch.clamp(diff.mean(dim=1, keepdim=True) * 4.0, 0.0, 1.0)

    # Smooth skin while protecting edge details
    smooth_amt = min(1.0, max(0.0, skin_smoothing))
    clarity_amt = max(0.0, detail_clarity)
    clarity_mult = 1.0 + clarity_amt

    smooth_blend = p_4d * (1.0 - smooth_amt) + smoothed * smooth_amt
    restored = smooth_blend * (1.0 - detail_mask) + (p_4d * clarity_mult) * detail_mask

    return torch.clamp(restored.squeeze(0).permute(1, 2, 0), 0.0, 1.0)


def _gpu_gaussian_blur(tensor: torch.Tensor, radius: int) -> torch.Tensor:
    """
    Hardware-accelerated 2D separable Gaussian blur directly on GPU tensor [B, C, H, W].
    Zero CPU/GPU transfers, PyTorch native with torchvision and conv2d fallbacks.
    """
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


class StoiqoInpaintStitcherNode:
    """
    [STOIQO] Inpaint Stitcher & Spatial Re-Roll
    Unified spatial stitcher and ROI isolator.
    - Isolates any target region (from Spatial Cropper bbox_info, manual coords, or MASK) into `cropped_roi`.
    - When `edited_image` is connected, re-integrates the edited/upscaled patch back into `original_image`
      with sub-pixel alignment, feathered alpha gradients, aspect-ratio protection, and color harmonization.
    """

    BLEND_MODES = [
        "Normal (Alpha Feather)",
        "Soft Gradient",
        "Sharp (Direct Insert)",
    ]

    FIT_MODES = [
        "Center Crop (Preserve Aspect)",
        "Stretch to Fill",
        "Center Fit (Letterbox / Pad)",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "original_image": (
                    "IMAGE",
                    {
                        "tooltip": "The original full-resolution master image [B, H, W, C].",
                    },
                ),
            },
            "optional": {
                "edited_image": (
                    "IMAGE",
                    {
                        "tooltip": "The edited, inpainted, or upscaled subject crop to composite back into original_image.",
                    },
                ),
                "optional_mask": (
                    "MASK",
                    {
                        "tooltip": "Optional mask. Defines organic blending boundaries or infers bounding box if bbox_info is empty.",
                    },
                ),
                "bbox_info": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "JSON metadata string from Spatial Cropper, dictionary, or 'xmin, ymin, xmax, ymax' coordinates.",
                    },
                ),
                "blend_mode": (
                    cls.BLEND_MODES,
                    {
                        "default": cls.BLEND_MODES[0],
                        "tooltip": "Edge transition algorithm between edited crop and original background.",
                    },
                ),
                "fit_mode": (
                    cls.FIT_MODES,
                    {
                        "default": cls.FIT_MODES[0],
                        "tooltip": "How to handle aspect ratio differences between edited_image and target bounding box.",
                    },
                ),
                "feather_radius": (
                    "INT",
                    {
                        "default": 16,
                        "min": 0,
                        "max": 128,
                        "step": 2,
                        "tooltip": "Gaussian feather radius in pixels for seamless edge blending.",
                    },
                ),
                "crop_padding_percent": (
                    "FLOAT",
                    {
                        "default": 0.0,
                        "min": 0.0,
                        "max": 0.50,
                        "step": 0.05,
                        "tooltip": "Extra padding margin expanded around mask bounds when inferring BBox from optional_mask.",
                    },
                ),
                "color_match": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Harmonize color distribution (mean/std) of edited patch to match the original background crop.",
                    },
                ),
                "color_match_strength": (
                    "FLOAT",
                    {
                        "default": 0.8,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.05,
                        "tooltip": "Strength of color profile harmonization (0.0 = original crop colors, 1.0 = fully harmonized).",
                    },
                ),
                "skin_smoothing": (
                    "FLOAT",
                    {
                        "default": 0.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.05,
                        "tooltip": "Zero-model pore-preserving bilateral skin softening on the target patch.",
                    },
                ),
                "detail_clarity": (
                    "FLOAT",
                    {
                        "default": 0.0,
                        "min": 0.0,
                        "max": 2.0,
                        "step": 0.05,
                        "tooltip": "High-pass micro-detail clarity boost on eyes, lashes, and focal contours.",
                    },
                ),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "IMAGE", "STRING")
    RETURN_NAMES = ("composite_image", "stitch_mask", "cropped_roi", "bbox_info")
    FUNCTION = "stitch_composite"
    CATEGORY = "STOIQO"

    def stitch_composite(
        self,
        original_image=None,
        edited_image=None,
        optional_mask=None,
        bbox_info="",
        blend_mode="Normal (Alpha Feather)",
        fit_mode="Center Crop (Preserve Aspect)",
        feather_radius=16,
        crop_padding_percent=0.0,
        color_match=False,
        color_match_strength=0.8,
        skin_smoothing=0.0,
        detail_clarity=0.0,
        unique_id=None,
        **kwargs,
    ):
        # Backward-compatibility aliases from SpatialReroll & FaceRestore
        if original_image is None:
            original_image = kwargs.get("image")
        if edited_image is None:
            edited_image = kwargs.get("replacement_image") or kwargs.get("restored_crop")
        if optional_mask is None:
            optional_mask = kwargs.get("mask")
        if not bbox_info and kwargs.get("bbox_json"):
            bbox_info = kwargs.get("bbox_json")
        if "color_harmonization" in kwargs and not color_match:
            color_match = bool(kwargs.get("color_harmonization"))
        if "eye_clarity" in kwargs and detail_clarity <= 0.0:
            detail_clarity = float(kwargs.get("eye_clarity", 0.0)) - 1.0
            detail_clarity = max(0.0, detail_clarity)

        with NodeTelemetryTimer(node_id=unique_id, node_name="InpaintStitcher") as timer:
            B, H, W, C = original_image.shape
            device = original_image.device
            out_image = original_image.clone()
            out_mask = torch.zeros((B, H, W), dtype=torch.float32, device=device)

            # Normalize optional_mask dimensions if provided
            norm_mask = None
            if optional_mask is not None:
                if optional_mask.ndim == 2:
                    norm_mask = optional_mask.unsqueeze(0).to(device=device, dtype=torch.float32)
                elif optional_mask.ndim == 4:
                    norm_mask = optional_mask.squeeze(1).to(device=device, dtype=torch.float32)
                else:
                    norm_mask = optional_mask.to(device=device, dtype=torch.float32)

            # 1. Parse bounding box metadata or infer from optional_mask
            parsed_bbox = None
            if bbox_info is not None:
                if isinstance(bbox_info, dict):
                    parsed_bbox = bbox_info
                elif isinstance(bbox_info, str) and bbox_info.strip():
                    clean_str = bbox_info.strip()
                    try:
                        parsed_bbox = json.loads(clean_str)
                    except Exception:
                        parts = [float(p.strip()) for p in re.split(r"[,;\s]+", clean_str) if p.strip()]
                        if len(parts) == 4:
                            if all(0.0 <= p <= 1.0 for p in parts):
                                parsed_bbox = {"normalized_box": parts}
                            else:
                                parsed_bbox = {"crop_box": parts}

            # If no bbox_info provided, infer bounding box from norm_mask non-zero region
            if not parsed_bbox and norm_mask is not None:
                m_slice = norm_mask[0]
                non_zero = torch.nonzero(m_slice > 0.01)
                if non_zero.numel() > 0:
                    min_y = int(non_zero[:, 0].min().item())
                    max_y = int(non_zero[:, 0].max().item())
                    min_x = int(non_zero[:, 1].min().item())
                    max_x = int(non_zero[:, 1].max().item())

                    pad_w = int((max_x - min_x) * float(crop_padding_percent))
                    pad_h = int((max_y - min_y) * float(crop_padding_percent))

                    ymin = max(0, min_y - pad_h)
                    ymax = min(H, max_y + pad_h + 1)
                    xmin = max(0, min_x - pad_w)
                    xmax = min(W, max_x + pad_w + 1)
                    parsed_bbox = {"crop_box": [xmin, ymin, xmax, ymax]}

            if not parsed_bbox:
                xmin, ymin, xmax, ymax = 0, 0, W, H
            else:
                norm_box = parsed_bbox.get("normalized_box")
                crop_box = parsed_bbox.get("crop_box")

                if norm_box and len(norm_box) == 4:
                    xmin_norm, ymin_norm, xmax_norm, ymax_norm = norm_box
                    xmin = max(0, min(W - 1, int(round(xmin_norm * W))))
                    xmax = max(xmin + 1, min(W, int(round(xmax_norm * W))))
                    ymin = max(0, min(H - 1, int(round(ymin_norm * H))))
                    ymax = max(ymin + 1, min(H, int(round(ymax_norm * H))))
                elif crop_box and len(crop_box) == 4:
                    xmin, ymin, xmax, ymax = [int(v) for v in crop_box]
                    xmin = max(0, min(W - 1, xmin))
                    xmax = max(xmin + 1, min(W, xmax))
                    ymin = max(0, min(H - 1, ymin))
                    ymax = max(ymin + 1, min(H, ymax))
                elif "x" in parsed_bbox and "y" in parsed_bbox:
                    bx = int(parsed_bbox.get("x", 0))
                    by = int(parsed_bbox.get("y", 0))
                    bw = int(parsed_bbox.get("width", parsed_bbox.get("w", W)))
                    bh = int(parsed_bbox.get("height", parsed_bbox.get("h", H)))
                    xmin = max(0, min(W - 1, bx))
                    ymin = max(0, min(H - 1, by))
                    xmax = max(xmin + 1, min(W, xmin + bw))
                    ymax = max(ymin + 1, min(H, ymin + bh))
                else:
                    xmin, ymin, xmax, ymax = 0, 0, W, H

            target_w = xmax - xmin
            target_h = ymax - ymin

            if target_w <= 0 or target_h <= 0:
                blank_mask = torch.zeros((B, H, W), dtype=torch.float32, device=device)
                return inject_telemetry((original_image, blank_mask, original_image, "{}"), timer.get_stats())

            # Extract cropped ROI from original image
            cropped_roi = original_image[:, ymin:ymax, xmin:xmax, :].clone()

            bbox_out_dict = {
                "x": int(xmin),
                "y": int(ymin),
                "width": int(target_w),
                "height": int(target_h),
                "original_width": int(W),
                "original_height": int(H),
                "crop_box": [int(xmin), int(ymin), int(xmax), int(ymax)],
                "normalized_box": [
                    round(xmin / max(1, W), 6),
                    round(ymin / max(1, H), 6),
                    round(xmax / max(1, W), 6),
                    round(ymax / max(1, H), 6),
                ],
            }
            bbox_out_json = json.dumps(bbox_out_dict, indent=2)

            # If no edited_image is connected: check if Beauty Polish is requested directly on the ROI
            if edited_image is None:
                if skin_smoothing > 0.0 or detail_clarity > 0.0:
                    for b in range(B):
                        roi_b = cropped_roi[b].clone()
                        polished_roi = _apply_beauty_polish(roi_b, skin_smoothing=skin_smoothing, detail_clarity=detail_clarity)
                        cropped_roi[b] = polished_roi
                        out_image[b, ymin:ymax, xmin:xmax, :] = polished_roi

                if norm_mask is not None:
                    out_mask[:, ymin:ymax, xmin:xmax] = norm_mask[:, ymin:ymax, xmin:xmax]
                else:
                    out_mask[:, ymin:ymax, xmin:xmax] = 1.0
                return inject_telemetry((out_image, out_mask, cropped_roi, bbox_out_json), timer.get_stats())

            # 3. Process each batch item for compositing edited_image
            for b in range(B):
                ed_idx = b if b < edited_image.shape[0] else 0
                cur_edited = edited_image[ed_idx:ed_idx + 1].to(device=device, dtype=original_image.dtype)
                H_ed, W_ed = cur_edited.shape[1], cur_edited.shape[2]
                cur_perm = cur_edited.permute(0, 3, 1, 2)  # [1, C, H_ed, W_ed]

                # Handle Aspect Ratio & Rescaling
                if fit_mode == "Stretch to Fill" or (H_ed == target_h and W_ed == target_w):
                    resized_ed = F.interpolate(
                        cur_perm,
                        size=(target_h, target_w),
                        mode="bicubic",
                        align_corners=False,
                    )
                    patch_tensor = resized_ed.permute(0, 2, 3, 1).squeeze(0).clamp(0.0, 1.0)
                elif fit_mode == "Center Fit (Letterbox / Pad)":
                    scale = min(target_w / W_ed, target_h / H_ed)
                    scaled_w = max(1, int(round(W_ed * scale)))
                    scaled_h = max(1, int(round(H_ed * scale)))
                    scaled = F.interpolate(cur_perm, size=(scaled_h, scaled_w), mode="bicubic", align_corners=False)
                    scaled_t = scaled.permute(0, 2, 3, 1).squeeze(0).clamp(0.0, 1.0)

                    pad_top = max(0, (target_h - scaled_h) // 2)
                    pad_left = max(0, (target_w - scaled_w) // 2)
                    patch_tensor = original_image[b, ymin:ymax, xmin:xmax, :].clone()
                    h_end = min(target_h, pad_top + scaled_h)
                    w_end = min(target_w, pad_left + scaled_w)
                    patch_tensor[pad_top:h_end, pad_left:w_end, :] = scaled_t[:h_end - pad_top, :w_end - pad_left, :]
                else:
                    # Default: "Center Crop (Preserve Aspect)"
                    scale = max(target_w / W_ed, target_h / H_ed)
                    scaled_w = max(1, int(round(W_ed * scale)))
                    scaled_h = max(1, int(round(H_ed * scale)))
                    scaled = F.interpolate(cur_perm, size=(scaled_h, scaled_w), mode="bicubic", align_corners=False)
                    scaled_t = scaled.permute(0, 2, 3, 1).squeeze(0).clamp(0.0, 1.0)

                    crop_top = max(0, (scaled_h - target_h) // 2)
                    crop_left = max(0, (scaled_w - target_w) // 2)
                    patch_tensor = scaled_t[crop_top:crop_top + target_h, crop_left:crop_left + target_w, :]

                # Optional Color Match with original background patch
                if color_match:
                    orig_patch = original_image[b, ymin:ymax, xmin:xmax, :]
                    patch_tensor = _match_color_distribution(patch_tensor, orig_patch, strength=color_match_strength)

                # Optional Beauty Polish on the composited patch
                if skin_smoothing > 0.0 or detail_clarity > 0.0:
                    patch_tensor = _apply_beauty_polish(patch_tensor, skin_smoothing=skin_smoothing, detail_clarity=detail_clarity)

                # 4. Generate blend alpha mask (GPU-vectorized)
                if blend_mode == "Sharp (Direct Insert)" or feather_radius <= 0:
                    alpha_patch = torch.ones((target_h, target_w, 1), dtype=torch.float32, device=device)
                else:
                    pad = max(1, min(feather_radius // 2, min(target_w, target_h) // 4))
                    mask_raw = torch.zeros((1, 1, target_h, target_w), dtype=torch.float32, device=device)
                    if target_h > 2 * pad and target_w > 2 * pad:
                        mask_raw[:, :, pad:target_h - pad, pad:target_w - pad] = 1.0
                    else:
                        mask_raw[:, :, :, :] = 1.0

                    if "Soft Gradient" in blend_mode:
                        eff_radius = int(feather_radius * 1.5)
                        blurred_mask = _gpu_gaussian_blur(mask_raw, eff_radius)
                        alpha_patch = (0.5 * (1.0 - torch.cos(blurred_mask * 3.1415926535))).squeeze(0).permute(1, 2, 0).clamp(0.0, 1.0)
                    else:
                        blurred_mask = _gpu_gaussian_blur(mask_raw, feather_radius)
                        alpha_patch = blurred_mask.squeeze(0).permute(1, 2, 0).clamp(0.0, 1.0)

                # If an organic segmentation mask is provided, modulate alpha_patch by it
                if norm_mask is not None:
                    m_slice = norm_mask[b] if b < norm_mask.shape[0] else norm_mask[0]
                    mask_crop = m_slice[ymin:ymax, xmin:xmax].unsqueeze(-1)
                    if feather_radius > 0 and blend_mode != "Sharp (Direct Insert)":
                        mask_crop_4d = mask_crop.permute(2, 0, 1).unsqueeze(0)
                        mask_crop = _gpu_gaussian_blur(mask_crop_4d, feather_radius).squeeze(0).permute(1, 2, 0).clamp(0.0, 1.0)
                    alpha_patch = alpha_patch * mask_crop

                # 5. Blend into composite image
                bg_patch = original_image[b, ymin:ymax, xmin:xmax, :]
                composite_patch = (patch_tensor * alpha_patch) + (bg_patch * (1.0 - alpha_patch))
                out_image[b, ymin:ymax, xmin:xmax, :] = composite_patch
                out_mask[b, ymin:ymax, xmin:xmax] = alpha_patch.squeeze(-1)

            return inject_telemetry((out_image, out_mask, cropped_roi, bbox_out_json), timer.get_stats())
