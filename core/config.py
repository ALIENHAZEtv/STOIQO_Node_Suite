"""
[STOIQO] Prompt Generator Engine — Configuration & Options
Hardware presets, attention modes, quantization options, and batch types.
"""

import os

try:
    import folder_paths
except ImportError:
    folder_paths = None

DEFAULT_MODEL_REPO = "Qwen/Qwen2.5-VL-7B-Instruct"

# ── MODEL PRESETS ──────────────────────────────────────────────────────────
# Tiered VRAM presets, dynamically quantized to 4-bit NF4 / 8-bit or loaded in 16-bit.
MODEL_PRESETS = {
    # ── Qwen3-VL & Qwen2.5-VL Series ─────────────────────────────────────────
    "Qwen3-VL-4B-Instruct (4bit, ~3.0 GB active)": "Qwen/Qwen3-VL-4B-Instruct",
    "Qwen3-VL-8B-Instruct (4bit, ~5.5 GB active)": "Qwen/Qwen3-VL-8B-Instruct",
    "Qwen2.5-VL-7B-Instruct (4bit, ~5.0 GB active)": "Qwen/Qwen2.5-VL-7B-Instruct",
    "Qwen2.5-VL-3B-Instruct (4bit, ~2.5 GB active)": "Qwen/Qwen2.5-VL-3B-Instruct",
    "Qwen2.5-VL-32B-Instruct (4bit, ~20 GB active)": "Qwen/Qwen2.5-VL-32B-Instruct",
    "Qwen2.5-VL-72B-Instruct (4bit, ~45 GB active)": "Qwen/Qwen2.5-VL-72B-Instruct",
    # ── Specialized & Multi-Family VLM Architectures ─────────────────────────
    "Florence-2-Large (Vision Expert, ~1.5 GB active)": "microsoft/Florence-2-large",
    "Florence-2-Base (Vision Expert, ~0.6 GB active)": "microsoft/Florence-2-base",
    "MiniCPM-V-2_6 (8B Multimodal, ~5.5 GB active)": "openbmb/MiniCPM-V-2_6",
    "InternVL2_5-8B (Multimodal, ~5.5 GB active)": "OpenGVLab/InternVL2_5-8B",
    # ── Legacy Aliases for Workflow Compatibility ────────────────────────────
    "<= 8 GB VRAM  -  Qwen2.5-VL-3B  (4bit, ~2.5 GB active)": "Qwen/Qwen2.5-VL-3B-Instruct",
    "<= 8 GB VRAM  -  Qwen3-VL-4B    (4bit, ~3.0 GB active)": "Qwen/Qwen3-VL-4B-Instruct",
    "12-16 GB VRAM  -  Qwen2.5-VL-7B  (4bit, ~5 GB active)": "Qwen/Qwen2.5-VL-7B-Instruct",
    "12-16 GB VRAM  -  Qwen3-VL-8B    (4bit, ~5.5 GB active)": "Qwen/Qwen3-VL-8B-Instruct",
    "24 GB VRAM  -  Qwen2.5-VL-32B  (4bit, ~20 GB active)": "Qwen/Qwen2.5-VL-32B-Instruct",
    "48+ GB VRAM  -  Qwen2.5-VL-72B  (4bit, ~45 GB active)": "Qwen/Qwen2.5-VL-72B-Instruct",
}

MODEL_MODES = [
    "Preset (Auto-Download)",
    "Local Folder (already on disk)",
]

CUSTOM_MODEL_KEY = "📁 Custom Model (Local Disk Path)"
API_ENDPOINT_KEY = "🌐 API Endpoint (Ollama / OpenAI / vLLM - 0 GB VRAM)"

# Discovered local models registry: label -> full_path
DISCOVERED_LOCAL_MODELS = {}


