"""
[STOIQO] Smart Folder Image Iterator
High-performance dataset and bulk image loader for ComfyUI.
Supports Single (iterative / Auto-Queue) and Batch (stacked tensor) loading,
instantaneous in-memory caching (0.00ms execution), mask companion filtering,
and flexible iteration modes (Sequential, Reverse, Random Shuffle).
"""

import os
import re
import random
import logging
import torch
import numpy as np
from PIL import Image, ImageOps

logger = logging.getLogger("STOIQO")

try:
    import folder_paths
except ImportError:
    class _MockFolderPaths:
        @staticmethod
        def get_input_directory():
            return "./input"
    folder_paths = _MockFolderPaths()


def natural_sort_key(s):
    """Sort strings containing numbers in natural human order (e.g. img2 before img10)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)]


class StoiqoSmartFolderImageIterator:
    """
    Intelligent image loader for datasets and batch processing.
    Loads images from a local folder either one by one (iterative / Auto-Queue)
    or all together as a single stacked batch tensor [B, H, W, 3].
    Includes in-memory filesystem caching for instantaneous 0.00ms execution.
    """

    _FOLDER_CACHE = {}

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
                "load_mode": (
                    ["Single (Iterative)", "Batch (All in Folder)"],
                    {
                        "default": "Single (Iterative)",
                        "tooltip": "Single: loads one image at index (ideal for Auto-Queue). Batch: stacks images into a single [B, H, W, 3] tensor.",
                    },
                ),
                "index": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 9999999,
                        "step": 1,
                        "tooltip": "Current index for Single mode. Increment via ComfyUI Primitive for Auto Queue.",
                    },
                ),
                "iteration_mode": (
                    ["Sequential", "Reverse", "Random (Seed)"],
                    {
                        "default": "Sequential",
                        "tooltip": "Sequential: 0 to N. Reverse: N to 0. Random: reproducible deterministic shuffle based on seed.",
                    },
                ),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xffffffffffffffff,
                        "tooltip": "Seed for Random (Seed) iteration mode.",
                    },
                ),
                "loop_folder": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "If True, wraps around (modulo total images) when the end is reached instead of completing.",
                    },
                ),
                "skip_captioned": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "If True, automatically skips images that already have a caption sidecar file (.txt/.json/.caption).",
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
                "max_batch_images": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 4096,
                        "step": 1,
                        "tooltip": "In Batch mode, maximum number of images to stack (0 = all images in folder).",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "INT", "INT")
    RETURN_NAMES = ("image", "mask", "filename", "width", "height")
    OUTPUT_IS_LIST = (False, False, False, False, False)
    FUNCTION = "load_image"
    CATEGORY = "STOIQO"

    @classmethod
    def IS_CHANGED(cls, folder_path, load_mode="Single (Iterative)", index=0, iteration_mode="Sequential", seed=0, loop_folder=False, skip_captioned=False, caption_extension=".txt", recursive=False, max_batch_images=0):
        try:
            mtime = os.path.getmtime(folder_path) if folder_path and os.path.isdir(folder_path) else 0.0
        except OSError:
            mtime = 0.0
        return f"{folder_path}_{mtime}_{load_mode}_{index}_{iteration_mode}_{seed}_{loop_folder}_{skip_captioned}_{caption_extension}_{recursive}_{max_batch_images}"

    @classmethod
    def _scan_directory(cls, folder_path, recursive=False):
        """
        Scans directory for valid image files while filtering out mask companion files
        (e.g. foo_mask.png or foo.mask.png when foo.png exists) so masks never pollute image datasets.
        """
        valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}
        raw_files = []

        if recursive:
            for root, _, filenames in os.walk(folder_path):
                for f in filenames:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in valid_exts:
                        rel = os.path.relpath(os.path.join(root, f), folder_path)
                        raw_files.append(rel.replace("\\", "/"))
        else:
            for f in os.listdir(folder_path):
                if os.path.isfile(os.path.join(folder_path, f)):
                    ext = os.path.splitext(f)[1].lower()
                    if ext in valid_exts:
                        raw_files.append(f)

        # Set of lowercase filepaths for rapid companion lookup
        raw_set_lower = {f.lower() for f in raw_files}

        clean_files = []
        for f in raw_files:
            dir_part, file_name = os.path.split(f)
            stem, ext = os.path.splitext(file_name)
            stem_lower = stem.lower()

            # Check if this file is a mask companion to an existing base image
            is_mask_companion = False
            if stem_lower.endswith(("_mask", ".mask")):
                base_stem = stem[:-5]
                for test_ext in valid_exts:
                    companion_rel = os.path.join(dir_part, f"{base_stem}{test_ext}").replace("\\", "/").lower()
                    if companion_rel in raw_set_lower:
                        is_mask_companion = True
                        break

            if not is_mask_companion:
                clean_files.append(f)

        clean_files.sort(key=natural_sort_key)
        return clean_files

    @classmethod
    def _get_cached_files(cls, folder_path, recursive=False):
        """
        Retrieves cached directory file list in 0.00ms.
        Automatically invalidates if folder modification time (mtime) changes.
        """
        abs_path = os.path.abspath(folder_path)
        cache_key = (abs_path, bool(recursive))

        try:
            mtime = os.path.getmtime(abs_path)
        except OSError:
            mtime = 0.0

        cached = cls._FOLDER_CACHE.get(cache_key)
        if cached is not None and cached.get("mtime") == mtime:
            return cached["files"]

        files = cls._scan_directory(abs_path, recursive)
        cls._FOLDER_CACHE[cache_key] = {
            "mtime": mtime,
            "files": files,
            "count": len(files),
        }
        return files

    @classmethod
    def _order_files(cls, files, iteration_mode, seed):
        """Orders files according to Sequential, Reverse, or Random (Seed) shuffle."""
        if not files:
            return []
        if iteration_mode == "Reverse":
            return list(reversed(files))
        elif iteration_mode == "Random (Seed)":
            rng = random.Random(seed)
            indices = list(range(len(files)))
            rng.shuffle(indices)
            return [files[i] for i in indices]
        return list(files)

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

    def load_image(
        self,
        folder_path,
        load_mode="Single (Iterative)",
        index=0,
        iteration_mode="Sequential",
        seed=0,
        loop_folder=False,
        skip_captioned=False,
        caption_extension=".txt",
        recursive=False,
        max_batch_images=0,
    ):
        blank = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
        blank_mask = torch.zeros((1, 64, 64), dtype=torch.float32)

        if not folder_path or not os.path.isdir(folder_path):
            default_dir = folder_paths.get_input_directory() if hasattr(folder_paths, "get_input_directory") else "./input"
            if os.path.isdir(default_dir):
                folder_path = default_dir
            elif not os.path.isdir(folder_path):
                return (blank, blank_mask, "INVALID_FOLDER", 64, 64)

        files = self._get_cached_files(folder_path, recursive)
        if not files:
            return (blank, blank_mask, "EMPTY_FOLDER", 64, 64)

        ordered_files = self._order_files(files, iteration_mode, seed)

        # ── Mode A: Batch (All in Folder) ─────────────────────────────────
        if load_mode == "Batch (All in Folder)":
            candidates = []
            for f in ordered_files:
                if skip_captioned:
                    base_name = os.path.splitext(f)[0]
                    cap_path = os.path.join(folder_path, base_name + caption_extension)
                    if os.path.exists(cap_path):
                        continue
                candidates.append(f)

            if max_batch_images > 0:
                candidates = candidates[:max_batch_images]

            if not candidates:
                logger.info("[Folder Iterator] Batch: All images processed or skipped.")
                return (blank, blank_mask, "COMPLETED", 64, 64)

            loaded_imgs = []
            loaded_masks = []
            target_h, target_w = None, None

            for f in candidates:
                img_path = os.path.join(folder_path, f)
                try:
                    img_t, mask_t, w, h = self._load_and_process_image(img_path)
                    if target_h is None:
                        target_h, target_w = img_t.shape[1], img_t.shape[2]
                    elif img_t.shape[1] != target_h or img_t.shape[2] != target_w:
                        # Resize to match first image dimensions [1, H, W, 3]
                        img_perm = img_t.permute(0, 3, 1, 2)
                        img_resized = torch.nn.functional.interpolate(
                            img_perm, size=(target_h, target_w), mode="bilinear", align_corners=False
                        )
                        img_t = img_resized.permute(0, 2, 3, 1)

                        mask_perm = mask_t.unsqueeze(1)
                        mask_resized = torch.nn.functional.interpolate(
                            mask_perm, size=(target_h, target_w), mode="nearest"
                        )
                        mask_t = mask_resized.squeeze(1)

                    loaded_imgs.append(img_t)
                    loaded_masks.append(mask_t)
                except Exception as e:
                    logger.warning(f"[Folder Iterator] Error loading batch image {f}: {e}")

            if not loaded_imgs:
                return (blank, blank_mask, "ERROR", 64, 64)

            batch_imgs = torch.cat(loaded_imgs, dim=0)
            batch_masks = torch.cat(loaded_masks, dim=0)
            summary_name = f"Batch ({len(loaded_imgs)} images): {candidates[0]} ... {candidates[-1]}"
            logger.info(f"[Folder Iterator] Loaded Image Batch [{len(loaded_imgs)}/{len(files)}]: {summary_name}")

            return {
                "ui": {
                    "progress": [f"{len(loaded_imgs)} / {len(files)} (Batch)"],
                    "filename": [summary_name],
                    "total": [len(files)],
                    "index": [len(loaded_imgs)],
                },
                "result": (batch_imgs, batch_masks, summary_name, int(target_w), int(target_h)),
            }

        # ── Mode B: Single (Iterative / Auto-Queue) ────────────────────────
        current_idx = index
        if loop_folder and len(ordered_files) > 0:
            current_idx = index % len(ordered_files)

        selected_file = None
        checked_count = 0
        max_to_check = len(ordered_files)

        while checked_count < max_to_check:
            if current_idx >= len(ordered_files):
                if loop_folder:
                    current_idx = 0
                else:
                    break

            candidate = ordered_files[current_idx]
            if skip_captioned:
                base_name = os.path.splitext(candidate)[0]
                cap_path = os.path.join(folder_path, base_name + caption_extension)
                if os.path.exists(cap_path):
                    current_idx += 1
                    checked_count += 1
                    continue

            selected_file = candidate
            break

        if selected_file is None:
            logger.info(f"[Folder Iterator] All images processed or index out of bounds (Index {index}).")
            return (blank, blank_mask, "COMPLETED", 64, 64)

        img_path = os.path.join(folder_path, selected_file)
        logger.info(f"[Folder Iterator] Loading Dataset Image [{current_idx + 1}/{len(ordered_files)}]: {selected_file}")

        try:
            img_tensor, mask_tensor, w, h = self._load_and_process_image(img_path)
            return {
                "ui": {
                    "progress": [f"{current_idx + 1} / {len(ordered_files)}"],
                    "filename": [selected_file],
                    "total": [len(ordered_files)],
                    "index": [current_idx],
                },
                "result": (img_tensor, mask_tensor, selected_file, int(w), int(h)),
            }
        except Exception as e:
            logger.warning(f"[Folder Iterator] Error loading {img_path}: {e}")
            return (blank, blank_mask, "ERROR", 64, 64)
