"""
[STOIQO] Smart Watermark & Logo Stamp Node
High-efficiency node that replaces complex multi-node watermarking pipelines.
Supports:
1. External logo / watermark images with automatic chroma-key background removal.
2. Dynamic on-the-fly typographic watermark synthesis (text, font, color, outline/shadow) without requiring external PNGs.
3. 9 cardinal placement anchors (Top-Left, Top-Center, Top-Right, Center-Left, Center, Center-Right, Bottom-Left, Bottom-Center, Bottom-Right).
4. Professional blend modes (Normal Alpha, Screen, Multiply, Overlay, Add / Glow).
5. Hardware-accelerated GPU feathering and telemetry tracking.
"""

import json
import numpy as np
import torch
import torch.nn.functional as F

try:
    from ..core.telemetry import NodeTelemetryTimer, inject_telemetry
except (ImportError, ValueError):
    from core.telemetry import NodeTelemetryTimer, inject_telemetry


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


def _render_text_watermark(
    text: str,
    font_category: str = "sans-serif",
    text_color: str = "white",
    add_outline: bool = True,
) -> torch.Tensor:
    """
    Renders high-definition typographic text with anti-aliasing and drop shadow into RGBA PyTorch tensor [1, H, W, 4].
    """
    from PIL import Image, ImageDraw, ImageFont

    color_map = {
        "white": (255, 255, 255),
        "black": (20, 20, 20),
        "gold": (255, 215, 0),
        "silver": (192, 192, 192),
        "cyan": (0, 230, 255),
        "red": (255, 50, 50),
    }
    rgb = color_map.get(text_color.lower(), (255, 255, 255))
    outline_color = (0, 0, 0, 220) if text_color.lower() != "black" else (255, 255, 255, 220)

    font_names = {
        "sans-serif": ["arial.ttf", "segoeui.ttf", "tahoma.ttf", "DejaVuSans.ttf"],
        "serif": ["times.ttf", "georgia.ttf", "DejaVuSerif.ttf"],
        "monospace": ["consola.ttf", "cour.ttf", "DejaVuSansMono.ttf"],
    }
    selected_names = font_names.get(font_category, font_names["sans-serif"])

    font_size = 48
    font = None
    for name in selected_names:
        try:
            font = ImageFont.truetype(name, font_size)
            break
        except Exception:
            pass
    if font is None:
        try:
            font = ImageFont.load_default()
        except Exception:
            pass

    dummy_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    draw = ImageDraw.Draw(dummy_img)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = max(10, bbox[2] - bbox[0])
    text_h = max(10, bbox[3] - bbox[1])

    pad = 8
    canvas_w = text_w + pad * 2
    canvas_h = text_h + pad * 2

    img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if add_outline:
        for ox in (-2, -1, 0, 1, 2):
            for oy in (-2, -1, 0, 1, 2):
                if ox != 0 or oy != 0:
                    draw.text((pad + ox - bbox[0], pad + oy - bbox[1]), text, font=font, fill=outline_color)

    draw.text((pad - bbox[0], pad - bbox[1]), text, font=font, fill=(*rgb, 255))

    np_img = np.array(img, dtype=np.float32) / 255.0
    return torch.from_numpy(np_img).unsqueeze(0)


def _blend_pixels(base_patch: torch.Tensor, wm_rgb: torch.Tensor, alpha_3d: torch.Tensor, blend_mode: str) -> torch.Tensor:
    """
    Applies creative blending modes between base image patch and watermark in linear float32.
    """
    if "Screen" in blend_mode:
        screen = 1.0 - (1.0 - base_patch) * (1.0 - wm_rgb)
        return base_patch * (1.0 - alpha_3d) + screen * alpha_3d
    elif "Multiply" in blend_mode:
        mult = base_patch * wm_rgb
        return base_patch * (1.0 - alpha_3d) + mult * alpha_3d
    elif "Overlay" in blend_mode:
        overlay = torch.where(
            base_patch <= 0.5,
            2.0 * base_patch * wm_rgb,
            1.0 - 2.0 * (1.0 - base_patch) * (1.0 - wm_rgb),
        )
        return base_patch * (1.0 - alpha_3d) + overlay * alpha_3d
    elif "Add" in blend_mode or "Glow" in blend_mode:
        return (base_patch + wm_rgb * alpha_3d).clamp(0.0, 1.0)
    else:
        return base_patch * (1.0 - alpha_3d) + wm_rgb * alpha_3d


