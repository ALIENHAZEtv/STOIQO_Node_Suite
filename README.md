# STOIQO-Comfyui-Nodes

A production-ready ComfyUI custom node suite for **Visual Prompt Generation, Multimodal Comparison, and Creative Utilities** powered by Vision-Language Models (Qwen2.5-VL and compatible architectures).

The suite provides complete modularity across Prompt Generation, VLM caching, Forensic Visual Diff, Interactive Before/After Split Sliders, Text Concatenation, and VAE-Safe Image Resolution generation.

---

## Key Features

| Feature | Details |
|---|---|
| **Prompt Generator Engine** | Generates, refines, and directs prompts in a single model pass from images or raw text directives |
| **VLM Model Loader** | Dedicated resident VRAM cache node emitting `STOIQO_MODEL` pipe for zero-latency workflows |
| **Visual Compare Slider & Zoom** | Interactive split curtain with synchronized 10x pan/zoom on identical pixel coordinates |
| **Visual Diff & Forensic Inspector** | Multi-image comparative analysis with structured difference reports and change tags |
| **Text Concatenate & Clean** | Multi-block prompt joining with smart separator hygiene and prefix/suffix formatting |
| **Image Resolution & Aspect Ratio** | Generates VAE-safe divisible width & height dimensions across standard aspect ratios |
| **Unified Hardware Presets** | VRAM-tiered presets (3B, 7B, 32B, 72B) or custom models with native Windows Folder Browser |
| **Download Progress Tracker** | Live byte-level HuggingFace download tracking on ComfyUI's top progress bar and canvas badge |
| **AI Personas & Directives** | Built-in system prompt personas (Visual Prompt Synthesizer, Dataset Annotator, Literal Describer) + custom override |
| **Dual Prompt Splitter** | Simultaneous outputs for concise tags (<75 tokens) and extended descriptive prose paragraph |
| **Negative & Artifact Auditor** | Forensic visual inspection of defects (anatomy, lighting, artifacts) with dedicated `negative` output pin |
| **Collapsible LoRA Toolkit** | On-demand dataset suite: trigger word pinned at index 0, blacklist filtering, tag shuffling, and Kohya JSON manifests |
| **Smart Pre-Scaling** | Protects VRAM by automatically scaling images to ~1.0 Mpx (multiples of 28 for Qwen2.5-VL 2D-RoPE ViT) |
| **Music Prompt & Lyrics Engine (YuE2)** | Composes full rhyming lyrics and acoustic production descriptors directly mapped to YuE2/Suno with optional multimodal cover art |
| **Trio Image Loader & Hero Preview** | Loads 3 images simultaneously with clickable thumbnail gallery and large synchronized vertical hero preview |
| **Native Theme Independence** | Zero hardcoded node colors: fully respects ComfyUI canvas themes and custom node coloring |

---

## Installation

### Option A — ComfyUI Manager (recommended)
Search for `STOIQO Comfyui Nodes` in the ComfyUI Manager custom nodes browser and click **Install**.

### Option B — Manual
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/ALIENHAZEtv/STOIQO_ComfyUI_Nodes.git
cd STOIQO_ComfyUI_Nodes
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
| `📁 Custom Model (Local Disk Path)` | Custom | Custom | Any local folder with `config.json` |

---

## Node Structure & Parameters

### `[STOIQO] Prompt Generator Engine`

#### Multimodal Connection Pins (Optional Inputs)
- `image`: Primary image input. Connect a single image or a batch. Leave disconnected to run the node in Text-Only mode.
- `reference_image`: Second reference image for multi-image contextual fusion (`<Image 1>`, `<Image 2>`).
- `reference_image_2`: Third reference image for multi-angle, character consistency, or palette comparison.

#### § 1. ENGINE & HARDWARE
- `model_preset`: Unified model dropdown. Select a pre-quantized 4-bit preset or `📁 Custom Model (Local Disk Path)`.
- `local_model_path`: Appears dynamically when *Custom Model* is chosen. Use the built-in **📁 Browse Model Folder on Disk** button to open the native Windows Explorer folder picker, or type an absolute path.
- `quantization`: `4bit - NF4 (Recommended - Low VRAM)`, `8bit`, or `none (fp16 / bf16)`.
- `attention_mode`: `sdpa (PyTorch Native - Recommended)`, `flash_attention_2`, or `eager`.
- `target_megapixel`: Resolution budget in Megapixels (default `1.0` MP = ~1024x1024). Automatically scales images to exact multiples of 28 for ViT tokens while preserving aspect ratio.
- `unload_model_after`: Frees VRAM immediately after execution (recommended for Flux/SDXL workflows).

