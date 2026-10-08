"""
[STOIQO] Prompt Generator Engine — Model Management & Execution
Handles model repo resolution, dynamic BitsAndBytes quantization, attention implementation,
caching, GPU/CPU lifecycle, and inference generation.
"""

import os
import gc
import json
import glob
import torch

from transformers import (
    AutoProcessor,
    BitsAndBytesConfig,
)

import time
from tqdm.auto import tqdm

import folder_paths
import comfy.model_management as mm
import comfy.utils

# ── Resilient safetensors safe_open compatibility patch ───────────────────────
try:
    import safetensors
    _orig_safe_open = getattr(safetensors, "safe_open", None)
    if _orig_safe_open is not None:
        def _resilient_safe_open(*args, **kwargs):
            try:
                return _orig_safe_open(*args, **kwargs)
            except TypeError as te:
                if "backend" in str(te):
                    kwargs.pop("backend", None)
                    return _orig_safe_open(*args, **kwargs)
                raise
        safetensors.safe_open = _resilient_safe_open
        try:
            import transformers.modeling_utils as tf_mod
            if hasattr(tf_mod, "safe_open"):
                tf_mod.safe_open = _resilient_safe_open
        except Exception:
            pass
except Exception:
    pass

try:
    from server import PromptServer
except ImportError:
    PromptServer = None

from .config import MODEL_PRESETS, ATTENTION_OPTIONS, CUSTOM_MODEL_KEY
from .vision import process_vision_info
from .text_processing import clean_llm_output


class ComfyHFDownloadProgress(tqdm):
    """
    Subclass of tqdm for huggingface_hub snapshot_download.
    Intercepts byte-level download updates and mirrors them to:
    1. ComfyUI's native progress bar (top navigation bar in web UI).
    2. ComfyUI WebSocket PromptServer with custom event 'stoiqo_download_progress'.
    3. Throttled console logging.
    """
    _comfy_pbar = None
    _last_pct = -1
    _last_log_time = 0.0
    _active_repo = ""

    @classmethod
    def set_active_repo(cls, repo_id):
        cls._active_repo = repo_id
        cls._comfy_pbar = None
        cls._last_pct = -1
        cls._last_log_time = 0.0

    @staticmethod
    def _format_bytes(size_bytes):
        if not size_bytes or size_bytes <= 0:
            return "0 B"
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        idx = 0
        s = float(size_bytes)
        while s >= 1024.0 and idx < len(units) - 1:
            s /= 1024.0
            idx += 1
        return f"{s:.1f} {units[idx]}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        is_byte_meter = kwargs.get("unit") == "B" or "download" in str(kwargs.get("desc", "")).lower()
        if is_byte_meter and ComfyHFDownloadProgress._comfy_pbar is None:
            ComfyHFDownloadProgress._comfy_pbar = comfy.utils.ProgressBar(100)

    def update(self, n=1):
        super().update(n)
        is_byte_meter = self.unit == "B" or "download" in str(self.desc).lower()
        if is_byte_meter and self.total and self.total > 0:
            pct = min(100, max(0, int((self.n / self.total) * 100)))
            now = time.time()
            if pct != ComfyHFDownloadProgress._last_pct or (now - ComfyHFDownloadProgress._last_log_time) >= 1.5:
                ComfyHFDownloadProgress._last_pct = pct
                ComfyHFDownloadProgress._last_log_time = now

                # 1. Update native ComfyUI top progress bar
                if ComfyHFDownloadProgress._comfy_pbar is not None:
                    ComfyHFDownloadProgress._comfy_pbar.update_absolute(pct, 100)

                # 2. Emit WebSocket progress event for Stoiqo UI canvas widgets
                if PromptServer is not None and hasattr(PromptServer, "instance") and PromptServer.instance is not None:
                    try:
                        PromptServer.instance.send_sync("stoiqo_download_progress", {
                            "repo": ComfyHFDownloadProgress._active_repo,
                            "percent": pct,
                            "downloaded_bytes": self.n,
                            "total_bytes": self.total,
                            "downloaded_str": self._format_bytes(self.n),
                            "total_str": self._format_bytes(self.total),
                            "status": "downloading" if pct < 100 else "complete"
                        })
                    except Exception:
                        pass

    def close(self):
        super().close()
        is_byte_meter = self.unit == "B" or "download" in str(self.desc).lower()
        if is_byte_meter and ComfyHFDownloadProgress._comfy_pbar is not None:
            ComfyHFDownloadProgress._comfy_pbar.update_absolute(100, 100)
            ComfyHFDownloadProgress._comfy_pbar = None
            ComfyHFDownloadProgress._last_pct = -1
            if PromptServer is not None and hasattr(PromptServer, "instance") and PromptServer.instance is not None:
                try:
                    PromptServer.instance.send_sync("stoiqo_download_progress", {
                        "repo": ComfyHFDownloadProgress._active_repo,
                        "percent": 100,
                        "status": "complete"
                    })
                except Exception:
                    pass


