"""
[STOIQO] Unit tests for Universal Context Pipe and Webhook Notifier nodes.
"""

import unittest
import json
import os
import shutil
import tempfile
from nodes.universal_pipe_node import StoiqoUniversalPipeInNode, StoiqoUniversalPipeOutNode
from nodes.webhook_notifier_node import StoiqoWebhookNotifierNode


class TestUniversalPipeAndWebhook(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_universal_pipe_pack_and_unpack(self):
        packer = StoiqoUniversalPipeInNode()
        unpacker = StoiqoUniversalPipeOutNode()

        dummy_model = "MockDiffusionModel"
        dummy_clip = "MockClipEncoder"
        dummy_vae = "MockVAE"
        dummy_pos = "Positive Conditioning"
        dummy_neg = "Negative Conditioning"
        dummy_seed = 42

        # 1. Pack
        pipe_tuple, pipe_dict = packer.pack_pipe(
            model=dummy_model,
            clip=dummy_clip,
            vae=dummy_vae,
            positive=dummy_pos,
            negative=dummy_neg,
            seed=dummy_seed,
        )

        self.assertIsInstance(pipe_dict, dict)
        self.assertEqual(pipe_dict["model"], dummy_model)
        self.assertEqual(pipe_dict["seed"], 42)

        # 2. Unpack
        (
            ret_pipe,
            ret_model,
            ret_clip,
            ret_vae,
            ret_pos,
            ret_neg,
            ret_latent,
            ret_img,
            ret_seed,
        ) = unpacker.unpack_pipe(pipe_dict)

        self.assertEqual(ret_model, dummy_model)
        self.assertEqual(ret_clip, dummy_clip)
        self.assertEqual(ret_vae, dummy_vae)
        self.assertEqual(ret_pos, dummy_pos)
        self.assertEqual(ret_neg, dummy_neg)
        self.assertEqual(ret_seed, 42)

    def test_universal_pipe_interoperability_with_rgthree_tuple(self):
        unpacker = StoiqoUniversalPipeOutNode()

        # Simulate an external rgthree/Efficiency tuple: (model, clip, vae, positive, negative, latent, images, seed)
        external_tuple = (
            "ModelX",
            "ClipY",
            "VaeZ",
            "PosCond",
            "NegCond",
            {"samples": "latent_tensor"},
            None,
            9999,
        )

        (
            _,
            ret_model,
            ret_clip,
            ret_vae,
            ret_pos,
            ret_neg,
            ret_latent,
            ret_img,
            ret_seed,
        ) = unpacker.unpack_pipe(external_tuple)

        self.assertEqual(ret_model, "ModelX")
        self.assertEqual(ret_clip, "ClipY")
        self.assertEqual(ret_vae, "VaeZ")
        self.assertEqual(ret_pos, "PosCond")
        self.assertEqual(ret_neg, "NegCond")
        self.assertEqual(ret_seed, 9999)

    def test_webhook_notifier_manifest_generation(self):
        notifier = StoiqoWebhookNotifierNode()

        dummy_pipe = {
            "model": "Flux1-Dev",
            "positive_prompt": "Cinematic portrait of a cyberpunk explorer",
            "seed": 123456,
        }

        pipe_out, img_out, status, json_str = notifier.dispatch_notification(
            service_format="Generic JSON POST",
            webhook_url="",  # No live HTTP dispatch during offline unit test
            title="Batch Complete",
            message="All 10 images rendered.",
            save_json_manifest=True,
            manifest_subfolder="test_manifests",
            pipe=dummy_pipe,
            seed=123456,
        )

        self.assertIn("Manifest saved", status)
        self.assertIn("123456", json_str)
        payload = json.loads(json_str)
        self.assertEqual(payload["seed"], 123456)
        self.assertEqual(payload["title"], "Batch Complete")
        self.assertIn("cyberpunk", payload["prompt"])

    def test_webhook_notifier_rejects_non_http_scheme(self):
        notifier = StoiqoWebhookNotifierNode()
        for dangerous_url in ["file:///etc/passwd", "ftp://example.com/upload", "gopher://evil.com"]:
            pipe_out, img_out, status, json_str = notifier.dispatch_notification(
                service_format="Generic JSON POST",
                webhook_url=dangerous_url,
                title="Security Test",
                message="Checking scheme validation",
                save_json_manifest=False,
                manifest_subfolder="test_manifests",
            )
            self.assertIn("rejected", status.lower())
            self.assertIn("http", status.lower())


if __name__ == "__main__":
    unittest.main()
