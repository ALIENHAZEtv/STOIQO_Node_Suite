"""
[STOIQO] Prompt Generator Engine — Text & Prompt Processing
LoRA tag processing, blacklist filtering, tag shuffling, Dual-Prompt (CLIP/T5) parsing,
surgical negative prompt extraction, and task prompt construction.
"""

import re
import random
from .prompt_types import (
    PROMPT_TYPE_DIRECTIVES,
    STYLE_PROMPTS,
    resolve_prompt_type,
)
from .styles import (
    ARTISTIC_STYLE_DIRECTIVES,
    resolve_artistic_style,
)


def clean_llm_output(text):
    """Strips markdown code fences and unnecessary whitespace from LLM output."""
    if not text:
        return ""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def build_task_prompt(
    prompt_type="Structured Categories",
    artistic_style="Auto-Detect / Preserve Original",
    directives="",
    input_text="",
    is_dual_prompt=False,
    is_artifact_audit=False,
):
    """Builds the comprehensive user instruction prompt sent to the LLM incorporating type, style, and directives."""
    resolved_type = resolve_prompt_type(prompt_type)
    resolved_style = resolve_artistic_style(artistic_style)
    base = PROMPT_TYPE_DIRECTIVES.get(resolved_type, STYLE_PROMPTS.get(resolved_type, ""))
    style_dir = ARTISTIC_STYLE_DIRECTIVES.get(resolved_style, "")
    parts = []

    if input_text and input_text.strip():
        parts.append(f"FOUNDATIONAL SOURCE TEXT / CONCEPT TO EXPAND OR REFINE:\n{input_text.strip()}\n")

    if base:
        parts.append(f"Task Format: {base}")
    if style_dir:
        parts.append(f"{style_dir}")
    if directives and directives.strip():
        parts.append(
            "⚠️ MANDATORY USER MODIFICATION DIRECTIVE (SUPREME PRIORITY):\n"
            f"{directives.strip()}\n"
            "INSTRUCTION FOR USER DIRECTIVES: Enforce these specific modifications into the final generated prompt and tags. "
            "You MUST substitute or overwrite any conflicting traits or attributes in the scene/subject with these requested modifications "
            "(e.g., hair color, clothing, accessories, lighting, environment elements), while keeping the rest of the visual scene intact and coherent."
        )

    if is_dual_prompt:
        parts.append(
            "⚡ DUAL-PROMPT SPECIALIZATION DIRECTIVE (CLIP + T5/DECODER COUPLING):\n"
            "- In the <PROMPT> block: Generate an expansive, descriptive, natural-language narrative optimized for T5-XXL and modern diffusion decoders (Flux / SD3 / AuraFlow).\n"
            "- In the <TAGS> block: Generate a compact, comma-separated list of individual keywords (< 75 tokens) strictly optimized for CLIP-L conditioning."
        )

    if is_artifact_audit:
        parts.append(
            "🔍 FORENSIC ARTIFACT AUDIT DIRECTIVE (SURGICAL NEGATIVE PROMPT):\n"
            "- Scrutinize the visual input forensically for anatomical errors (e.g. extra/fused fingers, distorted eyes, asymmetrical limbs), lighting incoherencies, compression artifacts, blurred details, and rendering flaws.\n"
            "- In the <NEGATIVE> block: Compile a comprehensive, targeted negative prompt enumerating every detected flaw and potential generation deformity to suppress them."
        )

    # Universal Three-Part Output Requirement & Strict Block Scope Rules:
    parts.append(
        "CRITICAL THREE-PART OUTPUT FORMAT & SCOPE RULES: You must structure the final output into exactly three clearly delineated blocks:\n\n"
        "<PROMPT>\n"
        "[Write the primary generative prompt here. Apply the Task Format (Layer 2), Artistic Style (Layer 3), and User Modification Directives (Layer 4) STRICTLY inside this block.]\n"
        "</PROMPT>\n\n"
        "<TAGS>\n"
        "[Write a flat, comma-separated list of individual visual keywords and concepts here (< 75 tokens). This must remain an objective catalog of visible elements, clothes, setting, and traits. Do NOT apply narrative prose, categorical labels, or style overrides to this block.]\n"
        "</TAGS>\n\n"
        "<NEGATIVE>\n"
        "[Write targeted negative prompt tokens here, identifying flaws, anatomical deformities, rendering artifacts, and bad lighting to avoid. Do NOT include scene categories or positive style adjectives here.]\n"
        "</NEGATIVE>\n\n"
        "Output ONLY these three blocks without conversational preambles, commentary, or markdown fences."
    )
    return "\n".join(parts)


