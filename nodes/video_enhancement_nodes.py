"""
[STOIQO] Video Enhancement Node
Unified Temporal Deflicker (Luminance Stabilization) & Frame Rate Multiplier (1x / 2x / 4x Interpolation).
Engineered for AI video generators (Wan 2.1, LTX-Video, CogVideo, AnimateDiff, MiniMax).
"""

import json
import math
import torch
import torch.nn.functional as F

try:
    from ..core.telemetry import NodeTelemetryTimer, inject_telemetry
except (ImportError, ValueError):
    from core.telemetry import NodeTelemetryTimer, inject_telemetry


class StoiqoVideoEnhancerNode:
    """
    [STOIQO] Video Deflicker & Frame Interpolator
    Unifies temporal luminance stabilization (deflicker) and motion-weighted frame
    interpolation (1x / 2x / 4x FPS) in a single GPU-vectorized post-processing hub.
    """

    FPS_MULTIPLIERS = [
        "1x (Original FPS - Deflicker Only)",
        "2x (Double FPS)",
        "4x (Quad FPS)",
    ]

    BLEND_CURVES = [
        "cosine_smooth",
        "bidirectional_linear",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": (
                    "IMAGE",
                    {"tooltip": "Input video frame batch [N, H, W, C]."},
                ),
                "enable_deflicker": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Stabilizes inter-frame luminance fluctuations (flickering/strobing common in AI video).",
                    },
                ),
                "fps_multiplier": (
                    cls.FPS_MULTIPLIERS,
                    {
                        "default": "2x (Double FPS)",
                        "tooltip": "Frame rate multiplier: 1x keeps original frames, 2x doubles FPS, 4x quadruples FPS.",
                    },
                ),
            },
            "optional": {
                "window_size": (
                    "INT",
                    {
                        "default": 5,
                        "min": 3,
                        "max": 15,
                        "step": 2,
                        "tooltip": "Sliding temporal window (in frames) for rolling average luminance computation.",
                    },
                ),
                "luminance_tolerance": (
                    "FLOAT",
                    {
                        "default": 0.08,
                        "min": 0.01,
                        "max": 0.30,
                        "step": 0.01,
                        "tooltip": "Maximum per-frame exposure correction tolerance threshold.",
                    },
                ),
                "stabilization_strength": (
                    "FLOAT",
                    {
                        "default": 0.85,
                        "min": 0.10,
                        "max": 1.0,
                        "step": 0.05,
                        "tooltip": "Temporal luminance stabilization blend intensity.",
                    },
                ),
                "motion_smoothness": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.2,
                        "max": 2.0,
                        "step": 0.1,
                        "tooltip": "Interpolation curve smoothness exponent between adjacent frames.",
                    },
                ),
                "blend_curve": (
                    cls.BLEND_CURVES,
                    {
                        "default": "cosine_smooth",
                        "tooltip": "Mathematical inter-frame blending curve (cosine_smooth = natural S-curve).",
                    },
                ),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("IMAGE", "INT", "STRING")
    RETURN_NAMES = ("enhanced_frames", "output_frame_count", "metrics_json")
    FUNCTION = "enhance_video"
    CATEGORY = "STOIQO"

    def deflicker_video(
        self,
        images: torch.Tensor,
        window_size: int = 5,
        luminance_tolerance: float = 0.08,
        stabilization_strength: float = 0.85,
        unique_id=None,
    ):
        with NodeTelemetryTimer(node_id=unique_id, node_name="TemporalDeflicker"):
            if len(images.shape) == 5:
                images = images.reshape(-1, images.shape[-3], images.shape[-2], images.shape[-1])

            n, h, w, c = images.shape
            if n < 3:
                return (images, json.dumps({"status": "bypassed_insufficient_frames", "frames": n}))

            r = images[..., 0]
            g = images[..., 1]
            b_chan = images[..., 2] if c >= 3 else images[..., 0]
            luma_per_pixel = 0.2126 * r + 0.7152 * g + 0.0722 * b_chan
            frame_lumas = luma_per_pixel.mean(dim=(1, 2))  # [N]

            pad = window_size // 2
            padded_lumas = F.pad(frame_lumas.unsqueeze(0).unsqueeze(0), (pad, pad), mode="replicate").squeeze()
            smoothed_lumas = torch.zeros_like(frame_lumas)

            for i in range(n):
                window = padded_lumas[i : i + window_size]
                smoothed_lumas[i] = window.mean()

            gain_ratios = torch.ones_like(frame_lumas)
            for i in range(n):
                fl = frame_lumas[i].item()
                sl = smoothed_lumas[i].item()
                if fl > 1e-4:
                    ratio = sl / fl
                    clamped_ratio = max(1.0 - luminance_tolerance, min(1.0 + luminance_tolerance, ratio))
                    gain_ratios[i] = 1.0 + (clamped_ratio - 1.0) * stabilization_strength

            output_frames = torch.clamp(images * gain_ratios.view(n, 1, 1, 1), 0.0, 1.0)
            metrics = {
                "total_frames": n,
                "window_size": window_size,
                "luminance_tolerance": luminance_tolerance,
                "avg_correction_pct": round(float(torch.abs(gain_ratios - 1.0).mean().item()) * 100, 2),
                "max_correction_pct": round(float(torch.abs(gain_ratios - 1.0).max().item()) * 100, 2),
            }
            return (output_frames, json.dumps(metrics, indent=2))

    def interpolate_frames(
        self,
        images: torch.Tensor,
        multiplier: str = "2x (Double FPS)",
        motion_smoothness: float = 1.0,
        blend_curve: str = "cosine_smooth",
        unique_id=None,
    ):
        with NodeTelemetryTimer(node_id=unique_id, node_name="FrameInterpolate"):
            if len(images.shape) == 5:
                images = images.reshape(-1, images.shape[-3], images.shape[-2], images.shape[-1])

            n, h, w, c = images.shape
            if "4x" in str(multiplier):
                factor = 4
            elif "2x" in str(multiplier):
                factor = 2
            else:
                factor = 1

            if n < 2 or factor == 1:
                return (images, n, json.dumps({"input_frames": n, "output_frames": n, "multiplier": 1}))

            interpolated_list = []
            for i in range(n - 1):
                f_start = images[i]
                f_end = images[i + 1]
                interpolated_list.append(f_start.unsqueeze(0))

                sub_count = factor - 1
                for step in range(1, sub_count + 1):
                    alpha = float(step) / float(factor)
                    if blend_curve == "cosine_smooth":
                        t = (1.0 - math.cos(alpha * math.pi)) * 0.5
                    else:
                        t = alpha

                    if motion_smoothness != 1.0 and t > 0.0:
                        t = math.pow(t, motion_smoothness)

                    inter_frame = f_start * (1.0 - t) + f_end * t
                    interpolated_list.append(inter_frame.unsqueeze(0))

            interpolated_list.append(images[-1].unsqueeze(0))
            result_tensor = torch.cat(interpolated_list, dim=0)
            total_out = int(result_tensor.shape[0])

            metrics = {
                "input_frames": n,
                "output_frames": total_out,
                "multiplier": factor,
                "blend_curve": blend_curve,
                "motion_smoothness": motion_smoothness,
            }
            return (result_tensor, total_out, json.dumps(metrics, indent=2))

    def enhance_video(
        self,
        images: torch.Tensor,
        enable_deflicker: bool = True,
        fps_multiplier: str = "2x (Double FPS)",
        window_size: int = 5,
        luminance_tolerance: float = 0.08,
        stabilization_strength: float = 0.85,
        motion_smoothness: float = 1.0,
        blend_curve: str = "cosine_smooth",
        unique_id=None,
    ):
        with NodeTelemetryTimer(node_id=unique_id, node_name="VideoEnhancer"):
            if len(images.shape) == 5:
                frames = images.reshape(-1, images.shape[-3], images.shape[-2], images.shape[-1])
            else:
                frames = images

            input_count = int(frames.shape[0])
            combined_metrics = {"input_frames": input_count, "deflicker_enabled": bool(enable_deflicker)}

            if enable_deflicker and input_count >= 3:
                frames, deflicker_json = self.deflicker_video(
                    frames,
                    window_size=window_size,
                    luminance_tolerance=luminance_tolerance,
                    stabilization_strength=stabilization_strength,
                    unique_id=unique_id,
                )
                try:
                    combined_metrics["deflicker"] = json.loads(deflicker_json)
                except Exception:
                    pass

            if "2x" in str(fps_multiplier) or "4x" in str(fps_multiplier):
                frames, out_count, interp_json = self.interpolate_frames(
                    frames,
                    multiplier=fps_multiplier,
                    motion_smoothness=motion_smoothness,
                    blend_curve=blend_curve,
                    unique_id=unique_id,
                )
                try:
                    combined_metrics["interpolation"] = json.loads(interp_json)
                except Exception:
                    pass
            else:
                out_count = int(frames.shape[0])
                combined_metrics["interpolation"] = {"multiplier": 1, "output_frames": out_count}

            combined_metrics["output_frames"] = out_count
            return (frames, out_count, json.dumps(combined_metrics, indent=2))


# Backward-compatible aliases
StoiqoTemporalDeflickerNode = StoiqoVideoEnhancerNode
StoiqoFrameInterpolateNode = StoiqoVideoEnhancerNode
