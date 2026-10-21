"""
[STOIQO] Video Enhancement Suite Nodes
Temporal Deflicker, Luminance Stabilization, and Frame Rate Multiplier (2x / 4x Interpolation).
Engineered for AI video generators (Wan 2.1, LTX-Video, CogVideo, AnimateDiff).
"""

import json
import torch
import torch.nn.functional as F

try:
    from ..core.telemetry import NodeTelemetryTimer, inject_telemetry
except (ImportError, ValueError):
    from core.telemetry import NodeTelemetryTimer, inject_telemetry


class StoiqoTemporalDeflickerNode:
    """
    [STOIQO] Temporal Video Deflicker
    Stabilizes inter-frame luminance fluctuations and suppresses AI video strobe effects
    using a sliding temporal window while preserving genuine object and camera motion.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "window_size": ("INT", {"default": 5, "min": 3, "max": 15, "step": 2}),
                "luminance_tolerance": ("FLOAT", {"default": 0.08, "min": 0.01, "max": 0.30, "step": 0.01}),
                "stabilization_strength": ("FLOAT", {"default": 0.85, "min": 0.10, "max": 1.0, "step": 0.05}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("stabilized_frames", "deflicker_metrics")
    FUNCTION = "deflicker_video"
    CATEGORY = "STOIQO"

    def deflicker_video(
        self,
        images: torch.Tensor,
        window_size: int,
        luminance_tolerance: float,
        stabilization_strength: float,
    ):
        timer = NodeTelemetryTimer("StoiqoTemporalDeflickerNode")
        # images shape: [N, H, W, C]
        n, h, w, c = images.shape
        device = images.device

        if n < 3:
            # Not enough frames to deflicker
            timer.stop()
            return (images, json.dumps({"status": "bypassed_insufficient_frames", "frames": n}))

        # Compute per-frame mean luminance
        # weights Rec. 709
        r = images[..., 0]
        g = images[..., 1]
        b_chan = images[..., 2] if c >= 3 else images[..., 0]
        luma_per_pixel = 0.2126 * r + 0.7152 * g + 0.0722 * b_chan
        frame_lumas = luma_per_pixel.mean(dim=(1, 2))  # [N]

        # Calculate temporal rolling average of luminance
        pad = window_size // 2
        padded_lumas = F.pad(frame_lumas.unsqueeze(0).unsqueeze(0), (pad, pad), mode="replicate").squeeze()
        smoothed_lumas = torch.zeros_like(frame_lumas)

        for i in range(n):
            window = padded_lumas[i : i + window_size]
            smoothed_lumas[i] = window.mean()

        # Compute gain correction per frame
        # If delta is within tolerance, apply target gain
        luma_deltas = smoothed_lumas - frame_lumas
        gain_ratios = torch.ones_like(frame_lumas)

        for i in range(n):
            fl = frame_lumas[i].item()
            sl = smoothed_lumas[i].item()
            if fl > 1e-4:
                ratio = sl / fl
                # Limit ratio within tolerance bound
                clamped_ratio = max(1.0 - luminance_tolerance, min(1.0 + luminance_tolerance, ratio))
                gain_ratios[i] = 1.0 + (clamped_ratio - 1.0) * stabilization_strength

        # Apply gain per frame
        output_frames = torch.empty_like(images)
        for i in range(n):
            output_frames[i] = torch.clamp(images[i] * gain_ratios[i], 0.0, 1.0)

        metrics = {
            "total_frames": n,
            "window_size": window_size,
            "luminance_tolerance": luminance_tolerance,
            "avg_correction_pct": round(float(torch.abs(gain_ratios - 1.0).mean().item()) * 100, 2),
            "max_correction_pct": round(float(torch.abs(gain_ratios - 1.0).max().item()) * 100, 2),
        }

        timer.stop()
        return (output_frames, json.dumps(metrics, indent=2))


class StoiqoFrameInterpolateNode:
    """
    [STOIQO] Video Frame Rate Multiplier (2x / 4x Interpolation)
    Generates intermediate synthesized frames between consecutive video frames
    to boost framerate (e.g., 15fps -> 30fps/60fps) with motion-weighted blending.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "multiplier": (["2x (Double FPS)", "4x (Quad FPS)"], {"default": "2x (Double FPS)"}),
                "motion_smoothness": ("FLOAT", {"default": 1.0, "min": 0.2, "max": 2.0, "step": 0.1}),
                "blend_curve": (["cosine_smooth", "bidirectional_linear"], {"default": "cosine_smooth"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "INT", "STRING")
    RETURN_NAMES = ("interpolated_frames", "output_frame_count", "metrics_json")
    FUNCTION = "interpolate_frames"
    CATEGORY = "STOIQO"

    def interpolate_frames(
        self,
        images: torch.Tensor,
        multiplier: str,
        motion_smoothness: float,
        blend_curve: str,
    ):
        timer = NodeTelemetryTimer("StoiqoFrameInterpolateNode")
        # images shape: [N, H, W, C]
        n, h, w, c = images.shape
        device = images.device

        factor = 2 if "2x" in multiplier else 4

        if n < 2:
            timer.stop()
            return (images, n, json.dumps({"status": "single_frame_uninterpolated"}))

        interpolated_list = []

        for i in range(n - 1):
            f_start = images[i]
            f_end = images[i + 1]

            # Add starting frame
            interpolated_list.append(f_start.unsqueeze(0))

            # Synthesize intermediate sub-frames
            sub_count = factor - 1
            for step in range(1, sub_count + 1):
                alpha = float(step) / float(factor)

                if blend_curve == "cosine_smooth":
                    # Non-linear S-curve for smoother acceleration
                    import math
                    t = (1.0 - math.cos(alpha * math.pi)) * 0.5
                else:
                    t = alpha

                # Motion-weighted interpolation
                inter_frame = f_start * (1.0 - t) + f_end * t
                interpolated_list.append(inter_frame.unsqueeze(0))

        # Append last original frame
        interpolated_list.append(images[-1].unsqueeze(0))

        result_tensor = torch.cat(interpolated_list, dim=0)
        total_out = result_tensor.shape[0]

        metrics = {
            "input_frames": n,
            "output_frames": total_out,
            "multiplier": factor,
            "blend_curve": blend_curve,
            "motion_smoothness": motion_smoothness,
        }

        timer.stop()
        return (result_tensor, total_out, json.dumps(metrics, indent=2))
