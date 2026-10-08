"""
[STOIQO] Smart Folder Image Iterator
"""

import os
import re
import torch
import numpy as np
from PIL import Image, ImageOps


def natural_sort_key(s):
    """Sort strings containing numbers in natural human order (e.g. img2 before img10)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)]


class StoiqoSmartFolderImageIterator:
    """
    Intelligent image loader for datasets. Designed to work with ComfyUI's Auto Queue.
    It can skip images that already have a caption (.txt/.json) alongside them.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder_path": (
                    "STRING",
                    {
                        "default": "",
                        "placeholder": "Absolute path to the image folder...",
                        "tooltip": "Folder containing images to process.",
                    },
                ),
                "index": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 9999999,
                        "step": 1,
                        "tooltip": "The current index. When using Auto Queue, ComfyUI can increment a primitive connected to this.",
                    },
                ),
                "skip_captioned": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "If True, it will automatically look forward from the current index to find the next image that DOES NOT have a .txt file.",
                    },
                ),
                "caption_extension": (
                    [".txt", ".json", ".caption"],
                    {
                        "default": ".txt",
                        "tooltip": "The extension of the caption files to check when skip_captioned is True.",
                    },
                ),
            },
            "optional": {
                "recursive": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "If True, recursively traverses subdirectories within folder_path to find all images.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "INT", "INT")
    RETURN_NAMES = ("image", "mask", "filename", "width", "height")
    OUTPUT_IS_LIST = (False, False, False, False, False)
    FUNCTION = "load_image"
    CATEGORY = "STOIQO/Dataset Tools"

    @classmethod
    def IS_CHANGED(cls, folder_path, index, skip_captioned, caption_extension, recursive=False):
        return f"{folder_path}_{index}_{skip_captioned}_{caption_extension}_{recursive}"

    def _load_and_process_image(self, img_path):
        with Image.open(img_path) as raw_img:
            i = ImageOps.exif_transpose(raw_img)
            width, height = i.size

            image = i.convert("RGB")
            image = np.array(image).astype(np.float32) / 255.0
            image = torch.from_numpy(image)[None,]

            if 'A' in i.getbands():
                mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                mask = 1. - mask
            else:
                mask = np.zeros((height, width), dtype=np.float32)
            mask = torch.from_numpy(mask)[None,]

            return image, mask, width, height

    def load_image(self, folder_path, index, skip_captioned, caption_extension, recursive=False):
        blank = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
        blank_mask = torch.zeros((1, 64, 64), dtype=torch.float32)

        if not os.path.isdir(folder_path):
            return (blank, blank_mask, "INVALID_FOLDER", 64, 64)

        valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
        files = []

        if recursive:
            for root, _, filenames in os.walk(folder_path):
                for f in filenames:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in valid_exts:
                        rel = os.path.relpath(os.path.join(root, f), folder_path)
                        files.append(rel.replace("\\", "/"))
        else:
            for f in os.listdir(folder_path):
                if os.path.isfile(os.path.join(folder_path, f)):
                    ext = os.path.splitext(f)[1].lower()
                    if ext in valid_exts:
                        files.append(f)

        files.sort(key=natural_sort_key)

        if not files:
            return (blank, blank_mask, "EMPTY_FOLDER", 64, 64)

        current_idx = index
        selected_file = None

        while current_idx < len(files):
            candidate = files[current_idx]
            if skip_captioned:
                base_name = os.path.splitext(candidate)[0]
                cap_path = os.path.join(folder_path, base_name + caption_extension)
                if os.path.exists(cap_path):
                    current_idx += 1
                    continue
            selected_file = candidate
            break

        if selected_file is None:
            print(f"[STOIQO] All images processed or index out of bounds (Index {index}).")
            return (blank, blank_mask, "COMPLETED", 64, 64)

        img_path = os.path.join(folder_path, selected_file)
        print(f"[STOIQO] Loading Dataset Image [{current_idx}/{len(files)}]: {selected_file}")

        try:
            img_tensor, mask_tensor, w, h = self._load_and_process_image(img_path)
            return (img_tensor, mask_tensor, selected_file, int(w), int(h))
        except Exception as e:
            print(f"[STOIQO] Error loading {img_path}: {e}")
            return (blank, blank_mask, "ERROR", 64, 64)
