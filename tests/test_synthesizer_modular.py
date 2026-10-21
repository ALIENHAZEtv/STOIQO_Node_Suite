"""
[STOIQO] Unit Tests — Prompt Synthesizer + Style/Sampling satellites (stub model, no GPU)
Also guards feature parity with the removed legacy Prompt Generator Engine.
"""

import importlib.util
import os
import sys
import unittest

import torch

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(root, "nodes", filename))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


synth_mod = _load("stoiqo_synth_node", "prompt_synthesizer_node.py")
style_mod = _load("stoiqo_style_node", "style_directives_node.py")
sampling_mod = _load("stoiqo_sampling_node", "sampling_options_node.py")

from core.image import MULTI_IMAGE_SYSTEM_PROMPT, TEXT_EXPANSION_SYSTEM_PROMPT  # noqa: E402


class StubModel:
    def __init__(self):
        self.calls = []

    def generate_single(self, **kwargs):
        self.calls.append(kwargs)
        return "<PROMPT>a cat</PROMPT>\n<TAGS>cat, cute</TAGS>\n<NEGATIVE>blurry</NEGATIVE>"


def _result(node_out):
    return node_out["result"]


class TestMentions(unittest.TestCase):
    def test_whole_word_only(self):
        self.assertTrue(synth_mod._mentions("Portrait of Ann in a park", "ann"))
        self.assertFalse(synth_mod._mentions("Joanna in a park", "ann"))
        self.assertFalse(synth_mod._mentions("anything", ""))


class TestSatellites(unittest.TestCase):
    def test_style_bundle_defaults_and_prefix(self):
        node = style_mod.StoiqoStyleDirectivesNode()
        req = node.INPUT_TYPES()["required"]
        (bundle,) = node.build_style(
            req["system_prompt"][1]["default"],
            req["prompt_type"][1]["default"],
            req["artistic_style"][1]["default"],
            negative_prompt_prefix="worst quality, ",
        )
        self.assertTrue(bundle["enable_dual_prompt"])
        self.assertTrue(bundle["audit_artifacts"])
        self.assertEqual(bundle["negative_prompt_prefix"], "worst quality, ")

    def test_sampling_bundle(self):
        (b,) = sampling_mod.StoiqoSamplingOptionsNode().build_sampling_options(seed=7, top_k=10)
        self.assertEqual((b["seed"], b["top_k"]), (7, 10))


class TestSynthesizer(unittest.TestCase):
    def setUp(self):
        self.node = synth_mod.StoiqoPromptSynthesizerNode()
        self.model = StubModel()

    def test_text_only_uses_text_expansion_system_prompt(self):
        prompts, tags, negs, raws = _result(self.node.synthesize_prompt(self.model, "a cat"))
        self.assertEqual((len(prompts), len(tags), len(negs), len(raws)), (1, 1, 1, 1))
        call = self.model.calls[0]
        self.assertIsNone(call["pil_images"])
        self.assertEqual(call["system_prompt"], TEXT_EXPANSION_SYSTEM_PROMPT)

    def test_batch_is_captioned_independently_with_incrementing_seed(self):
        batch = torch.rand(6, 64, 64, 3)
        prompts, tags, negs, raws = _result(self.node.synthesize_prompt(self.model, "x", image=batch))
        self.assertEqual(len(prompts), 6)  # no truncation: every image gets its own caption
        self.assertEqual([c["seed"] for c in self.model.calls], [42 + i for i in range(6)])
        self.assertTrue(all(not c["is_multi_image"] for c in self.model.calls))

    def test_context_hub_fuses_into_one_multi_image_job(self):
        a, b = torch.rand(1, 64, 64, 3), torch.rand(1, 64, 64, 3)
        ctx = {"images": [a, b], "fusion_mode": "Comparative Difference (What Changed)"}
        prompts, *_ = _result(self.node.synthesize_prompt(self.model, "x", multi_image_context=ctx))
        self.assertEqual(len(prompts), 1)
        call = self.model.calls[0]
        self.assertTrue(call["is_multi_image"])
        self.assertEqual(len(call["pil_images"]), 2)
        self.assertEqual(call["system_prompt"], MULTI_IMAGE_SYSTEM_PROMPT)

    def test_primary_image_plus_hub_are_fused_together(self):
        primary = torch.rand(1, 64, 64, 3)
        ctx = {"images": [torch.rand(1, 64, 64, 3), torch.rand(1, 64, 64, 3)], "fusion_mode": "x"}
        self.node.synthesize_prompt(self.model, "x", image=primary, multi_image_context=ctx)
        self.assertEqual(len(self.model.calls[0]["pil_images"]), 3)

    def test_negative_prefix_and_top_k_are_forwarded(self):
        style = {"negative_prompt_prefix": "worst quality, ", "audit_artifacts": True}
        sampling = {"top_k": 17}
        _, _, negs, _ = _result(self.node.synthesize_prompt(
            self.model, "a cat", style_directives=style, sampling_options=sampling))
        self.assertEqual(self.model.calls[0]["top_k"], 17)
        self.assertTrue(negs[0].startswith("worst quality"))

    def test_missing_generate_single_warns(self):
        with self.assertLogs(synth_mod.logger, level="WARNING"):
            result = _result(self.node.synthesize_prompt(object(), "a cat"))
        self.assertEqual(len(result), 4)

    def test_character_smart_detect_whole_word(self):
        char = {
            "injection_mode": "Smart Detect (Inject only when Name or Trigger is in Prompt)",
            "character_name": "Ann",
            "character_dna": "red hair",
        }
        self.node.synthesize_prompt(self.model, "Joanna in a park", character_context=char)
        self.node.synthesize_prompt(self.model, "Ann in a park", character_context=char)
        self.assertNotIn("red hair", self.model.calls[0]["task_prompt"])
        self.assertIn("red hair", self.model.calls[1]["task_prompt"])

    def test_regional_mode_directive(self):
        self.node.synthesize_prompt(
            self.model,
            "two dancers",
            regional_mode="Left / Right / Background",
        )
        task_prompt = self.model.calls[0]["task_prompt"]
        self.assertIn("REGIONAL COMPOSITION DIRECTIVE", task_prompt)
        self.assertIn("[LEFT:", task_prompt)
        self.assertIn("[RIGHT:", task_prompt)
        self.assertIn("[BACKGROUND:", task_prompt)


class TestRoutesModule(unittest.TestCase):
    def test_routes_module_importable_headless(self):
        from core.routes import register_stoiqo_routes
        register_stoiqo_routes()  # must not raise without ComfyUI


if __name__ == "__main__":
    unittest.main()
