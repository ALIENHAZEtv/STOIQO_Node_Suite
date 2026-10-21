"""
[STOIQO] Trio Image Loader
Compact multi-image loader with Hero preview and interactive thumbnail switching.
Supports loading up to 3 images with individual outputs, focused output, and auto-batching.
"""

import os
import hashlib
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image, ImageOps

try:
    import folder_paths
except ImportError:
    class _MockFolderPaths:
        @staticmethod
        def get_input_directory():
            return "./input"
        @staticmethod
        def get_annotated_filepath(name):
            return name
        @staticmethod
        def exists_annotated_filepath(name):
            return True
    folder_paths = _MockFolderPaths()

try:
    import node_helpers
except ImportError:
    class _MockNodeHelpers:
        @staticmethod
        def pillow(func, img):
            return func(img)
    node_helpers = _MockNodeHelpers()


def _safe_load_image(image_name):
    """
    Loads an image from ComfyUI input directory using native conventions.
    Returns (image_tensor [1, H, W, 3], mask_tensor [1, H, W], width, height, is_valid)
    """
    if not image_name or image_name == "none":
        dummy_img = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
        dummy_mask = torch.zeros((1, 64, 64), dtype=torch.float32)
        return dummy_img, dummy_mask, 64, 64, False

    image_path = folder_paths.get_annotated_filepath(image_name)
    if not os.path.exists(image_path):
        dummy_img = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
        dummy_mask = torch.zeros((1, 64, 64), dtype=torch.float32)
        return dummy_img, dummy_mask, 64, 64, False

    try:
        with Image.open(image_path) as raw_img:
            img = node_helpers.pillow(ImageOps.exif_transpose, raw_img)
            w, h = img.size

            # RGB Image Tensor
            rgb_img = img.convert("RGB")
            img_arr = np.array(rgb_img).astype(np.float32) / 255.0
            image_tensor = torch.from_numpy(img_arr)[None,]  # [1, H, W, 3]

            # Alpha Mask Tensor (1.0 = opaque/inverted as per ComfyUI convention)
            if "A" in img.getbands():
                alpha_arr = np.array(img.getchannel("A")).astype(np.float32) / 255.0
                mask_tensor = 1.0 - torch.from_numpy(alpha_arr)[None,]
            else:
                mask_tensor = torch.zeros((1, h, w), dtype=torch.float32)

            return image_tensor, mask_tensor, w, h, True
    except Exception as e:
        print(f"[STOIQO Trio Loader] Errore caricamento {image_name}: {e}")
        dummy_img = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
        dummy_mask = torch.zeros((1, 64, 64), dtype=torch.float32)
        return dummy_img, dummy_mask, 64, 64, False


