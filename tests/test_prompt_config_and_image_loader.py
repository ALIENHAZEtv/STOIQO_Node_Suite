"""
[STOIQO] Unit Tests for StoiqoImageLoaderNode and Integrated StoiqoPromptGeneratorNode.
"""

import unittest
import torch
from nodes.image_loader_node import StoiqoImageLoaderNode, _fit_image_and_mask_to_target
from nodes.prompt_generator_node import StoiqoPromptGeneratorNode


class TestPromptConfigAndImageLoader(unittest.TestCase):
    def test_prompt_generator_minimal_canvas_and_integrated_settings(self):
        gen_node = StoiqoPromptGeneratorNode()
        req = gen_node.INPUT_TYPES()["required"]
        opt = gen_node.INPUT_TYPES()["optional"]

        # Only minimal parameters in required
        self.assertIn("prompt_type", req)
        self.assertIn("prompt_style", req)
        self.assertIn("custom_modifications", req)
        self.assertIn("seed", req)
        self.assertEqual(len(req), 4)

        # External sockets and integrated ⚙ settings
        self.assertIn("text_input", opt)
        self.assertIn("image_input", opt)
        self.assertIn("model", opt)
        self.assertIn("character", opt)
        self.assertIn("preset", opt)
        self.assertIn("fusion_mode", opt)
        self.assertIn("system_prompt", opt)
        self.assertIn("temperature", opt)
        self.assertIn("max_new_tokens", opt)

    def test_image_loader_signature_and_outputs(self):
        node = StoiqoImageLoaderNode()
        self.assertEqual(len(node.RETURN_TYPES), 6)
        self.assertEqual(node.RETURN_NAMES, ("image", "mask", "image_1", "image_2", "image_3", "loaded_count"))

        # Test fallback when no files exist
        res = node.load_images("non_existent_1.png", "non_existent_2.png", "none")
        self.assertIn("result", res)
        unified_img, mask, img1, img2, img3, count = res["result"]
        self.assertEqual(count, 0)
        self.assertEqual(unified_img.shape, (1, 64, 64, 3))

    def test_image_loader_aspect_fit_modes(self):
        img = torch.ones((1, 100, 177, 3), dtype=torch.float32)
        mask = torch.zeros((1, 100, 177), dtype=torch.float32)

        # Center Fit (Letterbox)
        fit_img, fit_mask = _fit_image_and_mask_to_target(img, mask, target_h=100, target_w=100, fit_mode="Center Fit (Letterbox / Pad)")
        self.assertEqual(fit_img.shape, (1, 100, 100, 3))
        self.assertEqual(fit_mask.shape, (1, 100, 100))

        # Center Crop
        crop_img, crop_mask = _fit_image_and_mask_to_target(img, mask, target_h=100, target_w=100, fit_mode="Center Crop (Preserve Aspect)")
        self.assertEqual(crop_img.shape, (1, 100, 100, 3))
        self.assertEqual(crop_mask.shape, (1, 100, 100))

    def test_prompt_generator_execution_with_integrated_sampling_options(self):
        class StubModel:
            def __init__(self):
                self.calls = []

            def generate_single(self, **kwargs):
                self.calls.append(kwargs)
                return "<PROMPT>A scenic cyberpunk mountain</PROMPT>\n<TAGS>mountain, neon</TAGS>\n<NEGATIVE>bad</NEGATIVE>"

        stub_model = StubModel()
        gen_node = StoiqoPromptGeneratorNode()

        out = gen_node.generate_prompt(
            prompt_type="Detailed Narrative",
            prompt_style="Cinematic Still (Anamorphic Movie)",
            custom_modifications="rainy night, neon reflections",
            text_input="solitary cyber samurai",
            model=stub_model,
            preset="Custom (Manual Tuning)",
            temperature=0.45,
            max_new_tokens=256,
            negative_prompt_prefix="grainy, ",
        )
        self.assertEqual(len(stub_model.calls), 1)
        self.assertEqual(stub_model.calls[0]["temperature"], 0.45)
        self.assertEqual(stub_model.calls[0]["max_new_tokens"], 256)
        prompts, tags, negs, raws = out["result"]
        self.assertTrue(negs[0].startswith("grainy, "))
        task_prompt = stub_model.calls[0]["task_prompt"]
        self.assertIn("solitary cyber samurai", task_prompt)
        self.assertIn("rainy night, neon reflections", task_prompt)


if __name__ == "__main__":
    unittest.main()
