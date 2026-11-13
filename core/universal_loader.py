"""
[STOIQO] Universal Model Loader Engine
Unified loader engine that detects, categorizes, and loads ANY model in ComfyUI:
- Diffusion Models (UNET / DiT / GGUF) -> MODEL
- Text Encoders / CLIP -> CLIP
- Variational AutoEncoders -> VAE
- Full Checkpoints -> MODEL + CLIP + VAE
- Vision-Language Models (VLM / LLM) -> STOIQO_MODEL + CLIP
"""

import os
import sys
import torch

try:
    import folder_paths
except ImportError:
    folder_paths = None

try:
    import comfy.sd
    import comfy.utils
    import comfy.model_management
    import comfy.model_sampling
except ImportError:
    comfy = None

from .config import (
    scan_local_vlm_models,
    MODEL_PRESETS,
    CUSTOM_MODEL_KEY,
    API_ENDPOINT_KEY,
)

try:
    from .model_manager import ModelManager
except Exception:
    ModelManager = None


MODEL_TYPE_OVERRIDE_OPTIONS = [
    "Auto-Detect",
    "MODEL (Diffusion / UNET / DiT)",
    "CLIP (Text Encoder)",
    "VAE (Variational AutoEncoder)",
    "VLM (Vision-Language / Reasoning)",
    "CHECKPOINT (All-in-One)",
]

SAMPLING_PRESETS = [
    "None (Standard / SD1.5 / SDXL / Krea 2)",
    "Z-Image Turbo (Shift: 3.0)",
    "Ace-Step 1.5 Audio (Shift: 3.0)",
    "Qwen-Image (Shift: 3.1)",
    "FLUX.1 Schnell / Dev (Auto-Shift 1.15)",
    "SD3 / SD3.5 (Shift: 3.0, Multi: 1000)",
    "AuraFlow (Shift: 1.73)",
    "Hunyuan 3D (Shift: 1.0)",
    "MiniMax H3 (Video: 12.0 / Audio: 3.0)",
    "Custom (Override manuale)",
]


def apply_flow_shift(model, preset: str, custom_shift: float = 3.0):
    """
    Applies flow-matching sampling shift schedules directly to a diffusion model.
    Supports FLUX.1, MiniMax H3, SD3/SD3.5, Z-Image Turbo, Ace-Step, Qwen-Image, and Custom shifts.
    """
    if not preset or preset.startswith("None"):
        return model

    if comfy is None or not hasattr(model, "clone"):
        if isinstance(model, dict):
            model["flow_shift_preset"] = preset
            model["custom_shift"] = custom_shift
        return model

    m = model.clone()
    try:
        if preset.startswith("FLUX.1"):
            sampling_base = comfy.model_sampling.ModelSamplingFlux
            sampling_type = comfy.model_sampling.CONST
            class ModelSamplingAdvancedFlux(sampling_base, sampling_type):
                pass
            model_sampling = ModelSamplingAdvancedFlux(model.model.model_config)
            model_sampling.set_parameters(shift=1.15)
            m.add_object_patch("model_sampling", model_sampling)
            return m

        elif preset.startswith("MiniMax H3"):
            if hasattr(comfy.model_sampling, "ModelSamplingAV"):
                class ModelSamplingAdvancedMiniMax(comfy.model_sampling.ModelSamplingAV, comfy.model_sampling.CONST):
                    pass
                original = m.get_model_object("model_sampling")
                model_sampling = ModelSamplingAdvancedMiniMax(model.model.model_config)
                model_sampling.set_parameters(shift=12.0, audio_shift=3.0)
                if hasattr(original, "noise_scale"):
                    model_sampling.set_noise_scale(original.noise_scale)
                m.add_object_patch("model_sampling", model_sampling)
                to = m.model_options["transformer_options"] = m.model_options.get("transformer_options", {}).copy()
                to["minimax_h3_sigma_shift_video"] = 12.0
                to["minimax_h3_sigma_shift_audio"] = 3.0
                return m

        # Discrete Flow Family
        shift = 3.0
        multiplier = 1.0

        if preset.startswith("Z-Image Turbo"):
            shift = 3.0
            multiplier = 1.0
        elif preset.startswith("Ace-Step"):
            shift = 3.0
            multiplier = 1.0
        elif preset.startswith("Qwen-Image"):
            shift = 3.1
            multiplier = 1.0
        elif preset.startswith("SD3"):
            shift = 3.0
            multiplier = 1000.0
        elif preset.startswith("AuraFlow"):
            shift = 1.73
            multiplier = 1.0
        elif preset.startswith("Hunyuan 3D"):
            shift = 1.0
            multiplier = 1.0
        elif preset.startswith("Custom"):
            shift = float(custom_shift)
            multiplier = 1.0

        sampling_base = comfy.model_sampling.ModelSamplingDiscreteFlow
        sampling_type = comfy.model_sampling.CONST
        class ModelSamplingAdvancedDiscrete(sampling_base, sampling_type):
            pass

        original = m.get_model_object("model_sampling")
        model_sampling = ModelSamplingAdvancedDiscrete(model.model.model_config)
        model_sampling.set_parameters(shift=shift, multiplier=multiplier)
        if hasattr(original, "noise_scale"):
            model_sampling.set_noise_scale(original.noise_scale)
        m.add_object_patch("model_sampling", model_sampling)
        return m
    except Exception as e:
        print(f"[STOIQO Flow Shift] Warning applying sampling preset '{preset}': {e}")
        return model


