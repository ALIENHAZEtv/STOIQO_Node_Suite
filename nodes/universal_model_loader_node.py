"""
[STOIQO] Universal Model Loader Node (All-in-One)
Polymorphic loader and dynamic model stacker for ComfyUI:
- Dynamic Stack UI: Add multiple models, toggle them on/off, select active model
- Diffusion Models (UNET / DiT / GGUF) -> MODEL
- Text Encoders / CLIP -> CLIP
- Variational AutoEncoders -> VAE
- Vision-Language Models (VLM / LLM) -> MODEL / CLIP
- Full Checkpoints -> MODEL / CLIP / VAE
"""

import json
import logging

logger = logging.getLogger("STOIQO")

try:
    import folder_paths
except ImportError:
    folder_paths = None

try:
    from ..core.universal_loader import (
        UniversalModelEngine,
        get_universal_model_choices,
        scan_all_system_models,
        SAMPLING_PRESETS,
    )
    from ..core.telemetry import NodeTelemetryTimer
except (ImportError, ValueError):
    from core.universal_loader import (
        UniversalModelEngine,
        get_universal_model_choices,
        scan_all_system_models,
        SAMPLING_PRESETS,
    )
    from core.telemetry import NodeTelemetryTimer


def register_model_loader_routes():
    """Registers GET /stoiqo/models endpoint for canvas UI model stacker."""
    try:
        from server import PromptServer
        from aiohttp import web

        if hasattr(PromptServer, "instance") and PromptServer.instance is not None:
            routes = PromptServer.instance.routes
            if not any(getattr(r, "path", None) == "/stoiqo/models" for r in routes):
                @routes.get("/stoiqo/models")
                async def stoiqo_list_models(request):
                    try:
                        choices = get_universal_model_choices()
                    except Exception:
                        choices = []
                    return web.json_response({"models": list(choices), "presets": list(SAMPLING_PRESETS)})
    except Exception as exc:
        logger.debug(f"[STOIQO] Notice: Model loader route registration deferred: {exc}")


register_model_loader_routes()


def parse_model_stack(raw):
    """
    Parses JSON list stored by the canvas widget:
    [{"name": str, "enabled": bool, "precision": str, "attention": str}, ...]
    """
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return []
        try:
            raw = json.loads(raw)
        except Exception:
            return []
    if not isinstance(raw, list):
        return []

    entries = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        entries.append({
            "name": name,
            "enabled": bool(item.get("enabled", True)),
            "precision": str(item.get("precision") or "default"),
            "attention": str(item.get("attention") or "sdpa"),
            "clip_type": str(item.get("clip_type") or "auto"),
            "flow_shift_preset": str(item.get("flow_shift_preset") or "None (Standard / SD1.5 / SDXL / Krea 2)"),
            "custom_shift": float(item.get("custom_shift", 3.0)),
            "custom_path": str(item.get("custom_path") or ""),
        })
    return entries


