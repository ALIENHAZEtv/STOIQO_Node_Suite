# STOIQO Node Suite (v2.0.0)

[![CI](https://github.com/ALIENHAZEtv/STOIQO_Node_Suite/actions/workflows/ci.yml/badge.svg)](https://github.com/ALIENHAZEtv/STOIQO_Node_Suite/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/downloads/)
[![ComfyUI-Manager](https://img.shields.io/badge/ComfyUI--Manager-Registered-purple.svg)](https://github.com/ltdrdata/ComfyUI-Manager)
[![Nodes: 21 Sovereign](https://img.shields.io/badge/Nodes-21%20Sovereign-emerald.svg)](#the-21-sovereign-nodes)
[![Tests: 151 Passing](https://img.shields.io/badge/Tests-151%20Passing-brightgreen.svg)](#-validation--test-suite)

Production-ready, unified ComfyUI custom node suite for **Visual & Multimodal Prompt Generation, DiT Model Routing, High-Precision Forensics, Music Composition, Video Stabilization, and Lossless Metadata-Embedded Media Export**.

Streamlined from early experimental prototypes into **21 hardened sovereign nodes**, the suite delivers professional performance across 6 architectural domains with zero third-party UI friction and 100% strict English-only UI standards.

---

## 🏛️ Key Architectural Features (v2.0)

| Capability | Engineering Highlights |
|---|---|
| **3-Layer Modular Prompt Engine** | Structured hierarchy decoupling Cognitive AI Persona (Layer 1), Structural Format (Layer 2), Aesthetic Style (Layer 3), and Director Modifications for surgical ideation control. |
| **Drop-in File Extensibility** | Add custom personas, styles, or output formats on the fly simply by dropping Markdown files with YAML frontmatter into `core/image/` directories. Zero Python/JS code edits needed. |
| **Progressive Disclosure (`⚙` Drawer)** | Keeps canvas nodes clean and compact. Advanced sampling parameters, multimodal fusion modes, and seed companion controls are tucked behind an interactive drawer with dynamic height adjustment. |
| **The 21 Sovereign Architecture** | Replaces fragmented legacy nodes with 21 focused, high-throughput modules covering diffusion, VLM, audio, video, and forensics. |
| **Sovereign Metadata Embedding** | Default `sidecar_metadata: "None"`. Full ComfyUI workflow JSON, seeds, prompts, and model hashes are embedded losslessly into PNG chunks, MP4 containers, or MP3 ID3 tags without polluting disk with `.txt` and `.json` sidecars. |
| **Frontend Auto-Healing Sanitizer** | Integrated `sanitizeNodeWidgetValues` and `beforeQueue` interceptor that auto-repairs corrupted browser states (e.g. invalid subfolders or shifted combos) before validation. |
| **Universal Flow-Matching Shift** | Dynamic DiT calibration in `Universal Model Loader` with automatic shift presets for Krea 2.0 Turbo, FLUX.1, Z-Image Turbo, Ace-Step 1.5, and SD3.5. |
| **Live WebSocket Token Streaming** | Real-time typewriter token streaming on the canvas via `TextIteratorStreamer` with direct user abort handling. |
| **Interactive Visual Forensics** | Split-slider curtain with synchronized 1:1 pan & zoom, scientific false-color thermal heatmaps (Turbo, Inferno, Jet), binary change masks, and SSIM/PSNR calculation in pure PyTorch. |
| **Seamless Backward Compatibility** | Built-in legacy alias mapping (`StoiqoVisualDiffNode`, `StoiqoTemporalDeflickerNode`, `StoiqoTripleImageLoaderNode`, `StoiqoResolutionNode`) guaranteeing zero breaking changes on older saved workflows. |
| **Monolith Minimalist Dark Theme** | Strict adherence to the Monolith Minimalist Dark system (`#0c0d11`, Titanium Slate, Precision Blue, Status Emerald, Amber, and Crimson Red). Zero unstyled cyberpunk neon. |

---

## 🎛️ The 3-Layer Modular Prompt Engine

The flagship **`[STOIQO] Prompt Generator`** (`StoiqoPromptGeneratorNode`) features a clean face with 3 stacked dropdowns and a director modification text area:

```
+-------------------------------------------------------------+
|                [STOIQO] Prompt Generator                    |
+-------------------------------------------------------------+
|  system_prompt   [ Layer 1: Cognitive AI Persona         ▼ ]|
|  prompt_type     [ Layer 2: Structural Output Format     ▼ ]|
|  prompt_style    [ Layer 3: Aesthetic Visual Medium      ▼ ]|
+-------------------------------------------------------------+
|  custom_modifications:                                      |
|  "Director instructions, lighting adjustments, mood shifts" |
+-------------------------------------------------------------+
|  ⚙ Advanced Settings & Sampling                  Show (10) ▾|
+-------------------------------------------------------------+
|  ● SINGLE IMAGE VISION   Structured Categories • ... ● LINKED|
+-------------------------------------------------------------+
```

### 1. Layer 1: Cognitive AI Persona (`system_prompt`)
Guides the fundamental perception protocol and model sampling profile:
* `Auto-Detect / Balanced`: Context-aware perception router based on connected inputs.
* `Generative Vision Engine`: High-fidelity single-image scene deconstruction.
* `Text-to-Prompt Expansion Engine`: Expands short user phrases into rich photographic prompts.
* `Multi-Image Synthesis Engine`: Cross-referential visual reasoning across batches.
* `Cinematic & Video Director`: Scene pacing, anamorphic lighting, and spatial camera choreography.
* `Dataset & LoRA Annotator`: Factual tagging and captioning with zero hallucinations.
* `Minimalist & Literal`: Concise, direct, and unbloated descriptive prompt.
* `SeedVR2 Upscale Guide`: Precision prompts for hi-res diffusion enhancement.
* `Custom (Manual Override)`: Full custom instructions via `custom_system_prompt`.

### 2. Layer 2: Structural Output Format (`prompt_type`)
Enforces strict syntactic framing on the generated prompt:
* `Detailed Narrative`: Fluid prose with camera, subject, atmosphere, and render details.
* `Structured Categories`: Distinct headers (`Subject`, `Environment`, `Lighting`, `Style`).
* `Short Summary`: Punchy 1-2 sentence core visual description.
* `Tags & Keywords`: Comma-separated weighted concept tags.
* `Booru Tags (Danbooru)`: Standardized anime/illustration tag list with rating tokens.
* `Cinematic & Video Script`: Shot-by-shot cinematic framing and temporal action beats.

### 3. Layer 3: Aesthetic Style & Visual Medium (`prompt_style`)
Injects lighting setups, medium signatures, and chromatic rendering:
* `Auto-Detect / Preserve Original`: Preserves input reference medium without override.
* `Photorealistic (Modern Digital RAW)`: Hasselblad/Sony sensor, natural micro-contrast.
* `Analog Film (35mm Vintage Stock)`: Kodak Portra / Cinestill 800T, organic grain and halation.
* `Cinematic Still (Anamorphic Movie)`: Panavision lenses, cinematic color grading, letterbox.
* `Studio Portrait & Editorial Fashion`: Profoto softboxes, rembrandt lighting, editorial skin.
* `Anime & Manga (2D Cel-shaded)`: Hand-drawn lineart, vibrant cel shading, anime aesthetic.
* `Comic Book & Graphic Novel`: Dark ink linework, halftone dot patterns, dynamic ink wash.
* `Pencil Sketch & Charcoal Drawing`: Cross-hatching graphite, smudged charcoal, textured paper.
* `3D Digital Render & CGI (PBR)`: Octane / Unreal Engine 5, raytraced reflections and subsurface scattering.
* `Digital Concept Art & Illustration`: Speedpaint brushes, matte painting, dynamic keys.
* `Oil Painting & Classical Fine Art`: Thick impasto brushwork, chiaroscuro, cracked canvas patina.

---

## 📁 Drop-in File Extensibility (`core/image/`)

Adding new personas, formats, or styles requires **zero code modifications**. Simply add a `.md` Markdown file with YAML frontmatter in the corresponding directory:

```
core/image/
├── personas/      # Cognitive persona prompts (.md)
├── types/         # Structural format templates (.md)
└── styles/        # Artistic style definitions (.md)
```

### Example: Adding a New Style (`core/image/styles/cyberpunk_noir.md`)
```markdown
---
name: "Cyberpunk Noir (Rain & Neon)"
description: "Dystopian rain-slicked streetscapes with neon reflections and heavy shadows."
aliases:
  - "cyberpunk"
  - "neon noir"
---
Cyberpunk noir visual style, drenched in pouring rain, reflective wet asphalt pavements, glowing neon signs in vivid cyan and magenta, atmospheric steam rising from street grates, high-contrast chiaroscuro shadows, anamorphic lens flares, dystopian architectural backdrop.
```
Upon restart, `Cyberpunk Noir (Rain & Neon)` automatically populates in the `prompt_style` dropdown!

---

## 🧩 The 21 Sovereign Nodes

The suite is systematically partitioned into **6 functional zones**:

### Zone 1: Pipeline Core & Generative Engines
* **`[STOIQO] Universal Model Loader (All-in-One)`** (`StoiqoUniversalModelLoaderNode`): Loads DiT, UNet, CLIP, Text Encoders, and VAE with configurable quantization (fp8, 4-bit NF4) and automated Flow Matching Shift calibration.
* **`[STOIQO] LoRA Stack`** (`StoiqoLoraStackNode`): Chains up to 4 concurrent LoRAs with zero-overhead transparent bypass switching and metadata inspection.
* **`[STOIQO] Seed & Resolution Controller`** (`StoiqoSeedControllerNode`): Advanced seed management, sub-seed variance exploration, and resolution quantization onto VAE-safe grids ($64\text{px}$ / $16\text{px}$).
* **`[STOIQO] Turbo Sampler & Direct Decoder`** (`StoiqoTurboSamplerNode`): High-throughput unified sampler (optimized for 8-step generation) with direct Float32 VAE decoding.

### Zone 2: Prompting, Vision-Language & Identity
* **`[STOIQO] Prompt Generator`** (`StoiqoPromptGeneratorNode`): Multimodal engine for prompt synthesis and enhancement from raw concepts or reference images, powered by Qwen-VL and VLM architectures.
* **`[STOIQO] Character Memory Bank (Lorebook & DNA)`** (`StoiqoCharacterMemoryNode`): Persists character profiles, aesthetic visual DNA, trigger tags, and negative constraints with dynamic prompt injection.
* **`[STOIQO] Text Concatenate & Clean`** (`StoiqoTextConcatenateNode`): Multi-segment string joiner with automated tag deduplication, whitespace normalization, and prefix/suffix formatting.
* **`[STOIQO] Show Prompt`** (`StoiqoShowPromptNode`): Interactive full-canvas viewer to monitor expanded prompts, character counts, and token estimates in real time.

### Zone 3: Image Retouching, Inpainting & Forensics
* **`[STOIQO] Image Loader (Multi-Slot)`** (`StoiqoImageLoaderNode`): Simultaneous loading of up to 3 reference images with synchronized previewing and aspect-ratio conforming.
* **`[STOIQO] Visual Compare Slider & Zoom`** (`StoiqoImageCompareNode`): Interactive split-slider before/after curtain, synchronized 1:1 pan & zoom, differential thermal heatmaps (Turbo, Inferno, Jet), and pixel delta masks.
* **`[STOIQO] Spatial Cropper & Mask Generator`** (`StoiqoSpatialCropperNode`): Semantic prompt-guided cropping with normalized bounding-box computation and an Impact-Pack `SEGS` compatible bridge.
* **`[STOIQO] Inpaint Stitcher & Spatial Re-Roll`** (`StoiqoInpaintStitcherNode`): Seam-free reassembly with exponential/Gaussian edge blending and color matching for surgical inpainting.
* **`[STOIQO] Frequency Separation & Texture Hub`** (`StoiqoFrequencySeparationNode`): Dual-band decomposition into low frequencies (color/lighting) and high frequencies (micro-texture) for high-end beauty retouching.
* **`[STOIQO] Smart Watermark & Logo Stamp`** (`StoiqoWatermarkNode`): Watermark and logo stamping with boundary positioning, opacity control, and chroma-key background removal.

### Zone 4: Audio & Music Production
* **`[STOIQO] Music Prompt & Lyrics Engine (YuE2)`** (`StoiqoMusicPromptEngineNode`): AI songwriting assistant structuring track sections (Intro, Verse, Chorus, Outro), BPM, key, and lyrics for Ace-Step 1.5 and YuE2 models.
* **`[STOIQO] Pro Audio Saver & Metadata Hub`** (`StoiqoAudioSaverNode`): High-quality 320 kbps MP3 and master WAV exporter with embedded ID3 tags (title, BPM, lyrics, genre) and zero disk sidecar clutter.

### Zone 5: Video & Motion Processing
* **`[STOIQO] Video Deflicker & Frame Interpolator`** (`StoiqoVideoEnhancerNode`): Temporal filter eliminating luminance strobing (deflickering) and frame rate multiplier (2x/4x) for AI video engines (LTX-Video, Wan, Hunyuan).
* **`[STOIQO] Pro Video Saver & Frame Exporter`** (`StoiqoVideoSaverNode`): MP4 video compiler (H.264 / ProRes) with native FFmpeg audio muxing and embedded generation metadata.

### Zone 6: Dataset, Training & Pro Export
* **`[STOIQO] Smart Folder Image Iterator`** (`StoiqoSmartFolderImageIterator`): Dataset iterator with natural alphanumeric sorting, recursive folder discovery, and automated skipping of already captioned images (`skip_captioned`).
* **`[STOIQO] Dataset & LoRA Toolkit`** (`StoiqoDatasetWriterNode`): Manifest and pairing generator for LoRA fine-tuning (Kohya / AI-Toolkit) with tag blacklisting and trigger word enforcement.
* **`[STOIQO] Pro Image Saver & Metadata Hub`** (`StoiqoProImageSaverNode`): Ultra-fast image saving hub in lossless PNG, WEBP, or JPEG with embedded full workflow JSON for total reproducibility.

---

## 📦 Installation

### Method 1: ComfyUI Manager (Recommended)
1. Open **ComfyUI Manager** within your ComfyUI interface.
2. Search for `STOIQO Node Suite` in the catalog.
3. Click **Install** and restart ComfyUI.

### Method 2: Manual Git Installation
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/ALIENHAZEtv/STOIQO_Node_Suite.git
cd STOIQO_Node_Suite
pip install -r requirements.txt
```
Restart ComfyUI. All 21 sovereign nodes will appear under the `STOIQO` category.

---

## 🎨 Included Example Workflows (`examples/`)

The [`examples/`](file:///y:/Project_ExCathedra/SideProject/ComfyUI_CustomNodes/STOIQO_Node_Suite/examples) directory provides ready-to-run templates:

1. **`00_stoiqo_master_showcase.json`**: Pure visual showroom of all 21 sovereign nodes organized by category with zero links.
2. **`01_prompt_synthesis_live_streaming.json`**: Prompt synthesis with real-time typewriter token streaming on canvas.
3. **`02_turbo_sampler_krea2_pipeline.json`**: Complete 8-step Text-to-Image pipeline with Krea 2.0 Turbo and direct Float32 VAE decode.
4. **`03_spatial_grounding_impact_pack_segs.json`**: Semantic segmentation and bridge into Impact-Pack detailers.
5. **`04_music_production_yue2_audio.json`**: Complete end-to-end music generation pipeline with Ace-Step 1.5 and YuE2.

---

## 🧪 Validation & Test Suite

The suite is hardened with a comprehensive test suite validating tensor geometry, HTTP/WebSocket endpoints, widget sanitization, and YAML schema compliance:

```bash
pytest tests/ -v
```
*Current status: **151 passed**, 1 skipped (0 failures).*

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](file:///y:/Project_ExCathedra/SideProject/ComfyUI_CustomNodes/STOIQO_Node_Suite/LICENSE) for complete terms.
