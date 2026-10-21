"""
Unit tests for [STOIQO] Telemetry, Performance Badges, and Character Consistency Synthesizer Integration
"""

import time
import unittest
import torch
from core.telemetry import NodeTelemetryTimer, inject_telemetry, TelemetryResult
from nodes.prompt_synthesizer_node import StoiqoPromptSynthesizerNode


class TestTelemetry(unittest.TestCase):
    def test_timer_context_and_stats(self):
        with NodeTelemetryTimer(node_id="test_node_42", node_name="TestSampler") as timer:
            time.sleep(0.01)  # 10ms
        stats = timer.get_stats()
        self.assertIn("time_ms", stats)
        self.assertGreaterEqual(stats["time_ms"], 8.0)
        self.assertIn("vram_gb", stats)
        self.assertEqual(stats["node_id"], "test_node_42")
        self.assertEqual(stats["node_name"], "TestSampler")

    def test_telemetry_result_dual_behavior(self):
        stats = {"time_ms": 150.5, "vram_gb": 3.8, "node_name": "TestNode"}
        res = inject_telemetry(("image_tensor", "latent_dict", "pipe_dict"), stats)

        # 1. Dict behavior for ComfyUI
        self.assertIsInstance(res, dict)
        self.assertIn("ui", res)
        self.assertIn("stoiqo_telemetry", res["ui"])
        self.assertEqual(res["ui"]["stoiqo_telemetry"][0]["time_ms"], 150.5)
        self.assertIn("result", res)

        # 2. Sequence behavior for direct indexing
        self.assertEqual(res[0], "image_tensor")
        self.assertEqual(res[1], "latent_dict")
        self.assertEqual(res[2], "pipe_dict")
        self.assertEqual(len(res), 3)

        # 3. Tuple unpacking behavior for Python calls
        img, lat, pipe = res
        self.assertEqual(img, "image_tensor")
        self.assertEqual(lat, "latent_dict")
        self.assertEqual(pipe, "pipe_dict")

    def test_inject_telemetry_dict_passthrough(self):
        stats = {"time_ms": 45.2, "vram_gb": 0.0}
        initial_dict = {
            "ui": {"custom_data": [1, 2, 3]},
            "result": ("val1", "val2"),
        }
        res = inject_telemetry(initial_dict, stats)
        self.assertIn("stoiqo_telemetry", res["ui"])
        self.assertIn("custom_data", res["ui"])
        v1, v2 = res
        self.assertEqual(v1, "val1")
        self.assertEqual(v2, "val2")

    def test_synthesizer_with_character_context(self):
        synth_node = StoiqoPromptSynthesizerNode()
        char_ctx = {
            "character_name": "Aria Vance",
            "trigger_tag": "aria_vance",
            "character_dna": "violet eyes, silver bob, pale skin, eyebrow scar",
            "signature_outfit": "black techwear jacket",
            "accessories_props": "fingerless gloves",
            "personality_vibe": "sharp, analytical",
            "negative_constraints": "wrong eye color, missing scar",
            "injection_mode": "Always Prepend (Force Character DNA)",
        }

        # Mock model loader
        class _MockModel:
            pass

        res = synth_node.synthesize_prompt(
            stoiqo_model=_MockModel(),
            user_directives="standing atop a neon skyscraper",
            character_context=char_ctx,
            unique_id="synth_node_1",
        )

        self.assertIsInstance(res, dict)
        self.assertIn("ui", res)
        self.assertIn("stoiqo_telemetry", res["ui"])
        self.assertEqual(res["ui"]["stoiqo_telemetry"][0]["node_name"], "PromptSynthesizer")

        prompt, tags, neg, raw = res["result"]
        prompt, tags, neg, raw = prompt[0], tags[0], neg[0], raw[0]
        self.assertIn("Character: Aria Vance", raw)
        self.assertIn("violet eyes", raw)
        self.assertIn("wrong eye color", neg)
        self.assertIn("missing scar", neg)


if __name__ == "__main__":
    unittest.main()
