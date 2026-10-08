"""
[STOIQO] Pro Image Saver & Metadata Hub
Advanced image exporter with multi-format support (PNG/WEBP/JPEG),
dynamic folder/filename tokens, JSON/TXT sidecars, and rich pass-through outputs.
"""

import os
import json
import re
from datetime import datetime
import numpy as np
import torch
from PIL import Image
from PIL.PngImagePlugin import PngInfo

import folder_paths


def _extract_graph_metadata(prompt_dict):
    """Extracts generation parameters from the ComfyUI prompt graph if available."""
    meta = {
        "seed": None,
        "steps": None,
        "cfg": None,
        "sampler_name": None,
        "scheduler": None,
        "model_name": None,
        "positive_prompt": None,
        "negative_prompt": None,
    }

    if not isinstance(prompt_dict, dict):
        return meta

    for node_id, node_data in prompt_dict.items():
        if not isinstance(node_data, dict):
            continue
        class_type = node_data.get("class_type", "")
        inputs = node_data.get("inputs", {})

        # KSampler inspection
        if "Sampler" in class_type or "KSampler" in class_type:
            if meta["seed"] is None:
                meta["seed"] = inputs.get("seed") or inputs.get("noise_seed")
            if meta["steps"] is None:
                meta["steps"] = inputs.get("steps")
            if meta["cfg"] is None:
                meta["cfg"] = inputs.get("cfg")
            if meta["sampler_name"] is None:
                meta["sampler_name"] = inputs.get("sampler_name")
            if meta["scheduler"] is None:
                meta["scheduler"] = inputs.get("scheduler")

        # Model Loader inspection
        if "CheckpointLoader" in class_type or "UNETLoader" in class_type:
            if meta["model_name"] is None:
                model = inputs.get("ckpt_name") or inputs.get("unet_name") or inputs.get("model_name")
                if model:
                    meta["model_name"] = os.path.splitext(os.path.basename(str(model)))[0]

        # Text prompt inspection
        if "CLIPTextEncode" in class_type or "TextEncode" in class_type:
            txt = inputs.get("text")
            if isinstance(txt, str) and txt.strip():
                node_title = str(node_data.get("_meta", {}).get("title", "")).lower()
                if "negative" in node_title:
                    if meta["negative_prompt"] is None:
                        meta["negative_prompt"] = txt.strip()
                else:
                    if meta["positive_prompt"] is None:
                        meta["positive_prompt"] = txt.strip()

    return meta


def _resolve_tokens(pattern, width, height, meta, counter=1):
    """Substitutes dynamic placeholders in filename or subfolder paths."""
    now = datetime.now()
    resolved = pattern

    # Date and Time tokens
    resolved = resolved.replace("%date%", now.strftime("%Y-%m-%d"))
    resolved = resolved.replace("%time%", now.strftime("%H%M%S"))
    resolved = resolved.replace("%year%", now.strftime("%Y"))
    resolved = resolved.replace("%month%", now.strftime("%m"))
    resolved = resolved.replace("%day%", now.strftime("%d"))
    resolved = resolved.replace("%hour%", now.strftime("%H"))
    resolved = resolved.replace("%minute%", now.strftime("%M"))

    # Dimension tokens
    resolved = resolved.replace("%width%", str(width))
    resolved = resolved.replace("%height%", str(height))

    # Meta tokens
    resolved = resolved.replace("%seed%", str(meta.get("seed") or "seed"))
    resolved = resolved.replace("%steps%", str(meta.get("steps") or "steps"))
    resolved = resolved.replace("%cfg%", str(meta.get("cfg") or "cfg"))
    resolved = resolved.replace("%sampler%", str(meta.get("sampler_name") or "sampler"))
    resolved = resolved.replace("%model%", str(meta.get("model_name") or "model"))
    resolved = resolved.replace("%counter%", f"{counter:05d}")

    # Clean redundant slashes or illegal characters
    resolved = re.sub(r"[<>:\"|?*]", "_", resolved)
    return resolved


