"""
[STOIQO] AI Persona & Style Directives Node
Satellite node for Stoiqo Prompt Engine. Defines AI personas, structural output formats,
and artistic styles without cluttering the main engine node.
"""

try:
    from ..core import (
        SYSTEM_PROMPT_CHOICES,
        PROMPT_TYPES,
        ARTISTIC_STYLES,
    )
except (ImportError, ValueError):
    from core import (
        SYSTEM_PROMPT_CHOICES,
        PROMPT_TYPES,
        ARTISTIC_STYLES,
    )


class StoiqoStyleDirectivesNode:
    """
    [STOIQO] AI Persona & Style Directives
    Configures prompt persona, structural output format, and aesthetic style.
    Connect to 'style_directives' input of Stoiqo Prompt Synthesizer Engine.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "system_prompt": (
                    SYSTEM_PROMPT_CHOICES,
                    {
                        "default": SYSTEM_PROMPT_CHOICES[0],
                        "tooltip": "AI Persona: core competence and role of the vision-language model.",
                    },
                ),
                "prompt_type": (
                    PROMPT_TYPES,
                    {
                        "default": PROMPT_TYPES[0],
                        "tooltip": "Structural output format (e.g. Structured Categories, Detailed Narrative, Short Summary, Tags, Cinematic Script).",
                    },
                ),
                "artistic_style": (
                    ARTISTIC_STYLES,
                    {
                        "default": ARTISTIC_STYLES[0],
                        "tooltip": "Aesthetic style injected into prompt generation (Auto-Detect, Photorealistic, Anime, Cyberpunk, 3D CGI...).",
                    },
                ),
            },
            "optional": {
                "custom_system_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "Active when system_prompt = 'Custom'. Write custom instructions here...",
                        "tooltip": "Custom system instructions used when system_prompt is set to 'Custom'.",
                    },
                ),
                "enable_dual_prompt": ("BOOLEAN", {"default": True, "tooltip": "Generate both concise tags and a long prose prompt."}),
                "audit_artifacts": ("BOOLEAN", {"default": True, "tooltip": "Generate a negative prompt from a visual defect audit."}),
                "negative_prompt_prefix": ("STRING", {"default": "", "placeholder": "e.g. worst quality, low quality, ", "tooltip": "Optional prefix prepended to the generated negative prompt."}),
            },
        }

    RETURN_TYPES = ("STOIQO_STYLE",)
    RETURN_NAMES = ("style_directives",)
    FUNCTION = "build_style"
    CATEGORY = "STOIQO"

    def build_style(
        self,
        system_prompt: str,
        prompt_type: str,
        artistic_style: str,
        custom_system_prompt: str = "",
        enable_dual_prompt: bool = True,
        audit_artifacts: bool = True,
        negative_prompt_prefix: str = "",
    ):
        style_bundle = {
            "system_prompt": system_prompt,
            "custom_system_prompt": custom_system_prompt,
            "prompt_type": prompt_type,
            "artistic_style": artistic_style,
            "enable_dual_prompt": enable_dual_prompt,
            "audit_artifacts": audit_artifacts,
            "negative_prompt_prefix": negative_prompt_prefix,
        }
        return (style_bundle,)