def parse_dual_prompt(raw_text):
    """Parses <TAGS>/<CLIP_L> and <T5_XXL>/<CAPTION> tags with fallback and length safety for tags."""
    tags_text = ""
    caption_text = ""

    tags_match = re.search(r"<(?:TAGS|CLIP_L|CLIP)>(.*?)</(?:TAGS|CLIP_L|CLIP)>", raw_text, re.DOTALL | re.IGNORECASE)
    caption_match = re.search(r"<(?:T5_XXL|T5|CAPTION|DESCRIPTION)>(.*?)</(?:T5_XXL|T5|CAPTION|DESCRIPTION)>", raw_text, re.DOTALL | re.IGNORECASE)

    if tags_match:
        tags_text = tags_match.group(1).strip()
    if caption_match:
        caption_text = caption_match.group(1).strip()

    # Fallback if tags were omitted or malformed
    if not tags_text and not caption_text:
        tags_text = raw_text.strip()
        caption_text = raw_text.strip()
    elif not tags_text:
        tags_text = caption_text
    elif not caption_text:
        caption_text = tags_text

    return tags_text, caption_text


def parse_artifact_audit(raw_text, custom_negative_prefix=""):
    """Extracts <AUDIT> analysis and <NEGATIVE_PROMPT> tokens with prefix injection."""
    audit_text = ""
    negative_prompt = ""

    audit_match = re.search(r"<AUDIT>(.*?)</AUDIT>", raw_text, re.DOTALL | re.IGNORECASE)
    neg_match = re.search(r"<NEGATIVE_PROMPT>(.*?)</NEGATIVE_PROMPT>", raw_text, re.DOTALL | re.IGNORECASE)

    if neg_match:
        negative_prompt = neg_match.group(1).strip()

    if audit_match:
        audit_text = audit_match.group(1).strip()
    else:
        audit_text = re.sub(r"<NEGATIVE_PROMPT>.*?</NEGATIVE_PROMPT>", "", raw_text, flags=re.DOTALL | re.IGNORECASE).strip()

    if not negative_prompt:
        negative_prompt = "blurry, low quality, distorted, artifacts"
    if not audit_text:
        audit_text = raw_text.strip()

    neg_parts = [p.strip() for p in negative_prompt.replace("\n", ",").split(",") if p.strip()]
    cleaned_neg = ", ".join(neg_parts)

    if custom_negative_prefix and custom_negative_prefix.strip():
        prefix = custom_negative_prefix.strip().rstrip(",") + ", "
        cleaned_neg = prefix + cleaned_neg

    return audit_text, cleaned_neg


def process_lora_caption(
    raw_caption,
    trigger_word="",
    blacklist_tags="",
    shuffle_tags=False,
    tag_separator=", ",
    seed=42,
    caption_style="Detailed Description",
):
    """
    Cleans, deduplicates, filters blacklist tags, shuffles, and pins trigger words
    for LoRA dataset captioning and prose outputs.
    Preserves Danbooru underscores when in Booru mode.
    """
    raw_text = raw_caption.strip()
    tw = trigger_word.strip().rstrip(",").strip() if trigger_word else ""

    blacklist_set = set()
    if blacklist_tags and blacklist_tags.strip():
        raw_blacklist = [b.strip().lower() for b in blacklist_tags.replace("\n", ",").replace(";", ",").split(",") if b.strip()]
        for b in raw_blacklist:
            blacklist_set.add(b)
            blacklist_set.add(b.replace("_", " "))
            blacklist_set.add(b.replace(" ", "_"))

    is_booru = "booru" in caption_style.lower() or "danbooru" in caption_style.lower()
    is_tag_mode = is_booru or ("Tags" in caption_style) or ("tag" in caption_style.lower()) or shuffle_tags
    non_tag_keywords = (
        "Narrative", "Summary", "Description", "Differences", "Flaw", "Audit",
        "Categories", "Cinematic", "Video", "Script", "Prose", "Structured"
    )
    if not is_tag_mode and not any(k in caption_style for k in non_tag_keywords):
        parts = [t.strip() for t in raw_text.split(",") if t.strip()]
        if len(parts) >= 3 and all(len(p.split()) <= 4 for p in parts[:5]):
            is_tag_mode = True

    if is_tag_mode:
        delimiter = "\n" if ("\n" in raw_text and "," not in raw_text) else ","
        parts = [t.strip() for t in raw_text.split(delimiter) if t.strip()]

        cleaned_tags = []
        seen = set()

        for t in parts:
            clean_t = t.strip().lstrip("*-• ").strip()
            if not clean_t:
                continue
            norm_t = clean_t if is_booru else clean_t.replace("_", " ")
            t_lower = norm_t.lower()

            if t_lower in blacklist_set or clean_t.lower() in blacklist_set or t_lower in seen:
                continue
            if tw and t_lower == tw.lower():
                continue

            seen.add(t_lower)
            cleaned_tags.append(norm_t)

        if shuffle_tags and len(cleaned_tags) > 1:
            rng = random.Random(seed)
            rng.shuffle(cleaned_tags)

        final_tags = []
        if tw:
            final_tags.append(tw)
        final_tags.extend(cleaned_tags)

        actual_sep = "\n" if ("\n" in tag_separator or "Newline" in tag_separator) else tag_separator
        final_caption = actual_sep.join(final_tags)
        return final_caption, final_tags
    else:
        final_caption = raw_text
        if blacklist_set:
            for bad_tag in blacklist_set:
                pattern = re.compile(rf"\b{re.escape(bad_tag)}\b", re.IGNORECASE)
                final_caption = pattern.sub("", final_caption)
            final_caption = re.sub(r"\s*,\s*,\s*", ", ", final_caption)
            final_caption = re.sub(r"[ \t]+", " ", final_caption).strip(" ,")

        if tw and not final_caption.lower().startswith(tw.lower()):
            final_caption = f"{tw}, {final_caption}"
        return final_caption, []


