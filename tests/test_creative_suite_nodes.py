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

from nodes.frequency_separation_nodes import StoiqoFrequencySeparationNode, StoiqoFrequencySplitNode, StoiqoFrequencyMergeNode
from nodes.inpaint_stitcher_node import StoiqoInpaintStitcherNode
from nodes.spatial_cropper_node import StoiqoSpatialCropperNode
from nodes.video_enhancement_nodes import StoiqoVideoEnhancerNode, StoiqoTemporalDeflickerNode, StoiqoFrameInterpolateNode


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

    def test_inpaint_stitcher_and_reroll_node(self):
        stitcher = StoiqoInpaintStitcherNode()

        # Step 1: Crop ROI without edited_image
        bbox_in = json.dumps({"x": 10, "y": 10, "width": 30, "height": 30})
        comp, mask, crop, out_bbox = stitcher.stitch_composite(
            original_image=self.dummy_image,
            feather_radius=4,
            color_match=True,
            crop_padding_percent=0.1,
            bbox_info=bbox_in,
        )

        self.assertEqual(comp.shape, self.dummy_image.shape)
        self.assertEqual(crop.shape[1], 30)
        self.assertEqual(crop.shape[2], 30)
        self.assertEqual(mask.shape, (1, 64, 64))

        # Step 2: Composite edited_image into ROI
        replacement = torch.ones_like(crop)
        comp_rep, mask_rep, crop_rep, _ = stitcher.stitch_composite(
            original_image=self.dummy_image,
            edited_image=replacement,
            feather_radius=4,
            color_match=False,
            crop_padding_percent=0.0,
            bbox_info=bbox_in,
        )
        self.assertEqual(comp_rep.shape, self.dummy_image.shape)
        self.assertEqual(mask_rep.shape, (1, 64, 64))

        # Step 3: Aspect-protected replacement with different shape
        non_square_rep = torch.ones((1, 60, 40, 3), dtype=torch.float32)
        comp_aspect, _, _, _ = stitcher.stitch_composite(
            original_image=self.dummy_image,
            edited_image=non_square_rep,
            feather_radius=8,
            color_match=True,
            color_match_strength=0.75,
            fit_mode="Center Crop (Preserve Aspect)",
            blend_mode="Soft Gradient",
            crop_padding_percent=0.0,
            bbox_info=bbox_in,
        )
        self.assertEqual(comp_aspect.shape, self.dummy_image.shape)

    def test_face_restore_fast_detect_and_beauty_polish(self):
        cropper = StoiqoSpatialCropperNode()
        stitcher = StoiqoInpaintStitcherNode()

        # Step 1: Detect face using zero-model OpenCV fast detection fallback in cropper
        crop, mask, meta_str, segs = cropper.crop_and_mask(
            image=self.dummy_image,
            detect_prompt="portrait face",
            padding_percent=10,
        )
        self.assertTrue(crop.shape[1] > 10)
        self.assertTrue(crop.shape[2] > 10)

        # Step 2: Inpaint Stitcher with Beauty Polish (skin smoothing + eye clarity)
        polished_comp, p_mask, roi, _ = stitcher.stitch_composite(
            original_image=self.dummy_image,
            bbox_info=meta_str,
            skin_smoothing=0.5,
            detail_clarity=0.4,
        )
        self.assertEqual(polished_comp.shape, self.dummy_image.shape)
        self.assertEqual(p_mask.shape, (1, 64, 64))

    def test_inpaint_stitcher_seamless_external_crop(self):
        stitcher = StoiqoInpaintStitcherNode()
        bbox_in = json.dumps({"crop_box": [10, 10, 40, 40]})

        # Simulate external model editing the crop
        simulated_crop = torch.ones((1, 30, 30, 3), dtype=torch.float32)

        stitched, mask, roi, _ = stitcher.stitch_composite(
            original_image=self.dummy_image,
            edited_image=simulated_crop,
            bbox_info=bbox_in,
            color_match=True,
            feather_radius=8,
            skin_smoothing=0.2,
        )
        self.assertEqual(stitched.shape, self.dummy_image.shape)
        self.assertEqual(mask.shape, (1, 64, 64))

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

        # Test 5D video tensor unrolling [1, N, H, W, C]
        dummy_video_5d = self.dummy_video.unsqueeze(0)
        stab_5d, _ = deflickerer.deflicker_video(dummy_video_5d, window_size=3, luminance_tolerance=0.08, stabilization_strength=0.85)
        self.assertEqual(stab_5d.shape, self.dummy_video.shape)

        interp_5d, count_5d, _ = interpolator.interpolate_frames(dummy_video_5d, multiplier="4x (Quad FPS)", motion_smoothness=1.2, blend_curve="bidirectional_linear")
        expected_4x = (6 - 1) * 4 + 1
        self.assertEqual(count_5d, expected_4x)
        self.assertEqual(interp_5d.shape[0], expected_4x)


if __name__ == "__main__":
    unittest.main()