def scan_local_vlm_models():
    """
    Scans standard ComfyUI directories (LLM, text_encoders, clip) and local HF hub cache
    for Vision-Language Models already present on disk.
    Strictly follows ComfyUI conventions without hardcoding any proprietary workspace paths.
    """
    discovered = {}
    search_dirs = []

    # 1. ComfyUI directory discovery (via folder_paths or upward traversal)
    comfy_candidates = []
    if folder_paths and hasattr(folder_paths, "__file__"):
        comfy_candidates.append(os.path.dirname(os.path.abspath(folder_paths.__file__)))

    curr = os.path.abspath(os.path.dirname(__file__))
    for _ in range(8):
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
        for cand in [
            os.path.join(curr, "engines", "comfyui", "ComfyUI"),
            os.path.join(curr, "ComfyUI"),
        ]:
            if os.path.isdir(cand) and cand not in comfy_candidates:
                comfy_candidates.append(cand)

    # 2. Ensure folder_paths has LLM registered
    if folder_paths is not None:
        try:
            if hasattr(folder_paths, "models_dir") and hasattr(folder_paths, "add_model_folder_path"):
                if not hasattr(folder_paths, "get_folder_paths") or not folder_paths.get_folder_paths("LLM"):
                    default_llm = os.path.join(folder_paths.models_dir, "LLM")
                    os.makedirs(default_llm, exist_ok=True)
                    folder_paths.add_model_folder_path("LLM", default_llm)
        except Exception:
            pass

        # Collect LLM directories from folder_paths
        if hasattr(folder_paths, "get_folder_paths"):
            try:
                for p in folder_paths.get_folder_paths("LLM"):
                    if p and os.path.isdir(p) and p not in search_dirs:
                        search_dirs.append(os.path.normpath(p))
            except Exception:
                pass

        if hasattr(folder_paths, "models_dir") and folder_paths.models_dir:
            fallback_llm = os.path.join(folder_paths.models_dir, "LLM")
            if os.path.isdir(fallback_llm) and fallback_llm not in search_dirs:
                search_dirs.append(os.path.normpath(fallback_llm))

    # 3. Parse extra_model_paths.yaml from discovered ComfyUI roots
    for c_root in comfy_candidates:
        for yml_name in ["extra_model_paths.yaml", "extra_model_paths.yml"]:
            yml_path = os.path.join(c_root, yml_name)
            if os.path.isfile(yml_path):
                try:
                    import yaml
                    with open(yml_path, "r", encoding="utf-8") as f:
                        cfg = yaml.safe_load(f)
                    if isinstance(cfg, dict):
                        for entry in cfg.values():
                            if isinstance(entry, dict):
                                base = entry.get("base_path", "")
                                for key in ("LLM", "text_encoders", "clip"):
                                    if key in entry:
                                        sub = str(entry[key]).strip()
                                        for s_line in sub.splitlines():
                                            s_line = s_line.strip()
                                            if not s_line:
                                                continue
                                            cand = os.path.join(base, s_line) if base else s_line
                                            if cand and os.path.isdir(cand) and cand not in search_dirs:
                                                search_dirs.append(os.path.normpath(cand))
                except Exception:
                    pass

    # 4. Environment overrides & standard Hugging Face hub cache
    custom_models_dir = os.environ.get("STOIQO_MODELS_DIR")
    if custom_models_dir and os.path.isdir(custom_models_dir) and custom_models_dir not in search_dirs:
        search_dirs.append(os.path.normpath(custom_models_dir))

    hf_home = os.environ.get("HF_HOME")
    if hf_home and os.path.isdir(os.path.join(hf_home, "hub")):
        search_dirs.append(os.path.normpath(os.path.join(hf_home, "hub")))
    elif os.path.isdir(os.path.expanduser("~/.cache/huggingface/hub")):
        search_dirs.append(os.path.normpath(os.path.expanduser("~/.cache/huggingface/hub")))

    # 5. Scan candidate directories for models (folders, HF cache, safetensors)
    for base_dir in search_dirs:
        if not os.path.isdir(base_dir):
            continue
        try:
            for item in os.listdir(base_dir):
                full_item = os.path.join(base_dir, item)

                # Case A: Hugging Face hub cache snapshot (models--<org>--<repo>/snapshots/<hash>)
                if item.startswith("models--") and os.path.isdir(full_item):
                    snap_dir = os.path.join(full_item, "snapshots")
                    if os.path.isdir(snap_dir):
                        try:
                            snaps = sorted(
                                [os.path.join(snap_dir, s) for s in os.listdir(snap_dir)],
                                key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0,
                                reverse=True,
                            )
                        except Exception:
                            snaps = [os.path.join(snap_dir, s) for s in os.listdir(snap_dir)]
                        for snap_path in snaps:
                            cfg_path = os.path.join(snap_path, "config.json")
                            if os.path.isfile(cfg_path):
                                repo_clean = item.replace("models--", "").replace("--", "/")
                                label = f"📁 [Local] {repo_clean} (HF Cache)"
                                if label not in discovered:
                                    discovered[label] = snap_path
                                break

                # Case B: Direct model directory containing config.json
                elif os.path.isdir(full_item):
                    cfg_path = os.path.join(full_item, "config.json")
                    if os.path.isfile(cfg_path):
                        dir_category = os.path.basename(base_dir)
                        label = f"📁 [Local] {item} ({dir_category})"
                        if label not in discovered:
                            discovered[label] = full_item

                # Case C: Standalone safetensors (Qwen, VLM, Florence, MiniCPM)
                elif full_item.endswith(".safetensors") and os.path.isfile(full_item):
                    fl = item.lower()
                    if any(k in fl for k in ("qwen3", "qwen2", "qwen", "florence", "minicpm", "internvl", "vlm")):
                        dir_category = os.path.basename(base_dir)
                        label = f"📁 [Local] {item} ({dir_category})"
                        if label not in discovered:
                            discovered[label] = full_item
        except Exception:
            continue

    # 6. Also check ComfyUI folder_paths if available
    if folder_paths is not None:
        for folder_type in ("text_encoders", "clip", "LLM"):
            try:
                fn_list = folder_paths.get_filename_list(folder_type) if hasattr(folder_paths, "get_filename_list") else []
                for fname in fn_list:
                    fl = fname.lower()
                    if any(k in fl for k in ("qwen3", "qwen2", "qwen", "florence", "minicpm", "internvl", "vlm")):
                        full_p = folder_paths.get_full_path(folder_type, fname) if hasattr(folder_paths, "get_full_path") else fname
                        label = f"📁 [Local] {fname} ({folder_type})"
                        if label not in discovered:
                            discovered[label] = full_p
            except Exception:
                pass

    return discovered


