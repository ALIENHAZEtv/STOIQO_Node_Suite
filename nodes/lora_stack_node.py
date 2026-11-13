"""
[STOIQO] LoRA Stack Node
Dynamic LoRA stacker: click "+ Add LoRA" on the canvas to append as many LoRAs as needed,
toggle each one on/off individually and tune its strength. Applies the active LoRAs to the
incoming MODEL (and optional CLIP) in order.

The canvas UI (src_js/nodes/loraStackNode.js) persists its state as JSON inside the hidden
`lora_stack` STRING widget:
    [{"name": "style/foo.safetensors", "strength": 1.0, "strength_clip": 1.0, "enabled": true}, ...]
"""

import json
import os

try:
    import folder_paths
except ImportError:
    class _MockFolderPaths:
        @staticmethod
        def get_filename_list(folder):
            return []

        @staticmethod
        def get_full_path(folder, filename):
            return None

    folder_paths = _MockFolderPaths()

try:
    import comfy.sd
    import comfy.utils
except ImportError:
    comfy = None


def extract_lora_trigger_words(lora_path: str) -> list:
    """
    Fast extraction of trained trigger words from safetensors header or sidecar files.
    Checks:
    1. Sidecar .civitai.info (JSON -> trainedWords)
    2. Sidecar .txt (comma-separated tags)
    3. Safetensors header metadata (modelspec.trigger_phrase, ss_tag_frequency)
    Zero tensor weights loaded; executes in sub-millisecond.
    """
    if not lora_path or not os.path.isfile(lora_path):
        return []

    triggers = []
    base, _ = os.path.splitext(lora_path)

    # 1. Sidecar .civitai.info
    info_path = base + ".civitai.info"
    if os.path.isfile(info_path):
        try:
            with open(info_path, "r", encoding="utf-8") as f:
                cdata = json.load(f)
                tw = cdata.get("trainedWords")
                if isinstance(tw, list):
                    for w in tw:
                        if isinstance(w, str) and w.strip():
                            triggers.append(w.strip())
        except Exception:
            pass

    # 2. Sidecar .txt
    if not triggers:
        txt_path = base + ".txt"
        if os.path.isfile(txt_path):
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        parts = [p.strip() for p in content.split(",") if p.strip()]
                        triggers.extend(parts[:10])
            except Exception:
                pass

    # 3. Safetensors header metadata
    if not triggers and lora_path.endswith(".safetensors"):
        try:
            import safetensors
            with safetensors.safe_open(lora_path, framework="pt") as f:
                meta = f.metadata()
                if meta:
                    tp = meta.get("modelspec.trigger_phrase")
                    if tp:
                        triggers.extend([t.strip() for t in tp.split(",") if t.strip()])
                    if not triggers and "ss_tag_frequency" in meta:
                        try:
                            tag_freq = json.loads(meta["ss_tag_frequency"])
                            all_tags = {}
                            for _, dir_tags in tag_freq.items():
                                if isinstance(dir_tags, dict):
                                    for t, count in dir_tags.items():
                                        all_tags[t] = all_tags.get(t, 0) + count
                            sorted_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)
                            triggers.extend([t[0] for t in sorted_tags[:5]])
                        except Exception:
                            pass
        except Exception:
            pass

    seen = set()
    unique_triggers = []
    for t in triggers:
        norm = t.lower().strip()
        if norm not in seen and len(norm) > 1:
            seen.add(norm)
            unique_triggers.append(t.strip())
    return unique_triggers


def register_lora_routes():
    """Registers GET /stoiqo/loras and /stoiqo/lora_info with ComfyUI's PromptServer."""
    try:
        from server import PromptServer
        from aiohttp import web

        if hasattr(PromptServer, "instance") and PromptServer.instance is not None:
            routes = PromptServer.instance.routes
            if not any(getattr(r, "path", None) == "/stoiqo/loras" for r in routes):
                @routes.get("/stoiqo/loras")
                async def stoiqo_list_loras(request):
                    try:
                        loras = folder_paths.get_filename_list("loras")
                    except Exception:
                        loras = []
                    return web.json_response({"loras": list(loras)})

            if not any(getattr(r, "path", None) == "/stoiqo/lora_info" for r in routes):
                @routes.get("/stoiqo/lora_info")
                async def stoiqo_lora_info(request):
                    name = request.query.get("name", "").strip()
                    if not name:
                        return web.json_response({"error": "name parameter missing"}, status=400)
                    full_path = folder_paths.get_full_path("loras", name)
                    triggers = extract_lora_trigger_words(full_path) if full_path else []
                    return web.json_response({
                        "name": name,
                        "found": full_path is not None,
                        "triggers": triggers,
                    })
    except Exception as exc:
        print(f"[STOIQO] Notice: LoRA route registration deferred: {exc}")


