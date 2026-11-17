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
from PIL import Image

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
    from nodes.audio_saver_node import StoiqoAudioSaverNode
    from nodes.video_saver_node import StoiqoVideoSaverNode
    from nodes.inpaint_stitcher_node import StoiqoInpaintStitcherNode
    from nodes.watermark_node import StoiqoWatermarkNode
    from nodes.turbo_sampler_node import StoiqoTurboSamplerNode
    from nodes.prompt_generator_node import StoiqoPromptGeneratorNode
    from nodes.show_prompt_node import StoiqoShowPromptNode
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
        # 1 from A + 1 from B + 1 Heatmap = 3 frames
        self.assertEqual(len(res["ui"]["stoiqo_images"]), 3)
        self.assertEqual(res["result"][0].shape, (1, 256, 256, 3))
        self.assertEqual(res["result"][1].shape, (1, 256, 256, 3))

    def test_image_compare_batch_mode(self):
        node = StoiqoImageCompareNode()
        img_a = torch.zeros((3, 128, 128, 3), dtype=torch.float32)
        img_b = torch.ones((2, 128, 128, 3), dtype=torch.float32)

        res = node.compare_images(img_a, img_b)
        self.assertIn("ui", res)
        self.assertIn("stoiqo_images", res["ui"])
        # 3 frames from A + 2 frames from B + 1 Heatmap = 6 frames
        self.assertEqual(len(res["ui"]["stoiqo_images"]), 6)
        names = [item["name"] for item in res["ui"]["stoiqo_images"]]
        self.assertIn("A1", names)
        self.assertIn("A2", names)
        self.assertIn("A3", names)
        self.assertIn("B1", names)
        self.assertIn("B2", names)
        self.assertIn("HEATMAP", names)

    def test_image_compare_single_input_batch(self):
        node = StoiqoImageCompareNode()
        # Single input tensor with 3 frames, image_b is None (rgthree style)
        img_a = torch.zeros((3, 128, 128, 3), dtype=torch.float32)
        res = node.compare_images(img_a, image_b=None)
        self.assertIn("ui", res)
        self.assertIn("stoiqo_images", res["ui"])
        # Frame 0 is A, frames 1 and 2 are B, plus 1 Heatmap = 4 frames
        self.assertEqual(len(res["ui"]["stoiqo_images"]), 4)
        self.assertEqual(res["result"][0].shape, (3, 128, 128, 3))
        self.assertEqual(res["result"][1].shape, (3, 128, 128, 3))

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

    def test_text_concatenate_template_and_list(self):
        node = StoiqoTextConcatenateNode()
        # Test template formatting
        res = node.concatenate(
            text_1="cyberpunk warrior",
            text_2="neon katanas",
            text_3="Tokyo 2099",
            separator=",  (Comma Space)",
            template="An epic portrait of {text_1} wielding {text_2} in {text_3}"
        )
        self.assertEqual(res["result"][0], "An epic portrait of cyberpunk warrior wielding neon katanas in Tokyo 2099")

        # Test list input flattening
        res_list = node.concatenate(
            text_1=["masterpiece", "8k"],
            text_2="vibrant sunset",
            separator=",  (Comma Space)"
        )
        self.assertEqual(res_list["result"][0], "masterpiece, 8k, vibrant sunset")

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

    def test_pro_saver_privacy_mode(self):
        saver = StoiqoProImageSaverNode()
        test_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32)

        subfolder = "test_run_privacy"
        result = saver.save_images_pro(
            images=test_tensor,
            filename_prefix="privacy_test",
            format="PNG (Lossless)",
            quality=90,
            subfolder=subfolder,
            sidecar_metadata="Both (.json + .txt)",
            prompt_text="Secret confidential prompt",
            negative_text="secret negative",
            save_workflow=True,
            privacy_mode=True,
        )

        out_images, out_filepath, out_filename, out_folder, out_meta_json = result["result"]
        self.assertTrue(os.path.exists(out_filepath))

        # Check that PNG metadata contains no parameters
        with Image.open(out_filepath) as img_opened:
            self.assertNotIn("parameters", img_opened.text)
            self.assertNotIn("prompt", img_opened.text)

        # Check sidecar JSON: no positive_prompt
        json_path = os.path.splitext(out_filepath)[0] + ".json"
        txt_path = os.path.splitext(out_filepath)[0] + ".txt"
        self.assertTrue(os.path.exists(json_path))
        # TXT caption is suppressed in privacy mode
        self.assertFalse(os.path.exists(txt_path))

        with open(json_path, "r", encoding="utf-8") as f:
            sidecar = json.load(f)
            self.assertTrue(sidecar.get("privacy_mode"))
            self.assertNotIn("positive_prompt", sidecar)

        # Cleanup
        try:
            os.remove(out_filepath)
            os.remove(json_path)
        except Exception:
            pass

    def test_pro_saver_jpeg_and_webp_exif_injection(self):
        saver = StoiqoProImageSaverNode()
        test_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32)

        subfolder = "test_run_exif"
        prompt_graph = {
            "3": {
                "class_type": "KSampler",
                "inputs": {"seed": 98765, "steps": 25, "cfg": 7.5, "sampler_name": "dpmpp_2m", "scheduler": "karras"},
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "cyberpunk_v2.safetensors"},
            }
        }
        extra_info = {"workflow": {"nodes": []}}

        # 1. JPEG test
        res_jpg = saver.save_images_pro(
            images=test_tensor,
            filename_prefix="exif_test_jpg",
            format="JPEG (Standard)",
            quality=95,
            subfolder=subfolder,
            sidecar_metadata="None",
            prompt_text="A neon cyberpunk warrior",
            negative_text="blurry, distorted",
            save_workflow=True,
            privacy_mode=False,
            prompt=prompt_graph,
            extra_pnginfo=extra_info,
        )
        jpg_path = res_jpg["result"][1]
        self.assertTrue(os.path.exists(jpg_path))
        with Image.open(jpg_path) as img_jpg:
            exif_jpg = img_jpg.getexif()
            self.assertIn(0x010E, exif_jpg)
            self.assertIn("A neon cyberpunk warrior", exif_jpg[0x010E])
            self.assertIn("Seed: 98765", exif_jpg[0x010E])
            self.assertIn(0x9286, exif_jpg)  # UserComment

        # 2. WEBP test
        res_webp = saver.save_images_pro(
            images=test_tensor,
            filename_prefix="exif_test_webp",
            format="WEBP (Quality)",
            quality=95,
            subfolder=subfolder,
            sidecar_metadata="None",
            prompt_text="A neon cyberpunk warrior",
            negative_text="blurry, distorted",
            save_workflow=True,
            privacy_mode=False,
            prompt=prompt_graph,
            extra_pnginfo=extra_info,
        )
        webp_path = res_webp["result"][1]
        self.assertTrue(os.path.exists(webp_path))
        with Image.open(webp_path) as img_webp:
            exif_webp = img_webp.getexif()
            self.assertIn(0x010E, exif_webp)
            self.assertIn("A neon cyberpunk warrior", exif_webp[0x010E])

        # Cleanup
        try:
            os.remove(jpg_path)
            os.remove(webp_path)
        except Exception:
            pass

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

    def test_audio_saver_formats_and_tokens(self):
        node = StoiqoAudioSaverNode()
        sample_rate = 44100
        t = torch.linspace(0, 0.25, int(sample_rate * 0.25))
        sine = torch.sin(2 * 3.14159 * 440 * t)
        dummy_waveform = torch.stack([sine, sine], dim=0)
        audio_input = {"waveform": dummy_waveform, "sample_rate": sample_rate}

        # 1. MP3 Export & Token resolution
        res_mp3 = node.save_audio_pro(
            audio=audio_input,
            filename_prefix="song_%genre%_%bpm%bpm",
            format="MP3 (320 kbps)",
            subfolder="test_audio_formats",
            title="Cyber Anthem",
            genre="Electro",
            bpm=128,
            sidecar_metadata="Both (.txt lyrics + .json)",
            lyrics="[Chorus]\nElectric heart",
        )
        _, mp3_path, mp3_name, mp3_meta = res_mp3["result"]
        self.assertTrue(os.path.exists(mp3_path))
        self.assertTrue(mp3_name.endswith(".mp3"))
        self.assertIn("Electro", mp3_name)
        self.assertIn("128bpm", mp3_name)
        self.assertGreater(os.path.getsize(mp3_path), 0)

        # 2. Collision resolution (second save must not overwrite, increments counter)
        res_mp3_2 = node.save_audio_pro(
            audio=audio_input,
            filename_prefix="song_%genre%_%bpm%bpm",
            format="MP3 (320 kbps)",
            subfolder="test_audio_formats",
            title="Cyber Anthem",
            genre="Electro",
            bpm=128,
            sidecar_metadata="None",
        )
        _, mp3_path_2, mp3_name_2, _ = res_mp3_2["result"]
        self.assertNotEqual(mp3_path, mp3_path_2)
        self.assertTrue(os.path.exists(mp3_path_2))

        # 3. FLAC Export
        res_flac = node.save_audio_pro(
            audio=audio_input,
            filename_prefix="track_flac",
            format="FLAC (Lossless)",
            subfolder="test_audio_formats",
            title="Acoustic Dream",
            sidecar_metadata="None",
        )
        _, flac_path, flac_name, _ = res_flac["result"]
        self.assertTrue(os.path.exists(flac_path))
        self.assertTrue(flac_name.endswith(".flac"))

        # 4. WAV 24-bit Export
        res_wav24 = node.save_audio_pro(
            audio=audio_input,
            filename_prefix="track_24bit",
            format="WAV (Lossless 24-bit)",
            subfolder="test_audio_formats",
            title="Studio Master",
            sidecar_metadata="None",
        )
        _, wav_path, wav_name, _ = res_wav24["result"]
        self.assertTrue(os.path.exists(wav_path))
        self.assertTrue(wav_name.endswith(".wav"))

        # Cleanup test files
        for p in [mp3_path, mp3_path_2, flac_path, wav_path]:
            try:
                if os.path.exists(p): os.remove(p)
                txt = os.path.splitext(p)[0] + ".txt"
                js = os.path.splitext(p)[0] + ".json"
                if os.path.exists(txt): os.remove(txt)
                if os.path.exists(js): os.remove(js)
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

    def test_video_saver_audio_muxing(self):
        node = StoiqoVideoSaverNode()
        frames = torch.zeros((10, 64, 64, 3), dtype=torch.float32)
        sample_rate = 44100
        t = torch.linspace(0, 0.5, int(sample_rate * 0.5))
        sine = torch.sin(2 * 3.14159 * 440 * t)
        dummy_audio = {"waveform": torch.stack([sine, sine], dim=0), "sample_rate": sample_rate}

        result = node.save_video_pro(
            images=frames,
            audio=dummy_audio,
            fps=24.0,
            filename_prefix="test_audio_mux_%fps%",
            format="MP4 (H.264)",
            subfolder="test_run_video",
            motion_prompt="Cinematic zoom",
            sidecar_metadata="Both (.json + .txt)",
        )

        out_imgs, out_filepath, out_filename, out_meta = result["result"]
        self.assertTrue(os.path.exists(out_filepath))
        meta_dict = json.loads(out_meta)
        self.assertTrue(meta_dict.get("has_audio", False))

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

        composite, mask, *_ = node.stitch_composite(
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

    def test_inpaint_stitcher_optional_mask(self):
        node = StoiqoInpaintStitcherNode()
        orig = torch.zeros((1, 200, 200, 3), dtype=torch.float32)
        edited_crop = torch.ones((1, 60, 60, 3), dtype=torch.float32)

        # Create a mask with a 60x60 white square at [40..100, 40..100]
        mask = torch.zeros((1, 200, 200), dtype=torch.float32)
        mask[0, 40:100, 40:100] = 1.0

        composite, out_mask, *_ = node.stitch_composite(
            original_image=orig,
            edited_image=edited_crop,
            bbox_info="",
            optional_mask=mask,
            blend_mode="Normal (Alpha Feather)",
            feather_radius=4,
        )

        self.assertEqual(composite.shape, (1, 200, 200, 3))
        self.assertEqual(out_mask.shape, (1, 200, 200))
        # Inner patch must have high intensity
        self.assertGreater(composite[0, 70, 70, 0].item(), 0.8)
        # Outside area must remain 0
        self.assertEqual(composite[0, 10, 10, 0].item(), 0.0)

    def test_inpaint_stitcher_string_bbox(self):
        node = StoiqoInpaintStitcherNode()
        orig = torch.zeros((1, 200, 200, 3), dtype=torch.float32)
        edited_crop = torch.ones((1, 80, 80, 3), dtype=torch.float32)

        composite, out_mask, *_ = node.stitch_composite(
            original_image=orig,
            edited_image=edited_crop,
            bbox_info="30, 30, 110, 110",
            blend_mode="Sharp (Direct Insert)",
            feather_radius=0,
        )

        self.assertEqual(composite.shape, (1, 200, 200, 3))
        self.assertGreater(composite[0, 70, 70, 0].item(), 0.9)
        self.assertEqual(composite[0, 5, 5, 0].item(), 0.0)

    def test_inpaint_stitcher_fit_modes(self):
        node = StoiqoInpaintStitcherNode()
        orig = torch.zeros((1, 200, 200, 3), dtype=torch.float32)
        # Non-square edited crop (100 wide x 50 high)
        edited_crop = torch.ones((1, 50, 100, 3), dtype=torch.float32)
        bbox = json.dumps({"crop_box": [50, 50, 150, 150]})

        for fit in ["Center Crop (Preserve Aspect)", "Stretch to Fill", "Center Fit (Letterbox / Pad)"]:
            composite, out_mask, *_ = node.stitch_composite(
                original_image=orig,
                edited_image=edited_crop,
                bbox_info=bbox,
                fit_mode=fit,
                blend_mode="Sharp (Direct Insert)",
                feather_radius=0,
            )
            self.assertEqual(composite.shape, (1, 200, 200, 3))
            self.assertGreater(composite[0, 100, 100, 0].item(), 0.5)

    def test_inpaint_stitcher_color_match(self):
        node = StoiqoInpaintStitcherNode()
        # Original has a warm tint (0.8, 0.4, 0.2)
        orig = torch.zeros((1, 100, 100, 3), dtype=torch.float32)
        orig[..., 0] = 0.8
        orig[..., 1] = 0.4
        orig[..., 2] = 0.2
        # Edited patch is neutral gray (0.5, 0.5, 0.5)
        edited_crop = torch.full((1, 40, 40, 3), 0.5, dtype=torch.float32)
        bbox = json.dumps({"crop_box": [30, 30, 70, 70]})

        composite, *_ = node.stitch_composite(
            original_image=orig,
            edited_image=edited_crop,
            bbox_info=bbox,
            color_match=True,
            color_match_strength=1.0,
            blend_mode="Sharp (Direct Insert)",
            feather_radius=0,
        )
        self.assertEqual(composite.shape, (1, 100, 100, 3))
        # After full color match, center should have red channel > green channel > blue channel
        self.assertGreater(composite[0, 50, 50, 0].item(), composite[0, 50, 50, 2].item())

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

    # ── 10. Turbo Sampler Node Tests ──────────────────────────
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

        img, lat, seed_out, w_out, h_out = node.sample_and_decode(
            positive_prompt="cinematic studio portrait",
            seed=12345,
            steps=4,
            cfg=1.0,
            sampler_name="euler",
            scheduler="simple",
            width=512,
            height=512,
            aspect_ratio="Custom (Manual Width & Height)",
            negative_mode="Zero-Out (Recommended for Krea 2 Turbo)",
            negative_prompt="",
            model=mock_model,
            clip=mock_clip,
            vae=mock_vae,
        )
        self.assertEqual(img.shape, (1, 512, 512, 3))
        self.assertIn("samples", lat)
        self.assertEqual(seed_out, 12345)
        self.assertEqual(w_out, 512)
        self.assertEqual(h_out, 512)

        # Test execution with pre-encoded positive conditioning (bypassing clip)
        mock_positive = [[torch.zeros((1, 77, 768)), {"pooled_output": torch.zeros((1, 768))}]]
        img_pos, lat_pos, seed_pos, w_pos, h_pos = node.sample_and_decode(
            positive_prompt="",
            seed=54321,
            steps=20,
            cfg=3.5,
            sampler_name="euler",
            scheduler="normal",
            width=512,
            height=512,
            aspect_ratio="Custom (Manual Width & Height)",
            negative_mode="None",
            negative_prompt="",
            model=mock_model,
            positive=mock_positive,
            vae=mock_vae,
        )
        self.assertEqual(img_pos.shape, (1, 512, 512, 3))
        self.assertEqual(seed_pos, 54321)

        # Test img2img via direct image tensor input
        input_image_tensor = torch.zeros((1, 512, 512, 3), dtype=torch.float32)
        img_i2i, lat_i2i, seed_i2i, w_i2i, h_i2i = node.sample_and_decode(
            positive_prompt="enhance portrait details",
            seed=999,
            steps=4,
            cfg=1.0,
            sampler_name="euler",
            scheduler="simple",
            width=512,
            height=512,
            aspect_ratio="Custom (Manual Width & Height)",
            negative_mode="Zero-Out (Recommended for Krea 2 Turbo)",
            negative_prompt="",
            denoise=0.65,
            image=input_image_tensor,
            model=mock_model,
            clip=mock_clip,
            vae=mock_vae,
        )
        self.assertEqual(img_i2i.shape, (1, 512, 512, 3))
        self.assertIn("samples", lat_i2i)
        self.assertEqual(lat_i2i["samples"].shape, (1, 4, 64, 64))
        self.assertEqual(seed_i2i, 999)

        # Test with latent_image input pin
        custom_lat = {"samples": torch.zeros((1, 4, 32, 32), dtype=torch.float32)}
        img_lat, lat_out, seed_lat, w_lat, h_lat = node.sample_and_decode(
            positive_prompt="",
            seed=1000,
            steps=4,
            cfg=1.0,
            sampler_name="euler",
            scheduler="simple",
            width=256,
            height=256,
            aspect_ratio="Custom (Manual Width & Height)",
            negative_mode="None",
            negative_prompt="",
            denoise=0.5,
            latent_image=custom_lat,
            model=mock_model,
            positive=mock_positive,
            vae=mock_vae,
        )
        self.assertEqual(lat_out["samples"].shape, (1, 4, 32, 32))
        self.assertEqual(seed_lat, 1000)

    # ── 12. All-in-One Prompt Generator Engine Tests ────────────
    def test_all_in_one_prompt_generator_text_mode(self):
        node = StoiqoPromptGeneratorNode()
        mock_vlm = {}  # fallback expansion
        res = node.generate_prompt(
            user_directives="high-tech neon laboratory, glowing vials",
            system_prompt="Visual Prompt Synthesizer",
            prompt_type="Detailed Narrative (Long)",
            artistic_style="Photorealistic (Modern Digital RAW)",
            temperature=0.7,
            seed=12345,
            negative_prompt_prefix="worst quality, blurry",
            model=mock_vlm,
        )
        self.assertIn("ui", res)
        self.assertIn("result", res)
        prompts, tags, negatives, raws = res["result"]
        self.assertEqual(len(prompts), 1)
        self.assertIn("neon laboratory", prompts[0].lower())
        self.assertTrue(len(tags[0]) > 0)
        self.assertTrue(len(negatives[0]) > 0)
        self.assertIn("worst quality", negatives[0])

    def test_all_in_one_prompt_generator_multi_image(self):
        node = StoiqoPromptGeneratorNode()
        img1 = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
        img2 = torch.ones((1, 64, 64, 3), dtype=torch.float32)
        img3 = torch.full((1, 64, 64, 3), 0.5, dtype=torch.float32)
        mock_vlm = {}

        res = node.generate_prompt(
            user_directives="fuse subjects and lighting",
            image=img1,
            image_2=img2,
            image_3=img3,
            fusion_mode="Contextual Fusion (Blend Style & Subject)",
            model=mock_vlm,
        )
        self.assertIn("ui", res)
        prompts, tags, negatives, raws = res["result"]
        self.assertEqual(len(prompts), 1)
        self.assertTrue(len(prompts[0]) > 0)

    def test_all_in_one_prompt_generator_batch_mode(self):
        node = StoiqoPromptGeneratorNode()
        batch = torch.zeros((3, 64, 64, 3), dtype=torch.float32)
        mock_vlm = {}

        res = node.generate_prompt(
            user_directives="dataset item",
            image=batch,
            fusion_mode="Independent Batch (Caption each image separately for datasets)",
            model=mock_vlm,
        )
        prompts, tags, negatives, raws = res["result"]
        self.assertEqual(len(prompts), 3)  # One caption per frame in batch

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

    def test_watermark_typographic_and_blend_modes(self):
        node = StoiqoWatermarkNode()
        base_img = torch.full((1, 256, 256, 3), 0.5, dtype=torch.float32)

        # 1. Typographic text watermark without external image
        res_text = node.apply_watermark(
            base_image=base_img,
            text_watermark="© STOIQO AI STUDIO",
            text_font="sans-serif",
            text_color="gold",
            text_outline=True,
            position="Center-Right",
            scale_mode="1/4",
            blend_mode="Screen (Light Logo)",
            opacity=0.9,
            unique_id="test_wm_typo",
        )
        out_img, out_mask, info_str = res_text
        self.assertEqual(out_img.shape, (1, 256, 256, 3))
        self.assertEqual(out_mask.shape, (1, 256, 256))
        self.assertGreater(out_mask.sum().item(), 0.0)
        self.assertIn("Center-Right", info_str)
        self.assertIn("Screen (Light Logo)", info_str)

        # 2. Test Center-Left position and Multiply blend
        res_mult = node.apply_watermark(
            base_image=base_img,
            text_watermark="CONFIDENTIAL",
            text_color="black",
            position="Center-Left",
            blend_mode="Multiply (Dark Logo)",
            opacity=1.0,
        )
        out_img_m, out_mask_m, info_str_m = res_mult
        self.assertEqual(out_img_m.shape, (1, 256, 256, 3))
        self.assertIn("Center-Left", info_str_m)

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

    def test_spatial_cropper_florence2_and_manual_override(self):
        from nodes.spatial_cropper_node import StoiqoSpatialCropperNode
        node = StoiqoSpatialCropperNode()
        dummy_img = torch.zeros((1, 512, 512, 3), dtype=torch.float32)

        # 1. Florence-2 loc tags
        mock_florence = MagicMock()
        mock_florence.generate_single.return_value = "<loc_200><loc_200><loc_800><loc_800>"
        mock_florence.keep_in_vram = False
        mock_florence.unload_model = MagicMock()

        crop_fl, mask_fl, meta_fl, segs_fl = node.crop_and_mask(
            stoiqo_model=mock_florence,
            image=dummy_img,
            detect_prompt="person",
        )
        self.assertGreater(crop_fl.shape[1], 100)
        self.assertGreater(crop_fl.shape[2], 100)
        mock_florence.unload_model.assert_called_once()

        # 2. Manual BBox override (skips VLM)
        crop_man, mask_man, meta_man, segs_man = node.crop_and_mask(
            image=dummy_img,
            manual_bbox="[50, 50, 200, 200]",
            detect_prompt="watch",
        )
        meta_dict = json.loads(meta_man)
        self.assertTrue(meta_dict["detected"])
        self.assertEqual(meta_dict["crop_box"], [50, 50, 200, 200])
        self.assertEqual(crop_man.shape[1], 150)
        self.assertEqual(crop_man.shape[2], 150)

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
        img, lat, seed_out, w_out, h_out = node.sample_and_decode(
            positive_prompt="",
            seed=0,
            steps=4,
            cfg=1.0,
            sampler_name="euler",
            scheduler="simple",
            width=256,
            height=256,
            aspect_ratio="Custom (Manual Width & Height)",
            negative_mode="Zero-Out (Recommended for Krea 2 Turbo)",
            negative_prompt="",
            pipe=mock_context,
        )
        self.assertEqual(img.shape, (1, 256, 256, 3))
        self.assertIn("samples", lat)
        self.assertEqual(seed_out, 98765)
        self.assertEqual(w_out, 256)
        self.assertEqual(h_out, 256)

    # ── 16. Killer Feature: Universal API Endpoint Resolution ───
    def test_model_manager_api_endpoint_resolution(self):
        from core import ModelManager, API_ENDPOINT_KEY
        mgr = ModelManager()
        resolved = mgr.resolve_model_repo(
            model_preset=API_ENDPOINT_KEY,
            local_model_path="http://127.0.0.1:42030/v1#qwen2.5-vl:7b"
        )
        self.assertTrue(resolved.startswith("api://"))
        self.assertIn("127.0.0.1:42030/v1", resolved)

        mgr.load_model(resolved, "none", "sdpa")
        self.assertTrue(getattr(mgr, "is_api_endpoint", False))
        self.assertEqual(mgr.model, "API_CLIENT")
        self.assertEqual(mgr.api_base_url, "http://127.0.0.1:42030/v1")
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

    # ── 17. Show Prompt Node Tests ──────────────────────────────
    def test_show_prompt_node_single_and_batch(self):
        node = StoiqoShowPromptNode()
        # Single prompt string
        res_single = node.display("cyberpunk female warrior, neon lighting, ultra detailed 8k")
        (out_single,) = res_single
        self.assertEqual(out_single, ["cyberpunk female warrior, neon lighting, ultra detailed 8k"])
        self.assertIn("ui", res_single)
        self.assertEqual(res_single["ui"]["count"], [1])
        self.assertEqual(len(res_single["ui"]["stats"]), 1)
        self.assertEqual(res_single["ui"]["stats"][0]["words"], 8)
        self.assertGreater(res_single["ui"]["stats"][0]["chars"], 30)

        # Batch prompt list
        batch_prompts = [
            "masterpiece portrait of an astronaut on Mars",
            "hyperrealistic macro photo of a glowing crystal",
            "steampunk clockwork owl perched on an ancient book",
        ]
        res_batch = node.display(batch_prompts)
        (out_batch,) = res_batch
        self.assertEqual(out_batch, batch_prompts)
        self.assertIn("ui", res_batch)
        self.assertEqual(res_batch["ui"]["count"], [3])
        self.assertEqual(len(res_batch["ui"]["stats"]), 3)
        self.assertEqual(res_batch["ui"]["stats"][0]["words"], 7)
        self.assertEqual(res_batch["ui"]["stats"][1]["words"], 7)
        self.assertEqual(res_batch["ui"]["stats"][2]["words"], 8)

    # ── 18. Unified Seed & Resolution Controller Node Tests ─────
    def test_unified_seed_and_resolution_controller(self):
        from nodes.seed_node import StoiqoSeedControllerNode
        node = StoiqoSeedControllerNode()

        # 1. Preset 16:9 at 1.0 MP with seed variance
        res = node.resolve_seed_and_resolution(
            seed=77777,
            aspect_ratio="16:9 (Widescreen / YouTube - 1344x768)",
            scale_target="1.0 MP (Standard SDXL / Flux / Krea)",
            swap_dimensions=False,
            multiple_of="16 (Flux / Wan / Modern Models)",
            variance_strength=0.15,
            variance_seed=42,
            seed_prefix="RUN_",
        )
        self.assertIn("ui", res)
        self.assertIn("result", res)
        seed_val, w, h, eff_seed, ar_val, res_str, seed_str = res["result"]
        self.assertEqual(seed_val, 77777)
        self.assertEqual(w, 1344)
        self.assertEqual(h, 768)
        self.assertNotEqual(eff_seed, 77777)
        self.assertAlmostEqual(ar_val, round(1344 / 768, 4), places=3)
        self.assertTrue(res_str.startswith("1344x768"))
        self.assertTrue(seed_str.startswith("RUN_77777"))

        # 2. Match Input Image with 1.5 MP scaling and dimension swap
        dummy_img = torch.zeros((1, 500, 1000, 3), dtype=torch.float32)  # 2:1 landscape
        res_img = node.resolve_seed_and_resolution(
            seed=12345,
            aspect_ratio="Match Input Image (If Connected)",
            scale_target="1.0 MP (Standard SDXL / Flux / Krea)",
            image=dummy_img,
            swap_dimensions=True,
            multiple_of="16 (Flux / Wan / Modern Models)",
        )
        _, w_img, h_img, *_ = res_img["result"]
        # Swapped 2:1 landscape -> portrait (h > w) and divisible by 16
        self.assertGreater(h_img, w_img)
        self.assertEqual(w_img % 16, 0)
        self.assertEqual(h_img % 16, 0)


if __name__ == "__main__":
    unittest.main()

