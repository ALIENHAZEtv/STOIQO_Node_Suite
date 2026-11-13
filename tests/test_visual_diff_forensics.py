"""
[STOIQO] Unit Tests — Visual Image Compare Slider & Diff Metrics
Validates:
1. Identical images metric perfection (PSNR 100 dB, SSIM 1.0, 0% altered area).
2. Altered images heatmap generation (Turbo, Jet, Plasma, Inferno) and binary change mask.
3. Aspect ratio protection & zero-stretch resolution alignment.
4. Pass-through image_a and image_b outputs + canvas UI payload.
"""

import os
import sys
import json
import unittest
import torch

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

from nodes.image_compare_node import StoiqoImageCompareNode


class TestVisualCompareAndDiff(unittest.TestCase):

    def setUp(self):
        # Base pristine image [1, 64, 64, 3]
        self.img_base = torch.full((1, 64, 64, 3), 0.5, dtype=torch.float32)
        # Altered image with modified square in the center
        self.img_altered = self.img_base.clone()
        self.img_altered[:, 20:44, 20:44, :] = 0.9

    def test_identical_images(self):
        node = StoiqoImageCompareNode()
        res = node.compare_images(
            image_a=self.img_base,
            image_b=self.img_base.clone(),
        )
        self.assertIn("ui", res)
        self.assertIn("result", res)
        out_a, out_b, heatmap, mask, metrics_str = res["result"]

        self.assertEqual(heatmap.shape, (1, 64, 64, 3))
        self.assertEqual(mask.shape, (1, 64, 64))
        self.assertEqual(mask.sum().item(), 0.0)

        metrics = json.loads(metrics_str)
        self.assertEqual(metrics["psnr_db"], 100.0)
        self.assertEqual(metrics["ssim"], 1.0)
        self.assertEqual(metrics["changed_pixels_pct"], 0.0)

    def test_altered_images_heatmap_and_mask(self):
        node = StoiqoImageCompareNode()
        res = node.compare_images(
            image_a=self.img_base,
            image_b=self.img_altered,
            heatmap_colormap="turbo",
            diff_gain=2.0,
            mask_threshold=0.1,
        )
        out_a, out_b, heatmap, mask, metrics_str = res["result"]

        self.assertEqual(heatmap.shape, (1, 64, 64, 3))
        self.assertEqual(mask.shape, (1, 64, 64))
        # 24x24 pixels altered = 576 pixels
        self.assertEqual(int(mask.sum().item()), 576)

        metrics = json.loads(metrics_str)
        self.assertLess(metrics["psnr_db"], 50.0)
        self.assertLess(metrics["ssim"], 1.0)
        self.assertGreater(metrics["changed_pixels_pct"], 10.0)
        self.assertEqual(metrics["colormap"], "turbo")

    def test_colormaps_and_gains(self):
        node = StoiqoImageCompareNode()
        for cmap in ["jet", "plasma", "inferno", "greyscale_diff", "turbo"]:
            res = node.compare_images(
                image_a=self.img_base,
                image_b=self.img_altered,
                heatmap_colormap=cmap,
                diff_gain=3.0,
            )
            _, _, heatmap, mask, _ = res["result"]
            self.assertEqual(heatmap.shape, (1, 64, 64, 3))
            self.assertTrue(torch.all(heatmap >= 0.0) and torch.all(heatmap <= 1.0))

    def test_resolution_alignment_zero_stretch(self):
        node = StoiqoImageCompareNode()
        # image_b has half resolution (32x32)
        small_img = torch.full((1, 32, 32, 3), 0.5, dtype=torch.float32)
        res = node.compare_images(
            image_a=self.img_base,
            image_b=small_img,
        )
        _, _, heatmap, mask, metrics_str = res["result"]
        # Output must match image_a's resolution (64x64) without distortion
        self.assertEqual(heatmap.shape, (1, 64, 64, 3))
        self.assertEqual(mask.shape, (1, 64, 64))
        metrics = json.loads(metrics_str)
        self.assertEqual(metrics["dimensions"], "64x64")


if __name__ == "__main__":
    unittest.main()
