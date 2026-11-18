"""
[STOIQO] Dynamic Prompt Engine CRUD API
=======================================
Provides complete Create, Read, Update, Delete (CRUD) operations
for Cognitive Personas (Layer 1), Prompt Types (Layer 2), and Artistic Styles (Layer 3).
Directly reads and modifies modular .md files with YAML frontmatter.
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional, Tuple

from .loader import (
    IMAGE_DIR,
    PERSONAS_DIR,
    TYPES_DIR,
    STYLES_DIR,
    parse_markdown_with_frontmatter,
    reload_image_definitions,
    SYSTEM_PERSONAS,
    PROMPT_TYPES,
    ARTISTIC_STYLES,
)

logger = logging.getLogger(__name__)

# Protected core definitions that cannot be deleted
CORE_PROTECTED = {
    "_contract.md",
    "Auto-Detect / Balanced",
    "Auto-Detect / Preserve Original",
    "Generative Vision Engine",
    "Multi-Image Synthesis Engine",
    "Cinematic & Video Director",
    "Dataset & LoRA Annotator",
    "SeedVR2 Upscale Guide",
    "Custom (Manual Override)",
    "Detailed Narrative",
    "Short Summary",
    "Structured Categories",
    "Booru / Comma-Separated Tags",
    "Tags & Keywords",
    "Cinematic Video Script",
    "Photorealistic (Modern Digital RAW)",
    "Analog Film (35mm Vintage Stock)",
    "Cinematic Still (Anamorphic Movie)",
    "Studio Portrait (Professional Editorial)",
    "Anime & Manga (2D Cel-shaded)",
    "Comic Book & Graphic Novel (Ink & Halftone)",
    "Pencil Sketch & Charcoal Drawing",
    "3D Digital Render & CGI (PBR)",
    "Digital Concept Art & Illustration",
    "Oil Painting & Classical Fine Art",
}


def _resolve_kind_dir(kind: str) -> str:
    k = kind.lower().strip()
    if k in ("main_prompts", "main_guidelines", "persona", "personas", "system_prompt", "layer1"):
        return PERSONAS_DIR
    elif k in ("type_prompts", "type_guidelines", "type", "types", "prompt_type", "layer2"):
        return TYPES_DIR
    elif k in ("style_prompts", "style_guidelines", "style", "styles", "prompt_style", "artistic_style", "layer3"):
        return STYLES_DIR
    else:
        raise ValueError(f"Unknown definition kind: '{kind}'. Expected 'main_prompts', 'type_prompts', or 'style_prompts'.")


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s-]+", "_", text).strip("_")
    return text or "custom_definition"


def _find_file_by_name(directory: str, target_name: str) -> Optional[Tuple[str, Dict[str, Any], str]]:
    """Scans directory and returns (filepath, frontmatter, body) if name matches."""
    if not os.path.isdir(directory):
        return None

    target_clean = target_name.strip().lower()
    for fn in os.listdir(directory):
        if not fn.endswith(".md") or fn.startswith("_"):
            continue
        fp = os.path.join(directory, fn)
        fm, body = parse_markdown_with_frontmatter(fp)
        fn_name = str(fm.get("name", "")).strip().lower()
        if fn_name == target_clean:
            return fp, fm, body
        # Check aliases
        for alias in fm.get("aliases", []):
            if str(alias).strip().lower() == target_clean:
                return fp, fm, body

    return None


def list_definitions(kind: str) -> List[Dict[str, Any]]:
    """Returns all definitions for a given layer kind."""
    target_dir = _resolve_kind_dir(kind)
    items = []
    if not os.path.isdir(target_dir):
        return items

    for fn in os.listdir(target_dir):
        if not fn.endswith(".md") or fn.startswith("_"):
            continue
        fp = os.path.join(target_dir, fn)
        fm, _ = parse_markdown_with_frontmatter(fp)
        name = fm.get("name", fn.replace(".md", ""))
        category = fm.get("category", "")
        order = fm.get("order", 999)
        is_core = name in CORE_PROTECTED or fn in CORE_PROTECTED or order < 50
        items.append({
            "name": name,
            "category": category,
            "order": order,
            "filename": fn,
            "is_core": is_core,
            "aliases": fm.get("aliases", []),
        })

    items.sort(key=lambda x: (x["order"], x["name"].lower()))
    return items


def get_definition(kind: str, name: str) -> Dict[str, Any]:
    """Retrieves full definition (frontmatter + body) by name."""
    target_dir = _resolve_kind_dir(kind)
    match = _find_file_by_name(target_dir, name)
    if not match:
        return {
            "status": "error",
            "message": f"Definition '{name}' not found in '{kind}'.",
        }

    fp, fm, body = match
    fn = os.path.basename(fp)
    is_core = name in CORE_PROTECTED or fn in CORE_PROTECTED or fm.get("order", 999) < 50

    return {
        "status": "ok",
        "kind": kind,
        "name": fm.get("name", name),
        "filename": fn,
        "frontmatter": fm,
        "body": body,
        "is_core": is_core,
    }


def save_definition(
    kind: str,
    name: str,
    body: str,
    frontmatter: Optional[Dict[str, Any]] = None,
    original_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates or updates a definition markdown file.
    If original_name is supplied and different from name, safely renames/moves file.
    """
    target_dir = _resolve_kind_dir(kind)
    os.makedirs(target_dir, exist_ok=True)

    name = name.strip()
    if not name:
        return {"status": "error", "message": "Definition name cannot be empty."}

    fm = dict(frontmatter or {})
    fm["name"] = name
    if "order" not in fm:
        fm["order"] = 200

    existing_match = None
    if original_name and original_name.strip():
        existing_match = _find_file_by_name(target_dir, original_name.strip())

    if not existing_match:
        existing_match = _find_file_by_name(target_dir, name)

    if existing_match:
        target_fp, old_fm, _ = existing_match
        # If renamed and target file doesn't match slug, determine new target
        if original_name and original_name.strip() != name:
            slug = _slugify(name.replace("//", "_"))
            new_fp = os.path.join(target_dir, f"{slug}.md")
            # Don't delete old file if it was protected core
            if original_name not in CORE_PROTECTED and os.path.basename(target_fp) not in CORE_PROTECTED:
                try:
                    os.remove(target_fp)
                except Exception as e:
                    logger.warning(f"[STOIQO] Could not remove old file {target_fp}: {e}")
            target_fp = new_fp
    else:
        slug = _slugify(name.replace("//", "_"))
        target_fp = os.path.join(target_dir, f"{slug}.md")
        idx = 2
        base_fp = target_fp
        while os.path.exists(target_fp):
            target_fp = os.path.join(target_dir, f"{slug}_{idx}.md")
            idx += 1

    # Format YAML Frontmatter
    lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                lines.append(f'  - "{item}"')
        elif isinstance(v, (int, float)):
            lines.append(f"{k}: {v}")
        elif isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        else:
            lines.append(f'{k}: "{v}"')
    lines.append("---")
    lines.append("")
    lines.append(body.strip())
    lines.append("")

    content = "\n".join(lines)
    try:
        with open(target_fp, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"[STOIQO] Failed to write definition file {target_fp}: {e}")
        return {"status": "error", "message": f"Failed to write file: {e}"}

    # Trigger dynamic SSOT reload
    reload_image_definitions()

    from .loader import SYSTEM_PERSONAS as SP, PROMPT_TYPES as PT, ARTISTIC_STYLES as AS

    return {
        "status": "ok",
        "kind": kind,
        "name": name,
        "filename": os.path.basename(target_fp),
        "message": f"Successfully saved '{name}'",
        "choices": {
            "system_personas": SP,
            "prompt_types": PT,
            "artistic_styles": AS,
        },
    }