def scan_all_system_models():
    """
    Scans ComfyUI model directories and categorizes every available model.
    Returns:
        dict: {
            "diffusion_models": [names],
            "checkpoints": [names],
            "text_encoders": [names],
            "vae": [names],
            "vlm": {label: path},
        }
    """
    diff_models = []
    ckpts = []
    clips = []
    vaes = []

    if folder_paths is not None and hasattr(folder_paths, "get_filename_list"):
        try:
            diff_models = folder_paths.get_filename_list("diffusion_models") or []
        except Exception:
            pass
        try:
            ckpts = folder_paths.get_filename_list("checkpoints") or []
        except Exception:
            pass
        try:
            clips = folder_paths.get_filename_list("text_encoders") or []
        except Exception:
            pass
        try:
            vaes = folder_paths.get_filename_list("vae") or []
        except Exception:
            pass

    vlms = scan_local_vlm_models()

    return {
        "diffusion_models": sorted(diff_models),
        "checkpoints": sorted(ckpts),
        "text_encoders": sorted(clips),
        "vae": sorted(vaes),
        "vlm": vlms,
    }


def get_universal_model_choices():
    """
    Builds a unified, human-readable list of choices for dropdowns.
    Prefixed with tags like [DiT/UNET], [CLIP], [VAE], [Checkpoint], [VLM].
    """
    all_models = scan_all_system_models()
    choices = []

    # 1. Diffusion Models (DiT / UNET)
    for m in all_models["diffusion_models"]:
        choices.append(f"[DiT/UNET] {m}")

    # 2. Text Encoders & CLIPs
    for c in all_models["text_encoders"]:
        choices.append(f"[CLIP] {c}")

    # 3. VAEs
    for v in all_models["vae"]:
        choices.append(f"[VAE] {v}")

    # 4. Full Checkpoints
    for ck in all_models["checkpoints"]:
        choices.append(f"[Checkpoint] {ck}")

    # 5. Local VLMs
    for label in all_models["vlm"].keys():
        clean_lbl = label.replace("📁 [Local] ", "").replace(" (HF Cache)", "")
        choices.append(f"[VLM] {clean_lbl}")

    # 6. Curated VLM Presets
    for preset_label in MODEL_PRESETS.keys():
        choices.append(f"[VLM Preset] {preset_label}")

    # 7. Fallback & Special endpoints
    choices.append(f"[Special] {CUSTOM_MODEL_KEY}")
    choices.append(f"[Special] {API_ENDPOINT_KEY}")

    if not choices:
        choices = ["none"]

    return choices


