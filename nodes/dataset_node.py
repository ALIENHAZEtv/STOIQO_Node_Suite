"""
[STOIQO] Dataset & LoRA Training Toolkit Node
Production-grade dataset formatter, image saver, and artifact pipeline for Kohya_ss and AI-Toolkit.
Features:
- Atomic image-caption pair exporting (saves .png/.webp/.jpg alongside .txt and .json).
- Multi-format caption routing (Prose, Booru Tags, Trigger-pinned, Combined).
- Visual deduplication via perceptual dHash to prevent LoRA overfitting.
- Tag cleaning, case-insensitive blacklisting, and deterministic tag shuffling with keep_tokens.
"""

import os
import re
import random
import numpy as np
import torch
from PIL import Image

try:
    from ..core import (
        save_artifacts,
        build_dataset_manifest,
        get_original_filename,
        resolve_output_dir,
        NodeTelemetryTimer,
        inject_telemetry,
    )
except (ImportError, ValueError):
    from core import (
        save_artifacts,
        build_dataset_manifest,
        get_original_filename,
        resolve_output_dir,
        NodeTelemetryTimer,
        inject_telemetry,
    )


def _compute_image_fingerprint(img_tensor):
    """Computes a normalized 16x16 perceptual thumbnail fingerprint (256 floats)."""
    if isinstance(img_tensor, torch.Tensor):
        t = img_tensor.detach().cpu()
        while t.ndim > 3:
            t = t[0]
        t = torch.clamp(t, 0.0, 1.0) * 255.0
        arr = t.numpy().astype(np.uint8)
    else:
        arr = np.clip(np.array(img_tensor), 0, 255).astype(np.uint8)

    pil = Image.fromarray(arr).convert("L").resize((16, 16), Image.Resampling.BILINEAR)
    return np.asarray(pil, dtype=np.float32) / 255.0


def _fingerprint_similarity(f1, f2):
    """Computes normalized perceptual similarity between two fingerprints (1.0 = identical)."""
    l1 = np.mean(np.abs(f1 - f2))
    return float(max(0.0, 1.0 - l1))


# Backwards compatibility alias
_compute_dhash = _compute_image_fingerprint
_hamming_similarity = _fingerprint_similarity


