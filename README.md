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
* **`[STOIQO] Universal Model Loader (All-in-One)`** (`StoiqoUniversalModelLoaderNode`): Carica DiT, UNet, CLIP, Text Encoders e VAE con quantizzazione configurabile (fp8, 4-bit NF4) e calibrazione automatica del Flow Matching Shift.
* **`[STOIQO] LoRA Stack`** (`StoiqoLoraStackNode`): Chaining fino a 4 LoRA contemporanee con selettore di bypass trasparente a costo zero computazionale.
* **`[STOIQO] Seed & Resolution Controller`** (`StoiqoSeedControllerNode`): Gestione avanzata del seed, varianza con sub-seed e quantizzazione delle risoluzioni su griglie VAE-safe ($64\text{px}$ / $16\text{px}$).
* **`[STOIQO] Turbo Sampler & Direct Decoder`** (`StoiqoTurboSamplerNode`): Campionatore unificato ad altissima velocità (ottimizzato per 8 step) con decodifica VAE diretta a Float32.

### Zone 2: Prompting, Vision-Language & Identity
* **`[STOIQO] Prompt Generator`** (`StoiqoPromptGeneratorNode`): Motore multimodale per sintesi e arricchimento di prompt testuali o da immagini di riferimento basato su architetture Qwen-VL e VLM.
* **`[STOIQO] Character Memory Bank (Lorebook & DNA)`** (`StoiqoCharacterMemoryNode`): Conserva profili persistenti di personaggi, DNA estetico, trigger tag e vincoli negativi con iniezione dinamica nel prompt.
* **`[STOIQO] Text Concatenate & Clean`** (`StoiqoTextConcatenateNode`): Unione multi-blocco con deduplicazione automatica dei tag, rimozione whitespace e formattazione prefisso/suffisso.
* **`[STOIQO] Show Prompt`** (`StoiqoShowPromptNode`): Visualizzatore interattivo a tutto schermo sul canvas per monitorare l'espansione del prompt finale.

### Zone 3: Image Retouching, Inpainting & Forensics
* **`[STOIQO] Image Loader (Multi-Slot)`** (`StoiqoImageLoaderNode`): Caricamento simultaneo di fino a 3 immagini di riferimento con anteprima sincronizzata.
* **`[STOIQO] Visual Compare Slider & Zoom`** (`StoiqoImageCompareNode`): Cursore split-slider interattivo prima/dopo, zoom sincronizzato 1:1, heatmap termica differenziale e maschere di cambio pixel.
* **`[STOIQO] Spatial Cropper & Mask Generator`** (`StoiqoSpatialCropperNode`): Ritaglio semantico guidato da prompt con calcolo delle coordinate normalizzate e bridge compatibile con Impact-Pack `SEGS`.
* **`[STOIQO] Inpaint Stitcher & Spatial Re-Roll`** (`StoiqoInpaintStitcherNode`): Riassemblaggio seam-free con blend esponenziale/gaussiano e correzione colore per inpainting chirurgico.
* **`[STOIQO] Frequency Separation & Texture Hub`** (`StoiqoFrequencySeparationNode`): Scomposizione in frequenze basse (colore/illuminazione) e alte (micro-texture) per ritocco avanzato.
* **`[STOIQO] Smart Watermark & Logo Stamp`** (`StoiqoWatermarkNode`): Applicazione di watermark e loghi con posizionamento perimetrale, trasparenza e chroma-key rimozione sfondo.

### Zone 4: Audio & Music Production
* **`[STOIQO] Music Prompt & Lyrics Engine (YuE2)`** (`StoiqoMusicPromptEngineNode`): Assistente compositivo AI per la strutturazione di brani (Intro, Verse, Chorus, Outro), BPM, tonalità e liriche per modelli Ace-Step e YuE2.
* **`[STOIQO] Pro Audio Saver & Metadata Hub`** (`StoiqoAudioSaverNode`): Esportatore MP3 a 320 kbps e WAV master con tag ID3 incorporati (titolo, BPM, liriche, genere) senza file collaterali su disco.

### Zone 5: Video & Motion Processing
* **`[STOIQO] Video Deflicker & Frame Interpolator`** (`StoiqoVideoEnhancerNode`): Filtro temporale per eliminare tremolii di luminanza (deflickering) e moltiplicatore FPS (2x/4x) per video AI (LTX-Video, Wan, Hunyuan).
* **`[STOIQO] Pro Video Saver & Frame Exporter`** (`StoiqoVideoSaverNode`): Compilatore video MP4 (H.264 / ProRes) con audio muxing nativo tramite FFmpeg e metadati di generazione integrati.

### Zone 6: Dataset, Training & Pro Export
* **`[STOIQO] Smart Folder Image Iterator`** (`StoiqoSmartFolderImageIterator`): Iteratore per dataset con ordinamento naturale, scoperta ricorsiva e skip automatico delle immagini già taggate (`skip_captioned`).
* **`[STOIQO] Dataset & LoRA Toolkit`** (`StoiqoDatasetWriterNode`): Scrittura di manifesti per addestramento LoRA (Kohya / AI-Toolkit) con blacklist di tag e gestione trigger word.
* **`[STOIQO] Pro Image Saver & Metadata Hub`** (`StoiqoProImageSaverNode`): Hub di salvataggio immagini ad altissima velocità in PNG lossless, WEBP o JPEG con embedding completo del workflow per riproducibilità totale.

---

## 📦 Installazione

### Metodo 1: ComfyUI Manager (Consigliato)
1. Apri **ComfyUI Manager** all'interno della tua installazione ComfyUI.
2. Cerca `STOIQO Comfyui Nodes` nel catalogo.
3. Clicca **Install** e riavvia ComfyUI.

### Metodo 2: Installazione Manuale Git
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/ALIENHAZEtv/STOIQO_Node_Suite.git
cd STOIQO_Node_Suite
pip install -r requirements.txt
```
Riavvia ComfyUI. Tutti i 21 nodi saranno disponibili nella categoria `STOIQO`.

---

## 🎨 Workflow Esempi Inclusi (`examples/`)

La directory [`examples/`](file:///y:/Project_ExCathedra/SideProject/ComfyUI_CustomNodes/STOIQO_Node_Suite/examples) fornisce template pronti all'uso:

1. **`00_stoiqo_master_showcase.json`**: Il visual showroom puro dei 21 nodi organizzati per categoria con zero cavi di collegamento.
2. **`01_prompt_synthesis_live_streaming.json`**: Sintesi di prompt con streaming live dei token sul canvas.
3. **`02_turbo_sampler_krea2_pipeline.json`**: Pipeline completa Text-to-Image in 8 step con Krea 2.0 Turbo e VAE decode integrato.
4. **`03_spatial_grounding_impact_pack_segs.json`**: Segmentazione semantica e ponte verso Impact-Pack detailer.
5. **`04_music_production_yue2_audio.json`**: Pipeline completa di generazione musicale con Ace-Step 1.5 e YuE2.

---

## 🧪 Validazione & Test Suite

La suite è coperta da test unitari rigorosi che convalidano le strutture tensoriali, le rotte HTTP/WebSocket e la sanitizzazione:

```bash
pytest tests/ -v
```
*Esito corrente: **150 passati**, 1 saltato.*

---

## 📄 Licenza

Distribuito sotto licenza **MIT**. Consulta il file [`LICENSE`](file:///y:/Project_ExCathedra/SideProject/ComfyUI_CustomNodes/STOIQO_Node_Suite/LICENSE) per i termini completi.
