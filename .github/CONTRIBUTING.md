# Contributing to STOIQO Node Suite

Thank you for your interest in contributing to **STOIQO Node Suite**! This document provides technical guidelines and development standards for maintaining and extending the suite.

---

## 🏛️ Architecture Overview: The 21 Sovereign Nodes

STOIQO Node Suite is strictly partitioned into **21 Sovereign Nodes** distributed across 6 functional zones:

1. **Pipeline Core & Generative Engines**: `StoiqoUniversalModelLoaderNode`, `StoiqoLoraStackNode`, `StoiqoSeedControllerNode`, `StoiqoTurboSamplerNode`
2. **Prompting, Vision-Language & Identity**: `StoiqoPromptGeneratorNode`, `StoiqoCharacterMemoryNode`, `StoiqoTextConcatenateNode`, `StoiqoShowPromptNode`
3. **Image Retouching, Inpainting & Forensics**: `StoiqoImageLoaderNode`, `StoiqoImageCompareNode`, `StoiqoSpatialCropperNode`, `StoiqoInpaintStitcherNode`, `StoiqoFrequencySeparationNode`, `StoiqoWatermarkNode`
4. **Audio & Music Production**: `StoiqoMusicPromptEngineNode`, `StoiqoAudioSaverNode`
5. **Video & Motion Processing**: `StoiqoVideoEnhancerNode`, `StoiqoVideoSaverNode`
6. **Dataset, Training & Pro Export**: `StoiqoSmartFolderImageIterator`, `StoiqoDatasetWriterNode`, `StoiqoProImageSaverNode`

### Core Invariants
* **Sovereign Media Export**: Savers (`ProImageSaver`, `AudioSaver`, `VideoSaver`) must default to `sidecar_metadata: "None"`. Full generation metadata and ComfyUI workflow JSON must be embedded losslessly into media containers (PNG chunks, MP4 containers, MP3 ID3 tags) without polluting the user's filesystem with `.txt` or `.json` files.
* **Backward Compatibility**: Never break existing workflow files. If a node class is refactored, register a legacy alias in `nodes/__init__.py` using `_LEGACY_ALIASES`.
* **Zero UI Divider Bloat**: Follow the Monolith Minimalist Dark design system (`#0c0d11`, Titanium Slate, Precision Blue, Status Emerald, Amber, Crimson Red). Avoid neon accents, fluorescent gradients, or unstyled dividers.

---

## 🛠️ Development Setup

### Prerequisites
* **Python**: 3.10 or higher
* **Node.js**: 20.x LTS or higher
* **npm**: 10.x or higher
* **PyTorch**: 2.2.0+ with CUDA (or CPU for testing)
* **ComfyUI**: Latest master release

### Clone and Install
```bash
# Clone the repository into ComfyUI custom_nodes
cd ComfyUI/custom_nodes
git clone https://github.com/ALIENHAZEtv/STOIQO_Node_Suite.git
cd STOIQO_Node_Suite

# Install Python requirements
pip install -r requirements.txt
pip install pytest

# Install Node.js dev dependencies (for esbuild)
npm install
```

---

## 💻 Frontend Development (`src_js/`)

The frontend is written in modular JavaScript/TypeScript in `src_js/` and bundled into `js/stoiqo_suite.js` via `esbuild`.

### Rules
1. **Never edit `js/stoiqo_suite.js` directly**: Changes must be made in `src_js/` and built using `npm run build`.
2. **Watch Mode**: During active development, run:
   ```bash
   npm run watch
   ```
3. **Bundle Check**: Before committing, verify that the compiled bundle is perfectly in sync with the source:
   ```bash
   npm run check:bundle
   ```

---

## 🧪 Testing (`tests/`)

Every contribution must pass the test suite:
```bash
pytest tests/ -v
```

When adding new nodes or fixing parameters:
* Add corresponding unit tests in `tests/test_nodes_schema.py` or `tests/test_utility_nodes.py`.
* Ensure tensor shapes, VLM fallback handlers, and widget sanitizers are verified.

---

## 📝 Commit Conventions

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

* `feat(...)`: A new feature or capability
* `fix(...)`: A bug fix or parameter stabilization
* `docs(...)`: Documentation updates
* `style(...)`: Formatting or UI visual refinements
* `refactor(...)`: Code refactoring without behavior changes
* `test(...)`: Adding or updating tests
* `chore(...)`: Maintenance tasks, dependency updates

Example:
```bash
git commit -m "fix(watermark): guard against near-invisible opacity and clamp shifted widgets"
```

---

## 🚀 Submitting a Pull Request

1. Create a topic branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes in `nodes/`, `core/`, or `src_js/`.
3. If frontend files were modified, run `npm run build` and `npm run check:bundle`.
4. Run tests: `pytest tests/ -v`.
5. Push to your fork and submit a Pull Request describing:
   * The problem being solved.
   * The architectural solution implemented.
   * Testing steps performed.
