"""
[STOIQO] Unit Tests — Music Parser & Section Extractor
Tests parsing resilience across bracket headers, XML tags, and Markdown syntax.
Ensures zero placeholder hallucination and strict cleanup.
"""

import unittest
import sys
import os

# Ensure package root is in path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

from core.music_prompts import (
    parse_music_response,
    clean_repetition_artifacts,
    normalize_lyrics_sections,
    detect_existing_lyrics,
)


class TestMusicParser(unittest.TestCase):

    def test_parse_bracket_headers(self):
        sample = """
[TITLE]
Eclissi di Cenere

[STYLE]
Melodic Death Metal, 140 BPM, Drop-D distorted guitars, double bass drums, gothic choir, growl verses and belted chorus.

[LYRICS]
[Verse 1]
(4 lines)
Sulle macerie di un impero muto
cammina il sangue che non si è arreso.
Un giuramento stretto nel buio,
un nodo d'ombra che resta acceso.

[Chorus]
Risorgeremo dalla fornace,
oltre il silenzio d'ogni ferita!
"""
        parsed = parse_music_response(sample, fallback_idea="death metal", target_language="Italian")
        self.assertEqual(parsed["title"], "Eclissi di Cenere")
        self.assertIn("Melodic Death Metal", parsed["style"])
        self.assertIn("[Verse 1]", parsed["lyrics"])
        self.assertIn("Sulle macerie di un impero muto", parsed["lyrics"])
        self.assertIn("[Chorus]", parsed["lyrics"])
        # Verify parenthetical "(4 lines)" was stripped
        self.assertNotIn("(4 lines)", parsed["lyrics"])
        self.assertNotIn("(4 lines)", parsed["style"])

    def test_parse_markdown_headers(self):
        sample = """
### Title
La Rinascita

### Style
Symphonic Metal, 140 BPM, Gritty Powerful Male Vocal

### Lyrics
#### Verse 1
Nelle fiamme di un fuoco che divora,
il sangue non si arrende.

#### Chorus
L'amore risorge sempre,
oltre ogni distruzione!
"""
        parsed = parse_music_response(sample, fallback_idea="metal", target_language="Italian")
        self.assertEqual(parsed["title"], "La Rinascita")
        self.assertIn("140 BPM", parsed["style"])
        self.assertIn("[Verse 1]", parsed["lyrics"])
        self.assertIn("[Chorus]", parsed["lyrics"])


    def test_parse_xml_headers(self):
        sample = """
<TITLE>Flame of Eternity</TITLE>
<STYLE>Contemporary Synthpop, 120 BPM, analog juno synths, punchy 808 drums, airy female vocals.</STYLE>
<ABC_PLANNING>false</ABC_PLANNING>
<MODE>full</MODE>
<DURATION>210.0</DURATION>
<LYRICS>
[Verse 1]
Walking through the neon rain
Shadows dancing on the glass
Nothing ever feels the same
When the summer turns to ash

[Chorus]
Hold me through the darkest night
We are burning like a star
</LYRICS>
"""
        parsed = parse_music_response(sample, fallback_idea="synthpop song", target_language="English")
        self.assertEqual(parsed["title"], "Flame of Eternity")
        self.assertIn("120 BPM", parsed["style"])
        self.assertIn("[Verse 1]", parsed["lyrics"])
        self.assertIn("Walking through the neon rain", parsed["lyrics"])
        self.assertEqual(parsed["max_duration"], 210.0)

    def test_parse_never_emits_fake_placeholders(self):
        # Empty or degraded text should NOT produce kindergarten templates
        sample = "Qualche frase sconnessa senza senso."
        parsed = parse_music_response(sample, fallback_idea="My Idea", target_language="Italian")
        self.assertNotIn("Parole che nascono dall'idea", parsed["lyrics"])
        self.assertNotIn("Incredibile Bellezza", parsed["lyrics"])
        self.assertNotIn("Dissolvenza finale...", parsed["lyrics"])

    def test_detect_existing_lyrics(self):
        user_lyrics = """
[Verse 1]
Line one of my song
Line two of my song

[Chorus]
This is my chorus hook
"""
        self.assertTrue(detect_existing_lyrics(user_lyrics))
        self.assertFalse(detect_existing_lyrics("A song about a fast car"))

    def test_clean_repetition_artifacts(self):
        glitch_text = "Il soleeeeeeeeeee splende e il ritmoritmoritmoritmo continua."
        cleaned = clean_repetition_artifacts(glitch_text)
        self.assertNotIn("eeeeeeeeeee", cleaned)
        self.assertNotIn("ritmoritmoritmoritmo", cleaned)


if __name__ == "__main__":
    unittest.main()
