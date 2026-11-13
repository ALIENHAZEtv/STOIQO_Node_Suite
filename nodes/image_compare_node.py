"""
[STOIQO] Visual Image Compare Slider Node
Provides interactive Before/After image comparison with split slider,
synchronized pan & zoom on identical pixel coordinates, perceptual scientific heatmaps,
binary difference masks, and structural difference metrics (SSIM, PSNR, MAE).
"""

import os
import json
import random
import math
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from PIL.PngImagePlugin import PngInfo

try:
    import folder_paths
except ImportError:
    import tempfile

    class _MockFolderPaths:
        @staticmethod
        def get_temp_directory():
            return tempfile.gettempdir()
        @staticmethod
        def get_output_directory():
            return "./output"
        @staticmethod
        def get_save_image_path(filename_prefix, output_dir, image_width=0, image_height=0):
            return (output_dir, filename_prefix, 0, "", filename_prefix)
    folder_paths = _MockFolderPaths()


def _apply_colormap(diff_intensity: torch.Tensor, colormap: str = "turbo") -> torch.Tensor:
    """
    Applies pure PyTorch vectorized scientific colormaps without heavy matplotlib dependencies.
    Input: diff_intensity tensor in range [0, 1] with shape [B, H, W]
    Output: RGB tensor with shape [B, H, W, 3] in range [0, 1]
    """
    x = diff_intensity.clamp(0.0, 1.0)

    if colormap == "greyscale_diff":
        return torch.stack([x, x, x], dim=-1)

    if colormap == "jet":
        r = (1.5 - torch.abs(4.0 * x - 3.0)).clamp(0.0, 1.0)
        g = (1.5 - torch.abs(4.0 * x - 2.0)).clamp(0.0, 1.0)
        b = (1.5 - torch.abs(4.0 * x - 1.0)).clamp(0.0, 1.0)
        return torch.stack([r, g, b], dim=-1)

    if colormap == "plasma":
        r = (0.05 + 1.2 * x - 0.25 * (x ** 2)).clamp(0.0, 1.0)
        g = (0.02 + 0.1 * x + 0.9 * (x ** 2)).clamp(0.0, 1.0)
        b = (0.5 + 0.8 * torch.sin(x * 3.14159) - 0.6 * x).clamp(0.0, 1.0)
        return torch.stack([r, g, b], dim=-1)

    if colormap == "inferno":
        r = (x * 1.3 - 0.1 * (x ** 2)).clamp(0.0, 1.0)
        g = ((x ** 2) * 1.2).clamp(0.0, 1.0)
        b = (torch.sin(x * 3.14159 * 0.7) * 0.9).clamp(0.0, 1.0)
        return torch.stack([r, g, b], dim=-1)

    # Default: Google Turbo Colormap (perceptually uniform scientific colormap)
    r = (0.1357 + x * (4.61539 - x * (42.6603 - x * (132.131 - x * (152.552 - x * 65.3884))))).clamp(0.0, 1.0)
    g = (0.0914 + x * (2.19418 + x * (4.84297 - x * (14.1850 - x * (4.2773 - x * 2.82956))))).clamp(0.0, 1.0)
    b = (0.1067 + x * (12.5845 - x * (86.4258 - x * (248.887 - x * (324.965 - x * 158.461))))).clamp(0.0, 1.0)
    return torch.stack([r, g, b], dim=-1)


def _calculate_ssim(img1: torch.Tensor, img2: torch.Tensor, window_size: int = 11) -> float:
    """
    Computes Structural Similarity Index (SSIM) between two tensors in range [0, 1].
    Vectorized in pure PyTorch using 2D average pooling.
    """
    if img1.ndim == 3:
        img1 = img1.unsqueeze(0)
    if img2.ndim == 3:
        img2 = img2.unsqueeze(0)

    x = img1.permute(0, 3, 1, 2).float()
    y = img2.permute(0, 3, 1, 2).float()

    c1 = (0.01) ** 2
    c2 = (0.03) ** 2

    pad = window_size // 2
    mu_x = F.avg_pool2d(x, kernel_size=window_size, stride=1, padding=pad)
    mu_y = F.avg_pool2d(y, kernel_size=window_size, stride=1, padding=pad)

    mu_x_sq = mu_x.pow(2)
    mu_y_sq = mu_y.pow(2)
    mu_xy = mu_x * mu_y

    sigma_x_sq = F.avg_pool2d(x * x, kernel_size=window_size, stride=1, padding=pad) - mu_x_sq
    sigma_y_sq = F.avg_pool2d(y * y, kernel_size=window_size, stride=1, padding=pad) - mu_y_sq
    sigma_xy = F.avg_pool2d(x * y, kernel_size=window_size, stride=1, padding=pad) - mu_xy

    ssim_map = ((2 * mu_xy + c1) * (2 * sigma_xy + c2)) / (
        (mu_x_sq + mu_y_sq + c1) * (sigma_x_sq + sigma_y_sq + c2) + 1e-8
    )
    return float(ssim_map.mean().item())


