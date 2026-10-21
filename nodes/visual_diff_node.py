"""
[STOIQO] Visual Diff & Forensic Inspector Node
Analyzes two images (<Image 1> Baseline vs <Image 2> Comparison) using a Vision-Language Model
to extract structured visual differences, character consistency shifts, optical alterations,
and concise change tags.
"""

import re
import random
import numpy as np
import torch

try:
    from ..core import (
        MODEL_SELECTION_CHOICES,
        QUANTIZATION_OPTIONS,
        ATTENTION_OPTIONS,
        ModelManager,
        tensor_to_pil,
        clean_llm_output,
    )
except (ImportError, ValueError):
    from core import (
        MODEL_SELECTION_CHOICES,
        QUANTIZATION_OPTIONS,
        ATTENTION_OPTIONS,
        ModelManager,
        tensor_to_pil,
        clean_llm_output,
    )


class StoiqoVisualDiffNode:
    """
    Forensic visual comparison engine for ComfyUI.
    Compares two images (<Image 1> Reference vs <Image 2> Comparison) across composition,
    lighting, subject consistency, fine textures, and rendering quality.
    """

    ANALYSIS_FOCUS_CHOICES = [
        "Comprehensive (All Elements)",
        "Subject & Character Consistency",
        "Style, Art & Palette Differences",
        "Lighting, Shadows & Atmosphere",
        "Fine Details, Textures & Sharpness",
        "Defects, Artifacts & Quality Degeneracy",
    ]

    ANALYSIS_DEPTH_CHOICES = [
        "Forensic Audit (Detailed Structured Sections)",
        "Executive Summary & Highlights",
        "Bullet Points Checklist",
    ]

    def __init__(self):
        self.model_mgr = ModelManager()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_a": (
                    "IMAGE",
                    {"tooltip": "Baseline / Reference Image (<Image 1>). Connect original image, generation A, or raw render."},
                ),
                "image_b": (
                    "IMAGE",
                    {"tooltip": "Comparison / Altered Image (<Image 2>). Connect modified image, upscale, alternative seed, or LoRA test."},
                ),
                "analysis_focus": (
                    cls.ANALYSIS_FOCUS_CHOICES,
                    {
                        "default": cls.ANALYSIS_FOCUS_CHOICES[0],
                        "tooltip": "Analytical focus of the visual comparison.",
                    },
                ),
                "analysis_depth": (
                    cls.ANALYSIS_DEPTH_CHOICES,
                    {
                        "default": cls.ANALYSIS_DEPTH_CHOICES[0],
                        "tooltip": "Format and density of the output report.",
                    },
                ),
                "custom_directives": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "Optional specific elements to scrutinize (e.g. check eye anatomy, inspect background blur, verify cloth texture)...",
                        "tooltip": "User directives guiding the comparison focus.",
                    },
                ),
                "target_megapixel": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.1,
                        "max": 4.0,
                        "step": 0.1,
                        "round": 0.01,
                        "tooltip": "Resolution budget per image in Megapixels (~1.0 MP = ~1024x1024). Resized to multiples of 28 for ViT tokens.",
                    },
                ),
                "seed": (
                    "INT",
                    {
                        "default": 42,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "control_after_generate": True,
                        "tooltip": "Seed for deterministic decoding.",
                    },
                ),
                "temperature": (
                    "FLOAT",
                    {
                        "default": 0.35,
                        "min": 0.0,
                        "max": 1.5,
                        "step": 0.05,
                        "tooltip": "Sampling temperature. Lower values (0.2-0.4) ensure rigorous, factual visual analysis.",
                    },
                ),
                "top_p": (
                    "FLOAT",
                    {
                        "default": 0.9,
                        "min": 0.1,
                        "max": 1.0,
                        "step": 0.05,
                        "tooltip": "Nucleus sampling boundary.",
                    },
                ),
                "max_new_tokens": (
                    "INT",
                    {
                        "default": 768,
                        "min": 128,
                        "max": 4096,
                        "tooltip": "Max token budget for the comprehensive difference report.",
                    },
                ),
            },
            "optional": {
                "stoiqo_model": (
                    "STOIQO_MODEL",
                    {"tooltip": "Optional preloaded model from '[STOIQO] VLM Model Loader'. If disconnected, uses internal hardware engine below."},
                ),
                "model_preset": (
                    MODEL_SELECTION_CHOICES,
                    {
                        "default": MODEL_SELECTION_CHOICES[1],
                        "tooltip": "Model preset (used when stoiqo_model is disconnected).",
                    },
                ),
                "local_model_path": (
                    "STRING",
                    {
                        "default": "",
                        "placeholder": "Active when model_preset = 'Custom Model' — click Browse or paste path",
                    },
                ),
                "quantization": (
                    QUANTIZATION_OPTIONS,
                    {
                        "default": QUANTIZATION_OPTIONS[0],
                        "tooltip": "Quantization mode (used when stoiqo_model is disconnected).",
                    },
                ),
                "attention_mode": (
                    ATTENTION_OPTIONS,
                    {
                        "default": ATTENTION_OPTIONS[0],
                        "tooltip": "Attention kernel (used when stoiqo_model is disconnected).",
                    },
                ),
                "unload_model_after": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Frees VRAM immediately after execution (only applies when using internal engine, not external pipe).",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("diff_report", "summary", "change_tags")
    OUTPUT_IS_LIST = (True, True, True)
    FUNCTION = "compare_images"
    OUTPUT_NODE = True
    CATEGORY = "STOIQO"

    def compare_images(
        self,
        image_a,
        image_b,
        analysis_focus,
        analysis_depth,
        custom_directives="",
        target_megapixel=1.0,
        seed=42,
        temperature=0.35,
        top_p=0.9,
        max_new_tokens=768,
        stoiqo_model=None,
        model_preset=MODEL_SELECTION_CHOICES[1],
        local_model_path="",
        quantization=QUANTIZATION_OPTIONS[0],
        attention_mode=ATTENTION_OPTIONS[0],
        unload_model_after=True,
    ):
        random.seed(seed)
        np.random.seed(seed % (2**32 - 1))
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

        # Resolve active ModelManager (external pipe or internal instance)
        active_mgr = stoiqo_model if stoiqo_model is not None else self.model_mgr
        if active_mgr.model is None:
            if getattr(active_mgr, "last_load_params", None) is not None:
                print("[STOIQO] Visual Diff: Model was offloaded in Low VRAM mode. Reloading for comparison pass...")
                active_mgr.load_model(**active_mgr.last_load_params)
            else:
                target_repo = active_mgr.resolve_model_repo(model_preset, local_model_path)
                active_mgr.load_model(target_repo, quantization, attention_mode=attention_mode)

        system_instruction = (
            "You are an elite forensic visual analyst and computer graphics quality auditor. "
            "Your task is to perform a rigorous, pixel-level visual comparison between <Image 1> (Baseline/Reference) "
            "and <Image 2> (Comparison/Altered). "
            "Identify all verifiable physical differences, lighting changes, compositional shifts, "
            "character consistency modifications, fine texture alterations, and rendering artifacts. "
            "Output your findings strictly using the specified structure. Do not hallucinate differences not visible in the images."
        )

        prompt_parts = [
            "Comparison Task: Evaluate visual differences between <Image 1> (Reference) and <Image 2> (Altered).",
            f"Primary Focus: {analysis_focus}.",
            f"Report Format: {analysis_depth}.",
        ]

        if custom_directives and custom_directives.strip():
            prompt_parts.append(f"User Specific Directives: {custom_directives.strip()}")

        prompt_parts.append(
            "Structure the output EXACTLY as follows:\n"
            "<SUMMARY>\n[1-2 sentence clear executive summary of the main visual changes]\n</SUMMARY>\n"
            "<REPORT>\n[Comprehensive breakdown of all detected differences organized by category]\n</REPORT>\n"
            "<CHANGE_TAGS>\n[Concise, comma-separated list of changed visual attributes and keywords]\n</CHANGE_TAGS>"
        )

        user_prompt = "\n\n".join(prompt_parts)

        # Handle batch matching (pair up images from batches A and B)
        num_a = image_a.shape[0]
        num_b = image_b.shape[0]
        max_pairs = max(num_a, num_b)

        results_report = []
        results_summary = []
        results_tags = []

        try:
            for i in range(max_pairs):
                idx_a = min(i, num_a - 1)
                idx_b = min(i, num_b - 1)

                pil_a, _ = tensor_to_pil(image_a[idx_a], target_megapixel=target_megapixel)
                pil_b, _ = tensor_to_pil(image_b[idx_b], target_megapixel=target_megapixel)

                raw_output = active_mgr.generate_single(
                    pil_images=[pil_a, pil_b],
                    task_prompt=user_prompt,
                    system_prompt=system_instruction,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    repetition_penalty=1.15,
                    is_multi_image=True,
                )

                cleaned = clean_llm_output(raw_output)

                # Parse tagged blocks
                summary_match = re.search(r"<SUMMARY>(.*?)</SUMMARY>", cleaned, re.DOTALL | re.IGNORECASE)
                report_match = re.search(r"<REPORT>(.*?)</REPORT>", cleaned, re.DOTALL | re.IGNORECASE)
                tags_match = re.search(r"<CHANGE_TAGS>(.*?)</CHANGE_TAGS>", cleaned, re.DOTALL | re.IGNORECASE)

                summary = summary_match.group(1).strip() if summary_match else ""
                report = report_match.group(1).strip() if report_match else ""
                change_tags = tags_match.group(1).strip() if tags_match else ""

                # Fallback if XML-like tags were omitted
                if not report:
                    # Strip any summary or tags tags that might exist
                    report = re.sub(r"</?(?:SUMMARY|CHANGE_TAGS)>.*?</(?:SUMMARY|CHANGE_TAGS)>", "", cleaned, flags=re.DOTALL | re.IGNORECASE).strip()
                    if not report:
                        report = cleaned.strip()

                if not summary:
                    # First 2 sentences of the report as summary
                    sentences = [s.strip() for s in report.split(".") if s.strip()]
                    summary = ". ".join(sentences[:2]) + "." if sentences else "Visual differences evaluated."

                if not change_tags:
                    # Extract general keywords
                    words = [w.strip() for w in summary.replace("\n", " ").split(" ") if len(w.strip()) > 3]
                    change_tags = ", ".join(list(dict.fromkeys(words))[:10])

                results_report.append(report)
                results_summary.append(summary)
                results_tags.append(change_tags)

        finally:
            if unload_model_after and stoiqo_model is None:
                self.model_mgr.unload_model()

        return (results_report, results_summary, results_tags)