def detect_model_kind(choice_str, file_path=""):
    """
    Detects the architectural role of a model based on label prefix,
    parent directory, or file extension/header.
    Returns: 'MODEL' | 'CLIP' | 'VAE' | 'CHECKPOINT' | 'VLM'
    """
    s = (choice_str or "").strip()
    low = s.lower()

    if s.startswith("[DiT/UNET]"):
        return "MODEL"
    if s.startswith("[CLIP]"):
        return "CLIP"
    if s.startswith("[VAE]"):
        return "VAE"
    if s.startswith("[Checkpoint]"):
        return "CHECKPOINT"
    if s.startswith("[VLM"):
        return "VLM"

    # Secondary inspection based on path / name
    if "vae" in low and not ("qwen" in low or "vit" in low):
        return "VAE"
    if any(k in low for k in ("text_encoder", "clip", "t5", "bert")):
        return "CLIP"
    if any(k in low for k in ("diffusion", "unet", "dit", "flux", "acestep", "wan", "mochi", "ltxv")):
        return "MODEL"
    if any(k in low for k in ("qwen3", "qwen2", "qwen-vl", "florence", "minicpm", "internvl")):
        return "VLM"
    if any(k in low for k in ("checkpoint", "ckpt")):
        return "CHECKPOINT"

    return "MODEL"


def resolve_raw_filename_or_repo(choice_str):
    """
    Strips dropdown prefixes to get the raw filename or repo id.
    """
    raw = choice_str
    for prefix in (
        "[DiT/UNET] ",
        "[CLIP] ",
        "[VAE] ",
        "[Checkpoint] ",
        "[VLM] ",
        "[VLM Preset] ",
        "[Special] ",
    ):
        if raw.startswith(prefix):
            raw = raw[len(prefix):]
            break
    return raw.strip()


def resolve_clip_type(clip_type_str: str, filename: str):
    """
    Intelligently resolves the required comfy.sd.CLIPType enum value (or type string).
    If clip_type_str is 'auto', inspects the filename pattern.
    """
    c_name = None
    if clip_type_str and clip_type_str != "auto":
        c_name = clip_type_str.upper()
    else:
        low = filename.lower()
        # 1. Krea2 (Qwen3-VL-4B is specifically used as text encoder for Krea2 in ComfyUI)
        if any(k in low for k in ("krea", "qwen3vl4b", "qwen3_vl_4b", "qwen3-vl-4b", "fineporn")):
            c_name = "KREA2"
        elif any(k in low for k in ("wan", "umt5")):
            c_name = "WAN"
        elif any(k in low for k in ("qwen_image", "qwenimage", "qwen3vl8b", "qwen3_vl_8b", "qwen3-vl-8b")):
            c_name = "QWEN_IMAGE"
        elif "ace" in low:
            c_name = "ACE"
        elif "flux" in low:
            c_name = "FLUX"
        elif "sd3" in low:
            c_name = "SD3"
        elif "mochi" in low:
            c_name = "MOCHI"
        elif "ltxv" in low:
            c_name = "LTXV"
        elif "lumina" in low:
            c_name = "LUMINA2"
        elif "minimax" in low:
            c_name = "MINIMAX"
        elif "hunyuan_video" in low:
            c_name = "HUNYUAN_VIDEO"
        elif "hunyuan" in low:
            c_name = "HUNYUAN_IMAGE"
        elif "ideogram" in low:
            c_name = "IDEOGRAM4"
        elif "boogu" in low:
            c_name = "BOOGU"
        elif "joyimage" in low:
            c_name = "JOYIMAGE"
        else:
            c_name = "STABLE_DIFFUSION"

    if comfy is not None and hasattr(comfy, "sd") and hasattr(comfy.sd, "CLIPType"):
        return getattr(comfy.sd.CLIPType, c_name, comfy.sd.CLIPType.STABLE_DIFFUSION)

    return c_name



