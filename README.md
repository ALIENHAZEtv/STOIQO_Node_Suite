# STOIQO Node Suite

[![CI](https://github.com/ALIENHAZEtv/STOIQO_Node_Suite/actions/workflows/ci.yml/badge.svg)](https://github.com/ALIENHAZEtv/STOIQO_Node_Suite/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/downloads/)
[![ComfyUI-Manager](https://img.shields.io/badge/ComfyUI--Manager-Registered-purple.svg)](https://github.com/ltdrdata/ComfyUI-Manager)

A production-ready ComfyUI custom node suite for **Visual Prompt Generation, Multimodal Comparison, and Creative Utilities** powered by Vision-Language Models (Qwen2.5-VL and compatible architectures).

The suite provides complete modularity across Prompt Generation, VLM caching, Forensic Visual Diff, Interactive Before/After Split Sliders, Text Concatenation, and VAE-Safe Image Resolution generation.

---

## Key Features

| Feature | Details |
|---|---|
| **Live WebSocket Token Streaming** | Real-time token streaming with live canvas typewriter effect via `TextIteratorStreamer` |
| **Integrated Video Audio Muxing** | Native FFmpeg AAC/Opus (320kbps) audio-video container muxing in `Pro Video Saver` with zero sync drift |
| **Conditioning Bypass & 16-Ch DiT** | Direct `CONDITIONING` inputs and native 16-channel latent synthesis in `Turbo Sampler` (FLUX/DiT) |
| **Flow-Matching Presets Hub** | Automatic flow-matching shifts in `Tri-Model Loader Hub` for Z-Image Turbo, FLUX.1, Ace-Step 1.5, SD3.5, and MiniMax H3 |
| **Instant Interrupt Support** | Immediate generation abort when user cancels via `comfy.model_management` |
| **Impact-Pack SEGS Bridge** | Direct `SEGS` output in `[STOIQO] Spatial Cropper` for open-vocabulary detection in Impact-Pack Detailers |
| **rgthree Context Compatibility** | Dual-compatible universal `pipe` connection in `Turbo Sampler` and `Tri-Model Loader Hub` |
| **GPU-Accelerated Tensor Ops** | Pure PyTorch CUDA separable Gaussian blur in `Inpaint Stitcher` and `Watermark Node` with zero PIL/CPU roundtrips |
| **Interactive Canvas Audio Player** | Embedded HTML5 audio player widget in `Pro Audio Saver` with scrubber, play/pause, and duration tracking |
| **Universal API Endpoints (0 GB VRAM)** | Native integration with local Ollama (`localhost:11434`), LM Studio, vLLM, or OpenAI-compatible APIs |
| **Prompt Synthesizer Engine** | Generates, refines, and directs prompts in a single model pass from images or raw text directives |
| **VLM Model Loader** | Dedicated resident VRAM cache node emitting `STOIQO_MODEL` pipe for zero-latency workflows |
| **Visual Compare Slider & Zoom** | Interactive split curtain with synchronized 10x pan/zoom on identical pixel coordinates |
| **Visual Diff & Forensic Inspector** | Multi-image comparative analysis with structured difference reports and change tags |
| **Text Concatenate & Clean** | Multi-block prompt joining with smart separator hygiene and prefix/suffix formatting |
| **Image Resolution & Aspect Ratio** | Generates VAE-safe divisible width & height dimensions across standard aspect ratios |
| **Unified Hardware Presets** | VRAM-tiered presets (3B, 7B, 32B, 72B), API endpoints, or custom models with native Windows Folder Browser |
| **Download Progress Tracker** | Live byte-level HuggingFace download tracking on ComfyUI's top progress bar and canvas badge |
| **AI Personas & Directives** | Built-in system prompt personas (Visual Prompt Synthesizer, Dataset Annotator, Literal Describer) + custom override |
| **Dual Prompt Splitter** | Simultaneous outputs for concise tags (<75 tokens) and extended descriptive prose paragraph |
| **Negative & Artifact Auditor** | Forensic visual inspection of defects (anatomy, lighting, artifacts) with dedicated `negative` output pin |
| **Collapsible LoRA Toolkit** | On-demand dataset suite: trigger word pinned at index 0, blacklist filtering, tag shuffling, and Kohya JSON manifests |
| **Smart Pre-Scaling** | Protects VRAM by automatically scaling images to ~1.0 Mpx (multiples of 28 for Qwen2.5-VL 2D-RoPE ViT) |
| **Music Prompt & Lyrics Engine (YuE2)** | Composes full rhyming lyrics and acoustic production descriptors directly mapped to YuE2/Suno with optional multimodal cover art |
| **Spatial Cropper & Mask Generator** | Visual grounding by text prompt producing cropped subjects, alpha masks, and normalized JSON bounding boxes |
| **Smart Folder Image Iterator** | Batch dataset processing with auto-queue resumption (`skip_captioned`) and recursive folder discovery |
| **Trio Image Loader & Hero Preview** | Loads 3 images simultaneously with clickable thumbnail gallery and large synchronized vertical hero preview |
| **Pro Image Saver & Metadata Hub** | High-speed multi-format export (PNG/WEBP/JPEG), dynamic filename templating, and sidecar JSON/TXT manifests without canvas clutter |
| **Native Theme Independence** | Zero hardcoded node colors: fully respects ComfyUI canvas themes and custom node coloring |

---

## Installation

### Option A — ComfyUI Manager (recommended)
Search for `STOIQO Comfyui Nodes` in the ComfyUI Manager custom nodes browser and click **Install**.

### Option B — Manual
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/ALIENHAZEtv/STOIQO_Node_Suite.git
cd STOIQO_Node_Suite
pip install -r requirements.txt
```
Restart ComfyUI. The nodes will appear under the **STOIQO** category.

---

## Supported Models

| Preset | VRAM (4-bit NF4) | Active Weight Size | Recommended GPU |
|---|---|---|---|
| `<= 8 GB VRAM - Qwen2.5-VL-3B` | ~2.5 GB | ~3.5 GB | GTX 1070, RTX 2060, RTX 3050/3060 8GB |
| `12-16 GB VRAM - Qwen2.5-VL-7B` *(Default)* | ~5.0 GB | ~7.0 GB | RTX 3060 12GB, RTX 4070, RTX 4080 |
| `24 GB VRAM - Qwen2.5-VL-32B` | ~20.0 GB | ~22.0 GB | RTX 3090, RTX 4090, A5000 |
| `48+ GB VRAM - Qwen2.5-VL-72B` | ~45.0 GB | ~48.0 GB | A6000, A100, Dual 3090/4090 |
| `🌐 API Endpoint (Ollama / OpenAI / vLLM)` | **0 GB (Offloaded)** | Remote / Local Host | Any GPU / CPU (Ollama, LM Studio, vLLM, OpenAI) |
| `📁 Custom Model (Local Disk Path)` | Custom | Custom | Any local folder with `config.json` |

---

## Node Structure & Parameters

### Modular Prompt Pipeline

`[STOIQO] VLM Model Loader` → `[STOIQO] Prompt Synthesizer Engine`, with optional satellite nodes plugged into the Synthesizer. (The former all-in-one *Prompt Generator Engine* has been removed; every feature now lives in these nodes.)

#### `[STOIQO] VLM Model Loader` — § Engine & Hardware
- `model_preset`: Pre-quantized 4-bit preset, API endpoint, or `📁 Custom Model (Local Disk Path)`.
- `local_model_path`: Custom model folder, with a **📁 Browse Model Folder on Disk** button (native folder picker) or an absolute path.
- `quantization`: `4bit - NF4 (Recommended - Low VRAM)`, `8bit`, or `none (fp16 / bf16)`.
- `attention_mode`: `sdpa (PyTorch Native - Recommended)`, `flash_attention_2`, or `eager`.
- `keep_in_vram`: When `False` (Low VRAM mode) the model is unloaded after generation and transparently reloaded on the next run (replaces the old `unload_model_after`).

#### `[STOIQO] Prompt Synthesizer Engine` — core
- `stoiqo_model` (required): pipe from the Model Loader.
- `user_directives`: Creative directives / modifications. In text-only mode this is the source concept to expand.
- `image` (optional): single image or batch. **A batch is captioned image-by-image** (seed + index), with list outputs — ideal for LoRA dataset tagging. No image = Text-Only mode.
- `multi_image_context` (optional): fuses images into **one** prompt (see Multi-Image Context Hub).
- `style_directives`, `sampling_options`, `character_context` (optional): satellites below.
- System prompt dispatch is automatic: Text-Only → text-expansion engine, single image → selected persona, multiple images → multi-image synthesis engine, `Custom` → your own instructions.
- Outputs (all lists, one entry per image): `prompt`, `tags` (<77 tokens), `negative` (surgical, with prefix), `raw_response`. Tokens stream live to the canvas.

#### `[STOIQO] AI Persona & Style Directives` — § Task & Directives
- `system_prompt`: persona preset or `✏️ Custom (Manual Override)` (uses `custom_system_prompt`).
- `prompt_type`: Detailed Narrative, Short Summary, Tags & Keywords, Structured Categories, Booru Tags, Cinematic & Video Script, …
- `artistic_style`: Auto-Detect, Photorealistic, Anime, 3D CGI, Pencil Sketch, Concept Art, Oil Painting, Cyberpunk, Vintage Film, …
- `enable_dual_prompt`: concise tags (<75 tokens) + extended prose.
- `audit_artifacts`: forensic defect audit → negative prompt.
- `negative_prompt_prefix`: prefix prepended to the negative prompt (e.g. `worst quality, low quality, `).

#### `[STOIQO] LLM Sampling & Precision` — § Sampling & Generation
- `temperature` (`0.0` = greedy), `top_p`, `top_k`, `repetition_penalty`, `max_new_tokens`, `seed`.
- `target_megapixel`: resolution budget (default `1.0` MP ≈ 1024×1024), scaled to multiples of 28 for the Qwen2.5-VL ViT.

#### `[STOIQO] Multi-Image Context Hub`
`image_1`, `image_2`, optional `image_3` + `fusion_mode` (Contextual Fusion, Comparative Difference, Character & Style Consistency, Sequential Angle). If the Synthesizer also has a primary `image`, it is fused as `<Image 1>`. The per-image megapixel budget shrinks automatically as more images are fused (min 0.35 MP).

#### `[STOIQO] Character Memory Bank`
Lorebook & visual DNA injected in *Always Prepend* mode or *Smart Detect* mode (whole-word match of name/trigger tag in the directives).

#### `[STOIQO] Dataset & LoRA Toolkit`
Trigger word pinned at index 0, blacklist filtering, tag shuffling, `.txt` / Kohya-compatible `.json` manifests, original-filename tracing through Reroutes. See the node tooltips for all options.

---

## Outputs

- `prompt`: **Final Descriptive Prompt** — rich narrative prose, standard caption, or the full T5-XXL paragraph in dual mode. (list of STRING)
- `tags`: **Concise Tags (< 77 tokens)** — comma-separated, optimal for CLIP ViT-L encoders, LoRA training and tag-based conditioning. (list of STRING)
- `negative`: **Surgical Negative Prompt** — flaws detected during visual audit, prefixed with your custom prefix. (list of STRING)
- `raw_response`: Unprocessed model output. (list of STRING)

---

## Companion Nodes in Suite


### 1. `[STOIQO] VLM Model Loader`
Preloads and caches a Vision-Language Model in VRAM once, emitting a `stoiqo_model` pipe. Connecting this pipe to `[STOIQO] Prompt Synthesizer Engine` or `[STOIQO] Visual Diff & Forensic Inspector` avoids redundant model re-initialization and allows chaining multiple tasks with zero VRAM re-allocation.

### 2. `[STOIQO] Visual Diff & Forensic Inspector`
Forensic comparison node taking `<Image 1>` (Baseline/Reference) and `<Image 2>` (Comparison/Altered).
- **Inputs:** `image_a`, `image_b`, `analysis_focus` (Consistency, Aesthetics, Lighting, Textures, Defects), `analysis_depth`, `custom_directives`.
- **Outputs:**
  - `diff_report`: Structured categorized report of all verifiable differences.
  - `summary`: 1-2 sentence executive overview.
  - `change_tags`: Comma-separated list of altered visual attributes and keywords.

### 3. `[STOIQO] Visual Compare Slider & Zoom`
Interactive canvas comparison node specifically tailored for before/after workflows (e.g. Original vs Upscaled, Base vs Denoised, Seed A vs Seed B).
- **Interactive Modes:**
  - `↔ Split Slider`: Draggable vertical curtain dividing Image A and Image B with grab handle `◄►`.
  - `👁 Toggle A/B`: Click or tap anywhere to instantly flip between Image A and Image B.
  - `◫ Side-by-Side`: Synchronous side-by-side view with identical coordinate alignment.
- **Synchronized Pan & Zoom:**
  - Mouse wheel zooms in up to **10.0x (1000%)** anchored directly under cursor coordinates.
  - Mouse drag pans across both images simultaneously.
  - **Resolution Normalized:** Automatically aligns different resolutions (e.g. 1024x1024 baseline vs 4096x4096 upscale) to the exact same relative pixel center, so zooming into an eye or texture inspects the exact same feature on both images!
  - `[⟲ Reset Zoom]` and `[🔍 XXX%]` indicator badges on top mini-toolbar.
- **Outputs:** Pass-through `image_a` and `image_b` pins so the node can be inserted non-destructively anywhere in the workflow graph.

### 4. `[STOIQO] Show Prompt`
Preview generated prompts directly on the canvas with single strings and batch lists, complete with a convenient **📋 Copy Prompt to Clipboard** button.

### 5. `[STOIQO] Text Concatenate & Clean`
Concatenates up to four text/prompt inputs with surgical precision:
- **Separators:** Comma-space (default), Space, Newline (`\n`), Double Newline / Paragraph (`\n\n`), Pipe (` | `), Semicolon (`; `), or custom separator string.
- **Hygiene & Formatting:** Automatic whitespace trimming, deduplication of redundant commas/separators, and empty block skipping.
- **Prefix & Suffix:** Optional prepend/append strings (master triggers, quality tags, artist names).
- **Outputs:** `text` (STRING), `word_count` (INT), `char_count` (INT).

### 6. `[STOIQO] Image Resolution & Aspect Ratio`
Generates mathematically safe `width` and `height` dimensions for diffusion models (Flux.1, SDXL, SD 3.5, SD 1.5):
- **Aspect Ratio Presets:** `1:1 Square`, `16:9 Landscape`, `9:16 Portrait / Story`, `4:3 Standard Photo`, `3:4 Classic Portrait`, `3:2 35mm`, `2:3 Portrait`, `21:9 Cinema`, `9:21 Vertical`, `4:5 / 5:4 Social Media`, or `✏️ Custom`.
- **Target Scale Presets:** `1.0 MP (1024 base - Flux/SDXL)`, `0.26 MP (512 base - SD 1.5)`, `1.5 MP (1280 base)`, `2.0 MP (1440 base)`, or `Exact Preset Dimensions`.
- **Safe Divisibility (`multiple_of`):** Enforces divisibility by 16 (default), 8, 32, or 64 to prevent VAE decode tensor dimension mismatch runtime crashes.
- **Orientation Swap:** Instant toggle to swap Width <-> Height (Landscape <-> Portrait flip).
- **Outputs:** `width` (INT), `height` (INT), `aspect_ratio` (FLOAT), `resolution_str` (STRING).

### 7. `[STOIQO] Music Prompt & Lyrics Engine (YuE2 & AI Audio)`
An autonomous AI Music Architect and Lyricist specifically designed for the **YuE2 / Suno** audio generation ecosystem and compatible AI music pipelines:
- **Zero-Genre Bias & Synesthesia:** Accepts natural-language song concepts and directives without forcing rigid templates. Optionally connect an `album_cover` image to synthesize acoustic textures, mood, and genre aesthetics from visual album artwork.
- **Strict YuE2 Engineering Standards:**
  - **`Style`:** Dense, comma-separated English acoustic production descriptor (`[Language], [Vocal Style], [Genre & Subgenres], [BPM Tempo], [Instruments], [Mix Profile]`). Strictly isolates musical instructions away from lyrical lines.
  - **`Lyrics`:** Exclusively singable verses, hooks, and choruses tagged with YuE2 structural markers (`[Verse 1]`, `[Chorus]`, `[Bridge]`, `[Outro]`). Free from chord progressions, guitar tabs, or non-singable stage directions.
  - **`Custom Lyrics Mode`:** Paste custom song lyrics into `custom_lyrics`; the engine preserves your lyrical text 100% untouched while autonomously reverse-engineering the matching acoustic style, BPM, key, duration, and arrangement mode.
- **Inputs:**
  - `idea`: Natural language description of the song theme, genre, mood, or creative directive.
  - `system_prompt`: Persona selector (`Universal Music Architect & Lyricist`, `Songwriter & Topliner`, `Sound Designer & Producer`, `Hit-Song Lyricist`, or `Custom`).
  - `genre`, `vocal`, `language`, `structure`, `tempo`: Musical parameters (includes `Auto / Inferred by AI` options for unconstrained creativity).
  - Optional: `album_cover` (IMAGE), `custom_lyrics` (STRING), `custom_directives` (STRING), `stoiqo_model` (STOIQO_MODEL cache pipe), `seed`, `temperature`, `repetition_penalty`, `max_new_tokens`.
- **12 Dedicated Output Pins:**
  - `style` (STRING): Complete acoustic production style prompt for YuE2/Suno.
  - `lyrics` (STRING): Pure structured singable lyrics.
  - `title` (STRING): Generated or inferred song title.
  - `abc_planning` (BOOLEAN): Symbolic ABC melody/harmony flag (`True` for `full` mode, `False` for `melody`).
  - `mode` (STRING): Execution mode string (`"full"` or `"melody"`).
  - `max_duration` (FLOAT): Recommended duration in seconds (120.0s to 240.0s for full songs).
  - `bpm` (INT): Discrete tempo value (e.g. `128`).
  - `musical_key` (STRING): Root note and scale (e.g. `F# Minor`, `Eb Major`).
  - `time_signature` (STRING): Metric signature (e.g. `4/4`, `3/4`, `6/8`).
  - `genre_tags` (STRING): Comma-separated genre and stylistic classification keywords.
  - `vocal_description` (STRING): Detailed description of vocal delivery, gender, and timbre.
  - `seed` (INT): Resolved random seed for deterministic reproduction.

### 8. `[STOIQO] Spatial Cropper & Mask Generator`
Visual Grounding node that uses the Vision-Language Model to locate any object, person, or detail described in plain English, outputting a surgical crop, binary mask, and normalized bounding box:
- **Visual Grounding:** Detects subjects from text prompts (`detect_prompt`, e.g. `"main subject"`, `"vintage watch"`, `"face"`, `"sneakers"`).
- **Bounding Box Parser:** Tolerant parser supporting Qwen2.5-VL 2D pixel coordinates, Cartesian coordinates, and bracketed formats.
- **Crop Shapes:** `Tight Bounding Box` or `1:1 Square (Centered on Subject)` — ideal for training LoRA avatar datasets with subject centering.
- **Edge Softening & Feathering:** Built-in `mask_feather` radius (0-64 px Gaussian blur) and `padding_percent` safety margin to prepare seamless inpainting masks.
- **Inputs:** `stoiqo_model` (STOIQO_MODEL), `image` (IMAGE), `detect_prompt` (STRING), `padding_percent` (INT), `target_megapixel` (FLOAT), `invert_mask` (BOOLEAN), `crop_shape`, `mask_feather` (INT), `coord_order`.
- **Outputs:**
  - `cropped_image` (IMAGE): Subject image cropped and bounded to detected coordinates.
  - `mask` (MASK): Standard ComfyUI alpha/binary mask of the detected bounding region.
  - `bbox_info` (STRING): JSON metadata containing normalized `ymin, xmin, ymax, xmax` coordinates.

### 9. `[STOIQO] Dataset & LoRA Toolkit`
Dedicated caption post-processing, sanitization, and dataset manifest exporter for fine-tuning Flux, SDXL, and SD 1.5 LoRAs:
- **Trigger Word Pinning:** Pins your training activator keyword (e.g. `sks_character, `) strictly at position index 0 of every output caption.
- **Blacklist Filtering:** Strips unwanted watermarks, quality buzzwords, or dataset noise (e.g. `blurry, watermark, signature, lowres`).
- **Deterministic Tag Shuffling:** Shuffles non-trigger tags via seed to prevent positional bias and model overfitting during training epochs.
- **Dual Manifest Export:** Exports sidecar `.txt` caption files and structured `.json` metadata manifests compliant with Kohya_ss, SimpleTuner, and AI-Toolkit.
- **Graph Lineage Tracing:** Automatically traverses upstream nodes to recover the original source image filename, even through reroutes.
- **Inputs:** `caption` (STRING), `tags` (STRING), `negative` (STRING), `trigger_word`, `blacklist_tags`, `shuffle_tags`, `tag_separator` (`, `, `\n`, ` | `), `save_txt`, `save_json_metadata`, `output_dir`, `use_original_filename`, `fallback_prefix`, optional `image`, `filename` override, `seed`.
- **Outputs:** `processed_caption` (STRING list), `processed_tags` (STRING list), `processed_negative` (STRING list).

### 10. `[STOIQO] Smart Folder Image Iterator`
Batch dataset ingestion node with stateful folder traversal and auto-queue resuming:
- **Folder Traversal:** Scans local directories for `.jpg`, `.jpeg`, `.png`, `.webp`, and `.bmp` files, with optional `recursive` subfolder discovery.
- **Smart Resume (`skip_captioned`):** Automatically detects if a companion caption file (`.txt`, `.json`, `.caption`) already exists next to the image and skips already processed files — allowing seamless resumption of large dataset captioning jobs without reprocessing.
- **Canvas Metadata:** Displays current image index, total image count, and loaded filename directly on the ComfyUI canvas.
- **Inputs:** `folder_path` (STRING), `index` (INT, 0 to 999999), `skip_captioned` (BOOLEAN), `caption_extension` (`.txt`, `.json`, `.caption`), `recursive` (BOOLEAN).
- **Outputs:** `image` (IMAGE), `mask` (MASK), `filename` (STRING), `width` (INT), `height` (INT).

### 11. `[STOIQO] Trio Image Loader (Hero & Thumbs)`
Ergonomic 3-slot image loader consolidating multiple standard loader nodes into a unified visual workspace:
- **Integrated Hero Preview:** Interactive canvas widget featuring clickable thumbnail cards for Slots 1, 2, and 3, paired with a synchronized vertical Hero Preview that updates instantly on click.
- **Smart Slot Routing:** Dedicated outputs for all 3 loaded images plus dynamic `focused_image` and `focused_mask` routed to whichever thumbnail is currently active.
- **Batch Output:** Emits a combined `batch_images` tensor stacking all loaded images together, along with an active `loaded_count` integer.
- **Inputs:** `image_1`, `image_2` (optional or `"none"`), `image_3` (optional or `"none"`), `active_focus` (`Slot 1`, `Slot 2`, `Slot 3`).
- **Outputs:** `image_1`, `mask_1`, `image_2`, `mask_2`, `image_3`, `mask_3`, `focused_image`, `focused_mask`, `batch_images`, `loaded_count`.

### 12. `[STOIQO] Pro Image Saver & Metadata Hub`
High-efficiency, production-grade image saver engineered for speed, clean canvas workflows, and complete metadata provenance:
- **Zero Canvas Clutter:** Suppresses redundant thumbnail preview re-renders, preventing UI freeze when saving large image batches or 4K renders.
- **Multi-Format Export:** Supports `PNG (Lossless)`, `WEBP (Quality)`, and `JPEG (Standard)` with configurable quality/compression controls.
- **Dynamic Token Templating:** File naming and subfolder paths support rich placeholders: `%date%`, `%time%`, `%year%`, `%month%`, `%day%`, `%seed%`, `%steps%`, `%cfg%`, `%sampler%`, `%model%`, `%width%`, `%height%`, and `%counter%`.
- **Sidecar Metadata Generation:** Saves paired `.txt` (prompt text) and comprehensive `.json` sidecars capturing model name, sampling settings, positive/negative prompts, dimensions, and full ComfyUI workflow graph.
- **Inputs:** `images` (IMAGE), `filename_prefix` (STRING), `format`, `quality` (INT), `subfolder` (STRING), `sidecar_metadata` (`Both`, `JSON`, `TXT`, `None`), `prompt_text`, `negative_text`, `save_workflow` (BOOLEAN).
- **Outputs:** `images` (IMAGE pass-through), `file_path` (STRING), `filename` (STRING), `folder_path` (STRING), `metadata_json` (STRING).

### 13. `[STOIQO] Smart Seed & Variance Controller`
Deterministic seed manager with Krea 2 micro-variance control:
- **Control Lifecycle:** `randomize` (new seed every generation), `fixed` (reproducibility), `increment` (+1), `decrement` (-1).
- **Krea 2 Micro-Variance:** Secondary perturbation slider (`variance_strength` 0.0 to 1.0) and deterministic `variance_seed` to create controlled compositional variations without breaking character identity.
- **Inputs:** `seed` (INT), `control_mode` (`randomize`, `fixed`, `increment`, `decrement`), `variance_strength` (FLOAT), optional `variance_seed` (INT), `seed_prefix` (STRING).
- **Outputs:** `seed` (INT), `effective_seed` (INT), `variance_strength` (FLOAT), `seed_str` (STRING).

### 14. `[STOIQO] Pro Audio Saver & Metadata Hub`
Audio exporter dedicated to the YuE 2 / Suno production ecosystem:
- **Multi-Format Export:** Saves lossless `WAV (24-bit / 16-bit)`, `FLAC (Lossless)`, and `MP3 (320 kbps)`.
- **Dynamic Templating & Sidecars:** Automatically writes paired `.txt` lyrics and rich `.json` metadata sidecars capturing song title, BPM, acoustic style descriptors, key, duration, and file size.
- **Inputs:** `audio` (AUDIO), `filename_prefix` (STRING), `format`, optional `subfolder`, `title`, `lyrics`, `style`, `bpm`, `sidecar_metadata`.
- **Outputs:** `audio` (AUDIO pass-through), `file_path` (STRING), `filename` (STRING), `metadata_json` (STRING).

### 15. `[STOIQO] Pro Video Saver & Frame Exporter`
High-efficiency video container exporter with native audiovisual multiplexing:
- **Frame Batch Encoding:** Converts frame sequences into high-bitrate `MP4 (H.264)`, `WebM (VP9)`, or animated `GIF`.
- **Integrated Audio Muxing (FFmpeg):** Dedicated optional `audio` input pin. Automatically encodes audio to AAC (MP4) or Opus (WebM) at 320 kbps and muxes directly into the output video container with zero quality loss or sync drift.
- **Cinematic Framerates:** Configurable framerates (`24.0 fps` cinema standard, `30.0 fps`, `60.0 fps`) and bitrate quality controls.
- **Motion Metadata:** Saves paired `.txt` and `.json` sidecars containing camera kinematics and motion prompts.
- **Inputs:** `images` (IMAGE tensor batch `[B, H, W, C]`), `fps` (FLOAT), `filename_prefix`, `format`, `quality` (INT), optional `audio` (AUDIO), `subfolder`, `motion_prompt`, `sidecar_metadata`.
- **Outputs:** `images` (IMAGE pass-through), `file_path` (STRING), `filename` (STRING), `metadata_json` (STRING).

### 16. `[STOIQO] Inpaint Stitcher & Composite`
Closes the visual inpainting & upscaling loop with Krea 2 and SeedVR2:
- **Visual Re-Integration:** Consumes `bbox_info` emitted by `[STOIQO] Spatial Cropper & Mask Generator`, scales the edited/upscaled patch, and re-stitches it with sub-pixel alignment onto the original master image.
- **Seamless Feathering & Color Matching:** Configurable Gaussian edge feathering (`Normal`, `Soft Gradient`, `Sharp`) and optional histogram color profile transfer to eliminate seam artifacts.
- **Inputs:** `original_image` (IMAGE), `edited_image` (IMAGE), `bbox_info` (STRING), optional `blend_mode`, `feather_radius` (INT), `color_match` (BOOLEAN).
- **Outputs:** `composite_image` (IMAGE), `stitch_mask` (MASK).

### 17. `[STOIQO] Smart Watermark & Logo Stamp`
Replaces bloated 8-node math and overlay setups with a clean, single-node branding stamp:
- **Aspect Ratio & Corner Alignment:** Automatic placement across `Bottom-Right`, `Bottom-Left`, `Top-Right`, `Top-Left`, or `Center` with percentage-based border margins.
- **Smart Scaling:** Instant relative width scaling (`1/8 (Default)`, `1/10`, `1/6`, `1/4`, `1/3`) or custom ratios with strict aspect ratio preservation.
- **Instant Background Removal:** Integrated Chroma-key background suppression (`Auto Chroma (Corner)`, `Chroma Black`, `Chroma White`) and edge feathering.
- **Inputs:** `base_image` (IMAGE batch), `watermark_image` (IMAGE), `position`, `scale_mode`, `custom_scale` (FLOAT), `margin_percent` (FLOAT), `opacity` (FLOAT), `remove_bg_mode`, `chroma_tolerance` (FLOAT), optional `feather_radius` (INT), `optional_mask` (MASK).
- **Outputs:** `image` (IMAGE), `watermark_mask` (MASK), `overlay_info` (STRING JSON).

### 18. `[STOIQO] Tri-Model Loader Hub`
Consolidates modular UNET / DiT, CLIP, and VAE loading into a single clean node for modern architectures:
- **Unified Pipeline Emitting:** Loads UNET (with FP8 options), CLIP (with `krea2`, `flux`, `minimax`, `yue2`, `ace`, `sd3`, `lumina2`, `wan`, `ltxv`, `qwen_image` recipes), and VAE in one pass, outputting individual pins plus a consolidated `STOIQO_PIPE` dictionary.
- **Integrated Flow-Matching Presets:** Built-in automatic shifts for `Z-Image Turbo (Shift: 3.0)`, `Ace-Step 1.5 (Shift: 3.0)`, `Qwen-Image (Shift: 3.1)`, `FLUX.1 Schnell/Dev (Auto-Shift: 1.15)`, `SD3/SD3.5 (Shift: 3.0, Multi: 1000)`, `AuraFlow (Shift: 1.73)`, `MiniMax H3`, and `Custom`.
- **Multimodal Support:** Optional `clip_name2` for Dual-CLIP architectures and optional `audio_vae_name` for multimodal video/audio models.
- **VRAM Conservation:** Optional CPU offloading for CLIP text encoders on memory-constrained GPUs.
- **Inputs:** `unet_name`, `weight_dtype`, `clip_name`, `clip_type`, `vae_name`, `flow_shift_preset`, optional `clip_name2`, `audio_vae_name`, `pipe`, `clip_device`, `custom_shift`.
- **Outputs:** `model` (MODEL), `clip` (CLIP), `vae` (VAE), `audio_vae` (VAE), `stoiqo_pipe` (STOIQO_PIPE).

### 19. `[STOIQO] Turbo Sampler & Direct Decoder`
High-speed end-to-end generation tailored for lightning-fast models like Krea 2 Turbo, FLUX, and DiT architectures:
- **All-in-One Generation Pipeline:** In a single step, creates Empty Latents at target dimensions, tokenizes prompts, applies negative zero-out (eliminating CFG burns), executes KSampler (4-8 steps), and decodes directly via VAE.
- **Conditioning Bypass:** Dedicated optional `positive` and `negative` (`CONDITIONING`) inputs to accept pre-encoded conditioning directly from external CLIP encoders, LoRAs, or ControlNets without requiring text re-tokenization.
- **16-Channel DiT Latents:** Automatically detects and synthesizes 16-channel latents (FLUX, modern DiT) or 4-channel latents (SD1.5, SDXL, Krea 2).
- **Pipe & Pin Flexibility:** Works seamlessly via individual MODEL / CLIP / VAE wires or a single `STOIQO_PIPE` link from the Tri-Model Loader Hub.
- **Inputs:** `positive_prompt` (STRING), `seed` (INT), `steps` (INT), `cfg` (FLOAT), `sampler_name`, `scheduler`, `width` (INT), `height` (INT), `negative_mode`, `negative_prompt`, `denoise`, optional `positive` (CONDITIONING), `negative` (CONDITIONING), `model`, `clip`, `vae`, `stoiqo_pipe`, `latent_image`.
- **Outputs:** `image` (IMAGE decoded), `latent` (LATENT raw), `stoiqo_pipe` (STOIQO_PIPE enriched).

### 20. `[STOIQO] Modular Prompt Synthesizer Engine`
Ultra-lean, next-generation modular prompt engine:
- **Zero-Setup Tri-Output:** Automatically synthesizes high-fidelity `prompt` (for Krea 2 / Flux), concise `tags` (<75 tokens for CLIP), and surgical `negative` (detecting blurs and anatomical defects) with tuned factory defaults (`temp=0.6`, `top_p=0.9`, `1.0 MP`).
- **Live Token Streaming:** Real-time token streaming with live canvas typewriter effect via WebSocket integration.
- **Inputs:** `stoiqo_model` (STOIQO_MODEL), `user_directives` (STRING), optional `image` (IMAGE), `style_directives` (STOIQO_STYLE), `sampling_options` (STOIQO_SAMPLING), `multi_image_context` (STOIQO_CONTEXT), `character_context` (STOIQO_CHARACTER).
- **Outputs:** `prompt` (STRING), `tags` (STRING), `negative` (STRING), `raw_response` (STRING).

### 21. `[STOIQO] AI Persona & Style Directives`
Satellite node for artistic customization:
- **Centralized Style Directives:** Configures AI Personas, custom system instructions, structural output types (Categories, Prose, Booru, Cinematic Script), and artistic styles (Photorealistic, Anime, Cyberpunk, etc.).
- **Inputs:** `system_prompt`, `prompt_type`, `artistic_style`, optional `custom_system_prompt`.
- **Outputs:** `style_directives` (STOIQO_STYLE).

### 22. `[STOIQO] LLM Sampling & Precision`
Satellite node for fine-grained inference controls:
- **Hyperparameter Fine-Tuning:** Exposes `temperature`, `top_p`, `top_k`, `repetition_penalty`, `max_new_tokens`, `target_megapixel`, and deterministic `seed`.
- **Inputs:** `temperature` (FLOAT), `top_p` (FLOAT), `top_k` (INT), `repetition_penalty` (FLOAT), `max_new_tokens` (INT), `target_megapixel` (FLOAT), `seed` (INT).
- **Outputs:** `sampling_options` (STOIQO_SAMPLING).

### 23. `[STOIQO] Multi-Image Context Hub`
Satellite node for multimodal reasoning across multiple images:
- **Multimodal Context Fusion:** Bundles reference images (`<Image 1>`, `<Image 2>`, `<Image 3>`) with contextual fusion, comparative difference, or character consistency strategies.
- **Inputs:** `image_1` (IMAGE), `image_2` (IMAGE), `fusion_mode`, optional `image_3` (IMAGE).
- **Outputs:** `multi_image_context` (STOIQO_CONTEXT).

### 24. `[STOIQO] LoRA Stack Hub`
Dynamic multi-LoRA stacking and weighting hub:
- **Multi-LoRA Chaining:** Stacks up to 4 LoRAs with independent model and CLIP weights without canvas clutter.
- **JSON Stack Export:** Emits standard `LORA_STACK` compatible with downstream samplers and loaders.
- **Outputs:** `lora_stack` (LORA_STACK).

### 25. `[STOIQO] Character Memory Bank (Lorebook & DNA)`
Character consistency manager for multi-scene narrative generation:
- **Character DNA Injection:** Stores identity triggers, facial attributes, hairstyle, wardrobe, and lorebooks.
- **Injection Modes:** `Always Prepend (Force Character DNA)` or `Smart Detect (Inject only when Name or Trigger is in Prompt)`.
- **Outputs:** `character_context` (STOIQO_CHARACTER).

### 26. `[STOIQO] Temporal Video Deflicker`
Temporal luminance smoother for AI-generated video:
- **Flicker Reduction:** Eliminates lighting oscillations and micro-jitter between frames in generative video models (LTX-Video, MiniMax, Wan).
- **Inputs:** `images` (IMAGE video batch), `window_size` (INT), `blend_strength` (FLOAT).
- **Outputs:** `images` (IMAGE smoothed).

### 27. `[STOIQO] Video Frame Rate Multiplier (2x / 4x)`
High-performance frame interpolator:
- **Smooth Playback:** Multiplies frame rates (e.g. 24fps -> 48fps or 60fps) using bidirectional optical flow motion estimation.
- **Inputs:** `images` (IMAGE), `multiplier` (2x, 4x), `motion_sensitivity`.
- **Outputs:** `images` (IMAGE interpolated).

### 28. `[STOIQO] Depth Map & 3D Parallax Extractor`
Depth estimation and camera motion synthesizer:
- **3D Parallax Effect:** Generates monocular depth maps and creates cinematic 3D camera pan/dolly animations from a single still image.
- **Outputs:** `depth_map` (IMAGE), `parallax_frames` (IMAGE video batch).

### 29. `[STOIQO] Face Restoration & Portrait Hub`
Dual-engine facial restoration hub:
- **Portrait Recovery:** Integrates CodeFormer and GFPGAN algorithms with fidelity weighting and face-mask feathering.
- **Outputs:** `restored_image` (IMAGE).

### 30. `[STOIQO] Frequency Split (Texture & Color)`
High/Low frequency decomposition for professional skin retouching:
- **Wavelet Separation:** Splits image into high-frequency texture (pores, hair, fine lines) and low-frequency color/tone.
- **Outputs:** `low_frequency` (IMAGE), `high_frequency` (IMAGE).

### 31. `[STOIQO] Frequency Merge & Recomposite`
Recombines frequency layers after independent filtering:
- **Recomposite:** Merges retouched texture and color layers back into a single flawless image without losing micro-detail.
- **Outputs:** `merged_image` (IMAGE).

### 32. `[STOIQO] Spatial Re-Roll & Contextual Fill`
Targeted compositional regeneration:
- **Local Variator:** Allows regenerating specific quadrants or masked areas while preserving surrounding canvas context.
- **Outputs:** `image` (IMAGE).

### 33. `[STOIQO] Universal Context Pipe (In / Bus)`
Clean workflow bus packer:
- **Signal Packaging:** Consolidates MODEL, CLIP, VAE, LATENT, IMAGE, and PROMPT signals into a single unified wire.
- **Outputs:** `pipe` (STOIQO_PIPE).

### 34. `[STOIQO] Universal Context Pipe (Out / Unpack)`
Clean workflow bus unpacker:
- **Signal Extraction:** Unpacks individual MODEL, CLIP, VAE, LATENT, IMAGE, and PROMPT pins at destination nodes.
- **Outputs:** `model`, `clip`, `vae`, `latent`, `image`, `positive`, `negative`.

### 35. `[STOIQO] Webhook Notifier & Pipeline Exporter`
Automated webhook integration:
- **Event Dispatch:** Dispatches HTTP POST webhooks with generation status, elapsed time, output paths, and metadata upon pipeline completion.
- **Outputs:** `status` (STRING).

---

## 🚀 Production Workflows & Master Workbench

The suite powers 18 production workflows available in `workspace/workflows/` and mapped in `WORKFLOWS_CATALOG.md`:
- **Grand Master Workbench** (`stoiqo_master_all_in_one_workbench.json`): 13 production pipelines arranged on a single 2D grid with 13 LiteGraph groups and 116 nodes.
- **Master Showcase** (`examples/00_stoiqo_master_showcase.json`): Interactive reference canvas hosting all 35 custom nodes.

---

## License

Apache 2.0.