#### § 2. TASK & DIRECTIVES
- `batch_mode`:
  - `Independent Images`: Processes each image in a batch individually (ideal for LoRA dataset tagging).
  - `Multi-Image Comparison / Fusion`: Feeds multiple images simultaneously into the LLM (`<Image 1>`, `<Image 2>`) to compare differences or synthesize a single fused prompt.
- `system_prompt`: Core behavioral AI persona selector:
  - `Visual Prompt Synthesizer` *(Default)*
  - `Objective Dataset Annotator`
  - `Literal & Essential Describer`
  - `✏️ Custom (Manual Override)`
- `custom_system_prompt`: Multiline text box revealed dynamically only when *Custom (Manual Override)* is selected.
- `prompt_type`: Structural output format:
  - `Detailed Narrative (Long)` *(Default)*
  - `Short Summary (Concise)`
  - `Tags & Keywords`
  - `Structured Categories`
  - `Custom Directives Only`
- `artistic_style`: Visual aesthetic directive:
  - `Auto-Detect / Preserve Original` *(Default)*
  - `Photorealistic & Cinematic`
  - `Anime & Manga (2D / Cel-shaded)`
  - `3D Digital Render & CGI`
  - `Pencil Sketch & Traditional Ink`
  - `Digital Concept Art & Illustration`
  - `Oil Painting & Fine Art`
  - `Cyberpunk & Sci-Fi`
  - `Vintage Film (35mm Analog, Grain)`
- `user_directives`: Multiline directive box for natural-language instructions, camera angles, lighting, focus, or source text to refine/expand.

#### § 3. SAMPLING & GENERATION
- `seed`: Random seed for deterministic generation and LoRA tag shuffling.
- `temperature`: Creativity slider (`0.0` = greedy deterministic, `0.6` = balanced, `1.0+` = highly creative).
- `top_p`: Nucleus sampling cutoff (default `0.9`).
- `repetition_penalty`: Penalizes repetitive phrases and tag loops (default `1.1`).
- `max_new_tokens`: Maximum token budget for the generated prompt (default `512`).

#### § 4. DUAL PROMPT & ARTIFACT AUDIT
- `enable_dual_prompt`: Tailors simultaneous outputs into two specialized streams: concise tags (<75 tokens for short text/tag encoders) and expansive descriptive prose for long text encoders.
- `audit_artifacts`: Forensically analyzes the image for anatomical errors, rendering flaws, and lighting defects, outputting a surgical negative prompt.
- `negative_prompt_prefix`: Optional prefix prepended to the negative prompt (e.g. `worst quality, low quality, `).

#### § 5. DATASET & LORA TOOLKIT (On-Demand)
- `enable_lora_toolkit`: Master switch. When `False`, all LoRA widgets collapse to `0px` to keep the node compact. When `True`, reveals:
  - `trigger_word`: Activator keyword pinned at index 0 of every caption file (e.g. `sks_char, `).
  - `blacklist_tags`: Unwanted tags to strip (e.g. watermark, signature, blurry, lowres).
  - `shuffle_tags`: Shuffles non-trigger tags deterministically to prevent position bias in LoRA training.
  - `tag_separator`: `, `, `\n (Newline)`, or ` | `.
  - `save_txt`: Saves captions as `.txt` files matching image filenames.
  - `save_json_metadata`: Saves structured `.json` manifests compliant with Kohya_ss, SimpleTuner, and AI-Toolkit.
  - `output_dir`: Output folder (auto-anchored to ComfyUI output directory).
  - `use_original_filename`: Traces upstream through Reroutes up to 6 hops to detect the source image filename.
  - `fallback_prefix`: Fallback name when original filename cannot be traced.

---

## Outputs

- `caption`: **Final Descriptive Prompt / Caption** — The primary, complete prompt with all chosen parameters (rich narrative prose, standard caption, or full T5-XXL descriptive paragraph in dual mode). (STRING or list of STRING for batches).
- `tags`: **Concise Individual Tags (< 77 tokens)** — Clean, comma-separated individual words/tags strictly bounded under 77 tokens, optimal for CLIP ViT-L encoders, LoRA training, and tag-based conditioning. (STRING or list of STRING for batches).
- `negative`: **Surgical Negative Prompt** — Targeted flaw tokens and rendering defects detected during visual audit, prefixed with your custom negative prefix. (STRING or list of STRING for batches).

---

## Companion Nodes in Suite

### 1. `[STOIQO] VLM Model Loader`
Preloads and caches a Vision-Language Model in VRAM once, emitting a `stoiqo_model` pipe. Connecting this pipe to `[STOIQO] Prompt Generator Engine` or `[STOIQO] Visual Diff & Forensic Inspector` avoids redundant model re-initialization and allows chaining multiple tasks with zero VRAM re-allocation.

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

---

## License

Apache 2.0.
