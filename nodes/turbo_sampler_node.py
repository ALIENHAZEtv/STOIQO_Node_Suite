"""
[STOIQO] Turbo Sampler & Direct Decoder Node (All-in-One Generator)
End-to-end accelerated generation studio. Takes prompts and models (or pipe),
performs aspect ratio calculation, prompt encoding, latent sampling, and direct VAE decoding
with pure standard ComfyUI outputs: IMAGE, LATENT, SEED, WIDTH, HEIGHT.
"""

import math
import torch
import torch.nn.functional as F

try:
    import comfy.samplers
    import comfy.sample
except ImportError:
    comfy = None

try:
    from ..core.telemetry import NodeTelemetryTimer, inject_telemetry
except (ImportError, ValueError):
    from core.telemetry import NodeTelemetryTimer, inject_telemetry


def _fourier_filter(x, threshold, scale):
    """Auxiliary spatial Fourier domain filter for FreeU v2."""
    x_freq = torch.fft.fftn(x.float(), dim=(-2, -1))
    x_freq = torch.fft.fftshift(x_freq, dim=(-2, -1))
    B, C, H, W = x_freq.shape
    mask = torch.ones((B, C, H, W), device=x.device)
    crow, ccol = H // 2, W // 2
    mask[..., crow - threshold:crow + threshold, ccol - threshold:ccol + threshold] = scale
    x_freq = x_freq * mask
    x_freq = torch.fft.ifftshift(x_freq, dim=(-2, -1))
    return torch.fft.ifftn(x_freq, dim=(-2, -1)).real.to(dtype=x.dtype)


