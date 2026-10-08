"""
[STOIQO] VLM Model Loader Node
Loads and caches a Vision-Language Model in VRAM once, emitting a STOIQO_MODEL pipe
for downstream prompt generators, visual inspectors, and batch captioners.
"""

try:
    from ..core import (
        MODEL_SELECTION_CHOICES,
        QUANTIZATION_OPTIONS,
        ATTENTION_OPTIONS,
        ModelManager,
    )
except (ImportError, ValueError):
    from core import (
        MODEL_SELECTION_CHOICES,
        QUANTIZATION_OPTIONS,
        ATTENTION_OPTIONS,
        ModelManager,
    )


class StoiqoVLMModelLoaderNode:
    """
    Dedicated VLM Model Loader for ComfyUI.
    Initializes Qwen2.5-VL with chosen 4-bit NF4 quantization and attention kernels,
    keeping it resident in VRAM for rapid chained execution without re-load overhead.
    """

    def __init__(self):
        self.model_mgr = ModelManager()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_preset": (
                    MODEL_SELECTION_CHOICES,
                    {
                        "default": MODEL_SELECTION_CHOICES[1],
                        "tooltip": "VLM Model Architecture: Select a pre-quantized 4-bit NF4 preset or choose '📁 Custom Model' to specify a folder already on disk.",
                    },
                ),
                "local_model_path": (
                    "STRING",
                    {
                        "default": "",
                        "placeholder": "Active when model_preset = 'Custom Model' — click Browse or paste path",
                        "tooltip": "Absolute path to a local model folder already on disk.",
                    },
                ),
                "quantization": (
                    QUANTIZATION_OPTIONS,
                    {
                        "default": QUANTIZATION_OPTIONS[0],
                        "tooltip": "VRAM quantization via bitsandbytes. '4bit - NF4' reduces memory by ~70% with negligible quality loss.",
                    },
                ),
                "attention_mode": (
                    ATTENTION_OPTIONS,
                    {
                        "default": ATTENTION_OPTIONS[0],
                        "tooltip": "Attention kernel: 'sdpa' (native PyTorch, fast & stable), 'flash_attention_2' (fastest on RTX 3000+), or 'eager'.",
                    },
                ),
            },
            "optional": {
                "keep_in_vram": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Keep model resident in VRAM for zero-latency subsequent inferences. If False (Low VRAM Mode), unloads the model immediately after generation to give 100% GPU memory to Flux / SDXL.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STOIQO_MODEL",)
    RETURN_NAMES = ("stoiqo_model",)
    FUNCTION = "load_vlm_model"
    CATEGORY = "STOIQO/Prompt Engine"

    def load_vlm_model(self, model_preset, local_model_path, quantization, attention_mode, keep_in_vram=True):
        target_repo = self.model_mgr.resolve_model_repo(model_preset, local_model_path)
        print(f"[STOIQO] Model Loader: preparing {target_repo} ({quantization}, {attention_mode}, keep_in_vram={keep_in_vram})...")
        self.model_mgr.load_model(target_repo, quantization, attention_mode=attention_mode, keep_in_vram=keep_in_vram)
        return (self.model_mgr,)
