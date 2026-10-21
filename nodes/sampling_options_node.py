"""
[STOIQO] LLM Sampling & Precision Node
Satellite node for Stoiqo Prompt Engine. Exposes hyperparameter controls
(temperature, top_p, top_k, repetition penalty, max tokens, resolution)
for power users without cluttering the main generation node.
"""


class StoiqoSamplingOptionsNode:
    """
    [STOIQO] LLM Sampling & Precision
    Fine-tunes VLM generation behavior (creativity, determinism, token length, visual resolution).
    Connect to 'sampling_options' input of Stoiqo Prompt Synthesizer Engine.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "temperature": (
                    "FLOAT",
                    {
                        "default": 0.6,
                        "min": 0.0,
                        "max": 2.0,
                        "step": 0.05,
                        "tooltip": "Creativity: 0.0 = deterministic greedy decoding, higher = more diverse.",
                    },
                ),
                "top_p": (
                    "FLOAT",
                    {
                        "default": 0.9,
                        "min": 0.05,
                        "max": 1.0,
                        "step": 0.05,
                        "tooltip": "Nucleus sampling: bounds the cumulative probability tail (1.0 = disabled).",
                    },
                ),
                "top_k": (
                    "INT",
                    {
                        "default": 40,
                        "min": 0,
                        "max": 200,
                        "step": 1,
                        "tooltip": "Limits candidate tokens to top K (0 = disabled).",
                    },
                ),
                "repetition_penalty": (
                    "FLOAT",
                    {
                        "default": 1.1,
                        "min": 1.0,
                        "max": 2.0,
                        "step": 0.05,
                        "tooltip": "Penalizes repeated phrases and tag loops (1.0 = no penalty).",
                    },
                ),
                "max_new_tokens": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 64,
                        "max": 4096,
                        "step": 64,
                        "tooltip": "Maximum token budget for generated prompt response.",
                    },
                ),
                "target_megapixel": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.1,
                        "max": 4.0,
                        "step": 0.1,
                        "round": 0.01,
                        "tooltip": "Visual resolution passed to ViT (1.0 = ~1024x1024). Higher = finer image details, lower = faster/less VRAM.",
                    },
                ),
                "seed": (
                    "INT",
                    {
                        "default": 42,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "control_after_generate": True,
                        "tooltip": "Seed for deterministic prompt sampling.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STOIQO_SAMPLING",)
    RETURN_NAMES = ("sampling_options",)
    FUNCTION = "build_sampling_options"
    CATEGORY = "STOIQO"

    def build_sampling_options(
        self,
        temperature: float = 0.6,
        top_p: float = 0.9,
        top_k: int = 40,
        repetition_penalty: float = 1.1,
        max_new_tokens: int = 1024,
        target_megapixel: float = 1.0,
        seed: int = 42,
    ):
        sampling_bundle = {
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "repetition_penalty": repetition_penalty,
            "max_new_tokens": max_new_tokens,
            "target_megapixel": target_megapixel,
            "seed": seed,
        }
        return (sampling_bundle,)
