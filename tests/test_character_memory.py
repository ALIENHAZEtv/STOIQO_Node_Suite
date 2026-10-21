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


if __name__ == "__main__":
    unittest.main()