def clip_tokens_safely(text, max_words=65):
    """Clips text safely under ~77 tokens at natural delimiters (comma or period)."""
    if not text:
        return ""
    words = text.split()
    if len(words) <= max_words:
        return text.strip()
    truncated = " ".join(words[:max_words])
    last_delim = max(truncated.rfind(","), truncated.rfind("."))
    if last_delim > 30:
        return truncated[:last_delim].strip()
    return truncated.strip()


def convert_to_tags(text, max_words=65):
    """
    Guarantees output is strictly formatted as concise, comma-separated individual tags / keywords
    bounded under ~77 tokens (for CLIP text encoders, LoRA training, and booru tag workflows).
    Preserves existing compound tags, decimal numbers (e.g. 85mm f/1.4 lens), and prepositions.
    """
    if not text:
        return ""
    clean = text.strip()

    # Split by commas, semicolons, or newlines
    raw_chunks = [c.strip() for c in re.split(r"[\n,;]+", clean) if c.strip()]
    if not raw_chunks:
        return ""

    extracted_tags = []
    seen = set()
    word_count = 0

    for chunk in raw_chunks:
        # Clean leading bullet points or markdown artifact markers, but preserve internal slashes, dots, hyphens
        tag = chunk.lstrip("*-• \t").strip()
        # Strip trailing punctuation like trailing period or comma
        tag = re.sub(r"[\.,;]+$", "", tag).strip()
        if not tag:
            continue

        # Skip headers like "Subject(s) & Focal Entity:" if someone passed raw categories
        if re.match(r"^[\w\s\(\)&]+:\s*$", tag):
            continue

        tag_lower = tag.lower()
        if tag_lower in seen:
            continue

        w_len = len(tag.split())
        if word_count + w_len > max_words and extracted_tags:
            break

        seen.add(tag_lower)
        extracted_tags.append(tag)
        word_count += w_len

        if word_count >= max_words:
            break

    if extracted_tags:
        return ", ".join(extracted_tags)
    return clip_tokens_safely(clean, max_words=max_words)


