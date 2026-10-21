"""
[STOIQO] Modular Prompt Synthesizer Engine Node
Ultra-lean, high-efficiency vision-language prompt synthesis node.
Generates prompt, tags, and surgical negative prompt automatically with tuned defaults,
while accepting modular satellite connections for Style, Sampling, and Multi-Image reasoning.
"""

import logging
import re

import torch

logger = logging.getLogger(__name__)


def _mentions(text: str, term: str) -> bool:
    """Whole-word, case-insensitive match (avoids substring false positives)."""
    if not term:
        return False
    return re.search(r"(?<!\w)" + re.escape(term.strip()) + r"(?!\w)", text, re.IGNORECASE) is not None


try:
    from ..core import (
        build_task_prompt,
        post_process_caption,
        tensor_to_pil,
        resolve_system_prompt,
        resolve_prompt_type,
        resolve_artistic_style,
        NodeTelemetryTimer,
        inject_telemetry,
    )
except (ImportError, ValueError):
    from core import (
        build_task_prompt,
        post_process_caption,
        tensor_to_pil,
        resolve_system_prompt,
        resolve_prompt_type,
        resolve_artistic_style,
        NodeTelemetryTimer,
        inject_telemetry,
    )


class StoiqoPromptSynthesizerNode:
    """
    [STOIQO] Modular Prompt Synthesizer Engine
    Next-generation modular vision-language engine.
    Compact interface: generates high-fidelity Prompt, concise Tags, and surgical Negative in one pass.
    A plain IMAGE batch is captioned image-by-image (list outputs); the Multi-Image Context Hub
    fuses several images into a single prompt.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "stoiqo_model": ("STOIQO_MODEL", {"tooltip": "Connect [STOIQO] VLM Model Loader here."}),
                "user_directives": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "Creative directives, specific modifications, or concept to generate...",
                        "tooltip": "User prompt directives and creative intent. In text-only mode this is the source concept to expand.",
                    },
                ),
            },
            "optional": {
                "image": ("IMAGE", {"tooltip": "Optional input image or batch (each image is captioned independently). If omitted, synthesizes prompt from text directives."}),
                "style_directives": ("STOIQO_STYLE", {"tooltip": "Optional connection from [STOIQO] AI Persona & Style Directives."}),
                "sampling_options": ("STOIQO_SAMPLING", {"tooltip": "Optional connection from [STOIQO] LLM Sampling & Precision."}),
                "multi_image_context": ("STOIQO_CONTEXT", {"tooltip": "Optional connection from [STOIQO] Multi-Image Context Hub (fuses images into ONE prompt)."}),
                "character_context": ("STOIQO_CHARACTER", {"tooltip": "Optional character visual DNA & Lorebook from [STOIQO] Character Memory Bank."}),
                "regional_mode": (
                    [
                        "Disabled",
                        "Left / Right / Background",
                        "Foreground / Background",
                        "Grid 2x2 Quadrants",
                    ],
                    {"default": "Disabled", "tooltip": "Regional Prompting (#94): Decomposes the scene into explicit spatial zones to eliminate attribute and color bleed."},
                ),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("prompt", "tags", "negative", "raw_response")
    # Lists: one entry per image when an IMAGE batch is captioned independently (dataset tagging).
    OUTPUT_IS_LIST = (True, True, True, True)
    FUNCTION = "synthesize_prompt"
    OUTPUT_NODE = True
    CATEGORY = "STOIQO"

    @staticmethod
    def _stream_targets(unique_id, prompt):
        """Node IDs for live WebSocket streaming (self + downstream ShowPrompt nodes)."""
        stream_ids = []
        if unique_id is not None:
            uid_str = str(unique_id)
            stream_ids.append(uid_str)
            if prompt and isinstance(prompt, dict):
                for nid, ninfo in prompt.items():
                    if isinstance(ninfo, dict) and "inputs" in ninfo:
                        for inval in ninfo["inputs"].values():
                            if isinstance(inval, list) and len(inval) > 0 and str(inval[0]) == uid_str:
                                stream_ids.append(str(nid))
        return stream_ids

    def synthesize_prompt(
        self,
        stoiqo_model,
        user_directives: str = "",
        image: torch.Tensor = None,
        style_directives: dict = None,
        sampling_options: dict = None,
        multi_image_context: dict = None,
        character_context: dict = None,
        regional_mode: str = "Disabled",
        unique_id: str = None,
        prompt: dict = None,
        extra_pnginfo: dict = None,
    ):
        with NodeTelemetryTimer(node_id=unique_id, node_name="PromptSynthesizer") as timer:
            # 1. Resolve Style Directives (Defaults if not connected)
            style = style_directives or {}
            system_prompt = style.get("system_prompt", "Visual Prompt Synthesizer")
            custom_system_prompt = style.get("custom_system_prompt", "")
            prompt_type = resolve_prompt_type(style.get("prompt_type", "Detailed Narrative (Long)"))
            artistic_style = resolve_artistic_style(style.get("artistic_style", "Auto-Detect / Preserve Original"))
            enable_dual = bool(style.get("enable_dual_prompt", True)) or ("Dual Prompt" in str(prompt_type))
            enable_audit = bool(style.get("audit_artifacts", True)) or any(
                k in str(prompt_type) for k in ("Artifact", "Negative Prompt", "Flaw")
            )
            negative_prefix = style.get("negative_prompt_prefix", "") or ""

            # 2. Resolve Sampling Options (Defaults if not connected)
            sampling = sampling_options or {}
            temperature = float(sampling.get("temperature", 0.6))
            top_p = float(sampling.get("top_p", 0.9))
            top_k = int(sampling.get("top_k", 40))
            repetition_penalty = float(sampling.get("repetition_penalty", 1.1))
            max_new_tokens = int(sampling.get("max_new_tokens", 1024))
            target_megapixel = float(sampling.get("target_megapixel", 1.0))
            seed = int(sampling.get("seed", 42))

            # 3. Collect input images. Each job = (pil_images, is_multi_image, seed).
            #    - Context Hub connected -> ONE fused multi-image job (primary image, if any, goes first).
            #    - Plain IMAGE batch      -> one independent job per image (seed + i), like the legacy engine.
            context_directive = ""
            jobs = []
            tensors = []
            if image is not None and isinstance(image, torch.Tensor):
                tensors = [image[b:b + 1] for b in range(image.shape[0])]

            if multi_image_context and "images" in multi_image_context:
                fusion_mode = multi_image_context.get("fusion_mode", "Contextual Fusion (Blend Style & Subject)")
                context_directive = f"\n[MULTI-IMAGE DIRECTIVE]: Apply {fusion_mode} across reference images."
                fused = list(tensors)
                for img_t in multi_image_context["images"]:
                    if img_t is not None and isinstance(img_t, torch.Tensor):
                        fused.append(img_t[0:1] if img_t.ndim == 4 else img_t.unsqueeze(0))
                if len(fused) > 1:
                    per_image_mpx = max(0.35, min(target_megapixel, 1.5 / len(fused)))
                    imgs = [tensor_to_pil(t, target_megapixel=per_image_mpx)[0] for t in fused]
                    jobs.append((imgs, True, seed))
                elif fused:
                    jobs.append((tensor_to_pil(fused[0], target_megapixel=target_megapixel)[0], False, seed))
            else:
                for i, t in enumerate(tensors):
                    jobs.append((tensor_to_pil(t, target_megapixel=target_megapixel)[0], False, seed + i))

            has_image = bool(jobs)
            is_multi_image = has_image and jobs[0][1]
            if not has_image:
                jobs.append((None, False, seed))

            active_system_prompt = resolve_system_prompt(
                system_prompt, custom_system_prompt, has_image=has_image, is_multi_image=is_multi_image
            )

            # 4. Integrate Character Memory Bank
            character_directive = ""
            character_negative = ""
            if character_context and isinstance(character_context, dict):
                c_mode = character_context.get("injection_mode", "Smart Detect (Inject only when Name or Trigger is in Prompt)")
                c_name = character_context.get("character_name", "")
                c_tag = character_context.get("trigger_tag", "")
                c_dna = character_context.get("character_dna", "")
                c_outfit = character_context.get("signature_outfit", "")
                c_acc = character_context.get("accessories_props", "")
                c_vibe = character_context.get("personality_vibe", "")
                character_negative = character_context.get("negative_constraints", "")

                should_inject_char = False
                if c_mode == "Always Prepend (Force Character DNA)":
                    should_inject_char = True
                elif "Smart Detect" in c_mode:
                    p_text = user_directives or ""
                    if not p_text.strip() or _mentions(p_text, c_name) or _mentions(p_text, c_tag):
                        should_inject_char = True

                if should_inject_char and c_dna:
                    parts = [f"Character: {c_name or c_tag}", f"DNA: {c_dna}"]
                    if c_outfit:
                        parts.append(f"Outfit: {c_outfit}")
                    if c_acc:
                        parts.append(f"Gear: {c_acc}")
                    if c_vibe:
                        parts.append(f"Vibe: {c_vibe}")
                    character_directive = f"\n[CHARACTER CONSTRAINT & VISUAL LOREBOOK]: {', '.join(parts)}."

            effective_directives = (character_directive + " " + (user_directives or "").strip() + context_directive).strip()
            if not has_image and not effective_directives:
                effective_directives = "Generate a visually stunning, cinematic scene with intricate details."

            # 5. Construct Task Prompt
            task_prompt = build_task_prompt(
                prompt_type=prompt_type,
                artistic_style=artistic_style,
                directives=effective_directives,
                input_text=effective_directives if not has_image else "",
                is_dual_prompt=enable_dual,
                is_artifact_audit=enable_audit,
            )

            # 5b. Regional Prompting Directive (#94)
            if regional_mode and regional_mode != "Disabled":
                if regional_mode == "Left / Right / Background":
                    reg_spec = "[LEFT: subject/elements on the left] | [RIGHT: subject/elements on the right] | [BACKGROUND: setting, environment, distant depth]"
                elif regional_mode == "Foreground / Background":
                    reg_spec = "[FOREGROUND: main focal subject, micro-textures, primary light] | [BACKGROUND: environment, distant scenery, ambient atmosphere]"
                elif regional_mode == "Grid 2x2 Quadrants":
                    reg_spec = "[TOP-LEFT: ...] | [TOP-RIGHT: ...] | [BOTTOM-LEFT: ...] | [BOTTOM-RIGHT: ...]"
                else:
                    reg_spec = "[ZONE_A: ...] | [ZONE_B: ...] | [BACKGROUND: ...]"
                task_prompt += f"\n\n# REGIONAL COMPOSITION DIRECTIVE (#94):\nDeconstruct the composition into isolated spatial zones according to mode '{regional_mode}'. Structure your <PROMPT> block strictly with regional demarcators:\n{reg_spec}"

            stream_ids = self._stream_targets(unique_id, prompt)

            # 6. Execute VLM inference per job and post-process into Prompt / Tags / Negative
            prompts, tags_out, negatives, raws = [], [], [], []
            for job_idx, (pil_images, job_multi, job_seed) in enumerate(jobs):
                if hasattr(stoiqo_model, "generate_single"):
                    raw_response = stoiqo_model.generate_single(
                        pil_images=pil_images,
                        task_prompt=task_prompt,
                        system_prompt=active_system_prompt,
                        max_new_tokens=max_new_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        top_k=top_k,
                        repetition_penalty=repetition_penalty,
                        is_multi_image=job_multi,
                        seed=job_seed,
                        node_id=stream_ids,
                    )
                else:
                    logger.warning("[STOIQO] Prompt Synthesizer: model pipe has no generate_single(); using placeholder output.")
                    raw_response = (
                        f"<PROMPT>A breathtaking image of {effective_directives or 'an elegant scene'}, {artistic_style}</PROMPT>\n"
                        f"<TAGS>masterpiece, 8k, detailed, {prompt_type}</TAGS>\n"
                        f"<NEGATIVE>blurry, bad anatomy, low quality, artifacts, watermark</NEGATIVE>"
                    )

                prompt_text, tags_text, negative_text, _ = post_process_caption(
                    raw_response,
                    is_dual_active=enable_dual,
                    is_audit_active=enable_audit,
                    negative_prompt_prefix=negative_prefix,
                    prompt_type=prompt_type,
                    seed=job_seed,
                )

                if character_negative.strip():
                    if negative_text and negative_text.strip():
                        negative_text = f"{negative_text.strip()}, {character_negative.strip()}"
                    else:
                        negative_text = character_negative.strip()

                prompts.append(prompt_text)
                tags_out.append(tags_text)
                negatives.append(negative_text)
                raws.append(raw_response)
                if len(jobs) > 1:
                    print(f"[STOIQO] [Image {job_idx + 1}/{len(jobs)}] Caption: {str(prompt_text)[:80]}...")

            return inject_telemetry({
                "ui": {
                    "text": prompts,
                },
                "result": (prompts, tags_out, negatives, raws),
            }, timer.get_stats())
