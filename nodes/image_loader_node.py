"""
[STOIQO] Image Loader
Ergonomic multi-image loader with Hero preview and interactive thumbnail switching.
Loads 1 to 3 images with an automatic unified output (batch of 1, 2, or 3 images),
mask output, individual slot outputs, and loaded count.
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
    Loads an image from ComfyUI input directory, direct local file path, or remote URL.
    Returns (image_tensor [1, H, W, 3], mask_tensor [1, H, W], width, height, is_valid)
    """
    if not image_name or image_name == "none":
        return None, None, 0, 0, False

    image_path = None
    temp_download = None
    if image_name.startswith("http://") or image_name.startswith("https://"):
        try:
            import urllib.request
            import tempfile
            req = urllib.request.Request(image_name, headers={"User-Agent": "STOIQO-ImageLoader/1.0"})
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = resp.read()
            tmp_fd, temp_download = tempfile.mkstemp(suffix=".png")
            with open(tmp_fd, "wb") as f:
                f.write(data)
            image_path = temp_download
        except Exception as err:
            print(f"[STOIQO Image Loader] Failed to download URL '{image_name}': {err}")
            return None, None, 0, 0, False
    elif os.path.isabs(image_name) and os.path.exists(image_name):
        image_path = image_name
    else:
        image_path = folder_paths.get_annotated_filepath(image_name)
        if not os.path.exists(image_path):
            return None, None, 0, 0, False

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
        print(f"[STOIQO Image Loader] Error loading {image_name}: {e}")
        return None, None, 0, 0, False
    finally:
        if temp_download and os.path.exists(temp_download):
            try:
                os.remove(temp_download)
            except Exception:
                pass


def _fit_image_and_mask_to_target(img_t, mask_t, target_h, target_w, fit_mode="Center Fit (Letterbox / Pad)"):
    """
    Fits an image tensor [1, H, W, 3] and mask tensor [1, H, W] to (target_h, target_w)
    strictly respecting aspect ratio rules (zero stretch).
    """
    _, h, w, c = img_t.shape
    if h == target_h and w == target_w:
        return img_t, mask_t

    if fit_mode == "Stretch to Fill":
        perm = img_t.permute(0, 3, 1, 2)
        resized_img = F.interpolate(perm, size=(target_h, target_w), mode="bilinear", align_corners=False).permute(0, 2, 3, 1)
        mask_4d = mask_t.unsqueeze(1)
        resized_mask = F.interpolate(mask_4d, size=(target_h, target_w), mode="bilinear", align_corners=False).squeeze(1)
        return resized_img, resized_mask

    scale_w = target_w / w
    scale_h = target_h / h

    if fit_mode == "Center Crop (Preserve Aspect)":
        scale = max(scale_w, scale_h)
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))

        perm = img_t.permute(0, 3, 1, 2)
        scaled_img = F.interpolate(perm, size=(new_h, new_w), mode="bilinear", align_corners=False).permute(0, 2, 3, 1)
        mask_4d = mask_t.unsqueeze(1)
        scaled_mask = F.interpolate(mask_4d, size=(new_h, new_w), mode="bilinear", align_corners=False).squeeze(1)

        start_x = (new_w - target_w) // 2
        start_y = (new_h - target_h) // 2
        out_img = scaled_img[:, start_y:start_y + target_h, start_x:start_x + target_w, :]
        out_mask = scaled_mask[:, start_y:start_y + target_h, start_x:start_x + target_w]
        return out_img, out_mask

    # Default: "Center Fit (Letterbox / Pad)" -> Zero stretch, zero crop
    scale = min(scale_w, scale_h)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))

    perm = img_t.permute(0, 3, 1, 2)
    scaled_img = F.interpolate(perm, size=(new_h, new_w), mode="bilinear", align_corners=False).permute(0, 2, 3, 1)
    mask_4d = mask_t.unsqueeze(1)
    scaled_mask = F.interpolate(mask_4d, size=(new_h, new_w), mode="bilinear", align_corners=False).squeeze(1)

    out_img = torch.zeros((1, target_h, target_w, c), dtype=img_t.dtype, device=img_t.device)
    # Background padding mask set to 1.0 (masked/transparent in ComfyUI convention)
    out_mask = torch.ones((1, target_h, target_w), dtype=mask_t.dtype, device=mask_t.device)

    start_x = (target_w - new_w) // 2
    start_y = (target_h - new_h) // 2
    out_img[:, start_y:start_y + new_h, start_x:start_x + new_w, :] = scaled_img
    out_mask[:, start_y:start_y + new_h, start_x:start_x + new_w] = scaled_mask

    return out_img, out_mask


