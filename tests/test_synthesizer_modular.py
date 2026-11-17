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


synth_mod = _load("stoiqo_generator_node", "prompt_generator_node.py")

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


class TestAllInOneGenerator(unittest.TestCase):
    def test_direct_controls_defaults_and_prefix(self):
        node = synth_mod.StoiqoPromptGeneratorNode()
        req = node.INPUT_TYPES()["required"]
        opt = node.INPUT_TYPES()["optional"]
        self.assertIn("system_prompt", req)
        self.assertIn("prompt_type", req)
        self.assertIn("prompt_style", req)
        self.assertIn("custom_modifications", req)
        self.assertIn("seed", opt)
        self.assertIn("text_input", opt)
        self.assertIn("image_input", opt)
        self.assertIn("model", opt)
        self.assertIn("character", opt)
        self.assertNotIn("preset", opt)
        self.assertIn("fusion_mode", opt)


class TestSynthesizer(unittest.TestCase):
    def setUp(self):
        self.node = synth_mod.StoiqoPromptGeneratorNode()
        self.model = StubModel()

    def test_text_only_uses_text_expansion_system_prompt(self):
        prompts, tags, negs, raws = _result(self.node.synthesize_prompt(self.model, "a cat"))
        self.assertEqual((len(prompts), len(tags), len(negs), len(raws)), (1, 1, 1, 1))
        call = self.model.calls[0]
        self.assertIsNone(call["pil_images"])
        self.assertTrue(call["system_prompt"].startswith(TEXT_EXPANSION_SYSTEM_PROMPT) or "ROLE & IDENTITY" in call["system_prompt"])
        self.assertIn("LAYER 2", call["system_prompt"])

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
        self.assertTrue(call["system_prompt"].startswith(MULTI_IMAGE_SYSTEM_PROMPT) or "ROLE & IDENTITY" in call["system_prompt"])
        self.assertIn("LAYER 2", call["system_prompt"])

    def test_primary_image_plus_hub_are_fused_together(self):
        primary = torch.rand(1, 64, 64, 3)
        ctx = {"images": [torch.rand(1, 64, 64, 3), torch.rand(1, 64, 64, 3)], "fusion_mode": "x"}
        self.node.synthesize_prompt(self.model, "x", image=primary, multi_image_context=ctx)
        self.assertEqual(len(self.model.calls[0]["pil_images"]), 3)

    def test_direct_multi_image_slots_fusion(self):
        img1 = torch.rand(1, 64, 64, 3)
        img2 = torch.rand(1, 64, 64, 3)
        img3 = torch.rand(1, 64, 64, 3)
        prompts, *_ = _result(self.node.generate_prompt(
            user_directives="fuse subjects",
            image=img1,
            image_2=img2,
            image_3=img3,
            fusion_mode="Contextual Fusion (Blend Style & Subject)",
            model=self.model,
        ))
        self.assertEqual(len(prompts), 1)
        call = self.model.calls[0]
        self.assertTrue(call["is_multi_image"])
        self.assertEqual(len(call["pil_images"]), 3)

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

    def test_clip_in_memory_text_generation(self):
        class StubClip:
            def __init__(self):
                self.tokenized_args = []
                self.generated_args = []

            def tokenize(self, prompt, image=None, skip_template=False, min_length=1, system_prompt=""):
                self.tokenized_args.append({"prompt": prompt, "system_prompt": system_prompt})
                return {"tokens": [1, 2, 3]}

            def generate(self, tokens, **kwargs):
                self.generated_args.append(kwargs)
                return [101, 102, 103]

            def decode(self, generated_ids):
                return "<think>planning thoughts</think><PROMPT>A breathtaking cinematic soccer kick</PROMPT><TAGS>soccer, athlete, action</TAGS>"

        stub_clip = StubClip()
        prompts, tags, negs, raws = _result(self.node.synthesize_prompt(
            stoiqo_model=None,
            user_directives="soccer kick",
            clip=stub_clip,
        ))
        self.assertEqual(len(stub_clip.tokenized_args), 1)
        self.assertEqual(len(stub_clip.generated_args), 1)
        self.assertIn("soccer kick", prompts[0].lower())



class TestRoutesModule(unittest.TestCase):
    def test_routes_module_importable_headless(self):
        from core.routes import register_stoiqo_routes
        register_stoiqo_routes()  # must not raise without ComfyUI


if __name__ == "__main__":
    unittest.main()
