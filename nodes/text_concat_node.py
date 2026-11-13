"""
[STOIQO] Text Concatenate & Clean Node
Combines multiple text strings (prompts, modifiers, lora triggers, prefixes, suffixes)
with configurable separators, tag deduplication, underscore conversion, and dynamic inputs.
"""

import re

try:
    from ..core.telemetry import NodeTelemetryTimer, inject_telemetry
except (ImportError, ValueError):
    try:
        from core.telemetry import NodeTelemetryTimer, inject_telemetry
    except Exception:
        NodeTelemetryTimer = None
        inject_telemetry = lambda ui, timer: ui


def _deduplicate_items(items, mode):
    """Deduplicates a list of tag/string items while strictly preserving first-seen order."""
    seen = set()
    unique = []
    for it in items:
        cleaned = it.strip()
        if not cleaned:
            continue
        key = cleaned.lower() if mode == "Case-Insensitive" else cleaned
        if key not in seen:
            seen.add(key)
            unique.append(cleaned)
    return unique


def _convert_underscores_safe(text):
    """Converts underscores to spaces while protecting special tags like <lora:...>."""
    tags = []
    def repl(m):
        tags.append(m.group(0))
        return f"XZXSTOIQOTAGTOKEN{len(tags)-1}XZX"

    protected = re.sub(r"<[^>]+>", repl, text)
    converted = protected.replace("_", " ")
    for i, tag in enumerate(tags):
        converted = converted.replace(f"XZXSTOIQOTAGTOKEN{i}XZX", tag)
    return converted


