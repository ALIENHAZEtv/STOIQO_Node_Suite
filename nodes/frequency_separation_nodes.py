"""
[STOIQO] Frequency Separation & Texture Hub Node
High/Low Frequency Decomposition and Seamless Recombination.
Enables professional frequency separation retouching, lighting correction,
micro-texture enhancement, and color grading directly in ComfyUI tensor space.
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


def _soft_knee_limiter(tensor: torch.Tensor, knee: float = 0.08) -> torch.Tensor:
    """
    Soft-knee highlight and shadow limiter.
    Preserves 100% linear fidelity in the normal range [knee, 1.0 - knee],
    while smoothly compressing extreme overshoots via tanh to prevent ringing halos.
    """
    res = tensor.clone()
    high_threshold = 1.0 - knee

    high_mask = res > high_threshold
    if high_mask.any():
        val = res[high_mask] - high_threshold
        res[high_mask] = high_threshold + knee * torch.tanh(val / knee)

    low_mask = res < knee
    if low_mask.any():
        val = knee - res[low_mask]
        res[low_mask] = knee - knee * torch.tanh(val / knee)

    return torch.clamp(res, 0.0, 1.0)


class StoiqoFrequencySeparationNode:
    """
    [STOIQO] Frequency Separation & Texture Hub
    Unified high/low frequency decomposition, micro-texture enhancement, and seamless recomposition.
    - If `high_freq_override` is None: splits `image` into Low and High frequency layers,
      and produces an enhanced/reconstructed master image with adjustable `texture_strength`.
    - If `high_freq_override` is connected: recombines `image` (as base lighting/color) with
      the high-frequency texture layer from `high_freq_override`.
    """

    HIGH_PASS_MODES = [
        "linear_offset_50",
        "raw_residual",
        "vivid_contrast",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": (
                    "IMAGE",
                    {"tooltip": "Source image tensor to decompose into low and high frequencies (or base lighting/color layer for recomposition)."},
                ),
                "blur_radius": (
                    "INT",
                    {
                        "default": 16,
                        "min": 1,
                        "max": 128,
                        "step": 1,
                        "tooltip": "Blur radius determining the boundary between low (lighting/color) and high (texture/pores) frequencies.",
                    },
                ),
                "texture_strength": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.0,
                        "max": 2.5,
                        "step": 0.05,
                        "tooltip": "Strength of high-frequency texture blended into the final output image (1.0 = exact 100% reconstruction; >1.0 = micro-texture boost).",
                    },
                ),
            },
            "optional": {
                "high_freq_override": (
                    "IMAGE",
                    {"tooltip": "Optional external high-frequency texture layer to merge onto `image` (bypasses internal high-pass generation)."},
                ),
                "texture_boost": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.2,
                        "max": 3.0,
                        "step": 0.05,
                        "tooltip": "High-frequency contrast multiplier applied during the decomposition pass.",
                    },
                ),
                "high_pass_mode": (
                    cls.HIGH_PASS_MODES,
                    {
                        "default": "linear_offset_50",
                        "tooltip": "Format of high-pass output: 'linear_offset_50' is standard 50% neutral gray for Photoshop/retouching workflows.",
                    },
                ),
                "soft_knee_limiter": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Smoothly rolls off extreme highlight/shadow overshoots, eliminating ringing halos on high-contrast edges.",
                    },
                ),
                "split_meta": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Optional metadata JSON string to auto-detect settings.",
                    },
                ),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "STRING")
    RETURN_NAMES = ("image", "low_freq_image", "high_freq_image", "split_meta")
    FUNCTION = "process_frequencies"
    CATEGORY = "STOIQO"

    def split_frequencies(
        self,
        image: torch.Tensor,
        blur_radius: int = 16,
        texture_boost: float = 1.0,
        high_pass_mode: str = "linear_offset_50",
        unique_id: str = None,
        **kwargs,
    ):
        """Backward-compatible helper for tests and pipelines calling split_frequencies directly."""
        res = self.process_frequencies(
            image=image,
            blur_radius=blur_radius,
            texture_strength=1.0,
            texture_boost=texture_boost,
            high_pass_mode=high_pass_mode,
            unique_id=unique_id,
            **kwargs,
        )
        # Returns (low_freq_image, high_freq_image, split_meta)
        return (res[1], res[2], res[3])

    def merge_frequencies(
        self,
        low_freq_image: torch.Tensor,
        high_freq_image: torch.Tensor,
        texture_strength: float = 1.0,
        reconstruct_mode: str = "linear_offset_50",
        split_meta: str = "",
        soft_knee_limiter: bool = True,
        unique_id: str = None,
        **kwargs,
    ):
        """Backward-compatible helper for tests and pipelines calling merge_frequencies directly."""
        res = self.process_frequencies(
            image=low_freq_image,
            high_freq_override=high_freq_image,
            texture_strength=texture_strength,
            high_pass_mode=reconstruct_mode,
            split_meta=split_meta,
            soft_knee_limiter=soft_knee_limiter,
            unique_id=unique_id,
            **kwargs,
        )
        # Returns (image,)
        return (res[0],)

    def process_frequencies(
        self,
        image: torch.Tensor,
        blur_radius: int = 16,
        texture_strength: float = 1.0,
        high_freq_override: torch.Tensor = None,
        texture_boost: float = 1.0,
        high_pass_mode: str = "linear_offset_50",
        soft_knee_limiter: bool = True,
        split_meta: str = "",
        unique_id: str = None,
        **kwargs,
    ):
        with NodeTelemetryTimer(node_id=unique_id, node_name="FrequencySeparationHub") as timer:
            b, h, w, c = image.shape
            mode = high_pass_mode

            if split_meta:
                try:
                    parsed = json.loads(split_meta)
                    if isinstance(parsed, dict):
                        if "high_pass_mode" in parsed:
                            mode = parsed["high_pass_mode"]
                        if "blur_radius" in parsed and blur_radius == 16:
                            blur_radius = int(parsed["blur_radius"])
                except Exception:
                    pass

            # 1. Calculate internal Low Frequency
            img_chw = image.permute(0, 3, 1, 2)
            low_chw = _apply_separable_blur(img_chw, blur_radius)
            low_freq = low_chw.permute(0, 2, 3, 1).contiguous()

            # 2. Determine High Frequency Layer
            if high_freq_override is not None:
                hf = high_freq_override.to(device=image.device, dtype=image.dtype)
                if hf.shape[1:3] != image.shape[1:3]:
                    hf = F.interpolate(
                        hf.permute(0, 3, 1, 2),
                        size=(h, w),
                        mode="bilinear",
                        align_corners=False,
                    ).permute(0, 2, 3, 1)
                if hf.shape[-1] != image.shape[-1]:
                    min_c = min(hf.shape[-1], image.shape[-1])
                    hf = hf[..., :min_c]
                high_freq = hf
            else:
                diff = (img_chw - low_chw) * texture_boost
                if mode == "linear_offset_50":
                    high_chw = torch.clamp(diff + 0.5, 0.0, 1.0)
                elif mode == "raw_residual":
                    high_chw = torch.clamp(diff, -1.0, 1.0)
                else:
                    high_chw = torch.clamp(torch.abs(diff) * 2.0, 0.0, 1.0)
                high_freq = high_chw.permute(0, 2, 3, 1).contiguous()

            # 3. Recomposite Master Image
            if mode == "linear_offset_50":
                high_centered = (high_freq - 0.5) * texture_strength
                merged = low_freq + high_centered
            elif mode == "raw_residual":
                merged = low_freq + (high_freq * texture_strength)
            else:
                high_centered = (high_freq - 0.5) * texture_strength
                merged = torch.where(
                    low_freq > 0.5,
                    1.0 - 2.0 * (1.0 - low_freq) * (1.0 - (high_centered + 0.5)),
                    2.0 * low_freq * (high_centered + 0.5),
                )

            if soft_knee_limiter:
                final_image = _soft_knee_limiter(merged, knee=0.08)
            else:
                final_image = torch.clamp(merged, 0.0, 1.0)

            meta = {
                "blur_radius": blur_radius,
                "texture_strength": texture_strength,
                "texture_boost": texture_boost,
                "high_pass_mode": mode,
                "soft_knee_limiter": soft_knee_limiter,
                "dimensions": {"width": w, "height": h, "batch": b},
                "channels": c,
            }
            meta_json = json.dumps(meta, indent=2)

            return inject_telemetry((final_image, low_freq, high_freq, meta_json), timer.get_stats())


# Backward-compatible aliases
StoiqoFrequencySplitNode = StoiqoFrequencySeparationNode
StoiqoFrequencyMergeNode = StoiqoFrequencySeparationNode
