"""
[STOIQO] Prompt Generator Engine — Main ComfyUI Node
"""

import re
import random
import numpy as np
import torch

try:
    from ..core import (
        MODEL_PRESETS,
        CUSTOM_MODEL_KEY,
        MODEL_SELECTION_CHOICES,
        MODEL_MODES,
        QUANTIZATION_OPTIONS,
        ATTENTION_OPTIONS,
        BATCH_MODES,
        SYSTEM_PROMPT_PRESETS,
        CUSTOM_SYSTEM_PROMPT_KEY,
        SYSTEM_PROMPT_CHOICES,
        PROMPT_TYPES,
        resolve_prompt_type,
        ARTISTIC_STYLES,
        resolve_artistic_style,
        CAPTION_STYLES,
        KREA2_PROMPT_IMAGE,
        KREA2_PROMPT_TEXT,
        KREA2_PROMPT_MULTI_IMAGE,
        resolve_system_prompt,
        tensor_to_pil,
        build_task_prompt,
        parse_dual_prompt,
        parse_artifact_audit,
        parse_three_way_prompt,
        process_lora_caption,
        post_process_caption,
        save_artifacts,
        build_dataset_manifest,
        get_original_filename,
        open_native_folder_dialog,
        ModelManager,
    )
except (ImportError, ValueError):
    from core import (
        MODEL_PRESETS,
        CUSTOM_MODEL_KEY,
        MODEL_SELECTION_CHOICES,
        MODEL_MODES,
        QUANTIZATION_OPTIONS,
        ATTENTION_OPTIONS,
        BATCH_MODES,
        SYSTEM_PROMPT_PRESETS,
        CUSTOM_SYSTEM_PROMPT_KEY,
        SYSTEM_PROMPT_CHOICES,
        PROMPT_TYPES,
        resolve_prompt_type,
        ARTISTIC_STYLES,
        resolve_artistic_style,
        CAPTION_STYLES,
        KREA2_PROMPT_IMAGE,
        KREA2_PROMPT_TEXT,
        KREA2_PROMPT_MULTI_IMAGE,
        resolve_system_prompt,
        tensor_to_pil,
        build_task_prompt,
        parse_dual_prompt,
        parse_artifact_audit,
        parse_three_way_prompt,
        process_lora_caption,
        post_process_caption,
        save_artifacts,
        build_dataset_manifest,
        get_original_filename,
        open_native_folder_dialog,
        ModelManager,
    )


def register_stoiqo_routes():
    """Registers /stoiqo/browse_folder endpoint with ComfyUI's PromptServer."""
    try:
        from server import PromptServer
        from aiohttp import web
        import asyncio

        if hasattr(PromptServer, "instance") and PromptServer.instance is not None:
            routes = PromptServer.instance.routes
            if not any(getattr(r, "path", None) == "/stoiqo/browse_folder" for r in routes):
                @routes.post("/stoiqo/browse_folder")
                async def browse_model_folder(request):
                    data = {}
                    try:
                        if request.can_read_body:
                            data = await request.json()
                    except Exception:
                        pass
                    initial_dir = data.get("initial_dir", "")
                    selected_path = await asyncio.to_thread(open_native_folder_dialog, initial_dir)
                    return web.json_response({"path": selected_path})
    except Exception as exc:
        print(f"[STOIQO] Notice: route registration deferred: {exc}")


register_stoiqo_routes()