def _align_image_tensors(image_a: torch.Tensor, image_b: torch.Tensor):
    """
    Aligns image_b to match image_a's resolution [B, H, W, C] without stretching or distortion.
    """
    if image_a.shape == image_b.shape:
        return image_a, image_b

    b_a, h_a, w_a, c_a = image_a.shape
    b_b, h_b, w_b, c_b = image_b.shape

    # Expand batch size if one is 1 and the other is > 1
    if b_b == 1 and b_a > 1:
        image_b = image_b.repeat(b_a, 1, 1, 1)

    # Scale and letterbox image_b to match image_a's dimensions
    scale_w = float(w_a) / float(w_b)
    scale_h = float(h_a) / float(h_b)
    scale = min(scale_w, scale_h)

    new_w = max(1, int(round(w_b * scale)))
    new_h = max(1, int(round(h_b * scale)))

    b_perm = image_b.permute(0, 3, 1, 2)
    b_resized = F.interpolate(b_perm, size=(new_h, new_w), mode="bicubic", align_corners=False)

    pad_h = h_a - new_h
    pad_w = w_a - new_w
    pad_top = pad_h // 2
    pad_bottom = pad_h - pad_top
    pad_left = pad_w // 2
    pad_right = pad_w - pad_left

    b_padded = F.pad(b_resized, (pad_left, pad_right, pad_top, pad_bottom), mode="constant", value=0.0)
    aligned_b = b_padded.permute(0, 2, 3, 1).clamp(0.0, 1.0)

    return image_a, aligned_b


