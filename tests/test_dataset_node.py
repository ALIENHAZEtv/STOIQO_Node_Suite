"""
Unit tests for [STOIQO] Dataset & LoRA Training Toolkit Node
"""

import os
import sys
import unittest
import tempfile
import shutil
import torch
from PIL import Image

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

from nodes.dataset_node import StoiqoDatasetWriterNode, _compute_dhash, _hamming_similarity


class TestDatasetNode(unittest.TestCase):
    def setUp(self):
        self.node = StoiqoDatasetWriterNode()
        self.temp_dir = tempfile.mkdtemp(prefix="stoiqo_test_dataset_")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_caption_cleaning_and_blacklist(self):
        captions, tags, negs, _ = self.node.process_and_save(
            caption="A photorealistic portrait of an elf, blurry, watermark, 8k resolution",
            tags="1girl, elf, pointy ears, watermark, signature, solo, elf",
            negative="ugly, deformed",
            trigger_word="sks_elf",
            blacklist_tags="watermark, signature, blurry",
            output_dir=self.temp_dir,
            save_txt=False,
        )

        cap = captions[0]
        tag_str = tags[0]

        # Blacklist terms stripped
        self.assertNotIn("watermark", cap)
        self.assertNotIn("blurry", cap)
        self.assertNotIn("watermark", tag_str)
        self.assertNotIn("signature", tag_str)

        # Trigger word pinned at start
        self.assertTrue(cap.startswith("sks_elf,"))
        self.assertTrue(tag_str.startswith("sks_elf,"))

        # Tag deduplication: 'elf' appeared twice, should only appear once
        tag_list = [t.strip() for t in tag_str.split(",")]
        self.assertEqual(tag_list.count("elf"), 1)

    def test_caption_format_routing(self):
        # 1. Booru Tags format
        c_booru, _, _, _ = self.node.process_and_save(
            caption="A beautiful dragon over a castle",
            tags="dragon, castle, clouds",
            trigger_word="sks_dragon",
            caption_format="Booru Tags (.txt)",
            output_dir=self.temp_dir,
            save_txt=True,
            fallback_prefix="booru_test",
        )
        self.assertEqual(c_booru[0], "sks_dragon, dragon, castle, clouds")
        txt_path = os.path.join(self.temp_dir, "booru_test_0001.txt")
        self.assertTrue(os.path.exists(txt_path))
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "sks_dragon, dragon, castle, clouds")

        # 2. Combined format
        c_comb, _, _, _ = self.node.process_and_save(
            caption="Majestic creature flying in thunder",
            tags="dragon, wings, lightning",
            trigger_word="sks_dragon",
            caption_format="Combined (Trigger + Tags + Prose)",
            output_dir=self.temp_dir,
            save_txt=True,
            fallback_prefix="comb_test",
        )
        txt_path2 = os.path.join(self.temp_dir, "comb_test_0001.txt")
        self.assertTrue(os.path.exists(txt_path2))
        with open(txt_path2, "r", encoding="utf-8") as f:
            content2 = f.read()
        self.assertIn("sks_dragon, dragon, wings, lightning", content2)
        self.assertIn("Majestic creature flying in thunder", content2)

    def test_tag_shuffling_with_keep_tokens(self):
        tags_in = "tagA, tagB, tagC, tagD, tagE, tagF"
        _, tags_out, _, _ = self.node.process_and_save(
            caption="test",
            tags=tags_in,
            trigger_word="my_trigger",
            shuffle_tags=True,
            keep_tokens=2,  # keep my_trigger and tagA in fixed positions
            seed=12345,
            output_dir=self.temp_dir,
            save_txt=False,
        )
        out_list = [t.strip() for t in tags_out[0].split(",")]
        # Pinned tokens remain in index 0 and 1
        self.assertEqual(out_list[0], "my_trigger")
        self.assertEqual(out_list[1], "tagA")
        # Remaining tokens are shuffled
        self.assertEqual(set(out_list[2:]), {"tagB", "tagC", "tagD", "tagE", "tagF"})

    def test_atomic_image_and_caption_saving(self):
        # Create a mock 64x64 RGB image tensor
        img_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
        img_tensor[0, :, :, 0] = 1.0  # pure red

        _, _, _, out_imgs = self.node.process_and_save(
            caption="A pure red square studio backdrop",
            tags="red, solid color, studio",
            trigger_word="sks_red",
            image=img_tensor,
            save_image=True,
            image_format="PNG (Lossless)",
            save_txt=True,
            save_json_metadata=True,
            output_dir=self.temp_dir,
            fallback_prefix="atomic_test",
        )

        img_path = os.path.join(self.temp_dir, "atomic_test_0001.png")
        txt_path = os.path.join(self.temp_dir, "atomic_test_0001.txt")
        json_path = os.path.join(self.temp_dir, "atomic_test_0001.json")

        self.assertTrue(os.path.exists(img_path))
        self.assertTrue(os.path.exists(txt_path))
        self.assertTrue(os.path.exists(json_path))

        # Check saved image dimensions
        with Image.open(img_path) as im:
            self.assertEqual(im.size, (64, 64))

    def test_perceptual_dhash_deduplication(self):
        # Batch of 3 images: img0 and img1 are identical; img2 is completely different
        img0 = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
        img1 = torch.zeros((1, 64, 64, 3), dtype=torch.float32)  # Duplicate!
        img2 = torch.ones((1, 64, 64, 3), dtype=torch.float32)   # Distinct!
        batch_tensor = torch.cat([img0, img1, img2], dim=0)

        captions = ["Frame 0", "Frame 1 (Duplicate)", "Frame 2 (Distinct)"]
        node_fresh = StoiqoDatasetWriterNode()

        out_caps, _, _, out_imgs = node_fresh.process_and_save(
            caption=captions,
            image=batch_tensor,
            deduplicate_images=True,
            similarity_threshold=0.95,
            save_image=True,
            save_txt=True,
            output_dir=self.temp_dir,
            fallback_prefix="dedup_test",
        )

        # Frame 1 should have been skipped! So total saved files should be 2, not 3!
        saved_txts = [f for f in os.listdir(self.temp_dir) if f.endswith(".txt")]
        saved_pngs = [f for f in os.listdir(self.temp_dir) if f.endswith(".png")]
        self.assertEqual(len(saved_txts), 2)
        self.assertEqual(len(saved_pngs), 2)


if __name__ == "__main__":
    unittest.main()