class StoiqoPromptGeneratorEngineNode:
    """
    Vision-Language Prompt Engineering Node for ComfyUI.
    Empowered by Qwen2.5-VL with tiered 4-bit quantizations, dual prompt synthesis (CLIP/T5),
    negative prompt artifact auditing, and LoRA dataset processing tools.
    """

    def __init__(self):
        register_stoiqo_routes()
        self.model_mgr = ModelManager()

    # Backward-compatibility property delegates
    @property
    def model(self):
        return self.model_mgr.model

    @property
    def processor(self):
        return self.model_mgr.processor

    @property
    def current_model_repo(self):
        return self.model_mgr.current_model_repo

    @property
    def current_attn(self):
        return self.model_mgr.current_attn

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # ── 1. MODEL & HARDWARE ENGINE ──
                "stoiqo_model": ("STOIQO_MODEL", {"tooltip": "Connect the Model Loader here."}),
                "target_megapixel": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.1,
                        "max": 4.0,
                        "step": 0.1,
                        "round": 0.01,
                        "tooltip": "Visual resolution budget in Megapixels (~1.0 Mpx = ~1024x1024). Resized to multiples of 28 for ViT tokens while preserving aspect ratio. Lower = faster & less VRAM, higher = finer details.",
                    },
                ),
                # ── 2. TASK & ARTISTIC DIRECTIVES ──
                "batch_mode": (
                    BATCH_MODES,
                    {
                        "default": "Independent Images",
                        "tooltip": "'Independent Images': processes each image in a batch separately (ideal for LoRA dataset tagging). 'Multi-Image Comparison / Fusion': feeds multiple images simultaneously into the LLM (<Image 1>, <Image 2>) to compare differences or synthesize a single fused prompt.",
                    },
                ),
                "system_prompt": (
                    SYSTEM_PROMPT_CHOICES,
                    {
                        "default": SYSTEM_PROMPT_CHOICES[0],
                        "tooltip": "AI Persona & Core Competence: sets the underlying role of the vision-language model. Choose a specialized preset, or select 'Custom' to write your own system instructions below.",
                    },
                ),
                "custom_system_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "Active only when system_prompt = 'Custom'. Write your custom system instructions here...",
                        "tooltip": "Custom system instructions. Automatically revealed on canvas only when system_prompt is set to 'Custom'.",
                    },
                ),
                "prompt_type": (
                    PROMPT_TYPES,
                    {
                        "default": PROMPT_TYPES[0],
                        "tooltip": "Structural output format: Structured Categories (default modular key-value), Detailed Narrative (dense prose for Flux/T5), Short Summary (concise <25 words), Tags & Keywords (Western flat list), Booru Tags (Danbooru anime taxonomy), or Cinematic & Video Script (motion & camera).",
                    },
                ),
                "artistic_style": (
                    ARTISTIC_STYLES,
                    {
                        "default": ARTISTIC_STYLES[0],
                        "tooltip": "Aesthetic style directive injected into prompt generation: Auto-Detect, Photorealistic, Anime, 3D CGI, Pencil Sketch, Concept Art, Oil Painting, Cyberpunk, Vintage Film.",
                    },
                ),
                "user_directives": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "Specific modifications or attribute overrides (e.g. 'capelli mori', 'abito rosso', 'luce al neon')...",
                        "tooltip": "User modification directives (Supreme Priority). Specifies attributes or elements to overwrite/change while keeping the rest of the input intact.",
                    },
                ),

                # ── 3. SAMPLING & GENERATION SLIDERS ──
                "seed": (
                    "INT",
                    {
                        "default": 42,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "control_after_generate": True,
                        "tooltip": "Seed for deterministic prompt sampling and LoRA tag shuffling. Reproducibility is best-effort on GPU with do_sample=True.",
                    },
                ),
                "temperature": (
                    "FLOAT",
                    {
                        "default": 0.6,
                        "min": 0.0,
                        "max": 1.5,
                        "step": 0.05,
                        "tooltip": "0.0 = deterministic greedy decoding. >0 = creative sampling (higher = more random).",
                    },
                ),
                "top_p": (
                    "FLOAT",
                    {
                        "default": 0.9,
                        "min": 0.1,
                        "max": 1.0,
                        "step": 0.05,
                        "tooltip": "Nucleus sampling: bounds the cumulative probability tail. Set to 1.0 to disable. Lower (0.8-0.9) produces more coherent, focused prompts.",
                    },
                ),
                "repetition_penalty": (
                    "FLOAT",
                    {
                        "default": 1.1,
                        "min": 1.0,
                        "max": 2.0,
                        "step": 0.05,
                        "tooltip": "Penalizes repeated phrases and tags. 1.0 = no penalty. Values between 1.1 and 1.25 prevent tag loops and redundant adjectives.",
                    },
                ),
                "max_new_tokens": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 128,
                        "max": 4096,
                        "tooltip": "Max token budget for generated output. Set to 1024+ for Structured Categories and dense Layer 2 narrative outputs.",
                    },
                ),
            },
            "optional": {
                # Legacy model mode parameter for saved workflows
                "model_mode": (
                    MODEL_MODES,
                    {"default": MODEL_MODES[0]},
                ),
                # ── A. MULTIMODAL & TEXT CONNECTION PINS ──
                "image": (
                    "IMAGE",
                    {"tooltip": "Primary image input. Leave disconnected to run the model in Text-Only mode using input_text."},
                ),
                "reference_image": (
                    "IMAGE",
                    {"tooltip": "Second reference image (e.g. style, background, or comparison target). Connecting this automatically activates multi-image contextual fusion (<Image 1>, <Image 2>)."},
                ),
                "reference_image_2": (
                    "IMAGE",
                    {"tooltip": "Third reference image (e.g. additional angle, palette, or character view). Evaluated alongside Image 1 and Image 2."},
                ),
                "input_text": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "Source prompt / concept to expand or refine (connect or enter here when no images are used)...",
                        "tooltip": "Source text input. Connect a STRING node or write here. When no image is connected to 'image', this provides the source content to elaborate/expand.",
                    },
                ),

                # ── B. SPECIAL SWITCHES (DUAL & ARTIFACT AUDIT) ──
                "enable_dual_prompt": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Split output into two tailored prompts: tags (<75 tokens for short text/tag encoders) and caption (extended descriptive prose for long text encoders).",
                    },
                ),
                "audit_artifacts": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Inspect image for anatomical, rendering, and lighting defects and synthesize a surgical negative prompt.",
                    },
                ),
                "negative_prompt_prefix": (
                    "STRING",
                    {
                        "default": "",
                        "placeholder": "e.g. worst quality, low quality, ",
                    },
                ),
            },
            "hidden": {
                "prompt": "PROMPT",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("caption", "tags", "negative")
    OUTPUT_IS_LIST = (True, True, True)
    FUNCTION = "generate_caption"
    OUTPUT_NODE = True
    CATEGORY = "STOIQO/Prompt Engine"

    # Backward-compatibility method delegates
    def _resolve_model_repo(self, model_mode=None):
        return self.model_mgr.resolve_model_repo(model_mode=model_mode)

    def _resolve_quant_config(self, quantization):
        return self.model_mgr.resolve_quant_config(quantization)

    def _resolve_attn_implementation(self, attention_mode):
        return self.model_mgr.resolve_attn_implementation(attention_mode)

    def _load_model(self, model_repo, attention_mode=ATTENTION_OPTIONS[0]):
        return self.model_mgr.load_model(model_repo, attention_mode)

    def _unload_model(self):
        return self.model_mgr.unload_model()

    def _generate_single(self, *args, **kwargs):
        return self.model_mgr.generate_single(*args, **kwargs)

    @staticmethod
    def _clean_llm_output(text):
        return clean_llm_output(text)

    @staticmethod
    def _build_task_prompt(
        prompt_type=PROMPT_TYPES[0],
        artistic_style=ARTISTIC_STYLES[0],
        directives="",
        input_text="",
        is_dual_prompt=False,
        is_artifact_audit=False,
        **kwargs,
    ):
        return build_task_prompt(
            prompt_type=prompt_type,
            artistic_style=artistic_style,
            directives=directives,
            input_text=input_text,
            is_dual_prompt=is_dual_prompt,
            is_artifact_audit=is_artifact_audit,
        )

    @staticmethod
    def _parse_dual_prompt(raw_text):
        return parse_dual_prompt(raw_text)

    @staticmethod
    def _parse_artifact_audit(raw_text, custom_negative_prefix=""):
        return parse_artifact_audit(raw_text, custom_negative_prefix)

    @staticmethod
    def _parse_three_way_prompt(raw_text, custom_negative_prefix=""):
        return parse_three_way_prompt(raw_text, custom_negative_prefix)

    @staticmethod
    def _process_lora_caption(*args, **kwargs):
        return process_lora_caption(*args, **kwargs)

    @staticmethod
    def _tensor_to_pil(tensor, target_megapixel=1.0):
        return tensor_to_pil(tensor, target_megapixel)

    @staticmethod
    def _save_artifacts(*args, **kwargs):
        return save_artifacts(*args, **kwargs)

    @staticmethod
    def _get_original_filename(prompt, unique_id, input_key="image"):
        return get_original_filename(prompt, unique_id, input_key)

    def generate_caption(
        self,
        # 1. Model & Hardware Engine
        model_preset=MODEL_SELECTION_CHOICES[1],
        local_model_path="",
        quantization=QUANTIZATION_OPTIONS[0],
        target_megapixel=1.0,
        attention_mode=ATTENTION_OPTIONS[0],
        # 2. Task & Directives
        batch_mode="Independent Images",
        system_prompt=SYSTEM_PROMPT_CHOICES[0],
        custom_system_prompt="",
        prompt_type=PROMPT_TYPES[0],
        artistic_style=ARTISTIC_STYLES[0],
        user_directives="",
        # Legacy fallback parameters
        system_prompt_preset=None,
        system_prompt_mode=None,
        model_mode=None,
        # 3. Generation Sliders
        seed=42,
        temperature=0.6,
        top_p=0.9,
        repetition_penalty=1.1,
        max_new_tokens=1024,
        # A. Multimodal Connection Pins
        image=None,
        reference_image=None,
        reference_image_2=None,
        input_text="",
        # B. Special Switches
        enable_dual_prompt=False,
        audit_artifacts=False,
        negative_prompt_prefix="",
        # C. Dataset & LoRA Toolkit
        stoiqo_model=None,
        # Hidden
        prompt=None,
        unique_id=None,
        # Backward compatibility fallback
        caption_style=None,
        **kwargs,
    ):
        if caption_style is not None and prompt_type == PROMPT_TYPES[0]:
            prompt_type = caption_style

        random.seed(seed)
        np.random.seed(seed % (2**32 - 1))
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

        return self._run_generate(
            target_megapixel=target_megapixel,
            batch_mode=batch_mode,
            system_prompt=system_prompt,
            custom_system_prompt=custom_system_prompt,
            prompt_type=prompt_type,
            artistic_style=artistic_style,
            user_directives=user_directives,
            system_prompt_preset=system_prompt_preset,
            system_prompt_mode=system_prompt_mode,
            seed=seed,
            temperature=temperature,
            max_new_tokens=max_new_tokens,
            image=image,
            reference_image=reference_image,
            reference_image_2=reference_image_2,
            input_text=input_text,
            enable_dual_prompt=enable_dual_prompt,
            audit_artifacts=audit_artifacts,
            negative_prompt_prefix=negative_prompt_prefix,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            stoiqo_model=stoiqo_model,
            prompt=prompt,
            unique_id=unique_id,
            model_mode=model_mode,
        )

    def _run_generate(
        self,
        target_megapixel,
        batch_mode,
        system_prompt,
        custom_system_prompt,
        prompt_type,
        artistic_style,
        user_directives,
        system_prompt_preset,
        system_prompt_mode,
        seed,
        temperature,
        max_new_tokens,
        image,
        reference_image,
        reference_image_2,
        input_text,
        enable_dual_prompt,
        audit_artifacts,
        negative_prompt_prefix,
        top_p,
        repetition_penalty,
        prompt,
        unique_id,
        stoiqo_model=None,
        model_mode=None,
    ):
        active_mgr = stoiqo_model if stoiqo_model is not None else self.model_mgr
        if active_mgr.model is None:
            if getattr(active_mgr, "last_load_params", None) is not None:
                active_mgr.load_model(**active_mgr.last_load_params)
            else:
                target_repo = active_mgr.resolve_model_repo(model_preset=None, local_model_path="", model_mode=model_mode)
                active_mgr.load_model(target_repo, "4bit - NF4 (Recommended - Low VRAM)")

        # Collect images from primary and optional reference sockets
        collected_tensors = []
        if image is not None:
            for b in range(image.shape[0]):
                collected_tensors.append(image[b:b+1])
        if reference_image is not None:
            for b in range(reference_image.shape[0]):
                collected_tensors.append(reference_image[b:b+1])
        if reference_image_2 is not None:
            for b in range(reference_image_2.shape[0]):
                collected_tensors.append(reference_image_2[b:b+1])

        total_images = len(collected_tensors)
        has_image = total_images > 0
        is_multi_image = (
            total_images > 1 and (
                batch_mode == "Multi-Image Comparison / Fusion"
                or reference_image is not None
                or reference_image_2 is not None
            )
        )
        is_dual_active = enable_dual_prompt or ("Dual Prompt" in str(prompt_type))
        is_audit_active = audit_artifacts or ("Artifact" in str(prompt_type)) or ("Negative Prompt" in str(prompt_type)) or ("Flaw" in str(prompt_type))

        

        # SSOT: Resolve active system prompt via core.system_prompts
        active_system_prompt = resolve_system_prompt(
            system_prompt=system_prompt,
            custom_system_prompt=custom_system_prompt,
            system_prompt_preset=system_prompt_preset,
            system_prompt_mode=system_prompt_mode,
            has_image=has_image,
            is_multi_image=is_multi_image,
        )

        active_prompt_type = resolve_prompt_type(prompt_type)
        active_artistic_style = resolve_artistic_style(artistic_style)
        task_prompt = build_task_prompt(
            prompt_type=active_prompt_type,
            artistic_style=active_artistic_style,
            directives=user_directives,
            input_text=input_text,
            is_dual_prompt=is_dual_active,
            is_artifact_audit=is_audit_active,
        )

        results_caption = []
        results_tags = []
        results_negative = []

        original_name = None
        if has_image and prompt is not None and unique_id is not None:
            try:
                name1 = get_original_filename(prompt, unique_id, "image")
                name2 = get_original_filename(prompt, unique_id, "reference_image") if reference_image is not None else None
                if name1 and name2:
                    original_name = f"{name1}_{name2}_multi"
                elif name1:
                    original_name = name1
                if original_name:
                    print(f"[STOIQO] Detected source filename(s): '{original_name}'")
            except Exception:
                pass

        # ── Case 1: Text-Only Generation ──────────────────────────────────────
        if not has_image:
            clean_source_text = (input_text or "").strip()
            if not clean_source_text:
                raise ValueError(
                    "[STOIQO] Modalita' Solo Testo: Nessuna immagine collegata e nessun testo sorgente fornito! "
                    "In assenza di immagini, devi collegare un nodo testo (STRING) o inserire il prompt di partenza nel socket 'input_text'."
                )
            print(f"[STOIQO] Processing text-only expansion for: '{clean_source_text[:60]}'...")
            raw_caption = active_mgr.generate_single(
                None, task_prompt, active_system_prompt, max_new_tokens, temperature,
                top_p=top_p, repetition_penalty=repetition_penalty,
                is_multi_image=False,
            )
            out_caption, out_tags, negative, _ = post_process_caption(
                raw_caption,
                is_dual_active=is_dual_active,
                is_audit_active=is_audit_active,
                negative_prompt_prefix=negative_prompt_prefix,
                seed=seed,
                prompt_type=prompt_type,
            )
            results_caption.append(out_caption)
            results_tags.append(out_tags)
            results_negative.append(negative)
            print(f"[STOIQO] [Text Output] Caption: {out_caption[:80]}...")

        # ── Case 2: Multi-Image Comparison / Fusion ────────────────────────────
        elif is_multi_image:
            num_multi = len(collected_tensors)
            per_image_mpx = max(0.35, min(target_megapixel, 1.5 / num_multi))
            print(f"[STOIQO] Processing {num_multi} image(s) in Multi-Image Comparison / Fusion mode (budget: {per_image_mpx:.2f} Mpx/img)...")

            pil_multi = []
            orig_sizes = []
            for img_t in collected_tensors:
                pil_img, orig_size = tensor_to_pil(img_t[0], target_megapixel=per_image_mpx)
                pil_multi.append(pil_img)
                orig_sizes.append(orig_size)

            raw_caption = active_mgr.generate_single(
                pil_multi, task_prompt, active_system_prompt, max_new_tokens, temperature,
                top_p=top_p, repetition_penalty=repetition_penalty,
                is_multi_image=True,
            )
            out_caption, out_tags, negative, tags_list = post_process_caption(
                raw_caption,
                is_dual_active=is_dual_active,
                is_audit_active=is_audit_active,
                negative_prompt_prefix=negative_prompt_prefix,
                seed=seed,
                prompt_type=prompt_type,
            )
            results_caption.append(out_caption)
            results_tags.append(out_tags)
            results_negative.append(negative)
            print(f"[STOIQO] [Multi-Image Output] Caption: {out_caption[:80]}...")
        # ── Case 3: Independent Images Batch ───────────────────────────────────
        else:
            print(f"[STOIQO] Processing batch of {total_images} independent image(s)...")
            for i in range(total_images):
                batch_seed = seed + i
                random.seed(batch_seed)
                np.random.seed(batch_seed % (2**32 - 1))
                torch.manual_seed(batch_seed)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed_all(batch_seed)

                pil_img, orig_size = tensor_to_pil(collected_tensors[i][0], target_megapixel=target_megapixel)
                raw_caption = active_mgr.generate_single(
                    pil_img, task_prompt, active_system_prompt, max_new_tokens, temperature,
                    top_p=top_p, repetition_penalty=repetition_penalty,
                    is_multi_image=False,
                )
                out_caption, out_tags, negative, tags_list = post_process_caption(
                    raw_caption,
                    is_dual_active=is_dual_active,
                    is_audit_active=is_audit_active,
                    negative_prompt_prefix=negative_prompt_prefix,
                    seed=seed + i,
                    prompt_type=prompt_type,
                )
                results_caption.append(out_caption)
                results_tags.append(out_tags)
                results_negative.append(negative)
                print(f"[STOIQO] [Image {i+1}/{total_images}] Caption: {out_caption[:80]}...")

        return (results_caption, results_tags, results_negative)
