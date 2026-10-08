"""
[STOIQO] Image Resolution & Aspect Ratio Node
Calculates optimal width and height for generative models (Flux.1, SDXL, SD 3.5, SD 1.5)
with standard aspect ratio presets, VAE divisibility alignment, dimension swapping, and Megapixel targets.
"""

import math


class StoiqoResolutionNode:
    """
    Image Resolution & Aspect Ratio Generator for ComfyUI.
    Provides standard aspect ratio presets, ensures safe divisibility (multiples of 8/16/32/64)
    to prevent VAE and attention tensor dimension mismatch errors, and outputs clean (width, height).
    """

    ASPECT_RATIOS = [
        "1:1 Square (1024 x 1024)",
        "16:9 Landscape Widescreen (1344 x 768)",
        "9:16 Portrait / Story (768 x 1344)",
        "4:3 Standard Photo (1152 x 896)",
        "3:4 Classic Portrait (896 x 1152)",
        "3:2 Classic 35mm (1216 x 832)",
        "2:3 Portrait 35mm (832 x 1216)",
        "21:9 Ultrawide Cinema (1536 x 640)",
        "9:21 Ultrawide Vertical (640 x 1536)",
        "4:5 Social Media Portrait (960 x 1200)",
        "5:4 Social Media Landscape (1200 x 960)",
        "✏️ Custom (Manual Width & Height)",
    ]

    SCALE_TARGETS = [
        "1.0 MP - Flux.1 / SDXL Standard (1024 base)",
        "0.26 MP - SD 1.5 Legacy (512 base)",
        "1.5 MP - High Quality (1280 base)",
        "2.0 MP - 2K Ultra HD (1440 base)",
        "Exact Preset Dimensions",
    ]

    MULTIPLE_OPTIONS = [16, 8, 32, 64]

    # Pre-calculated standard dimensions for 1.0 MP (Flux/SDXL optimal)
    PRESET_DIMS_1MP = {
        "1:1 Square (1024 x 1024)": (1024, 1024),
        "16:9 Landscape Widescreen (1344 x 768)": (1344, 768),
        "9:16 Portrait / Story (768 x 1344)": (768, 1344),
        "4:3 Standard Photo (1152 x 896)": (1152, 896),
        "3:4 Classic Portrait (896 x 1152)": (896, 1152),
        "3:2 Classic 35mm (1216 x 832)": (1216, 832),
        "2:3 Portrait 35mm (832 x 1216)": (832, 1216),
        "21:9 Ultrawide Cinema (1536 x 640)": (1536, 640),
        "9:21 Ultrawide Vertical (640 x 1536)": (640, 1536),
        "4:5 Social Media Portrait (960 x 1200)": (960, 1200),
        "5:4 Social Media Landscape (1200 x 960)": (1200, 960),
    }

    # Ratio float definitions (w / h)
    RATIO_VALUES = {
        "1:1 Square (1024 x 1024)": 1.0 / 1.0,
        "16:9 Landscape Widescreen (1344 x 768)": 16.0 / 9.0,
        "9:16 Portrait / Story (768 x 1344)": 9.0 / 16.0,
        "4:3 Standard Photo (1152 x 896)": 4.0 / 3.0,
        "3:4 Classic Portrait (896 x 1152)": 3.0 / 4.0,
        "3:2 Classic 35mm (1216 x 832)": 3.0 / 2.0,
        "2:3 Portrait 35mm (832 x 1216)": 2.0 / 3.0,
        "21:9 Ultrawide Cinema (1536 x 640)": 21.0 / 9.0,
        "9:21 Ultrawide Vertical (640 x 1536)": 9.0 / 21.0,
        "4:5 Social Media Portrait (960 x 1200)": 4.0 / 5.0,
        "5:4 Social Media Landscape (1200 x 960)": 5.0 / 4.0,
    }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "aspect_ratio": (
                    cls.ASPECT_RATIOS,
                    {
                        "default": cls.ASPECT_RATIOS[0],
                        "tooltip": "Standard aspect ratio preset or custom manual dimension mode.",
                    },
                ),
                "scale_target": (
                    cls.SCALE_TARGETS,
                    {
                        "default": cls.SCALE_TARGETS[0],
                        "tooltip": "Target total pixel count / megapixel budget for the output image.",
                    },
                ),
            },
            "optional": {
                "image": (
                    "IMAGE",
                    {
                        "tooltip": "Optional input image. If connected, automatically extracts its true aspect ratio and scales it to the target megapixel budget with safe VAE divisibility.",
                    },
                ),
                "swap_dimensions": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Instantly swaps Width and Height (Landscape <-> Portrait flip).",
                    },
                ),
                "multiple_of": (
                    cls.MULTIPLE_OPTIONS,
                    {
                        "default": 16,
                        "tooltip": "Ensures width and height are divisible by this value (16 is recommended for Flux and VAEs).",
                    },
                ),
                "custom_width": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 64,
                        "max": 8192,
                        "step": 8,
                        "tooltip": "Manual width used when '✏️ Custom' aspect ratio is selected.",
                    },
                ),
                "custom_height": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 64,
                        "max": 8192,
                        "step": 8,
                        "tooltip": "Manual height used when '✏️ Custom' aspect ratio is selected.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("INT", "INT", "FLOAT", "STRING")
    RETURN_NAMES = ("width", "height", "aspect_ratio", "resolution_str")
    FUNCTION = "get_resolution"
    CATEGORY = "STOIQO/Utilities"

    def get_resolution(
        self,
        aspect_ratio,
        scale_target,
        image=None,
        swap_dimensions=False,
        multiple_of=16,
        custom_width=1024,
        custom_height=1024,
    ):
        step = max(8, int(multiple_of))

        # Check if an image is connected to auto-detect aspect ratio
        if image is not None and hasattr(image, "shape") and len(image.shape) >= 3:
            # ComfyUI Image tensor shape is [B, H, W, C]
            img_h = int(image.shape[1])
            img_w = int(image.shape[2])

            if scale_target == "Exact Preset Dimensions":
                w = max(step, int(round(img_w / step)) * step)
                h = max(step, int(round(img_h / step)) * step)
            else:
                if "0.26 MP" in scale_target:
                    target_pixels = 512 * 512
                elif "1.5 MP" in scale_target:
                    target_pixels = 1280 * 1280
                elif "2.0 MP" in scale_target:
                    target_pixels = 1440 * 1440
                else:
                    target_pixels = 1024 * 1024

                ratio = float(img_w) / max(1.0, float(img_h))
                raw_h = math.sqrt(target_pixels / ratio)
                raw_w = raw_h * ratio
                w = max(step, int(round(raw_w / step)) * step)
                h = max(step, int(round(raw_h / step)) * step)
        elif aspect_ratio == "✏️ Custom (Manual Width & Height)":
            w = int(round(custom_width / step)) * step
            h = int(round(custom_height / step)) * step
        elif scale_target == "Exact Preset Dimensions" and aspect_ratio in self.PRESET_DIMS_1MP:
            w, h = self.PRESET_DIMS_1MP[aspect_ratio]
            w = int(round(w / step)) * step
            h = int(round(h / step)) * step
        else:
            # Determine target pixel count
            if "0.26 MP" in scale_target:
                target_pixels = 512 * 512  # ~262,144 px
            elif "1.5 MP" in scale_target:
                target_pixels = 1280 * 1280  # ~1,638,400 px
            elif "2.0 MP" in scale_target:
                target_pixels = 1440 * 1440  # ~2,073,600 px
            else:
                # Default 1.0 MP (1024x1024 = 1,048,576 px)
                target_pixels = 1024 * 1024

            ratio = self.RATIO_VALUES.get(aspect_ratio, 1.0)

            # Compute ideal unconstrained dimensions
            raw_h = math.sqrt(target_pixels / ratio)
            raw_w = raw_h * ratio

            # Snap to step multiple
            w = max(step, int(round(raw_w / step)) * step)
            h = max(step, int(round(raw_h / step)) * step)

        # Apply swap if requested
        if swap_dimensions:
            w, h = h, w

        final_w = int(w)
        final_h = int(h)
        calc_ratio = round(final_w / final_h, 4) if final_h > 0 else 1.0
        mpx = round((final_w * final_h) / 1_000_000.0, 2)
        res_str = f"{final_w}x{final_h} ({calc_ratio:.2f}:1, {mpx} MP)"

        return (final_w, final_h, calc_ratio, res_str)
