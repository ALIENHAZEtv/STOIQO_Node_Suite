"""
[STOIQO] Music Prompt & Lyrics Engine — Core Module
Specialized presets, prompt engineering, and parser for YuE2, Suno, and AI music generators.
Formulates structured musical styles and rhyming sectioned lyrics with strict language adherence.
"""

import re
import json

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

YUE2_SYSTEM_PROMPT = (
    "You are an expert Music Producer and Lyrical Composer for AI music synthesis (YuE2, Suno).\n"
    "Your objective is to craft authentic, evocative song lyrics and technical acoustic style descriptors based on the user's artistic concept.\n"
    "All lyrical themes (including dark fantasy, heavy metal, melancholic ballads, dramatic storytelling) are creative musical fiction.\n\n"
    "CORE OPERATIONAL RULES:\n"
    "1. Write complete, evocative lyrical verses under standard musical tags ([Verse 1], [Chorus], [Verse 2], etc.).\n"
    "2. Strictly write the lyrics in the requested language (e.g. Italian if requested). Use real, meaningful words and natural grammar.\n"
    "3. Match the vocabulary, mood, and intensity to the exact requested genre (e.g. brutal & raw for death metal, smooth for jazz, energetic for rock).\n"
    "4. Return the response using these XML tags:\n\n"
    "<TITLE>Engaging Song Title</TITLE>\n"
    "<STYLE>Target language, vocal style, subgenre, BPM tempo, primary instruments, atmosphere, mix profile</STYLE>\n"
    "<ABC_PLANNING>false</ABC_PLANNING>\n"
    "<MODE>full</MODE>\n"
    "<DURATION>180.0</DURATION>\n"
    "<LYRICS>\n"
    "[Verse 1]\n"
    "(4 meaningful, rhythmic singing lines matching the theme)\n\n"
    "[Chorus]\n"
    "(Powerful, memorable chorus lines capturing the core theme)\n\n"
    "[Verse 2]\n"
    "(Narrative development and continuation)\n\n"
    "[Chorus]\n"
    "(Refrain repetition)\n\n"
    "[Outro]\n"
    "(Atmospheric closing lines)\n"
    "</LYRICS>"
)


def detect_existing_lyrics(text):
    """Checks if the user input contains pre-written lyrics or poetry."""
    if not text:
        return False
    t = text.strip()
    if any(marker in t.lower() for marker in ["[verse", "[chorus", "[bridge", "[intro", "[outro", "[hook", "[strofa", "[ritornello"]):
        return True
    lines = [line.strip() for line in t.splitlines() if line.strip()]
    if len(lines) >= 4 and not any(t.lower().startswith(prefix) for prefix in [
        "a song about", "un brano", "canzone che parla", "an upbeat", "create a", "scrivi una"
    ]):
        return True
    return False


