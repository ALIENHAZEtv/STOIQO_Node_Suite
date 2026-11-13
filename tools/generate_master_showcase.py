"""
[STOIQO] Master Showcase Workflow Generator (V2 - Ultra-Clean Grid Layout)
Mathematically guarantees ZERO overlaps and generous breathing room for all 35 custom nodes.
"""

import json
import os

def build_workflow():
    workflow_id = "stoiqo-master-showcase-v2"
    
    nodes = []
    links = []
    groups = []
    
    current_link_id = 1
    
    def add_link(origin_node, origin_slot, target_node, target_slot, link_type):
        nonlocal current_link_id
        lid = current_link_id
        current_link_id += 1
        links.append([lid, origin_node, origin_slot, target_node, target_slot, link_type])
        return lid

    # =========================================================================
    # ZONE 1: VISION-LANGUAGE INTELLIGENCE (VLM & DIRECTIVES) [CYAN]
    # Bounding: [60, 60, 2220, 1220]
    # =========================================================================
    groups.append({
        "title": "ZONE 1: VISION-LANGUAGE INTELLIGENCE & DIRECTIVES (Qwen2.5-VL)",
        "bounding": [60, 60, 2220, 1220],
        "color": "#06b6d4",
        "font_size": 28
    })

    # Node 1: VLM Model Loader (Col 1, Top)
    nodes.append({
        "id": 1,
        "type": "StoiqoVLMModelLoaderNode",
        "pos": [120, 160],
        "size": [400, 260],
        "flags": {},
        "order": 1,
        "mode": 0,
        "inputs": [],
        "outputs": [
            {"name": "stoiqo_model", "type": "STOIQO_MODEL", "links": [1, 2], "slot_index": 0}
        ],
        "properties": {"Node name for S&R": "StoiqoVLMModelLoaderNode"},
        "widgets_values": [
            "Qwen2.5-VL-7B-Instruct (4-bit NF4 Recommended)",
            "",
            "4bit - NF4 (Recommended - Low VRAM)",
            "sdpa",
            True
        ]
    })

    # Node 2: Style Directives (Col 1, Mid)
    nodes.append({
        "id": 2,
        "type": "StoiqoStyleDirectivesNode",
        "pos": [120, 500],
        "size": [400, 360],
        "flags": {},
        "order": 2,
        "mode": 0,
        "inputs": [],
        "outputs": [
            {"name": "style_directives", "type": "STOIQO_STYLE", "links": [3], "slot_index": 0}
        ],
        "properties": {"Node name for S&R": "StoiqoStyleDirectivesNode"},
        "widgets_values": [
            "Visual Prompt Synthesizer",
            "",
            "Detailed Narrative (Long)",
            "Photographic (Cinematic 35mm)",
            True,
            True,
            "ugly, distorted, blurry, artifacts"
        ]
    })

    # Node 3: Sampling Options (Col 1, Bottom)
    nodes.append({
        "id": 3,
        "type": "StoiqoSamplingOptionsNode",
        "pos": [120, 940],
        "size": [400, 260],
        "flags": {},
        "order": 3,
        "mode": 0,
        "inputs": [],
        "outputs": [
            {"name": "sampling_options", "type": "STOIQO_SAMPLING", "links": [4, 5], "slot_index": 0}
        ],
        "properties": {"Node name for S&R": "StoiqoSamplingOptionsNode"},
        "widgets_values": [
            0.6,
            0.9,
            40,
            1.1,
            1024,
            1.0,
            42
        ]
    })

    # Node 4: Character Memory Bank (Col 2, Top - Tall with 15 widgets)
    nodes.append({
        "id": 4,
        "type": "StoiqoCharacterMemoryNode",
        "pos": [580, 160],
        "size": [460, 760],
        "flags": {},
        "order": 4,
        "mode": 0,
        "inputs": [
            {"name": "reference_image", "type": "IMAGE", "link": None}
        ],
        "outputs": [
            {"name": "full_prompt", "type": "STRING", "links": None, "slot_index": 0},
            {"name": "character_context", "type": "STOIQO_CHARACTER", "links": [6], "slot_index": 1},
            {"name": "character_dna", "type": "STRING", "links": None, "slot_index": 2},
            {"name": "trigger_tag", "type": "STRING", "links": None, "slot_index": 3},
            {"name": "negative_prompt", "type": "STRING", "links": None, "slot_index": 4},
            {"name": "reference_image", "type": "IMAGE", "links": None, "slot_index": 5}
        ],
        "properties": {"Node name for S&R": "StoiqoCharacterMemoryNode"},
        "widgets_values": [
            "Elena Frost",
            "elena_frost",
            "Custom (User Defined)",
            "woman in early 30s",
            "pale skin, high cheekbones, thin scar across bridge of nose",
            "piercing sapphire eyes",
            "long platinum braided hair",
            "tall athletic build",
            "wolf tattoo on left shoulder",
            "white winter fur cloak, dark leather armor",
            "silver runic dagger on hip",
            "stoic, observant, cold exterior with hidden warmth",
            "wrong eye color, modern clothes, blonde hair",
            "Smart Detect (Inject only when Name or Trigger is in Prompt)",
            "Elena Frost standing in a snow-covered pine forest at twilight"
        ]
    })

    # Node 5: Multi-Image Context Hub (Col 2, Bottom)
    nodes.append({
        "id": 5,
        "type": "StoiqoMultiImageContextNode",
        "pos": [580, 980],
        "size": [460, 220],
        "flags": {},
        "order": 5,
        "mode": 0,
        "inputs": [
            {"name": "image_1", "type": "IMAGE", "link": None},
            {"name": "image_2", "type": "IMAGE", "link": None},
            {"name": "image_3", "type": "IMAGE", "link": None},
            {"name": "image_4", "type": "IMAGE", "link": None}
        ],
        "outputs": [
            {"name": "multi_image_context", "type": "STOIQO_CONTEXT", "links": [7], "slot_index": 0}
        ],
        "properties": {"Node name for S&R": "StoiqoMultiImageContextNode"},
        "widgets_values": [
            "Contextual Fusion (Blend Style & Subject)"
        ]
    })

    # Node 6: Prompt Generator Engine (Col 3)
    nodes.append({
        "id": 6,
        "type": "StoiqoPromptGeneratorNode",
        "pos": [1100, 160],
        "size": [480, 520],
        "flags": {},
        "order": 6,
        "mode": 0,
        "inputs": [
            {"name": "stoiqo_model", "type": "STOIQO_MODEL", "link": 1},
            {"name": "image", "type": "IMAGE", "link": None},
            {"name": "style_directives", "type": "STOIQO_STYLE", "link": 3},
            {"name": "sampling_options", "type": "STOIQO_SAMPLING", "link": 4},
            {"name": "multi_image_context", "type": "STOIQO_CONTEXT", "link": 7},
            {"name": "character_context", "type": "STOIQO_CHARACTER", "link": 6}
        ],
        "outputs": [
            {"name": "prompt", "type": "STRING", "links": [8, 9], "slot_index": 0},
            {"name": "tags", "type": "STRING", "links": None, "slot_index": 1},
            {"name": "negative", "type": "STRING", "links": [10], "slot_index": 2},
            {"name": "raw_response", "type": "STRING", "links": None, "slot_index": 3}
        ],
        "properties": {"Node name for S&R": "StoiqoPromptGeneratorNode"},
        "widgets_values": [
            "cinematic portrait of Elena Frost in the snowy forest, dramatic volumetric moonlight",
            "Disabled"
        ]
    })

    # Node 7: Show Prompt (Col 4)
    nodes.append({
        "id": 7,
        "type": "StoiqoShowPromptNode",
        "pos": [1640, 160],
        "size": [400, 480],
        "flags": {},
        "order": 7,
        "mode": 0,
        "inputs": [
            {"name": "text", "type": "STRING", "link": 8}
        ],
        "outputs": [
            {"name": "text", "type": "STRING", "links": None, "slot_index": 0}
        ],
        "properties": {"Node name for S&R": "StoiqoShowPromptNode"},
        "widgets_values": [""]
    })

    # Zone 1 Links
    links.append([1, 1, 0, 6, 0, "STOIQO_MODEL"])
    links.append([3, 2, 0, 6, 2, "STOIQO_STYLE"])
    links.append([4, 3, 0, 6, 3, "STOIQO_SAMPLING"])
    links.append([6, 4, 1, 6, 5, "STOIQO_CHARACTER"])
    links.append([7, 5, 0, 6, 4, "STOIQO_CONTEXT"])
    links.append([8, 6, 0, 7, 0, "STRING"])

    # =========================================================================
    # ZONE 2: TURBO GENERATION & UNIVERSAL BUS [PURPLE]
    # Bounding: [2360, 60, 2300, 1220]
    # =========================================================================
    groups.append({
        "title": "ZONE 2: TURBO GENERATION & UNIVERSAL BUS (Krea 2 Turbo / FLUX / SDXL)",
        "bounding": [2360, 60, 2300, 1220],
        "color": "#8b5cf6",
        "font_size": 28
    })

    # Node 8: Universal Model Loader (DiT / Diffusion)
    nodes.append({
        "id": 8,
        "type": "StoiqoUniversalModelLoaderNode",
        "pos": [2420, 140],
        "size": [380, 140],
        "flags": {},
        "order": 8,
        "mode": 0,
        "inputs": [],
        "outputs": [
            {"name": "model", "type": "*", "links": [11], "slot_index": 0}
        ],
        "properties": {"Node name for S&R": "StoiqoUniversalModelLoaderNode"},
        "widgets_values": [
            "[DiT/UNET] krea2TurboUncensored_v1.safetensors",
            "auto",
            "default",
            "sdpa",
            "Z-Image Turbo (Shift: 3.0)",
            3.0,
            "",
            True
        ]
    })

    # Node 81: Universal Model Loader (CLIP / Text Encoder)
    nodes.append({
        "id": 81,
        "type": "StoiqoUniversalModelLoaderNode",
        "pos": [2420, 300],
        "size": [380, 140],
        "flags": {},
        "order": 8,
        "mode": 0,
        "inputs": [],
        "outputs": [
            {"name": "model", "type": "*", "links": [12], "slot_index": 0}
        ],
        "properties": {"Node name for S&R": "StoiqoUniversalModelLoaderNode"},
        "widgets_values": [
            "[CLIP] Qwen3-VL-4B-Instruct-Uncensored-FP8.safetensors",
            "krea2",
            "default",
            "sdpa",
            "None (Standard / SD1.5 / SDXL / Krea 2)",
            3.0,
            "",
            True
        ]
    })

    # Node 82: Universal Model Loader (VAE)
    nodes.append({
        "id": 82,
        "type": "StoiqoUniversalModelLoaderNode",
        "pos": [2420, 460],
        "size": [380, 140],
        "flags": {},
        "order": 8,
        "mode": 0,
        "inputs": [],
        "outputs": [
            {"name": "model", "type": "*", "links": [13], "slot_index": 0}
        ],
        "properties": {"Node name for S&R": "StoiqoUniversalModelLoaderNode"},
        "widgets_values": [
            "[VAE] qwen_image_vae.safetensors",
            "auto",
            "default",
            "sdpa",
            "None (Standard / SD1.5 / SDXL / Krea 2)",
            3.0,
            "",
            True
        ]
    })

    # Node 9: LoRA Stack (Col 1, Bottom)
    nodes.append({
        "id": 9,
        "type": "StoiqoLoraStackNode",
        "pos": [2420, 620],
        "size": [400, 560],
        "flags": {},
        "order": 9,
        "mode": 0,
        "inputs": [
            {"name": "lora_stack", "type": "LORA_STACK", "link": None},
            {"name": "model", "type": "MODEL", "link": 11},
            {"name": "clip", "type": "CLIP", "link": 12}
        ],
        "outputs": [
            {"name": "model", "type": "MODEL", "links": [15], "slot_index": 0},
            {"name": "clip", "type": "CLIP", "links": [16], "slot_index": 1},
            {"name": "lora_stack", "type": "LORA_STACK", "links": None, "slot_index": 2}
        ],
        "properties": {"Node name for S&R": "StoiqoLoraStackNode"},
        "widgets_values": [
            "None", 1.0, 1.0,
            "None", 1.0, 1.0,
            "None", 1.0, 1.0,
            "None", 1.0, 1.0
        ]
    })

    # Node 10: Seed Controller (Col 2, Top)
    nodes.append({
        "id": 10,
        "type": "StoiqoSeedControllerNode",
        "pos": [2880, 160],
        "size": [360, 260],
        "flags": {},
        "order": 10,
        "mode": 0,
        "inputs": [],
        "outputs": [
            {"name": "seed", "type": "INT", "links": [17], "slot_index": 0},
            {"name": "seed_float", "type": "FLOAT", "links": None, "slot_index": 1},
            {"name": "variance_info", "type": "STRING", "links": None, "slot_index": 2}
        ],
        "properties": {"Node name for S&R": "StoiqoSeedControllerNode"},
        "widgets_values": [
            133742,
            "randomize",
            "Fixed Constant",
            0.05,
            "Independent Variance"
        ]
    })

    # Node 11: Resolution Selector (Col 2, Bottom)
    nodes.append({
        "id": 11,
        "type": "StoiqoResolutionNode",
        "pos": [2880, 520],
        "size": [360, 280],
        "flags": {},
        "order": 11,
        "mode": 0,
        "inputs": [],
        "outputs": [
            {"name": "width", "type": "INT", "links": [18], "slot_index": 0},
            {"name": "height", "type": "INT", "links": [19], "slot_index": 1},
            {"name": "aspect_ratio_str", "type": "STRING", "links": None, "slot_index": 2},
            {"name": "resolution_tuple", "type": "RESOLUTION_TUPLE", "links": None, "slot_index": 3}
        ],
        "properties": {"Node name for S&R": "StoiqoResolutionNode"},
        "widgets_values": [
            "1:1 Square (1024x1024)",
            "1024x1024 (1.0 MP standard)",
            False,
            1024,
            1024,
            1.0
        ]
    })

    # Node 12: Universal Pipe In (Col 3, Top)
    nodes.append({
        "id": 12,
        "type": "StoiqoUniversalPipeInNode",
        "pos": [3300, 160],
        "size": [380, 420],
        "flags": {},
        "order": 12,
        "mode": 0,
        "inputs": [
            {"name": "pipe", "type": "*", "link": None},
            {"name": "model", "type": "MODEL", "link": 15},
            {"name": "clip", "type": "CLIP", "link": 16},
            {"name": "vae", "type": "VAE", "link": 13},
            {"name": "positive", "type": "CONDITIONING", "link": None},
            {"name": "negative", "type": "CONDITIONING", "link": None},
            {"name": "latent", "type": "LATENT", "link": None},
            {"name": "images", "type": "IMAGE", "link": None},
            {"name": "seed", "type": "INT", "link": 17}
        ],
        "outputs": [
            {"name": "pipe", "type": "*", "links": [20, 21], "slot_index": 0},
            {"name": "stoiqo_pipe", "type": "STOIQO_PIPE", "links": None, "slot_index": 1}
        ],
        "properties": {"Node name for S&R": "StoiqoUniversalPipeInNode"},
        "widgets_values": [0]
    })

    # Node 13: Universal Pipe Out (Col 3, Bottom)
    nodes.append({
        "id": 13,
        "type": "StoiqoUniversalPipeOutNode",
        "pos": [3300, 660],
        "size": [380, 440],
        "flags": {},
        "order": 13,
        "mode": 0,
        "inputs": [
            {"name": "pipe", "type": "*", "link": 20}
        ],
        "outputs": [
            {"name": "pipe", "type": "*", "links": None, "slot_index": 0},
            {"name": "model", "type": "MODEL", "links": None, "slot_index": 1},
            {"name": "clip", "type": "CLIP", "links": None, "slot_index": 2},
            {"name": "vae", "type": "VAE", "links": None, "slot_index": 3},
            {"name": "positive", "type": "CONDITIONING", "links": None, "slot_index": 4},
            {"name": "negative", "type": "CONDITIONING", "links": None, "slot_index": 5},
            {"name": "latent", "type": "LATENT", "links": None, "slot_index": 6},
            {"name": "images", "type": "IMAGE", "links": None, "slot_index": 7},
            {"name": "seed", "type": "INT", "links": None, "slot_index": 8}
        ],
        "properties": {"Node name for S&R": "StoiqoUniversalPipeOutNode"},
        "widgets_values": []
    })

    # Node 14: Turbo Sampler (Col 4)
    nodes.append({
        "id": 14,
        "type": "StoiqoTurboSamplerNode",
        "pos": [3740, 160],
        "size": [460, 780],
        "flags": {},
        "order": 14,
        "mode": 0,
        "inputs": [
            {"name": "model", "type": "MODEL", "link": None},
            {"name": "clip", "type": "CLIP", "link": None},
            {"name": "vae", "type": "VAE", "link": None},
            {"name": "pipe", "type": "*", "link": 21},
            {"name": "stoiqo_pipe", "type": "STOIQO_PIPE", "link": None},
            {"name": "latent_image", "type": "LATENT", "link": None}
        ],
        "outputs": [
            {"name": "image", "type": "IMAGE", "links": [22, 23, 24, 25, 26, 27], "slot_index": 0},
            {"name": "latent", "type": "LATENT", "links": None, "slot_index": 1},
            {"name": "stoiqo_pipe", "type": "STOIQO_PIPE", "links": None, "slot_index": 2}
        ],
        "properties": {"Node name for S&R": "StoiqoTurboSamplerNode"},
        "widgets_values": [
            "A high-end cinematic studio portrait of Elena Frost with sapphire eyes, volumetric snow lighting, 8k crisp details",
            133742,
            4,
            1.0,
            "euler",
            "simple",
            1024,
            1024,
            "Zero-Out (Recommended for Krea 2 Turbo)",
            "",
            1.0,
            "Disabled",
            1.3,
            1.4,
            0.6,
            0.4
        ]
    })

    # Zone 2 Links
    links.append([11, 8, 0, 9, 1, "MODEL"])
    links.append([12, 81, 0, 9, 2, "CLIP"])
    links.append([13, 82, 0, 12, 3, "VAE"])
    links.append([15, 9, 0, 12, 1, "MODEL"])
    links.append([16, 9, 1, 12, 2, "CLIP"])
    links.append([17, 10, 0, 12, 8, "INT"])
    links.append([18, 11, 0, 14, 6, "INT"])
    links.append([19, 11, 1, 14, 7, "INT"])
    links.append([20, 12, 0, 13, 0, "*"])
    links.append([21, 12, 0, 14, 3, "*"])

    # =========================================================================
    # ZONE 3: CREATIVE RETOUCHING, SPATIAL GROUNDING & 3D PARALLAX [EMERALD]
    # Bounding: [60, 1340, 2760, 1260]
    # =========================================================================
    groups.append({
        "title": "ZONE 3: CREATIVE RETOUCHING, SPATIAL GROUNDING & 3D PARALLAX",
        "bounding": [60, 1340, 2760, 1260],
        "color": "#10b981",
        "font_size": 28
    })

    # Node 15: Spatial Cropper (Col 1, Top)
    nodes.append({
        "id": 15,
        "type": "StoiqoSpatialCropperNode",
        "pos": [120, 1440],
        "size": [420, 480],
        "flags": {},
        "order": 15,
        "mode": 0,
        "inputs": [
            {"name": "stoiqo_model", "type": "STOIQO_MODEL", "link": 2},
            {"name": "image", "type": "IMAGE", "link": 22}
        ],
        "outputs": [
            {"name": "cropped_image", "type": "IMAGE", "links": [28], "slot_index": 0},
            {"name": "mask", "type": "MASK", "links": [29], "slot_index": 1},
            {"name": "bbox_info", "type": "STRING", "links": [30, 31], "slot_index": 2},
            {"name": "segs", "type": "SEGS", "links": None, "slot_index": 3}
        ],
        "properties": {"Node name for S&R": "StoiqoSpatialCropperNode"},
        "widgets_values": [
            "face",
            10,
            1.0,
            False,
            "Tight Bounding Box",
            8,
            "ymin, xmin, ymax, xmax (Qwen Standard)"
        ]
    })

    # Node 16: Spatial Re-Roll (Col 1, Bottom)
    nodes.append({
        "id": 16,
        "type": "StoiqoSpatialRerollNode",
        "pos": [120, 2000],
        "size": [420, 460],
        "flags": {},
        "order": 16,
        "mode": 0,
        "inputs": [
            {"name": "image", "type": "IMAGE", "link": 23},
            {"name": "mask", "type": "MASK", "link": 29},
            {"name": "replacement_image", "type": "IMAGE", "link": None},
            {"name": "bbox_json", "type": "STRING", "link": 30}
        ],
        "outputs": [
            {"name": "composite_image", "type": "IMAGE", "links": None, "slot_index": 0},
            {"name": "cropped_roi", "type": "IMAGE", "links": None, "slot_index": 1},
            {"name": "roi_mask", "type": "MASK", "links": None, "slot_index": 2},
            {"name": "bbox_info", "type": "STRING", "links": None, "slot_index": 3}
        ],
        "properties": {"Node name for S&R": "StoiqoSpatialRerollNode"},
        "widgets_values": [
            16,
            True,
            0.10,
            ""
        ]
    })

    # Node 17: Inpaint Stitcher (Col 2, Top)
    nodes.append({
        "id": 17,
        "type": "StoiqoInpaintStitcherNode",
        "pos": [600, 1440],
        "size": [420, 360],
        "flags": {},
        "order": 17,
        "mode": 0,
        "inputs": [
            {"name": "original_image", "type": "IMAGE", "link": 24},
            {"name": "edited_image", "type": "IMAGE", "link": 28},
            {"name": "bbox_info", "type": "STRING", "link": 31}
        ],
        "outputs": [
            {"name": "composite_image", "type": "IMAGE", "links": [32], "slot_index": 0},
            {"name": "stitch_mask", "type": "MASK", "links": None, "slot_index": 1}
        ],
        "properties": {"Node name for S&R": "StoiqoInpaintStitcherNode"},
        "widgets_values": [
            "Normal (Alpha Feather)",
            16,
            False
        ]
    })

    # Node 18: Face Restoration Hub (Col 2, Bottom)
    nodes.append({
        "id": 18,
        "type": "StoiqoFaceRestoreHub",
        "pos": [600, 1900],
        "size": [420, 480],
        "flags": {},
        "order": 18,
        "mode": 0,
        "inputs": [
            {"name": "image", "type": "IMAGE", "link": 25}
        ],
        "outputs": [
            {"name": "restored_image", "type": "IMAGE", "links": [33], "slot_index": 0},
            {"name": "face_crops", "type": "IMAGE", "links": None, "slot_index": 1},
            {"name": "face_masks", "type": "MASK", "links": None, "slot_index": 2},
            {"name": "face_count", "type": "INT", "links": None, "slot_index": 3},
            {"name": "face_bboxes_json", "type": "STRING", "links": None, "slot_index": 4}
        ],
        "properties": {"Node name for S&R": "StoiqoFaceRestoreHub"},
        "widgets_values": [
            0.80,
            0.35,
            1.25,
            16,
            0.20
        ]
    })

    # Node 19: Frequency Split (Col 3, Top)
    nodes.append({
        "id": 19,
        "type": "StoiqoFrequencySplitNode",
        "pos": [1080, 1440],
        "size": [380, 320],
        "flags": {},
        "order": 19,
        "mode": 0,
        "inputs": [
            {"name": "image", "type": "IMAGE", "link": 33}
        ],
        "outputs": [
            {"name": "low_freq_image", "type": "IMAGE", "links": [34], "slot_index": 0},
            {"name": "high_freq_image", "type": "IMAGE", "links": [35], "slot_index": 1},
            {"name": "split_meta", "type": "STRING", "links": [36], "slot_index": 2}
        ],
        "properties": {"Node name for S&R": "StoiqoFrequencySplitNode"},
        "widgets_values": [
            16,
            1.0,
            "linear_offset_50"
        ]
    })

    # Node 20: Frequency Merge (Col 3, Bottom)
    nodes.append({
        "id": 20,
        "type": "StoiqoFrequencyMergeNode",
        "pos": [1080, 1860],
        "size": [380, 340],
        "flags": {},
        "order": 20,
        "mode": 0,
        "inputs": [
            {"name": "low_freq_image", "type": "IMAGE", "link": 34},
            {"name": "high_freq_image", "type": "IMAGE", "link": 35},
            {"name": "split_meta", "type": "STRING", "link": 36}
        ],
        "outputs": [
            {"name": "image", "type": "IMAGE", "links": [37], "slot_index": 0}
        ],
        "properties": {"Node name for S&R": "StoiqoFrequencyMergeNode"},
        "widgets_values": [
            1.0,
            "linear_offset_50"
        ]
    })

    # Node 21: Depth Parallax Extractor (Col 4)
    nodes.append({
        "id": 21,
        "type": "StoiqoDepthParallaxExtractor",
        "pos": [1520, 1440],
        "size": [420, 440],
        "flags": {},
        "order": 21,
        "mode": 0,
        "inputs": [
            {"name": "image", "type": "IMAGE", "link": 26}
        ],
        "outputs": [
            {"name": "depth_map", "type": "IMAGE", "links": None, "slot_index": 0},
            {"name": "foreground_mask", "type": "MASK", "links": None, "slot_index": 1},
            {"name": "midground_mask", "type": "MASK", "links": None, "slot_index": 2},
            {"name": "background_mask", "type": "MASK", "links": None, "slot_index": 3},
            {"name": "disparity_json", "type": "STRING", "links": None, "slot_index": 4}
        ],
        "properties": {"Node name for S&R": "StoiqoDepthParallaxExtractor"},
        "widgets_values": [
            0.65,
            0.35,
            8,
            False,
            32
        ]
    })

    # Node 22: Watermark Node (Col 5)
    nodes.append({
        "id": 22,
        "type": "StoiqoWatermarkNode",
        "pos": [2000, 1440],
        "size": [420, 580],
        "flags": {},
        "order": 22,
        "mode": 0,
        "inputs": [
            {"name": "base_image", "type": "IMAGE", "link": 37},
            {"name": "watermark_image", "type": "IMAGE", "link": None},
            {"name": "optional_mask", "type": "MASK", "link": None}
        ],
        "outputs": [
            {"name": "image", "type": "IMAGE", "links": [38], "slot_index": 0},
            {"name": "watermark_mask", "type": "MASK", "links": None, "slot_index": 1},
            {"name": "overlay_info", "type": "STRING", "links": None, "slot_index": 2}
        ],
        "properties": {"Node name for S&R": "StoiqoWatermarkNode"},
        "widgets_values": [
            "Bottom-Right",
            "1/8 (Default)",
            0.125,
            0.02,
            0.90,
            "Auto Chroma (Corner)",
            0.10,
            2
        ]
    })

    # Zone 3 Links
    links.append([2, 1, 0, 15, 0, "STOIQO_MODEL"])
    links.append([22, 14, 0, 15, 1, "IMAGE"])
    links.append([23, 14, 0, 16, 0, "IMAGE"])
    links.append([24, 14, 0, 17, 0, "IMAGE"])
    links.append([25, 14, 0, 18, 0, "IMAGE"])
    links.append([26, 14, 0, 21, 0, "IMAGE"])
    links.append([28, 15, 0, 17, 1, "IMAGE"])
    links.append([29, 15, 1, 16, 1, "MASK"])
    links.append([30, 15, 2, 16, 3, "STRING"])
    links.append([31, 15, 2, 17, 2, "STRING"])
    links.append([33, 18, 0, 19, 0, "IMAGE"])
    links.append([34, 19, 0, 20, 0, "IMAGE"])
    links.append([35, 19, 1, 20, 1, "IMAGE"])
    links.append([36, 19, 2, 20, 2, "STRING"])
    links.append([37, 20, 0, 22, 0, "IMAGE"])

    # =========================================================================
    # ZONE 4: AI AUDIO & MUSIC PRODUCTION (YuE 2) [AMBER]
    # Bounding: [2900, 1340, 980, 850]
    # =========================================================================
    groups.append({
        "title": "ZONE 4: AI AUDIO & MUSIC GENERATION ENGINE (YuE 2)",
        "bounding": [2900, 1340, 980, 850],
        "color": "#f59e0b",
        "font_size": 28
    })

    # Node 23: Music Prompt Engine (Col 1)
    nodes.append({
        "id": 23,
        "type": "StoiqoMusicPromptEngineNode",
        "pos": [2960, 1440],
        "size": [420, 620],
        "flags": {},
        "order": 23,
        "mode": 0,
        "inputs": [
            {"name": "stoiqo_model", "type": "STOIQO_MODEL", "link": None},
            {"name": "image_inspiration", "type": "IMAGE", "link": None},
            {"name": "sampling_options", "type": "STOIQO_SAMPLING", "link": 5}
        ],
        "outputs": [
            {"name": "complete_prompt", "type": "STRING", "links": None, "slot_index": 0},
            {"name": "lyrics", "type": "STRING", "links": [39], "slot_index": 1},
            {"name": "meta_prompt", "type": "STRING", "links": None, "slot_index": 2},
            {"name": "vocal_style_str", "type": "STRING", "links": None, "slot_index": 3},
            {"name": "genre_str", "type": "STRING", "links": [40], "slot_index": 4},
            {"name": "raw_response", "type": "STRING", "links": None, "slot_index": 5}
        ],
        "properties": {"Node name for S&R": "StoiqoMusicPromptEngineNode"},
        "widgets_values": [
            "Cosmic voyage across glowing nebulae and digital dreams",
            "Synthwave (Retro Electro, 80s Cyberpunk, Neon Drive)",
            "Ethereal Breathy Female Vocal",
            "Verse 1, Chorus, Verse 2, Chorus, Bridge, Outro",
            "Standard Mid-Tempo (115-128 BPM)",
            "English",
            "Energetic & Driving",
            "",
            "YuE 2 Music & Lyrics Synthesizer",
            ""
        ]
    })

    # Node 24: Audio Saver (Col 2)
    nodes.append({
        "id": 24,
        "type": "StoiqoAudioSaverNode",
        "pos": [3440, 1440],
        "size": [400, 540],
        "flags": {},
        "order": 24,
        "mode": 0,
        "inputs": [
            {"name": "audio", "type": "AUDIO", "link": None},
            {"name": "lyrics", "type": "STRING", "link": 39},
            {"name": "style", "type": "STRING", "link": 40}
        ],
        "outputs": [
            {"name": "audio", "type": "AUDIO", "links": None, "slot_index": 0},
            {"name": "file_path", "type": "STRING", "links": None, "slot_index": 1},
            {"name": "filename", "type": "STRING", "links": None, "slot_index": 2},
            {"name": "metadata_json", "type": "STRING", "links": None, "slot_index": 3}
        ],
        "properties": {"Node name for S&R": "StoiqoAudioSaverNode"},
        "widgets_values": [
            "%date%_%title%_%bpm%bpm",
            "WAV (Lossless 24-bit)",
            "StoiqoAudio/%date%",
            "Cosmic Voyage",
            120,
            "Both (.txt lyrics + .json)"
        ]
    })

    # Zone 4 Links
    links.append([5, 3, 0, 23, 2, "STOIQO_SAMPLING"])
    links.append([39, 23, 1, 24, 1, "STRING"])
    links.append([40, 23, 4, 24, 2, "STRING"])

    # =========================================================================
    # ZONE 5: VIDEO ENHANCEMENT & TEMPORAL DYNAMICS [MAGENTA]
    # Bounding: [60, 2680, 1500, 920]
    # =========================================================================
    groups.append({
        "title": "ZONE 5: VIDEO ENHANCEMENT, DEFLICKER & FRAME RATE MULTIPLIER",
        "bounding": [60, 2680, 1500, 920],
        "color": "#ec4899",
        "font_size": 28
    })

    # Node 25: Temporal Deflicker (Col 1)
    nodes.append({
        "id": 25,
        "type": "StoiqoTemporalDeflickerNode",
        "pos": [120, 2780],
        "size": [400, 340],
        "flags": {},
        "order": 25,
        "mode": 0,
        "inputs": [
            {"name": "images", "type": "IMAGE", "link": None}
        ],
        "outputs": [
            {"name": "stabilized_frames", "type": "IMAGE", "links": [41], "slot_index": 0},
            {"name": "deflicker_metrics", "type": "STRING", "links": None, "slot_index": 1}
        ],
        "properties": {"Node name for S&R": "StoiqoTemporalDeflickerNode"},
        "widgets_values": [
            5,
            0.08,
            0.85
        ]
    })

    # Node 26: Frame Rate Interpolator (Col 2)
    nodes.append({
        "id": 26,
        "type": "StoiqoFrameInterpolateNode",
        "pos": [580, 2780],
        "size": [400, 340],
        "flags": {},
        "order": 26,
        "mode": 0,
        "inputs": [
            {"name": "images", "type": "IMAGE", "link": 41}
        ],
        "outputs": [
            {"name": "interpolated_frames", "type": "IMAGE", "links": [42], "slot_index": 0},
            {"name": "output_frame_count", "type": "INT", "links": None, "slot_index": 1},
            {"name": "metrics_json", "type": "STRING", "links": None, "slot_index": 2}
        ],
        "properties": {"Node name for S&R": "StoiqoFrameInterpolateNode"},
        "widgets_values": [
            "2x (Double FPS)",
            1.0,
            "cosine_smooth"
        ]
    })

    # Node 27: Video Saver (Col 3)
    nodes.append({
        "id": 27,
        "type": "StoiqoVideoSaverNode",
        "pos": [1040, 2780],
        "size": [440, 620],
        "flags": {},
        "order": 27,
        "mode": 0,
        "inputs": [
            {"name": "images", "type": "IMAGE", "link": 42},
            {"name": "motion_prompt", "type": "STRING", "link": None}
        ],
        "outputs": [
            {"name": "images", "type": "IMAGE", "links": None, "slot_index": 0},
            {"name": "file_path", "type": "STRING", "links": None, "slot_index": 1},
            {"name": "filename", "type": "STRING", "links": None, "slot_index": 2},
            {"name": "folder_path", "type": "STRING", "links": None, "slot_index": 3},
            {"name": "metadata_json", "type": "STRING", "links": None, "slot_index": 4}
        ],
        "properties": {"Node name for S&R": "StoiqoVideoSaverNode"},
        "widgets_values": [
            48.0,
            "%date%_minimax_%fps%",
            "MP4 (H.264)",
            85,
            "StoiqoVideos/%date%",
            "",
            "Both (.json + .txt)"
        ]
    })

    # Zone 5 Links
    links.append([41, 25, 0, 26, 0, "IMAGE"])
    links.append([42, 26, 0, 27, 0, "IMAGE"])

    # =========================================================================
    # ZONE 6: DATASET, COMPARISON & PIPELINE UTILITIES [BLUE]
    # Bounding: [1640, 2680, 2350, 980]
    # =========================================================================
    groups.append({
        "title": "ZONE 6: DATASET TOOLKIT, FORENSIC DIFF & WEBHOOK PIPELINE",
        "bounding": [1640, 2680, 2350, 980],
        "color": "#3b82f6",
        "font_size": 28
    })

    # Node 28: Smart Folder Iterator (Col 1, Top)
    nodes.append({
        "id": 28,
        "type": "StoiqoSmartFolderImageIterator",
        "pos": [1700, 2780],
        "size": [380, 360],
        "flags": {},
        "order": 28,
        "mode": 0,
        "inputs": [],
        "outputs": [
            {"name": "image", "type": "IMAGE", "links": [43, 44], "slot_index": 0},
            {"name": "mask", "type": "MASK", "links": None, "slot_index": 1},
            {"name": "filename", "type": "STRING", "links": None, "slot_index": 2},
            {"name": "width", "type": "INT", "links": None, "slot_index": 3},
            {"name": "height", "type": "INT", "links": None, "slot_index": 4}
        ],
        "properties": {"Node name for S&R": "StoiqoSmartFolderImageIterator"},
        "widgets_values": [
            "./workspace/datasets/portraits",
            0,
            True,
            ".txt",
            False
        ]
    })

    # Node 29: Dataset Writer (Col 1, Bottom)
    nodes.append({
        "id": 29,
        "type": "StoiqoDatasetWriterNode",
        "pos": [1700, 3220],
        "size": [380, 380],
        "flags": {},
        "order": 29,
        "mode": 0,
        "inputs": [
            {"name": "image", "type": "IMAGE", "link": 43},
            {"name": "caption", "type": "STRING", "link": 9},
            {"name": "tags", "type": "STRING", "link": None}
        ],
        "outputs": [
            {"name": "image", "type": "IMAGE", "links": None, "slot_index": 0},
            {"name": "caption", "type": "STRING", "links": None, "slot_index": 1},
            {"name": "file_path", "type": "STRING", "links": None, "slot_index": 2}
        ],
        "properties": {"Node name for S&R": "StoiqoDatasetWriterNode"},
        "widgets_values": [
            "./workspace/lora_dataset_out",
            "img",
            "both (copy image & write caption)",
            ".txt",
            ", "
        ]
    })

    # Node 30: Trio Image Loader (Col 2, Top)
    nodes.append({
        "id": 30,
        "type": "StoiqoTripleImageLoaderNode",
        "pos": [2140, 2780],
        "size": [380, 340],
        "flags": {},
        "order": 30,
        "mode": 0,
        "inputs": [],
        "outputs": [
            {"name": "hero_image", "type": "IMAGE", "links": [45], "slot_index": 0},
            {"name": "thumb_1", "type": "IMAGE", "links": None, "slot_index": 1},
            {"name": "thumb_2", "type": "IMAGE", "links": None, "slot_index": 2},
            {"name": "batch_image", "type": "IMAGE", "links": None, "slot_index": 3}
        ],
        "properties": {"Node name for S&R": "StoiqoTripleImageLoaderNode"},
        "widgets_values": [
            "hero.png",
            "thumb1.png",
            "thumb2.png",
            "Individual Outputs (Hero & Thumbs Separate)"
        ]
    })

    # Node 31: Visual Diff (Col 2, Bottom)
    nodes.append({
        "id": 31,
        "type": "StoiqoVisualDiffNode",
        "pos": [2140, 3200],
        "size": [380, 360],
        "flags": {},
        "order": 31,
        "mode": 0,
        "inputs": [
            {"name": "image_a", "type": "IMAGE", "link": 44},
            {"name": "image_b", "type": "IMAGE", "link": 45}
        ],
        "outputs": [
            {"name": "diff_image", "type": "IMAGE", "links": None, "slot_index": 0},
            {"name": "metric_psnr", "type": "FLOAT", "links": None, "slot_index": 1},
            {"name": "metric_ssim", "type": "FLOAT", "links": None, "slot_index": 2},
            {"name": "diff_json", "type": "STRING", "links": None, "slot_index": 3}
        ],
        "properties": {"Node name for S&R": "StoiqoVisualDiffNode"},
        "widgets_values": [
            "Heatmap Difference",
            0.05,
            "turbo",
            1.5
        ]
    })

    # Node 32: Visual Compare Slider (Col 3, Top)
    nodes.append({
        "id": 32,
        "type": "StoiqoImageCompareNode",
        "pos": [2580, 2780],
        "size": [380, 280],
        "flags": {},
        "order": 32,
        "mode": 0,
        "inputs": [
            {"name": "image_a", "type": "IMAGE", "link": None},
            {"name": "image_b", "type": "IMAGE", "link": None}
        ],
        "outputs": [
            {"name": "composite_image", "type": "IMAGE", "links": None, "slot_index": 0},
            {"name": "mask", "type": "MASK", "links": None, "slot_index": 1}
        ],
        "properties": {"Node name for S&R": "StoiqoImageCompareNode"},
        "widgets_values": [
            "Horizontal Split Slider",
            0.50
        ]
    })

    # Node 33: Text Concatenate (Col 3, Bottom)
    nodes.append({
        "id": 33,
        "type": "StoiqoTextConcatenateNode",
        "pos": [2580, 3140],
        "size": [380, 360],
        "flags": {},
        "order": 33,
        "mode": 0,
        "inputs": [
            {"name": "text_a", "type": "STRING", "link": None},
            {"name": "text_b", "type": "STRING", "link": None},
            {"name": "text_c", "type": "STRING", "link": None},
            {"name": "text_d", "type": "STRING", "link": None}
        ],
        "outputs": [
            {"name": "text", "type": "STRING", "links": None, "slot_index": 0}
        ],
        "properties": {"Node name for S&R": "StoiqoTextConcatenateNode"},
        "widgets_values": [
            "masterpiece, best quality",
            "volumetric cinematic light",
            "",
            "",
            ", ",
            True,
            True
        ]
    })

    # Node 34: Webhook Notifier (Col 4)
    nodes.append({
        "id": 34,
        "type": "StoiqoWebhookNotifierNode",
        "pos": [3020, 2780],
        "size": [420, 560],
        "flags": {},
        "order": 34,
        "mode": 0,
        "inputs": [
            {"name": "pipe", "type": "*", "link": None},
            {"name": "images", "type": "IMAGE", "link": 38}
        ],
        "outputs": [
            {"name": "pipe", "type": "*", "links": None, "slot_index": 0},
            {"name": "images", "type": "IMAGE", "links": [46], "slot_index": 1},
            {"name": "status", "type": "STRING", "links": None, "slot_index": 2},
            {"name": "json_payload", "type": "STRING", "links": None, "slot_index": 3}
        ],
        "properties": {"Node name for S&R": "StoiqoWebhookNotifierNode"},
        "widgets_values": [
            "Discord Webhook Embed",
            "",
            "ComfyUI (STOIQO) Render Complete",
            "Scene synthesized and post-processed successfully.",
            True,
            "stoiqo_manifests",
            0,
            "",
            10
        ]
    })

    # Node 35: Pro Image Saver (Col 5)
    nodes.append({
        "id": 35,
        "type": "StoiqoProImageSaverNode",
        "pos": [3500, 2780],
        "size": [440, 620],
        "flags": {},
        "order": 35,
        "mode": 0,
        "inputs": [
            {"name": "images", "type": "IMAGE", "link": 46},
            {"name": "prompt_text", "type": "STRING", "link": None},
            {"name": "negative_text", "type": "STRING", "link": 10}
        ],
        "outputs": [
            {"name": "images", "type": "IMAGE", "links": None, "slot_index": 0},
            {"name": "file_path", "type": "STRING", "links": None, "slot_index": 1},
            {"name": "filename", "type": "STRING", "links": None, "slot_index": 2},
            {"name": "folder_path", "type": "STRING", "links": None, "slot_index": 3},
            {"name": "metadata_json", "type": "STRING", "links": None, "slot_index": 4}
        ],
        "properties": {"Node name for S&R": "StoiqoProImageSaverNode"},
        "widgets_values": [
            "%date%_render_%counter%",
            "PNG (Lossless)",
            90,
            "StoiqoCreations/%date%",
            "Both (.json + .txt)",
            "",
            "",
            True
        ]
    })

    # Zone 6 Links
    links.append([9, 6, 0, 29, 1, "STRING"])
    links.append([10, 6, 2, 35, 2, "STRING"])
    links.append([38, 22, 0, 34, 1, "IMAGE"])
    links.append([43, 28, 0, 29, 0, "IMAGE"])
    links.append([44, 28, 0, 31, 0, "IMAGE"])
    links.append([45, 30, 0, 31, 1, "IMAGE"])
    links.append([46, 34, 1, 35, 0, "IMAGE"])

    # Mathematical Collision Verification
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            n1 = nodes[i]
            n2 = nodes[j]
            x1, y1 = n1["pos"]
            w1, h1 = n1["size"]
            x2, y2 = n2["pos"]
            w2, h2 = n2["size"]
            
            # Check overlap
            overlap_x = not (x1 + w1 <= x2 or x2 + w2 <= x1)
            overlap_y = not (y1 + h1 <= y2 or y2 + h2 <= y1)
            if overlap_x and overlap_y:
                raise ValueError(f"COLLISION DETECTED between Node {n1['id']} ({n1['type']}) and Node {n2['id']} ({n2['type']})!")

    workflow = {
        "id": workflow_id,
        "revision": 2,
        "last_node_id": 35,
        "last_link_id": len(links),
        "nodes": nodes,
        "links": links,
        "groups": groups,
        "config": {},
        "extra": {
            "ds": {
                "scale": 0.50,
                "offset": [50, 50]
            }
        },
        "version": 0.4
    }

    return workflow

if __name__ == "__main__":
    wf = build_workflow()
    print(f"[STOIQO Generator V2] PASSED verification! 0 overlaps detected across {len(wf['nodes'])} nodes.")
    
    # Destination 1: ExCathedra workspace/workflows
    p1 = r"y:\Project_ExCathedra\ExCathedra\workspace\workflows\STOIQO_Master_Showcase.json"
    with open(p1, "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2)
    print(f"[STOIQO Generator V2] Saved to: {p1}")

    # Destination 2: STOIQO_Node_Suite examples
    p2 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "00_stoiqo_master_showcase.json")
    os.makedirs(os.path.dirname(p2), exist_ok=True)
    with open(p2, "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2)
    print(f"[STOIQO Generator V2] Saved to: {p2}")
