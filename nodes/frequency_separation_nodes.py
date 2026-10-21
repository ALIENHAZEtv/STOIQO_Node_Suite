"""
[STOIQO] Frequency Separation Nodes
High/Low Frequency Decomposition and Seamless Recombination.
Enables professional retouching, lighting correction, and texture enhancement
directly in ComfyUI tensor space.
"""

import json
import torch
import torch.nn.functional as F

try:
    from ..core.telemetry import NodeTelemetryTimer, inject_telemetry
except (ImportError, ValueError):
    from core.telemetry import NodeTelemetryTimer, inject_telemetry


def _apply_separable_blur(tensor: torch.Tensor, radius: int) -> torch.Tensor:
    """
    Applies 2D separable Gaussian blur on tensor [B, C, H, W].
    Zero CPU/GPU transfers, native GPU convolution.
    """
    if radius <= 0:
        return tensor

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


class StoiqoFrequencySplitNode:
    """
    [STOIQO] Frequency Split (Texture & Color Decomposition)
    Splits an image into Low-Frequency (lighting, base colors, soft gradients)
    and High-Frequency (micro-textures, skin pores, hair, sharp edges).
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "blur_radius": ("INT", {"default": 16, "min": 1, "max": 128, "step": 1}),
                "texture_boost": ("FLOAT", {"default": 1.0, "min": 0.2, "max": 3.0, "step": 0.05}),
                "high_pass_mode": (["linear_offset_50", "raw_residual", "absolute_energy"], {"default": "linear_offset_50"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "IMAGE", "STRING")
    RETURN_NAMES = ("low_freq_image", "high_freq_image", "split_meta")
    FUNCTION = "split_frequencies"
    CATEGORY = "STOIQO"

    def split_frequencies(self, image: torch.Tensor, blur_radius: int, texture_boost: float, high_pass_mode: str):
        timer = NodeTelemetryTimer("StoiqoFrequencySplitNode")
        # image shape: [B, H, W, C]
        b, h, w, c = image.shape
        device = image.device

        # Convert to [B, C, H, W] for convolution
        img_chw = image.permute(0, 3, 1, 2)

        # Calculate Low Frequency via Gaussian Blur
        low_chw = _apply_separable_blur(img_chw, blur_radius)

        # Calculate High Frequency residual
        diff = (img_chw - low_chw) * texture_boost

        if high_pass_mode == "linear_offset_50":
            # 50% neutral gray offset (standard high-pass format)
            high_chw = torch.clamp(diff + 0.5, 0.0, 1.0)
        elif high_pass_mode == "raw_residual":
            # Raw difference clamped to valid RGB
            high_chw = torch.clamp(diff, -1.0, 1.0)
        else:
            # Absolute texture energy visualization
            high_chw = torch.clamp(torch.abs(diff) * 2.0, 0.0, 1.0)

        # Permute back to [B, H, W, C]
        low_freq = low_chw.permute(0, 2, 3, 1).contiguous()
        high_freq = high_chw.permute(0, 2, 3, 1).contiguous()

        meta = {
            "blur_radius": blur_radius,
            "texture_boost": texture_boost,
            "high_pass_mode": high_pass_mode,
            "dimensions": {"width": w, "height": h, "batch": b},
            "channels": c,
        }

        timer.stop()
        return (low_freq, high_freq, json.dumps(meta))


class StoiqoFrequencyMergeNode:
    """
    [STOIQO] Frequency Merge & Recomposite
    Recombines Low-Frequency and High-Frequency channels back into a final master image
    with seamless color and texture preservation.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "low_freq_image": ("IMAGE",),
                "high_freq_image": ("IMAGE",),
                "texture_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.5, "step": 0.05}),
                "reconstruct_mode": (["linear_offset_50", "raw_residual", "vivid_contrast"], {"default": "linear_offset_50"}),
            },
            "optional": {
                "split_meta": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "merge_frequencies"
    CATEGORY = "STOIQO"

    def merge_frequencies(self, low_freq_image: torch.Tensor, high_freq_image: torch.Tensor, texture_strength: float, reconstruct_mode: str, split_meta: str = ""):
        timer = NodeTelemetryTimer("StoiqoFrequencyMergeNode")

        # Auto-detect mode from metadata if available
        mode = reconstruct_mode
        if split_meta:
            try:
                parsed = json.loads(split_meta)
                if "high_pass_mode" in parsed:
                    mode = parsed["high_pass_mode"]
            except Exception:
                pass

        if mode == "linear_offset_50":
            # Reconstruct: Low + (High - 0.5) * texture_strength
            high_centered = (high_freq_image - 0.5) * texture_strength
            merged = low_freq_image + high_centered
        elif mode == "raw_residual":
            merged = low_freq_image + (high_freq_image * texture_strength)
        else:
            # Vivid contrast blend
            high_centered = (high_freq_image - 0.5) * texture_strength
            merged = torch.where(
                low_freq_image > 0.5,
                1.0 - 2.0 * (1.0 - low_freq_image) * (1.0 - (high_centered + 0.5)),
                2.0 * low_freq_image * (high_centered + 0.5)
            )

        output = torch.clamp(merged, 0.0, 1.0)
        timer.stop()
        return (output,)
