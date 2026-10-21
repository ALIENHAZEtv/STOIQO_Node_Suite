"""
[STOIQO] Turbo Sampler & Direct Decoder Node
All-in-one high-performance generation pipeline tailored for rapid models like Krea 2 Turbo.
Consolidates Empty Latent creation, Prompt Encoding, Negative Zero-Out, KSampler, and VAE Decode
into a single responsive node.
"""

import torch

try:
    import comfy.samplers
    import comfy.sample
    import comfy.model_management
    import comfy.utils
    from nodes import common_ksampler
except ImportError:
    comfy = None
    common_ksampler = None

try:
    from ..core.telemetry import NodeTelemetryTimer, inject_telemetry
except (ImportError, ValueError):
    from core.telemetry import NodeTelemetryTimer, inject_telemetry



class StoiqoTurboSamplerNode:
    """
    [STOIQO] Turbo Sampler & Direct Decoder
    Accelerated end-to-end generation node. Takes prompts and models (or STOIQO_PIPE),
    performs prompt encoding, latent sampling, and VAE decoding in one pass.
    """

    @classmethod
    def INPUT_TYPES(cls):
        samplers = comfy.samplers.KSampler.SAMPLERS if comfy is not None else ["euler", "euler_ancestral", "dpmpp_2m"]
        schedulers = comfy.samplers.KSampler.SCHEDULERS if comfy is not None else ["simple", "normal", "karras", "sgm_uniform"]

        return {
            "required": {
                "positive_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "dynamicPrompts": True,
                        "default": "A high-end commercial photo of an elegant subject, dramatic studio lighting, 8k resolution, crisp details.",
                        "tooltip": "Positive prompt text description.",
                    },
                ),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "control_after_generate": True,
                        "tooltip": "Random seed (connect Stoiqo Seed Controller or set directly).",
                    },
                ),
                "steps": (
                    "INT",
                    {
                        "default": 4,
                        "min": 1,
                        "max": 100,
                        "step": 1,
                        "tooltip": "Inference steps (default: 4 for Krea 2 Turbo).",
                    },
                ),
                "cfg": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.0,
                        "max": 30.0,
                        "step": 0.1,
                        "round": 0.01,
                        "tooltip": "Classifier-Free Guidance scale (1.0 for Krea 2 Turbo).",
                    },
                ),
                "sampler_name": (samplers, {"default": "euler", "tooltip": "Sampling algorithm."}),
                "scheduler": (schedulers, {"default": "simple", "tooltip": "Noise schedule."}),
                "width": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 64,
                        "max": 8192,
                        "step": 8,
                        "tooltip": "Generation width in pixels (or connect Stoiqo Resolution Node).",
                    },
                ),
                "height": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 64,
                        "max": 8192,
                        "step": 8,
                        "tooltip": "Generation height in pixels (or connect Stoiqo Resolution Node).",
                    },
                ),
                "negative_mode": (
                    [
                        "Zero-Out (Recommended for Krea 2 Turbo)",
                        "Text Encoded",
                        "None",
                    ],
                    {"default": "Zero-Out (Recommended for Krea 2 Turbo)", "tooltip": "Negative conditioning mode: Zero-Out avoids color burns with CFG=1.0."},
                ),
                "negative_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "dynamicPrompts": True,
                        "default": "",
                        "tooltip": "Optional negative prompt text (used when negative_mode is Text Encoded).",
                    },
                ),
                "denoise": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.01,
                        "tooltip": "Denoising strength (1.0 for txt2img; <1.0 for img2img refinement).",
                    },
                ),
            },
            "optional": {
                "model": ("MODEL", {"tooltip": "Diffusion model (optional if pipe or stoiqo_pipe is provided)."}),
                "clip": ("CLIP", {"tooltip": "Text encoder / CLIP (optional if pipe or stoiqo_pipe is provided)."}),
                "vae": ("VAE", {"tooltip": "Variational Auto-Encoder (optional if pipe or stoiqo_pipe is provided)."}),
                "pipe": ("*", {"tooltip": "Universal Pipeline / Context connection (compatible with STOIQO_PIPE, rgthree CONTEXT, or Impact pipe dict)."}),
                "stoiqo_pipe": ("STOIQO_PIPE", {"tooltip": "Legacy STOIQO pipeline bundle from Tri-Model Loader Hub."}),
                "latent_image": ("LATENT", {"tooltip": "Optional input latent for img2img or multi-stage refining."}),
                "freeu_mode": (
                    [
                        "Disabled",
                        "SDXL Optimal (b1=1.3, b2=1.4, s1=0.6, s2=0.4)",
                        "SD1.5 / Turbo (b1=1.15, b2=1.2, s1=0.9, s2=0.2)",
                        "Gentle Clarity (b1=1.1, b2=1.15, s1=0.95, s2=0.85)",
                        "Custom",
                    ],
                    {"default": "Disabled", "tooltip": "FreeU v2 feature map enhancement for crisp textures with 0 extra VRAM (#95)."},
                ),
                "freeu_b1": ("FLOAT", {"default": 1.3, "min": 0.0, "max": 10.0, "step": 0.01, "tooltip": "FreeU Backbone 1 scale."}),
                "freeu_b2": ("FLOAT", {"default": 1.4, "min": 0.0, "max": 10.0, "step": 0.01, "tooltip": "FreeU Backbone 2 scale."}),
                "freeu_s1": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 10.0, "step": 0.01, "tooltip": "FreeU Skip 1 scale."}),
                "freeu_s2": ("FLOAT", {"default": 0.4, "min": 0.0, "max": 10.0, "step": 0.01, "tooltip": "FreeU Skip 2 scale."}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    @staticmethod
    def _apply_freeu_v2(model, mode: str, b1: float = 1.3, b2: float = 1.4, s1: float = 0.6, s2: float = 0.4):
        """FreeU v2 feature map rescaling on U-Net blocks (zero computational cost, zero extra VRAM)."""
        if mode == "Disabled" or model is None:
            return model
        if "SDXL" in mode:
            b1, b2, s1, s2 = 1.3, 1.4, 0.6, 0.4
        elif "SD1.5" in mode:
            b1, b2, s1, s2 = 1.15, 1.20, 0.90, 0.20
        elif "Gentle" in mode:
            b1, b2, s1, s2 = 1.10, 1.15, 0.95, 0.85

        if not hasattr(model, "clone") or not hasattr(model, "set_model_output_block_patch"):
            return model

        try:
            model_channels = getattr(getattr(getattr(model, "model", None), "model_config", None), "unet_config", {}).get("model_channels")
            if not model_channels:
                return model

            scale_dict = {model_channels * 4: (b1, s1), model_channels * 2: (b2, s2)}
            on_cpu_devices = {}

            def _fourier_filter(x, threshold, scale):
                x_freq = torch.fft.fftn(x.float(), dim=(-2, -1))
                x_freq = torch.fft.fftshift(x_freq, dim=(-2, -1))
                B, C, H, W = x_freq.shape
                mask = torch.ones((B, C, H, W), device=x.device)
                crow, ccol = H // 2, W // 2
                mask[..., crow - threshold : crow + threshold, ccol - threshold : ccol + threshold] = scale
                x_freq = x_freq * mask
                x_freq = torch.fft.ifftshift(x_freq, dim=(-2, -1))
                x_filtered = torch.fft.ifftn(x_freq, dim=(-2, -1)).real
                return x_filtered.to(x.dtype)

            def output_block_patch(h, hsp, transformer_options):
                scale = scale_dict.get(int(h.shape[1]), None)
                if scale is not None:
                    hidden_mean = h.mean(1).unsqueeze(1)
                    B = hidden_mean.shape[0]
                    hidden_max, _ = torch.max(hidden_mean.view(B, -1), dim=-1, keepdim=True)
                    hidden_min, _ = torch.min(hidden_mean.view(B, -1), dim=-1, keepdim=True)
                    denom = (hidden_max - hidden_min).unsqueeze(2).unsqueeze(3)
                    if (denom > 0).all():
                        hidden_mean = (hidden_mean - hidden_min.unsqueeze(2).unsqueeze(3)) / denom

                    h[:, : h.shape[1] // 2] = h[:, : h.shape[1] // 2] * ((scale[0] - 1) * hidden_mean + 1)

                    if hsp.device not in on_cpu_devices:
                        try:
                            hsp = _fourier_filter(hsp, threshold=1, scale=scale[1])
                        except Exception:
                            on_cpu_devices[hsp.device] = True
                            hsp = _fourier_filter(hsp.cpu(), threshold=1, scale=scale[1]).to(hsp.device)
                    else:
                        hsp = _fourier_filter(hsp.cpu(), threshold=1, scale=scale[1]).to(hsp.device)

                return h, hsp

            m = model.clone()
            m.set_model_output_block_patch(output_block_patch)
            return m
        except Exception:
            return model

    RETURN_TYPES = ("IMAGE", "LATENT", "STOIQO_PIPE")
    RETURN_NAMES = ("image", "latent", "stoiqo_pipe")
    FUNCTION = "sample_and_decode"
    CATEGORY = "STOIQO"

    def sample_and_decode(
        self,
        positive_prompt: str,
        seed: int,
        steps: int,
        cfg: float,
        sampler_name: str,
        scheduler: str,
        width: int,
        height: int,
        negative_mode: str,
        negative_prompt: str,
        denoise: float = 1.0,
        model=None,
        clip=None,
        vae=None,
        pipe=None,
        stoiqo_pipe=None,
        latent_image=None,
        freeu_mode: str = "Disabled",
        freeu_b1: float = 1.3,
        freeu_b2: float = 1.4,
        freeu_s1: float = 0.6,
        freeu_s2: float = 0.4,
        unique_id=None,
        prompt=None,
        extra_pnginfo=None,
    ):
        with NodeTelemetryTimer(node_id=unique_id, node_name="TurboSampler") as timer:
            # Resolve model, clip, vae, latent, prompts from input pins or pipe (STOIQO / rgthree / Impact)
            in_pipe = pipe if pipe is not None else stoiqo_pipe
            if in_pipe is not None and isinstance(in_pipe, dict):
                if model is None:
                    model = in_pipe.get("model")
                if clip is None:
                    clip = in_pipe.get("clip")
                if vae is None:
                    vae = in_pipe.get("vae")
                if latent_image is None:
                    latent_image = in_pipe.get("latent") or in_pipe.get("latent_image") or in_pipe.get("samples")
                if not positive_prompt or positive_prompt.strip() == "":
                    positive_prompt = in_pipe.get("positive_prompt") or in_pipe.get("text") or in_pipe.get("text_pos") or ""
                if not negative_prompt or negative_prompt.strip() == "":
                    negative_prompt = in_pipe.get("negative_prompt") or in_pipe.get("text_neg") or ""

            if model is None:
                raise ValueError("[STOIQO Turbo Sampler] Diffusion MODEL is required (connect model pin or pipe).")
            if clip is None:
                raise ValueError("[STOIQO Turbo Sampler] CLIP text encoder is required (connect clip pin or pipe).")
            if vae is None:
                raise ValueError("[STOIQO Turbo Sampler] VAE is required for direct decoding (connect vae pin or pipe).")

            # Headless testing mock fallback
            if comfy is None or common_ksampler is None:
                mock_img = torch.zeros((1, height, width, 3), dtype=torch.float32)
                mock_lat = {"samples": torch.zeros((1, 4, height // 8, width // 8), dtype=torch.float32)}
                out_pipe = dict(in_pipe) if isinstance(in_pipe, dict) else {}
                out_pipe.update({
                    "model": model,
                    "clip": clip,
                    "vae": vae,
                    "image": mock_img,
                    "images": mock_img,
                    "latent": mock_lat,
                    "positive": in_pipe.get("positive", None) if isinstance(in_pipe, dict) else None,
                    "negative": in_pipe.get("negative", None) if isinstance(in_pipe, dict) else None,
                    "positive_prompt": positive_prompt,
                    "text": positive_prompt,
                    "text_pos": positive_prompt,
                    "negative_prompt": negative_prompt,
                    "text_neg": negative_prompt,
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": sampler_name,
                    "scheduler": scheduler,
                    "denoise": denoise,
                    "width": width,
                    "height": height,
                })
                return inject_telemetry((mock_img, mock_lat, out_pipe), timer.get_stats())

            # 1. Prepare Latent
            if latent_image is not None and "samples" in latent_image:
                active_latent = latent_image
            else:
                dev = comfy.model_management.intermediate_device()
                dt = comfy.model_management.intermediate_dtype()
                blank_samples = torch.zeros([1, 4, height // 8, width // 8], device=dev, dtype=dt)
                active_latent = {"samples": blank_samples, "downscale_ratio_spacial": 8}

            # 2. Encode Positive Prompt
            pos_tokens = clip.tokenize(positive_prompt)
            positive_cond = clip.encode_from_tokens_scheduled(pos_tokens)

            # 3. Encode / Zero-Out Negative Conditioning
            if negative_mode == "Zero-Out (Recommended for Krea 2 Turbo)":
                c_zero = []
                for t in positive_cond:
                    d = t[1].copy()
                    if "pooled_output" in d and d["pooled_output"] is not None:
                        d["pooled_output"] = torch.zeros_like(d["pooled_output"])
                    if "conditioning_lyrics" in d and d["conditioning_lyrics"] is not None:
                        d["conditioning_lyrics"] = torch.zeros_like(d["conditioning_lyrics"])
                    c_zero.append([torch.zeros_like(t[0]), d])
                negative_cond = c_zero
            elif negative_mode == "Text Encoded" and negative_prompt.strip():
                neg_tokens = clip.tokenize(negative_prompt)
                negative_cond = clip.encode_from_tokens_scheduled(neg_tokens)
            else:
                # Empty / None negative
                neg_tokens = clip.tokenize("")
                negative_cond = clip.encode_from_tokens_scheduled(neg_tokens)

            # 4. Apply FreeU v2 feature map enhancement if active
            sampling_model = self._apply_freeu_v2(model, freeu_mode, freeu_b1, freeu_b2, freeu_s1, freeu_s2)

            # 5. Perform KSampler execution
            sampled_latent_tuple = common_ksampler(
                model=sampling_model,
                seed=seed,
                steps=steps,
                cfg=cfg,
                sampler_name=sampler_name,
                scheduler=scheduler,
                positive=positive_cond,
                negative=negative_cond,
                latent=active_latent,
                denoise=denoise,
            )
            sampled_latent = sampled_latent_tuple[0]

            # 5. Direct VAE Decode
            lat_tensor = sampled_latent["samples"]
            if hasattr(lat_tensor, "is_nested") and lat_tensor.is_nested:
                lat_tensor = lat_tensor.unbind()[0]

            decoded_images = vae.decode(lat_tensor)
            if len(decoded_images.shape) == 5:
                decoded_images = decoded_images.reshape(-1, decoded_images.shape[-3], decoded_images.shape[-2], decoded_images.shape[-1])

            # 6. Update STOIQO_PIPE & rgthree Context compatible pipe
            out_pipe = dict(in_pipe) if isinstance(in_pipe, dict) else {}
            out_pipe.update({
                "model": model,
                "clip": clip,
                "vae": vae,
                "latent": sampled_latent,
                "image": decoded_images,
                "images": decoded_images,
                "positive": positive_cond if "positive_cond" in locals() else None,
                "negative": negative_cond if "negative_cond" in locals() else None,
                "positive_prompt": positive_prompt,
                "text": positive_prompt,
                "text_pos": positive_prompt,
                "negative_prompt": negative_prompt,
                "text_neg": negative_prompt,
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "denoise": denoise,
                "width": width,
                "height": height,
            })

            return inject_telemetry((decoded_images, sampled_latent, out_pipe), timer.get_stats())

