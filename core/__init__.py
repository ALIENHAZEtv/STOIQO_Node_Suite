"""
[STOIQO] Prompt Generator Engine — Core Package
"""

from .config import (
    DEFAULT_MODEL_REPO,
    MODEL_PRESETS,
    CUSTOM_MODEL_KEY,
    MODEL_SELECTION_CHOICES,
    MODEL_MODES,
    MODEL_CHOICES,
    QUANTIZATION_OPTIONS,
    ATTENTION_OPTIONS,
    BATCH_MODES,
    SYSTEM_PROMPT_MODES,
)
from .image import (
    SYSTEM_PROMPT_PRESETS,
    CUSTOM_SYSTEM_PROMPT_KEY,
    SYSTEM_PROMPT_CHOICES,
    TEXT_EXPANSION_SYSTEM_PROMPT,
    MULTI_IMAGE_SYSTEM_PROMPT,
    BASE_TEXT_EXPANSION_PROMPT,
    BASE_MULTI_IMAGE_PROMPT,
    LEGACY_SYSTEM_PROMPT_ALIASES,
    resolve_system_prompt,
    PROMPT_TYPES,
    PROMPT_TYPE_DIRECTIVES,
    resolve_prompt_type,
    CAPTION_STYLES,
    STYLE_PROMPTS,
    ARTISTIC_STYLES,
    ARTISTIC_STYLE_DIRECTIVES,
    resolve_artistic_style,
)
from .music import (
    GENRE_PRESETS,
    VOCAL_PRESETS,
    LANGUAGE_PRESETS,
    SONG_STRUCTURES,
    TEMPO_PRESETS,
    YUE2_SYSTEM_PROMPT,
    MUSIC_SYSTEM_PROMPT_PRESETS,
    MUSIC_CUSTOM_SYSTEM_PROMPT_KEY,
    MUSIC_SYSTEM_PROMPT_CHOICES,
    resolve_music_system_prompt,
    build_music_task_prompt,
    parse_music_response,
    clean_user_custom_lyrics,
    clean_user_custom_directives,
)

KREA2_PROMPT_IMAGE = SYSTEM_PROMPT_PRESETS["Generative Prompt"]
KREA2_PROMPT_TEXT = BASE_TEXT_EXPANSION_PROMPT
KREA2_PROMPT_MULTI_IMAGE = BASE_MULTI_IMAGE_PROMPT
from .vision import (
    process_vision_info,
    tensor_to_pil,
)
from .text_processing import (
    clean_llm_output,
    build_task_prompt,
    parse_dual_prompt,
    parse_artifact_audit,
    parse_three_way_prompt,
    process_lora_caption,
    post_process_caption,
    clip_tokens_safely,
    convert_to_tags,
)
from .storage import (
    resolve_output_dir,
    save_artifacts,
    get_original_filename,
    open_native_folder_dialog,
    build_dataset_manifest,
)
from .model_manager import ModelManager

__all__ = [
    "DEFAULT_MODEL_REPO",
    "MODEL_PRESETS",
    "CUSTOM_MODEL_KEY",
    "MODEL_SELECTION_CHOICES",
    "MODEL_MODES",
    "MODEL_CHOICES",
    "QUANTIZATION_OPTIONS",
    "ATTENTION_OPTIONS",
    "BATCH_MODES",
    "SYSTEM_PROMPT_MODES",
    "SYSTEM_PROMPT_PRESETS",
    "CUSTOM_SYSTEM_PROMPT_KEY",
    "SYSTEM_PROMPT_CHOICES",
    "PROMPT_TYPES",
    "PROMPT_TYPE_DIRECTIVES",
    "resolve_prompt_type",
    "ARTISTIC_STYLES",
    "ARTISTIC_STYLE_DIRECTIVES",
    "resolve_artistic_style",
    "CAPTION_STYLES",
    "STYLE_PROMPTS",
    "TEXT_EXPANSION_SYSTEM_PROMPT",
    "MULTI_IMAGE_SYSTEM_PROMPT",
    "BASE_TEXT_EXPANSION_PROMPT",
    "BASE_MULTI_IMAGE_PROMPT",
    "KREA2_PROMPT_IMAGE",
    "KREA2_PROMPT_TEXT",
    "KREA2_PROMPT_MULTI_IMAGE",
    "resolve_system_prompt",
    "process_vision_info",
    "tensor_to_pil",
    "clean_llm_output",
    "build_task_prompt",
    "parse_dual_prompt",
    "parse_artifact_audit",
    "parse_three_way_prompt",
    "process_lora_caption",
    "post_process_caption",
    "clip_tokens_safely",
    "convert_to_tags",
    "resolve_output_dir",
    "save_artifacts",
    "get_original_filename",
    "open_native_folder_dialog",
    "build_dataset_manifest",
    "ModelManager",
]

