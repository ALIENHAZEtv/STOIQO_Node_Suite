"""
[STOIQO] Spatial Re-Roll & Contextual Generative Fill Node
Allows selective regeneration of bounding box sub-regions or mask regions
with edge feathering, color profile harmonization, and freeze-lock of surrounding pixels.
"""

import json
import torch
import torch.nn.functional as F

try:
    from ..core.telemetry import NodeTelemetryTimer, inject_telemetry
except (ImportError, ValueError):
    from core.telemetry import NodeTelemetryTimer, inject_telemetry


def _feather_mask_gpu(mask: torch.Tensor, radius: int) -> torch.Tensor:
    """
    Feathers binary/soft mask [B, H, W] directly on GPU using Gaussian convolution.
    """
    if radius <= 0:
        return mask
    device = mask.device
    sigma = max(0.1, float(radius) / 2.0)
    k_size = int(radius) * 2 + 1
    x = torch.arange(-k_size // 2 + 1, k_size // 2 + 1, dtype=torch.float32, device=device)
    k1d = torch.exp(-0.5 * (x / sigma) ** 2)
    k1d = k1d / k1d.sum()
    kh = k1d.view(1, 1, 1, -1)
    kv = k1d.view(1, 1, -1, 1)

    m4d = mask.unsqueeze(1)
    pad = k_size // 2
    feathered = F.conv2d(F.conv2d(m4d, kh, padding=(0, pad)), kv, padding=(pad, 0)).squeeze(1)
    return torch.clamp(feathered, 0.0, 1.0)


def _match_local_color_profile(source: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """
    Transfers mean and standard deviation color profile from target to source.
    Tensors [B, H, W, C] in range 0.0..1.0.
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


class StoiqoSpatialRerollNode:
    """
    [STOIQO] Spatial Re-Roll & Generative Fill
    Selects a target region (via MASK or BBOX JSON), isolates it for regeneration,
    and blends replacement renders seamlessly back into the master image.
    Surrounding pixels are 100% frozen and bit-exact preserved.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "feather_radius": ("INT", {"default": 16, "min": 0, "max": 128, "step": 1}),
                "color_harmonization": ("BOOLEAN", {"default": True}),
                "crop_padding_percent": ("FLOAT", {"default": 0.10, "min": 0.0, "max": 0.50, "step": 0.05}),
            },
            "optional": {
                "mask": ("MASK",),
                "replacement_image": ("IMAGE",),
                "bbox_json": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("IMAGE", "IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("composite_image", "cropped_roi", "roi_mask", "bbox_info")
    FUNCTION = "process_spatial_reroll"
    CATEGORY = "STOIQO"

    def process_spatial_reroll(
        self,
        image: torch.Tensor,
        feather_radius: int,
        color_harmonization: bool,
        crop_padding_percent: float,
        mask: torch.Tensor = None,
        replacement_image: torch.Tensor = None,
        bbox_json: str = "",
    ):
        timer = NodeTelemetryTimer("StoiqoSpatialRerollNode")
        b, h, w, c = image.shape
        device = image.device

        # Determine Bounding Box coordinates
        x1, y1, x2, y2 = 0, 0, w, h
        has_roi = False

        if bbox_json and bbox_json.strip():
            try:
                meta = json.loads(bbox_json)
                bx = meta.get("x", 0)
                by = meta.get("y", 0)
                bw = meta.get("width", meta.get("w", w))
                bh = meta.get("height", meta.get("h", h))
                x1 = max(0, min(w - 1, int(bx)))
                y1 = max(0, min(h - 1, int(by)))
                x2 = max(x1 + 1, min(w, x1 + int(bw)))
                y2 = max(y1 + 1, min(h, y1 + int(bh)))
                has_roi = True
            except Exception:
                has_roi = False

        if not has_roi and mask is not None:
            # Extract bounding box from mask non-zero pixels
            m_batch = mask[0] if mask.ndim == 3 else mask
            nz = torch.nonzero(m_batch > 0.05)
            if len(nz) > 0:
                min_y = int(nz[:, 0].min().item())
                max_y = int(nz[:, 0].max().item())
                min_x = int(nz[:, 1].min().item())
                max_x = int(nz[:, 1].max().item())

                # Apply padding percent
                pad_w = int((max_x - min_x) * crop_padding_percent)
                pad_h = int((max_y - min_y) * crop_padding_percent)

                x1 = max(0, min_x - pad_w)
                y1 = max(0, min_y - pad_h)
                x2 = min(w, max_x + pad_w + 1)
                y2 = min(h, max_y + pad_h + 1)
                has_roi = True

        if not has_roi:
            # Fallback: center 50% box
            x1, y1 = w // 4, h // 4
            x2, y2 = 3 * w // 4, 3 * h // 4

        # Crop Region of Interest (ROI)
        cropped_roi = image[:, y1:y2, x1:x2, :].clone()

        # Build ROI Mask
        if mask is not None:
            roi_mask = mask[:, y1:y2, x1:x2].clone()
        else:
            roi_mask = torch.ones((b, y2 - y1, x2 - x1), dtype=torch.float32, device=device)

        # Feather mask
        if feather_radius > 0:
            roi_mask = _feather_mask_gpu(roi_mask, feather_radius)

        # If replacement image is provided, composite it back
        composite_image = image.clone()
        if replacement_image is not None:
            # Resize replacement to ROI dimensions if needed
            rep = replacement_image
            if rep.shape[1] != (y2 - y1) or rep.shape[2] != (x2 - x1):
                rep = F.interpolate(
                    rep.permute(0, 3, 1, 2),
                    size=(y2 - y1, x2 - x1),
                    mode="bilinear",
                    align_corners=False,
                ).permute(0, 2, 3, 1)

            # Color profile harmonization
            if color_harmonization:
                rep = _match_local_color_profile(rep, cropped_roi)

            # Alpha blending: composite = background * (1 - mask) + replacement * mask
            blend_alpha = roi_mask.unsqueeze(-1).repeat(1, 1, 1, c)
            blended_roi = cropped_roi * (1.0 - blend_alpha) + rep * blend_alpha
            composite_image[:, y1:y2, x1:x2, :] = torch.clamp(blended_roi, 0.0, 1.0)

        bbox_info_dict = {
            "x": x1,
            "y": y1,
            "width": x2 - x1,
            "height": y2 - y1,
            "original_width": w,
            "original_height": h,
            "feather_radius": feather_radius,
            "color_harmonization": color_harmonization,
        }

        timer.stop()
        return (
            composite_image,
            cropped_roi,
            roi_mask,
            json.dumps(bbox_info_dict, indent=2),
        )