class UniversalModelEngine:
    """
    Unified loader engine responsible for loading any model on demand:
    DiT, UNET, CLIP, VAE, Checkpoint, or VLM.
    Automatically handles architecture detection, offloading, precision, and attention.
    """

    def __init__(self):
        self.vlm_manager = ModelManager()

    def load(
        self,
        model_choice: str,
        precision: str = "default",
        attention: str = "sdpa",
        clip_type: str = "auto",
        custom_path: str = "",
        keep_in_vram: bool = True,
        **kwargs,
    ):
        """
        Loads the selected model and returns a single polymorphic output (loaded_obj,).
        Connectable to any downstream ComfyUI socket (MODEL, CLIP, VAE, STOIQO_MODEL).
        """
        # Support alias keywords for compatibility
        weight_dtype = kwargs.get("weight_dtype", precision)
        attn_mode = kwargs.get("vlm_attention", attention)
        clip_recipe = kwargs.get("clip_type", clip_type)
        type_override = kwargs.get("type_override", "Auto-Detect")
        custom_p = custom_path or kwargs.get("custom_path", "")
        keep_vram = kwargs.get("keep_in_vram", keep_in_vram)

        raw_name = resolve_raw_filename_or_repo(model_choice)
        if (raw_name in (CUSTOM_MODEL_KEY, API_ENDPOINT_KEY) or not raw_name) and custom_p and custom_p.strip():
            raw_name = custom_p.strip()

        # Determine target kind
        if type_override != "Auto-Detect":
            if "MODEL" in type_override:
                kind = "MODEL"
            elif "CLIP" in type_override:
                kind = "CLIP"
            elif "VAE" in type_override:
                kind = "VAE"
            elif "VLM" in type_override:
                kind = "VLM"
            elif "CHECKPOINT" in type_override:
                kind = "CHECKPOINT"
            else:
                kind = detect_model_kind(model_choice, raw_name)
        else:
            kind = detect_model_kind(model_choice, raw_name)

        loaded_obj = None
        print(f"[STOIQO Universal Loader] Target: '{raw_name}' detected as {kind} (clip_type: {clip_recipe}, precision: {weight_dtype}, attention: {attn_mode}, keep_in_vram: {keep_vram})")

        # ── 1. VAE LOADING ────────────────────────────────────────────────────
        if kind == "VAE":
            if folder_paths is not None and hasattr(folder_paths, "get_full_path_or_raise"):
                try:
                    import nodes as comfy_nodes
                    loaded_obj = comfy_nodes.VAELoader().load_vae(raw_name)[0]
                except Exception:
                    try:
                        vae_path = folder_paths.get_full_path_or_raise("vae", raw_name)
                        sd = comfy.utils.load_torch_file(vae_path)
                        loaded_obj = comfy.sd.VAE(sd=sd)
                    except Exception as err:
                        print(f"[STOIQO Universal Loader] VAE loading failed: {err}")
            if loaded_obj is None:
                loaded_obj = {"name": raw_name, "kind": "VAE"}

        # ── 2. CLIP / TEXT ENCODER LOADING ────────────────────────────────────
        elif kind == "CLIP":
            c_type = resolve_clip_type(clip_recipe, raw_name) if comfy else None
            clip_options = {}

            if folder_paths is not None:
                try:
                    clip_path = folder_paths.get_full_path_or_raise("text_encoders", raw_name)
                except Exception:
                    try:
                        clip_path = folder_paths.get_full_path_or_raise("clip", raw_name)
                    except Exception:
                        clip_path = raw_name

                emb_dirs = folder_paths.get_folder_paths("embeddings") if hasattr(folder_paths, "get_folder_paths") else []
                if comfy is not None:
                    try:
                        print(f"[STOIQO Universal Loader] Loading CLIP '{raw_name}' with recipe {c_type}...")
                        loaded_obj = comfy.sd.load_clip(
                            ckpt_paths=[clip_path],
                            embedding_directory=emb_dirs,
                            clip_type=c_type,
                            model_options=clip_options,
                        )
                    except Exception as clip_err:
                        print(f"[STOIQO Universal Loader] Comfy CLIP loading error: {clip_err}")

            if loaded_obj is None and "qwen" in raw_name.lower():
                try:
                    self.vlm_manager.load_model(raw_name, quantization="4bit - NF4", keep_in_vram=keep_vram)
                    loaded_obj = self.vlm_manager
                except Exception:
                    pass

            if loaded_obj is None:
                loaded_obj = {"name": raw_name, "kind": "CLIP", "clip_type": str(c_type)}

        # ── 3. DIFFUSION MODEL (UNET / DiT) LOADING ───────────────────────────
        elif kind == "MODEL":
            model_options = {}
            if weight_dtype == "fp8_e4m3fn":
                model_options["dtype"] = torch.float8_e4m3fn
            elif weight_dtype == "fp8_e4m3fn_fast":
                model_options["dtype"] = torch.float8_e4m3fn
                model_options["fp8_optimizations"] = True
            elif weight_dtype == "fp8_e5m2":
                model_options["dtype"] = torch.float8_e5m2
            elif weight_dtype == "fp16":
                model_options["dtype"] = torch.float16
            elif weight_dtype == "bf16":
                model_options["dtype"] = torch.bfloat16

            if folder_paths is not None and comfy is not None:
                try:
                    unet_path = folder_paths.get_full_path_or_raise("diffusion_models", raw_name)
                    loaded_obj = comfy.sd.load_diffusion_model(unet_path, model_options=model_options)
                except Exception as unet_err:
                    print(f"[STOIQO Universal Loader] Diffusion model load failed: {unet_err}")

            flow_shift = kwargs.get("flow_shift_preset", "None (Standard / SD1.5 / SDXL / Krea 2)")
            c_shift = kwargs.get("custom_shift", 3.0)
            if loaded_obj is None:
                # Fallback dictionary for testing / headless execution
                loaded_obj = {"name": raw_name, "kind": "MODEL", "dtype": weight_dtype}
            loaded_obj = apply_flow_shift(loaded_obj, flow_shift, c_shift)

        # ── 4. FULL CHECKPOINT (UNET + CLIP + VAE) ───────────────────────────
        elif kind == "CHECKPOINT":
            if folder_paths is not None and comfy is not None:
                try:
                    ckpt_path = folder_paths.get_full_path_or_raise("checkpoints", raw_name)
                    emb_dirs = folder_paths.get_folder_paths("embeddings") if hasattr(folder_paths, "get_folder_paths") else []
                    ckpt_res = comfy.sd.load_checkpoint_guess_config(
                        ckpt_path,
                        output_vae=True,
                        output_clip=True,
                        embedding_directory=emb_dirs,
                    )
                    loaded_obj = ckpt_res[0]  # Primary MODEL
                except Exception as ckpt_err:
                    print(f"[STOIQO Universal Loader] Checkpoint load failed: {ckpt_err}")

            flow_shift = kwargs.get("flow_shift_preset", "None (Standard / SD1.5 / SDXL / Krea 2)")
            c_shift = kwargs.get("custom_shift", 3.0)
            if loaded_obj is None:
                loaded_obj = {"name": raw_name, "kind": "CHECKPOINT"}
            loaded_obj = apply_flow_shift(loaded_obj, flow_shift, c_shift)

        # ── 5. VLM (VISION-LANGUAGE MODEL) LOADING ────────────────────────────
        elif kind == "VLM":
            quant_map = {
                "4bit - NF4": "4bit - NF4",
                "8bit": "8bit",
                "default": "4bit - NF4",
            }
            quant = quant_map.get(weight_dtype, "4bit - NF4")
            resolved_repo = self.vlm_manager.resolve_model_repo(raw_name, custom_p)
            self.vlm_manager.load_model(
                resolved_repo,
                quantization=quant,
                attention_mode=attn_mode,
                keep_in_vram=keep_vram,
            )
            loaded_obj = self.vlm_manager

        return (loaded_obj,)

