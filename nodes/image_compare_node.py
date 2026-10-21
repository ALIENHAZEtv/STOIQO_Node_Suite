"""
[STOIQO] Visual Image Compare Slider Node
Provides interactive Before/After image comparison with split slider,
synchronized pan & zoom on identical pixel coordinates, and pass-through outputs.
"""

import os
import json
import random
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

try:
    import folder_paths
except ImportError:
    import tempfile

    class _MockFolderPaths:
        @staticmethod
        def get_temp_directory():
            return tempfile.gettempdir()
        @staticmethod
        def get_output_directory():
            return "./output"
        @staticmethod
        def get_save_image_path(filename_prefix, output_dir, image_width=0, image_height=0):
            return (output_dir, filename_prefix, 0, "", filename_prefix)
    folder_paths = _MockFolderPaths()


class StoiqoImageCompareNode:
    """
    Interactive Visual Comparison Node for ComfyUI.
    Compares two images (e.g. Original vs Upscaled, Base vs Filtered, Seed A vs Seed B)
    with a draggable split slider and synchronized pan & zoom locked to the exact same coordinates.
    """

    COMPARISON_MODES = [
        "Split Slider (Before / After)",
        "Hold to Toggle (A/B Flicker)",
        "Side-by-Side (Synchronized)",
    ]

    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
        self.prefix_append = "_stoiqo_compare_" + "".join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(5))
        self.compress_level = 1
        self._last_saved_files = []

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_a": (
                    "IMAGE",
                    {"tooltip": "Image A (Before / Baseline / Original)."},
                ),
                "image_b": (
                    "IMAGE",
                    {"tooltip": "Image B (After / Upscaled / Altered)."},
                ),
            },
            "optional": {
                "initial_mode": (
                    cls.COMPARISON_MODES,
                    {
                        "default": cls.COMPARISON_MODES[0],
                        "tooltip": "Default interaction mode on canvas: Split Slider curtain, Hold to Toggle, or Side-by-Side.",
                    },
                ),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("IMAGE", "IMAGE")
    RETURN_NAMES = ("image_a", "image_b")
    FUNCTION = "compare_images"
    OUTPUT_NODE = True
    CATEGORY = "STOIQO"

    def compare_images(self, image_a, image_b, initial_mode=COMPARISON_MODES[0], prompt=None, extra_pnginfo=None):
        if image_a is None or image_b is None:
            raise ValueError("[STOIQO Image Compare] Both image_a and image_b must be connected.")
        if len(image_a) == 0 or len(image_b) == 0:
            raise ValueError("[STOIQO Image Compare] Input image tensors must contain at least one frame.")

        # Clean up temporary files from previous generations to ensure only the latest generation is kept
        if hasattr(self, "_last_saved_files") and self._last_saved_files:
            for old_path in self._last_saved_files:
                try:
                    if os.path.exists(old_path):
                        os.remove(old_path)
                except OSError:
                    pass
            self._last_saved_files = []
        else:
            self._last_saved_files = []

        self.output_dir = folder_paths.get_temp_directory()
        filename_prefix = "stoiqo_cmp" + self.prefix_append
        full_output_folder, filename, counter, subfolder, _ = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, image_a[0].shape[1], image_a[0].shape[0]
        )

        results = []
        # Always pick the latest frame if multiple frames / batch are passed
        pairs_to_save = [
            ("A", image_a[-1], "Original / Before"),
            ("B", image_b[-1], "Upscaled / After"),
        ]

        for tag, tensor_img, label in pairs_to_save:
            arr = (255.0 * tensor_img.cpu().numpy()).clip(0, 255).astype(np.uint8)
            pil_img = Image.fromarray(arr)

            metadata = PngInfo()
            if prompt is not None:
                metadata.add_text("prompt", json.dumps(prompt))
            if extra_pnginfo is not None:
                for k, v in extra_pnginfo.items():
                    metadata.add_text(k, json.dumps(v))

            file_name = f"{filename}_{tag}_{counter:05}_.png"
            file_path = os.path.join(full_output_folder, file_name)
            pil_img.save(file_path, pnginfo=metadata, compress_level=self.compress_level)
            self._last_saved_files.append(file_path)

            results.append({
                "filename": file_name,
                "subfolder": subfolder,
                "type": self.type,
                "label": label,
                "width": pil_img.width,
                "height": pil_img.height,
            })
            counter += 1

        # NOTE: deliberately NOT using the "images" key: the ComfyUI frontend intercepts it,
        # injects its own preview widget and auto-resizes the node (infinite growth with
        # our custom canvas widget). A dedicated key keeps the custom widget in full control.
        return {
            "ui": {
                "stoiqo_images": results,
                "mode": [initial_mode],
            },
            "result": (image_a, image_b),
        }