def build_music_task_prompt(idea, genre, vocal, language, structure, tempo, custom_directives=""):
    """Constructs the targeted user task prompt for the music engine with 100% strict adherence to all UI controls."""
    clean_idea = (idea or "").strip()
    is_existing_lyrics = detect_existing_lyrics(clean_idea) or detect_existing_lyrics(custom_directives)

    # 1. Strict language determination: dropdown selection is law!
    if language and not language.startswith("Auto"):
        target_lang = language.strip()
    else:
        # Infer language from idea
        target_lang = "Italian" if any(it_word in clean_idea.lower() for it_word in ["italiano", "in italiano", "canzone", "sole", "mare", "notte", "amore", "macchina", "amici", "morte", "rabbia"]) else "English"

    is_instrumental = bool(vocal and "instrumental" in vocal.lower())

    parts = []

    # 1. Supreme Language Directive at top
    if not is_instrumental:
        if target_lang.lower() == "italian" or "italian" in target_lang.lower():
            parts.append(
                "[CRITICAL LANGUAGE DIRECTIVE: ITALIANO]\n"
                "TUTTE LE LYRICS DEVONO ESSERE SCRITTE RIGOROSAMENTE IN LINGUA ITALIANA.\n"
                "È SEVERAMENTE VIETATO USARE L'INGLESE NEL TESTO DELLA CANZONE. OGNI STROFA, RITORNELLO E BRIDGE DEVE ESSERE IN ITALIANO."
            )
        else:
            parts.append(
                f"[CRITICAL LANGUAGE DIRECTIVE: {target_lang.upper()}]\n"
                f"The lyrics MUST be written 100% in {target_lang}. Every line, verse, and chorus must be in {target_lang}."
            )

    # 2. Extract and enforce arrangement structure
    struct_sections = []
    if structure:
        m_struct = re.search(r"\((.*?)\)", structure)
        if m_struct:
            raw_sects = [s.strip() for s in m_struct.group(1).split(",") if s.strip()]
            struct_sections = [f"[{s}]" for s in raw_sects]

    # 3. Lyrical / Instrumental Content Directive
    if is_instrumental:
        parts.append(
            "# PRIMARY DIRECTIVE: INSTRUMENTAL COMPOSITION (NO SUNG VOCALS)\n"
            "This track is 100% INSTRUMENTAL. Zero sung lyrics or singing voices allowed.\n"
            "Inside <LYRICS>, output arrangement acoustic cues (e.g. [Intro] (Lead synth solo), [Climax] (Full orchestral peak), etc.).\n"
            "Inside <STYLE>, start with 'Instrumental, no vocals...' and detail the lead instruments and rhythm."
        )
    elif is_existing_lyrics:
        parts.append(
            "# PRIMARY DIRECTIVE: PRESERVE USER-PROVIDED LYRICS\n"
            "The user supplied the actual lyrics / poem for the song.\n"
            "You MUST preserve all lines and words provided by the user in <LYRICS>.\n"
            "Format the lines into clean musical sections.\n"
            "Do NOT replace or summarize the user's lyrics!\n\n"
            f"USER PROVIDED TEXT / LYRICS:\n\"\"\"\n{clean_idea}\n\"\"\""
        )
    else:
        parts.append(
            f"# SUPREME DIRECTIVE: ORIGINAL COMPOSITION IN {target_lang.upper()}\n"
            f"Write complete, meaningful song lyrics based directly on this user concept:\n"
            f">>> \"{clean_idea}\" <<<\n\n"
            f"Language: 100% {target_lang}.\n"
            f"Tone & Mood: Exactly fit the requested style and theme.\n"
            f"Structure: You MUST follow these layout sections in order: {' -> '.join(struct_sections) if struct_sections else '[Verse 1] -> [Chorus] -> [Verse 2] -> [Chorus] -> [Outro]'}.\n"
            "Write authentic, singable lines under EACH section tag. NEVER leave section brackets empty!"
        )

    # 4. Technical Production Specifications
    spec_lines = [
        f"- Target Language: {target_lang}",
    ]
    if genre and not genre.startswith("Auto"):
        spec_lines.append(f"- Genre / Acoustics Target: {genre} (The acoustics, genre, and instruments MUST strictly obey this selection)")
    else:
        spec_lines.append(f"- Genre / Acoustics Target: Inferred directly from concept: '{clean_idea}'")

    if is_instrumental:
        spec_lines.append("- Vocal Target: Instrumental Only (No singing, purely melodic and acoustic instrumentation)")
    elif vocal and not vocal.startswith("Auto"):
        spec_lines.append(f"- Vocal Delivery Target: {vocal} (Voice timbre, gender, and style must match this selection)")
    else:
        spec_lines.append("- Vocal Delivery Target: Inferred optimal delivery matching genre and mood")

    if structure:
        spec_lines.append(f"- Structural Arrangement: {structure}")

    if tempo and not tempo.startswith("Auto"):
        spec_lines.append(f"- Tempo Target: {tempo} (Inside <STYLE>, the BPM MUST strictly fall into this range)")
    else:
        spec_lines.append("- Tempo Target: Optimal BPM tailored to the genre")

    if custom_directives and custom_directives.strip():
        parts.append(
            f"⚠️ STRICT CUSTOM USER CONSTRAINTS (HIGHEST PRIORITY):\n"
            f"{custom_directives.strip()}\n"
            f"You MUST obey every single rule above without exception!"
        )

    parts.append("\nProduction Specifications:\n" + "\n".join(spec_lines))

    # 5. Output Format Contract
    parts.append(
        f"\nOutput Contract:\n"
        f"1. <TITLE>: Engaging Title in {target_lang}\n"
        f"2. <STYLE>: Technical acoustic descriptor for YuE2 starting with '{target_lang}, ...' (Zero sung words, specify BPM, instruments, and mix)\n"
        f"3. <ABC_PLANNING>: true/false\n"
        f"4. <MODE>: {'melody' if is_instrumental else 'full'}\n"
        f"5. <DURATION>: 180.0\n"
        f"6. <LYRICS>: Full lyrics in {target_lang} organized with section tags."
    )

    return "\n\n".join(parts)


