"""
[STOIQO] Prompt Generator Node
Lean, high-efficiency vision-language prompt generation node.
Generates prompt, tags, and surgical negative prompt automatically with tuned defaults,
while accepting modular connections for Config, Character Memory, and Multi-Image reasoning.
"""

import hashlib
import logging
import re
import traceback
import numpy as np
import torch

logger = logging.getLogger(__name__)

# In-memory prompt cache for accelerating repeat iterations with identical inputs
_PROMPT_CACHE = {}
_MAX_PROMPT_CACHE_ENTRIES = 128


def _compute_prompt_cache_key(model_ref, job_idx, pil_images, task_prompt, system_prompt, seed, temp, top_p, top_k):
    h = hashlib.sha256()
    h.update(str(getattr(model_ref, "model_name", id(model_ref))).encode())
    h.update(str(task_prompt).encode())
    h.update(str(system_prompt).encode())
    h.update(f"{seed}_{temp}_{top_p}_{top_k}_{job_idx}".encode())
    if pil_images is not None:
        if isinstance(pil_images, (list, tuple)):
            for p in pil_images:
                if hasattr(p, "tobytes"):
                    h.update(p.tobytes()[:4096])
        elif hasattr(pil_images, "tobytes"):
            h.update(pil_images.tobytes()[:4096])
    return h.hexdigest()


def _mentions(text: str, term: str) -> bool:
    """Whole-word, case-insensitive match (avoids substring false positives)."""
    if not term:
        return False
    return re.search(r"(?<!\w)" + re.escape(term.strip()) + r"(?!\w)", text, re.IGNORECASE) is not None


try:
    from ..core import (
        build_task_prompt,
        build_dynamic_system_prompt,
        post_process_caption,
        tensor_to_pil,
        resolve_system_prompt,
        resolve_prompt_type,
        resolve_artistic_style,
        NodeTelemetryTimer,
        inject_telemetry,
        SYSTEM_PROMPT_CHOICES,
        PROMPT_TYPES,
        ARTISTIC_STYLES,
    )
except (ImportError, ValueError):
    from core import (
        build_task_prompt,
        build_dynamic_system_prompt,
        post_process_caption,
        tensor_to_pil,
        resolve_system_prompt,
        resolve_prompt_type,
        resolve_artistic_style,
        NodeTelemetryTimer,
        inject_telemetry,
        SYSTEM_PROMPT_CHOICES,
        PROMPT_TYPES,
        ARTISTIC_STYLES,
    )


