"""
[STOIQO] Master Showcase Workflow Generator
Generates the definitive 21-node STOIQO Suite Visual Showroom.

Invariant: ZERO links (pure visual showroom / node showcase).
Organized into 6 clean architectural zones following the Monolith Minimalist Dark system.
"""

import json
import os

def build_showcase():
    nodes = []
    groups = []

    # Helper to create slot objects
    def make_slot(name, slot_type, is_input=True):
        if is_input:
            return {"name": name, "type": slot_type, "link": None}
        return {"name": name, "type": slot_type, "links": []}

    # =========================================================================
    # ZONE 1: PIPELINE CORE & GENERATIVE ENGINES (Precision Blue #2997ff)
    # Bounding: [60, 60, 520, 1540]
    # =========================================================================
    groups.append({
        "title": "ZONE 1: PIPELINE CORE & GENERATIVE ENGINES",
        "bounding": [60, 60, 520, 1540],
        "color": "#182234",
        "font_size": 24
    })

    # Node 1: Universal Model Loader
    nodes.append({
        "id": 1,
        "type": "StoiqoUniversalModelLoaderNode",
        "pos": [100, 130],
        "size": [440, 290],
        "flags": {},
        "order": 1,
        "mode": 0,
        "inputs": [],
        "outputs": [make_slot("model", "MODEL", False)],
        "properties": {"Node name for S&R": "StoiqoUniversalModelLoaderNode"},
        "widgets_values": [
            "[DiT/UNET] krea2_raw_bf16.safetensors",
            "auto",
            "default",
            "sdpa",
            "Auto (Detect from model)",
            0.0,
            "",
            False,
            "None"
        ]
    })

    # Node 2: LoRA Stack
    nodes.append({
        "id": 2,
        "type": "StoiqoLoraStackNode",
        "pos": [100, 460],
        "size": [440, 240],
        "flags": {},
        "order": 2,
        "mode": 0,
        "inputs": [
            make_slot("model", "MODEL"),
            make_slot("clip", "CLIP"),
            make_slot("optional_lora_stack", "LORA_STACK")
        ],
        "outputs": [
            make_slot("model", "MODEL", False),
            make_slot("clip", "CLIP", False),
            make_slot("lora_summary", "STRING", False)
        ],
        "properties": {"Node name for S&R": "StoiqoLoraStackNode"},
        "widgets_values": ["None", "None"]
    })

    # Node 3: Seed & Resolution Controller
    nodes.append({
        "id": 3,
        "type": "StoiqoSeedControllerNode",
        "pos": [100, 740],
        "size": [440, 360],
        "flags": {},
        "order": 3,
        "mode": 0,
        "inputs": [make_slot("image", "IMAGE")],
        "outputs": [
            make_slot("seed", "INT", False),
            make_slot("width", "INT", False),
            make_slot("height", "INT", False),
            make_slot("effective_seed", "INT", False),
            make_slot("aspect_ratio", "STRING", False),
            make_slot("resolution_str", "STRING", False),
            make_slot("seed_str", "STRING", False)
        ],
        "properties": {"Node name for S&R": "StoiqoSeedControllerNode"},
        "widgets_values": [
            42,
            "1:1 Square (1024x1024)",
            "1.0x (Native / Base Resolution)",
            False,
            1024,
            1024,
            "16px (DiT / Modern Standard)",
            0.0,
            42,
            ""
        ]
    })

    # Node 4: Turbo Sampler & Direct Decoder
    nodes.append({
        "id": 4,
        "type": "StoiqoTurboSamplerNode",
        "pos": [100, 1140],
        "size": [440, 420],
        "flags": {},
        "order": 4,
        "mode": 0,
        "inputs": [
            make_slot("model", "MODEL"),
            make_slot("clip", "CLIP"),
            make_slot("vae", "VAE"),
            make_slot("image", "IMAGE"),
            make_slot("latent_image", "LATENT")
        ],
        "outputs": [
            make_slot("image", "IMAGE", False),
            make_slot("latent", "LATENT", False),
            make_slot("seed", "INT", False),
            make_slot("width", "INT", False),
            make_slot("height", "INT", False)
        ],
        "properties": {"Node name for S&R": "StoiqoTurboSamplerNode"},
        "widgets_values": [
            "masterpiece, cinematic, 8k, highly detailed",
            "ugly, blurry, low quality",
            42,
            8,
            1.0,
            "euler",
            "simple",
            1024,
            1024,
            1.0
        ]
    })

    # =========================================================================
    # ZONE 2: PROMPTING, VLM & IDENTITY (Status Emerald #30d158)
    # Bounding: [620, 60, 520, 1540]
    # =========================================================================
    groups.append({
        "title": "ZONE 2: PROMPTING, VLM & IDENTITY",
        "bounding": [620, 60, 520, 1540],
        "color": "#14261d",
        "font_size": 24
    })

    # Node 5: Prompt Generator
    nodes.append({
        "id": 5,
        "type": "StoiqoPromptGeneratorNode",
        "pos": [660, 130],
        "size": [440, 450],
        "flags": {},
        "order": 5,
        "mode": 0,
        "inputs": [
            make_slot("image_input", "IMAGE"),
            make_slot("model", "MODEL"),
            make_slot("character", "STRING")
        ],
        "outputs": [
            make_slot("prompt", "STRING", False),
            make_slot("tags", "STRING", False),
            make_slot("negative", "STRING", False),
            make_slot("raw_response", "STRING", False)
        ],
        "properties": {"Node name for S&R": "StoiqoPromptGeneratorNode"},
        "widgets_values": [
            "Image Generation (Txt2Img)",
            "Cinematic (Film Still)",
            "",
            42,
            "",
            "Direct Prompt Pass",
            "Balanced Synthesizer",
            "Standard Visual Directives",
            "",
            "",
            0.7,
            512,
            0.9,
            50,
            1.1
        ]
    })

    # Node 6: Character Memory Bank
    nodes.append({
        "id": 6,
        "type": "StoiqoCharacterMemoryNode",
        "pos": [660, 620],
        "size": [440, 390],
        "flags": {},
        "order": 6,
        "mode": 0,
        "inputs": [make_slot("reference_image", "IMAGE")],
        "outputs": [
            make_slot("full_prompt", "STRING", False),
            make_slot("character_context", "STRING", False),
            make_slot("character_dna", "STRING", False),
            make_slot("trigger_tag", "STRING", False),
            make_slot("negative_constraints", "STRING", False),
            make_slot("reference_image", "IMAGE", False)
        ],
        "properties": {"Node name for S&R": "StoiqoCharacterMemoryNode"},
        "widgets_values": [
            "New Profile (Custom)",
            "Aria",
            "aria_character",
            "athletic build, silver hair, cybernetic iris",
            "tactical titanium jacket, dark jeans",
            "Append to Prompt",
            "distorted anatomy, extra limbs",
            "confident, focused",
            "",
            "",
            ""
        ]
    })

    # Node 7: Text Concatenate & Clean
    nodes.append({
        "id": 7,
        "type": "StoiqoTextConcatenateNode",
        "pos": [660, 1050],
        "size": [440, 320],
        "flags": {},
        "order": 7,
        "mode": 0,
        "inputs": [],
        "outputs": [
            make_slot("text", "STRING", False),
            make_slot("word_count", "INT", False),
            make_slot("char_count", "INT", False),
            make_slot("token_count", "INT", False)
        ],
        "properties": {"Node name for S&R": "StoiqoTextConcatenateNode"},
        "widgets_values": [
            "", "", "", "", "", "", "", "",
            "{text_1}, {text_2}",
            ", ",
            ", ",
            "",
            "",
            True,
            True,
            True,
            True
        ]
    })

    # Node 8: Show Prompt
    nodes.append({
        "id": 8,
        "type": "StoiqoShowPromptNode",
        "pos": [660, 1410],
        "size": [440, 160],
        "flags": {},
        "order": 8,
        "mode": 0,
        "inputs": [],
        "outputs": [make_slot("text", "STRING", False)],
        "properties": {"Node name for S&R": "StoiqoShowPromptNode"},
        "widgets_values": ["[STOIQO] Active prompt preview will render here."]
    })

    # =========================================================================
    # ZONE 3: IMAGE RETOUCHING, INPAINTING & WATERMARK (Amber #ff9f0a)
    # Bounding: [1180, 60, 940, 1540]
    # 2 Sub-Columns inside Zone 3:
    #   Sub-Col A: x = 1220, width = 420
    #   Sub-Col B: x = 1670, width = 420
    # =========================================================================
    groups.append({
        "title": "ZONE 3: IMAGE RETOUCHING, INPAINTING & FORENSICS",
        "bounding": [1180, 60, 940, 1540],
        "color": "#2b2014",
        "font_size": 24
    })

    # Node 9: Image Loader Multi-Slot (Sub-Col A, Top)
    nodes.append({
        "id": 9,
        "type": "StoiqoImageLoaderNode",
        "pos": [1220, 130],
        "size": [420, 270],
        "flags": {},
        "order": 9,
        "mode": 0,
        "inputs": [],
        "outputs": [
            make_slot("image", "IMAGE", False),
            make_slot("mask", "MASK", False),
            make_slot("image_1", "IMAGE", False),
            make_slot("image_2", "IMAGE", False),
            make_slot("image_3", "IMAGE", False),
            make_slot("loaded_count", "INT", False)
        ],
        "properties": {"Node name for S&R": "StoiqoImageLoaderNode"},
        "widgets_values": ["", "", "", "Pad with Transparency", "Slot 1 (Single / Main)"]
    })

    # Node 10: Spatial Cropper & Mask Gen (Sub-Col A, Mid)
    nodes.append({
        "id": 10,
        "type": "StoiqoSpatialCropperNode",
        "pos": [1220, 440],
        "size": [420, 360],
        "flags": {},
        "order": 10,
        "mode": 0,
        "inputs": [
            make_slot("image", "IMAGE"),
            make_slot("model", "MODEL")
        ],
        "outputs": [
            make_slot("cropped_image", "IMAGE", False),
            make_slot("mask", "MASK", False),
            make_slot("bbox_info", "BBOX_INFO", False),
            make_slot("segs", "SEGS", False)
        ],
        "properties": {"Node name for S&R": "StoiqoSpatialCropperNode"},
        "widgets_values": ["", "", 10, "Square (1:1)", 16, False, 1.0, "xyxy"]
    })

    # Node 11: Inpaint Stitcher (Sub-Col A, Bottom)
    nodes.append({
        "id": 11,
        "type": "StoiqoInpaintStitcherNode",
        "pos": [1220, 840],
        "size": [420, 400],
        "flags": {},
        "order": 11,
        "mode": 0,
        "inputs": [
            make_slot("original_image", "IMAGE"),
            make_slot("edited_image", "IMAGE"),
            make_slot("optional_mask", "MASK")
        ],
        "outputs": [
            make_slot("composite_image", "IMAGE", False),
            make_slot("stitch_mask", "MASK", False),
            make_slot("cropped_roi", "IMAGE", False),
            make_slot("bbox_info", "BBOX_INFO", False)
        ],
        "properties": {"Node name for S&R": "StoiqoInpaintStitcherNode"},
        "widgets_values": [
            "", "Normal", "Pad with Transparency", 16, 5, "None", 0.5, 0.0, 0.0
        ]
    })

    # Node 12: Visual Compare Slider & Zoom (Sub-Col B, Top)
    nodes.append({
        "id": 12,
        "type": "StoiqoImageCompareNode",
        "pos": [1670, 130],
        "size": [420, 310],
        "flags": {},
        "order": 12,
        "mode": 0,
        "inputs": [
            make_slot("image_a", "IMAGE"),
            make_slot("image_b", "IMAGE")
        ],
        "outputs": [
            make_slot("image_a", "IMAGE", False),
            make_slot("image_b", "IMAGE", False),
            make_slot("diff_heatmap", "IMAGE", False),
            make_slot("diff_mask", "MASK", False),
            make_slot("metrics_json", "STRING", False)
        ],
        "properties": {"Node name for S&R": "StoiqoImageCompareNode"},
        "widgets_values": ["Split Slider (Interactive)", "Turbo", 2.0, 0.1]
    })

    # Node 13: Frequency Separation Hub (Sub-Col B, Mid)
    nodes.append({
        "id": 13,
        "type": "StoiqoFrequencySeparationNode",
        "pos": [1670, 480],
        "size": [420, 320],
        "flags": {},
        "order": 13,
        "mode": 0,
        "inputs": [
            make_slot("image", "IMAGE"),
            make_slot("high_freq_override", "IMAGE")
        ],
        "outputs": [
            make_slot("image", "IMAGE", False),
            make_slot("low_freq_image", "IMAGE", False),
            make_slot("high_freq_image", "IMAGE", False),
            make_slot("split_meta", "STRING", False)
        ],
        "properties": {"Node name for S&R": "StoiqoFrequencySeparationNode"},
        "widgets_values": [8.0, 1.0, 1.0, "Wavelet / Gaussian", True, ""]
    })

    # Node 14: Smart Watermark & Logo Stamp (Sub-Col B, Bottom)
    nodes.append({
        "id": 14,
        "type": "StoiqoWatermarkNode",
        "pos": [1670, 840],
        "size": [420, 440],
        "flags": {},
        "order": 14,
        "mode": 0,
        "inputs": [
            make_slot("base_image", "IMAGE"),
            make_slot("watermark_image", "IMAGE"),
            make_slot("optional_mask", "MASK")
        ],
        "outputs": [
            make_slot("image", "IMAGE", False),
            make_slot("watermark_mask", "MASK", False),
            make_slot("overlay_info", "STRING", False)
        ],
        "properties": {"Node name for S&R": "StoiqoWatermarkNode"},
        "widgets_values": [
            "Bottom-Right",
            "Proportional (Canvas Ratio)",
            15,
            5,
            0.85,
            "Alpha Blending",
            "",
            "#ffffff",
            "None (Keep Image As-Is)",
            10,
            2
        ]
    })

    # =========================================================================
    # ZONE 4: AUDIO & MUSIC PRODUCTION (Precision Blue #2997ff)
    # Bounding: [60, 1640, 520, 860]
    # =========================================================================
    groups.append({
        "title": "ZONE 4: AUDIO & MUSIC PRODUCTION",
        "bounding": [60, 1640, 520, 860],
        "color": "#191e2b",
        "font_size": 24
    })

    # Node 15: Music Prompt & Lyrics Engine
    nodes.append({
        "id": 15,
        "type": "StoiqoMusicPromptEngineNode",
        "pos": [100, 1710],
        "size": [440, 440],
        "flags": {},
        "order": 15,
        "mode": 0,
        "inputs": [
            make_slot("cover_image", "IMAGE"),
            make_slot("model", "MODEL")
        ],
        "outputs": [
            make_slot("style", "STRING", False),
            make_slot("lyrics", "STRING", False),
            make_slot("title", "STRING", False),
            make_slot("abc_planning", "STRING", False),
            make_slot("mode", "STRING", False),
            make_slot("max_duration", "FLOAT", False),
            make_slot("bpm", "INT", False),
            make_slot("musical_key", "STRING", False),
            make_slot("time_signature", "STRING", False),
            make_slot("genre_tags", "STRING", False),
            make_slot("vocal_description", "STRING", False),
            make_slot("seed", "INT", False)
        ],
        "properties": {"Node name for S&R": "StoiqoMusicPromptEngineNode"},
        "widgets_values": [
            "Cyberpunk synthwave electronic driving beat",
            "Standard Producer Directives",
            "Synthwave / Retrowave",
            "Instrumental",
            "English",
            "Verse-Chorus-Verse-Chorus-Outro",
            "Moderate (100-120 BPM)",
            "", "", "",
            42,
            0.7,
            1.1,
            512
        ]
    })

    # Node 16: Pro Audio Saver & Metadata Hub
    nodes.append({
        "id": 16,
        "type": "StoiqoAudioSaverNode",
        "pos": [100, 2190],
        "size": [440, 270],
        "flags": {},
        "order": 16,
        "mode": 0,
        "inputs": [make_slot("audio", "AUDIO")],
        "outputs": [
            make_slot("audio", "AUDIO", False),
            make_slot("file_path", "STRING", False),
            make_slot("filename", "STRING", False),
            make_slot("metadata_json", "STRING", False)
        ],
        "properties": {"Node name for S&R": "StoiqoAudioSaverNode"},
        "widgets_values": [
            "ExCathedra_Audio",
            "MP3 (320kbps)",
            "StoiqoMusic/%date%",
            "Master Audio Track",
            "",
            "Cinematic / Modern",
            "Electronic",
            120,
            "None"
        ]
    })

    # =========================================================================
    # ZONE 5: VIDEO & MOTION GENERATION (Crimson Red #ff453a)
    # Bounding: [620, 1640, 520, 860]
    # =========================================================================
    groups.append({
        "title": "ZONE 5: VIDEO & MOTION GENERATION",
        "bounding": [620, 1640, 520, 860],
        "color": "#281414",
        "font_size": 24
    })

    # Node 17: Video Deflicker & Frame Interpolator
    nodes.append({
        "id": 17,
        "type": "StoiqoVideoEnhancerNode",
        "pos": [660, 1710],
        "size": [440, 360],
        "flags": {},
        "order": 17,
        "mode": 0,
        "inputs": [make_slot("images", "IMAGE")],
        "outputs": [
            make_slot("enhanced_frames", "IMAGE", False),
            make_slot("output_frame_count", "INT", False),
            make_slot("metrics_json", "STRING", False)
        ],
        "properties": {"Node name for S&R": "StoiqoVideoEnhancerNode"},
        "widgets_values": [
            True,
            1,
            3,
            0.05,
            0.5,
            0.5,
            "Linear"
        ]
    })

    # Node 18: Pro Video Saver & Frame Exporter
    nodes.append({
        "id": 18,
        "type": "StoiqoVideoSaverNode",
        "pos": [660, 2110],
        "size": [440, 340],
        "flags": {},
        "order": 18,
        "mode": 0,
        "inputs": [
            make_slot("images", "IMAGE"),
            make_slot("audio", "AUDIO")
        ],
        "outputs": [
            make_slot("images", "IMAGE", False),
            make_slot("file_path", "STRING", False),
            make_slot("filename", "STRING", False),
            make_slot("metadata_json", "STRING", False)
        ],
        "properties": {"Node name for S&R": "StoiqoVideoSaverNode"},
        "widgets_values": [
            24,
            "ExCathedra_Video",
            "MP4 (h264)",
            90,
            "StoiqoVideo/%date%",
            "",
            "None"
        ]
    })

    # =========================================================================
    # ZONE 6: DATASET, TRAINING & PRO EXPORT (Titanium #1c1d22)
    # Bounding: [1180, 1640, 940, 860]
    # =========================================================================
    groups.append({
        "title": "ZONE 6: DATASET, TRAINING & PRO EXPORT",
        "bounding": [1180, 1640, 940, 860],
        "color": "#1c1d22",
        "font_size": 24
    })

    # Node 19: Smart Folder Image Iterator (Sub-Col A, Top)
    nodes.append({
        "id": 19,
        "type": "StoiqoSmartFolderImageIterator",
        "pos": [1220, 1710],
        "size": [420, 360],
        "flags": {},
        "order": 19,
        "mode": 0,
        "inputs": [],
        "outputs": [
            make_slot("image", "IMAGE", False),
            make_slot("mask", "MASK", False),
            make_slot("filename", "STRING", False),
            make_slot("width", "INT", False),
            make_slot("height", "INT", False)
        ],
        "properties": {"Node name for S&R": "StoiqoSmartFolderImageIterator"},
        "widgets_values": [
            "workspace/datasets/input",
            "Alphabetical Order",
            0,
            "Incremental (+1)",
            42,
            True,
            False,
            ".txt",
            False,
            1
        ]
    })

    # Node 20: Dataset & LoRA Toolkit (Sub-Col B, Top)
    nodes.append({
        "id": 20,
        "type": "StoiqoDatasetWriterNode",
        "pos": [1670, 1710],
        "size": [420, 480],
        "flags": {},
        "order": 20,
        "mode": 0,
        "inputs": [make_slot("image", "IMAGE")],
        "outputs": [
            make_slot("prompt", "STRING", False),
            make_slot("tags", "STRING", False),
            make_slot("negative", "STRING", False),
            make_slot("image", "IMAGE", False)
        ],
        "properties": {"Node name for S&R": "StoiqoDatasetWriterNode"},
        "widgets_values": [
            "",
            "",
            "Danbooru Tags + Natural Text",
            "",
            False,
            0,
            ", ",
            True,
            True,
            "workspace/datasets/output",
            True,
            "dataset_sample",
            "",
            "",
            True,
            "PNG",
            False,
            0.95,
            "",
            42
        ]
    })

    # Node 21: Pro Image Saver & Metadata Hub (Sub-Col A, Bottom)
    nodes.append({
        "id": 21,
        "type": "StoiqoProImageSaverNode",
        "pos": [1220, 2110],
        "size": [420, 340],
        "flags": {},
        "order": 21,
        "mode": 0,
        "inputs": [make_slot("images", "IMAGE")],
        "outputs": [
            make_slot("images", "IMAGE", False),
            make_slot("file_path", "STRING", False),
            make_slot("filename", "STRING", False),
            make_slot("folder_path", "STRING", False),
            make_slot("metadata_json", "STRING", False)
        ],
        "properties": {"Node name for S&R": "StoiqoProImageSaverNode"},
        "widgets_values": [
            "ExCathedra_Txt2Img",
            "PNG (Lossless)",
            90,
            "StoiqoCreations/%date%",
            "None",
            True,
            False
        ]
    })

    workflow = {
        "id": "stoiqo-master-showcase-v3",
        "revision": 3,
        "last_node_id": 21,
        "last_link_id": 0,
        "nodes": nodes,
        "links": [],
        "groups": groups,
        "config": {},
        "extra": {
            "ds": {
                "scale": 0.65,
                "offset": [100, 50]
            }
        },
        "version": 0.4
    }

    return workflow

def main():
    wf = build_showcase()
    
    # Target 1: workspace workflows
    target_workspace = r"y:\Project_ExCathedra\ExCathedra\workspace\workflows\stoiqo_master_showcase.json"
    os.makedirs(os.path.dirname(target_workspace), exist_ok=True)
    with open(target_workspace, "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2)
    print(f"Generated showroom showcase: {target_workspace}")

    # Target 2: suite examples
    target_example = r"y:\Project_ExCathedra\SideProject\ComfyUI_CustomNodes\STOIQO_Node_Suite\examples\00_stoiqo_master_showcase.json"
    os.makedirs(os.path.dirname(target_example), exist_ok=True)
    with open(target_example, "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2)
    print(f"Generated showroom showcase: {target_example}")

if __name__ == "__main__":
    main()
