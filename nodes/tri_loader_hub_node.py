"""
[STOIQO] Tri-Model Loader Hub Node
Consolidates modular modern architecture (UNET/DiT, CLIP, VAE) into a single clean node.
Produces individual MODEL, CLIP, VAE outputs and a unified STOIQO_PIPE for streamlined workflows.
"""

import os
import torch

try:
    import folder_paths
except ImportError:
    class _MockFolderPaths:
        @staticmethod
        def get_filename_list(folder):
            return ["none"]
        @staticmethod
        def get_full_path_or_raise(folder, filename):
            return filename
        @staticmethod
        def get_folder_paths(folder):
            return []
    folder_paths = _MockFolderPaths()

try:
    import comfy.sd
    import comfy.utils
    import comfy.model_management
except ImportError:
    comfy = None


class StoiqoTriLoaderHubNode:
    """
    [STOIQO] Tri-Model Loader Hub
    Single-node loader for modern diffusion architectures (Krea 2, SeedVR2, MiniMax, YuE 2).
    Unifies UNET, CLIP, and VAE loading and emits individual pins plus a unified STOIQO_PIPE.
    """

    @classmethod
    def INPUT_TYPES(cls):
        unets = folder_paths.get_filename_list("diffusion_models") if hasattr(folder_paths, "get_filename_list") else []
        clips = folder_paths.get_filename_list("text_encoders") if hasattr(folder_paths, "get_filename_list") else []
        vaes = folder_paths.get_filename_list("vae") if hasattr(folder_paths, "get_filename_list") else []

        if not unets:
            unets = ["none"]
        if not clips:
            clips = ["none"]
        if not vaes:
            vaes = ["none"]

        clip_types = [
            "krea2",
            "stable_diffusion",
            "minimax",
            "yue2",
            "sd3",
            "lumina2",
            "wan",
            "mochi",
            "ltxv",
            "qwen_image",
            "hunyuan_image",
        ]

        return {
            "required": {
                "unet_name": (unets, {"tooltip": "Diffusion model / UNET / DiT checkpoint (e.g. Krea 2 Turbo)."}),
                "weight_dtype": (
                    ["default", "fp8_e4m3fn", "fp8_e4m3fn_fast", "fp8_e5m2"],
                    {"default": "default", "tooltip": "UNET quantization / precision mode."},
                ),
                "clip_name": (clips, {"tooltip": "Text encoder / CLIP model checkpoint."}),
                "clip_type": (clip_types, {"default": "krea2", "tooltip": "CLIP architecture recipe (default: krea2)."}),
                "vae_name": (vaes, {"tooltip": "Variational Auto-Encoder (VAE) checkpoint."}),
            },
            "optional": {
                "pipe": ("*", {"tooltip": "Optional incoming pipeline or rgthree Context to merge with."}),
                "clip_device": (["default", "cpu"], {"default": "default", "tooltip": "Device for CLIP model (select CPU to save VRAM on tight GPUs)."}),
            },
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STOIQO_PIPE")
    RETURN_NAMES = ("model", "clip", "vae", "stoiqo_pipe")
    FUNCTION = "load_tri_models"
    CATEGORY = "STOIQO"

    def load_tri_models(
        self,
        unet_name: str,
        weight_dtype: str,
        clip_name: str,
        clip_type: str,
        vae_name: str,
        pipe=None,
        clip_device: str = "default",
    ):
        if comfy is None:
            # Fallback for headless testing environments
            model = {"name": unet_name, "dtype": weight_dtype}
            clip = {"name": clip_name, "type": clip_type}
            vae = {"name": vae_name}
            out_pipe = dict(pipe) if isinstance(pipe, dict) else {}
            out_pipe.update({
                "model": model,
                "clip": clip,
                "vae": vae,
                "unet_name": unet_name,
                "clip_name": clip_name,
                "vae_name": vae_name,
                "clip_type": clip_type,
                "positive": out_pipe.get("positive", None),
                "negative": out_pipe.get("negative", None),
                "latent": out_pipe.get("latent", None),
                "image": out_pipe.get("image", None),
                "images": out_pipe.get("images", None),
                "seed": out_pipe.get("seed", None),
            })
            return (model, clip, vae, out_pipe)

        # 1. Load UNET / DiT
        model_options = {}
        if weight_dtype == "fp8_e4m3fn":
            model_options["dtype"] = torch.float8_e4m3fn
        elif weight_dtype == "fp8_e4m3fn_fast":
            model_options["dtype"] = torch.float8_e4m3fn
            model_options["fp8_optimizations"] = True
        elif weight_dtype == "fp8_e5m2":
            model_options["dtype"] = torch.float8_e5m2

        unet_path = folder_paths.get_full_path_or_raise("diffusion_models", unet_name)
        model = comfy.sd.load_diffusion_model(unet_path, model_options=model_options)

        # 2. Load CLIP
        c_type = getattr(comfy.sd.CLIPType, clip_type.upper(), comfy.sd.CLIPType.STABLE_DIFFUSION)
        clip_options = {}
        if clip_device == "cpu":
            clip_options["load_device"] = clip_options["offload_device"] = torch.device("cpu")

        clip_path = folder_paths.get_full_path_or_raise("text_encoders", clip_name)
        emb_dirs = folder_paths.get_folder_paths("embeddings") if hasattr(folder_paths, "get_folder_paths") else []
        clip = comfy.sd.load_clip(
            ckpt_paths=[clip_path],
            embedding_directory=emb_dirs,
            clip_type=c_type,
            model_options=clip_options,
        )

        # 3. Load VAE
        try:
            import nodes as comfy_nodes
            vae = comfy_nodes.VAELoader().load_vae(vae_name)[0]
        except Exception:
            vae_path = folder_paths.get_full_path_or_raise("vae", vae_name)
            sd = comfy.utils.load_torch_file(vae_path)
            vae = comfy.sd.VAE(sd=sd)

        # 4. Construct STOIQO_PIPE (with rgthree context compatibility)
        stoiqo_pipe = dict(pipe) if isinstance(pipe, dict) else {}
        stoiqo_pipe.update({
            "model": model,
            "clip": clip,
            "vae": vae,
            "unet_name": unet_name,
            "clip_name": clip_name,
            "vae_name": vae_name,
            "clip_type": clip_type,
            "positive": stoiqo_pipe.get("positive", None),
            "negative": stoiqo_pipe.get("negative", None),
            "latent": stoiqo_pipe.get("latent", None),
            "image": stoiqo_pipe.get("image", None),
            "images": stoiqo_pipe.get("images", None),
            "seed": stoiqo_pipe.get("seed", None),
        })

        return (model, clip, vae, stoiqo_pipe)
