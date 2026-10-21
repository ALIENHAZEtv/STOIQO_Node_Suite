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

from core.music import (
    parse_music_response,
    clean_repetition_artifacts,
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

    def test_lyrics_with_trailing_style_and_full_outro(self):
        sample = """
[TITLE]
Respiro di Ferro

[LYRICS]
[Verse 1]
Nelle strade bagnate di pioggia
il metallo risuona feroce.

[Chorus]
Brucia la notte!

[Outro]
Il silenzio cala sulla città.

[STYLE]
Industrial Metal, 130 BPM, heavy guitars, aggressive vocals.
"""
        parsed = parse_music_response(sample, fallback_idea="metal", target_language="Italian")
        self.assertEqual(parsed["title"], "Respiro di Ferro")
        self.assertIn("[Verse 1]", parsed["lyrics"])
        self.assertIn("[Chorus]", parsed["lyrics"])
        self.assertIn("[Outro]", parsed["lyrics"])
        self.assertIn("Il silenzio cala sulla città", parsed["lyrics"])
        self.assertNotIn("Industrial Metal", parsed["lyrics"])
        self.assertIn("Industrial Metal", parsed["style"])


    def test_custom_lyrics_verbatim_passthrough(self):
        user_lyrics = """[Verse 1]
Le mie parole scritte da me
Senza modifiche del modello
[Chorus]
Questo ritornello resta puro
Nessun filtro me lo toglie"""
        raw_llm = """[TITLE]
Canzone Mia

[STYLE]
Italian, warm male vocal, Acoustic Pop, 110 BPM, acoustic guitar, soft percussion

[LYRICS]
[Verse 1]
Testo allucinato dall'AI che non deve essere usato
"""
        parsed = parse_music_response(
            raw_llm,
            fallback_idea="pop song",
            target_language="Italian",
            custom_lyrics=user_lyrics,
        )
        # Verify user lyrics are preserved 100% verbatim
        self.assertEqual(parsed["lyrics"], user_lyrics.strip())
        self.assertEqual(parsed["title"], "Canzone Mia")
        self.assertIn("Acoustic Pop", parsed["style"])

    def test_cjk_glyph_elimination_for_european_lyrics(self):
        raw_llm_with_cjk = """[TITLE]
Notte di Luna 月亮

[STYLE]
Italian, powerful female vocal, Synthwave, 120 BPM, analog synths 音乐

[LYRICS]
[Verse 1]
Sotto le luci al neon della città 城市
guardo le ombre correre via 你好
[Chorus]
Brucia la fiamma dentro il mio cuore 火
non ci fermiamo più nel buio
"""
        parsed = parse_music_response(
            raw_llm_with_cjk,
            fallback_idea="synthwave",
            target_language="Italian",
        )
        # Verify no CJK glyphs survive in title, style, or lyrics
        self.assertNotIn("月亮", parsed["title"])
        self.assertNotIn("音乐", parsed["style"])
        self.assertNotIn("城市", parsed["lyrics"])
        self.assertNotIn("你好", parsed["lyrics"])
        self.assertNotIn("火", parsed["lyrics"])
        self.assertIn("Notte di Luna", parsed["title"])
        self.assertIn("Sotto le luci al neon", parsed["lyrics"])

    def test_reject_corrupted_deserialization_tokens(self):
        raw_llm = """[TITLE]
Death Metal Love

[STYLE]
Death metal, 110 BPM, growl vocals, heavy guitars

[LYRICS]
[Verse 1]
Nelle ombre del silenzio profondo
Brucia il sangue che non si arrende
[Chorus]
L'amore e la morte si fondono insieme
Oltre il buio di questa terra
"""
        parsed_rand = parse_music_response(
            raw_llm,
            fallback_idea="death metal",
            target_language="Italian",
            custom_lyrics="randomize",
        )
        self.assertNotIn("randomize", parsed_rand["lyrics"])
        self.assertIn("Nelle ombre del silenzio", parsed_rand["lyrics"])

        parsed_float = parse_music_response(
            raw_llm,
            fallback_idea="death metal",
            target_language="Italian",
            custom_lyrics="0.7",
        )
        self.assertNotIn("0.7", parsed_float["lyrics"])
        self.assertIn("Nelle ombre del silenzio", parsed_float["lyrics"])

    def test_strip_aborted_metadata_and_cjk_punctuation(self):
        sample = """### [TITLE]
"Black Rose: The Slayers' Veil"

### [MODE]
full

### [DURATION]
210.0

### [ABC_PLANNINGING

 ，。
"""
        parsed = parse_music_response(
            sample,
            fallback_idea="dark fantasy gothic metal song",
            target_language="English",
            genre="Metal",
        )
        self.assertEqual(parsed["title"], "Black Rose: The Slayers' Veil")
        self.assertNotIn("ABC_PLANNING", parsed["lyrics"])
        self.assertNotIn("### [TITLE]", parsed["lyrics"])
        self.assertNotIn("### [MODE]", parsed["lyrics"])
        self.assertNotIn("### [DURATION]", parsed["lyrics"])
        self.assertNotIn("，", parsed["lyrics"])
        self.assertNotIn("。", parsed["lyrics"])
        # Must have valid structured lyrics generated
        self.assertIn("[Verse 1]", parsed["lyrics"])
        self.assertIn("[Chorus]", parsed["lyrics"])
        self.assertEqual(parsed["mode"], "full")
        self.assertEqual(parsed["max_duration"], 210.0)

    def test_reject_numeric_hallucinations_and_provide_singable_lyrics(self):
        sample = """
[STYLE]
Aggressive Death Metal, 110 BPM, Clean vocals, drop-d tuned guitars, heavy drop-bD bass, distorted guitars.

[LYRICS]
[Verse 11]
Cables wrapped in chains,  strings 45 and 15,  no escape,  the grip is tight.  The 5  the 6  
[Chorus]
Slipknotsions 120,  slipknotsions  80,  slipknot  300,  slipknot  150.  The  4  5  6  7  The  8  9  The 1
[Verse 2]
Ink  35,  45,  the  5  the  6
[Chorus]
Slipknotons  200,  slipknotons  110,  slipknot  400,  slipknot  250.  The  4  5  6  7  The  8  9  The  1
[Bridge]
Nin  4  the  5  the  6
[Outro]
In slipknotsions  40,  slipknotons  25,  slipknot  150,  slipknot  125.  The  4  5  The  6  The  7  The  8  The  9
"""
        parsed = parse_music_response(
            sample,
            fallback_idea="A death metal song about how much is beautiful love in slipknots style",
            target_language="English",
            genre="Metal",
        )
        self.assertNotIn("Slipknotsions", parsed["lyrics"])
        self.assertNotIn("strings 45 and 15", parsed["lyrics"])
        self.assertNotIn("The 4 5 6 7", parsed["lyrics"])
        self.assertIn("[Verse 1]", parsed["lyrics"])
        self.assertIn("[Chorus]", parsed["lyrics"])
        self.assertIn("[Outro]", parsed["lyrics"])
        lines = [ln for ln in parsed["lyrics"].splitlines() if ln and not ln.startswith("[")]
        self.assertTrue(len(lines) >= 8)

    def test_parse_granular_music_parameters(self):
        sample = """
[TITLE]
Neon Shadows

[BPM]
128

[KEY]
F# Minor

[TIME_SIGNATURE]
4/4

[GENRE_TAGS]
Cyberpunk, Darkwave, Industrial Synth

[VOCAL_DESCRIPTION]
Detached robotic vocoder with emotional layered harmonies

[DURATION]
195.0

[MODE]
full

[STYLE]
English, detached robotic vocoder with emotional layered harmonies, cyberpunk darkwave industrial synth, 128 BPM, F# Minor, 4/4 meter, arpeggiated analog bass, gated reverb drums, wide stereo pads

[LYRICS]
[Verse 1]
Walking through the neon rain alone tonight,
Reflections in the puddles losing all their light.
A circuit whispers secrets that I cannot keep,
The digital horizon never goes to sleep.

[Chorus]
We are the shadows in the cyber glow,
Running from the memories we used to know!
Caught in the wires where the pulses beat,
Dancing on the edge of every broken street!
"""
        parsed = parse_music_response(
            sample,
            fallback_idea="cyberpunk darkwave",
            target_language="English",
        )
        self.assertEqual(parsed["title"], "Neon Shadows")
        self.assertEqual(parsed["bpm"], 128)
        self.assertEqual(parsed["musical_key"], "F# Minor")
        self.assertEqual(parsed["time_signature"], "4/4")
        self.assertEqual(parsed["duration"] if "duration" in parsed else parsed["max_duration"], 195.0)
        self.assertEqual(parsed["mode"], "full")
        self.assertIn("Cyberpunk", parsed["genre_tags"])
        self.assertIn("vocoder", parsed["vocal_description"])
        self.assertIn("[Verse 1]", parsed["lyrics"])
        self.assertIn("[Chorus]", parsed["lyrics"])
        self.assertNotIn("128", parsed["lyrics"])
        self.assertNotIn("F# Minor", parsed["lyrics"])

    def test_dynamic_duration_expansion_for_full_song(self):
        # A full multi-section song with 24 lines that would clip if limited to 180s
        sample = """
[TITLE]
Epic Anthem of the Stars

[BPM]
100

[DURATION]
120.0

[STYLE]
Cinematic Rock, 100 BPM

[LYRICS]
[Intro]
(Instrumental build)

[Verse 1]
Through the cosmic dust we rise above the falling sun,
Looking for the promised light before the day is done.
Silent echoes in the dark are calling out my name,
Every heartbeat in the void is burning like a flame.

[Pre-Chorus]
Can you hear the thunder rolling through the midnight sky?
We were never born to crawl, we only learned to fly!

[Chorus]
Ignite the stars and let the shadows fall,
Together we will answer to the thunder call!
No fear inside this sanctuary of the brave,
We are the dreamers that the galaxies will save!

[Verse 2]
Drifting on the solar winds across the edge of time,
Every scar upon the soul becomes a sacred rhyme.
Footsteps on the meteor that crumble into space,
Nothing can erase the golden memories of your face.

[Pre-Chorus]
Can you hear the thunder rolling through the midnight sky?
We were never born to crawl, we only learned to fly!

[Chorus]
Ignite the stars and let the shadows fall,
Together we will answer to the thunder call!
No fear inside this sanctuary of the brave,
We are the dreamers that the galaxies will save!

[Bridge]
Break the gravity, shatter the glass,
Watch all the sorrow and misery pass!
Look to the heavens and open your eyes,
This is the moment the universe cries!

[Chorus]
Ignite the stars and let the shadows fall,
Together we will answer to the thunder call!
No fear inside this sanctuary of the brave,
We are the dreamers that the galaxies will save!

[Outro]
Fading into the cosmic glow.
Forever free.
We let it go.
"""
        parsed = parse_music_response(sample, fallback_idea="rock", target_language="English")
        # Ensure duration was expanded past the requested 120.0s to avoid YuE2 hard clipping
        self.assertGreater(parsed["max_duration"], 200.0)
        self.assertEqual(parsed["bpm"], 100)


if __name__ == "__main__":
    unittest.main()




