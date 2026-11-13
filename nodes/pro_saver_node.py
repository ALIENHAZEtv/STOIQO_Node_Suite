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

try:
    import folder_paths
except ImportError:
    import tempfile

    class _MockFolderPaths:
        @staticmethod
        def get_output_directory():
            return "./output"
        @staticmethod
        def get_temp_directory():
            return tempfile.gettempdir()
        @staticmethod
        def get_save_image_path(filename_prefix, output_dir, image_width=0, image_height=0):
            return (output_dir, filename_prefix, 0, "", filename_prefix)
    folder_paths = _MockFolderPaths()


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

    def _resolve_text(val):
        if isinstance(val, str) and val.strip():
            return val.strip()
        if isinstance(val, (list, tuple)) and len(val) >= 2 and prompt_dict:
            src_id = str(val[0])
            src_node = prompt_dict.get(src_id)
            if src_node and isinstance(src_node, dict):
                src_inputs = src_node.get("inputs", {})
                src_type = src_node.get("class_type", "")
                if "TextConcatenate" in src_type or "Concat" in src_type:
                    collected = []
                    for i in range(1, 9):
                        part = _resolve_text(src_inputs.get(f"text_{i}"))
                        if part:
                            collected.append(part)
                    sep = src_inputs.get("custom_separator") or ", "
                    return sep.join(collected)
                if "PromptGenerator" in src_type:
                    return _resolve_text(src_inputs.get("custom_modifications")) or _resolve_text(src_inputs.get("text_input")) or ""
                if "text" in src_inputs:
                    return _resolve_text(src_inputs.get("text"))
        return None

    for node_id, node_data in prompt_dict.items():
        if not isinstance(node_data, dict):
            continue
        class_type = node_data.get("class_type", "")
        inputs = node_data.get("inputs", {})

        # KSampler & StoiqoTurboSampler inspection
        if "Sampler" in class_type or "KSampler" in class_type or "TurboSampler" in class_type:
            if meta["seed"] is None:
                meta["seed"] = inputs.get("seed") or inputs.get("noise_seed")
                if isinstance(meta["seed"], (list, tuple)) and prompt_dict:
                    src_node = prompt_dict.get(str(meta["seed"][0]))
                    if src_node:
                        meta["seed"] = src_node.get("inputs", {}).get("seed")
            if meta["steps"] is None:
                meta["steps"] = inputs.get("steps")
            if meta["cfg"] is None:
                meta["cfg"] = inputs.get("cfg")
            if meta["sampler_name"] is None:
                meta["sampler_name"] = inputs.get("sampler_name")
            if meta["scheduler"] is None:
                meta["scheduler"] = inputs.get("scheduler")
            if meta["positive_prompt"] is None:
                pos = _resolve_text(inputs.get("positive") or inputs.get("positive_prompt"))
                if pos:
                    meta["positive_prompt"] = pos
            if meta["negative_prompt"] is None:
                neg = _resolve_text(inputs.get("negative") or inputs.get("negative_prompt"))
                if neg:
                    meta["negative_prompt"] = neg

        # Model Loader inspection
        if "ModelLoader" in class_type or "CheckpointLoader" in class_type or "UNETLoader" in class_type:
            if meta["model_name"] is None:
                model = inputs.get("model_name") or inputs.get("ckpt_name") or inputs.get("unet_name")
                if model:
                    meta["model_name"] = os.path.splitext(os.path.basename(str(model)))[0]

        # Seed Controller inspection
        if "SeedController" in class_type or "Seed" in class_type:
            if meta["seed"] is None and "seed" in inputs:
                meta["seed"] = inputs.get("seed")

        # Standard CLIPTextEncode inspection
        if "CLIPTextEncode" in class_type or "TextEncode" in class_type:
            txt = _resolve_text(inputs.get("text"))
            if txt:
                node_title = str(node_data.get("_meta", {}).get("title", "")).lower()
                if "negative" in node_title:
                    if meta["negative_prompt"] is None:
                        meta["negative_prompt"] = txt
                else:
                    if meta["positive_prompt"] is None:
                        meta["positive_prompt"] = txt

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


def _format_a1111_parameters(meta, w, h):
    """Formats standard A1111/Civitai parameter string for EXIF ImageDescription and PNG parameters."""
    pos = (meta.get("positive_prompt") or "").strip()
    neg = (meta.get("negative_prompt") or "").strip()
    parts = []
    if pos:
        parts.append(pos)
    if neg:
        parts.append(f"Negative prompt: {neg}")

    details = []
    if meta.get("steps") is not None:
        details.append(f"Steps: {meta['steps']}")
    if meta.get("sampler_name") is not None:
        details.append(f"Sampler: {meta['sampler_name']}")
    if meta.get("cfg") is not None:
        details.append(f"CFG scale: {meta['cfg']}")
    if meta.get("seed") is not None:
        details.append(f"Seed: {meta['seed']}")
    details.append(f"Size: {w}x{h}")
    if meta.get("model_name"):
        details.append(f"Model: {meta['model_name']}")

    if details:
        parts.append(", ".join(details))
    return "\n".join(parts)


