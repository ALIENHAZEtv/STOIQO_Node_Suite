import os
import sys
import unittest
import tempfile
import torch
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nodes.folder_iterator_node import StoiqoSmartFolderImageIterator
from nodes.image_loader_node import StoiqoImageLoaderNode


class TestSmartFolderImageIterator(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.folder = self.temp_dir.name
        self.node = StoiqoSmartFolderImageIterator()

        # Create dummy images
        for i in range(5):
            arr = np.full((64, 64, 3), i * 40, dtype=np.uint8)
            img = Image.fromarray(arr)
            img.save(os.path.join(self.folder, f"sample_{i:02d}.png"))

        # Create a mask companion for sample_00.png
        mask_arr = np.full((64, 64), 255, dtype=np.uint8)
        mask_img = Image.fromarray(mask_arr)
        mask_img.save(os.path.join(self.folder, "sample_00_mask.png"))

        # Create a standalone image whose name ends with _mask but has no base companion
        mask_standalone = Image.fromarray(arr)
        mask_standalone.save(os.path.join(self.folder, "lone_mask.png"))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cache_and_mask_filtering(self):
        # 5 sample images + 1 lone_mask (sample_00_mask is excluded because sample_00 exists)
        files = StoiqoSmartFolderImageIterator._get_cached_files(self.folder, recursive=False)
        self.assertIn("sample_00.png", files)
        self.assertIn("sample_04.png", files)
        self.assertIn("lone_mask.png", files)
        self.assertNotIn("sample_00_mask.png", files)
        self.assertEqual(len(files), 6)

        # Cache test: re-fetching from memory returns identical list without disk rescan
        cached = StoiqoSmartFolderImageIterator._get_cached_files(self.folder, recursive=False)
        self.assertIs(files, cached)

    def test_single_iterative_mode(self):
        res = self.node.load_image(
            folder_path=self.folder,
            load_mode="Single (Iterative)",
            index=0,
            iteration_mode="Sequential",
        )
        self.assertIn("result", res)
        img, mask, filename, w, h = res["result"]
        self.assertEqual(img.shape, (1, 64, 64, 3))
        self.assertEqual(mask.shape, (1, 64, 64))
        self.assertEqual(filename, "lone_mask.png") # lone_mask sorts before sample_00
        self.assertEqual(w, 64)
        self.assertEqual(h, 64)

    def test_reverse_iteration_mode(self):
        res = self.node.load_image(
            folder_path=self.folder,
            load_mode="Single (Iterative)",
            index=0,
            iteration_mode="Reverse",
        )
        img, mask, filename, w, h = res["result"]
        # Last file naturally is sample_04.png
        self.assertEqual(filename, "sample_04.png")

    def test_random_seed_reproducible(self):
        res1 = self.node.load_image(
            folder_path=self.folder,
            load_mode="Single (Iterative)",
            index=0,
            iteration_mode="Random (Seed)",
            seed=42,
        )
        res2 = self.node.load_image(
            folder_path=self.folder,
            load_mode="Single (Iterative)",
            index=0,
            iteration_mode="Random (Seed)",
            seed=42,
        )
        self.assertEqual(res1["result"][2], res2["result"][2])

    def test_batch_all_mode(self):
        res = self.node.load_image(
            folder_path=self.folder,
            load_mode="Batch (All in Folder)",
            max_batch_images=4,
        )
        self.assertIn("result", res)
        img, mask, filename, w, h = res["result"]
        # Batch of 4 images
        self.assertEqual(img.shape, (4, 64, 64, 3))
        self.assertEqual(mask.shape, (4, 64, 64))
        self.assertIn("Batch", filename)

    def test_loop_folder(self):
        # Index 10 with 6 files: 10 % 6 = 4 -> index 4
        res_loop = self.node.load_image(
            folder_path=self.folder,
            load_mode="Single (Iterative)",
            index=10,
            loop_folder=True,
        )
        self.assertNotEqual(res_loop["result"][2], "COMPLETED")

        # Without loop, index 10 is out of bounds -> COMPLETED
        res_no_loop = self.node.load_image(
            folder_path=self.folder,
            load_mode="Single (Iterative)",
            index=10,
            loop_folder=False,
        )
        self.assertEqual(res_no_loop[2], "COMPLETED")


if __name__ == "__main__":
    unittest.main()