class StoiqoTurboSamplerNode:
    """
    [STOIQO] Turbo Sampler & Direct Decoder (All-in-One)
    Accelerated end-to-end generation studio. Performs aspect ratio presets, prompt encoding,
    latent sampling, and VAE decoding in one pass with standard outputs (IMAGE, LATENT, SEED, WIDTH, HEIGHT).
    """

    ASPECT_RATIO_PRESETS = [
        "1:1 Square (1024x1024)",
        "16:9 Landscape (1344x768)",
        "9:16 Portrait (768x1344)",
        "4:3 Classic (1152x864)",
        "3:4 Portrait (864x1152)",
        "21:9 Cinema (1536x640)",
        "Custom (Manual Width & Height)",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        samplers = comfy.samplers.KSampler.SAMPLERS if comfy is not None else ["euler", "euler_ancestral", "dpmpp_2m"]
        schedulers = comfy.samplers.KSampler.SCHEDULERS if comfy is not None else ["simple", "normal", "karras", "sgm_uniform", "beta"]

        return {
            "required": {
                "positive": (
                    "STRING",
                    {
                        "multiline": True,
                        "dynamicPrompts": True,
                        "default": "masterpiece, cinematic, 8k, highly detailed, photorealistic, dramatic studio lighting, intricate textures",
                        "tooltip": "Positive prompt text (type directly or connect from a prompt synthesizer / text node).",
                    },
                ),
                "negative": (
                    "STRING",
                    {
                        "multiline": True,
                        "dynamicPrompts": True,
                        "default": "",
                        "tooltip": "Negative prompt text. If left empty, automatically zeros out negative conditioning (ideal for Turbo/Krea2/Flux).",
                    },
                ),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "control_after_generate": True,
                        "tooltip": "Random seed (manual or connected from Seed Node).",
                    },
                ),
                "steps": (
                    "INT",
                    {
                        "default": 8,
                        "min": 1,
                        "max": 100,
                        "step": 1,
                        "tooltip": "Inference steps (default: 8 for Turbo / Krea 2).",
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
                        "tooltip": "Guidance scale (1.0 for Krea 2 Turbo / Flux).",
                    },
                ),
                "sampler_name": (samplers, {"default": "euler", "tooltip": "Sampling algorithm."}),
                "scheduler": (schedulers, {"default": "beta", "tooltip": "Noise schedule."}),
                "width": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 64,
                        "max": 8192,
                        "step": 8,
                        "tooltip": "Width in pixels (set manually or connected from Resolution Node).",
                    },
                ),
                "height": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 64,
                        "max": 8192,
                        "step": 8,
                        "tooltip": "Height in pixels (set manually or connected from Resolution Node).",
                    },
                ),
                "denoise": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.01,
                        "tooltip": "Denoising strength (1.0 for txt2img; <1.0 for img2img).",
                    },
                ),
            },
            "optional": {
                "model": ("MODEL", {"tooltip": "Diffusion model."}),
                "clip": ("CLIP", {"tooltip": "Text encoder / CLIP."}),
                "vae": ("VAE", {"tooltip": "Variational Auto-Encoder for direct decoding into IMAGE."}),
                "image": ("IMAGE", {"tooltip": "Optional input image for direct img2img."}),
                "latent_image": ("LATENT", {"tooltip": "Optional input latent for img2img or refining."}),
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
                model_channels = 320

            scale = (b1, s1) if mode != "Custom" else (b1, s1)
            scale2 = (b2, s2) if mode != "Custom" else (b2, s2)

            on_cpu_devices = {}

            def output_block_patch(h, hsp, transformer_options):
                ch = h.shape[1]
                if ch == model_channels * 4:
                    h[:, :ch // 2] = h[:, :ch // 2] * scale[0]
                    if hsp.device not in on_cpu_devices:
                        try:
                            hsp = _fourier_filter(hsp, threshold=1, scale=scale[1])
                        except Exception:
                            on_cpu_devices[hsp.device] = True
                            hsp = _fourier_filter(hsp.cpu(), threshold=1, scale=scale[1]).to(hsp.device)
                    else:
                        hsp = _fourier_filter(hsp.cpu(), threshold=1, scale=scale[1]).to(hsp.device)
                elif ch == model_channels * 2:
                    h[:, :ch // 2] = h[:, :ch // 2] * scale2[0]
                    if hsp.device not in on_cpu_devices:
                        try:
                            hsp = _fourier_filter(hsp, threshold=1, scale=scale2[1])
                        except Exception:
                            on_cpu_devices[hsp.device] = True
                            hsp = _fourier_filter(hsp.cpu(), threshold=1, scale=scale2[1]).to(hsp.device)
                    else:
                        hsp = _fourier_filter(hsp.cpu(), threshold=1, scale=scale2[1]).to(hsp.device)
                return h, hsp

            m = model.clone()
            m.set_model_output_block_patch(output_block_patch)
            return m
        except Exception:
            return model

    RETURN_TYPES = ("IMAGE", "LATENT", "INT", "INT", "INT")
    RETURN_NAMES = ("image", "latent", "seed", "width", "height")
    FUNCTION = "sample_and_decode"
    CATEGORY = "STOIQO"

    def sample_and_decode(
        self,
        positive: str = "",
        negative: str = "",
        seed: int = 0,
        steps: int = 8,
        cfg: float = 1.0,
        sampler_name: str = "euler",
        scheduler: str = "beta",
        width: int = 1024,
        height: int = 1024,
        denoise: float = 1.0,
        model=None,
        clip=None,
        vae=None,
        image=None,
        latent_image=None,
        unique_id=None,
        prompt=None,
        extra_pnginfo=None,
        positive_prompt: str = None,
        negative_prompt: str = None,
        negative_mode: str = None,
        pipe=None,
        stoiqo_pipe=None,
        freeu_mode: str = "Disabled",
        freeu_b1: float = 1.3,
        freeu_b2: float = 1.4,
        freeu_s1: float = 0.6,
        freeu_s2: float = 0.4,
        aspect_ratio: str = None,
        **kwargs,
    ):
        timer = NodeTelemetryTimer(node_id=unique_id, node_name="TurboSampler") if NodeTelemetryTimer else None
        if timer:
            timer.__enter__()

        # Resolve single source of truth for positive & negative
        resolved_positive = positive if (positive is not None and str(positive).strip() != "") else (positive_prompt or "")
        resolved_negative = negative if (negative is not None and str(negative).strip() != "") else (negative_prompt or "")

        # Resolve dimensions (strictly use width and height directly, aligned to 8-pixel VAE multiples)
        target_width = max(64, int((int(width) // 8) * 8))
        target_height = max(64, int((int(height) // 8) * 8))

        # Guard denoise strength: in pure txt2img (no image and no latent input),
        # denoise must be > 0.0. If denoise <= 0.0, ksampler executes 0 steps, leaving
        # an untouched zero-latent that decodes into a flat gray image.
        if (image is None and latent_image is None) and (denoise is None or float(denoise) <= 0.0):
            print("[STOIQO Turbo Sampler] WARNING: 'denoise' was 0.0 on pure txt2img. Resetting to 1.0 to prevent gray blank image.")
            denoise = 1.0

        # Unpack pipeline bundle if connected
        in_pipe = pipe if pipe is not None else stoiqo_pipe
        if in_pipe is not None and isinstance(in_pipe, dict):
            model = model if model is not None else in_pipe.get("model")
            clip = clip if clip is not None else in_pipe.get("clip")
            vae = vae if vae is not None else in_pipe.get("vae")
            positive = positive if positive is not None else (in_pipe.get("positive_cond") or in_pipe.get("positive"))
            negative = negative if negative is not None else (in_pipe.get("negative_cond") or in_pipe.get("negative"))
            latent_image = latent_image if latent_image is not None else (in_pipe.get("latent_image") or in_pipe.get("latent"))
            image = image if image is not None else (in_pipe.get("image") or in_pipe.get("images"))
            if not positive_prompt and "positive_prompt" in in_pipe:
                positive_prompt = str(in_pipe["positive_prompt"])
            elif not positive_prompt and "text" in in_pipe:
                positive_prompt = str(in_pipe["text"])
            if (seed == 0 or seed is None) and "seed" in in_pipe and in_pipe["seed"] is not None:
                seed = int(in_pipe["seed"])

        # Fallback Mock / Offline test mode
        if comfy is None or not hasattr(comfy, "sample") or not hasattr(comfy.sample, "sample") or isinstance(model, dict):
            if model is None:
                raise ValueError("[STOIQO Turbo Sampler] Neither 'model' nor valid 'pipe' was provided.")
            mock_samples = torch.zeros((1, 4, target_height // 8, target_width // 8), dtype=torch.float32)
            mock_latent = {"samples": mock_samples}
            mock_image = torch.zeros((1, target_height, target_width, 3), dtype=torch.float32)
            return inject_telemetry(
                (mock_image, mock_latent, int(seed), int(target_width), int(target_height)),
                timer.get_stats() if timer else None,
            )

        try:
            import nodes
            common_ksampler = nodes.common_ksampler
        except Exception:
            try:
                from nodes import common_ksampler
            except Exception:
                common_ksampler = None

        if common_ksampler is None:
            def _fallback_ksampler(model, seed, steps, cfg, sampler_name, scheduler, positive, negative, latent, denoise=1.0, disable_noise=False, start_step=None, last_step=None, force_full_denoise=False):
                latent_image = latent["samples"]
                if hasattr(comfy.sample, "fix_empty_latent_channels"):
                    latent_image = comfy.sample.fix_empty_latent_channels(
                        model, latent_image, latent.get("downscale_ratio_spacial", None), latent.get("downscale_ratio_temporal", None)
                    )
                noise = comfy.sample.prepare_noise(latent_image, seed)
                samples = comfy.sample.sample(
                    model, noise, steps, cfg, sampler_name, scheduler, positive, negative, latent_image,
                    denoise=denoise, seed=seed
                )
                out = latent.copy()
                out["samples"] = samples
                return (out,)
            common_ksampler = _fallback_ksampler

        try:
            # 1. Determine Latent Source (image img2img vs latent_image vs empty latent)
            active_latent = None
            if image is not None and vae is not None:
                img_tensor = image
                if len(img_tensor.shape) == 5:
                    img_tensor = img_tensor.reshape(-1, img_tensor.shape[-3], img_tensor.shape[-2], img_tensor.shape[-1])
                target_img_h = (img_tensor.shape[1] // 8) * 8
                target_img_w = (img_tensor.shape[2] // 8) * 8
                if img_tensor.shape[1] != target_img_h or img_tensor.shape[2] != target_img_w:
                    img_perm = img_tensor.permute(0, 3, 1, 2)
                    img_resized = F.interpolate(img_perm, size=(target_img_h, target_img_w), mode="bilinear", align_corners=False)
                    img_tensor = img_resized.permute(0, 2, 3, 1)
                active_latent = {"samples": vae.encode(img_tensor[:, :, :, :3])}
            elif latent_image is not None:
                active_latent = latent_image
            else:
                # Dynamic latent channel detection (16 channels for Flux/SD3, 4 channels for SDXL/SD1.5)
                latent_channels = 4
                if model is not None:
                    inner_model = getattr(model, "model", model)
                    arch = getattr(inner_model, "latent_format", None)
                    if arch and hasattr(arch, "latent_channels"):
                        latent_channels = arch.latent_channels
                    elif hasattr(inner_model, "diffusion_model") and hasattr(inner_model.diffusion_model, "in_channels"):
                        latent_channels = inner_model.diffusion_model.in_channels

                device = comfy.model_management.intermediate_device() if (comfy and hasattr(comfy, "model_management")) else (model.load_device if hasattr(model, "load_device") else "cpu")
                latent_tensor = torch.zeros(
                    [1, latent_channels, target_height // 8, target_width // 8],
                    device=device,
                )
                active_latent = {"samples": latent_tensor, "downscale_ratio_spacial": 8}

            # 2. Positive Conditioning
            # 2. Positive Conditioning (Single Source of Truth)
            if isinstance(resolved_positive, (list, tuple)):
                positive_cond = resolved_positive
            else:
                if clip is None:
                    raise ValueError("[STOIQO Turbo Sampler] Missing 'clip' text encoder for positive prompt.")
                if not str(resolved_positive).strip():
                    print("[STOIQO Turbo Sampler] ⚠️ WARNING: Positive prompt is empty (''). Generation will proceed without text guidance (pure noise). Ensure 'positive' input is connected to your Prompt Generator or Concatenate node.")
                pos_tokens = clip.tokenize(str(resolved_positive))
                positive_cond = clip.encode_from_tokens_scheduled(pos_tokens)

            # 3. Negative Conditioning (Single Source of Truth)
            # If negative conditioning passed directly, use it.
            # If negative text provided, encode it.
            # Otherwise auto Zero-Out (safe for Krea 2 Turbo & Flux to prevent CFG burns).
            if isinstance(resolved_negative, (list, tuple)):
                negative_cond = resolved_negative
            elif isinstance(resolved_negative, str) and resolved_negative.strip() and clip is not None:
                neg_tokens = clip.tokenize(resolved_negative.strip())
                negative_cond = clip.encode_from_tokens_scheduled(neg_tokens)
            else:
                c_zero = []
                for t in positive_cond:
                    d = t[1].copy()
                    if "pooled_output" in d and d["pooled_output"] is not None:
                        d["pooled_output"] = torch.zeros_like(d["pooled_output"])
                    if "conditioning_lyrics" in d and d["conditioning_lyrics"] is not None:
                        d["conditioning_lyrics"] = torch.zeros_like(d["conditioning_lyrics"])
                    c_zero.append([torch.zeros_like(t[0]), d])
                negative_cond = c_zero

            # 4. Apply FreeU v2 feature map enhancement
            sampling_model = self._apply_freeu_v2(model, freeu_mode, freeu_b1, freeu_b2, freeu_s1, freeu_s2)

            # 5. Execute KSampler
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

            # 6. Direct VAE Decode
            if vae is not None:
                lat_tensor = sampled_latent["samples"]
                if hasattr(lat_tensor, "is_nested") and lat_tensor.is_nested:
                    lat_tensor = lat_tensor.unbind()[0]
                if hasattr(vae, "decode"):
                    decoded_images = vae.decode(lat_tensor)
                else:
                    decoded_images = torch.zeros((1, target_height, target_width, 3), dtype=torch.float32)
                if len(decoded_images.shape) == 5:
                    decoded_images = decoded_images.reshape(-1, decoded_images.shape[-3], decoded_images.shape[-2], decoded_images.shape[-1])
            else:
                decoded_images = torch.zeros((1, target_height, target_width, 3), dtype=torch.float32)

            return inject_telemetry(
                (decoded_images, sampled_latent, int(seed), int(target_width), int(target_height)),
                timer.get_stats() if timer else None,
            )
        finally:
            pass
