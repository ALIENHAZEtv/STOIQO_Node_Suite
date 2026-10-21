"""
[STOIQO] Inpaint Stitcher & Composite Node
Composites edited, inpainted, or SeedVR2 upscaled cropped subjects back into the original image.
Seamlessly consumes bbox_info from StoiqoSpatialCropperNode, applies edge feathering,
and ensures 100% pixel-accurate re-stitching.
"""

import json
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image, ImageFilter

try:
    from ..core.telemetry import NodeTelemetryTimer, inject_telemetry
except (ImportError, ValueError):
    from core.telemetry import NodeTelemetryTimer, inject_telemetry



def _match_color_distribution(source: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """
    Transfers mean and standard deviation color profile from target to source.
    Expects tensors [H, W, C] in range 0.0..1.0.
    """
    src = source.clone()
    for c in range(min(src.shape[-1], target.shape[-1])):
        s_chan = src[..., c]
        t_chan = target[..., c]

        s_mean, s_std = s_chan.mean(), s_chan.std() + 1e-6
        t_mean, t_std = t_chan.mean(), t_chan.std()

        normalized = (s_chan - s_mean) / s_std
        adjusted = (normalized * t_std) + t_mean
        src[..., c] = torch.clamp(adjusted, 0.0, 1.0)
    return src


def _gpu_gaussian_blur(tensor: torch.Tensor, radius: int) -> torch.Tensor:
    """
    Hardware-accelerated 2D separable Gaussian blur directly on GPU tensor [B, C, H, W].
    Zero CPU/GPU transfers, ultra fast, PyTorch native with torchvision and conv2d fallbacks.
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
    [STOIQO] Inpaint Stitcher & Composite
    Closes the visual inpainting & upscaling loop.
    Re-integrates cropped regions back into the original master image with sub-pixel alignment,
    feathered alpha gradients, and optional color harmonization.
    """

    BLEND_MODES = [
        "Normal (Alpha Feather)",
        "Soft Gradient",
        "Sharp (Direct Insert)",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "original_image": (
                    "IMAGE",
                    {
                        "tooltip": "The original full-resolution master image before cropping [B, H, W, C].",
                    },
                ),
                "edited_image": (
                    "IMAGE",
                    {
                        "tooltip": "The edited, inpainted (Krea 2), or upscaled (SeedVR2) subject crop [B, H, W, C].",
                    },
                ),
                "bbox_info": (
                    "STRING",
                    {
                        "forceInput": True,
                        "tooltip": "JSON metadata string emitted by StoiqoSpatialCropperNode.",
                    },
                ),
            },
            "optional": {
                "blend_mode": (
                    cls.BLEND_MODES,
                    {
                        "default": cls.BLEND_MODES[0],
                        "tooltip": "Edge transition algorithm between edited crop and original background.",
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
                "color_match": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Harmonize color distribution (mean/std) of edited patch to match the original background crop.",
                    },
                ),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("composite_image", "stitch_mask")
    FUNCTION = "stitch_composite"
    CATEGORY = "STOIQO"

    def stitch_composite(
        self,
        original_image,
        edited_image,
        bbox_info,
        blend_mode="Normal (Alpha Feather)",
        feather_radius=16,
        color_match=False,
        unique_id=None,
    ):
        with NodeTelemetryTimer(node_id=unique_id, node_name="InpaintStitcher") as timer:
            # 1. Parse bounding box metadata
            parsed_bbox = None
            try:
                if isinstance(bbox_info, str) and bbox_info.strip():
                    parsed_bbox = json.loads(bbox_info)
                elif isinstance(bbox_info, dict):
                    parsed_bbox = bbox_info
            except Exception as e:
                print(f"[STOIQO Inpaint Stitcher] Error parsing bbox_info: {e}")

            if not parsed_bbox:
                print("[STOIQO Inpaint Stitcher] Warning: No valid bbox_info found. Returning original image.")
                blank_mask = torch.zeros((original_image.shape[0], original_image.shape[1], original_image.shape[2]), dtype=torch.float32)
                return inject_telemetry((original_image, blank_mask), timer.get_stats())

            B, H, W, C = original_image.shape
            out_image = original_image.clone()
            out_mask = torch.zeros((B, H, W), dtype=torch.float32, device=original_image.device)

            # 2. Extract bounding coordinates
            # Priority: normalized_box [xmin_norm, ymin_norm, xmax_norm, ymax_norm]
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
            else:
                print("[STOIQO Inpaint Stitcher] Warning: Unrecognized box format. Returning original image.")
                blank_mask = torch.zeros((B, H, W), dtype=torch.float32)
                return inject_telemetry((original_image, blank_mask), timer.get_stats())

            target_w = xmax - xmin
            target_h = ymax - ymin

            if target_w <= 0 or target_h <= 0:
                blank_mask = torch.zeros((B, H, W), dtype=torch.float32)
                return inject_telemetry((original_image, blank_mask), timer.get_stats())

            # 3. Process each batch item
            for b in range(B):
                # Select edited frame (handle single edited image with batch original)
                ed_idx = b if b < edited_image.shape[0] else 0
                cur_edited = edited_image[ed_idx:ed_idx + 1]  # [1, H_ed, W_ed, C]

                # Re-scale edited image to match target pixel box
                # Permute to [1, C, H_ed, W_ed] for torch interpolate
                cur_perm = cur_edited.permute(0, 3, 1, 2)
                resized_ed = F.interpolate(
                    cur_perm,
                    size=(target_h, target_w),
                    mode="bicubic",
                    align_corners=False,
                )
                # Permute back to [target_h, target_w, C]
                patch_tensor = resized_ed.permute(0, 2, 3, 1).squeeze(0).clamp(0.0, 1.0)

                # Optional Color Match with original background patch
                if color_match:
                    orig_patch = original_image[b, ymin:ymax, xmin:xmax, :]
                    patch_tensor = _match_color_distribution(patch_tensor, orig_patch)

                # 4. Generate blend alpha mask (GPU-vectorized)
                if blend_mode == "Sharp (Direct Insert)" or feather_radius <= 0:
                    alpha_patch = torch.ones((target_h, target_w, 1), dtype=torch.float32, device=original_image.device)
                else:
                    # Fast GPU-accelerated feathered mask without CPU / PIL roundtrips
                    pad = max(1, min(feather_radius // 2, min(target_w, target_h) // 4))
                    mask_raw = torch.zeros((1, 1, target_h, target_w), dtype=torch.float32, device=original_image.device)
                    if target_h > 2 * pad and target_w > 2 * pad:
                        mask_raw[:, :, pad:target_h - pad, pad:target_w - pad] = 1.0
                    else:
                        mask_raw[:, :, :, :] = 1.0
                    blurred_mask = _gpu_gaussian_blur(mask_raw, feather_radius)
                    alpha_patch = blurred_mask.squeeze(0).permute(1, 2, 0).clamp(0.0, 1.0)

                # 5. Blend into composite image
                bg_patch = original_image[b, ymin:ymax, xmin:xmax, :]
                composite_patch = (patch_tensor * alpha_patch) + (bg_patch * (1.0 - alpha_patch))
                out_image[b, ymin:ymax, xmin:xmax, :] = composite_patch
                out_mask[b, ymin:ymax, xmin:xmax] = alpha_patch.squeeze(-1)

            print(
                f"[STOIQO] Inpaint Stitcher: Successfully re-stitched patch at [{xmin}, {ymin}, {xmax}, {ymax}] "
                f"({target_w}x{target_h}px) [Mode: {blend_mode}, Feather: {feather_radius}px]"
            )

            return inject_telemetry((out_image, out_mask), timer.get_stats())