class StoiqoWatermarkNode:
    """
    [STOIQO] Smart Watermark & Logo Stamp
    Stamps branding logos or on-the-fly typographic text over image batches with smart scaling,
    9 cardinal anchors, automatic chroma/alpha extraction, blend modes, and feathering.
    """

    POSITION_CHOICES = [
        "Bottom-Right",
        "Bottom-Left",
        "Top-Right",
        "Top-Left",
        "Center",
        "Top-Center",
        "Bottom-Center",
        "Center-Left",
        "Center-Right",
    ]

    SCALE_CHOICES = [
        "1/8 (Default)",
        "1/10",
        "1/6",
        "1/5",
        "1/4",
        "1/3",
        "1/2",
        "Custom Ratio",
        "Custom Width (px)",
    ]

    BLEND_CHOICES = [
        "Normal (Alpha)",
        "Screen (Light Logo)",
        "Multiply (Dark Logo)",
        "Overlay (Contrast)",
        "Add (Glow)",
    ]

    CHROMA_CHOICES = [
        "None (Use Alpha/RGB)",
        "Auto Chroma (Corner)",
        "Chroma Black",
        "Chroma White",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_image": ("IMAGE", {"tooltip": "Base image or batch of images to watermark."}),
                "position": (cls.POSITION_CHOICES, {"default": "Bottom-Right", "tooltip": "Placement anchor on the base image (9 cardinal anchors)."}),
                "scale_mode": (cls.SCALE_CHOICES, {"default": "1/8 (Default)", "tooltip": "Size of watermark relative to base image width or fixed pixels."}),
                "custom_scale": ("FLOAT", {"default": 0.125, "min": 0.005, "max": 8192.0, "step": 0.005, "tooltip": "Multiplier for Custom Ratio (0.01 - 1.0) or exact pixel width when Custom Width (px) is selected."}),
                "margin_percent": ("FLOAT", {"default": 0.02, "min": 0.0, "max": 0.35, "step": 0.005, "tooltip": "Margin distance from image borders as a fraction of image dimensions (0.02 = 2%)."}),
                "opacity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.02, "tooltip": "Overall opacity of the watermark overlay (0.0 = invisible, 1.0 = solid)."}),
                "blend_mode": (cls.BLEND_CHOICES, {"default": "Normal (Alpha)", "tooltip": "Compositing blend mode (Normal, Screen, Multiply, Overlay, Add)."}),
            },
            "optional": {
                "watermark_image": ("IMAGE", {"tooltip": "Logo or watermark image. Takes precedence over text watermark when connected."}),
                "text_watermark": ("STRING", {"default": "", "placeholder": "Optional text to stamp (leave empty if using watermark_image)...", "tooltip": "Typographic watermark rendered on-the-fly without needing external files."}),
                "text_color": (["white", "black", "gold", "silver", "cyan", "red"], {"default": "white", "tooltip": "Color for text watermark."}),
                "remove_bg_mode": (cls.CHROMA_CHOICES, {"default": "None (Use Alpha/RGB)", "tooltip": "Automatically remove background color (e.g. black or white logo backgrounds)."}),
                "chroma_tolerance": ("FLOAT", {"default": 0.10, "min": 0.01, "max": 0.60, "step": 0.01, "tooltip": "Color distance threshold for chroma background removal."}),
                "feather_radius": ("INT", {"default": 0, "min": 0, "max": 32, "step": 1, "tooltip": "Gaussian feathering radius in pixels to soften watermark outer edges."}),
                "optional_mask": ("MASK", {"tooltip": "Optional external alpha mask for the watermark image (overrides internal chroma keying if provided)."}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("image", "watermark_mask", "overlay_info")
    FUNCTION = "apply_watermark"
    CATEGORY = "STOIQO"

    def apply_watermark(
        self,
        base_image: torch.Tensor,
        position: str = "Bottom-Right",
        scale_mode: str = "1/8 (Default)",
        custom_scale: float = 0.125,
        margin_percent: float = 0.02,
        opacity: float = 1.0,
        blend_mode: str = "Normal (Alpha)",
        watermark_image: torch.Tensor = None,
        text_watermark: str = "",
        text_color: str = "white",
        remove_bg_mode: str = "None (Use Alpha/RGB)",
        chroma_tolerance: float = 0.10,
        feather_radius: int = 0,
        optional_mask: torch.Tensor = None,
        unique_id: str = None,
        **kwargs,
    ):
        timer = NodeTelemetryTimer(node_id=unique_id, node_name="SmartWatermark") if NodeTelemetryTimer else None
        if timer:
            timer.__enter__()

        # Ensure base_image is 4D [B, H, W, C]
        if base_image.ndim == 3:
            base_image = base_image.unsqueeze(0)

        B_base, H_base, W_base, C_base = base_image.shape

        # Resolve active watermark source (Image or Typographic Text)
        if watermark_image is not None and isinstance(watermark_image, torch.Tensor):
            active_wm = watermark_image
            wm_source_type = "image"
        elif text_watermark and text_watermark.strip():
            text_font = kwargs.get("text_font", "sans-serif")
            text_outline = kwargs.get("text_outline", True)
            active_wm = _render_text_watermark(
                text=text_watermark.strip(),
                font_category=text_font,
                text_color=text_color,
                add_outline=text_outline,
            )
            wm_source_type = f"text: '{text_watermark.strip()}'"
        else:
            # No watermark image and no text provided: clean bypass without modifying image
            zero_mask = torch.zeros((B_base, H_base, W_base), dtype=torch.float32, device=base_image.device)
            return (base_image, zero_mask, "No watermark applied (no watermark_image or text_watermark provided).")

        B_base, H_base, W_base, C_base = base_image.shape
        B_wm, H_wm, W_wm, C_wm = active_wm.shape

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

        wm_aspect = float(H_wm) / float(W_wm)
        target_wm_h = max(16, int(round(target_wm_w * wm_aspect)))

        if target_wm_h > H_base:
            target_wm_h = H_base
            target_wm_w = max(16, int(round(target_wm_h / wm_aspect)))

        margin_x = int(round(W_base * margin_percent))
        margin_y = int(round(H_base * margin_percent))

        # Calculate top-left (pos_x, pos_y) based on all 9 cardinal positions
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
        elif position == "Center-Left":
            pos_x = margin_x
            pos_y = (H_base - target_wm_h) // 2
        elif position == "Center-Right":
            pos_x = W_base - target_wm_w - margin_x
            pos_y = (H_base - target_wm_h) // 2
        else:
            pos_x = W_base - target_wm_w - margin_x
            pos_y = H_base - target_wm_h - margin_y

        pos_x = max(0, min(W_base - target_wm_w, pos_x))
        pos_y = max(0, min(H_base - target_wm_h, pos_y))

        # Prepare watermark image resized to (target_wm_h, target_wm_w)
        wm_source = active_wm[0:1].to(device=base_image.device, dtype=base_image.dtype)
        wm_perm = wm_source.permute(0, 3, 1, 2)
        wm_resized = F.interpolate(wm_perm, size=(target_wm_h, target_wm_w), mode="bilinear", align_corners=False)
        wm_rgb = wm_resized.permute(0, 2, 3, 1)[0]  # [target_wm_h, target_wm_w, C]

        # Compute Alpha Mask
        if optional_mask is not None:
            mask_t = optional_mask[0:1].to(device=base_image.device, dtype=base_image.dtype)
            if len(mask_t.shape) == 3:
                mask_t = mask_t.unsqueeze(1)
            mask_resized = F.interpolate(mask_t, size=(target_wm_h, target_wm_w), mode="bilinear", align_corners=False)
            alpha = mask_resized[0, 0]
        elif C_wm >= 4:
            # Native alpha channel in watermark
            alpha = wm_resized[0, 3]
        elif remove_bg_mode == "Auto Chroma (Corner)":
            corner_color = wm_rgb[0, 0, :3]
            diff = torch.norm(wm_rgb[:, :, :3] - corner_color, dim=2)
            alpha = torch.clamp((diff - chroma_tolerance) / max(0.01, chroma_tolerance * 0.5), 0.0, 1.0)
        elif remove_bg_mode == "Chroma Black":
            max_val = torch.max(wm_rgb[:, :, :3], dim=2).values
            alpha = torch.clamp((max_val - chroma_tolerance) / max(0.01, chroma_tolerance * 0.5), 0.0, 1.0)
        elif remove_bg_mode == "Chroma White":
            min_val = torch.min(wm_rgb[:, :, :3], dim=2).values
            alpha = torch.clamp(((1.0 - chroma_tolerance) - min_val) / max(0.01, chroma_tolerance * 0.5), 0.0, 1.0)
        elif "None" in remove_bg_mode or "Preserve" in remove_bg_mode:
            alpha = torch.ones((target_wm_h, target_wm_w), device=wm_rgb.device, dtype=wm_rgb.dtype)
        else:
            alpha = torch.ones((target_wm_h, target_wm_w), device=wm_rgb.device, dtype=wm_rgb.dtype)

        # Apply feathering if requested (GPU-accelerated separable Gaussian blur)
        if feather_radius > 0:
            alpha_4d = alpha.unsqueeze(0).unsqueeze(0)
            alpha_blurred = _gpu_gaussian_blur(alpha_4d, feather_radius)
            alpha = alpha_blurred[0, 0].clamp(0.0, 1.0)

        # Scale alpha by opacity
        alpha = torch.clamp(alpha * float(opacity), 0.0, 1.0)

        # Broadcast compositing across base_image batch
        out_images = base_image.clone()
        out_masks = torch.zeros((B_base, H_base, W_base), dtype=torch.float32, device=base_image.device)

        alpha_3d = alpha.unsqueeze(-1)
        wm_patch = wm_rgb[:, :, :3]

        for b in range(B_base):
            base_patch = out_images[b, pos_y:pos_y + target_wm_h, pos_x:pos_x + target_wm_w, :3]
            blended = _blend_pixels(base_patch, wm_patch, alpha_3d, blend_mode)
            out_images[b, pos_y:pos_y + target_wm_h, pos_x:pos_x + target_wm_w, :3] = blended
            out_masks[b, pos_y:pos_y + target_wm_h, pos_x:pos_x + target_wm_w] = alpha

        info_dict = {
            "position": position,
            "scale_mode": scale_mode,
            "blend_mode": blend_mode,
            "source_type": wm_source_type,
            "target_width": target_wm_w,
            "target_height": target_wm_h,
            "pos_x": pos_x,
            "pos_y": pos_y,
            "margin_x": margin_x,
            "margin_y": margin_y,
            "opacity": opacity,
            "base_resolution": f"{W_base}x{H_base}",
        }

        safe_wm_type = str(wm_source_type).replace("©", "(c)")
        print(f"[STOIQO] Watermark: Applied {safe_wm_type} at {position} ({target_wm_w}x{target_wm_h}px, blend: {blend_mode}, opacity: {opacity})")

        return inject_telemetry(
            (out_images, out_masks, json.dumps(info_dict, indent=2)),
            timer.get_stats() if timer else None,
        )
