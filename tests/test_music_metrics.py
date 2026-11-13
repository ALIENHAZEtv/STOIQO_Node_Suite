"""
[STOIQO] Unit Tests — Music Metrics & Syllable Verification
Tests poetic syllable counting, Sinalefe (synalepha) elision,
classical/modern meter classification, line balancing,
and StoiqoMusicPromptEngineNode integration with Low-VRAM offloading.
"""

import unittest
import sys
import os

# Ensure package root is in path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

from core.music import (
    count_poetic_syllables_line,
    classify_meter,
    analyze_lyrics_metrics,
    auto_structure_unstructured_lyrics,
    auto_balance_long_lines,
    parse_music_response,
)
from nodes.music_prompt_node import StoiqoMusicPromptEngineNode


class TestMusicMetrics(unittest.TestCase):

    def test_italian_syllable_count_with_sinalefe(self):
        # "Tra le catene e la ruggine viva" -> 11 metric syllables with sinalefe (catene e)
        line = "Tra le catene e la ruggine viva"
        syl = count_poetic_syllables_line(line, language="Italian")
        self.assertEqual(syl, 11)

        # "urlo nel fango una furia che sale" -> 11 metric syllables with sinalefe (fango una)
        line2 = "urlo nel fango una furia che sale"
        syl2 = count_poetic_syllables_line(line2, language="Italian")
        self.assertEqual(syl2, 11)

    def test_english_syllable_count_rules(self):
        # "love", "make", "time" -> 1 syllable each (silent e)
        self.assertEqual(count_poetic_syllables_line("love make time", language="English"), 3)
        # "little bottle table" -> 2 syllables each (consonant + le)
        self.assertEqual(count_poetic_syllables_line("little bottle table", language="English"), 6)
        # "Torn from the wire in a cathedral of dust" -> 11 syllables
        line = "Torn from the wire in a cathedral of dust"
        self.assertEqual(count_poetic_syllables_line(line, language="English"), 11)

    def test_meter_classification(self):
        self.assertEqual(classify_meter(11.0, language="Italian"), "Endecasillabo (11)")
        self.assertEqual(classify_meter(7.0, language="Italian"), "Settenario (7)")
        self.assertEqual(classify_meter(8.0, language="Italian"), "Ottonario (8)")
        self.assertEqual(classify_meter(8.0, language="English"), "Iambic Tetrameter (8)")
        self.assertEqual(classify_meter(10.0, language="English"), "Iambic Pentameter (10)")

    def test_analyze_lyrics_metrics(self):
        lyrics = (
            "[Verse 1]\n"
            "Tra le catene e la ruggine viva,\n"
            "urlo nel fango una furia che sale.\n"
            "Sotto la pelle la carne si priva,\n"
            "di ogni veleno che squarcia il male.\n\n"
            "[Chorus]\n"
            "Brucia l'abisso e non c'è salvezza,\n"
            "questo è l'amore che spacca i confini!\n"
        )
        res = analyze_lyrics_metrics(lyrics, language="Italian")
        self.assertEqual(res["total_lines"], 6)
        self.assertGreaterEqual(res["rhythmic_balance_score"], 80)
        self.assertIn("Endecasillabo", res["dominant_song_meter"])
        self.assertEqual(len(res["sections"]), 2)
        self.assertEqual(res["sections"][0]["section_name"], "[Verse 1]")
        self.assertTrue(res["sections"][0]["is_balanced"])

    def test_auto_structure_unstructured_lyrics(self):
        unstructured = (
            "Cammino piano lungo questa via\n"
            "tra ombre stese contro la memoria\n"
            "c'è un vento antico che non vola via\n"
            "il tempo scritto dentro la mia storia\n"
            "e brucia il fuoco che non si consuma\n"
            "oltre la notte e il gelo della sera\n"
            "la voce sale limpida tra i monti\n"
            "libera e forte verso la chimera\n"
        )
        structured = auto_structure_unstructured_lyrics(unstructured)
        self.assertIn("[Verse 1]", structured)
        self.assertIn("[Chorus]", structured)
        lines = structured.splitlines()
        self.assertEqual(lines[0], "[Verse 1]")

    def test_auto_balance_long_lines(self):
        long_line = "Questa è una lunghissima riga poetica che continua senza fermarsi mai, e supera ogni limite ragionevole di sillabe per un verso musicale"
        balanced = auto_balance_long_lines(long_line, max_syllables=18, language="Italian")
        lines = [l for l in balanced.splitlines() if l.strip()]
        self.assertGreaterEqual(len(lines), 2)

    def test_parse_music_response_includes_metrics(self):
        sample = """
[TITLE]
Respiro di Ferro

[STYLE]
Italian Alternative Rock, 125 BPM, crunchy overdrive guitars, punchy drums, expressive male vocals, warm studio mix.

[LYRICS]
[Verse 1]
Tra le catene e la ruggine viva,
urlo nel fango una furia che sale.
Sotto la pelle la carne si priva,
di ogni veleno che squarcia il male.

[Chorus]
Brucia l'abisso e non c'è salvezza,
questo è l'amore che spacca i confini!
"""
        parsed = parse_music_response(sample, fallback_idea="rock song", target_language="Italian")
        self.assertIn("metrics", parsed)
        self.assertIn("dominant_meter", parsed)
        self.assertIn("rhythmic_score", parsed)
        self.assertIn("Endecasillabo", parsed["dominant_meter"])
        self.assertGreaterEqual(parsed["rhythmic_score"], 80)

    def test_node_execution_and_low_vram_offload(self):
        class MockModelManager:
            def __init__(self):
                self.model = object()
                self.unloaded = False
                self.keep_in_vram = False

            def generate_single(self, *args, **kwargs):
                return """
[TITLE]
Canto del Mare

[STYLE]
Folk Ballad, 80 BPM, acoustic guitar, soft female voice.

[LYRICS]
[Verse 1]
Onde d'argento nel sole dorato,
porto nel cuore un antico cantato.
Vento che soffia lontano dal porto,
chiama il ricordo del tempo risorto.

[Chorus]
Canta il profondo nel buio del mare,
anime pronte a ricominciare!
"""

            def unload_model(self):
                self.unloaded = True

        mock_mgr = MockModelManager()
        node = StoiqoMusicPromptEngineNode()
        out = node.generate_music_prompt(
            idea="Una ballata folk sul mare",
            language="Italian",
            model=mock_mgr,
        )
        # Check return signature: exactly 12 items
        result_tuple = out["result"]
        self.assertEqual(len(result_tuple), 12)
        style, lyrics, title, abc, mode, dur, bpm, key, time_sig, gtags, vdesc, seed = result_tuple
        self.assertEqual(title, "Canto del Mare")
        self.assertIn("Folk Ballad", style)
        self.assertIn("[Verse 1]", lyrics)
        self.assertEqual(bpm, 80)
        # Check UI info
        ui_info = out["ui"]["music_info"][0]
        self.assertIn("dominant_meter", ui_info)
        self.assertIn("rhythmic_score", ui_info)
        self.assertIn("metric_summary", ui_info)
        # Check low-vram unload was triggered
        self.assertTrue(mock_mgr.unloaded)


if __name__ == "__main__":
    unittest.main()