def parse_three_way_prompt(raw_text, custom_negative_prefix=""):
    """
    Parses the 3-part structured LLM output:
    1. <PROMPT> (or <CAPTION> / <DESCRIPTION>) -> Main generative prompt
    2. <TAGS> (or <CLIP_L> / <CLIP> / <KEYWORDS>) -> Flat comma-separated tag list
    3. <NEGATIVE> (or <NEGATIVE_PROMPT>) -> Targeted negative prompt
    Robust against unclosed tags caused by token limit truncation.
    """
    clean = clean_llm_output(raw_text)

    # Extract <PROMPT> block (closed OR truncated up to next block or EOF)
    prompt_match = re.search(
        r"<(?:PROMPT|CAPTION|DESCRIPTION)>\s*(.*?)(?:</(?:PROMPT|CAPTION|DESCRIPTION)>|(?=<(?:TAGS|CLIP_L|CLIP|KEYWORDS|NEGATIVE|NEGATIVE_PROMPT)>)|$)",
        clean,
        re.DOTALL | re.IGNORECASE,
    )
    # Extract <TAGS> block (closed OR truncated up to next block or EOF)
    tags_match = re.search(
        r"<(?:TAGS|CLIP_L|CLIP|KEYWORDS)>\s*(.*?)(?:</(?:TAGS|CLIP_L|CLIP|KEYWORDS)>|(?=<(?:NEGATIVE|NEGATIVE_PROMPT)>)|$)",
        clean,
        re.DOTALL | re.IGNORECASE,
    )
    # Extract <NEGATIVE> block (closed OR truncated to EOF)
    neg_match = re.search(
        r"<(?:NEGATIVE|NEGATIVE_PROMPT)>\s*(.*?)(?:</(?:NEGATIVE|NEGATIVE_PROMPT)>|$)",
        clean,
        re.DOTALL | re.IGNORECASE,
    )

    # 1. Main prompt
    if prompt_match and prompt_match.group(1).strip():
        prompt_text = prompt_match.group(1).strip()
    else:
        # Strip other XML tags if present
        prompt_text = re.sub(r"<(?:TAGS|CLIP_L|CLIP|KEYWORDS)>.*?(?:</(?:TAGS|CLIP_L|CLIP|KEYWORDS)>|$)", "", clean, flags=re.DOTALL | re.IGNORECASE)
        prompt_text = re.sub(r"<(?:NEGATIVE|NEGATIVE_PROMPT)>.*?(?:</(?:NEGATIVE|NEGATIVE_PROMPT)>|$)", "", prompt_text, flags=re.DOTALL | re.IGNORECASE)
        # Strip opening <PROMPT> tag if unclosed
        prompt_text = re.sub(r"^<(?:PROMPT|CAPTION|DESCRIPTION)>\s*", "", prompt_text.strip(), flags=re.IGNORECASE)
        prompt_text = re.sub(r"</(?:PROMPT|CAPTION|DESCRIPTION)>\s*$", "", prompt_text.strip(), flags=re.IGNORECASE)

    if not prompt_text:
        prompt_text = clean.strip()

    # 2. Tags
    if tags_match and tags_match.group(1).strip():
        tags_raw = tags_match.group(1).strip()
        tags_text = convert_to_tags(tags_raw, max_words=65)
    else:
        # Extract tags from prompt if tags block was truncated/absent
        tags_text = convert_to_tags(prompt_text, max_words=65)

    # 3. Negative
    if neg_match and neg_match.group(1).strip():
        negative_raw = neg_match.group(1).strip()
    else:
        negative_raw = "blurry, low quality, distorted, extra limbs, bad anatomy, artifacts"

    neg_parts = [p.strip() for p in negative_raw.replace("\n", ",").split(",") if p.strip()]
    cleaned_neg = ", ".join(neg_parts)

    if custom_negative_prefix and custom_negative_prefix.strip():
        prefix = custom_negative_prefix.strip().rstrip(",") + ", "
        cleaned_neg = prefix + cleaned_neg

    return prompt_text, tags_text, cleaned_neg


def post_process_caption(
    raw_caption,
    is_dual_active=False,
    is_audit_active=False,
    negative_prompt_prefix="",
    trigger_word="",
    blacklist_tags="",
    shuffle_tags=False,
    tag_separator=", ",
    seed=42,
    prompt_type="Detailed Narrative (Long)",
):
    """
    Single Source of Truth (SSOT) for prompt outputs:
    1. caption: Always the primary full/descriptive prompt (following System Prompt & Prompt Type).
    2. tags: Strictly concise comma-separated tags/keywords bounded under 77 tokens.
    3. negative: Surgical negative prompt addressing detected flaws + prefix.
    Returns: (caption, tags, negative, tags_list)
    """
    raw_prompt, raw_tags, raw_neg = parse_three_way_prompt(
        raw_caption, custom_negative_prefix=negative_prompt_prefix
    )

    # Post-process main caption with trigger words / blacklist if configured
    caption, tags_list = process_lora_caption(
        raw_prompt,
        trigger_word=trigger_word,
        blacklist_tags=blacklist_tags,
        shuffle_tags=shuffle_tags,
        tag_separator=tag_separator,
        seed=seed,
        caption_style=prompt_type,
    )

    # Post-process tags with trigger words / blacklist
    tags_style = "Booru Tags" if "Booru" in str(prompt_type) else "Tags"
    tags, _ = process_lora_caption(
        raw_tags,
        trigger_word=trigger_word,
        blacklist_tags=blacklist_tags,
        shuffle_tags=shuffle_tags,
        tag_separator=tag_separator,
        seed=seed,
        caption_style=tags_style,
    )
    tags = convert_to_tags(tags, max_words=65)

    negative = raw_neg

    return caption, tags, negative, tags_list