class StoiqoTripleImageLoaderNode:
    """
    [STOIQO] Trio Image Loader
    Consolidates 3 image loaders into a single ergonomic node with a Hero Preview
    and clickable thumbnails to focus and route images dynamically.
    """

    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory() if hasattr(folder_paths, "get_input_directory") else "input"
        files = []
        if os.path.exists(input_dir):
            files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
            if hasattr(folder_paths, "filter_files_content_types"):
                files = folder_paths.filter_files_content_types(files, ["image"])
        files = sorted(files)
        files_with_none = ["none"] + files

        return {
            "required": {
                "image_1": (files, {"image_upload": True, "tooltip": "Primary image (Slot 1)"}),
                "image_2": (files_with_none, {"image_upload": True, "default": "none", "tooltip": "Secondary image (Slot 2)"}),
                "image_3": (files_with_none, {"image_upload": True, "default": "none", "tooltip": "Tertiary image (Slot 3)"}),
            },
            "optional": {
                "active_focus": (["Slot 1", "Slot 2", "Slot 3"], {"default": "Slot 1", "tooltip": "Image routed to focused_image output"}),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "IMAGE", "MASK", "IMAGE", "MASK", "IMAGE", "MASK", "IMAGE", "INT")
    RETURN_NAMES = (
        "image_1", "mask_1",
        "image_2", "mask_2",
        "image_3", "mask_3",
        "focused_image", "focused_mask",
        "batch_images", "loaded_count"
    )
    FUNCTION = "load_trio_images"
    OUTPUT_NODE = False
    CATEGORY = "STOIQO"

    def load_trio_images(self, image_1, image_2="none", image_3="none", active_focus="Slot 1"):
        img1, mask1, w1, h1, v1 = _safe_load_image(image_1)
        img2, mask2, w2, h2, v2 = _safe_load_image(image_2)
        img3, mask3, w3, h3, v3 = _safe_load_image(image_3)

        valid_list = []
        if v1:
            valid_list.append((img1, mask1))
        if v2:
            valid_list.append((img2, mask2))
        if v3:
            valid_list.append((img3, mask3))

        loaded_count = len(valid_list)

        # Focused Image selection
        if active_focus == "Slot 2" and v2:
            focused_img, focused_mask = img2, mask2
        elif active_focus == "Slot 3" and v3:
            focused_img, focused_mask = img3, mask3
        else:
            focused_img, focused_mask = (img1, mask1) if v1 else (img2 if v2 else (img3, mask3))

        # Auto-batch concatenation: resize all valid images to match slot 1 dimensions
        if valid_list:
            target_h, target_w = valid_list[0][0].shape[1], valid_list[0][0].shape[2]
            batch_tensors = []
            for img_t, _ in valid_list:
                if img_t.shape[1] == target_h and img_t.shape[2] == target_w:
                    batch_tensors.append(img_t)
                else:
                    # Reshape to [1, C, H, W] for interpolate, then back to [1, H, W, C]
                    perm = img_t.permute(0, 3, 1, 2)
                    resized = F.interpolate(perm, size=(target_h, target_w), mode="bilinear", align_corners=False)
                    batch_tensors.append(resized.permute(0, 2, 3, 1))
            batch_images = torch.cat(batch_tensors, dim=0)
        else:
            batch_images = img1

        # Metadata for UI Preview
        ui_images = [
            {"filename": image_1, "subfolder": "", "type": "input", "slot": 1, "valid": v1, "width": w1, "height": h1},
            {"filename": image_2 if image_2 != "none" else "", "subfolder": "", "type": "input", "slot": 2, "valid": v2, "width": w2, "height": h2},
            {"filename": image_3 if image_3 != "none" else "", "subfolder": "", "type": "input", "slot": 3, "valid": v3, "width": w3, "height": h3},
        ]

        active_slot_num = 1 if active_focus == "Slot 1" else (2 if active_focus == "Slot 2" else 3)

        return {
            "ui": {
                "trio_info": ui_images,
                "active_slot": [active_slot_num],
            },
            "result": (
                img1, mask1,
                img2, mask2,
                img3, mask3,
                focused_img, focused_mask,
                batch_images,
                loaded_count
            ),
        }

    @classmethod
    def IS_CHANGED(cls, image_1, image_2="none", image_3="none", active_focus="Slot 1"):
        hashes = []
        for img in [image_1, image_2, image_3]:
            if img and img != "none":
                try:
                    p = folder_paths.get_annotated_filepath(img)
                    if os.path.exists(p):
                        m = hashlib.sha256()
                        with open(p, "rb") as f:
                            m.update(f.read())
                        hashes.append(m.hexdigest())
                except Exception:
                    pass
        hashes.append(str(active_focus))
        return "-".join(hashes)

    @classmethod
    def VALIDATE_INPUTS(cls, image_1, image_2="none", image_3="none", active_focus="Slot 1"):
        exists_fn = getattr(folder_paths, "exists_annotated_filepath", lambda p: True)
        if not image_1 or not exists_fn(image_1):
            return f"Invalid primary image: {image_1}"
        if image_2 and image_2 != "none" and not exists_fn(image_2):
            return f"Invalid image 2: {image_2}"
        if image_3 and image_3 != "none" and not exists_fn(image_3):
            return f"Invalid image 3: {image_3}"
        return True
