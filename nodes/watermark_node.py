"""
[STOIQO] Smart Watermark & Logo Stamp Node
High-efficiency node that replaces complex multi-node watermarking pipelines.
Automatically computes aspect ratios, margin offsets, alpha transparency,
and chroma-key background removal for pristine logo overlay.
"""

import json
import torch
import torch.nn.functional as F
import numpy as np


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


class StoiqoWatermarkNode:
    """
    [STOIQO] Smart Watermark & Logo Stamp
    Stamps branding logos or watermarks over image batches with smart scaling,
    corner alignment, automatic chroma/alpha extraction, and feathering.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_image": ("IMAGE", {"tooltip": "Base image or batch of images to watermark."}),
                "watermark_image": ("IMAGE", {"tooltip": "Logo or watermark image."}),
                "position": (
                    [
                        "Bottom-Right",
                        "Bottom-Left",
                        "Top-Right",
                        "Top-Left",
                        "Center",
                        "Top-Center",
                        "Bottom-Center",
                    ],
                    {"default": "Bottom-Right", "tooltip": "Placement anchor on the base image."},
                ),
                "scale_mode": (
                    [
                        "1/8 (Default)",
                        "1/10",
                        "1/6",
                        "1/5",
                        "1/4",
                        "1/3",
                        "1/2",
                        "Custom Ratio",
                        "Custom Width (px)",
                    ],
                    {"default": "1/8 (Default)", "tooltip": "Size of watermark relative to base image width or fixed pixels."},
                ),
                "custom_scale": (
                    "FLOAT",
                    {"default": 0.125, "min": 0.005, "max": 8192.0, "step": 0.005, "tooltip": "Multiplier for Custom Ratio (0.01 - 1.0) or exact pixel width when Custom Width (px) is selected."},
                ),
                "margin_percent": (
                    "FLOAT",
                    {"default": 0.02, "min": 0.0, "max": 0.35, "step": 0.005, "tooltip": "Margin distance from image borders as a fraction of image dimensions (0.02 = 2%)."},
                ),
                "opacity": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.02, "tooltip": "Overall opacity of the watermark overlay (0.0 = invisible, 1.0 = solid)."},
                ),
                "remove_bg_mode": (
                    [
                        "None (Use Alpha/RGB)",
                        "Auto Chroma (Corner)",
                        "Chroma Black",
                        "Chroma White",
                    ],
                    {"default": "Auto Chroma (Corner)", "tooltip": "Automatically remove background color (e.g. black or white logo backgrounds)."},
                ),
                "chroma_tolerance": (
                    "FLOAT",
                    {"default": 0.10, "min": 0.01, "max": 0.60, "step": 0.01, "tooltip": "Color distance threshold for chroma background removal."},
                ),
            },
            "optional": {
                "feather_radius": (
                    "INT",
                    {"default": 1, "min": 0, "max": 32, "step": 1, "tooltip": "Gaussian feathering radius in pixels to soften watermark outer edges."},
                ),
                "optional_mask": (
                    "MASK",
                    {"tooltip": "Optional external alpha mask for the watermark image (overrides internal chroma keying if provided)."},
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("image", "watermark_mask", "overlay_info")
    FUNCTION = "apply_watermark"
    CATEGORY = "STOIQO"

    def apply_watermark(
        self,
        base_image: torch.Tensor,
        watermark_image: torch.Tensor,
        position: str = "Bottom-Right",
        scale_mode: str = "1/8 (Default)",
        custom_scale: float = 0.125,
        margin_percent: float = 0.02,
        opacity: float = 1.0,
        remove_bg_mode: str = "Auto Chroma (Corner)",
        chroma_tolerance: float = 0.10,
        feather_radius: int = 1,
        optional_mask: torch.Tensor = None,
    ):
        B_base, H_base, W_base, C_base = base_image.shape
        B_wm, H_wm, W_wm, C_wm = watermark_image.shape

        # Select target watermark width ratio
        ratio_map = {
            "1/8 (Default)": 1.0 / 8.0,
            "1/10": 1.0 / 10.0,
            "1/6": 1.0 / 6.0,
            "1/5": 1.0 / 5.0,
            "1/4": 1.0 / 4.0,
            "1/3": 1.0 / 3.0,
            "1/2": 1.0 / 2.0,
        }

        if scale_mode in ratio_map:
            target_wm_w = max(16, int(round(W_base * ratio_map[scale_mode])))
        elif scale_mode == "Custom Ratio":
            target_wm_w = max(16, int(round(W_base * max(0.01, min(1.0, custom_scale)))))
        elif scale_mode == "Custom Width (px)":
            target_wm_w = max(16, min(W_base, int(round(custom_scale))))
        else:
            target_wm_w = max(16, int(round(W_base * 0.125)))

        # Preserve aspect ratio of watermark
        wm_aspect = float(H_wm) / float(W_wm)
        target_wm_h = max(16, int(round(target_wm_w * wm_aspect)))

        # Clamp if watermark height exceeds base image
        if target_wm_h > H_base:
            target_wm_h = H_base
            target_wm_w = max(16, int(round(target_wm_h / wm_aspect)))

        # Margins in pixels
        margin_x = int(round(W_base * margin_percent))
        margin_y = int(round(H_base * margin_percent))

        # Calculate top-left (x, y) based on chosen position
        if position == "Bottom-Right":
            pos_x = W_base - target_wm_w - margin_x
            pos_y = H_base - target_wm_h - margin_y
        elif position == "Bottom-Left":
            pos_x = margin_x
            pos_y = H_base - target_wm_h - margin_y
        elif position == "Top-Right":
            pos_x = W_base - target_wm_w - margin_x
            pos_y = margin_y
        elif position == "Top-Left":
            pos_x = margin_x
            pos_y = margin_y
        elif position == "Center":
            pos_x = (W_base - target_wm_w) // 2
            pos_y = (H_base - target_wm_h) // 2
        elif position == "Top-Center":
            pos_x = (W_base - target_wm_w) // 2
            pos_y = margin_y
        elif position == "Bottom-Center":
            pos_x = (W_base - target_wm_w) // 2
            pos_y = H_base - target_wm_h - margin_y
        else:
            pos_x = W_base - target_wm_w - margin_x
            pos_y = H_base - target_wm_h - margin_y

        pos_x = max(0, min(W_base - target_wm_w, pos_x))
        pos_y = max(0, min(H_base - target_wm_h, pos_y))

        # Prepare watermark image resized to (target_wm_h, target_wm_w)
        # Permute [B, H, W, C] -> [B, C, H, W]
        wm_perm = watermark_image[0:1].permute(0, 3, 1, 2)
        wm_resized = F.interpolate(wm_perm, size=(target_wm_h, target_wm_w), mode="bilinear", align_corners=False)
        wm_rgb = wm_resized.permute(0, 2, 3, 1)[0]  # [target_wm_h, target_wm_w, 3]

        # Compute Alpha Mask
        if optional_mask is not None:
            # External mask provided
            mask_t = optional_mask[0:1]
            if len(mask_t.shape) == 3:
                mask_t = mask_t.unsqueeze(1)  # [1, 1, H, W]
            mask_resized = F.interpolate(mask_t, size=(target_wm_h, target_wm_w), mode="bilinear", align_corners=False)
            alpha = mask_resized[0, 0]  # [target_wm_h, target_wm_w]
        elif C_wm >= 4:
            # Native alpha channel embedded in watermark image
            alpha = wm_resized[0, 3]
        elif remove_bg_mode == "Auto Chroma (Corner)":
            # Sample corner pixel (top-left) as background key
            corner_color = wm_rgb[0, 0, :3]
            diff = torch.norm(wm_rgb[:, :, :3] - corner_color, dim=2)
            alpha = torch.where(diff < chroma_tolerance, torch.zeros_like(diff), torch.ones_like(diff))
            # Smooth transition around tolerance boundary
            transition = torch.clamp((diff - chroma_tolerance) / max(0.01, chroma_tolerance * 0.5), 0.0, 1.0)
            alpha = transition
        elif remove_bg_mode == "Chroma Black":
            max_val = torch.max(wm_rgb[:, :, :3], dim=2).values
            alpha = torch.clamp((max_val - chroma_tolerance) / max(0.01, chroma_tolerance * 0.5), 0.0, 1.0)
        elif remove_bg_mode == "Chroma White":
            min_val = torch.min(wm_rgb[:, :, :3], dim=2).values
            alpha = torch.clamp(((1.0 - chroma_tolerance) - min_val) / max(0.01, chroma_tolerance * 0.5), 0.0, 1.0)
        else:
            alpha = torch.ones((target_wm_h, target_wm_w), device=wm_rgb.device, dtype=wm_rgb.dtype)

        # Apply feathering if requested (GPU-accelerated separable Gaussian blur)
        if feather_radius > 0:
            alpha_4d = alpha.unsqueeze(0).unsqueeze(0)  # [1, 1, H, W]
            alpha_blurred = _gpu_gaussian_blur(alpha_4d, feather_radius)
            alpha = alpha_blurred[0, 0].clamp(0.0, 1.0)

        # Scale alpha by opacity
        alpha = torch.clamp(alpha * opacity, 0.0, 1.0)

        # Broadcast compositing across base_image batch
        out_images = base_image.clone()
        out_masks = torch.zeros((B_base, H_base, W_base), dtype=torch.float32, device=base_image.device)

        # Alpha shape [target_wm_h, target_wm_w, 1]
        alpha_3d = alpha.unsqueeze(-1)
        patch_wm = wm_rgb[:, :, :3] * alpha_3d

        for b in range(B_base):
            base_patch = out_images[b, pos_y:pos_y + target_wm_h, pos_x:pos_x + target_wm_w, :3]
            blended_patch = base_patch * (1.0 - alpha_3d) + patch_wm
            out_images[b, pos_y:pos_y + target_wm_h, pos_x:pos_x + target_wm_w, :3] = blended_patch
            out_masks[b, pos_y:pos_y + target_wm_h, pos_x:pos_x + target_wm_w] = alpha

        info_dict = {
            "position": position,
            "scale_mode": scale_mode,
            "target_width": target_wm_w,
            "target_height": target_wm_h,
            "pos_x": pos_x,
            "pos_y": pos_y,
            "margin_x": margin_x,
            "margin_y": margin_y,
            "opacity": opacity,
            "base_resolution": f"{W_base}x{H_base}",
        }

        return (out_images, out_masks, json.dumps(info_dict, indent=2))
