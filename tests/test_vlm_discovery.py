"""
[STOIQO] Dynamic Model Discovery & Universal VLM Loader Test Suite
Verifies that:
1. Local VLM/CLIP models (Qwen3, Qwen2.5, etc.) are dynamically discovered.
2. Qwen3-VL models are prioritized at the top as primary default.
3. Universal model resolution works across local files, presets, arbitrary HF repos, and API endpoints.
4. Backwards compatibility aliases remain functional.
"""

import unittest
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

from core.config import (
    get_vlm_model_choices,
    scan_local_vlm_models,
    DISCOVERED_LOCAL_MODELS,
    MODEL_PRESETS,
    CUSTOM_MODEL_KEY,
    API_ENDPOINT_KEY,
)
from core.model_manager import ModelManager
from nodes.universal_model_loader_node import StoiqoUniversalModelLoaderNode


class TestVLMUniversalDiscovery(unittest.TestCase):

    def setUp(self):
        self.mgr = ModelManager()

    def test_dynamic_choices_contains_presets_and_specials(self):
        choices = get_vlm_model_choices()
        self.assertIsInstance(choices, list)
        self.assertGreater(len(choices), 0)

        # Must contain API and Custom keys
        self.assertIn(API_ENDPOINT_KEY, choices)
        self.assertIn(CUSTOM_MODEL_KEY, choices)

        # Must contain core presets
        self.assertIn("Qwen3-VL-4B-Instruct (4bit, ~3.0 GB active)", choices)
        self.assertIn("Florence-2-Large (Vision Expert, ~1.5 GB active)", choices)
        self.assertIn("MiniCPM-V-2_6 (8B Multimodal, ~5.5 GB active)", choices)

    def test_qwen3_prioritization(self):
        choices = get_vlm_model_choices()
        first_choice = choices[0]
        # If any Qwen3 model exists locally or in presets, the top item should be a Qwen3 model
        self.assertTrue("qwen3" in first_choice.lower() or "qwen-3" in first_choice.lower(),
                        f"Expected top choice to be a Qwen3-VL model, got: {first_choice}")

    def test_resolve_local_discovered_model(self):
        discovered = scan_local_vlm_models()
        if discovered:
            first_label = list(discovered.keys())[0]
            resolved_path = self.mgr.resolve_model_repo(model_preset=first_label)
            self.assertEqual(resolved_path, discovered[first_label])

    def test_resolve_arbitrary_huggingface_repo(self):
        arbitrary_repo = "openbmb/MiniCPM-V-2_6"
        resolved = self.mgr.resolve_model_repo(model_preset=arbitrary_repo)
        self.assertEqual(resolved, arbitrary_repo)

    def test_resolve_legacy_preset_alias(self):
        legacy = "<= 8 GB VRAM  -  Qwen2.5-VL-3B  (4bit, ~2.5 GB active)"
        resolved = self.mgr.resolve_model_repo(model_preset=legacy)
        self.assertEqual(resolved, "Qwen/Qwen2.5-VL-3B-Instruct")

    def test_node_input_types_uses_dynamic_scanner(self):
        input_types = StoiqoUniversalModelLoaderNode.INPUT_TYPES()
        self.assertIn("required", input_types)
        model_name_tuple = input_types["required"]["model_name"]
        choices = model_name_tuple[0]
        config = model_name_tuple[1]

        self.assertIsInstance(choices, list)
        self.assertIn("default", config)
        self.assertEqual(config["default"], choices[0])


if __name__ == "__main__":
    unittest.main()
