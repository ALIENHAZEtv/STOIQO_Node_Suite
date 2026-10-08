"""
[STOIQO] Music Prompt & Lyrics Engine — Preset Standards
Defines industry-standard genres, vocal timbres, lyrical structures, and BPM ranges.
"""

GENRE_PRESETS = [
    "Auto / From Idea (Infers from prompt)",
    "Pop (Contemporary, Synthpop, Indie Pop)",
    "Rock (Classic Rock, Alternative, Indie Rock, Hard Rock)",
    "Metal (Heavy Metal, Symphonic Metal, Modern Metalcore)",
    "Hip-Hop & Trap (Boom Bap, Modern Trap, Melodic Rap)",
    "Electronic & EDM (Synthwave, House, Melodic Techno, Drum & Bass)",
    "Acoustic & Folk (Indie Folk, Country, Bluegrass, Singer-Songwriter)",
    "Cinematic & Epic (Orchestral, Hybrid Trailer, Ethereal Soundtrack)",
    "R&B & Soul (Neo-Soul, Motown, Contemporary R&B)",
    "Jazz & Blues (Smooth Jazz, Bebop, Delta Blues, Lounge)",
    "Pirate & Sea Shanty (Folk Sea Shanty, Celtic Tavern, Bodhrán)",
    "Lo-Fi & Chill (Lo-Fi Hip Hop, Chillhop, Dream Pop, Ambient)",
    "Funk & Disco (Retro Funk, Nu-Disco, Groove)",
    "Reggae & Dub (Roots Reggae, Modern Dub)",
]

VOCAL_PRESETS = [
    "Auto / Matched to Genre",
    "Warm Expressive Female Vocal",
    "Ethereal Airy Female Vocal",
    "Gritty Powerful Male Vocal",
    "Deep Resonant Male Vocal",
    "Dynamic Vocal Duet (Male & Female)",
    "Harmonized Choir & Gang Vocals",
    "Soulful Belted Vocal",
    "Soft Intimate Whisper Vocal",
    "Instrumental Only (No Vocals)",
]

LANGUAGE_PRESETS = [
    "Italian",
    "English",
    "Spanish",
    "French",
    "Japanese",
    "German",
    "Portuguese",
    "Latin",
    "Auto (Detect from Idea)",
]

SONG_STRUCTURES = [
    "Standard Pop/Rock (Verse 1, Chorus, Verse 2, Chorus, Bridge, Chorus, Outro)",
    "Full Extended Anthem (Intro, Verse 1, Pre-Chorus, Chorus, Verse 2, Chorus, Bridge, Chorus, Outro)",
    "Short & Punchy (Verse 1, Chorus, Verse 2, Chorus, Outro)",
    "Sea Shanty / Folk Strophic (Verse 1, Chorus, Verse 2, Chorus, Verse 3, Chorus, Outro)",
    "Storytelling Ballad (Verse 1, Verse 2, Chorus, Verse 3, Bridge, Outro)",
    "Instrumental Structure (Intro, Theme A, Theme B, Solo, Climax, Outro)",
]

TEMPO_PRESETS = [
    "Auto (Optimal for Genre)",
    "Slow Ballad (65-78 BPM)",
    "Mid-Tempo Groove (85-105 BPM)",
    "Upbeat Driving (115-128 BPM)",
    "High Energy Fast (132-150 BPM)",
    "Very Fast Rush (155-175 BPM)",
]
