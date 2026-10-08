"""
[STOIQO] Prompt Generator Engine — Vision Preprocessing
Image conversion, dynamic ViT aspect-ratio scaling (multiples of 28), and vision utilities.
"""

import numpy as np
from PIL import Image


def get_process_vision_info():
    """
    Retrieves process_vision_info from qwen_vl_utils if installed,
    otherwise provides an optimized local fallback.
    """
    try:
        from qwen_vl_utils import process_vision_info
        return process_vision_info
    except ImportError:
        pass

    def process_vision_info(messages):
        images = []
        for msg in messages:
            content = msg.get("content", [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "image":
                            img = item.get("image")
                            if isinstance(img, Image.Image):
                                images.append(img.convert("RGB") if img.mode != "RGB" else img)
                            elif isinstance(img, str):
                                images.append(Image.open(img).convert("RGB"))
        return (images if images else None), None

    return process_vision_info


process_vision_info = get_process_vision_info()


def tensor_to_pil(tensor, target_megapixel=1.0):
    """
    Converts a PyTorch image tensor to a PIL Image scaled to target_megapixel,
    snapped to multiples of 28 pixels as required by Qwen-VL's 2D-RoPE ViT architecture.
    Preserves original aspect ratio without distortion.
    """
    t = tensor.squeeze(0) if tensor.ndim == 4 else tensor
    arr = (255.0 * t.cpu().numpy()).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    if img.mode != "RGB":
        img = img.convert("RGB")

    orig_size = img.size
    w, h = img.size

    target_area = target_megapixel * 1024 * 1024
    current_area = w * h

    if current_area > target_area:
        scale = (target_area / current_area) ** 0.5
        new_w, new_h = int(w * scale), int(h * scale)
    else:
        new_w, new_h = w, h

    # Qwen-VL ViT requires dimensions to be exact multiples of 28.
    # Enforce a minimum floor of 224px (8x8 ViT patches) to prevent extreme low-res loss.
    min_floor = 224 if (w >= 224 and h >= 224) else 28
    new_w = max(min_floor, round(new_w / 28) * 28)
    new_h = max(min_floor, round(new_h / 28) * 28)

    if (new_w, new_h) != (w, h):
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        print(f"[STOIQO] Image resized: ({w}x{h}) -> ({new_w}x{new_h}) [{new_w * new_h / 1e6:.2f} MP]")
    else:
        print(f"[STOIQO] Image kept at resolution: ({new_w}x{new_h}) [{new_w * new_h / 1e6:.2f} MP]")

    return img, orig_size