class StoiqoImageLoaderNode:
    """
    [STOIQO] Image Loader
    Unified ergonomic image loader with Hero preview and interactive thumbnail switching.
    Loads 1 to 3 images with an automatic unified output (batch of 1, 2, or 3 images),
    mask output, individual slot outputs, and loaded count.
    Supports zero-stretch aspect-ratio protected fitting and URL downloading.
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
        if not files:
            files = ["none"]
        files_with_none = ["none"] + [f for f in files if f != "none"]

        return {
            "required": {
                "image_1": (files, {"image_upload": True, "tooltip": "Primary image (Slot 1)"}),
                "image_2": (files_with_none, {"image_upload": True, "default": "none", "tooltip": "Optional secondary image (Slot 2)"}),
                "image_3": (files_with_none, {"image_upload": True, "default": "none", "tooltip": "Optional tertiary image (Slot 3)"}),
            },
            "optional": {
                "fit_mode": (
                    [
                        "Center Fit (Letterbox / Pad)",
                        "Center Crop (Preserve Aspect)",
                        "Stretch to Fill",
                    ],
                    {
                        "default": "Center Fit (Letterbox / Pad)",
                        "tooltip": "Aspect ratio preservation mode when batching multiple images of different dimensions.",
                    },
                ),
                "active_focus": (["Slot 1", "Slot 2", "Slot 3"], {"default": "Slot 1", "tooltip": "Image routed to focused preview"}),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "IMAGE", "IMAGE", "IMAGE", "INT")
    RETURN_NAMES = (
        "image", "mask",
        "image_1", "image_2", "image_3",
        "loaded_count"
    )
    FUNCTION = "load_images"
    OUTPUT_NODE = False
    CATEGORY = "STOIQO"

    def load_images(
        self,
        image_1,
        image_2="none",
        image_3="none",
        fit_mode="Center Fit (Letterbox / Pad)",
        active_focus="Slot 1",
        **kwargs,
    ):
        img1, mask1, w1, h1, v1 = _safe_load_image(image_1)
        img2, mask2, w2, h2, v2 = _safe_load_image(image_2)
        img3, mask3, w3, h3, v3 = _safe_load_image(image_3)

        valid_list = []
        if v1 and img1 is not None:
            valid_list.append((img1, mask1))
        if v2 and img2 is not None:
            valid_list.append((img2, mask2))
        if v3 and img3 is not None:
            valid_list.append((img3, mask3))

        loaded_count = len(valid_list)

        # Fallback if no images could be loaded
        if not valid_list:
            dummy_img = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
            dummy_mask = torch.zeros((1, 64, 64), dtype=torch.float32)
            return {
                "ui": {"trio_info": [], "active_slot": [1]},
                "result": (dummy_img, dummy_mask, dummy_img, dummy_img, dummy_img, 0)
            }

        # Unified Image output:
        # If 1 image -> that image tensor [1, H, W, 3]
        # If 2 or 3 images -> batched tensor [N, H, W, 3] fitted to match slot 1 aspect ratio & dimensions
        if len(valid_list) == 1:
            unified_image = valid_list[0][0]
            unified_mask = valid_list[0][1]
        else:
            target_h, target_w = valid_list[0][0].shape[1], valid_list[0][0].shape[2]
            batch_images = []
            batch_masks = []
            for img_t, msk_t in valid_list:
                fitted_img, fitted_msk = _fit_image_and_mask_to_target(
                    img_t, msk_t, target_h, target_w, fit_mode=fit_mode
                )
                batch_images.append(fitted_img)
                batch_masks.append(fitted_msk)
            unified_image = torch.cat(batch_images, dim=0)
            unified_mask = torch.cat(batch_masks, dim=0)

        # Individual slot outputs: if not loaded, return empty 1x1 tensor so downstream receives valid tensor
        empty_slot = torch.zeros((1, 1, 1, 3), dtype=torch.float32)
        out_img1 = img1 if (v1 and img1 is not None) else empty_slot
        out_img2 = img2 if (v2 and img2 is not None) else empty_slot
        out_img3 = img3 if (v3 and img3 is not None) else empty_slot

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
                unified_image,
                unified_mask,
                out_img1,
                out_img2,
                out_img3,
                loaded_count
            ),
        }

    @classmethod
    def IS_CHANGED(cls, image_1, image_2="none", image_3="none", active_focus="Slot 1", **kwargs):
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
    def VALIDATE_INPUTS(cls, image_1, image_2="none", image_3="none", active_focus="Slot 1", **kwargs):
        exists_fn = getattr(folder_paths, "exists_annotated_filepath", lambda p: True)
        if not image_1 or not exists_fn(image_1):
            return f"Invalid primary image: {image_1}"
        if image_2 and image_2 != "none" and not exists_fn(image_2):
            return f"Invalid image 2: {image_2}"
        if image_3 and image_3 != "none" and not exists_fn(image_3):
            return f"Invalid image 3: {image_3}"
        return True


# Backward compatibility alias
StoiqoTripleImageLoaderNode = StoiqoImageLoaderNode