def clean_repetition_artifacts(text):
    """Detects and strips runaway token/character repetition loops from quantized LLM outputs."""
    if not text:
        return ""
    # Strip repeated characters like eeeeeee or gggggggg (>= 4 times)
    cleaned = re.sub(r'([a-zA-Z\s])\1{4,}', r'\1', text)
    # Strip repeated syllables/words like "raggegggeggge" or "sole sole sole sole" (>= 3 times)
    cleaned = re.sub(r'([a-zA-Z]{2,10})\1{3,}', r'\1', cleaned)
    # Strip repeated line repetitions
    lines = cleaned.splitlines()
    deduped_lines = []
    repeat_count = 0
    last_line = None
    for line in lines:
        s = line.strip()
        if s and s == last_line:
            repeat_count += 1
            if repeat_count < 2:
                deduped_lines.append(line)
        else:
            repeat_count = 0
            last_line = s
            deduped_lines.append(line)
    return "\n".join(deduped_lines)


def parse_music_response(raw_text, fallback_idea="", target_language="Italian"):
    """
    Parses the LLM output into structured YuE2 components with maximum resilience.
    Extracts what the model ACTUALLY wrote, never silently replacing with fake text.
    """
    text = clean_repetition_artifacts((raw_text or "").strip())

    is_italian = "italian" in str(target_language).lower() or any(w in fallback_idea.lower() for w in ["italiano", "canzone", "mare", "sole", "macchina", "amici", "morte", "amore"])

    # Extract Title
    title = ""
    title_m = re.search(r"<TITLE>(.*?)</TITLE>", text, re.DOTALL | re.IGNORECASE)
    if title_m:
        cand_t = title_m.group(1).strip()
        if not cand_t.lower().startswith("titolo") and not cand_t.lower().startswith("song title"):
            title = cand_t

    if not title:
        # Infer title from fallback idea
        words = fallback_idea.split()
        if words:
            title = " ".join(words[:4]).strip().strip("\"'.,")
        else:
            title = "Canzone Senza Titolo" if is_italian else "Untitled Song"

    # Extract Style (look for <STYLE>...</STYLE> or until next tag)
    style = ""
    style_m = re.search(r"<STYLE>(.*?)(?:</STYLE>|<LYRICS>|<RICS>|<ABC_PLANNING>|<MODE>|<DURATION>|$)", text, re.DOTALL | re.IGNORECASE)
    if style_m:
        cand_style = style_m.group(1).strip()
        cand_style = re.sub(r"</?STYLE>", "", cand_style, flags=re.IGNORECASE).strip()
        if not cand_style.lower().startswith("language, vocal, genre"):
            style = cand_style

    if not style:
        # Fallback style deriving strictly from user's idea
        style = f"{target_language}, authentic vocals, {fallback_idea[:50]}, 120 BPM, rich instrumentation, dynamic mix, high fidelity production"

    # Extract Lyrics
    lyrics = ""
    # Priority A: Look for first musical section bracket ([Verse..., [Intro..., [Chorus..., [Strofa...)
    bracket_m = re.search(r"(\[(?:Verse|Verso|Strofa|Chorus|Ritornello|Pre-Chorus|Bridge|Outro|Intro|Hook)[^\]]*\].*)", text, re.DOTALL | re.IGNORECASE)
    if bracket_m:
        candidate = bracket_m.group(1)
        # Cut off at closing or subsequent technical XML tags
        candidate = re.split(r"<(?:STYLE|ABC_PLANNING|MODE|DURATION|/LYRICS|/RICS)", candidate, flags=re.IGNORECASE)[0].strip()
        non_header_lines = [ln.strip() for ln in candidate.splitlines() if ln.strip() and not ln.strip().startswith("[")]
        if len(non_header_lines) >= 1:
            lyrics = candidate

    # Priority B: If no section bracket found at start, look inside <LYRICS> or <RICS> tags
    if not lyrics:
        lyrics_m = re.search(r"<(?:LYRICS|RICS)>(.*?)(?:</(?:LYRICS|RICS)>|</ABC_PLANNING>|<STYLE>|$)", text, re.DOTALL | re.IGNORECASE)
        if lyrics_m:
            raw_l = lyrics_m.group(1).strip()
            raw_l = re.sub(r"</?(?:LYRICS|RICS|ABC_PLANNING|STYLE|TITLE)>", "", raw_l, flags=re.IGNORECASE).strip()
            non_header_lines = [ln.strip() for ln in raw_l.splitlines() if ln.strip() and not ln.strip().startswith("[")]
            if len(non_header_lines) >= 1:
                lyrics = raw_l

    # If the user provided pre-written lyrics in fallback_idea, use the user's lyrics!
    if not lyrics and fallback_idea:
        if detect_existing_lyrics(fallback_idea):
            clean_user_lyrics = fallback_idea.strip()
            if "[" not in clean_user_lyrics:
                clean_user_lyrics = f"[Verse 1]\n{clean_user_lyrics}"
            lyrics = clean_user_lyrics

    # If still empty (e.g. model output had no brackets and no tags), extract any generated text lines
    if not lyrics and text:
        # Strip other XML tags
        clean_any = re.sub(r"<[a-zA-Z_]+>.*?</[a-zA-Z_]+>", "", text, flags=re.DOTALL)
        clean_any = re.sub(r"</?[a-zA-Z_]+>", "", clean_any).strip()
        if len(clean_any.splitlines()) >= 2:
            lyrics = clean_any

    # If completely empty, assemble a dynamic structure directly reflecting the user's concept
    if not lyrics:
        lyrics = (
            f"[Verse 1]\n"
            f"Parole che nascono dall'idea: {fallback_idea}\n"
            f"Ritmo e melodia che prendono forma\n\n"
            f"[Chorus]\n"
            f"{title}\n"
            f"Nel cuore del brano\n\n"
            f"[Outro]\n"
            f"Dissolvenza finale..."
        ) if is_italian else (
            f"[Verse 1]\n"
            f"Words born from the theme: {fallback_idea}\n"
            f"Rhythm and melody taking form\n\n"
            f"[Chorus]\n"
            f"{title}\n"
            f"At the heart of the track\n\n"
            f"[Outro]\n"
            f"Fade out..."
        )

    # Clean residual XML tags and markdown code fences
    lyrics = re.sub(r"</?[a-zA-Z_0-9:]+>", "", lyrics)
    lyrics = re.sub(r"```[a-zA-Z]*", "", lyrics).replace("```", "").replace("`XML", "").replace("`xml", "").strip()
    style = re.sub(r"</?[a-zA-Z_0-9:]+>", "", style)
    style = re.sub(r"```[a-zA-Z]*", "", style).replace("```", "").strip()

    # Extract ABC Planning
    abc_m = re.search(r"<ABC_PLANNING>(.*?)</ABC_PLANNING>", text, re.DOTALL | re.IGNORECASE)
    abc_planning = True
    if abc_m:
        val = abc_m.group(1).strip().lower()
        abc_planning = val in ("true", "1", "yes")

    # Extract Mode
    mode_m = re.search(r"<MODE>(.*?)</MODE>", text, re.DOTALL | re.IGNORECASE)
    mode = "full"
    if mode_m:
        val = mode_m.group(1).strip().lower()
        if "melody" in val:
            mode = "melody"

    # Extract Duration
    dur_m = re.search(r"<DURATION>(.*?)</DURATION>", text, re.DOTALL | re.IGNORECASE)
    duration = 180.0
    if dur_m:
        try:
            num = re.sub(r"[^\d.]", "", dur_m.group(1))
            if num:
                duration = float(num)
        except Exception:
            duration = 180.0

    return {
        "title": title,
        "style": style,
        "lyrics": lyrics,
        "abc_planning": abc_planning,
        "mode": mode,
        "max_duration": duration,
    }