def _tensor_to_pil(img_tensor):
    """Converts a [H, W, C] or [1, H, W, C] tensor to a PIL Image."""
    if isinstance(img_tensor, torch.Tensor):
        t = img_tensor.detach().cpu()
        while t.ndim > 3:
            t = t[0]
        t = torch.clamp(t, 0.0, 1.0) * 255.0
        arr = t.numpy().astype(np.uint8)
    else:
        arr = np.clip(np.array(img_tensor), 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


class StoiqoDatasetWriterNode:
    """
    [STOIQO] Dataset & LoRA Toolkit
    Dataset formatter, image exporter, and artifact saver for LoRA/checkpoint training.
    Supports atomic image + caption pairs, perceptual deduplication, tag shuffling, and Kohya manifests.
    """

    CAPTION_FORMAT_OPTIONS = [
        "Prose Caption (.txt)",
        "Booru Tags (.txt)",
        "Trigger + Tags (.txt)",
        "Combined (Trigger + Tags + Prose)",
        "Prose in .txt, Tags in _tags.txt",
    ]

    IMAGE_FORMAT_OPTIONS = [
        "PNG (Lossless)",
        "WEBP (Quality 95)",
        "JPG (Quality 95)",
    ]

    TAG_SEPARATORS = [", ", "\n (Newline)", " | "]

    def __init__(self):
        self.session_hashes = []

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "caption": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Natural language prose caption (from Prompt Generator or VLM).",
                    },
                ),
                "trigger_word": (
                    "STRING",
                    {
                        "default": "",
                        "placeholder": "e.g. sks_char",
                        "tooltip": "Activator keyword pinned at index 0 of every caption file for LoRA training.",
                    },
                ),
                "caption_format": (
                    cls.CAPTION_FORMAT_OPTIONS,
                    {
                        "default": cls.CAPTION_FORMAT_OPTIONS[0],
                        "tooltip": "Format written into the primary <stem>.txt file for training.",
                    },
                ),
                "blacklist_tags": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "watermark, signature, text, username, artist name, blurry, lowres",
                        "tooltip": "Unwanted tags to strip (case-insensitive, applies to both tags and prose).",
                    },
                ),
                "shuffle_tags": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Shuffle non-trigger tags deterministically via seed (prevents positional bias in LoRA training).",
                    },
                ),
                "keep_tokens": (
                    "INT",
                    {
                        "default": 1,
                        "min": 0,
                        "max": 20,
                        "tooltip": "Number of initial tags to keep fixed at the start when shuffling (e.g. 1 keeps trigger word).",
                    },
                ),
                "tag_separator": (
                    cls.TAG_SEPARATORS,
                    {
                        "default": cls.TAG_SEPARATORS[0],
                        "tooltip": "Separator between tags. ', ' = Kohya standard. Newline = one per line.",
                    },
                ),
                "save_txt": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Save captions as .txt files paired with images.",
                    },
                ),
                "save_json_metadata": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Save Kohya/AI-Toolkit compliant JSON manifest sidecar alongside .txt.",
                    },
                ),
                "output_dir": (
                    "STRING",
                    {
                        "default": "./output/dataset",
                        "tooltip": "Output folder. Saves paired image, .txt caption, and .json sidecars.",
                    },
                ),
                "use_original_filename": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Auto-detect source filename from the connected Image node.",
                    },
                ),
                "fallback_prefix": (
                    "STRING",
                    {
                        "default": "dataset_item",
                        "placeholder": "Used when original filename cannot be detected",
                    },
                ),
            },
            "optional": {
                "image": (
                    "IMAGE",
                    {
                        "tooltip": "Connect image or batch of images. Enables image saving, resolution detection, and deduplication.",
                    },
                ),
                "tags": (
                    "STRING",
                    {
                        "forceInput": True,
                        "default": "",
                        "tooltip": "Comma-separated tag list (from Prompt Generator or Danbooru tagger).",
                    },
                ),
                "negative": (
                    "STRING",
                    {
                        "forceInput": True,
                        "default": "",
                        "tooltip": "Negative prompt constraints (optional).",
                    },
                ),
                "save_image": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Save the image file alongside the .txt caption file for atomic dataset creation.",
                    },
                ),
                "image_format": (
                    cls.IMAGE_FORMAT_OPTIONS,
                    {
                        "default": cls.IMAGE_FORMAT_OPTIONS[0],
                        "tooltip": "Image format to save when save_image is enabled.",
                    },
                ),
                "deduplicate_images": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Skip near-duplicate image frames using perceptual dHash to prevent LoRA overfitting.",
                    },
                ),
                "similarity_threshold": (
                    "FLOAT",
                    {
                        "default": 0.95,
                        "min": 0.70,
                        "max": 1.00,
                        "step": 0.01,
                        "tooltip": "Threshold to consider two images duplicates (0.95 = 95% visual similarity).",
                    },
                ),
                "filename": (
                    "STRING",
                    {
                        "tooltip": "Explicit filename override stem (e.g. from Smart Folder Image Iterator).",
                    },
                ),
                "seed": (
                    "INT",
                    {
                        "default": 42,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "tooltip": "Seed for deterministic tag shuffling.",
                    },
                ),
            },
            "hidden": {
                "prompt": "PROMPT",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "IMAGE")
    RETURN_NAMES = ("prompt", "tags", "negative", "image")
    OUTPUT_IS_LIST = (True, True, True, True)
    FUNCTION = "process_and_save"
    OUTPUT_NODE = True
    CATEGORY = "STOIQO"

    def process_and_save(
        self,
        caption="",
        trigger_word="",
        caption_format="Prose Caption (.txt)",
        blacklist_tags="watermark, signature, text, username, artist name, blurry, lowres",
        shuffle_tags=False,
        keep_tokens=1,
        tag_separator=", ",
        save_txt=True,
        save_json_metadata=False,
        output_dir="./output/dataset",
        use_original_filename=True,
        fallback_prefix="dataset_item",
        image=None,
        tags="",
        negative="",
        save_image=False,
        image_format="PNG (Lossless)",
        deduplicate_images=False,
        similarity_threshold=0.95,
        filename=None,
        seed=42,
        prompt=None,
        unique_id=None,
        **kwargs,
    ):
        with NodeTelemetryTimer(node_id=unique_id, node_name="DatasetWriter") as timer:
            # 1. Normalize list inputs
            caption_list = caption if isinstance(caption, list) else [caption]
            tags_list_in = tags if isinstance(tags, list) else [tags]
            negative_list = negative if isinstance(negative, list) else [negative]
            if filename is not None:
                filename_list = [str(f) for f in filename] if isinstance(filename, (list, tuple)) else [str(filename)]
            else:
                filename_list = []

            # 2. Normalize images
            img_list = []
            if image is not None:
                if isinstance(image, torch.Tensor) and image.ndim == 4:
                    img_list = [image[b:b + 1] for b in range(image.shape[0])]
                elif isinstance(image, list):
                    img_list = image
                else:
                    img_list = [image]

            total_items = max(len(caption_list), len(tags_list_in), len(img_list), len(filename_list), 1)

            out_captions = []
            out_tags = []
            out_negatives = []
            out_images = []

            # 3. Clean Trigger Word
            clean_trigger = str(trigger_word or "").strip().rstrip(",").strip()

            # 4. Parse Blacklist
            raw_bl = str(blacklist_tags or "").replace("\n", ",").replace(";", ",")
            bl_set = {t.strip().lower() for t in raw_bl.split(",") if t.strip()}

            resolved_folder = resolve_output_dir(output_dir)
            os.makedirs(resolved_folder, exist_ok=True)

            for i in range(total_items):
                cap_text = str(caption_list[i]) if i < len(caption_list) else ""
                tag_text = str(tags_list_in[i]) if i < len(tags_list_in) else ""
                neg_text = str(negative_list[i]) if i < len(negative_list) else ""
                curr_img = img_list[i] if i < len(img_list) else (img_list[0] if img_list else None)

                # ── 5. Perceptual Deduplication (Fingerprint) ─────────────
                if deduplicate_images and curr_img is not None:
                    curr_hash = _compute_image_fingerprint(curr_img)
                    is_duplicate = False
                    for prev_h in self.session_hashes:
                        sim = _fingerprint_similarity(curr_hash, prev_h)
                        if sim >= similarity_threshold:
                            print(f"[STOIQO Dataset] Skipping duplicate frame #{i + 1} (similarity: {sim * 100:.1f}%)")
                            is_duplicate = True
                            break

                    if is_duplicate:
                        continue
                    self.session_hashes.append(curr_hash)

                # ── 6. Process and Filter Tags ─────────────────────────────
                raw_tags = [t.strip() for t in tag_text.split(",") if t.strip()]
                unique_tags = []
                seen_tags = set()

                for t in raw_tags:
                    clean_t = re.sub(r"^[(\[{]+|[)\]}]+$", "", t).strip()
                    norm_t = clean_t.lower().replace("_", " ")
                    if norm_t and norm_t not in bl_set and norm_t not in seen_tags:
                        seen_tags.add(norm_t)
                        unique_tags.append(clean_t)

                # Ensure trigger word is present if configured
                if clean_trigger:
                    norm_trig = clean_trigger.lower().replace("_", " ")
                    if norm_trig in seen_tags:
                        unique_tags = [t for t in unique_tags if t.lower().replace("_", " ") != norm_trig]
                    unique_tags.insert(0, clean_trigger)

                # Shuffle non-pinned tags deterministically
                if shuffle_tags and len(unique_tags) > keep_tokens:
                    pinned = unique_tags[:keep_tokens]
                    to_shuffle = unique_tags[keep_tokens:]
                    rng = random.Random(seed + i)
                    rng.shuffle(to_shuffle)
                    unique_tags = pinned + to_shuffle

                sep = tag_separator.replace("\\n", "\n").replace(" (Newline)", "")
                final_tags = sep.join(unique_tags)

                # ── 7. Process Caption (Prose) ─────────────────────────────
                final_caption = cap_text
                if bl_set and final_caption:
                    for bad in bl_set:
                        pattern = re.compile(rf"\b{re.escape(bad)}\b", re.IGNORECASE)
                        final_caption = pattern.sub("", final_caption)
                    final_caption = re.sub(r"\s*,\s*,\s*", ", ", final_caption)
                    final_caption = re.sub(r"[ \t]+", " ", final_caption).strip(" ,")

                if clean_trigger and final_caption and not final_caption.lower().startswith(clean_trigger.lower()):
                    final_caption = f"{clean_trigger}, {final_caption}"

                # ── 8. Format Primary Training Text ────────────────────────
                if caption_format == "Booru Tags (.txt)":
                    primary_training_text = final_tags
                elif caption_format == "Trigger + Tags (.txt)":
                    if clean_trigger and not final_tags.startswith(clean_trigger):
                        primary_training_text = f"{clean_trigger}, {final_tags}" if final_tags else clean_trigger
                    else:
                        primary_training_text = final_tags
                elif caption_format == "Combined (Trigger + Tags + Prose)":
                    parts = []
                    if final_tags:
                        parts.append(final_tags)
                    if final_caption and final_caption != final_tags:
                        parts.append(final_caption)
                    primary_training_text = ". ".join(parts)
                else:
                    # Prose Caption (.txt) or dual mode
                    primary_training_text = final_caption if final_caption else final_tags

                out_captions.append(primary_training_text)
                out_tags.append(final_tags)
                out_negatives.append(neg_text)
                if curr_img is not None:
                    out_images.append(curr_img)

                # ── 9. Resolve Destination Filename Stem (SSOT Precedence) ────────────
                # Precedence:
                # 1. Explicit filename input socket (authoritative per-frame override)
                # 2. Upstream image metadata via use_original_filename (if detected)
                # 3. Deterministic fallback_prefix + sequential counter
                original_name = None
                if i < len(filename_list) and filename_list[i] and filename_list[i].strip():
                    fname = filename_list[i].strip()
                    if "." in fname:
                        fname = os.path.splitext(fname)[0]
                    original_name = fname
                elif use_original_filename and curr_img is not None:
                    detected = get_original_filename(prompt, unique_id, "image")
                    if detected:
                        original_name = detected

                if original_name:
                    stem = original_name
                else:
                    prefix = fallback_prefix.strip() or "dataset_item"
                    counter = i + 1
                    while True:
                        candidate_stem = f"{prefix}_{counter:04d}"
                        txt_check = os.path.join(resolved_folder, f"{candidate_stem}.txt")
                        png_check = os.path.join(resolved_folder, f"{candidate_stem}.png")
                        if not os.path.exists(txt_check) and not os.path.exists(png_check):
                            stem = candidate_stem
                            break
                        counter += 1

                # ── 10. Save Image (if requested) ───────────────────────────
                img_width, img_height = 0, 0
                if save_image and curr_img is not None:
                    pil_img = _tensor_to_pil(curr_img)
                    img_width, img_height = pil_img.size

                    if "PNG" in image_format:
                        img_filename = f"{stem}.png"
                        pil_img.save(os.path.join(resolved_folder, img_filename), format="PNG", compress_level=4)
                    elif "WEBP" in image_format:
                        img_filename = f"{stem}.webp"
                        pil_img.save(os.path.join(resolved_folder, img_filename), format="WEBP", quality=95)
                    else:
                        img_filename = f"{stem}.jpg"
                        pil_img.save(os.path.join(resolved_folder, img_filename), format="JPEG", quality=95)
                    print(f"[STOIQO Dataset] Saved image: {os.path.join(resolved_folder, img_filename)}")

                # ── 11. Save Captions & JSON Manifest ───────────────────────
                if save_txt:
                    txt_path = os.path.join(resolved_folder, f"{stem}.txt")
                    with open(txt_path, "w", encoding="utf-8") as tf:
                        tf.write(primary_training_text)
                    print(f"[STOIQO Dataset] Saved caption: {txt_path}")

                    # Dual file mode: save tags separately only if explicitly selected
                    if caption_format == "Prose in .txt, Tags in _tags.txt" and final_tags:
                        tags_txt_path = os.path.join(resolved_folder, f"{stem}_tags.txt")
                        with open(tags_txt_path, "w", encoding="utf-8") as tf:
                            tf.write(final_tags)

                if save_json_metadata:
                    meta = build_dataset_manifest(
                        caption=primary_training_text,
                        tags=final_tags,
                        negative=neg_text,
                        tags_list=unique_tags,
                        trigger_word=clean_trigger,
                        shuffle_tags=shuffle_tags,
                        seed=seed + i,
                        width=img_width,
                        height=img_height,
                    )
                    json_path = os.path.join(resolved_folder, f"{stem}.json")
                    with open(json_path, "w", encoding="utf-8") as jf:
                        import json
                        json.dump(meta, jf, indent=2, ensure_ascii=False)
                    print(f"[STOIQO Dataset] Saved metadata: {json_path}")

            final_img_out = out_images if out_images else (img_list if img_list else [torch.zeros((1, 64, 64, 3), dtype=torch.float32)])

            return inject_telemetry(
                (out_captions, out_tags, out_negatives, final_img_out),
                timer.get_stats(),
            )
