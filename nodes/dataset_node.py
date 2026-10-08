"""
[STOIQO] Dataset & LoRA Toolkit Node
"""

import re
import random
import os

try:
    from ..core import (
        save_artifacts,
        build_dataset_manifest,
        get_original_filename,
        resolve_output_dir,
    )
except (ImportError, ValueError):
    from core import (
        save_artifacts,
        build_dataset_manifest,
        get_original_filename,
        resolve_output_dir,
    )

class StoiqoDatasetWriterNode:
    """
    Dataset formatter and artifact saver for LoRA training.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "caption": ("STRING", {"forceInput": True}),
                "tags": ("STRING", {"forceInput": True}),
                "negative": ("STRING", {"forceInput": True}),
                "trigger_word": (
                    "STRING",
                    {
                        "default": "",
                        "placeholder": "e.g. sks_char, ",
                        "tooltip": "Activator keyword pinned at index 0 of every caption file.",
                    },
                ),
                "blacklist_tags": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "watermark, signature, text, username, artist name, blurry, lowres",
                        "tooltip": "Unwanted tags to strip (case-insensitive, applies to Booru tags and prose).",
                    },
                ),
                "shuffle_tags": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Shuffle non-trigger tags deterministically via seed (prevents positional bias in LoRA training).",
                    },
                ),
                "tag_separator": (
                    [", ", "\n (Newline)", " | "],
                    {
                        "default": ", ",
                        "tooltip": "Separator between tags in the final caption. ',' = Kohya/AI-Toolkit standard. Newline = one tag per line. '|' = custom dataset formats.",
                    },
                ),
                "save_txt": ("BOOLEAN", {"default": True, "tooltip": "Save captions as .txt files."}),
                "save_json_metadata": ("BOOLEAN", {"default": False, "tooltip": "Save Kohya/AI-Toolkit compliant JSON manifest."}),
                "output_dir": ("STRING", {"default": "./output/captions", "tooltip": "Output folder (auto-anchored to ComfyUI output directory). Tip: if using Smart Folder Iterator with skip_captioned, set this to the dataset folder to save captions alongside images."}),
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
                        "default": "caption",
                        "placeholder": "Used when the original filename cannot be detected",
                    },
                ),
            },
            "optional": {
                "image": ("IMAGE", {"tooltip": "Connect the original image to detect its filename and resolution for the metadata JSON."}),
                "filename": ("STRING", {"forceInput": True, "tooltip": "Optional filename override (e.g. from Smart Folder Image Iterator)."}),
                "seed": ("INT", {"default": 42, "min": 0, "max": 0xFFFFFFFFFFFFFFFF, "tooltip": "Seed for deterministic tag shuffling."}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("processed_caption", "processed_tags", "processed_negative")
    OUTPUT_IS_LIST = (True, True, True)
    FUNCTION = "process_and_save"
    OUTPUT_NODE = True
    CATEGORY = "STOIQO/Prompt Engine"

    def process_and_save(
        self,
        caption,
        tags,
        negative,
        trigger_word,
        blacklist_tags,
        shuffle_tags,
        tag_separator,
        save_txt,
        save_json_metadata,
        output_dir,
        use_original_filename,
        fallback_prefix,
        image=None,
        filename=None,
        seed=42,
        prompt=None,
        unique_id=None,
    ):
        if not isinstance(caption, list):
            caption = [caption]
        if not isinstance(tags, list):
            tags = [tags]
        if not isinstance(negative, list):
            negative = [negative]

        out_captions = []
        out_tags = []
        out_negatives = []

        trigger_word = str(trigger_word).strip()
        if trigger_word and not trigger_word.endswith(","):
            trigger_word += ","

        bl_tags = [t.strip().lower() for t in blacklist_tags.replace("\n", ",").replace(";", ",").split(",") if t.strip()]

        for i in range(len(caption)):
            cap = str(caption[i])
            tag_str = str(tags[i]) if i < len(tags) else ""
            neg_str = str(negative[i]) if i < len(negative) else ""

            # 1. Process Tags
            current_tags = [t.strip() for t in tag_str.split(",") if t.strip()]
            filtered_tags = [t for t in current_tags if t.lower() not in bl_tags and t.lower().replace("_", " ") not in bl_tags]

            if shuffle_tags and len(filtered_tags) > 1:
                rng = random.Random(seed + i)
                rng.shuffle(filtered_tags)

            if trigger_word:
                trigger_clean = trigger_word.rstrip(",").strip()
                if trigger_clean in filtered_tags:
                    filtered_tags.remove(trigger_clean)
                filtered_tags.insert(0, trigger_clean)

            sep = tag_separator.replace("\\n", "\n").replace(" (Newline)", "")
            final_tags = sep.join(filtered_tags)

            # 2. Process Caption (Prose)
            final_caption = cap
            if bl_tags:
                for bad in bl_tags:
                    pattern = re.compile(rf"\b{re.escape(bad)}\b", re.IGNORECASE)
                    final_caption = pattern.sub("", final_caption)
                final_caption = re.sub(r"\s*,\s*,\s*", ", ", final_caption)
                final_caption = re.sub(r"[ \t]+", " ", final_caption).strip(" ,")

            if trigger_word and not final_caption.lower().startswith(trigger_word.rstrip(",").lower()):
                final_caption = f"{trigger_word.rstrip(',')}, {final_caption}"

            out_captions.append(final_caption)
            out_tags.append(final_tags)
            out_negatives.append(neg_str)

            # 3. Save Artifacts
            if save_txt or save_json_metadata:
                original_name = None
                if filename is not None and str(filename).strip():
                    fname = str(filename).strip()
                    if '.' in fname:
                        fname = os.path.splitext(fname)[0]
                    original_name = fname
                elif use_original_filename and image is not None:
                    name1 = get_original_filename(prompt, unique_id, "image")
                    if name1:
                        original_name = name1

                resolved_folder = resolve_output_dir(output_dir)
                if original_name:
                    stem = original_name
                else:
                    prefix = fallback_prefix.strip() or "caption"
                    candidate_stem = f"{prefix}_{i + 1:04d}" if len(caption) > 1 else prefix
                    candidate_file = os.path.join(resolved_folder, f"{candidate_stem}.txt")
                    candidate_json = os.path.join(resolved_folder, f"{candidate_stem}.json")
                    if os.path.exists(candidate_file) or os.path.exists(candidate_json):
                        counter = 1
                        while True:
                            indexed_stem = f"{prefix}_{counter:04d}"
                            if not os.path.exists(os.path.join(resolved_folder, f"{indexed_stem}.txt")) and not os.path.exists(os.path.join(resolved_folder, f"{indexed_stem}.json")):
                                candidate_stem = indexed_stem
                                break
                            counter += 1
                    stem = candidate_stem

                meta = None
                if save_json_metadata:
                    meta = build_dataset_manifest(
                        caption=final_caption,
                        tags=final_tags,
                        negative=neg_str,
                        tags_list=filtered_tags,
                        trigger_word=trigger_word,
                        shuffle_tags=shuffle_tags,
                        seed=seed + i,
                    )

                save_artifacts(
                    stem=stem,
                    caption=final_caption,
                    tags=final_tags,
                    negative=neg_str,
                    meta=meta,
                    save_txt=save_txt,
                    save_json_metadata=save_json_metadata,
                    output_dir=output_dir,
                )

        return (out_captions, out_tags, out_negatives)
