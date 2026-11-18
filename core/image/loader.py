"""
[STOIQO] Modular Image Prompt Engine — Dynamic Drop-in Loader
Automatically scans and loads Cognitive Personas (Layer 1), Prompt Types (Layer 2),
and Artistic Styles (Layer 3) from disk markdown files with YAML frontmatter.
Allows zero-code extensions by simply dropping .md files into their respective folders.
"""

import os
import re
import logging
from typing import Dict, List, Tuple, Any

try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger(__name__)

IMAGE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PROMPTS_DIR = os.path.join(IMAGE_DIR, "main_prompts")
TYPE_PROMPTS_DIR = os.path.join(IMAGE_DIR, "type_prompts")
STYLE_PROMPTS_DIR = os.path.join(IMAGE_DIR, "style_prompts")
# Direct aliases
PERSONAS_DIR = MAIN_PROMPTS_DIR
TYPES_DIR = TYPE_PROMPTS_DIR
STYLES_DIR = STYLE_PROMPTS_DIR


def parse_markdown_with_frontmatter(file_path: str) -> Tuple[Dict[str, Any], str]:
    """
    Parses a markdown file with optional YAML frontmatter.
    Returns (frontmatter_dict, body_text).
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"[STOIQO] Failed to read {file_path}: {e}")
        return {}, ""

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_raw = parts[1].strip()
            body = parts[2].strip()
            if yaml:
                try:
                    data = yaml.safe_load(fm_raw)
                    if isinstance(data, dict):
                        return data, body
                except Exception as e:
                    logger.warning(f"[STOIQO] YAML parse warning in {file_path}: {e}")

            # Lightweight fallback parser if PyYAML is unavailable or malformed
            data = {}
            current_list_key = None
            for line in fm_raw.splitlines():
                line_str = line.rstrip()
                if not line_str or line_str.startswith("#"):
                    continue
                if line_str.startswith("  - ") and current_list_key:
                    val = line_str[4:].strip().strip('"').strip("'")
                    data[current_list_key].append(val)
                elif ":" in line_str:
                    k, v = line_str.split(":", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if not v:
                        current_list_key = k
                        data[k] = []
                    else:
                        current_list_key = None
                        if v.replace(".", "", 1).isdigit():
                            data[k] = float(v) if "." in v else int(v)
                        else:
                            data[k] = v
            return data, body

    return {}, content.strip()


# ── GLOBAL REGISTRIES & SSOT STATE ───────────────────────────────────────────

SHARED_OUTPUT_CONTRACT = ""
SYSTEM_PERSONAS: List[str] = []
SYSTEM_PROMPT_PRESETS: Dict[str, str] = {}
LEGACY_SYSTEM_PROMPT_ALIASES: Dict[str, str] = {}
PERSONA_SAMPLING_DEFAULTS: Dict[str, Dict[str, Any]] = {}
TEXT_EXPANSION_SYSTEM_PROMPT = ""
MULTI_IMAGE_SYSTEM_PROMPT = ""
BASE_TEXT_EXPANSION_PROMPT = ""
BASE_MULTI_IMAGE_PROMPT = ""
CUSTOM_SYSTEM_PROMPT_KEY = "✏️ Custom (Manual Override)"
SYSTEM_PROMPT_CHOICES: List[str] = []

PROMPT_TYPES: List[str] = []
PROMPT_TYPE_DIRECTIVES: Dict[str, str] = {}
LEGACY_PROMPT_TYPE_ALIASES: Dict[str, str] = {}

ARTISTIC_STYLES: List[str] = []
ARTISTIC_STYLE_DIRECTIVES: Dict[str, str] = {}
NON_PHOTOGRAPHIC_STYLES: Dict[str, Dict[str, str]] = {}
LEGACY_ARTISTIC_STYLE_ALIASES: Dict[str, str] = {}


def _compose_prompt(persona_body: str) -> str:
    """Combines a cognitive persona protocol with the unified output contract."""
    return persona_body.strip() + "\n\n" + SHARED_OUTPUT_CONTRACT


def reload_image_definitions():
    """Scans personas/, types/, and styles/ directories and rebuilds all SSOT registries."""
    global SHARED_OUTPUT_CONTRACT, SYSTEM_PERSONAS, SYSTEM_PROMPT_PRESETS
    global LEGACY_SYSTEM_PROMPT_ALIASES, PERSONA_SAMPLING_DEFAULTS
    global TEXT_EXPANSION_SYSTEM_PROMPT, MULTI_IMAGE_SYSTEM_PROMPT
    global BASE_TEXT_EXPANSION_PROMPT, BASE_MULTI_IMAGE_PROMPT, SYSTEM_PROMPT_CHOICES
    global PROMPT_TYPES, PROMPT_TYPE_DIRECTIVES, LEGACY_PROMPT_TYPE_ALIASES
    global ARTISTIC_STYLES, ARTISTIC_STYLE_DIRECTIVES, NON_PHOTOGRAPHIC_STYLES
    global LEGACY_ARTISTIC_STYLE_ALIASES

    # 1. Load Shared Output Contract
    contract_file = os.path.join(IMAGE_DIR, "_contract.md")
    if not os.path.isfile(contract_file):
        contract_file = os.path.join(PERSONAS_DIR, "_contract.md")
    if os.path.isfile(contract_file):
        with open(contract_file, "r", encoding="utf-8") as f:
            SHARED_OUTPUT_CONTRACT = f.read().strip()
    else:
        SHARED_OUTPUT_CONTRACT = (
            "# INVIOLABLE RULES & OUTPUT PURITY\n"
            "- STRICT ZERO FILLER: Zero conversational text, zero preambles, zero explanations, and zero markdown fences.\n"
            "- ABSOLUTE OUTPUT CONTRACT: Your entire response must consist EXCLUSIVELY of the three XML blocks: <PROMPT>, <TAGS>, and <NEGATIVE>.\n"
            "- NO BUZZWORDS: Never use empty cliches ('masterpiece', '8k', 'photorealistic').\n"
            "- TAGS BUDGET: Keep the <TAGS> block strictly concise and bounded under 75 tokens for CLIP compatibility.\n\n"
            "# REQUIRED OUTPUT CONTRACT\n"
            "Analyze the target input, apply active user custom overrides, and format your response strictly into the three XML blocks: <PROMPT>, <TAGS>, and <NEGATIVE>."
        )

    # 2. Scan and Load Layer 1: Personas
    personas_raw = []
    if os.path.isdir(PERSONAS_DIR):
        for fn in os.listdir(PERSONAS_DIR):
            if fn.endswith(".md") and not fn.startswith("_"):
                fp = os.path.join(PERSONAS_DIR, fn)
                fm, body = parse_markdown_with_frontmatter(fp)
                if fm and "name" in fm:
                    personas_raw.append((fm.get("order", 999), fm, body))

    personas_raw.sort(key=lambda x: x[0])

    new_personas = ["Auto-Detect / Balanced", "None (Raw / No System Prompt)"]
    new_presets = {}
    new_aliases = {
        "Auto-Detect / Balanced": "Auto-Detect / Balanced",
        "None": "None (Raw / No System Prompt)",
        "None (Raw / No System Prompt)": "None (Raw / No System Prompt)",
        "Custom": CUSTOM_SYSTEM_PROMPT_KEY,
        "Custom (Manual Override)": CUSTOM_SYSTEM_PROMPT_KEY,
    }
    new_sampling = {
        "Auto-Detect / Balanced": {
            "temperature": 0.65,
            "max_new_tokens": 1024,
            "top_p": 0.90,
            "top_k": 50,
            "repetition_penalty": 1.15,
        },
        "None (Raw / No System Prompt)": {
            "temperature": 0.65,
            "max_new_tokens": 1024,
            "top_p": 0.90,
            "top_k": 50,
            "repetition_penalty": 1.15,
        },
        "Custom (Manual Override)": {
            "temperature": 0.65,
            "max_new_tokens": 1024,
            "top_p": 0.90,
            "top_k": 50,
            "repetition_penalty": 1.15,
        },
    }

    t_exp = ""
    m_img = ""

    for _, fm, body in personas_raw:
        name = fm["name"]
        composed = _compose_prompt(body)
        new_personas.append(name)
        new_presets[name] = composed

        new_sampling[name] = {
            "temperature": float(fm.get("temperature", 0.65)),
            "max_new_tokens": int(fm.get("max_new_tokens", 1024)),
            "top_p": float(fm.get("top_p", 0.90)),
            "top_k": int(fm.get("top_k", 50)),
            "repetition_penalty": float(fm.get("repetition_penalty", 1.15)),
        }

        if name == "Text-to-Prompt Expansion Engine":
            t_exp = composed
        elif name == "Multi-Image Synthesis Engine":
            m_img = composed

        for alias in fm.get("aliases", []):
            if alias:
                new_aliases[alias] = name
                new_presets[alias] = composed

    new_personas.append("Custom (Manual Override)")

    SYSTEM_PERSONAS = new_personas
    SYSTEM_PROMPT_PRESETS = new_presets
    LEGACY_SYSTEM_PROMPT_ALIASES = new_aliases
    PERSONA_SAMPLING_DEFAULTS = new_sampling
    TEXT_EXPANSION_SYSTEM_PROMPT = t_exp or _compose_prompt("Text Expansion Protocol")
    MULTI_IMAGE_SYSTEM_PROMPT = m_img or _compose_prompt("Multi-Image Fusion Protocol")
    BASE_TEXT_EXPANSION_PROMPT = TEXT_EXPANSION_SYSTEM_PROMPT
    BASE_MULTI_IMAGE_PROMPT = MULTI_IMAGE_SYSTEM_PROMPT
    SYSTEM_PROMPT_CHOICES = list(SYSTEM_PROMPT_PRESETS.keys()) + [CUSTOM_SYSTEM_PROMPT_KEY]

    # 3. Scan and Load Layer 2: Types
    types_raw = []
    if os.path.isdir(TYPES_DIR):
        for fn in os.listdir(TYPES_DIR):
            if fn.endswith(".md") and not fn.startswith("_"):
                fp = os.path.join(TYPES_DIR, fn)
                fm, body = parse_markdown_with_frontmatter(fp)
                if fm and "name" in fm:
                    types_raw.append((fm.get("order", 999), fm, body))

    types_raw.sort(key=lambda x: x[0])

    new_types = []
    new_type_directives = {
        "None (Freeform / No Format Directive)": "",
        "None": "",
    }
    new_type_aliases = {
        "None": "None (Freeform / No Format Directive)",
        "None (Freeform / No Format Directive)": "None (Freeform / No Format Directive)",
        "Detailed Narrative (Long)": "Detailed Narrative",
        "Short Summary (Concise)": "Short Summary",
        "Custom Directives Only": "Structured Categories",
    }

    for _, fm, body in types_raw:
        name = fm["name"]
        new_types.append(name)
        new_type_directives[name] = body
        for alias in fm.get("aliases", []):
            if alias:
                new_type_aliases[alias] = name

    # Add None option
    if "None (Freeform / No Format Directive)" not in new_types:
        new_types.append("None (Freeform / No Format Directive)")

    PROMPT_TYPES = new_types
    PROMPT_TYPE_DIRECTIVES = new_type_directives
    LEGACY_PROMPT_TYPE_ALIASES = new_type_aliases

    # 4. Scan and Load Layer 3: Styles
    styles_raw = []
    if os.path.isdir(STYLES_DIR):
        for fn in os.listdir(STYLES_DIR):
            if fn.endswith(".md") and not fn.startswith("_"):
                fp = os.path.join(STYLES_DIR, fn)
                fm, body = parse_markdown_with_frontmatter(fp)
                if fm and "name" in fm:
                    styles_raw.append((fm.get("order", 999), fm, body))

    styles_raw.sort(key=lambda x: x[0])

    new_styles = []
    new_style_directives = {
        "None (No Style Injection)": "",
        "None": "",
        "Auto-Detect / Preserve Original": "",
    }
    new_non_photo = {}
    new_style_aliases = {
        "None": "None (No Style Injection)",
        "None (No Style Injection)": "None (No Style Injection)",
        "Photorealistic & Cinematic": "Photorealistic (Modern Digital RAW)",
        "Vintage Film (35mm Analog, Grain)": "Analog Film (35mm Vintage Stock)",
        "Anime & Manga (2D / Cel-shaded)": "Anime & Manga (2D Cel-shaded)",
        "Comic Book & Graphic Novel": "Comic Book & Graphic Novel (Ink & Halftone)",
        "Pencil Sketch & Traditional Ink": "Pencil Sketch & Charcoal Drawing",
        "3D Digital Render & CGI": "3D Digital Render & CGI (PBR)",
        "3D CGI & Octane Render": "3D Digital Render & CGI (PBR)",
        "Digital Concept Art & Illustration": "Digital Concept Art & Illustration",
        "Digital Concept Art (ArtStation)": "Digital Concept Art & Illustration",
        "Oil Painting & Fine Art": "Oil Painting & Classical Fine Art",
        "Cyberpunk & Sci-Fi": "Cinematic Still (Anamorphic Movie)",
    }

    for _, fm, body in styles_raw:
        name = fm["name"]
        new_styles.append(name)
        new_style_directives[name] = body

        if "medium_type" in fm or "prohibited" in fm:
            new_non_photo[name] = {
                "medium_label": str(fm.get("medium_label", name)),
                "medium_type": str(fm.get("medium_type", "")),
                "prohibited": str(fm.get("prohibited", "")),
                "replacement": str(fm.get("replacement", "")),
                "tag_injection": str(fm.get("tag_injection", "")),
                "negative_injection": str(fm.get("negative_injection", "")),
            }

        for alias in fm.get("aliases", []):
            if alias:
                new_style_aliases[alias] = name

    # Add None option
    if "None (No Style Injection)" not in new_styles:
        # Place right after Auto-Detect if present, otherwise at top
        if "Auto-Detect / Preserve Original" in new_styles:
            auto_idx = new_styles.index("Auto-Detect / Preserve Original")
            new_styles.insert(auto_idx + 1, "None (No Style Injection)")
        else:
            new_styles.insert(0, "None (No Style Injection)")

    ARTISTIC_STYLES = new_styles
    ARTISTIC_STYLE_DIRECTIVES = new_style_directives
    NON_PHOTOGRAPHIC_STYLES = new_non_photo
    LEGACY_ARTISTIC_STYLE_ALIASES = new_style_aliases


# Initial scan on module import
reload_image_definitions()


# ── SSOT SYSTEM PROMPT RESOLVER ──────────────────────────────────────────────
def resolve_system_prompt(
    system_prompt,
    custom_system_prompt="",
    system_prompt_preset=None,
    system_prompt_mode=None,
    has_image=True,
    is_multi_image=False,
):
    """
    Single Source of Truth (SSOT) for resolving the active system prompt.
    Automatically dispatches according to the 3 input typologies:
    - None Option -> Empty string (No System Prompt)
    - Typology 1: Text-Only (has_image=False) -> TEXT_EXPANSION_SYSTEM_PROMPT
    - Typology 2: 1 Image (has_image=True, is_multi_image=False) -> Selected Persona
    - Typology 3: 2 or 3 Images (is_multi_image=True) -> MULTI_IMAGE_SYSTEM_PROMPT
    - Manual Custom Override -> custom_system_prompt
    """
    if system_prompt == "None" or str(system_prompt).startswith("None"):
        return ""

    is_custom = (
        system_prompt == CUSTOM_SYSTEM_PROMPT_KEY
        or system_prompt == "Custom"
        or "Custom" in str(system_prompt)
        or (system_prompt_mode is not None and "Custom" in str(system_prompt_mode))
    )

    if is_custom:
        user_custom_text = custom_system_prompt.strip()
        if not user_custom_text and isinstance(system_prompt, str) and system_prompt not in SYSTEM_PROMPT_CHOICES:
            user_custom_text = system_prompt.strip()

        if user_custom_text:
            return user_custom_text

    # Explicit direct requests
    if system_prompt == "Text-to-Prompt Expansion Engine":
        return TEXT_EXPANSION_SYSTEM_PROMPT
    if system_prompt == "Multi-Image Synthesis Engine":
        return MULTI_IMAGE_SYSTEM_PROMPT

    # Typology 3: Multi-Image
    if is_multi_image:
        return MULTI_IMAGE_SYSTEM_PROMPT

    # Typology 1: Text-Only
    if not has_image:
        return TEXT_EXPANSION_SYSTEM_PROMPT

    # Typology 2: 1 Image
    target_key = LEGACY_SYSTEM_PROMPT_ALIASES.get(system_prompt, system_prompt)
    if target_key not in SYSTEM_PROMPT_PRESETS and system_prompt_preset:
        target_key = LEGACY_SYSTEM_PROMPT_ALIASES.get(system_prompt_preset, system_prompt_preset)

    return SYSTEM_PROMPT_PRESETS.get(target_key, SYSTEM_PROMPT_PRESETS.get("Generative Vision Engine", TEXT_EXPANSION_SYSTEM_PROMPT))


# ── DYNAMIC 3-LAYER FUSION ENGINE ────────────────────────────────────────────
def build_dynamic_system_prompt(
    base_system_prompt: str,
    prompt_type: str = "Detailed Narrative",
    artistic_style: str = "Auto-Detect / Preserve Original",
) -> str:
    """
    Fuses the base VLM system persona (Layer 1) with the structural prompt_type directive
    (Layer 2) and the artistic_style aesthetic injection (Layer 3) into a single cohesive prompt.
    """
    if not base_system_prompt:
        return ""

    resolved_type = LEGACY_PROMPT_TYPE_ALIASES.get(prompt_type, prompt_type)
    resolved_style = LEGACY_ARTISTIC_STYLE_ALIASES.get(artistic_style, artistic_style)

    if not resolved_type or resolved_type == "None" or str(resolved_type).startswith("None"):
        type_directive = ""
    else:
        type_directive = PROMPT_TYPE_DIRECTIVES.get(resolved_type, "")
        if not type_directive and ("STRUCTURAL FORMAT" in str(prompt_type) or len(str(prompt_type)) > 50):
            type_directive = prompt_type

    if not resolved_style or resolved_style == "None" or str(resolved_style).startswith("None") or resolved_style == "Auto-Detect / Preserve Original":
        style_directive = ""
    else:
        style_directive = ARTISTIC_STYLE_DIRECTIVES.get(resolved_style, "")
        if not style_directive and ("AESTHETIC INJECTION" in str(artistic_style) or len(str(artistic_style)) > 50):
            style_directive = artistic_style

    if not type_directive and not style_directive:
        return base_system_prompt

    injected_layers = []
    if type_directive:
        injected_layers.append(
            f"# LAYER 2 — STRUCTURAL OUTPUT FORMAT\n{type_directive}"
        )
    if style_directive:
        style_layer = f"# LAYER 3 — VISUAL AESTHETIC INJECTION\n{style_directive}"
        if resolved_style in NON_PHOTOGRAPHIC_STYLES:
            medium_info = NON_PHOTOGRAPHIC_STYLES[resolved_style]
            supremacy = (
                f"\n\n# ⚠️ INVIOLABLE MEDIUM OVERRIDE & PROHIBITIONS:\n"
                f"The selected artistic style is strictly '{resolved_style}' ({medium_info['medium_type']}).\n"
                f"- This visual medium strictly SUPERSEDES all photographic, lens, and camera instructions from preceding layers.\n"
                f"- STRICT PROHIBITION: Never output photographic camera specifications ({medium_info['prohibited']}).\n"
                f"- ARTISTIC EXECUTION: Represent all visual elements purely through {medium_info['replacement']}."
            )
            style_layer += supremacy
        injected_layers.append(style_layer)

    anchor = "# REQUIRED OUTPUT CONTRACT"
    if anchor in base_system_prompt:
        pre, _, post = base_system_prompt.rpartition(anchor)
        fused = pre.rstrip() + "\n\n" + "\n\n".join(injected_layers) + "\n\n" + anchor + post
    else:
        fused = base_system_prompt.rstrip() + "\n\n" + "\n\n".join(injected_layers)

    return fused


def resolve_prompt_type(prompt_type: str) -> str:
    if not prompt_type or prompt_type == "None" or str(prompt_type).startswith("None"):
        return ""
    resolved_key = LEGACY_PROMPT_TYPE_ALIASES.get(prompt_type, prompt_type)
    return PROMPT_TYPE_DIRECTIVES.get(resolved_key, PROMPT_TYPE_DIRECTIVES.get("Detailed Narrative", ""))


def resolve_artistic_style(artistic_style: str) -> str:
    if not artistic_style or artistic_style == "None" or str(artistic_style).startswith("None"):
        return "None"
    return LEGACY_ARTISTIC_STYLE_ALIASES.get(artistic_style, artistic_style)
