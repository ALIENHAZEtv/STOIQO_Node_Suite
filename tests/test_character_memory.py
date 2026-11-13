"""
Unit tests for [STOIQO] Character Memory Bank (Lorebook & DNA) Node
"""

import os
import sys
import unittest
import torch

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

from nodes.character_memory_node import StoiqoCharacterMemoryNode, PRESETS


class TestCharacterMemoryNode(unittest.TestCase):
    def setUp(self):
        self.node = StoiqoCharacterMemoryNode()

    def test_preset_overlay(self):
        full_prompt, ctx, dna, tag, neg, ref = self.node.process_character(
            character_name="Kaelen",
            trigger_tag="kaelen_cyber",
            preset_profile="Cyberpunk Netrunner (Neon / Chrome / Micro-circuits)",
            gender_age="",
            face_and_skin="",
            eye_color_style="",
            hair_style_color="",
            body_build="",
            distinctive_marks="",
            signature_outfit="",
            accessories_props="",
            personality_vibe="",
            negative_constraints="",
            injection_mode="Always Prepend (Force Character DNA)",
            user_prompt="standing in the rainy neon street",
        )
        self.assertIn("electric violet", dna)
        self.assertIn("silver bob", dna)
        self.assertIn("Kaelen", full_prompt)
        self.assertIn("standing in the rainy neon street", full_prompt)
        self.assertIn("wrong eye color", neg)
        self.assertEqual(tag, "kaelen_cyber")
        self.assertIsInstance(ctx, dict)
        self.assertEqual(ctx["character_name"], "Kaelen")
        self.assertIsInstance(ref, torch.Tensor)

    def test_custom_character_dna_compilation(self):
        full_prompt, ctx, dna, tag, neg, ref = self.node.process_character(
            character_name="Elena Frost",
            trigger_tag="elena_frost",
            preset_profile="Custom (User Defined)",
            gender_age="woman in early 30s",
            face_and_skin="pale skin, high cheekbones, thin scar across bridge of nose",
            eye_color_style="piercing sapphire eyes",
            hair_style_color="long platinum braided hair",
            body_build="tall athletic build",
            distinctive_marks="wolf tattoo on left shoulder",
            signature_outfit="white winter fur cloak, dark leather armor",
            accessories_props="silver dagger at belt",
            personality_vibe="cold, calculating, unyielding",
            negative_constraints="brown hair, dark skin, smiling, modern clothes",
            injection_mode="Always Prepend (Force Character DNA)",
            user_prompt="overlooking a frozen valley",
        )
        self.assertIn("piercing sapphire eyes", dna)
        self.assertIn("thin scar across bridge of nose", dna)
        self.assertIn("Elena Frost", full_prompt)
        self.assertIn("white winter fur cloak", full_prompt)
        self.assertEqual(ctx["trigger_tag"], "elena_frost")

    def test_smart_detect_injection(self):
        # 1. Trigger present in prompt -> Should inject
        full_p, _, _, _, _, _ = self.node.process_character(
            character_name="Aria",
            trigger_tag="aria_netrunner",
            preset_profile="Cyberpunk Netrunner (Neon / Chrome / Micro-circuits)",
            gender_age="young woman",
            face_and_skin="pale skin",
            eye_color_style="violet eyes",
            hair_style_color="silver bob",
            body_build="athletic",
            distinctive_marks="neural port",
            injection_mode="Smart Detect (Inject only when Name or Trigger is in Prompt)",
            user_prompt="A cinematic portrait of Aria hacking a server terminal",
        )
        self.assertIn("silver bob", full_p)
        self.assertIn("hacking a server terminal", full_p)

        # 2. Trigger NOT in prompt -> Should NOT inject
        full_p_no, _, _, _, _, _ = self.node.process_character(
            character_name="Aria",
            trigger_tag="aria_netrunner",
            preset_profile="Cyberpunk Netrunner (Neon / Chrome / Micro-circuits)",
            gender_age="young woman",
            face_and_skin="pale skin",
            eye_color_style="violet eyes",
            hair_style_color="silver bob",
            body_build="athletic",
            distinctive_marks="neural port",
            injection_mode="Smart Detect (Inject only when Name or Trigger is in Prompt)",
            user_prompt="A lonely cybernetic car parked in an empty alleyway at night",
        )
        self.assertEqual(full_p_no, "A lonely cybernetic car parked in an empty alleyway at night")

    def test_passthrough_reference_image(self):
        ref_in = torch.ones((1, 128, 128, 3), dtype=torch.float32)
        _, _, _, _, _, ref_out = self.node.process_character(
            character_name="TestChar",
            trigger_tag="test",
            preset_profile="Custom (User Defined)",
            gender_age="man",
            face_and_skin="skin",
            eye_color_style="eyes",
            hair_style_color="hair",
            body_build="build",
            distinctive_marks="",
            reference_image=ref_in,
        )
        self.assertEqual(ref_out.shape, (1, 128, 128, 3))
        self.assertTrue(torch.equal(ref_in, ref_out))

    def test_json_disk_save_and_load(self):
        # 1. Save profile to disk
        test_save_name = "test_unit_hero"
        full_p, ctx, dna, tag, neg, _ = self.node.process_character(
            character_name="Nova Prime",
            trigger_tag="nova_prime_lora",
            character_profile="Custom (Manual Edit)",
            physical_dna="android warrior with glowing gold ocular optics, polished chrome plating",
            outfit_and_gear="quantum energy shield, solar energy cannon",
            negative_constraints="human skin, organic tissue, broken armor",
            personality_vibe="calculating, protective, resolute",
            save_profile_as=test_save_name,
        )
        self.assertEqual(ctx["character_name"], "Nova Prime")
        self.assertIn("glowing gold ocular optics", dna)

        # Verify file exists on disk
        presets_dir = os.path.join(root, "presets", "characters")
        saved_file = os.path.join(presets_dir, f"{test_save_name}.character.json")
        self.assertTrue(os.path.exists(saved_file))

        # 2. Load from disk via custom_json_data file path
        _, ctx_loaded, dna_loaded, _, _, _ = self.node.process_character(
            custom_json_data=saved_file,
            injection_mode="Always Prepend (Force Character DNA)",
        )
        self.assertEqual(ctx_loaded["character_name"], "Nova Prime")
        self.assertEqual(ctx_loaded["trigger_tag"], "nova_prime_lora")
        self.assertIn("glowing gold ocular optics", dna_loaded)

        # Cleanup
        try:
            if os.path.exists(saved_file):
                os.remove(saved_file)
        except Exception:
            pass

    def test_word_boundary_safety(self):
        # Ensure 'Mia' does NOT match 'Miami' or 'Marianne'
        full_p, _, _, _, _, _ = self.node.process_character(
            character_name="Mia",
            trigger_tag="mia",
            character_profile="Custom (Manual Edit)",
            physical_dna="athletic runner",
            injection_mode="Smart Detect (Inject only when Name or Trigger is in Prompt)",
            user_prompt="Traveling across Miami at dusk",
        )
        # Should NOT inject because 'Mia' is part of 'Miami'
        self.assertEqual(full_p, "Traveling across Miami at dusk")

        # Now test with exact word 'Mia'
        full_p_match, _, _, _, _, _ = self.node.process_character(
            character_name="Mia",
            trigger_tag="mia",
            character_profile="Custom (Manual Edit)",
            physical_dna="athletic runner",
            injection_mode="Smart Detect (Inject only when Name or Trigger is in Prompt)",
            user_prompt="Mia is jogging through the city park",
        )
        self.assertIn("athletic runner", full_p_match)
        self.assertIn("Mia is jogging", full_p_match)


if __name__ == "__main__":
    unittest.main()
