"""
[STOIQO] Prompt Generator Engine — Configuration & Options
Hardware presets, attention modes, quantization options, and batch types.
"""

DEFAULT_MODEL_REPO = "Qwen/Qwen2.5-VL-7B-Instruct"

# ── MODEL PRESETS ──────────────────────────────────────────────────────────
# Tiered VRAM presets, dynamically quantized to 4-bit NF4 / 8-bit or loaded in 16-bit.
MODEL_PRESETS = {
    "<= 8 GB VRAM  -  Qwen2.5-VL-3B  (4bit, ~2.5 GB active)": "Qwen/Qwen2.5-VL-3B-Instruct",
    "12-16 GB VRAM  -  Qwen2.5-VL-7B  (4bit, ~5 GB active)": "Qwen/Qwen2.5-VL-7B-Instruct",
    "24 GB VRAM  -  Qwen2.5-VL-32B  (4bit, ~20 GB active)": "Qwen/Qwen2.5-VL-32B-Instruct",
    "48+ GB VRAM  -  Qwen2.5-VL-72B  (4bit, ~45 GB active)": "Qwen/Qwen2.5-VL-72B-Instruct",
}

MODEL_MODES = [
    "Preset (Auto-Download)",
    "Local Folder (already on disk)",
]

CUSTOM_MODEL_KEY = "📁 Custom Model (Local Disk Path)"
API_ENDPOINT_KEY = "🌐 API Endpoint (Ollama / OpenAI / vLLM - 0 GB VRAM)"

# Unified choices: Presets + Custom Model + API Endpoint
MODEL_SELECTION_CHOICES = list(MODEL_PRESETS.keys()) + [CUSTOM_MODEL_KEY, API_ENDPOINT_KEY]

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
