# STOIQO Node Suite (v2.0.0)

[![CI](https://github.com/ALIENHAZEtv/STOIQO_Node_Suite/actions/workflows/ci.yml/badge.svg)](https://github.com/ALIENHAZEtv/STOIQO_Node_Suite/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/downloads/)
[![ComfyUI-Manager](https://img.shields.io/badge/ComfyUI--Manager-Registered-purple.svg)](https://github.com/ltdrdata/ComfyUI-Manager)
[![Nodes: 21 Sovereign](https://img.shields.io/badge/Nodes-21%20Sovereign-emerald.svg)](#the-21-sovereign-nodes)

Production-ready, unified ComfyUI custom node suite for **Visual & Multimodal Prompt Generation, DiT Model Routing, High-Precision Forensics, Music Composition, Video Stabilization, and Lossless Metadata-Embedded Media Export**.

Streamlined from early experimental prototypes into **21 hardened sovereign nodes**, the suite delivers professional performance across 6 architectural domains with zero third-party UI friction.

---

## 🏛️ Key Architectural Features (v2.0)

| Capability | Engineering Highlights |
|---|---|
| **The 21 Sovereign Architecture** | Replaces fragmented legacy nodes with 21 focused, high-throughput modules covering diffusion, VLM, audio, video, and forensics. |
| **Sovereign Metadata Embedding** | Default `sidecar_metadata: "None"`. Full ComfyUI workflow JSON, seeds, prompts, and model hashes are embedded losslessly into PNG chunks, MP4 containers, or MP3 ID3 tags without polluting disk with `.txt` and `.json` sidecars. |
| **Frontend Auto-Healing Sanitizer** | Integrated `sanitizeNodeWidgetValues` and `beforeQueue` interceptor that auto-repairs corrupted browser states (e.g. invalid subfolders or shifted combos) before validation. |
| **Universal Flow-Matching Shift** | Dynamic DiT calibration in `Universal Model Loader` with automatic shift presets for Krea 2.0 Turbo, FLUX.1, Z-Image Turbo, Ace-Step 1.5, and SD3.5. |
| **Live WebSocket Token Streaming** | Real-time typewriter token streaming on the canvas via `TextIteratorStreamer` with direct user abort handling. |
| **Interactive Visual Forensics** | Split-slider curtain with synchronized 1:1 pan & zoom, scientific false-color thermal heatmaps (Turbo, Inferno, Jet), binary change masks, and SSIM/PSNR calculation in pure PyTorch. |
| **Seamless Backward Compatibility** | Built-in legacy alias mapping (`StoiqoVisualDiffNode`, `StoiqoTemporalDeflickerNode`, `StoiqoTripleImageLoaderNode`, `StoiqoResolutionNode`) guaranteeing zero breaking changes on older saved workflows. |
| **Native Dark Theme Integration** | Strict adherence to the Monolith Minimalist Dark system (`#0c0d11`, Titanium Slate, Precision Blue, Status Emerald, Amber, and Crimson Red). Zero unstyled cyberpunk neon. |

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

The suite is hardened with a comprehensive test suite validating tensor geometry, HTTP/WebSocket endpoints, and widget sanitization:

```bash
pytest tests/ -v
```
*Current status: **150 passed**, 1 skipped.*

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](file:///y:/Project_ExCathedra/SideProject/ComfyUI_CustomNodes/STOIQO_Node_Suite/LICENSE) for complete terms.
