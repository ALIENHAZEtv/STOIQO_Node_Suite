"""
STOIQO-Comfyui-Nodes
====================
Production-ready ComfyUI custom node suite for Visual Prompt Generation, Multimodal Comparison,
and Creative Utilities. Powered by Qwen2.5-VL with tiered 4-bit quantization, forensic visual diff,
interactive split-slider comparison, text concatenation, VAE-safe resolution generation,
negative prompt auditing, and Kohya/AI-Toolkit dataset export.
"""

try:
    from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
except (ImportError, ValueError):
    import sys, os
    _this_dir = os.path.dirname(os.path.abspath(__file__))
    if _this_dir not in sys.path:
        sys.path.insert(0, _this_dir)
    from nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