class StoiqoProImageSaverNode:
    """
    [STOIQO] Pro Image Saver & Metadata Hub
    High-efficiency image saver with multi-format support, sidecars, and zero preview clutter.
    """

    FORMAT_OPTIONS = [
        "PNG (Lossless)",
        "WEBP (Quality)",
        "JPEG (Standard)",
    ]

    SIDECAR_OPTIONS = [
        "Both (.json + .txt)",
        "JSON (.json)",
        "TXT Caption (.txt)",
        "None",
    ]

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "Image tensor(s) to save."}),
                "filename_prefix": (
                    "STRING",
                    {
                        "default": "%date%_render",
                        "tooltip": "Filename pattern. Supports %date%, %time%, %seed%, %width%, %height%, %counter%",
                    },
                ),
                "format": (
                    cls.FORMAT_OPTIONS,
                    {
                        "default": cls.FORMAT_OPTIONS[0],
                        "tooltip": "Export image format (PNG, WEBP, or JPEG).",
                    },
                ),
                "quality": (
                    "INT",
                    {
                        "default": 90,
                        "min": 1,
                        "max": 100,
                        "step": 1,
                        "tooltip": "Quality percentage for WEBP/JPEG or compression mapping for PNG.",
                    },
                ),
            },
            "optional": {
                "subfolder": (
                    "STRING",
                    {
                        "default": "StoiqoCreations/%date%",
                        "tooltip": "Subfolder relative to ComfyUI output directory. Supports %date%, %year%, etc.",
                    },
                ),
                "sidecar_metadata": (
                    cls.SIDECAR_OPTIONS,
                    {
                        "default": cls.SIDECAR_OPTIONS[0],
                        "tooltip": "Generate human-readable sidecar metadata files alongside the image.",
                    },
                ),
                "prompt_text": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Optional prompt text to write into TXT caption and JSON metadata.",
                    },
                ),
                "negative_text": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Optional negative prompt text.",
                    },
                ),
                "save_workflow": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Embed full ComfyUI graph metadata into PNG chunks or JSON sidecar.",
                    },
                ),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("images", "file_path", "filename", "folder_path", "metadata_json")
    FUNCTION = "save_images_pro"
    OUTPUT_NODE = True
    CATEGORY = "STOIQO/Loaders & IO"

    def save_images_pro(
        self,
        images,
        filename_prefix="%date%_render",
        format="PNG (Lossless)",
        quality=90,
        subfolder="StoiqoCreations/%date%",
        sidecar_metadata="Both (.json + .txt)",
        prompt_text="",
        negative_text="",
        save_workflow=True,
        prompt=None,
        extra_pnginfo=None,
    ):
        extracted_meta = _extract_graph_metadata(prompt)
        if prompt_text.strip():
            extracted_meta["positive_prompt"] = prompt_text.strip()
        if negative_text.strip():
            extracted_meta["negative_prompt"] = negative_text.strip()

        # Format extension & PIL format name
        if "WEBP" in format:
            ext = ".webp"
            pil_fmt = "WEBP"
        elif "JPEG" in format:
            ext = ".jpg"
            pil_fmt = "JPEG"
        else:
            ext = ".png"
            pil_fmt = "PNG"

        # Determine target folder
        w = images[0].shape[2]
        h = images[0].shape[1]
        resolved_subfolder = _resolve_tokens(subfolder, w, h, extracted_meta)
        target_dir = os.path.join(self.output_dir, resolved_subfolder)
        os.makedirs(target_dir, exist_ok=True)

        saved_files = []
        saved_infos = []
        first_file_path = ""
        first_file_name = ""

        # Find starting counter in target directory
        pattern_base = _resolve_tokens(filename_prefix, w, h, extracted_meta, counter=1)
        base_clean = pattern_base.replace("%counter%", "")
        existing = [f for f in os.listdir(target_dir) if f.startswith(base_clean) and f.endswith(ext)]
        counter = len(existing) + 1

        for batch_idx, img_tensor in enumerate(images):
            arr = (255.0 * img_tensor.cpu().numpy()).clip(0, 255).astype(np.uint8)
            pil_img = Image.fromarray(arr)
            cur_w, cur_h = pil_img.size

            # Resolve filename with counter
            raw_filename = _resolve_tokens(filename_prefix, cur_w, cur_h, extracted_meta, counter=counter)
            if "%counter%" not in filename_prefix:
                raw_filename = f"{raw_filename}_{counter:04d}"

            file_name = f"{raw_filename}{ext}"
            file_path = os.path.join(target_dir, file_name)

            # Metadata prep
            pnginfo = PngInfo() if pil_fmt == "PNG" and save_workflow else None
            if pnginfo and save_workflow:
                if prompt is not None:
                    pnginfo.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for k, v in extra_pnginfo.items():
                        pnginfo.add_text(k, json.dumps(v))
                if extracted_meta["positive_prompt"]:
                    pnginfo.add_text("parameters", extracted_meta["positive_prompt"])

            # Save according to format
            if pil_fmt == "PNG":
                # Quality 1-100 maps to compress_level 9 to 1 (inverted: higher quality = faster/lower compression)
                comp_level = max(1, min(9, int((100 - quality) / 10)))
                pil_img.save(file_path, format="PNG", pnginfo=pnginfo, compress_level=comp_level)
            elif pil_fmt == "WEBP":
                pil_img.save(file_path, format="WEBP", quality=quality, lossless=(quality >= 100))
            elif pil_fmt == "JPEG":
                rgb_pil = pil_img.convert("RGB")
                rgb_pil.save(file_path, format="JPEG", quality=quality, subsampling=0)

            # File size calculation
            file_bytes = os.path.getsize(file_path)
            size_mb = file_bytes / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB" if size_mb >= 1.0 else f"{file_bytes / 1024:.1f} KB"

            # Sidecar generation
            if sidecar_metadata in ("JSON (.json)", "Both (.json + .txt)"):
                sidecar_data = {
                    "filename": file_name,
                    "resolution": f"{cur_w}x{cur_h}",
                    "file_size": size_str,
                    "format": pil_fmt,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "positive_prompt": extracted_meta["positive_prompt"] or "",
                    "negative_prompt": extracted_meta["negative_prompt"] or "",
                    "generation_parameters": {
                        "seed": extracted_meta["seed"],
                        "steps": extracted_meta["steps"],
                        "cfg": extracted_meta["cfg"],
                        "sampler": extracted_meta["sampler_name"],
                        "scheduler": extracted_meta["scheduler"],
                        "model": extracted_meta["model_name"],
                    },
                }
                if save_workflow and extra_pnginfo:
                    sidecar_data["workflow"] = extra_pnginfo.get("workflow")

                json_path = os.path.splitext(file_path)[0] + ".json"
                try:
                    with open(json_path, "w", encoding="utf-8") as jf:
                        json.dump(sidecar_data, jf, indent=2, ensure_ascii=False)
                except Exception as e:
                    print(f"[STOIQO Pro Saver] Warning saving JSON sidecar: {e}")

            if sidecar_metadata in ("TXT Caption (.txt)", "Both (.json + .txt)"):
                caption_text = extracted_meta["positive_prompt"] or ""
                txt_path = os.path.splitext(file_path)[0] + ".txt"
                try:
                    with open(txt_path, "w", encoding="utf-8") as tf:
                        tf.write(caption_text)
                except Exception as e:
                    print(f"[STOIQO Pro Saver] Warning saving TXT caption: {e}")

            if not first_file_path:
                first_file_path = file_path
                first_file_name = file_name

            saved_files.append(file_path)
            saved_infos.append({
                "filename": file_name,
                "filepath": file_path,
                "subfolder": resolved_subfolder,
                "size_str": size_str,
                "width": cur_w,
                "height": cur_h,
                "format": pil_fmt,
            })
            counter += 1

        metadata_dump = json.dumps(saved_infos, indent=2)

        return {
            "ui": {
                "saved_info": saved_infos,
            },
            "result": (
                images,
                first_file_path,
                first_file_name,
                target_dir,
                metadata_dump,
            ),
        }