class StoiqoProImageSaverNode:
    """
    [STOIQO] Pro Image Saver & Metadata Hub
    High-efficiency image saver with multi-format support, EXIF injection, Privacy Mode, and zero preview clutter.
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
                "save_workflow": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Embed full ComfyUI graph metadata and A1111/Civitai parameters into PNG/EXIF or JSON sidecar.",
                    },
                ),
                "privacy_mode": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Privacy Mode: When enabled, strips 100% of metadata (prompts, seeds, models, workflow graphs, and EXIF) for safe, lightweight public web publishing.",
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
    CATEGORY = "STOIQO"

    def save_images_pro(
        self,
        images,
        filename_prefix="%date%_render",
        format="PNG (Lossless)",
        quality=90,
        subfolder="StoiqoCreations/%date%",
        sidecar_metadata="Both (.json + .txt)",
        save_workflow=True,
        privacy_mode=False,
        prompt_text=None,
        negative_text=None,
        prompt=None,
        extra_pnginfo=None,
        **kwargs,
    ):
        extracted_meta = _extract_graph_metadata(prompt)
        if prompt_text and str(prompt_text).strip():
            extracted_meta["positive_prompt"] = str(prompt_text).strip()
        if negative_text and str(negative_text).strip():
            extracted_meta["negative_prompt"] = str(negative_text).strip()

        # If Privacy Mode is active, strip all sensitive generation data
        if privacy_mode:
            save_workflow = False
            extracted_meta["positive_prompt"] = ""
            extracted_meta["negative_prompt"] = ""
            extracted_meta["seed"] = None
            extracted_meta["steps"] = None
            extracted_meta["cfg"] = None
            extracted_meta["sampler_name"] = None
            extracted_meta["model_name"] = None

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
            arr = (img_tensor.clamp(0.0, 1.0).mul(255).to(torch.uint8)).cpu().numpy()
            pil_img = Image.fromarray(arr)
            cur_w, cur_h = pil_img.size

            # Resolve filename with counter
            raw_filename = _resolve_tokens(filename_prefix, cur_w, cur_h, extracted_meta, counter=counter)
            if "%counter%" not in filename_prefix:
                raw_filename = f"{raw_filename}_{counter:04d}"

            file_name = f"{raw_filename}{ext}"
            file_path = os.path.join(target_dir, file_name)

            # Metadata prep
            pnginfo = None
            exif = None

            if not privacy_mode and save_workflow:
                a1111_params = _format_a1111_parameters(extracted_meta, cur_w, cur_h)

                if pil_fmt == "PNG":
                    pnginfo = PngInfo()
                    if prompt is not None:
                        pnginfo.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for k, v in extra_pnginfo.items():
                            pnginfo.add_text(k, json.dumps(v))
                    if a1111_params:
                        pnginfo.add_text("parameters", a1111_params)
                else:
                    # Injected EXIF for WEBP and JPEG (Civitai, A1111 & ComfyUI readable)
                    exif = pil_img.getexif()
                    if a1111_params:
                        exif[0x010E] = a1111_params  # ImageDescription
                    user_comment_data = {}
                    if prompt is not None:
                        user_comment_data["prompt"] = prompt
                    if extra_pnginfo is not None and "workflow" in extra_pnginfo:
                        user_comment_data["workflow"] = extra_pnginfo["workflow"]
                    if user_comment_data:
                        comment_bytes = b"ASCII\x00\x00\x00" + json.dumps(user_comment_data, ensure_ascii=False).encode("utf-8")
                        exif[0x9286] = comment_bytes  # UserComment

            # Save according to format
            if pil_fmt == "PNG":
                comp_level = max(1, min(9, int((100 - quality) / 10)))
                pil_img.save(file_path, format="PNG", pnginfo=pnginfo, compress_level=comp_level)
            elif pil_fmt == "WEBP":
                save_kwargs = {"quality": quality, "lossless": (quality >= 100)}
                if exif and len(exif) > 0 and not privacy_mode:
                    save_kwargs["exif"] = exif
                pil_img.save(file_path, format="WEBP", **save_kwargs)
            elif pil_fmt == "JPEG":
                rgb_pil = pil_img.convert("RGB")
                save_kwargs = {"quality": quality, "subsampling": 0}
                if exif and len(exif) > 0 and not privacy_mode:
                    save_kwargs["exif"] = exif
                rgb_pil.save(file_path, format="JPEG", **save_kwargs)

            # File size calculation
            file_bytes = os.path.getsize(file_path)
            size_mb = file_bytes / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB" if size_mb >= 1.0 else f"{file_bytes / 1024:.1f} KB"

            # Sidecar generation
            if sidecar_metadata in ("JSON (.json)", "Both (.json + .txt)"):
                if privacy_mode:
                    sidecar_data = {
                        "filename": file_name,
                        "resolution": f"{cur_w}x{cur_h}",
                        "file_size": size_str,
                        "format": pil_fmt,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "privacy_mode": True,
                    }
                else:
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
                        "privacy_mode": False,
                    }
                    if save_workflow and extra_pnginfo:
                        sidecar_data["workflow"] = extra_pnginfo.get("workflow")

                json_path = os.path.splitext(file_path)[0] + ".json"
                try:
                    with open(json_path, "w", encoding="utf-8") as jf:
                        json.dump(sidecar_data, jf, indent=2, ensure_ascii=False)
                except Exception as e:
                    print(f"[STOIQO Pro Saver] Warning saving JSON sidecar: {e}")

            if not privacy_mode and sidecar_metadata in ("TXT Caption (.txt)", "Both (.json + .txt)"):
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
                "privacy_mode": privacy_mode,
            })
            counter += 1

        ui_images = [
            {
                "filename": s["filename"],
                "subfolder": s["subfolder"],
                "type": self.type,
            }
            for s in saved_infos
        ]

        metadata_dump = json.dumps(saved_infos, indent=2)

        return {
            "ui": {
                "images": ui_images,
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