class ModelManager:
    """Manages VLM model loading, device placement, quantization, caching, and inference."""

    def __init__(self):
        self.model = None
        self.processor = None
        self.current_model_repo = ""
        self.current_cache_key = None
        self.current_attn = None
        self.keep_in_vram = True
        self.last_load_params = None

    def resolve_model_repo(self, model_preset, local_model_path, model_mode=None):
        """Resolves target model path from unified preset dropdown or local folder path with safety validation."""
        is_custom = (
            model_preset == CUSTOM_MODEL_KEY
            or "Custom" in str(model_preset)
            or (model_mode is not None and "Local Folder" in str(model_mode))
        )
        if is_custom:
            path = local_model_path.strip()
            if not path:
                raise ValueError(
                    "[STOIQO] Model is set to 'Custom Model' but local_model_path is empty.\n"
                    "Click '📁 Browse Model Folder on Disk' or paste the absolute path to your model folder."
                )
            if not os.path.isabs(path):
                raise ValueError(
                    f"[STOIQO] local_model_path must be an absolute path, got: '{path}'"
                )
            if not os.path.isdir(path):
                raise FileNotFoundError(
                    f"[STOIQO] local_model_path folder does not exist: '{path}'\n"
                    "Double-check the path."
                )
            if not os.path.exists(os.path.join(path, "config.json")):
                print(f"[STOIQO] Warning: '{path}' has no config.json — may not be a valid model folder.")
            print(f"[STOIQO] Loading model from local disk: {path}")
            return path

        # Preset mode: lookup by exact key, fallback to 7B
        repo = MODEL_PRESETS.get(model_preset)
        if repo:
            return repo
        print(f"[STOIQO] Warning: preset '{model_preset}' not found in MODEL_PRESETS. Falling back to 7B.")
        return list(MODEL_PRESETS.values())[1]

    def resolve_quant_config(self, quantization):
        """Builds BitsAndBytesConfig with hardware-accelerated bfloat16/float16 compute_dtype."""
        if "4bit" in quantization:
            compute_dtype = (
                torch.bfloat16
                if torch.cuda.is_available() and torch.cuda.is_bf16_supported()
                else torch.float16
            )
            return BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=compute_dtype,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
        if "8bit" in quantization:
            return BitsAndBytesConfig(load_in_8bit=True)
        return None

    def resolve_attn_implementation(self, attention_mode):
        """Selects attention implementation kernel with GPU capability checks and graceful fallback."""
        mode_lower = attention_mode.lower()
        if "flash" in mode_lower:
            try:
                import flash_attn  # noqa: F401
                if torch.cuda.is_available() and torch.cuda.get_device_capability()[0] >= 8:
                    return "flash_attention_2"
                print("[STOIQO] Flash-Attention 2 requires Ampere+ GPU (RTX 3000+). Falling back to 'sdpa'.")
                return "sdpa"
            except ImportError:
                print("[STOIQO] flash_attn package not installed. Falling back to 'sdpa'.")
                return "sdpa"
        if "eager" in mode_lower:
            return "eager"
        # sdpa is default (and graceful fallback for legacy 'auto')
        return "sdpa"

    @staticmethod
    def get_llm_models_dir():
        """
        Resolves the LLM models directory respecting ComfyUI configuration.
        Strict Priority:
        1. ComfyUI folder_paths.get_folder_paths("LLM") (e.g. from extra_model_paths.yaml).
        2. Parsing extra_model_paths.yaml directly if folder_paths wasn't registered.
        3. Fallback to folder_paths.models_dir / "LLM".
        """
        llm_dir = None
        try:
            if hasattr(folder_paths, "get_folder_paths"):
                paths = folder_paths.get_folder_paths("LLM")
                if paths and len(paths) > 0 and paths[0]:
                    llm_dir = paths[0]
        except Exception:
            llm_dir = None

        if not llm_dir:
            # Fallback: parse extra_model_paths.yaml directly from ComfyUI directory
            try:
                comfy_dir = os.path.dirname(os.path.abspath(folder_paths.__file__))
                for candidate_name in ["extra_model_paths.yaml", "extra_model_paths.yml"]:
                    yaml_path = os.path.join(comfy_dir, candidate_name)
                    if os.path.isfile(yaml_path):
                        import yaml
                        with open(yaml_path, "r", encoding="utf-8") as f:
                            cfg = yaml.safe_load(f)
                        if isinstance(cfg, dict):
                            for entry in cfg.values():
                                if isinstance(entry, dict) and "LLM" in entry:
                                    base = entry.get("base_path", "")
                                    sub = entry.get("LLM", "LLM").strip()
                                    candidate = os.path.join(base, sub) if base else sub
                                    if candidate:
                                        llm_dir = os.path.normpath(candidate)
                                        break
                    if llm_dir:
                        break
            except Exception:
                pass

        if not llm_dir:
            llm_dir = os.path.join(folder_paths.models_dir, "LLM")

        os.makedirs(llm_dir, exist_ok=True)
        try:
            folder_paths.add_model_folder_path("LLM", llm_dir)
        except Exception:
            pass
        return llm_dir

    @staticmethod
    def find_local_model_snapshot(repo_id):
        """
        Scans all known local model storage directories to check if the model is already downloaded.
        Returns the absolute snapshot directory if valid weights are found, otherwise None.
        """
        import glob

        # Risolve la root di ExCathedra cercando user_data risalendo l'albero
        curr = os.path.abspath(os.path.dirname(__file__))
        detected_root = None
        for _ in range(8):
            curr = os.path.dirname(curr)
            if os.path.isdir(os.path.join(curr, "user_data")) or os.path.isdir(os.path.join(curr, "workspace")):
                detected_root = curr
                break
        workspace_root = detected_root or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".."))
        sandbox_cache = os.path.join(workspace_root, "user_data", "_sandbox", ".cache", "huggingface", "hub")

        search_dirs = [
            ModelManager.get_llm_models_dir(),
            os.path.join(folder_paths.models_dir, "LLM"),
            os.path.join(workspace_root, "workspace", "models", "LLM"),
            sandbox_cache,
            os.path.expanduser("~/.cache/huggingface/hub"),
        ]
        try:
            if hasattr(folder_paths, "get_folder_paths"):
                for p in folder_paths.get_folder_paths("LLM"):
                    if p and p not in search_dirs:
                        search_dirs.append(p)
        except Exception:
            pass

        hf_home = os.environ.get("HF_HOME")
        if hf_home:
            search_dirs.append(os.path.join(hf_home, "hub"))

        hub_name = "models--" + repo_id.replace("/", "--")
        repo_name = repo_id.split("/")[-1]

        for s_dir in search_dirs:
            if not s_dir or not os.path.isdir(s_dir):
                continue

            # Case A: Hugging Face hub cache layout (models--org--name/snapshots/<hash>)
            hub_path = os.path.join(s_dir, hub_name, "snapshots")
            if os.path.isdir(hub_path):
                for snap in os.listdir(hub_path):
                    snap_dir = os.path.join(hub_path, snap)
                    cfg = os.path.join(snap_dir, "config.json")
                    if os.path.isfile(cfg):
                        blobs_dir = os.path.join(s_dir, hub_name, "blobs")
                        incomplete = glob.glob(os.path.join(blobs_dir, "*.incomplete")) if os.path.isdir(blobs_dir) else []
                        weights = (
                            glob.glob(os.path.join(snap_dir, "*.safetensors"))
                            or glob.glob(os.path.join(snap_dir, "*.bin"))
                            or [os.path.join(snap_dir, "model.safetensors.index.json")]
                        )
                        if any(os.path.exists(w) for w in weights) and not incomplete:
                            return snap_dir

            # Case B: Direct folder named after repo (e.g. Qwen2.5-VL-7B-Instruct)
            direct_path = os.path.join(s_dir, repo_name)
            if os.path.isdir(direct_path) and os.path.isfile(os.path.join(direct_path, "config.json")):
                return direct_path

        return None

    def load_model(self, model_repo, quantization, attention_mode=ATTENTION_OPTIONS[0], keep_in_vram=True):
        """Loads and caches the model and processor into VRAM using ComfyUI memory management."""
        self.keep_in_vram = keep_in_vram
        self.last_load_params = {
            "model_repo": model_repo,
            "quantization": quantization,
            "attention_mode": attention_mode,
            "keep_in_vram": keep_in_vram,
        }
        chosen_attn = self.resolve_attn_implementation(attention_mode)
        cache_key = (model_repo, quantization, chosen_attn)
        if self.model is not None and self.current_cache_key == cache_key:
            return

        llm_models_dir = self.get_llm_models_dir()

        print(f"\n[STOIQO] Target model: {model_repo}")
        print(f"[STOIQO] Configured models directory: {llm_models_dir}")
        print(f"[STOIQO] Attention backend requested: '{chosen_attn}' (selected: {attention_mode})")

        # ── Step 1: Check if already present on disk (zero-download check) ─────
        load_target = model_repo
        is_local = os.path.isdir(model_repo)

        if not is_local:
            existing_snap = self.find_local_model_snapshot(model_repo)
            if existing_snap:
                load_target = existing_snap
                is_local = True
                print(f"[STOIQO] [OK] Model already present locally! Loaded from: {load_target}")
                print("[STOIQO] Network download bypassed — loading directly from disk.")

        # ── Step 2: Download only if NOT found anywhere locally ────────────────
        if not is_local:
            try:
                from huggingface_hub import snapshot_download
                print(f"[STOIQO] Model not found in any local path. Downloading '{model_repo}' to: {llm_models_dir}...")
                ComfyHFDownloadProgress.set_active_repo(model_repo)
                snapshot_dir = snapshot_download(
                    repo_id=model_repo,
                    cache_dir=llm_models_dir,
                    tqdm_class=ComfyHFDownloadProgress,
                )
                if snapshot_dir and os.path.isdir(snapshot_dir):
                    load_target = snapshot_dir
                    is_local = True
                    print(f"[STOIQO] Download completed successfully: {load_target}")
            except Exception as dl_err:
                print(f"[STOIQO] Warning: snapshot_download check failed ({dl_err}). Falling back to standard loader.")
                load_target = model_repo

        target_device = mm.get_torch_device()
        print(f"[STOIQO] Using device: {target_device} via ComfyUI model management")

        if target_device.type == "cuda":
            dtype = (
                torch.bfloat16
                if torch.cuda.is_available() and torch.cuda.is_bf16_supported()
                else torch.float16
            )
        else:
            dtype = torch.float32

        load_kwargs = {
            "device_map": {"": target_device},
            "torch_dtype": dtype,
            "cache_dir": llm_models_dir,
            "attn_implementation": chosen_attn,
        }

        if os.path.isdir(load_target):
            load_kwargs["local_files_only"] = True

        quant_cfg = self.resolve_quant_config(quantization)
        if quant_cfg is not None:
            if target_device.type == "cuda":
                load_kwargs["quantization_config"] = quant_cfg
                print(f"[STOIQO] Quantization: {quantization}")
            else:
                print("[STOIQO] Warning: Quantization (4-bit/8-bit) requires CUDA; falling back to unquantized mode on non-CUDA device.")
        else:
            print(f"[STOIQO] Quantization: None (full precision {dtype})")
            if any(k in str(model_repo).lower() for k in ("32b", "72b")):
                print(f"[STOIQO] WARNING: Running large model ({model_repo}) without quantization requires high VRAM (>= 60 GB)!")

        # Detect model class from repo path or local config.json
        is_qwen25 = False
        config_path = os.path.join(load_target, "config.json") if os.path.isdir(load_target) else None
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                is_qwen25 = "2_5" in cfg.get("model_type", "") or "2.5" in cfg.get("architectures", [""])[0]
            except Exception:
                pass
        else:
            is_qwen25 = "Qwen2.5" in model_repo or "qwen2.5" in model_repo.lower() or "/Qwen2.5-VL" in model_repo

        if is_qwen25:
            from transformers import Qwen2_5_VLForConditionalGeneration as ModelClass
        else:
            from transformers import Qwen2VLForConditionalGeneration as ModelClass

        # Resilient loading with attention fallback and OOM safeguard
        try:
            self.model = ModelClass.from_pretrained(load_target, **load_kwargs)
        except torch.cuda.OutOfMemoryError as oom_exc:
            self.unload_model()
            raise RuntimeError(
                f"[STOIQO] CUDA Out of Memory while loading '{model_repo}'!\n"
                "Suggestions to fix:\n"
                "1. Set 'quantization' to '4bit - NF4' to cut VRAM usage by ~70%.\n"
                "2. Pick a smaller model preset (e.g. 3B or 7B instead of 32B/72B).\n"
                "3. Ensure other GPU-heavy processes or workflows are closed."
            ) from oom_exc
        except Exception as primary_exc:
            print(f"[STOIQO] Failed to load with attn_implementation='{chosen_attn}': {primary_exc}")
            if chosen_attn != "sdpa" and hasattr(torch.nn.functional, "scaled_dot_product_attention"):
                print("[STOIQO] Falling back to 'sdpa' attention...")
                load_kwargs["attn_implementation"] = "sdpa"
                try:
                    self.model = ModelClass.from_pretrained(load_target, **load_kwargs)
                    chosen_attn = "sdpa"
                except torch.cuda.OutOfMemoryError as oom_exc:
                    self.unload_model()
                    raise RuntimeError(
                        f"[STOIQO] CUDA Out of Memory while loading '{model_repo}'!\n"
                        "Enable '4bit - NF4' quantization or use a smaller model."
                    ) from oom_exc
                except Exception as sdpa_exc:
                    print(f"[STOIQO] SDPA failed ({sdpa_exc}). Falling back to 'eager' attention...")
                    load_kwargs["attn_implementation"] = "eager"
                    try:
                        self.model = ModelClass.from_pretrained(load_target, **load_kwargs)
                        chosen_attn = "eager"
                    except torch.cuda.OutOfMemoryError as oom_exc:
                        self.unload_model()
                        raise RuntimeError(
                            f"[STOIQO] CUDA Out of Memory while loading '{model_repo}'!\n"
                            "Enable '4bit - NF4' quantization or use a smaller model."
                        ) from oom_exc
            elif chosen_attn != "eager":
                print("[STOIQO] Falling back to 'eager' attention...")
                load_kwargs["attn_implementation"] = "eager"
                try:
                    self.model = ModelClass.from_pretrained(load_target, **load_kwargs)
                    chosen_attn = "eager"
                except torch.cuda.OutOfMemoryError as oom_exc:
                    self.unload_model()
                    raise RuntimeError(
                        f"[STOIQO] CUDA Out of Memory while loading '{model_repo}'!\n"
                        "Enable '4bit - NF4' quantization or use a smaller model."
                    ) from oom_exc
            else:
                raise primary_exc

        is_local_target = os.path.isdir(load_target)
        try:
            self.processor = AutoProcessor.from_pretrained(
                load_target,
                cache_dir=llm_models_dir,
                local_files_only=is_local_target,
            )
        except Exception as proc_exc:
            print(f"[STOIQO] AutoProcessor failed ({proc_exc}); retrying with trust_remote_code=True...")
            self.processor = AutoProcessor.from_pretrained(
                load_target,
                cache_dir=llm_models_dir,
                trust_remote_code=True,
                local_files_only=is_local_target,
            )
        self.current_model_repo = model_repo
        self.current_cache_key = (model_repo, quantization, chosen_attn)
        self.current_attn = chosen_attn
        print(f"[STOIQO] Model ready: {model_repo} [Attention: {chosen_attn}]\n")

    def unload_model(self):
        """Forces immediate GPU VRAM release with CPU offload and cache purging."""
        print("[STOIQO] Unloading model and freeing VRAM...")
        vram_before = torch.cuda.memory_allocated() if torch.cuda.is_available() else 0

        if self.model is not None:
            try:
                self.model.to("cpu")
            except Exception:
                pass
        self.model = None
        self.processor = None
        self.current_model_repo = ""
        self.current_cache_key = None
        self.current_attn = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            try:
                torch.cuda.ipc_collect()
            except Exception:
                pass
        mm.soft_empty_cache()

        if torch.cuda.is_available():
            vram_after = torch.cuda.memory_allocated()
            freed_mb = max(0.0, (vram_before - vram_after) / (1024 * 1024))
            remaining_mb = vram_after / (1024 * 1024)
            print(f"[STOIQO] VRAM freed: {freed_mb:.1f} MB | Active allocated remaining: {remaining_mb:.1f} MB")

    def generate_single(
        self,
        pil_images,
        task_prompt,
        system_prompt,
        max_new_tokens,
        temperature,
        top_p=0.9,
        repetition_penalty=1.1,
        is_multi_image=False,
    ):
        if self.model is None:
            if self.last_load_params is not None:
                print("[STOIQO] Model was offloaded in Low VRAM mode. Reloading for current inference pass...")
                self.load_model(**self.last_load_params)
            else:
                raise RuntimeError(
                    "[STOIQO] No VLM model is loaded and no prior load parameters exist.\n"
                    "Please ensure a model is loaded via [STOIQO] VLM Model Loader or configured in the engine node."
                )

        messages = []
        if system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})

        content_list = []
        if pil_images is not None:
            if is_multi_image and isinstance(pil_images, list):
                for idx, img in enumerate(pil_images):
                    content_list.append({"type": "text", "text": f"<Image {idx + 1}>:"})
                    content_list.append({"type": "image", "image": img})
            else:
                content_list.append({"type": "image", "image": pil_images})

        content_list.append({"type": "text", "text": task_prompt})

        messages.append({
            "role": "user",
            "content": content_list,
        })

        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        image_inputs, _ = process_vision_info(messages)
        proc_kwargs = {
            "text": [text],
            "padding": True,
            "return_tensors": "pt",
        }
        if image_inputs is not None:
            proc_kwargs["images"] = image_inputs

        inputs = self.processor(**proc_kwargs).to(next(self.model.parameters()).device)

        gen_kwargs = {"max_new_tokens": max_new_tokens}
        if repetition_penalty and repetition_penalty != 1.0:
            gen_kwargs["repetition_penalty"] = repetition_penalty
        if temperature > 0:
            gen_kwargs["do_sample"] = True
            gen_kwargs["temperature"] = temperature
            if top_p and 0.0 < top_p < 1.0:
                gen_kwargs["top_p"] = top_p
        else:
            gen_kwargs["do_sample"] = False

        try:
            with torch.no_grad():
                generated_ids = self.model.generate(**inputs, **gen_kwargs)
        except torch.cuda.OutOfMemoryError as oom_exc:
            self.unload_model()
            raise RuntimeError(
                "[STOIQO] CUDA Out of Memory during inference generation!\n"
                "Suggestions to fix:\n"
                "1. Reduce 'target_megapixel' (e.g. from 1.0 to 0.5 or 0.25).\n"
                "2. Reduce 'max_new_tokens' (e.g. from 2048 to 512).\n"
                "3. Enable '4bit - NF4' quantization.\n"
                "4. Free VRAM by setting 'unload_model_after' to True."
            ) from oom_exc

        trimmed = [
            out[len(inp):] for inp, out in zip(inputs.input_ids, generated_ids)
        ]
        tokens_count = len(trimmed[0])
        print(f"[STOIQO] Inference complete: {tokens_count} tokens generated (budget: {max_new_tokens}, temp: {temperature})")
        decoded = self.processor.batch_decode(
            trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0].strip()

        if not getattr(self, "keep_in_vram", True):
            print("[STOIQO] Low VRAM Mode: Offloading model immediately after generation to free GPU memory.")
            self.unload_model()

        return clean_llm_output(decoded)
