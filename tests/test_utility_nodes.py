"""
[STOIQO] Unit Tests — Utility Nodes Suite
Validates:
1. StoiqoImageCompareNode (Visual Compare Slider & Zoom)
2. StoiqoTextConcatenateNode (Prompt Concatenation, Tag Deduplication & Token Counter)
3. StoiqoProImageSaverNode (Pro Image Export, Token Resolution & Sidecars)
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json
import torch

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

comfy_path = os.environ.get("COMFYUI_PATH", "")
if comfy_path and os.path.isdir(comfy_path) and comfy_path not in sys.path:
    sys.path.append(comfy_path)

try:
    from nodes.image_compare_node import StoiqoImageCompareNode
    from nodes.text_concat_node import StoiqoTextConcatenateNode
    from nodes.pro_saver_node import StoiqoProImageSaverNode, _resolve_tokens
    from nodes.resolution_node import StoiqoResolutionNode
    from nodes.seed_node import StoiqoSeedControllerNode
    from nodes.audio_saver_node import StoiqoAudioSaverNode
    from nodes.video_saver_node import StoiqoVideoSaverNode
    from nodes.inpaint_stitcher_node import StoiqoInpaintStitcherNode
    from nodes.watermark_node import StoiqoWatermarkNode
    from nodes.tri_loader_hub_node import StoiqoTriLoaderHubNode
    from nodes.turbo_sampler_node import StoiqoTurboSamplerNode
    from nodes.style_directives_node import StoiqoStyleDirectivesNode
    from nodes.sampling_options_node import StoiqoSamplingOptionsNode
    from nodes.multi_image_context_node import StoiqoMultiImageContextNode
    from nodes.prompt_synthesizer_node import StoiqoPromptSynthesizerNode
    COMFY_LOADED = True
except Exception as _e:
    _IMPORT_ERROR = str(_e)
    COMFY_LOADED = False


class TestUtilityNodes(unittest.TestCase):

    def setUp(self):
        if not COMFY_LOADED:
            self.skipTest(f"ComfyUI engine environment not fully initialized: {_IMPORT_ERROR}")

    # ── 1. Image Compare Node Tests ─────────────────────────────
    def test_image_compare_node(self):
        node = StoiqoImageCompareNode()
        img_a = torch.zeros((1, 256, 256, 3), dtype=torch.float32)
        img_b = torch.ones((1, 256, 256, 3), dtype=torch.float32)

        res = node.compare_images(img_a, img_b)
        self.assertIn("ui", res)
        self.assertIn("stoiqo_images", res["ui"])
        self.assertEqual(len(res["ui"]["stoiqo_images"]), 2)
        self.assertEqual(res["result"][0].shape, (1, 256, 256, 3))
        self.assertEqual(res["result"][1].shape, (1, 256, 256, 3))

    # ── 2. Text Concatenate Node Tests ──────────────────────────
    def test_text_concatenate_basic(self):
        node = StoiqoTextConcatenateNode()
        res = node.concatenate(
            text_1="masterpiece, highly detailed portrait",
            text_2="cyberpunk neon lighting, 8k resolution",
            separator=",  (Comma Space)"
        )
        self.assertIn("ui", res)
        self.assertIn("result", res)

        text, words, chars, tokens = res["result"]
        self.assertEqual(text, "masterpiece, highly detailed portrait, cyberpunk neon lighting, 8k resolution")
        self.assertGreater(words, 5)
        self.assertGreater(tokens, 5)

    def test_text_concatenate_deduplication(self):
        node = StoiqoTextConcatenateNode()
        res = node.concatenate(
            text_1="1girl, blue eyes, masterpiece",
            text_2="blue eyes, wet hair, 1GIRL, 8k",
            separator=",  (Comma Space)",
            deduplicate_tags="Case-Insensitive"
        )
        text = res["result"][0]
        self.assertEqual(text, "1girl, blue eyes, masterpiece, wet hair, 8k")

    def test_text_concatenate_syntax_cleanup(self):
        node = StoiqoTextConcatenateNode()
        res = node.concatenate(
            text_1="portrait of girl , , with blue_eyes",
            text_2="<lora:cyber_v1:0.8> , neon_city",
            separator=",  (Comma Space)",
            clean_whitespace=True,
            convert_underscores=True
        )
        text = res["result"][0]
        self.assertIn("blue eyes", text)
        self.assertIn("<lora:cyber_v1:0.8>", text)  # LoRA preserved
        self.assertIn("neon city", text)
        self.assertNotIn(" ,", text)
        self.assertNotIn(", ,", text)

    # ── 3. Resolution Node Tests (Krea 2, SeedVR2, MiniMax) ────
    def test_resolution_node_modern_targets(self):
        node = StoiqoResolutionNode()
        # Krea 2 Standard (1:1)
        w, h, ratio, res_str = node.get_resolution(
            aspect_ratio="1:1 Square (1024 x 1024)",
            scale_target="1.0 MP - Krea 2 Standard (1024 base)",
            multiple_of=16,
        )
        self.assertEqual(w, 1024)
        self.assertEqual(h, 1024)
        self.assertEqual(w % 16, 0)
        self.assertEqual(h % 16, 0)

        # SeedVR2 4x / 4K UHD Master (16:9)
        w, h, ratio, res_str = node.get_resolution(
            aspect_ratio="16:9 Landscape Widescreen (1344 x 768)",
            scale_target="4.0 MP - SeedVR2 4x / 4K UHD Master (2160 base)",
            multiple_of=16,
        )
        self.assertGreaterEqual(w, 2800)
        self.assertEqual(w % 16, 0)
        self.assertEqual(h % 16, 0)

        # MiniMax 720p Video (16:9)
        w, h, ratio, res_str = node.get_resolution(
            aspect_ratio="16:9 Landscape Widescreen (1344 x 768)",
            scale_target="0.9 MP - MiniMax 720p Video (1280 base)",
            multiple_of=16,
        )
        self.assertEqual(w % 16, 0)
        self.assertEqual(h % 16, 0)
        self.assertAlmostEqual(w / h, 16.0 / 9.0, delta=0.1)

    # ── 4. Pro Image Saver Tests ────────────────────────────────
    def test_pro_saver_token_resolution(self):
        meta = {
            "seed": 424242,
            "steps": 25,
            "cfg": 7.0,
            "sampler_name": "euler_ancestral",
            "model_name": "CyberRealistic_v5",
        }
        pattern = "Render_%seed%_%sampler%_%width%x%height%_%counter%"
        res = _resolve_tokens(pattern, 512, 768, meta, counter=7)
        self.assertIn("424242", res)
        self.assertIn("euler_ancestral", res)
        self.assertIn("512x768", res)
        self.assertIn("00007", res)

    def test_pro_saver_export_with_sidecars(self):
        saver = StoiqoProImageSaverNode()
        test_tensor = torch.zeros((1, 128, 128, 3), dtype=torch.float32)

        subfolder = "test_run_suite"
        result = saver.save_images_pro(
            images=test_tensor,
            filename_prefix="test_unit_%seed%",
            format="PNG (Lossless)",
            quality=90,
            subfolder=subfolder,
            sidecar_metadata="Both (.json + .txt)",
            prompt_text="A scenic sunset over mountain range",
            negative_text="blurry, low quality",
            save_workflow=False,
        )

        out_images, out_filepath, out_filename, out_folder, out_meta_json = result["result"]
        self.assertTrue(os.path.exists(out_filepath))
        self.assertTrue(out_filename.endswith(".png"))

        # Verify ui images payload for ComfyUI sidebar and UI preview
        self.assertIn("ui", result)
        self.assertIn("images", result["ui"])
        self.assertEqual(len(result["ui"]["images"]), 1)
        self.assertEqual(result["ui"]["images"][0]["filename"], out_filename)
        self.assertEqual(result["ui"]["images"][0]["subfolder"], subfolder)
        self.assertEqual(result["ui"]["images"][0]["type"], "output")

        # Check sidecars
        base_path = os.path.splitext(out_filepath)[0]
        json_path = base_path + ".json"
        txt_path = base_path + ".txt"
        self.assertTrue(os.path.exists(json_path))
        self.assertTrue(os.path.exists(txt_path))

        # Cleanup test files
        try:
            os.remove(out_filepath)
            os.remove(json_path)
            os.remove(txt_path)
        except Exception:
            pass

    # ── 5. Seed Controller Tests ────────────────────────────────
    def test_seed_controller(self):
        node = StoiqoSeedControllerNode()
        # Fixed mode
        s, eff, v_str, s_str = node.resolve_seed(seed=42, control_mode="fixed", variance_strength=0.0)
        self.assertEqual(s, 42)
        self.assertEqual(eff, 42)
        self.assertEqual(s_str, "42")

        # Increment mode
        s, eff, v_str, s_str = node.resolve_seed(seed=42, control_mode="increment", variance_strength=0.0)
        self.assertEqual(s, 43)

        # Variance mode (Krea 2 perturbation)
        s, eff, v_str, s_str = node.resolve_seed(seed=100, control_mode="fixed", variance_strength=0.5, variance_seed=999)
        self.assertEqual(s, 100)
        self.assertNotEqual(eff, 100)

    # ── 6. Audio Saver Tests (YuE 2) ───────────────────────────
    def test_audio_saver_export(self):
        node = StoiqoAudioSaverNode()
        sample_rate = 44100
        # 0.5s stereo sine wave
        t = torch.linspace(0, 0.5, int(sample_rate * 0.5))
        sine = torch.sin(2 * 3.14159 * 440 * t)
        dummy_waveform = torch.stack([sine, sine], dim=0)
        audio_input = {"waveform": dummy_waveform, "sample_rate": sample_rate}

        subfolder = "test_run_audio"
        result = node.save_audio_pro(
            audio=audio_input,
            filename_prefix="test_yue2_%title%",
            format="WAV (Standard 16-bit)",
            subfolder=subfolder,
            title="Cosmic Drift",
            lyrics="[Verse 1]\nFloating in the neon sky",
            style="Synthwave, 120 BPM",
            bpm=120,
            sidecar_metadata="Both (.txt lyrics + .json)",
        )

        out_audio, out_filepath, out_filename, out_meta = result["result"]
        self.assertTrue(os.path.exists(out_filepath))
        self.assertIn("ui", result)
        self.assertIn("audio", result["ui"])
        self.assertEqual(result["ui"]["audio"][0]["filename"], out_filename)

        # Cleanup
        try:
            os.remove(out_filepath)
            os.remove(os.path.splitext(out_filepath)[0] + ".txt")
            os.remove(os.path.splitext(out_filepath)[0] + ".json")
        except Exception:
            pass

    # ── 7. Video Saver Tests (MiniMax) ─────────────────────────
    def test_video_saver_export(self):
        node = StoiqoVideoSaverNode()
        # 5 frames of 64x64 RGB
        dummy_frames = torch.zeros((5, 64, 64, 3), dtype=torch.float32)

        subfolder = "test_run_video"
        result = node.save_video_pro(
            images=dummy_frames,
            fps=24.0,
            filename_prefix="test_minimax_%fps%",
            format="GIF (Animated)",
            subfolder=subfolder,
            motion_prompt="Camera dolly-in smoothly towards subject",
            sidecar_metadata="Both (.json + .txt)",
        )

        out_imgs, out_filepath, out_filename, out_meta = result["result"]
        self.assertTrue(os.path.exists(out_filepath))
        self.assertIn("ui", result)
        self.assertIn("images", result["ui"])

        # Cleanup
        try:
            os.remove(out_filepath)
            os.remove(os.path.splitext(out_filepath)[0] + ".txt")
            os.remove(os.path.splitext(out_filepath)[0] + ".json")
        except Exception:
            pass

    # ── 8. Inpaint Stitcher Tests (Krea 2 / SeedVR2) ───────────
    def test_inpaint_stitcher(self):
        node = StoiqoInpaintStitcherNode()
        orig = torch.zeros((1, 200, 200, 3), dtype=torch.float32)
        # Edited patch filled with 1.0 (white)
        edited_crop = torch.ones((1, 50, 50, 3), dtype=torch.float32)
        bbox_info = json.dumps({
            "normalized_box": [0.25, 0.25, 0.75, 0.75],
            "crop_box": [50, 50, 150, 150],
        })

        composite, mask = node.stitch_composite(
            original_image=orig,
            edited_image=edited_crop,
            bbox_info=bbox_info,
            blend_mode="Sharp (Direct Insert)",
            feather_radius=0,
        )

        self.assertEqual(composite.shape, (1, 200, 200, 3))
        self.assertEqual(mask.shape, (1, 200, 200))
        # Center of patched area should be ~1.0
        self.assertGreater(composite[0, 100, 100, 0].item(), 0.9)
        # Background corner should be 0.0
        self.assertEqual(composite[0, 10, 10, 0].item(), 0.0)

    # ── 9. Smart Watermark Node Tests ─────────────────────────
    def test_watermark_node_placement_and_scaling(self):
        node = StoiqoWatermarkNode()
        base = torch.zeros((1, 800, 800, 3), dtype=torch.float32)
        # 100x100 white logo
        wm = torch.ones((1, 100, 100, 3), dtype=torch.float32)

        out_img, out_mask, info_str = node.apply_watermark(
            base_image=base,
            watermark_image=wm,
            position="Bottom-Right",
            scale_mode="1/8 (Default)",
            margin_percent=0.02,
            opacity=0.8,
            remove_bg_mode="None (Use Alpha/RGB)",
        )

        self.assertEqual(out_img.shape, (1, 800, 800, 3))
        self.assertEqual(out_mask.shape, (1, 800, 800))
        info = json.loads(info_str)
        self.assertEqual(info["target_width"], 100)  # 800 * 1/8 = 100
        self.assertEqual(info["position"], "Bottom-Right")
        # In bottom-right corner, pixel should be scaled by opacity 0.8
        self.assertAlmostEqual(out_img[0, info["pos_y"] + 10, info["pos_x"] + 10, 0].item(), 0.8, places=2)
        # Top-left corner should be unaffected 0.0
        self.assertEqual(out_img[0, 10, 10, 0].item(), 0.0)

    # ── 10. Tri-Model Loader Hub Tests ────────────────────────
    def test_tri_loader_hub_structure(self):
        node = StoiqoTriLoaderHubNode()
        model, clip, vae, pipe = node.load_tri_models(
            unet_name="krea2_turbo.safetensors",
            weight_dtype="default",
            clip_name="qwen2_5_vl.safetensors",
            clip_type="krea2",
            vae_name="ae.safetensors",
            clip_device="default",
        )
        self.assertIsNotNone(model)
        self.assertIsNotNone(clip)
        self.assertIsNotNone(vae)
        self.assertIn("model", pipe)
        self.assertIn("clip", pipe)
        self.assertIn("vae", pipe)
        self.assertEqual(pipe["clip_type"], "krea2")

    # ── 11. Turbo Sampler Node Tests ──────────────────────────
    def test_turbo_sampler_pipeline_mock(self):
        node = StoiqoTurboSamplerNode()
        # Test validation error when models missing
        with self.assertRaises(ValueError):
            node.sample_and_decode(
                positive_prompt="test prompt",
                seed=42,
                steps=4,
                cfg=1.0,
                sampler_name="euler",
                scheduler="simple",
                width=512,
                height=512,
                negative_mode="Zero-Out (Recommended for Krea 2 Turbo)",
                negative_prompt="",
                model=None,
            )

        # Test execution with mock models
        mock_model = {"type": "mock_unet"}
        mock_clip = {"type": "mock_clip"}
        mock_vae = {"type": "mock_vae"}

        img, lat, pipe = node.sample_and_decode(
            positive_prompt="cinematic studio portrait",
            seed=12345,
            steps=4,
            cfg=1.0,
            sampler_name="euler",
            scheduler="simple",
            width=512,
            height=512,
            negative_mode="Zero-Out (Recommended for Krea 2 Turbo)",
            negative_prompt="",
            model=mock_model,
            clip=mock_clip,
            vae=mock_vae,
        )
        self.assertEqual(img.shape, (1, 512, 512, 3))
        self.assertIn("samples", lat)
        self.assertEqual(pipe["seed"], 12345)

    # ── 12. Modular Prompt Engine Satellites Tests ────────────
    def test_modular_style_directives_node(self):
        node = StoiqoStyleDirectivesNode()
        res = node.build_style(
            system_prompt="Visual Prompt Synthesizer",
            prompt_type="Detailed Narrative (Long)",
            artistic_style="Photorealistic (Crisp, 8k)",
            custom_system_prompt="",
        )
        style = res[0]
        self.assertEqual(style["system_prompt"], "Visual Prompt Synthesizer")
        self.assertEqual(style["artistic_style"], "Photorealistic (Crisp, 8k)")

    def test_modular_sampling_options_node(self):
        node = StoiqoSamplingOptionsNode()
        res = node.build_sampling_options(
            temperature=0.75,
            top_p=0.85,
            top_k=50,
            repetition_penalty=1.15,
            max_new_tokens=2048,
            target_megapixel=1.2,
            seed=9999,
        )
        sampling = res[0]
        self.assertEqual(sampling["temperature"], 0.75)
        self.assertEqual(sampling["top_k"], 50)
        self.assertEqual(sampling["seed"], 9999)

    def test_modular_multi_image_context_node(self):
        node = StoiqoMultiImageContextNode()
        img1 = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
        img2 = torch.ones((1, 64, 64, 3), dtype=torch.float32)
        res = node.build_context(
            image_1=img1,
            image_2=img2,
            fusion_mode="Contextual Fusion (Blend Style & Subject)",
        )
        ctx = res[0]
        self.assertEqual(len(ctx["images"]), 2)
        self.assertIn("Fusion", ctx["fusion_mode"])

    def test_modular_prompt_synthesizer_node(self):
        node = StoiqoPromptSynthesizerNode()
        mock_vlm = {} # Will fallback to mock response
        res = node.synthesize_prompt(
            stoiqo_model=mock_vlm,
            user_directives="high-tech neon laboratory, glowing vials",
        )
        self.assertIn("ui", res)
        self.assertIn("result", res)
        prompt, tags, negative, raw = res["result"]
        self.assertEqual(len(prompt), 1)  # list outputs: one entry per image/job
        prompt, tags, negative = prompt[0], tags[0], negative[0]
        self.assertTrue(len(prompt) > 0)
        self.assertTrue(len(tags) > 0)
        self.assertTrue(len(negative) > 0)
        self.assertIn("neon laboratory", prompt)

    # ── 13. Watermark Node Tests (RGB & RGBA Channels) ────────
    def test_watermark_node_rgb_and_rgba(self):
        node = StoiqoWatermarkNode()
        base_img = torch.zeros((1, 256, 256, 3), dtype=torch.float32)

        # 1. RGB watermark test
        wm_rgb = torch.ones((1, 64, 64, 3), dtype=torch.float32)
        res_rgb = node.apply_watermark(
            base_image=base_img,
            watermark_image=wm_rgb,
            position="Bottom-Right",
            scale_mode="1/8 (Default)",
            opacity=0.8,
            remove_bg_mode="None (Preserve Full)",
        )
        out_img, out_mask, info_str = res_rgb
        self.assertEqual(out_img.shape, (1, 256, 256, 3))
        self.assertEqual(out_mask.shape, (1, 256, 256))
        self.assertIn("Bottom-Right", info_str)

        # 2. RGBA watermark test (Native 4th channel alpha)
        wm_rgba = torch.ones((1, 64, 64, 4), dtype=torch.float32)
        wm_rgba[:, :, :, 3] = 0.5  # half transparent alpha channel
        res_rgba = node.apply_watermark(
            base_image=base_img,
            watermark_image=wm_rgba,
            position="Top-Left",
            scale_mode="1/4",
            opacity=1.0,
        )
        out_img_rgba, out_mask_rgba, info_str_rgba = res_rgba
        self.assertEqual(out_img_rgba.shape, (1, 256, 256, 3))
        self.assertEqual(out_mask_rgba.shape, (1, 256, 256))
        self.assertIn("Top-Left", info_str_rgba)

    # ── 14. Killer Feature: SEGS Bridge Tests (Impact-Pack Interop) ──
    def test_spatial_cropper_segs_bridge(self):
        from nodes.spatial_cropper_node import StoiqoSpatialCropperNode
        node = StoiqoSpatialCropperNode()
        dummy_img = torch.zeros((1, 512, 512, 3), dtype=torch.float32)
        mock_model = MagicMock()
        mock_model.generate_single.return_value = '```json\n{"bbox_2d": [100, 100, 300, 300]}\n```'
        crop_img, crop_mask, crop_meta, segs = node.crop_and_mask(
            stoiqo_model=mock_model,
            image=dummy_img,
            detect_prompt="jewelry portrait",
            padding_percent=0,
            crop_shape="Tight Bounding Box",
        )
        self.assertEqual(crop_img.shape[0], 1)
        self.assertIsNotNone(segs)
        shape_tuple, seg_list = segs
        self.assertEqual(shape_tuple, (512, 512))
        self.assertEqual(len(seg_list), 1)
        first_seg = seg_list[0]
        self.assertEqual(first_seg.label, "jewelry portrait")
        self.assertEqual(first_seg.confidence, 0.99)
        self.assertTrue(hasattr(first_seg, "cropped_image"))
        self.assertTrue(hasattr(first_seg, "cropped_mask"))

    # ── 15. Killer Feature: rgthree Context Compatibility ───────
    def test_rgthree_context_pipe_compatibility(self):
        node = StoiqoTurboSamplerNode()
        mock_context = {
            "model": {"type": "mock_diffusion_model"},
            "clip": {"type": "mock_clip_encoder"},
            "vae": {"type": "mock_vae"},
            "text": "masterpiece, ultra-detailed portrait",
            "text_neg": "blurry, low quality",
            "seed": 98765,
        }
        img, lat, out_pipe = node.sample_and_decode(
            positive_prompt="",
            seed=0,
            steps=4,
            cfg=1.0,
            sampler_name="euler",
            scheduler="simple",
            width=256,
            height=256,
            negative_mode="Zero-Out (Recommended for Krea 2 Turbo)",
            negative_prompt="",
            pipe=mock_context,
        )
        self.assertEqual(img.shape, (1, 256, 256, 3))
        self.assertIn("images", out_pipe)
        self.assertIn("positive", out_pipe)
        self.assertIn("negative", out_pipe)
        self.assertEqual(out_pipe["positive_prompt"], "masterpiece, ultra-detailed portrait")
        self.assertEqual(out_pipe["negative_prompt"], "blurry, low quality")

    # ── 16. Killer Feature: Universal API Endpoint Resolution ───
    def test_model_manager_api_endpoint_resolution(self):
        from core import ModelManager, API_ENDPOINT_KEY
        mgr = ModelManager()
        resolved = mgr.resolve_model_repo(
            model_preset=API_ENDPOINT_KEY,
            local_model_path="http://localhost:11434/v1#qwen2.5-vl:7b"
        )
        self.assertTrue(resolved.startswith("api://"))
        self.assertIn("localhost:11434/v1", resolved)

        mgr.load_model(resolved, "none", "sdpa")
        self.assertTrue(getattr(mgr, "is_api_endpoint", False))
        self.assertEqual(mgr.model, "API_CLIENT")
        self.assertEqual(mgr.api_base_url, "http://localhost:11434/v1")
        self.assertEqual(mgr.api_model_name, "qwen2.5-vl:7b")

    def test_turbo_sampler_freeu_v2_rescaling(self):
        node = StoiqoTurboSamplerNode()
        # Test disabled pass-through
        dummy = {"mock": "model"}
        m_disabled = node._apply_freeu_v2(dummy, "Disabled")
        self.assertIs(m_disabled, dummy)

        # Test preset parameters resolution without crashing on mock
        m_sdxl = node._apply_freeu_v2(dummy, "SDXL Optimal (b1=1.3, b2=1.4, s1=0.6, s2=0.4)")
        self.assertIsNotNone(m_sdxl)


if __name__ == "__main__":
    unittest.main()

