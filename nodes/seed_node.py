"""
[STOIQO] Seed & Resolution Controller Node
Unified deterministic seed manager (with 5-seed session history & micro-variance)
and aspect-ratio / megapixel resolution calculator with safe VAE divisibility.
"""

import math
import random


class StoiqoSeedControllerNode:
    """
    [STOIQO] Seed & Resolution Controller
    Combines seed management (with session history & Krea 2 micro-variance) and
    safe aspect-ratio / megapixel resolution calculation in a single compact hub.
    """

    CONTROL_MODES = [
        "randomize",
        "fixed",
        "increment",
        "decrement",
    ]

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
        "1.0 MP - Krea 2 Standard (1024 base)",
        "2.0 MP - SeedVR2 2x Upscale Target (1440 base)",
        "4.0 MP - SeedVR2 4x / 4K UHD Master (2160 base)",
        "0.9 MP - MiniMax 720p Video (1280 base)",
        "2.1 MP - MiniMax 1080p Video (1920 base)",
        "Exact Preset Dimensions",
    ]

    MULTIPLE_OPTIONS = [16, 8, 32, 64]

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

    def __init__(self):
        self.last_seed = None
        self.seed_history = []

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "step": 1,
                        "control_after_generate": True,
                        "tooltip": "Base integer seed with native randomize/fixed/increment/decrement controls.",
                    },
                ),
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
                        "tooltip": "Optional input image. If connected, extracts its aspect ratio and scales it to the target megapixel budget.",
                    },
                ),
                "swap_dimensions": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Instantly swaps Width and Height (Landscape <-> Portrait flip).",
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
                "multiple_of": (
                    cls.MULTIPLE_OPTIONS,
                    {
                        "default": 16,
                        "tooltip": "Ensures width and height are divisible by this value (16 recommended for Flux/Krea 2/SeedVR2).",
                    },
                ),
                "variance_strength": (
                    "FLOAT",
                    {
                        "default": 0.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.05,
                        "tooltip": "Micro-variance delta (0.0 = exact deterministic seed, >0.0 = structured perturbation).",
                    },
                ),
                "variance_seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "step": 1,
                        "tooltip": "Secondary seed for deterministic variance blending.",
                    },
                ),
                "seed_prefix": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Optional prefix prepended to seed_str output (e.g. 'seed_').",
                    },
                ),
            },
        }

    RETURN_TYPES = ("INT", "INT", "INT", "INT", "FLOAT", "STRING", "STRING")
    RETURN_NAMES = ("seed", "width", "height", "effective_seed", "aspect_ratio", "resolution_str", "seed_str")
    FUNCTION = "resolve_seed_and_resolution"
    OUTPUT_NODE = True
    CATEGORY = "STOIQO"

    @classmethod
    def IS_CHANGED(
        cls,
        seed=0,
        aspect_ratio="1:1 Square (1024 x 1024)",
        scale_target="1.0 MP - Krea 2 Standard (1024 base)",
        image=None,
        swap_dimensions=False,
        custom_width=1024,
        custom_height=1024,
        multiple_of=16,
        variance_strength=0.0,
        variance_seed=0,
        seed_prefix="",
        control_mode=None,
        **kwargs,
    ):
        if control_mode == "randomize":
            return float("nan")
        img_shape = tuple(image.shape) if (image is not None and hasattr(image, "shape")) else None
        return f"{seed}_{aspect_ratio}_{scale_target}_{img_shape}_{swap_dimensions}_{custom_width}_{custom_height}_{multiple_of}_{variance_strength}_{variance_seed}_{seed_prefix}"

    def get_resolution(
        self,
        aspect_ratio="1:1 Square (1024 x 1024)",
        scale_target="1.0 MP - Krea 2 Standard (1024 base)",
        image=None,
        swap_dimensions=False,
        multiple_of=16,
        custom_width=1024,
        custom_height=1024,
    ):
        try:
            step = max(8, int(str(multiple_of).split()[0]))
        except (ValueError, IndexError):
            step = 16

        # Normalize aspect_ratio key if passed by prefix (e.g. "16:9 ...")
        matched_ar = aspect_ratio
        if matched_ar not in self.PRESET_DIMS_1MP and "Custom" not in str(matched_ar):
            prefix = str(matched_ar).split()[0] if matched_ar else ""
            for k in self.PRESET_DIMS_1MP:
                if prefix and k.startswith(prefix):
                    matched_ar = k
                    break

        if image is not None and hasattr(image, "shape") and len(image.shape) >= 3:
            img_h = int(image.shape[1])
            img_w = int(image.shape[2])

            if scale_target == "Exact Preset Dimensions":
                w = max(step, int(round(img_w / step)) * step)
                h = max(step, int(round(img_h / step)) * step)
            else:
                if "0.26 MP" in scale_target:
                    target_pixels = 512 * 512
                elif "0.9 MP" in scale_target:
                    target_pixels = 1280 * 720
                elif "1.5 MP" in scale_target:
                    target_pixels = 1280 * 1280
                elif "2.0 MP" in scale_target:
                    target_pixels = 1440 * 1440
                elif "2.1 MP" in scale_target:
                    target_pixels = 1920 * 1080
                elif "4.0 MP" in scale_target:
                    target_pixels = 2160 * 2160
                else:
                    target_pixels = 1024 * 1024

                ratio = float(img_w) / max(1.0, float(img_h))
                raw_h = math.sqrt(target_pixels / ratio)
                raw_w = raw_h * ratio
                w = max(step, int(round(raw_w / step)) * step)
                h = max(step, int(round(raw_h / step)) * step)
        elif "Custom" in str(matched_ar):
            w = int(round(custom_width / step)) * step
            h = int(round(custom_height / step)) * step
        elif (scale_target == "Exact Preset Dimensions" or "1.0 MP" in scale_target) and matched_ar in self.PRESET_DIMS_1MP:
            w, h = self.PRESET_DIMS_1MP[matched_ar]
            w = int(round(w / step)) * step
            h = int(round(h / step)) * step
        else:
            if "0.26 MP" in scale_target:
                target_pixels = 512 * 512
            elif "0.9 MP" in scale_target:
                target_pixels = 1280 * 720
            elif "1.5 MP" in scale_target:
                target_pixels = 1280 * 1280
            elif "2.0 MP" in scale_target:
                target_pixels = 1440 * 1440
            elif "2.1 MP" in scale_target:
                target_pixels = 1920 * 1080
            elif "4.0 MP" in scale_target:
                target_pixels = 2160 * 2160
            else:
                target_pixels = 1024 * 1024

            ratio = self.RATIO_VALUES.get(matched_ar, 1.0)
            raw_h = math.sqrt(target_pixels / ratio)
            raw_w = raw_h * ratio
            w = max(step, int(round(raw_w / step)) * step)
            h = max(step, int(round(raw_h / step)) * step)

        if swap_dimensions:
            w, h = h, w

        final_w = int(w)
        final_h = int(h)
        calc_ratio = round(final_w / final_h, 4) if final_h > 0 else 1.0
        mpx = round((final_w * final_h) / 1_000_000.0, 2)
        res_str = f"{final_w}x{final_h} ({calc_ratio:.2f}:1, {mpx} MP)"

        return (final_w, final_h, calc_ratio, res_str)

    def resolve_seed(
        self,
        seed: int = 0,
        variance_strength: float = 0.0,
        variance_seed: int = 0,
        seed_prefix: str = "",
        control_mode: str = None,
        **kwargs,
    ):
        MAX_SEED = 0xFFFFFFFFFFFFFFFF
        active_seed = int(seed)

        if control_mode == "randomize":
            active_seed = random.randint(0, MAX_SEED)
        elif control_mode == "increment":
            active_seed = (active_seed + 1) % MAX_SEED
        elif control_mode == "decrement":
            active_seed = (active_seed - 1) if active_seed > 0 else MAX_SEED

        if variance_strength > 0.0:
            v_seed = variance_seed if variance_seed > 0 else (active_seed ^ 0x5DEECE66D)
            perturbation = int((v_seed % 1000003) * variance_strength)
            effective_seed = (active_seed + perturbation) % MAX_SEED
        else:
            effective_seed = active_seed

        seed_str = f"{seed_prefix}{active_seed}"
        return (active_seed, effective_seed, float(variance_strength), seed_str)

    def resolve_seed_and_resolution(
        self,
        seed: int = 0,
        aspect_ratio: str = "1:1 Square (1024 x 1024)",
        scale_target: str = "1.0 MP - Krea 2 Standard (1024 base)",
        image=None,
        swap_dimensions: bool = False,
        custom_width: int = 1024,
        custom_height: int = 1024,
        multiple_of: int = 16,
        variance_strength: float = 0.0,
        variance_seed: int = 0,
        seed_prefix: str = "",
        control_mode: str = None,
        **kwargs,
    ):
        active_seed, effective_seed, _, seed_str = self.resolve_seed(
            seed=seed,
            variance_strength=variance_strength,
            variance_seed=variance_seed,
            seed_prefix=seed_prefix,
            control_mode=control_mode,
        )
        final_w, final_h, calc_ratio, res_str = self.get_resolution(
            aspect_ratio=aspect_ratio,
            scale_target=scale_target,
            image=image,
            swap_dimensions=swap_dimensions,
            multiple_of=multiple_of,
            custom_width=custom_width,
            custom_height=custom_height,
        )

        # Track last 5 unique seeds in session history
        if not any(item.get("seed") == active_seed for item in self.seed_history):
            self.seed_history.append({"seed": active_seed})
            if len(self.seed_history) > 5:
                self.seed_history = self.seed_history[-5:]

        return {
            "ui": {
                "active_seed": [active_seed],
                "effective_seed": [effective_seed],
                "seed_history": list(self.seed_history),
                "resolution": [f"{final_w}×{final_h}"],
            },
            "result": (
                active_seed,
                final_w,
                final_h,
                effective_seed,
                calc_ratio,
                res_str,
                seed_str,
            ),
        }


# Backward-compatible alias for unit tests importing StoiqoResolutionNode
StoiqoResolutionNode = StoiqoSeedControllerNode