register_lora_routes()


def _to_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_lora_stack(raw):
    """
    Parses the JSON stored by the canvas widget into a clean list of dicts:
    {"name": str, "strength": float, "strength_clip": float, "enabled": bool}.
    Invalid / empty entries are dropped. Never raises on malformed input.
    """
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return []
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            print("[STOIQO] LoRA Stack: lora_stack JSON is malformed, ignoring it.")
            return []
    else:
        data = raw

    if not isinstance(data, list):
        return []

    entries = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name or name.lower() == "none":
            continue
        strength = _to_float(item.get("strength"), 1.0)
        strength_clip = _to_float(item.get("strength_clip"), strength)
        entries.append(
            {
                "name": name,
                "strength": strength,
                "strength_clip": strength_clip,
                "enabled": bool(item.get("enabled", True)),
                "block_filter": str(item.get("block_filter") or "All Blocks (Standard)"),
            }
        )
    return entries


class StoiqoLoraStackNode:
    """
    [STOIQO] LoRA Stack
    Single node, unlimited LoRAs: add with "+", toggle each one individually, set strengths.
    """

    def __init__(self):
        self._lora_cache = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL", {"tooltip": "Diffusion model to patch with the active LoRAs."}),
            },
            "optional": {
                "clip": ("CLIP", {"tooltip": "Optional text encoder to patch with the active LoRAs."}),
                "optional_lora_stack": (
                    "LORA_STACK",
                    {
                        "tooltip": "Optional incoming LoRA stack from upstream node to daisy-chain.",
                    },
                ),
                "block_filter": (
                    [
                        "All Blocks (Standard)",
                        "Style / Texture Only (OUT Blocks)",
                        "Character / Structure Only (IN/MID Blocks)",
                        "Face & Pose Focused (MID Block)",
                    ],
                    {"default": "All Blocks (Standard)", "tooltip": "LoRA Block Weighting: Filter specific layers (IN=geometry/pose, MID=subject/face, OUT=texture/style)."},
                ),
                "lora_stack": (
                    "STRING",
                    {
                        "default": "[]",
                        "multiline": False,
                        "tooltip": "Managed by the canvas UI (hidden). JSON list of LoRAs.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING")
    RETURN_NAMES = ("model", "clip", "lora_summary")
    FUNCTION = "apply_loras"
    CATEGORY = "STOIQO"

    @staticmethod
    def filter_lora_state_dict(state_dict, block_filter: str):
        """LoRA Block Weighting: selects or scales weights by architectural layer."""
        if not block_filter or block_filter == "All Blocks (Standard)" or not isinstance(state_dict, dict):
            return state_dict

        filtered = {}
        for k, v in state_dict.items():
            if "lora_te" in k or "text_model" in k or "clip" in k:
                filtered[k] = v
                continue

            is_in = "input_blocks" in k or "down_blocks" in k or ".down." in k or "double_blocks" in k
            is_mid = "middle_block" in k or "mid_block" in k or ".mid." in k
            is_out = "output_blocks" in k or "up_blocks" in k or ".up." in k or "single_blocks" in k

            if block_filter == "Style / Texture Only (OUT Blocks)":
                if is_out:
                    filtered[k] = v
            elif block_filter == "Character / Structure Only (IN/MID Blocks)":
                if is_in or is_mid:
                    filtered[k] = v
            elif block_filter == "Face & Pose Focused (MID Block)":
                if is_mid:
                    filtered[k] = v
                elif is_in:
                    filtered[k] = v * 0.3
            else:
                filtered[k] = v
        return filtered

    def _load_lora_state_dict(self, path):
        import os

        try:
            mtime = os.path.getmtime(path)
        except OSError:
            mtime = 0
        key = (path, mtime)
        cached = self._lora_cache.get(key)
        if cached is not None:
            return cached
        state_dict = comfy.utils.load_torch_file(path, safe_load=True)
        # Keep only a handful of LoRAs in RAM to bound memory usage.
        if len(self._lora_cache) >= 4:
            self._lora_cache.pop(next(iter(self._lora_cache)))
        self._lora_cache[key] = state_dict
        return state_dict

    def apply_loras(
        self,
        model,
        clip=None,
        arg3=None,
        arg4=None,
        optional_lora_stack=None,
        **kwargs,
    ):
        # Gracefully handle all calling conventions:
        # 1. apply_loras(model, clip, lora_stack) [3 args]
        # 2. apply_loras(model, clip, lora_stack, block_filter) [4 args, old signature]
        # 3. apply_loras(model, clip, block_filter, lora_stack) [4 args, matching INPUT_TYPES order]
        # 4. keyword arguments
        lora_stack = kwargs.get("lora_stack", None)
        block_filter = kwargs.get("block_filter", None)

        for arg in (arg3, arg4):
            if arg is None:
                continue
            if isinstance(arg, str):
                s = arg.strip()
                if s.startswith("[") or s.startswith("{"):
                    lora_stack = arg
                elif s in [
                    "All Blocks (Standard)",
                    "Style / Texture Only (OUT Blocks)",
                    "Character / Structure Only (IN/MID Blocks)",
                    "Face & Pose Focused (MID Block)",
                ]:
                    block_filter = arg
                elif not lora_stack and s:
                    if any(c in s for c in '[]{}:"'):
                        lora_stack = arg
                    else:
                        block_filter = arg

        if lora_stack is None:
            lora_stack = "[]"
        if block_filter is None:
            block_filter = "All Blocks (Standard)"

        # 1. Process optional incoming LORA_STACK
        entries = []
        if optional_lora_stack and isinstance(optional_lora_stack, (list, tuple)):
            for item in optional_lora_stack:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    st_name = str(item[0])
                    st_sm = _to_float(item[1], 1.0)
                    st_sc = _to_float(item[2], st_sm) if len(item) > 2 else st_sm
                    entries.append({
                        "name": st_name,
                        "strength": st_sm,
                        "strength_clip": st_sc,
                        "enabled": True,
                        "source": "upstream_stack",
                    })

        # 2. Append local node entries
        entries.extend(parse_lora_stack(lora_stack))
        summary_lines = []

        for entry in entries:
            name = entry["name"]
            sm = entry["strength"]
            sc = entry["strength_clip"] if clip is not None else 0.0
            entry_filter = entry.get("block_filter") or block_filter

            if not entry.get("enabled", True):
                summary_lines.append(f"[OFF] {name}")
                continue
            if sm == 0.0 and sc == 0.0:
                summary_lines.append(f"[SKIP strength 0] {name}")
                continue

            # Look up path & triggers
            path = folder_paths.get_full_path("loras", name)
            triggers = extract_lora_trigger_words(path) if path else []
            triggers_str = f" (Triggers: {', '.join(triggers[:5])})" if triggers else ""

            if comfy is None:
                # Headless environment (unit tests): nothing to patch.
                summary_lines.append(f"[ON] {name} @ {sm:g}" + (f" [{entry_filter}]" if entry_filter != "All Blocks (Standard)" else "") + triggers_str)
                continue

            if path is None:
                print(f"[STOIQO] LoRA Stack: '{name}' not found in models/loras, skipped.")
                summary_lines.append(f"[MISSING] {name}")
                continue

            try:
                raw_state_dict = self._load_lora_state_dict(path)
                state_dict = self.filter_lora_state_dict(raw_state_dict, entry_filter)
                model, clip = comfy.sd.load_lora_for_models(model, clip, state_dict, sm, sc)
                filter_tag = f" [{entry_filter}]" if entry_filter != "All Blocks (Standard)" else ""
                summary_lines.append(f"[ON] {name} @ {sm:g}" + (f" / clip {sc:g}" if clip is not None and sc != sm else "") + filter_tag + triggers_str)
                print(f"[STOIQO] LoRA Stack: applied '{name}' (model={sm:g}, clip={sc:g}{filter_tag}{triggers_str})")
            except Exception as err:
                print(f"[STOIQO] LoRA Stack: Error patching '{name}': {err}. Skipping this LoRA.")
                summary_lines.append(f"[ERROR] {name} ({err})")

        summary = "\n".join(summary_lines) if summary_lines else "(no LoRAs)"
        return (model, clip, summary)
