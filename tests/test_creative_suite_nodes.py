"""
[STOIQO] Unit Tests — Creative Suite Native Nodes
Validates:
1. Frequency Separation (Split & Merge)
2. Depth Parallax Extractor (Depth map, 3 segmentation masks, Disparity JSON)
3. Spatial Re-Roll & Generative Fill (ROI cropping, masking, and feathered composite)
4. Face Restoration Hub (Detection, eye clarity, skin smoothing, and elliptical composite)
5. Video Enhancement (Temporal Deflicker & 2x/4x Frame Rate Multiplier)
"""

import os
import sys
import json
import unittest
import torch

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

from nodes.frequency_separation_nodes import StoiqoFrequencySplitNode, StoiqoFrequencyMergeNode
from nodes.depth_parallax_node import StoiqoDepthParallaxExtractor
from nodes.spatial_reroll_node import StoiqoSpatialRerollNode
from nodes.face_restore_hub_node import StoiqoFaceRestoreHub
from nodes.video_enhancement_nodes import StoiqoTemporalDeflickerNode, StoiqoFrameInterpolateNode


class TestCreativeSuiteNodes(unittest.TestCase):

    def setUp(self):
        # Create dummy batch [1, 64, 64, 3] in [0, 1]
        self.dummy_image = torch.rand((1, 64, 64, 3), dtype=torch.float32)
        # Create dummy video batch [6, 32, 32, 3]
        self.dummy_video = torch.rand((6, 32, 32, 3), dtype=torch.float32)

    def test_frequency_split_and_merge(self):
        splitter = StoiqoFrequencySplitNode()
        merger = StoiqoFrequencyMergeNode()

        low, high, meta_str = splitter.split_frequencies(
            image=self.dummy_image,
            blur_radius=8,
            texture_boost=1.0,
            high_pass_mode="linear_offset_50",
        )

        self.assertEqual(low.shape, self.dummy_image.shape)
        self.assertEqual(high.shape, self.dummy_image.shape)
        self.assertTrue(len(meta_str) > 0)

        # Merge back
        merged, = merger.merge_frequencies(
            low_freq_image=low,
            high_freq_image=high,
            texture_strength=1.0,
            reconstruct_mode="linear_offset_50",
            split_meta=meta_str,
        )

        self.assertEqual(merged.shape, self.dummy_image.shape)
        # Merged reconstruction should be close to original within float tolerance
        diff = torch.abs(merged - self.dummy_image).mean().item()
        self.assertLess(diff, 0.05)

    def test_depth_parallax_extractor(self):
        extractor = StoiqoDepthParallaxExtractor()

        depth, fg, mid, bg, meta_json = extractor.extract_depth_parallax(
            image=self.dummy_image,
            fg_threshold=0.65,
            bg_threshold=0.35,
            feather_radius=4,
            invert_depth=False,
            mesh_subdivisions=16,
        )

        self.assertEqual(depth.shape, self.dummy_image.shape)
        self.assertEqual(fg.shape, (1, 64, 64))
        self.assertEqual(mid.shape, (1, 64, 64))
        self.assertEqual(bg.shape, (1, 64, 64))

        meta = json.loads(meta_json)
        self.assertIn("perspective_layers", meta)
        self.assertEqual(len(meta["perspective_layers"]), 3)

    def test_spatial_reroll_node(self):
        reroller = StoiqoSpatialRerollNode()

        # Step 1: Crop ROI without replacement
        bbox_in = json.dumps({"x": 10, "y": 10, "width": 30, "height": 30})
        comp, crop, mask, out_bbox = reroller.process_spatial_reroll(
            image=self.dummy_image,
            feather_radius=4,
            color_harmonization=True,
            crop_padding_percent=0.1,
            bbox_json=bbox_in,
        )

        self.assertEqual(comp.shape, self.dummy_image.shape)
        self.assertEqual(crop.shape[1], 30)
        self.assertEqual(crop.shape[2], 30)
        self.assertEqual(mask.shape, (1, 30, 30))

        # Step 2: Composite replacement image into ROI
        replacement = torch.ones_like(crop)
        comp_rep, _, _, _ = reroller.process_spatial_reroll(
            image=self.dummy_image,
            feather_radius=4,
            color_harmonization=False,
            crop_padding_percent=0.0,
            replacement_image=replacement,
            bbox_json=bbox_in,
        )
        self.assertEqual(comp_rep.shape, self.dummy_image.shape)

    def test_face_restore_hub(self):
        restorer = StoiqoFaceRestoreHub()

        restored, primary_crop, primary_mask, count, meta = restorer.restore_portrait(
            image=self.dummy_image,
            fidelity_weight=0.8,
            skin_smoothing=0.3,
            eye_clarity=1.2,
            feather_edges=8,
            face_padding_percent=0.2,
        )

        self.assertEqual(restored.shape, self.dummy_image.shape)
        self.assertTrue(count >= 1)
        self.assertEqual(primary_mask.shape, (1, 64, 64))

    def test_video_enhancements(self):
        deflickerer = StoiqoTemporalDeflickerNode()
        interpolator = StoiqoFrameInterpolateNode()

        # Test deflicker
        stab, metrics_str = deflickerer.deflicker_video(
            images=self.dummy_video,
            window_size=3,
            luminance_tolerance=0.08,
            stabilization_strength=0.85,
        )
        self.assertEqual(stab.shape, self.dummy_video.shape)
        metrics = json.loads(metrics_str)
        self.assertEqual(metrics["total_frames"], 6)

        # Test 2x interpolation (6 frames -> 11 frames)
        interp, out_count, meta_str = interpolator.interpolate_frames(
            images=self.dummy_video,
            multiplier="2x (Double FPS)",
            motion_smoothness=1.0,
            blend_curve="cosine_smooth",
        )
        expected_frames = (6 - 1) * 2 + 1
        self.assertEqual(out_count, expected_frames)
        self.assertEqual(interp.shape[0], expected_frames)
        self.assertEqual(interp.shape[1:], self.dummy_video.shape[1:])


if __name__ == "__main__":
    unittest.main()
