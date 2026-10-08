"""
[STOIQO] Prompt Generator Engine — Nodes Package
"""

from .engine_node import StoiqoPromptGeneratorEngineNode
from .show_prompt_node import StoiqoShowPromptNode
from .model_loader_node import StoiqoVLMModelLoaderNode
from .visual_diff_node import StoiqoVisualDiffNode
from .image_compare_node import StoiqoImageCompareNode
from .text_concat_node import StoiqoTextConcatenateNode
from .resolution_node import StoiqoResolutionNode
from .dataset_node import StoiqoDatasetWriterNode
from .image_loader_node import StoiqoSmartFolderImageIterator
from .spatial_cropper_node import StoiqoSpatialCropperNode
from .trio_loader_node import StoiqoTripleImageLoaderNode
from .pro_saver_node import StoiqoProImageSaverNode
from .music_prompt_node import StoiqoMusicPromptEngineNode

# Backward compatibility aliases
QwenVLCaptionerNode = StoiqoPromptGeneratorEngineNode
QwenVLTextDisplayNode = StoiqoShowPromptNode

NODE_CLASS_MAPPINGS = {
    "StoiqoPromptGeneratorEngineNode": StoiqoPromptGeneratorEngineNode,
    "StoiqoShowPromptNode": StoiqoShowPromptNode,
    "StoiqoVLMModelLoaderNode": StoiqoVLMModelLoaderNode,
    "StoiqoVisualDiffNode": StoiqoVisualDiffNode,
    "StoiqoImageCompareNode": StoiqoImageCompareNode,
    "StoiqoTextConcatenateNode": StoiqoTextConcatenateNode,
    "StoiqoResolutionNode": StoiqoResolutionNode,
    "StoiqoDatasetWriterNode": StoiqoDatasetWriterNode,
    "StoiqoSmartFolderImageIterator": StoiqoSmartFolderImageIterator,
    "StoiqoSpatialCropperNode": StoiqoSpatialCropperNode,
    "StoiqoTripleImageLoaderNode": StoiqoTripleImageLoaderNode,
    "StoiqoProImageSaverNode": StoiqoProImageSaverNode,
    "StoiqoMusicPromptEngineNode": StoiqoMusicPromptEngineNode,
    # Backward compatibility aliases for existing saved workflows
    "QwenVLCaptionerNode": StoiqoPromptGeneratorEngineNode,
    "QwenVLTextDisplayNode": StoiqoShowPromptNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StoiqoPromptGeneratorEngineNode": "[STOIQO] Prompt Generator Engine",
    "StoiqoShowPromptNode": "[STOIQO] Show Prompt",
    "StoiqoVLMModelLoaderNode": "[STOIQO] VLM Model Loader",
    "StoiqoVisualDiffNode": "[STOIQO] Visual Diff & Forensic Inspector",
    "StoiqoImageCompareNode": "[STOIQO] Visual Compare Slider & Zoom",
    "StoiqoTextConcatenateNode": "[STOIQO] Text Concatenate & Clean",
    "StoiqoResolutionNode": "[STOIQO] Image Resolution & Aspect Ratio",
    "StoiqoDatasetWriterNode": "[STOIQO] Dataset & LoRA Toolkit",
    "StoiqoSmartFolderImageIterator": "[STOIQO] Smart Folder Image Iterator",
    "StoiqoSpatialCropperNode": "[STOIQO] Spatial Cropper & Mask Generator",
    "StoiqoTripleImageLoaderNode": "[STOIQO] Trio Image Loader (Hero & Thumbs)",
    "StoiqoProImageSaverNode": "[STOIQO] Pro Image Saver & Metadata Hub",
    "StoiqoMusicPromptEngineNode": "[STOIQO] Music Prompt & Lyrics Engine (YuE2)",
    # Backward compatibility aliases
    "QwenVLCaptionerNode": "[STOIQO] Prompt Generator Engine (Legacy)",
    "QwenVLTextDisplayNode": "[STOIQO] Show Prompt (Legacy)",
}

__all__ = [
    "StoiqoPromptGeneratorEngineNode",
    "StoiqoShowPromptNode",
    "StoiqoVLMModelLoaderNode",
    "StoiqoVisualDiffNode",
    "StoiqoImageCompareNode",
    "StoiqoTextConcatenateNode",
    "StoiqoResolutionNode",
    "StoiqoDatasetWriterNode",
    "StoiqoSmartFolderImageIterator",
    "StoiqoSpatialCropperNode",
    "StoiqoTripleImageLoaderNode",
    "StoiqoProImageSaverNode",
    "StoiqoMusicPromptEngineNode",
    "QwenVLCaptionerNode",
    "QwenVLTextDisplayNode",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