class StoiqoUniversalModelLoaderNode:
    """
    [STOIQO] Universal Model Loader (All-in-One)
    Polymorphic loader for ComfyUI. Automatically sniffs and loads any model type:
    - Diffusion Models (DiT, UNET, GGUF)
    - Text Encoders & CLIPs
    - Variational Autoencoders (VAE)
    - Vision-Language Models (VLM / LLM)
    - Full Checkpoints

    Features a single universal output pin (*) that dynamically connects to any
    downstream model input socket (model, clip, vae).
    """

    def __init__(self):
        self.engine = UniversalModelEngine()

    @classmethod
    def INPUT_TYPES(cls):
        choices = get_universal_model_choices()
        return {
            "required": {
                "model_name": (
                    choices,
                    {
                        "default": choices[0],
                        "tooltip": "Fallback single model selection if dynamic model stack is not used.",
                    },
                ),
                "clip_type": (
                    ["auto", "krea2", "flux", "wan", "sd3", "ace", "qwen_image", "lumina2", "mochi", "ltxv", "minimax", "stable_diffusion"],
                    {
                        "default": "auto",
                        "tooltip": "Recipe for text encoders (auto detects Krea2, Flux, Wan, Ace, etc. automatically).",
                    },
                ),
                "precision": (
                    ["default", "fp8_e4m3fn", "fp8_e4m3fn_fast", "fp8_e5m2", "4bit - NF4", "8bit", "fp16", "bf16"],
                    {
                        "default": "default",
                        "tooltip": "Precision / quantization mode (e.g. fp8 for DiT/Flux/Wan, 4bit-NF4 for VLMs).",
                    },
                ),
                "attention": (
                    ["sdpa", "flash_attention_2", "eager"],
                    {
                        "default": "sdpa",
                        "tooltip": "Attention kernel (sdpa for standard PyTorch, flash_attention_2 for RTX 3000/4000).",
                    },
                ),
            },
            "optional": {
                "flow_shift_preset": (
                    SAMPLING_PRESETS,
                    {
                        "default": "None (Standard / SD1.5 / SDXL / Krea 2)",
                        "tooltip": "Flow-matching sampling preset (e.g. Z-Image Turbo, Qwen, Flux, SD3). Applies when loading a diffusion model.",
                    },
                ),
                "custom_shift": (
                    "FLOAT",
                    {
                        "default": 3.0,
                        "min": 0.0,
                        "max": 100.0,
                        "step": 0.01,
                        "tooltip": "Custom shift if flow_shift_preset is set to Custom.",
                    },
                ),
                "custom_path": (
                    "STRING",
                    {
                        "default": "",
                        "placeholder": "Active for [Special] Custom Model or API Endpoint (e.g. http://127.0.0.1:42030/v1#qwen2.5-vl:7b)",
                        "tooltip": "Absolute folder path on disk or remote API endpoint URL.",
                    },
                ),
                "keep_in_vram": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Keep model resident in VRAM for zero-latency subsequent inferences. If False (Low VRAM Mode), unloads the model immediately after generation to give 100% GPU memory to diffusion models.",
                    },
                ),
                "model_stack": (
                    "STRING",
                    {
                        "default": "[]",
                        "multiline": False,
                        "tooltip": "Managed by the canvas UI (hidden). JSON list of models with on/off toggles.",
                    },
                ),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("model",)
    FUNCTION = "load_universal"
    CATEGORY = "STOIQO"

    def load_universal(
        self,
        model_name,
        clip_type="auto",
        precision="default",
        attention="sdpa",
        flow_shift_preset="None (Standard / SD1.5 / SDXL / Krea 2)",
        custom_shift=3.0,
        custom_path="",
        keep_in_vram=True,
        model_stack="[]",
        unique_id=None,
        prompt=None,
        extra_pnginfo=None,
        **kwargs,
    ):
        with NodeTelemetryTimer(node_id=unique_id, node_name="UniversalModelLoader") as timer:
            stack_entries = parse_model_stack(model_stack)
            active_models = [m for m in stack_entries if m.get("enabled", True)]

            # If there are active models in the stack, use the first active model
            if active_models:
                target_m = active_models[0]
                eff_model_name = target_m.get("name", model_name)
                eff_precision = target_m.get("precision", precision)
                eff_attention = target_m.get("attention", attention)
                eff_clip_type = target_m.get("clip_type", clip_type)
                eff_shift_preset = target_m.get("flow_shift_preset", flow_shift_preset)
                eff_custom_shift = target_m.get("custom_shift", custom_shift)
                custom_path = target_m.get("custom_path") or custom_path
                logger.info(f"[Universal Model Loader] Using active stack model: '{eff_model_name}' (precision={eff_precision})")
            else:
                eff_model_name = model_name
                eff_precision = precision
                eff_attention = attention
                eff_clip_type = clip_type
                eff_shift_preset = flow_shift_preset
                eff_custom_shift = custom_shift

            return self.engine.load(
                model_choice=eff_model_name,
                clip_type=eff_clip_type,
                precision=eff_precision,
                attention=eff_attention,
                flow_shift_preset=eff_shift_preset,
                custom_shift=eff_custom_shift,
                custom_path=custom_path,
                keep_in_vram=keep_in_vram,
                **kwargs,
            )