def get_vlm_model_choices():
    """
    Dynamically compiles VLM model choices for ComfyUI dropdown menus.
    Priority order:
    1. Local models found in workspace/disk (Qwen3-VL first, then other local VLMs)
    2. Curated online presets (Qwen3-VL, Qwen2.5-VL, Florence-2, MiniCPM-V, InternVL)
    3. External connections (API Endpoint & Custom local folder path)
    4. Legacy alias keys for backwards compatibility with saved workflows
    """
    global DISCOVERED_LOCAL_MODELS
    DISCOVERED_LOCAL_MODELS = scan_local_vlm_models()

    local_qwen3 = []
    local_others = []
    for label in DISCOVERED_LOCAL_MODELS.keys():
        ll = label.lower()
        if "qwen3" in ll or "qwen-3" in ll:
            local_qwen3.append(label)
        else:
            local_others.append(label)

    # Sort each local group alphabetically
    local_qwen3.sort()
    local_others.sort()

    # Online presets (clean keys first: Qwen3-VL prioritized before other local/online VLMs)
    legacy_keys = [
        k for k in MODEL_PRESETS.keys()
        if k.startswith("<=") or k.startswith("12-16") or k.startswith("24") or k.startswith("48")
    ]
    legacy_set = set(legacy_keys)
    preset_keys = [k for k in MODEL_PRESETS.keys() if k not in legacy_set]
    qwen3_presets = [k for k in preset_keys if "qwen3" in k.lower() or "qwen-3" in k.lower()]
    other_presets = [k for k in preset_keys if k not in qwen3_presets]

    choices = (
        local_qwen3
        + qwen3_presets
        + local_others
        + other_presets
        + [API_ENDPOINT_KEY, CUSTOM_MODEL_KEY]
        + legacy_keys
    )

    # Deduplicate while strictly preserving order
    seen = set()
    deduped = []
    for c in choices:
        if c not in seen:
            seen.add(c)
            deduped.append(c)

    return deduped


# Evaluated at module load, refreshed dynamically per node instantiation
MODEL_SELECTION_CHOICES = get_vlm_model_choices()

# Legacy alias
MODEL_CHOICES = list(MODEL_PRESETS.keys())

QUANTIZATION_OPTIONS = [
    "4bit - NF4 (Recommended - Low VRAM)",
    "8bit",
    "none (fp16 / bf16 - High VRAM)",
]

ATTENTION_OPTIONS = [
    "sdpa (PyTorch Native - Recommended)",
    "flash_attention_2 (Fastest - RTX 3000+)",
    "eager (Fallback - Slowest)",
]

BATCH_MODES = [
    "Independent Images",
    "Multi-Image Comparison / Fusion",
]

SYSTEM_PROMPT_MODES = [
    "Preset Default (Recommended)",
    "Append Custom to Preset",
    "Custom Only (Manual Override)",
]
