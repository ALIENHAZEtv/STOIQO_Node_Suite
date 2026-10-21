"""
[STOIQO] Nodes Package
"""

try:
    from ..core.routes import register_stoiqo_routes
except (ImportError, ValueError):
    from core.routes import register_stoiqo_routes

register_stoiqo_routes()

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
from .seed_node import StoiqoSeedControllerNode
from .audio_saver_node import StoiqoAudioSaverNode
from .video_saver_node import StoiqoVideoSaverNode
from .inpaint_stitcher_node import StoiqoInpaintStitcherNode
from .watermark_node import StoiqoWatermarkNode
from .tri_loader_hub_node import StoiqoTriLoaderHubNode
from .turbo_sampler_node import StoiqoTurboSamplerNode
from .style_directives_node import StoiqoStyleDirectivesNode
from .sampling_options_node import StoiqoSamplingOptionsNode
from .multi_image_context_node import StoiqoMultiImageContextNode
from .prompt_synthesizer_node import StoiqoPromptSynthesizerNode
from .lora_stack_node import StoiqoLoraStackNode
from .character_memory_node import StoiqoCharacterMemoryNode
from .universal_pipe_node import StoiqoUniversalPipeInNode, StoiqoUniversalPipeOutNode
from .webhook_notifier_node import StoiqoWebhookNotifierNode
from .frequency_separation_nodes import StoiqoFrequencySplitNode, StoiqoFrequencyMergeNode
from .depth_parallax_node import StoiqoDepthParallaxExtractor
from .spatial_reroll_node import StoiqoSpatialRerollNode
from .face_restore_hub_node import StoiqoFaceRestoreHub
from .video_enhancement_nodes import StoiqoTemporalDeflickerNode, StoiqoFrameInterpolateNode

NODE_CLASS_MAPPINGS = {
    "StoiqoUniversalPipeInNode": StoiqoUniversalPipeInNode,
    "StoiqoUniversalPipeOutNode": StoiqoUniversalPipeOutNode,
    "StoiqoWebhookNotifierNode": StoiqoWebhookNotifierNode,
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
    "StoiqoSeedControllerNode": StoiqoSeedControllerNode,
    "StoiqoAudioSaverNode": StoiqoAudioSaverNode,
    "StoiqoVideoSaverNode": StoiqoVideoSaverNode,
    "StoiqoInpaintStitcherNode": StoiqoInpaintStitcherNode,
    "StoiqoWatermarkNode": StoiqoWatermarkNode,
    "StoiqoTriLoaderHubNode": StoiqoTriLoaderHubNode,
    "StoiqoTurboSamplerNode": StoiqoTurboSamplerNode,
    "StoiqoStyleDirectivesNode": StoiqoStyleDirectivesNode,
    "StoiqoSamplingOptionsNode": StoiqoSamplingOptionsNode,
    "StoiqoMultiImageContextNode": StoiqoMultiImageContextNode,
    "StoiqoPromptSynthesizerNode": StoiqoPromptSynthesizerNode,
    "StoiqoLoraStackNode": StoiqoLoraStackNode,
    "StoiqoCharacterMemoryNode": StoiqoCharacterMemoryNode,
    "StoiqoFrequencySplitNode": StoiqoFrequencySplitNode,
    "StoiqoFrequencyMergeNode": StoiqoFrequencyMergeNode,
    "StoiqoDepthParallaxExtractor": StoiqoDepthParallaxExtractor,
    "StoiqoSpatialRerollNode": StoiqoSpatialRerollNode,
    "StoiqoFaceRestoreHub": StoiqoFaceRestoreHub,
    "StoiqoTemporalDeflickerNode": StoiqoTemporalDeflickerNode,
    "StoiqoFrameInterpolateNode": StoiqoFrameInterpolateNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StoiqoUniversalPipeInNode": "[STOIQO] Universal Context Pipe (In / Bus)",
    "StoiqoUniversalPipeOutNode": "[STOIQO] Universal Context Pipe (Out / Unpack)",
    "StoiqoWebhookNotifierNode": "[STOIQO] Webhook Notifier & Pipeline Exporter",
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
    "StoiqoSeedControllerNode": "[STOIQO] Smart Seed & Variance Controller",
    "StoiqoAudioSaverNode": "[STOIQO] Pro Audio Saver & Metadata Hub",
    "StoiqoVideoSaverNode": "[STOIQO] Pro Video Saver & Frame Exporter",
    "StoiqoInpaintStitcherNode": "[STOIQO] Inpaint Stitcher & Composite",
    "StoiqoWatermarkNode": "[STOIQO] Smart Watermark & Logo Stamp",
    "StoiqoTriLoaderHubNode": "[STOIQO] Tri-Model Loader Hub",
    "StoiqoTurboSamplerNode": "[STOIQO] Turbo Sampler & Direct Decoder",
    "StoiqoStyleDirectivesNode": "[STOIQO] AI Persona & Style Directives",
    "StoiqoSamplingOptionsNode": "[STOIQO] LLM Sampling & Precision",
    "StoiqoMultiImageContextNode": "[STOIQO] Multi-Image Context Hub",
    "StoiqoPromptSynthesizerNode": "[STOIQO] Prompt Synthesizer Engine",
    "StoiqoLoraStackNode": "[STOIQO] LoRA Stack",
    "StoiqoCharacterMemoryNode": "[STOIQO] Character Memory Bank (Lorebook & DNA)",
    "StoiqoFrequencySplitNode": "[STOIQO] Frequency Split (Texture & Color)",
    "StoiqoFrequencyMergeNode": "[STOIQO] Frequency Merge & Recomposite",
    "StoiqoDepthParallaxExtractor": "[STOIQO] Depth Map & 3D Parallax Extractor",
    "StoiqoSpatialRerollNode": "[STOIQO] Spatial Re-Roll & Contextual Fill",
    "StoiqoFaceRestoreHub": "[STOIQO] Face Restoration & Portrait Hub",
    "StoiqoTemporalDeflickerNode": "[STOIQO] Temporal Video Deflicker",
    "StoiqoFrameInterpolateNode": "[STOIQO] Video Frame Rate Multiplier (2x / 4x)",
}

__all__ = [
    "StoiqoUniversalPipeInNode",
    "StoiqoUniversalPipeOutNode",
    "StoiqoWebhookNotifierNode",
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
    "StoiqoSeedControllerNode",
    "StoiqoAudioSaverNode",
    "StoiqoVideoSaverNode",
    "StoiqoInpaintStitcherNode",
    "StoiqoWatermarkNode",
    "StoiqoTriLoaderHubNode",
    "StoiqoTurboSamplerNode",
    "StoiqoStyleDirectivesNode",
    "StoiqoSamplingOptionsNode",
    "StoiqoMultiImageContextNode",
    "StoiqoPromptSynthesizerNode",
    "StoiqoLoraStackNode",
    "StoiqoCharacterMemoryNode",
    "StoiqoFrequencySplitNode",
    "StoiqoFrequencyMergeNode",
    "StoiqoDepthParallaxExtractor",
    "StoiqoSpatialRerollNode",
    "StoiqoFaceRestoreHub",
    "StoiqoTemporalDeflickerNode",
    "StoiqoFrameInterpolateNode",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]


