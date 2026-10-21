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


def register_lora_routes():
    """Registers GET /stoiqo/loras (list of available LoRA files) with ComfyUI's PromptServer."""
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
                "block_filter": (
                    [
                        "All Blocks (Standard)",
                        "Style / Texture Only (OUT Blocks)",
                        "Character / Structure Only (IN/MID Blocks)",
                        "Face & Pose Focused (MID Block)",
                    ],
                    {"default": "All Blocks (Standard)", "tooltip": "LoRA Block Weighting (#80): Filter specific layers (IN=geometry/pose, MID=subject/face, OUT=texture/style)."},
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

    def apply_loras(self, model, clip=None, lora_stack="[]", block_filter="All Blocks (Standard)"):
        # Handle positional swap if block_filter contains json array
        if lora_stack == "[]" and isinstance(block_filter, str) and block_filter.strip().startswith("["):
            lora_stack, block_filter = block_filter, "All Blocks (Standard)"

        entries = parse_lora_stack(lora_stack)
        summary_lines = []

        for entry in entries:
            name = entry["name"]
            sm = entry["strength"]
            sc = entry["strength_clip"] if clip is not None else 0.0
            entry_filter = entry.get("block_filter") or block_filter

            if not entry["enabled"]:
                summary_lines.append(f"[OFF] {name}")
                continue
            if sm == 0.0 and sc == 0.0:
                summary_lines.append(f"[SKIP strength 0] {name}")
                continue

            if comfy is None:
                # Headless environment (unit tests): nothing to patch.
                summary_lines.append(f"[ON] {name} @ {sm:g}" + (f" [{entry_filter}]" if entry_filter != "All Blocks (Standard)" else ""))
                continue

            path = folder_paths.get_full_path("loras", name)
            if path is None:
                print(f"[STOIQO] LoRA Stack: '{name}' not found in models/loras, skipped.")
                summary_lines.append(f"[MISSING] {name}")
                continue

            raw_state_dict = self._load_lora_state_dict(path)
            state_dict = self.filter_lora_state_dict(raw_state_dict, entry_filter)
            model, clip = comfy.sd.load_lora_for_models(model, clip, state_dict, sm, sc)
            filter_tag = f" [{entry_filter}]" if entry_filter != "All Blocks (Standard)" else ""
            summary_lines.append(f"[ON] {name} @ {sm:g}" + (f" / clip {sc:g}" if clip is not None and sc != sm else "") + filter_tag)
            print(f"[STOIQO] LoRA Stack: applied '{name}' (model={sm:g}, clip={sc:g}{filter_tag})")

        summary = "\n".join(summary_lines) if summary_lines else "(no LoRAs)"
        return (model, clip, summary)