def delete_definition(kind: str, name: str) -> Dict[str, Any]:
    """Deletes a custom definition markdown file, protecting core presets."""
    name = name.strip()
    if name in CORE_PROTECTED:
        return {
            "status": "error",
            "message": f"'{name}' is a core protected template and cannot be deleted.",
        }

    target_dir = _resolve_kind_dir(kind)
    match = _find_file_by_name(target_dir, name)
    if not match:
        return {
            "status": "error",
            "message": f"Definition '{name}' not found.",
        }

    fp, fm, _ = match
    fn = os.path.basename(fp)
    if fn in CORE_PROTECTED or fm.get("order", 999) < 50:
        return {
            "status": "error",
            "message": f"'{name}' is a core protected template and cannot be deleted.",
        }

    try:
        os.remove(fp)
    except Exception as e:
        logger.error(f"[STOIQO] Failed to delete {fp}: {e}")
        return {"status": "error", "message": f"Failed to delete file: {e}"}

    # Trigger dynamic SSOT reload
    reload_image_definitions()

    from .loader import SYSTEM_PERSONAS as SP, PROMPT_TYPES as PT, ARTISTIC_STYLES as AS

    return {
        "status": "ok",
        "kind": kind,
        "name": name,
        "message": f"Successfully deleted '{name}'",
        "choices": {
            "system_personas": SP,
            "prompt_types": PT,
            "artistic_styles": AS,
        },
    }
