"""
[STOIQO] Multi-Image Context Hub Node
Satellite node for Stoiqo Prompt Engine. Manages multi-image contextual fusion,
comparative difference inspection, and character/style consistency without bloating
the single-image engine interface.
"""

import torch


class StoiqoMultiImageContextNode:
    """
    [STOIQO] Multi-Image Context Hub
    Bundles multiple image references (<Image 1>, <Image 2>, <Image 3>) with a chosen fusion directive.
    Connect to 'multi_image_context' input of Stoiqo Prompt Synthesizer Engine.
    """

    FUSION_MODES = [
        "Contextual Fusion (Blend Style & Subject)",
        "Comparative Difference (What Changed)",
        "Character & Style Consistency",
        "Sequential Angle / Multi-View",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_1": ("IMAGE", {"tooltip": "Primary subject image (<Image 1>)."}),
                "image_2": ("IMAGE", {"tooltip": "Secondary reference image (<Image 2> - e.g. style, lighting, or target comparison)."}),
                "fusion_mode": (
                    cls.FUSION_MODES,
                    {"default": cls.FUSION_MODES[0], "tooltip": "Multimodal reasoning strategy applied across connected images."},
                ),
            },
            "optional": {
                "image_3": ("IMAGE", {"tooltip": "Optional tertiary reference image (<Image 3> - e.g. background, color palette, or additional angle)."}),
            },
        }

    RETURN_TYPES = ("STOIQO_CONTEXT",)
    RETURN_NAMES = ("multi_image_context",)
    FUNCTION = "build_context"
    CATEGORY = "STOIQO"

    def build_context(
        self,
        image_1: torch.Tensor,
        image_2: torch.Tensor,
        fusion_mode: str,
        image_3: torch.Tensor = None,
    ):
        images_list = [image_1, image_2]
        if image_3 is not None:
            images_list.append(image_3)

        context_bundle = {
            "images": images_list,
            "fusion_mode": fusion_mode,
        }
        return (context_bundle,)
