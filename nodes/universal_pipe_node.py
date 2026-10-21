"""
[STOIQO] Universal Context Pipe Nodes
Zero-friction workflow consolidation bus, fully compatible with rgthree Context,
Efficiency Nodes, and Impact Pack standard pipelines.
"""

from typing import Any, Dict, Optional, Tuple, Union


def _extract_pipe_data(pipe_input: Any) -> Dict[str, Any]:
    """
    Normalizes any incoming pipe structure (dict, tuple, list, or custom object)
    into a standard dictionary format.
    Supports rgthree Context, Efficiency Nodes PIPE_LINE, Impact Pack BASIC_PIPE,
    and STOIQO_PIPE.
    """
    data = {
        "model": None,
        "clip": None,
        "vae": None,
        "positive": None,
        "negative": None,
        "latent": None,
        "images": None,
        "seed": None,
        "extra": {},
    }

    if pipe_input is None:
        return data

    if isinstance(pipe_input, dict):
        data["model"] = pipe_input.get("model")
        data["clip"] = pipe_input.get("clip")
        data["vae"] = pipe_input.get("vae")
        data["positive"] = pipe_input.get("positive") or pipe_input.get("positive_prompt") or pipe_input.get("text_pos")
        data["negative"] = pipe_input.get("negative") or pipe_input.get("negative_prompt") or pipe_input.get("text_neg")
        data["latent"] = pipe_input.get("latent") or pipe_input.get("samples") or pipe_input.get("latent_image")
        data["images"] = pipe_input.get("images") or pipe_input.get("image")
        data["seed"] = pipe_input.get("seed")
        # Preserve extra keys
        for k, v in pipe_input.items():
            if k not in data and k != "extra":
                data["extra"][k] = v
        return data

    if isinstance(pipe_input, (tuple, list)):
        # Common convention for Impact Pack BASIC_PIPE: (model, clip, vae, positive, negative)
        # rgthree context tuple convention or Efficiency pipe: (model, clip, vae, positive, negative, latent, ...)
        length = len(pipe_input)
        if length >= 1:
            data["model"] = pipe_input[0]
        if length >= 2:
            data["clip"] = pipe_input[1]
        if length >= 3:
            data["vae"] = pipe_input[2]
        if length >= 4:
            data["positive"] = pipe_input[3]
        if length >= 5:
            data["negative"] = pipe_input[4]
        if length >= 6:
            data["latent"] = pipe_input[5]
        if length >= 7:
            data["images"] = pipe_input[6]
        if length >= 8:
            data["seed"] = pipe_input[7]
        return data

    # Object attribute fallback
    for field in ("model", "clip", "vae", "positive", "negative", "latent", "images", "seed"):
        if hasattr(pipe_input, field):
            data[field] = getattr(pipe_input, field)

    return data


class StoiqoUniversalPipeInNode:
    """
    [STOIQO] Universal Context Pipe (Packer & Bus)
    Merges multiple connections into a single universal pipeline bus (* / STOIQO_PIPE).
    Can receive an existing pipe to override or augment individual components.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "pipe": ("*", {"tooltip": "Existing pipeline bus (rgthree, Efficiency, Impact, or STOIQO) to merge/pass through."}),
                "model": ("MODEL", {"tooltip": "Diffusion model."}),
                "clip": ("CLIP", {"tooltip": "CLIP text encoder."}),
                "vae": ("VAE", {"tooltip": "Variational Auto-Encoder."}),
                "positive": ("CONDITIONING", {"tooltip": "Positive conditioning."}),
                "negative": ("CONDITIONING", {"tooltip": "Negative conditioning."}),
                "latent": ("LATENT", {"tooltip": "Latent representation."}),
                "images": ("IMAGE", {"tooltip": "Tensor image or batch."}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF, "tooltip": "Generation seed."}),
            },
        }

    RETURN_TYPES = ("*", "STOIQO_PIPE")
    RETURN_NAMES = ("pipe", "stoiqo_pipe")
    FUNCTION = "pack_pipe"
    CATEGORY = "STOIQO/Pipeline"

    def pack_pipe(
        self,
        pipe=None,
        model=None,
        clip=None,
        vae=None,
        positive=None,
        negative=None,
        latent=None,
        images=None,
        seed=None,
    ):
        base_data = _extract_pipe_data(pipe)

        # Override with explicit pin inputs if provided
        packed = {
            "model": model if model is not None else base_data["model"],
            "clip": clip if clip is not None else base_data["clip"],
            "vae": vae if vae is not None else base_data["vae"],
            "positive": positive if positive is not None else base_data["positive"],
            "negative": negative if negative is not None else base_data["negative"],
            "latent": latent if latent is not None else base_data["latent"],
            "images": images if images is not None else base_data["images"],
            "seed": seed if seed is not None else base_data["seed"],
        }
        if base_data.get("extra"):
            packed["extra"] = base_data["extra"]

        return (packed, packed)


class StoiqoUniversalPipeOutNode:
    """
    [STOIQO] Universal Context Pipe (Unpacker & Extractor)
    Unpacks any universal pipeline bus into individual ComfyUI output pins
    for standard connections.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "pipe": ("*", {"tooltip": "Universal pipeline bus (rgthree, Efficiency, Impact, or STOIQO)."}),
            },
        }

    RETURN_TYPES = (
        "*",
        "MODEL",
        "CLIP",
        "VAE",
        "CONDITIONING",
        "CONDITIONING",
        "LATENT",
        "IMAGE",
        "INT",
    )
    RETURN_NAMES = (
        "pipe",
        "model",
        "clip",
        "vae",
        "positive",
        "negative",
        "latent",
        "images",
        "seed",
    )
    FUNCTION = "unpack_pipe"
    CATEGORY = "STOIQO/Pipeline"

    def unpack_pipe(self, pipe=None):
        data = _extract_pipe_data(pipe)

        seed_val = data["seed"]
        if seed_val is None or not isinstance(seed_val, int):
            seed_val = 0

        return (
            pipe,
            data["model"],
            data["clip"],
            data["vae"],
            data["positive"],
            data["negative"],
            data["latent"],
            data["images"],
            seed_val,
        )