class StoiqoTextConcatenateNode:
    """
    Concatenates and cleans multiple text blocks for prompt engineering.
    Features dynamic input expansion, tag deduplication, syntax sanitization,
    and returns token/word statistics.
    """

    SEPARATOR_CHOICES = [
        ",  (Comma Space)",
        "   (Single Space)",
        "\\n (Newline)",
        "\\n\\n (Double Newline / Paragraph)",
        " |  (Pipe Separator)",
        ";  (Semicolon)",
        "✏️ Custom Separator",
    ]

    DEDUP_CHOICES = [
        "None",
        "Exact Match",
        "Case-Insensitive",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_1": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "First text block (e.g. Master Subject, Base Caption, or Style).",
                    },
                ),
                "text_2": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Second text block (e.g. Environment, Details, or Quality Modifiers).",
                    },
                ),
            },
            "optional": {
                "text_3": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Optional third text block (e.g. Camera, Lighting, or LoRA triggers).",
                    },
                ),
                "text_4": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Optional fourth text block (e.g. Artist style or Rendering tags).",
                    },
                ),
                "text_5": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Optional fifth text block.",
                    },
                ),
                "text_6": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Optional sixth text block.",
                    },
                ),
                "text_7": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Optional seventh text block.",
                    },
                ),
                "text_8": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Optional eighth text block.",
                    },
                ),
                "template": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "Optional template: e.g. {text_1} featuring {text_2} in {text_3} style",
                        "tooltip": "Formatting template. When non-empty, substitutes placeholders like {text_1}..{text_8} or {1}..{8} instead of standard sequential concatenation.",
                    },
                ),
                "separator": (
                    cls.SEPARATOR_CHOICES,
                    {
                        "default": cls.SEPARATOR_CHOICES[0],
                        "tooltip": "Separator placed between non-empty text blocks.",
                    },
                ),
                "custom_separator": (
                    "STRING",
                    {
                        "default": ", ",
                        "tooltip": "Custom separator string used when '✏️ Custom Separator' is selected above.",
                    },
                ),
                "prefix": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Text prepended to the very beginning of the concatenated result.",
                    },
                ),
                "suffix": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Text appended to the very end of the concatenated result.",
                    },
                ),
                "deduplicate_tags": (
                    cls.DEDUP_CHOICES,
                    {
                        "default": cls.DEDUP_CHOICES[0],
                        "tooltip": "Deduplicate tags across inputs (preserves first occurrence).",
                    },
                ),
                "clean_whitespace": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Strips extraneous whitespace, trailing commas, and collapses multiple spaces.",
                    },
                ),
                "convert_underscores": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Converts booru underscores ('blue_eyes') to spaces ('blue eyes') while protecting LoRAs.",
                    },
                ),
                "skip_empty": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Ignores empty or whitespace-only inputs so separators are not duplicated.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "INT", "INT", "INT")
    RETURN_NAMES = ("text", "word_count", "char_count", "token_count")
    FUNCTION = "concatenate"
    OUTPUT_NODE = True
    CATEGORY = "STOIQO"

    def concatenate(
        self,
        text_1,
        text_2,
        separator,
        text_3="",
        text_4="",
        text_5="",
        text_6="",
        text_7="",
        text_8="",
        template="",
        custom_separator=", ",
        prefix="",
        suffix="",
        deduplicate_tags="None",
        clean_whitespace=True,
        convert_underscores=False,
        skip_empty=True,
        unique_id=None,
        **kwargs
    ):
        timer = NodeTelemetryTimer(node_id=unique_id, node_name="TextConcatenate") if NodeTelemetryTimer else None
        if timer:
            timer.__enter__()

        try:
            # Resolve active separator token
            if separator == ",  (Comma Space)":
                sep = ", "
            elif separator == "   (Single Space)":
                sep = " "
            elif separator == "\\n (Newline)":
                sep = "\n"
            elif separator == "\\n\\n (Double Newline / Paragraph)":
                sep = "\n\n"
            elif separator == " |  (Pipe Separator)":
                sep = " | "
            elif separator == ";  (Semicolon)":
                sep = "; "
            elif separator == "✏️ Custom Separator":
                sep = custom_separator
            else:
                sep = ", "

            raw_parts = [text_1, text_2, text_3, text_4, text_5, text_6, text_7, text_8]
            # Include any extra kwargs if passed dynamically
            for k in sorted(kwargs.keys()):
                if k.startswith("text_"):
                    raw_parts.append(kwargs[k])

            slot_values = {}
            for idx, part in enumerate(raw_parts, 1):
                if isinstance(part, (list, tuple)):
                    slot_values[f"text_{idx}"] = sep.join(str(x) for x in part if x is not None)
                else:
                    slot_values[f"text_{idx}"] = str(part or "")

            processed_parts = []
            for part in raw_parts:
                if part is None:
                    continue
                if isinstance(part, (list, tuple)):
                    part_str = sep.join(str(x) for x in part if x is not None and str(x).strip())
                else:
                    part_str = str(part)

                if convert_underscores:
                    part_str = _convert_underscores_safe(part_str)

                if clean_whitespace:
                    part_str = part_str.strip()
                    # Clean stray leading/trailing commas if separator is comma-based
                    if sep.strip() == ",":
                        part_str = part_str.strip(",")

                if skip_empty and not part_str:
                    continue

                processed_parts.append(part_str)

            # Template evaluation or Tag Deduplication / Normal Concatenation
            if template and template.strip():
                tpl = template
                for idx, part in enumerate(raw_parts, 1):
                    if part is None:
                        p_val = ""
                    elif isinstance(part, (list, tuple)):
                        p_val = sep.join(str(x) for x in part if x is not None and str(x).strip())
                    else:
                        p_val = str(part)
                    if convert_underscores:
                        p_val = _convert_underscores_safe(p_val)
                    if clean_whitespace:
                        p_val = p_val.strip()
                        if sep.strip() == ",":
                            p_val = p_val.strip(",")
                    tpl = tpl.replace(f"{{text_{idx}}}", p_val).replace(f"{{text{idx}}}", p_val).replace(f"{{{idx}}}", p_val)

                # Remove unfulfilled placeholders
                tpl = re.sub(r"\{text_?\d+\}", "", tpl)
                tpl = re.sub(r"\{\d+\}", "", tpl)
                combined = tpl
            elif deduplicate_tags != "None" and processed_parts:
                if sep.strip() == ",":
                    # Deduplicate individual comma-separated tags across all parts
                    all_tags = []
                    for p in processed_parts:
                        for t in p.split(","):
                            if t.strip():
                                all_tags.append(t.strip())
                    unique_tags = _deduplicate_items(all_tags, deduplicate_tags)
                    combined = ", ".join(unique_tags)
                else:
                    # Deduplicate block-level items
                    unique_parts = _deduplicate_items(processed_parts, deduplicate_tags)
                    combined = sep.join(unique_parts)
            else:
                combined = sep.join(processed_parts)

            # Apply global cleanups
            if clean_whitespace:
                # Collapse repeated spaces inside lines (while preserving newlines)
                combined = re.sub(r"[ \t]+", " ", combined)
                # Fix spacing before punctuation: "word , word" -> "word, word"
                combined = re.sub(r"\s+([,;.!?])", r"\1", combined)
                # Remove duplicated consecutive commas e.g. ", ," -> ", "
                combined = re.sub(r",\s*,+", ", ", combined)
                combined = combined.strip(" ,;\t\n\r")

            # Apply prefix and suffix
            prefix_clean = prefix.strip() if clean_whitespace else prefix
            suffix_clean = suffix.strip() if clean_whitespace else suffix

            final_chunks = []
            if prefix_clean:
                final_chunks.append(prefix_clean)
            if combined:
                final_chunks.append(combined)
            if suffix_clean:
                final_chunks.append(suffix_clean)

            if prefix_clean or suffix_clean:
                if sep.strip() == ",":
                    result = ", ".join(final_chunks)
                elif "\n" in sep:
                    result = "\n".join(final_chunks)
                else:
                    result = sep.join(final_chunks)
            else:
                result = combined

            if clean_whitespace and result:
                result = re.sub(r",\s*,+", ", ", result)
                result = re.sub(r"\s+([,;.!?])", r"\1", result)
                result = result.strip(" ,;\t\n\r")

            word_count = len(result.split()) if result else 0
            char_count = len(result)
            # Standard estimated token count (max between word count and chars/3.8)
            est_token_count = max(word_count, int(char_count / 3.8)) if result else 0

            ui_payload = {
                "token_info": [{
                    "words": word_count,
                    "chars": char_count,
                    "tokens": est_token_count
                }],
                "slot_values": [slot_values]
            }
            if timer and inject_telemetry:
                timer.__exit__(None, None, None)
                timer = None
                inject_telemetry(ui_payload, timer)

            return {
                "ui": ui_payload,
                "result": (result, word_count, char_count, est_token_count)
            }
        finally:
            if timer:
                timer.__exit__(None, None, None)