class StoiqoPromptGeneratorNode:
    """
    [STOIQO] Prompt Generator (All-in-One Engine)
    Autonomous vision-language and prompt synthesis studio.
    Generates high-fidelity Prompt, concise Tags, and surgical Negative prompt in one pass.
    Features integrated persona presets, structural output formatting, aesthetic styling,
    multi-image multimodal reasoning, regional composition directives, and standard ComfyUI outputs.
    """

    PRESETS = [
        "Balanced Synthesizer (Recommended)",
        "Maximum Creativity (Wild Ideation)",
        "Scientific / Accurate Visual Description",
        "Synthetic Captioning for LoRA / Training",
        "Deterministic / Exact Logic (Greedy)",
        "Cinematic Storyteller",
        "Custom (Manual Tuning)",
    ]

    PRESET_VALUES = {
        "Balanced Synthesizer (Recommended)": {
            "temperature": 0.65,
            "max_new_tokens": 1024,
            "top_p": 0.90,
            "top_k": 50,
            "repetition_penalty": 1.15,
        },
        "Maximum Creativity (Wild Ideation)": {
            "temperature": 0.95,
            "max_new_tokens": 1536,
            "top_p": 0.95,
            "top_k": 80,
            "repetition_penalty": 1.10,
        },
        "Scientific / Accurate Visual Description": {
            "temperature": 0.20,
            "max_new_tokens": 768,
            "top_p": 0.80,
            "top_k": 30,
            "repetition_penalty": 1.20,
        },
        "Synthetic Captioning for LoRA / Training": {
            "temperature": 0.35,
            "max_new_tokens": 512,
            "top_p": 0.85,
            "top_k": 40,
            "repetition_penalty": 1.15,
        },
        "Deterministic / Exact Logic (Greedy)": {
            "temperature": 0.0,
            "max_new_tokens": 512,
            "top_p": 0.0,
            "top_k": 1,
            "repetition_penalty": 1.20,
        },
        "Cinematic Storyteller": {
            "temperature": 0.75,
            "max_new_tokens": 1280,
            "top_p": 0.92,
            "top_k": 60,
            "repetition_penalty": 1.12,
        },
    }

    SYSTEM_PERSONAS = [
        "Auto-Detect / Balanced",
        "Text-to-Prompt Expansion Engine",
        "Generative Captioning (Single Image)",
        "Multi-Image Synthesis Engine",
        "Visual Prompt Synthesizer",
        "Custom",
    ]

    FUSION_MODES = [
        "Auto (Fuse 2-4 images, Batch if >4)",
        "Contextual Fusion (Blend Style & Subject)",
        "Comparative Difference (What Changed)",
        "Character & Style Consistency",
        "Sequential Angle / Multi-View",
        "Subject + Background Harmonization",
        "Storyboard / Temporal Sequence",
        "Independent Batch (Caption each image separately for datasets)",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        p_types = PROMPT_TYPES if PROMPT_TYPES else ["Detailed Narrative (Long)"]
        a_styles = ARTISTIC_STYLES if ARTISTIC_STYLES else ["Auto-Detect / Preserve Original"]

        return {
            "required": {
                "prompt_type": (
                    p_types,
                    {
                        "default": "Detailed Narrative (Long)" if "Detailed Narrative (Long)" in p_types else p_types[0],
                        "tooltip": "Formato strutturale di output per il prompt generato.",
                    },
                ),
                "prompt_style": (
                    a_styles,
                    {
                        "default": "Auto-Detect / Preserve Original" if "Auto-Detect / Preserve Original" in a_styles else a_styles[0],
                        "tooltip": "Stile estetico e archetipo visivo da applicare.",
                    },
                ),
                "custom_modifications": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "Modifiche e istruzioni di regia (es. renderlo più dark, pioggia battente, luce al neon, abito da sera)...",
                        "tooltip": "Istruzioni di regia e modifiche aggiuntive da applicare al soggetto.",
                    },
                ),
                "seed": (
                    "INT",
                    {
                        "default": 42,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "control_after_generate": True,
                        "tooltip": "Seed per generazioni riproducibili o randomizzabili.",
                    },
                ),
            },
            "optional": {
                "text_input": (
                    "STRING",
                    {
                        "forceInput": True,
                        "tooltip": "Soggetto / prompt di partenza in formato testuale (collegabile da Primitive, Text Node o stringa).",
                    },
                ),
                "image_input": (
                    "IMAGE",
                    {
                        "tooltip": "Soggetto / riferimento visivo in formato immagine o batch (supporta anche batch multi-immagine da Image Loader).",
                    },
                ),
                "model": (
                    "*",
                    {
                        "tooltip": "Modello cognitivo VLM o CLIP da Universal Model Loader.",
                    },
                ),
                "character": (
                    "*",
                    {
                        "tooltip": "Modulo opzionale [STOIQO] Character Memory Bank (Lorebook & DNA visivo del personaggio).",
                    },
                ),
                "preset": (
                    cls.PRESETS,
                    {
                        "default": cls.PRESETS[0],
                        "tooltip": "Preset di calibrazione per il comportamento di sintesi LLM/VLM.",
                    },
                ),
                "fusion_mode": (
                    cls.FUSION_MODES,
                    {
                        "default": cls.FUSION_MODES[0],
                        "tooltip": "Strategia di ragionamento multimodale quando image_input contiene più immagini.",
                    },
                ),
                "system_prompt": (
                    cls.SYSTEM_PERSONAS,
                    {
                        "default": cls.SYSTEM_PERSONAS[0],
                        "tooltip": "Ruolo cognitivo o AI persona che guida la costruzione del prompt.",
                    },
                ),
                "custom_system_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "Custom system instructions (active when system_prompt is 'Custom')...",
                        "tooltip": "Istruzioni di sistema custom passate direttamente al VLM/LLM.",
                    },
                ),
                "negative_prompt_prefix": (
                    "STRING",
                    {
                        "default": "",
                        "placeholder": "e.g. worst quality, low quality, blurry, ",
                        "tooltip": "Prefisso anteposto automaticamente al negative prompt generato.",
                    },
                ),
                "temperature": (
                    "FLOAT",
                    {
                        "default": 0.65,
                        "min": 0.0,
                        "max": 2.0,
                        "step": 0.05,
                        "tooltip": "Creatività e varianza (0.0 = deterministico, 0.65 = bilanciato, >0.9 = creativo).",
                    },
                ),
                "max_new_tokens": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 64,
                        "max": 4096,
                        "step": 64,
                        "tooltip": "Budget massimo di token per il prompt generato.",
                    },
                ),
                "top_p": (
                    "FLOAT",
                    {
                        "default": 0.90,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.05,
                        "tooltip": "Soglia di probabilità per Nucleus Sampling.",
                    },
                ),
                "top_k": (
                    "INT",
                    {
                        "default": 50,
                        "min": 1,
                        "max": 100,
                        "step": 1,
                        "tooltip": "Cutoff Top-K sul vocabolario.",
                    },
                ),
                "repetition_penalty": (
                    "FLOAT",
                    {
                        "default": 1.15,
                        "min": 1.0,
                        "max": 2.0,
                        "step": 0.05,
                        "tooltip": "Penalità applicata ai token ripetuti.",
                    },
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
    OUTPUT_IS_LIST = (True, True, True, True)
    FUNCTION = "generate_prompt"
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

    def generate_prompt(
        self,
        prompt_type: str = "Detailed Narrative (Long)",
        prompt_style: str = "Auto-Detect / Preserve Original",
        custom_modifications: str = "",
        seed: int = 42,
        text_input: str = None,
        image_input: torch.Tensor = None,
        model=None,
        character=None,
        preset: str = "Balanced Synthesizer (Recommended)",
        fusion_mode: str = "Auto (Fuse 2-4 images, Batch if >4)",
        system_prompt: str = "Auto-Detect / Balanced",
        custom_system_prompt: str = "",
        negative_prompt_prefix: str = "",
        temperature: float = 0.65,
        max_new_tokens: int = 1024,
        top_p: float = 0.90,
        top_k: int = 50,
        repetition_penalty: float = 1.15,
        # Backward-compatibility alias inputs
        config: dict = None,
        multi_image: dict = None,
        user_directives: str = None,
        artistic_style: str = None,
        image: torch.Tensor = None,
        image_2: torch.Tensor = None,
        image_3: torch.Tensor = None,
        image_4: torch.Tensor = None,
        regional_mode: str = "Disabled",
        character_context=None,
        enable_cache: bool = False,
        clip=None,
        stoiqo_model=None,
        style_directives: dict = None,
        sampling_options: dict = None,
        multi_image_context: dict = None,
        image_mode: str = None,
        unique_id: str = None,
        prompt: dict = None,
        extra_pnginfo: dict = None,
        **kwargs,
    ):
        # 0. Harmonize inputs and aliases
        subject_text = (text_input or kwargs.get("text") or "").strip()
        mods = (custom_modifications or user_directives or "").strip()
        chosen_style = prompt_style or artistic_style or "Auto-Detect / Preserve Original"
        chosen_type = prompt_type or "Detailed Narrative (Long)"

        active_char = character if character is not None else character_context
        active_mi = multi_image if multi_image is not None else multi_image_context
        active_image = image_input if image_input is not None else image

        # Resolve incoming model polymorphism
        active_vlm = model if model is not None else stoiqo_model
        if active_vlm is not None:
            if hasattr(active_vlm, "generate_single"):
                stoiqo_model = active_vlm
            elif hasattr(active_vlm, "generate") or hasattr(active_vlm, "tokenize") or hasattr(active_vlm, "cond_stage_model"):
                if clip is None:
                    clip = active_vlm
                stoiqo_model = None
            else:
                stoiqo_model = active_vlm

        # Handle flexible positional invocation
        if isinstance(stoiqo_model, str) and not mods and not subject_text:
            mods = stoiqo_model
            stoiqo_model = None
        if isinstance(model, str) and not mods and not subject_text:
            mods = model
            model = None

        active_node_name = "PromptGenerator"
        with NodeTelemetryTimer(node_id=unique_id, node_name=active_node_name) as timer:
            # 1. Resolve Config and Settings (including integrated preset values)
            cfg = dict(config) if isinstance(config, dict) else {}
            if preset in self.PRESET_VALUES and preset != "Custom (Manual Tuning)" and not cfg:
                pv = self.PRESET_VALUES[preset]
                default_temp = pv["temperature"]
                default_tokens = pv["max_new_tokens"]
                default_top_p = pv["top_p"]
                default_top_k = pv["top_k"]
                default_rep_pen = pv["repetition_penalty"]
            else:
                default_temp = temperature if temperature is not None else 0.65
                default_tokens = max_new_tokens if max_new_tokens is not None else 1024
                default_top_p = top_p if top_p is not None else 0.90
                default_top_k = top_k if top_k is not None else 50
                default_rep_pen = repetition_penalty if repetition_penalty is not None else 1.15

            style = style_directives if isinstance(style_directives, dict) else {}
            sampling = sampling_options if isinstance(sampling_options, dict) else {}

            resolved_prompt_type = resolve_prompt_type(cfg.get("prompt_type") or style.get("prompt_type") or chosen_type)
            resolved_artistic_style = resolve_artistic_style(cfg.get("artistic_style") or style.get("artistic_style") or chosen_style)

            enable_dual = bool(cfg.get("enable_dual_prompt", False)) or bool(style.get("enable_dual_prompt", False)) or ("Dual Prompt" in str(resolved_prompt_type))
            enable_audit = bool(cfg.get("audit_artifacts", False)) or bool(style.get("audit_artifacts", False)) or any(
                k in str(resolved_prompt_type) for k in ("Artifact", "Negative Prompt", "Flaw")
            )
            negative_prefix = cfg.get("negative_prompt_prefix") or style.get("negative_prompt_prefix", "") or negative_prompt_prefix or ""

            active_temperature = float(cfg.get("temperature", sampling.get("temperature", default_temp)))
            active_top_p = float(cfg.get("top_p", sampling.get("top_p", default_top_p)))
            active_top_k = int(cfg.get("top_k", sampling.get("top_k", default_top_k)))
            active_repetition_penalty = float(cfg.get("repetition_penalty", sampling.get("repetition_penalty", default_rep_pen)))
            active_max_new_tokens = int(cfg.get("max_new_tokens", sampling.get("max_new_tokens", default_tokens)))
            target_megapixel = float(cfg.get("target_megapixel", sampling.get("target_megapixel", 1.0)))
            active_seed = int(cfg.get("seed", sampling.get("seed", seed)))

            active_regional_mode = cfg.get("regional_mode") or regional_mode or "Disabled"
            active_fusion_mode = image_mode or fusion_mode or "Blend Style & Subject"

            # 2. Collect and Resolve Input Images
            context_directive = ""
            jobs = []
            raw_images = [img for img in (active_image, image_2, image_3, image_4) if img is not None and isinstance(img, torch.Tensor) and img.numel() > 0]
            if active_mi and isinstance(active_mi, dict) and "images" in active_mi:
                for img_t in active_mi["images"]:
                    if img_t is not None and isinstance(img_t, torch.Tensor) and img_t.numel() > 0:
                        raw_images.append(img_t)
                if "fusion_mode" in active_mi:
                    active_fusion_mode = active_mi["fusion_mode"]

            tensors = []
            for img_t in raw_images:
                if img_t.ndim == 4:
                    for b in range(img_t.shape[0]):
                        tensors.append(img_t[b:b + 1])
                elif img_t.ndim == 3:
                    tensors.append(img_t.unsqueeze(0))

            if tensors:
                batch_size = len(tensors)
                if batch_size == 1:
                    pil_img = tensor_to_pil(tensors[0], target_megapixel=target_megapixel)[0]
                    jobs.append((pil_img, False, active_seed))
                elif "Independent Batch" in str(active_fusion_mode) or (batch_size > 4 and not active_mi):
                    for i in range(batch_size):
                        pil_img = tensor_to_pil(tensors[i], target_megapixel=target_megapixel)[0]
                        jobs.append((pil_img, False, active_seed + i))
                else:
                    per_image_mpx = max(0.35, min(target_megapixel, 1.5 / batch_size))
                    imgs = [tensor_to_pil(t, target_megapixel=per_image_mpx)[0] for t in tensors]
                    context_directive = f"\n[MULTI-IMAGE CROSS-GENERATION DIRECTIVE]: Apply {active_fusion_mode} across the {batch_size} provided reference images."
                    jobs.append((imgs, True, active_seed))

            has_image = bool(jobs)
            is_multi_image = has_image and jobs[0][1]
            if not has_image:
                jobs.append((None, False, active_seed))

            # System prompt selection
            cfg_sys_choice = cfg.get("system_prompt") or style.get("system_prompt") or system_prompt
            cfg_custom_sys = cfg.get("custom_system_prompt") or style.get("custom_system_prompt") or custom_system_prompt or ""

            if not cfg_sys_choice or cfg_sys_choice == "Auto-Detect / Balanced":
                if is_multi_image:
                    active_system_prompt_choice = "Multi-Image Synthesis Engine"
                elif has_image:
                    active_system_prompt_choice = "Generative Captioning (Single Image)"
                else:
                    active_system_prompt_choice = "Text-to-Prompt Expansion Engine"
            else:
                active_system_prompt_choice = cfg_sys_choice

            active_system_prompt = resolve_system_prompt(
                active_system_prompt_choice, cfg_custom_sys, has_image=has_image, is_multi_image=is_multi_image
            )

            is_manual_custom = (
                active_system_prompt_choice == "✏️ Custom (Manual Override)"
                or "Custom" in str(active_system_prompt_choice)
                or bool(cfg_custom_sys.strip())
            )
            if not is_manual_custom:
                active_system_prompt = build_dynamic_system_prompt(
                    base_system_prompt=active_system_prompt,
                    prompt_type=resolved_prompt_type,
                    artistic_style=resolved_artistic_style,
                )
                print(f"[STOIQO] System prompt fused with type='{resolved_prompt_type}' style='{resolved_artistic_style}'.")

            # 3. Integrate Character Memory Bank
            character_directive = ""
            character_negative = ""
            if active_char and isinstance(active_char, dict):
                c_mode = active_char.get("injection_mode", "Smart Detect (Inject only when Name or Trigger is in Prompt)")
                c_name = active_char.get("character_name", "")
                c_tag = active_char.get("trigger_tag", "")
                c_dna = active_char.get("character_dna", "")
                c_outfit = active_char.get("signature_outfit", "")
                c_acc = active_char.get("accessories_props", "")
                c_vibe = active_char.get("personality_vibe", "")
                character_negative = active_char.get("negative_constraints", "")

                should_inject_char = False
                if c_mode == "Always Prepend (Force Character DNA)":
                    should_inject_char = True
                elif "Smart Detect" in c_mode:
                    combined_probe = f"{subject_text} {mods}"
                    if not combined_probe.strip() or _mentions(combined_probe, c_name) or _mentions(combined_probe, c_tag):
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

            # Construct effective directives combining subject, modifications, and character lore
            directive_parts = []
            if character_directive:
                directive_parts.append(character_directive.strip())
            if subject_text:
                directive_parts.append(f"Subject / Base Concept: {subject_text}")
            if mods:
                directive_parts.append(f"Directives & Modifications: {mods}")
            if context_directive:
                directive_parts.append(context_directive.strip())

            effective_directives = "\n".join(directive_parts).strip()
            if not has_image and not effective_directives:
                effective_directives = "Generate a visually stunning, cinematic scene with intricate details."

            # 4. Construct Task Prompt
            input_for_task = effective_directives
            if has_image:
                # If image is provided, visual subject is the image; text is the modifications to apply
                img_directives = []
                if subject_text:
                    img_directives.append(f"Subject Reference: {subject_text}")
                if mods:
                    img_directives.append(f"Modifications to Apply: {mods}")
                input_for_task = "\n".join(img_directives) if img_directives else "Describe and enhance this image."

            task_prompt = build_task_prompt(
                prompt_type=resolved_prompt_type,
                artistic_style=resolved_artistic_style,
                directives=effective_directives,
                input_text=input_for_task,
                is_dual_prompt=enable_dual,
                is_artifact_audit=enable_audit,
            )

            # 4b. Regional Prompting Directive
            if active_regional_mode and active_regional_mode != "Disabled":
                if active_regional_mode == "Left / Right / Background":
                    reg_spec = "[LEFT: subject/elements on the left] | [RIGHT: subject/elements on the right] | [BACKGROUND: setting, environment, distant depth]"
                elif active_regional_mode == "Foreground / Background":
                    reg_spec = "[FOREGROUND: main focal subject, micro-textures, primary light] | [BACKGROUND: environment, distant scenery, ambient atmosphere]"
                elif active_regional_mode == "Grid 2x2 Quadrants":
                    reg_spec = "[TOP-LEFT: ...] | [TOP-RIGHT: ...] | [BOTTOM-LEFT: ...] | [BOTTOM-RIGHT: ...]"
                else:
                    reg_spec = "[ZONE_A: ...] | [ZONE_B: ...] | [BACKGROUND: ...]"
                task_prompt += f"\n\n# REGIONAL COMPOSITION DIRECTIVE (#94):\nDeconstruct the composition into isolated spatial zones according to mode '{active_regional_mode}'. Structure your <PROMPT> block strictly with regional demarcators:\n{reg_spec}"

            stream_ids = self._stream_targets(unique_id, prompt)

            # 5. Execute VLM inference per job and post-process into Prompt / Tags / Negative
            prompts, tags_out, negatives, raws = [], [], [], []
            try:
                for job_idx, (pil_images, job_multi, job_seed) in enumerate(jobs):
                    raw_response = None
                    cache_key = None
                    if enable_cache:
                        cache_key = _compute_prompt_cache_key(
                            active_vlm, job_idx, pil_images, task_prompt, active_system_prompt, job_seed, active_temperature, active_top_p, active_top_k
                        )
                        if cache_key in _PROMPT_CACHE:
                            raw_response = _PROMPT_CACHE[cache_key]
                            print(f"[STOIQO] Prompt cache hit for job {job_idx + 1}/{len(jobs)}; returning cached response.")

                    if raw_response is None:
                        if hasattr(stoiqo_model, "generate_single"):
                            raw_response = stoiqo_model.generate_single(
                                pil_images=pil_images,
                                task_prompt=task_prompt,
                                system_prompt=active_system_prompt,
                                max_new_tokens=active_max_new_tokens,
                                temperature=active_temperature,
                                top_p=active_top_p,
                                top_k=active_top_k,
                                repetition_penalty=active_repetition_penalty,
                                is_multi_image=job_multi,
                                seed=job_seed,
                                node_id=stream_ids,
                            )
                        elif clip is not None and hasattr(clip, "generate") and hasattr(clip, "tokenize"):
                            try:
                                full_prompt_text = task_prompt or effective_directives

                                # Convert image input to a PyTorch tensor [B, H, W, 3] expected by ComfyUI's Qwen3VL tokenizer
                                clip_image_tensor = None
                                if pil_images is not None:
                                    if isinstance(pil_images, torch.Tensor):
                                        clip_image_tensor = pil_images if pil_images.ndim == 4 else pil_images.unsqueeze(0)
                                    elif isinstance(pil_images, (list, tuple)):
                                        t_parts = []
                                        for img in pil_images:
                                            if isinstance(img, torch.Tensor):
                                                t_parts.append(img if img.ndim == 4 else img.unsqueeze(0))
                                            elif img is not None:
                                                t_arr = np.array(img).astype(np.float32) / 255.0
                                                t_parts.append(torch.from_numpy(t_arr)[None,])
                                        if t_parts:
                                            try:
                                                clip_image_tensor = torch.cat(t_parts, dim=0)
                                            except Exception:
                                                clip_image_tensor = t_parts[0]
                                    else:
                                        t_arr = np.array(pil_images).astype(np.float32) / 255.0
                                        clip_image_tensor = torch.from_numpy(t_arr)[None,]

                                tokens = clip.tokenize(
                                    full_prompt_text,
                                    image=clip_image_tensor,
                                    skip_template=False,
                                    min_length=1,
                                    system_prompt=active_system_prompt,
                                )
                                do_sample_flag = bool(cfg.get("do_sample", active_temperature >= 0.01))
                                generated_ids = clip.generate(
                                    tokens,
                                    do_sample=do_sample_flag,
                                    max_length=active_max_new_tokens,
                                    temperature=active_temperature,
                                    top_k=max(1, active_top_k),
                                    top_p=active_top_p,
                                    repetition_penalty=active_repetition_penalty,
                                    seed=job_seed,
                                )
                                decoded_text = clip.decode(generated_ids)
                                reasoning, _, clean_text = decoded_text.partition("</think>")
                                if not reasoning.lstrip().startswith("<think>") and not full_prompt_text.rstrip().endswith("<think>"):
                                    clean_text = decoded_text
                                clean_text = clean_text.strip()
                                if "<PROMPT>" in clean_text:
                                    raw_response = clean_text
                                else:
                                    raw_response = (
                                        f"<PROMPT>{clean_text}</PROMPT>\n"
                                        f"<TAGS>masterpiece, detailed, 8k, {resolved_prompt_type}</TAGS>\n"
                                        f"<NEGATIVE>blurry, bad anatomy, low quality, artifacts, watermark</NEGATIVE>"
                                    )
                                print(f"[STOIQO] VLM text generation successful: {clean_text[:120]}...")
                            except Exception as clip_err:
                                logger.warning(f"[STOIQO] CLIP text generation error: {clip_err}; using fallback.")
                                traceback.print_exc()
                                raw_response = (
                                    f"<PROMPT>{effective_directives}, {resolved_artistic_style}</PROMPT>\n"
                                    f"<TAGS>masterpiece, 8k, detailed, {resolved_prompt_type}</TAGS>\n"
                                    f"<NEGATIVE>blurry, bad anatomy, low quality, artifacts, watermark</NEGATIVE>"
                                )
                        else:
                            logger.warning("[STOIQO] Prompt Generator: neither stoiqo_model nor generative clip provided; using fallback expansion.")
                            raw_response = (
                                f"<PROMPT>A breathtaking image of {effective_directives or 'an elegant scene'}, {resolved_artistic_style}</PROMPT>\n"
                                f"<TAGS>masterpiece, 8k, detailed, {resolved_prompt_type}</TAGS>\n"
                                f"<NEGATIVE>blurry, bad anatomy, low quality, artifacts, watermark</NEGATIVE>"
                            )

                        if enable_cache and cache_key:
                            if len(_PROMPT_CACHE) >= _MAX_PROMPT_CACHE_ENTRIES:
                                _PROMPT_CACHE.pop(next(iter(_PROMPT_CACHE)))
                            _PROMPT_CACHE[cache_key] = raw_response

                    prompt_text, tags_text, negative_text, _ = post_process_caption(
                        raw_response,
                        is_dual_active=enable_dual,
                        is_audit_active=enable_audit,
                        negative_prompt_prefix=negative_prefix,
                        prompt_type=resolved_prompt_type,
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
            finally:
                if active_vlm is not None and not getattr(active_vlm, "keep_in_vram", True):
                    if hasattr(active_vlm, "unload_model"):
                        active_vlm.unload_model()

            if not has_image:
                mode_key = "text_expansion"
                mode_label = "Text Expansion"
                mode_count = 0
            elif is_multi_image:
                fused_cnt = len(jobs[0][0]) if (jobs and isinstance(jobs[0][0], list)) else 2
                mode_key = "multi_fusion"
                mode_label = f"Multi-Image Fusion ({fused_cnt} images)"
                mode_count = fused_cnt
            elif len(jobs) > 1:
                mode_key = "batch_caption"
                mode_label = f"Batch Caption ({len(jobs)} images)"
                mode_count = len(jobs)
            else:
                mode_key = "single_image"
                mode_label = "Single Image Vision"
                mode_count = 1

            mode_payload = {
                "mode": mode_key,
                "label": mode_label,
                "count": mode_count,
                "prompt_type": resolved_prompt_type,
                "artistic_style": resolved_artistic_style,
            }

            return inject_telemetry({
                "ui": {
                    "text": prompts,
                    "stoiqo_mode": [mode_payload],
                },
                "result": (prompts, tags_out, negatives, raws),
            }, timer.get_stats())

    # Backward compatibility method
    def synthesize_prompt(self, *args, **kwargs):
        kwargs["_is_synthesizer"] = True
        if args:
            if len(args) == 1:
                if isinstance(args[0], str):
                    kwargs.setdefault("user_directives", args[0])
                else:
                    kwargs.setdefault("model", args[0])
            elif len(args) >= 2:
                if isinstance(args[0], str):
                    kwargs.setdefault("user_directives", args[0])
                    kwargs.setdefault("prompt_type", args[1])
                else:
                    kwargs.setdefault("model", args[0])
                    kwargs.setdefault("user_directives", args[1])
                if len(args) >= 3:
                    kwargs.setdefault("image", args[2])
        return self.generate_prompt(**kwargs)

