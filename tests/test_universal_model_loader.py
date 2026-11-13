"""
[STOIQO] Universal Model Loader Test Suite
Verifies polymorphic model auto-detection, choices generation, input schema,
and pipe construction.
"""

import os
import sys
import unittest

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

from core.universal_loader import (
    get_universal_model_choices,
    scan_all_system_models,
    detect_model_kind,
    resolve_raw_filename_or_repo,
    UniversalModelEngine,
    MODEL_TYPE_OVERRIDE_OPTIONS,
)
from nodes.universal_model_loader_node import StoiqoUniversalModelLoaderNode


class TestUniversalModelLoader(unittest.TestCase):

    def test_get_universal_choices(self):
        choices = get_universal_model_choices()
        self.assertIsInstance(choices, list)
        self.assertGreater(len(choices), 0)

        # Check special categories exist
        special_choices = [c for c in choices if c.startswith("[Special]")]
        self.assertGreater(len(special_choices), 0)

        # Check VLM presets exist
        vlm_presets = [c for c in choices if c.startswith("[VLM Preset]")]
        self.assertGreater(len(vlm_presets), 0)

    def test_detect_model_kind_from_labels(self):
        self.assertEqual(detect_model_kind("[DiT/UNET] acestep_v1.5_turbo.safetensors"), "MODEL")
        self.assertEqual(detect_model_kind("[CLIP] qwen_0.6b_ace15.safetensors"), "CLIP")
        self.assertEqual(detect_model_kind("[VAE] ace_1.5_vae.safetensors"), "VAE")
        self.assertEqual(detect_model_kind("[Checkpoint] sd15_base.safetensors"), "CHECKPOINT")
        self.assertEqual(detect_model_kind("[VLM] Qwen3-VL-4B"), "VLM")
        self.assertEqual(detect_model_kind("[VLM Preset] Florence-2-Large"), "VLM")

    def test_detect_model_kind_from_raw_names(self):
        self.assertEqual(detect_model_kind("flux_vae.safetensors"), "VAE")
        self.assertEqual(detect_model_kind("qwen3_text_encoder.safetensors"), "CLIP")
        self.assertEqual(detect_model_kind("wan2.1_diffusion.safetensors"), "MODEL")
        self.assertEqual(detect_model_kind("Qwen/Qwen2.5-VL-7B-Instruct"), "VLM")

    def test_resolve_raw_filename_or_repo(self):
        raw = resolve_raw_filename_or_repo("[DiT/UNET] acestep_v1.5_turbo.safetensors")
        self.assertEqual(raw, "acestep_v1.5_turbo.safetensors")

        raw_vlm = resolve_raw_filename_or_repo("[VLM Preset] Qwen3-VL-4B-Instruct")
        self.assertEqual(raw_vlm, "Qwen3-VL-4B-Instruct")

    def test_node_schema_and_types(self):
        schema = StoiqoUniversalModelLoaderNode.INPUT_TYPES()
        self.assertIn("required", schema)
        self.assertIn("model_name", schema["required"])
        self.assertIn("clip_type", schema["required"])
        self.assertIn("precision", schema["required"])
        self.assertIn("attention", schema["required"])

        # Verify optional controls for custom models, Low-VRAM, and Flow Shift
        self.assertIn("optional", schema)
        self.assertIn("custom_path", schema["optional"])
        self.assertIn("keep_in_vram", schema["optional"])
        self.assertIn("flow_shift_preset", schema["optional"])
        self.assertIn("custom_shift", schema["optional"])

        self.assertEqual(
            StoiqoUniversalModelLoaderNode.RETURN_TYPES,
            ("*",),
        )
        self.assertEqual(
            StoiqoUniversalModelLoaderNode.RETURN_NAMES,
            ("model",),
        )

    def test_flow_shift_presets_and_application(self):
        from core.universal_loader import apply_flow_shift, SAMPLING_PRESETS
        self.assertIsInstance(SAMPLING_PRESETS, list)
        self.assertGreater(len(SAMPLING_PRESETS), 5)

        # Mock model dict
        mock_model = {"name": "test_dit.safetensors", "kind": "MODEL"}
        shifted = apply_flow_shift(mock_model, "Z-Image Turbo (Shift: 3.0)")
        self.assertEqual(shifted.get("flow_shift_preset"), "Z-Image Turbo (Shift: 3.0)")

        # Custom shift
        custom_shifted = apply_flow_shift(mock_model, "Custom (Override manuale)", custom_shift=4.5)
        self.assertEqual(custom_shifted.get("custom_shift"), 4.5)

    def test_engine_flow_shift_integration(self):
        engine = UniversalModelEngine()
        res = engine.load(
            model_choice="[DiT/UNET] krea2_turbo.safetensors",
            flow_shift_preset="Z-Image Turbo (Shift: 3.0)",
            custom_shift=3.0,
        )
        self.assertIsInstance(res, tuple)
        self.assertEqual(len(res), 1)
        loaded = res[0]
        self.assertIsInstance(loaded, dict)
        self.assertEqual(loaded.get("flow_shift_preset"), "Z-Image Turbo (Shift: 3.0)")

    def test_resolve_clip_type_auto_detection(self):
        from core.universal_loader import resolve_clip_type
        # Test Krea2 / Qwen3-VL-4B detection
        c_krea = resolve_clip_type("auto", "qwen3VL4BAbliteratedComfyui_v10.safetensors")
        self.assertIsNotNone(c_krea)

        # Test Wan detection
        c_wan = resolve_clip_type("auto", "wan2.1_umt5_xxl.safetensors")
        self.assertIsNotNone(c_wan)

        # Test Flux detection
        c_flux = resolve_clip_type("auto", "t5xxl_fp8_flux.safetensors")
        self.assertIsNotNone(c_flux)

    def test_engine_single_polymorphic_output(self):
        engine = UniversalModelEngine()

        # Simulate loading with a non-existent or mock choice
        # Should cleanly return a 1-tuple (loaded_obj,)
        res = engine.load(
            model_choice="[VAE] non_existent_vae.safetensors",
            precision="default",
            attention="sdpa",
            custom_path="",
            keep_in_vram=True,
        )

        self.assertIsInstance(res, tuple)
        self.assertEqual(len(res), 1)


if __name__ == "__main__":
    unittest.main()