class StoiqoImageCompareNode:
    """
    [STOIQO] Visual Compare Slider & Zoom
    Interactive Visual Comparison and Mathematical Difference Analyzer for ComfyUI.
    Compares two images with a draggable split slider, synchronized pan & zoom locked to the
    exact same coordinates, false-color thermal heatmaps, binary difference masks, and SSIM/PSNR metrics.
    """

    COMPARISON_MODES = [
        "Split Slider (Before / After)",
        "Hover Slider (rgthree style)",
        "Hold to Toggle (A/B Flicker)",
        "Side-by-Side (Synchronized)",
    ]

    COLORMAP_CHOICES = ["turbo", "inferno", "plasma", "jet", "greyscale_diff"]

    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
        self.prefix_append = "_stoiqo_compare_" + "".join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(5))
        self.compress_level = 1
        self._last_saved_files = []

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_a": (
                    "IMAGE",
                    {"tooltip": "Image A (Before / Baseline / Batch of images to compare)."},
                ),
            },
            "optional": {
                "image_b": (
                    "IMAGE",
                    {"tooltip": "Image B (After / Upscaled / Altered - optional if image_a is a batch)."},
                ),
                "initial_mode": (
                    cls.COMPARISON_MODES,
                    {
                        "default": cls.COMPARISON_MODES[0],
                        "tooltip": "Default interaction mode on canvas: Split Slider curtain, Hover Slider, Hold to Toggle, or Side-by-Side.",
                    },
                ),
                "heatmap_colormap": (
                    cls.COLORMAP_CHOICES,
                    {
                        "default": "turbo",
                        "tooltip": "Scientific false-color palette for visual heatmap (Turbo, Inferno, Plasma, Jet).",
                    },
                ),
                "diff_gain": (
                    "FLOAT",
                    {
                        "default": 2.0,
                        "min": 0.1,
                        "max": 10.0,
                        "step": 0.1,
                        "tooltip": "Heatmap sensitivity boost multiplier to expose subtle micro-differences.",
                    },
                ),
                "mask_threshold": (
                    "FLOAT",
                    {
                        "default": 0.05,
                        "min": 0.001,
                        "max": 1.0,
                        "step": 0.01,
                        "tooltip": "Pixel difference threshold for binary change mask (0.05 = 5% RGB delta).",
                    },
                ),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("image_a", "image_b", "diff_heatmap", "diff_mask", "metrics_json")
    FUNCTION = "compare_images"
    OUTPUT_NODE = True
    CATEGORY = "STOIQO"

    def compare_images(
        self,
        image_a,
        image_b=None,
        initial_mode=COMPARISON_MODES[0],
        heatmap_colormap="turbo",
        diff_gain=2.0,
        mask_threshold=0.05,
        prompt=None,
        extra_pnginfo=None,
    ):
        if image_a is None and image_b is None:
            raise ValueError("[STOIQO Image Compare] At least image_a must be connected.")
        if image_a is None:
            image_a = image_b
            image_b = None
        if len(image_a) == 0:
            raise ValueError("[STOIQO Image Compare] Input image tensor must contain at least one frame.")

        # Clean up temporary files from previous generations
        if hasattr(self, "_last_saved_files") and self._last_saved_files:
            for old_path in self._last_saved_files:
                try:
                    if os.path.exists(old_path):
                        os.remove(old_path)
                except OSError:
                    pass
            self._last_saved_files = []
        else:
            self._last_saved_files = []

        self.output_dir = folder_paths.get_temp_directory()
        filename_prefix = "stoiqo_cmp" + self.prefix_append
        full_output_folder, filename, counter, subfolder, _ = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, image_a[0].shape[1], image_a[0].shape[0]
        )

        # Distribute frames into A and B groups
        if image_b is not None and len(image_b) > 0:
            frames_a = [image_a[i] for i in range(min(len(image_a), 8))]
            frames_b = [image_b[i] for i in range(min(len(image_b), 8))]
            eff_b = image_b
        elif len(image_a) >= 2:
            # Single input with batch >= 2: compare item 0 vs items 1..N
            frames_a = [image_a[0]]
            frames_b = [image_a[i] for i in range(1, min(len(image_a), 9))]
            eff_b = image_a[1:2]
        else:
            frames_a = [image_a[0]]
            frames_b = [image_a[0]]
            eff_b = image_a

        # ── 1. Calculate Mathematical Difference Metrics, Heatmap & Mask ──
        aligned_a, aligned_b = _align_image_tensors(image_a[0:1], eff_b[0:1])
        b_dev = aligned_a.device
        aligned_b = aligned_b.to(device=b_dev)

        delta = torch.abs(aligned_a - aligned_b)
        delta_intensity = delta.mean(dim=-1)  # [1, H, W]

        # Calculate metrics
        mse = torch.mean((aligned_a - aligned_b) ** 2).item()
        psnr = 10.0 * math.log10(1.0 / max(mse, 1e-10))
        mae = delta.mean().item()
        ssim_val = _calculate_ssim(aligned_a, aligned_b)

        # Binary Difference Mask
        diff_mask = (delta_intensity > mask_threshold).float()  # [1, H, W]
        changed_pixels_pct = round(float(diff_mask.mean().item()) * 100.0, 2)

        # Amplified false-color heatmap
        amplified = (delta_intensity * diff_gain).clamp(0.0, 1.0)
        diff_heatmap = _apply_colormap(amplified, colormap=heatmap_colormap)  # [1, H, W, 3]

        metrics_data = {
            "ssim": round(ssim_val, 4),
            "psnr_db": round(psnr, 2),
            "mae": round(mae, 4),
            "changed_pixels_pct": changed_pixels_pct,
            "mask_threshold": mask_threshold,
            "diff_gain": diff_gain,
            "colormap": heatmap_colormap,
            "dimensions": f"{aligned_a.shape[2]}x{aligned_a.shape[1]}",
        }
        metrics_json = json.dumps(metrics_data, indent=2)

        # ── 2. Save preview frames (A, B and Diff Heatmap) for canvas ──
        items_to_save = []
        is_multi_a = len(frames_a) > 1
        for idx, t_img in enumerate(frames_a):
            tag = f"A{idx + 1}" if is_multi_a else "A"
            label = f"Image A ({idx + 1})" if is_multi_a else "Image A (Original)"
            items_to_save.append(("A", idx, tag, t_img, label))

        is_multi_b = len(frames_b) > 1
        for idx, t_img in enumerate(frames_b):
            tag = f"B{idx + 1}" if is_multi_b else "B"
            label = f"Image B ({idx + 1})" if is_multi_b else "Image B (Altered)"
            items_to_save.append(("B", idx, tag, t_img, label))

        # Add Heatmap frame as third selectable side
        items_to_save.append(("DIFF", 0, "HEATMAP", diff_heatmap[0], f"Heatmap (Δ: {changed_pixels_pct}%)"))

        results = []
        for side, idx, tag, tensor_img, label in items_to_save:
            arr = (255.0 * tensor_img.detach().cpu().numpy()).clip(0, 255).astype(np.uint8)
            pil_img = Image.fromarray(arr)

            metadata = PngInfo()
            if prompt is not None:
                metadata.add_text("prompt", json.dumps(prompt))
            if extra_pnginfo is not None:
                for k, v in extra_pnginfo.items():
                    metadata.add_text(k, json.dumps(v))

            file_name = f"{filename}_{tag}_{counter:05}_.png"
            file_path = os.path.join(full_output_folder, file_name)
            pil_img.save(file_path, pnginfo=metadata, compress_level=self.compress_level)
            self._last_saved_files.append(file_path)

            results.append({
                "filename": file_name,
                "subfolder": subfolder,
                "type": self.type,
                "label": label,
                "name": tag,
                "side": side,
                "index": idx,
                "width": pil_img.width,
                "height": pil_img.height,
            })
            counter += 1

        final_b = image_b if image_b is not None else image_a
        return {
            "ui": {
                "stoiqo_images": results,
                "mode": [initial_mode],
                "metrics": [metrics_data],
            },
            "result": (image_a, final_b, diff_heatmap, diff_mask, metrics_json),
        }
