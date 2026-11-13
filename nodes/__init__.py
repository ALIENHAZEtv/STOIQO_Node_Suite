"""
[STOIQO] Nodes Package
Fault-tolerant custom node registry for ComfyUI.
"""

import importlib
import logging

logger = logging.getLogger("STOIQO")

# 1. Safely register HTTP routes
try:
    from ..core.routes import register_stoiqo_routes
except (ImportError, ValueError):
    try:
        from core.routes import register_stoiqo_routes
    except Exception:
        register_stoiqo_routes = lambda: None

try:
    register_stoiqo_routes()
except Exception as e:
    logger.warning(f"[STOIQO] Route registration warning: {e}")

# 2. Dynamic Node Registry Table
# Format: (module_name, [(class_name, display_name), ...])
_NODE_DEFINITIONS = [
    # Core Loaders & Pipeline Infrastructure
    ("seed_node", [
        ("StoiqoSeedControllerNode", "[STOIQO] Seed & Resolution Controller")
    ]),
    ("universal_model_loader_node", [
        ("StoiqoUniversalModelLoaderNode", "[STOIQO] Universal Model Loader (All-in-One)")
    ]),
    ("show_prompt_node", [
        ("StoiqoShowPromptNode", "[STOIQO] Show Prompt")
    ]),
    ("image_compare_node", [
        ("StoiqoImageCompareNode", "[STOIQO] Visual Compare Slider & Zoom")
    ]),
    ("text_concat_node", [
        ("StoiqoTextConcatenateNode", "[STOIQO] Text Concatenate & Clean")
    ]),
    ("dataset_node", [
        ("StoiqoDatasetWriterNode", "[STOIQO] Dataset & LoRA Toolkit")
    ]),
    ("image_loader_node", [
        ("StoiqoImageLoaderNode", "[STOIQO] Image Loader")
    ]),
    ("folder_iterator_node", [
        ("StoiqoSmartFolderImageIterator", "[STOIQO] Smart Folder Image Iterator")
    ]),
    ("spatial_cropper_node", [
        ("StoiqoSpatialCropperNode", "[STOIQO] Spatial Cropper & Mask Generator")
    ]),
    ("pro_saver_node", [
        ("StoiqoProImageSaverNode", "[STOIQO] Pro Image Saver & Metadata Hub")
    ]),
    ("music_prompt_node", [
        ("StoiqoMusicPromptEngineNode", "[STOIQO] Music Prompt & Lyrics Engine (YuE2)")
    ]),
    ("audio_saver_node", [
        ("StoiqoAudioSaverNode", "[STOIQO] Pro Audio Saver & Metadata Hub")
    ]),
    ("video_saver_node", [
        ("StoiqoVideoSaverNode", "[STOIQO] Pro Video Saver & Frame Exporter")
    ]),
    ("inpaint_stitcher_node", [
        ("StoiqoInpaintStitcherNode", "[STOIQO] Inpaint Stitcher & Spatial Re-Roll")
    ]),
    ("watermark_node", [
        ("StoiqoWatermarkNode", "[STOIQO] Smart Watermark & Logo Stamp")
    ]),
    ("turbo_sampler_node", [
        ("StoiqoTurboSamplerNode", "[STOIQO] Turbo Sampler & Direct Decoder")
    ]),
    ("prompt_generator_node", [
        ("StoiqoPromptGeneratorNode", "[STOIQO] Prompt Generator")
    ]),
    ("lora_stack_node", [
        ("StoiqoLoraStackNode", "[STOIQO] LoRA Stack")
    ]),
    ("character_memory_node", [
        ("StoiqoCharacterMemoryNode", "[STOIQO] Character Memory Bank (Lorebook & DNA)")
    ]),
    ("frequency_separation_nodes", [
        ("StoiqoFrequencySeparationNode", "[STOIQO] Frequency Separation & Texture Hub"),
    ]),
    ("video_enhancement_nodes", [
        ("StoiqoVideoEnhancerNode", "[STOIQO] Video Deflicker & Frame Interpolator"),
    ]),
]

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

for module_name, classes in _NODE_DEFINITIONS:
    mod = None
    try:
        mod = importlib.import_module(f".{module_name}", package=__name__)
    except (ImportError, ValueError):
        try:
            mod = importlib.import_module(f"nodes.{module_name}")
        except Exception as err:
            logger.warning(f"[STOIQO] Notice: Could not load node module '{module_name}': {err}")
            continue
    except Exception as err:
        logger.error(f"[STOIQO] Error initializing node module '{module_name}': {err}", exc_info=True)
        continue

    for cls_name, display_name in classes:
        cls_obj = getattr(mod, cls_name, None)
        if cls_obj is not None:
            NODE_CLASS_MAPPINGS[cls_name] = cls_obj
            NODE_DISPLAY_NAME_MAPPINGS[cls_name] = display_name
            globals()[cls_name] = cls_obj
        else:
            logger.warning(f"[STOIQO] Notice: Class '{cls_name}' not found in '{module_name}'")

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
] + list(NODE_CLASS_MAPPINGS.keys())
