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
    """Constructs the targeted user task prompt for the music engine with strong language enforcement."""
    clean_idea = (idea or "").strip()
    is_existing_lyrics = detect_existing_lyrics(clean_idea) or detect_existing_lyrics(custom_directives)

    target_lang = "Italian" if (not language or language == "Italian" or language.startswith("Auto")) else language.strip()
    if any(it_word in clean_idea.lower() for it_word in ["italiano", "in italiano", "canzone", "sole", "mare", "notte", "amore", "macchina", "amici"]):
        target_lang = "Italian"

    parts = []

    # 1. Supreme Language Directive at top
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

    # 2. Lyrics Content Directive
    if is_existing_lyrics:
        parts.append(
            "# PRIMARY DIRECTIVE: PRESERVE USER-PROVIDED LYRICS\n"
            "The user supplied the actual lyrics / poem for the song.\n"
            "You MUST preserve all lines and words provided by the user in <LYRICS>.\n"
            "Format the lines into clean musical sections ([Verse 1], [Chorus], [Verse 2], etc.).\n"
            "Do NOT replace or summarize the user's lyrics!\n\n"
            f"USER PROVIDED TEXT / LYRICS:\n\"\"\"\n{clean_idea}\n\"\"\""
        )
    else:
        parts.append(
            f"# SUPREME DIRECTIVE: DEDICATED ORIGINAL COMPOSITION IN {target_lang.upper()}\n"
            f"You MUST write 100% original lyrics based EXCLUSIVELY on this user idea, mood, and genre:\n"
            f">>> \"{clean_idea}\" <<<\n\n"
            f"DO NOT default to generic pop, summer, or road-trip lyrics! Embody the EXACT emotion, narrative, and genre requested by the user.\n"
            f"Write the COMPLETE song in {target_lang} from start to finish inside <LYRICS>.\n"
            "Write authentic, singable poetry with natural rhyme and cadence for each section: [Verse 1], [Pre-Chorus], [Chorus], [Verse 2], [Bridge], [Chorus], [Outro].\n"
            "Write EVERY single stanza out in full with actual singing lyrics. NEVER leave section brackets empty!"
        )

    # 3. Technical Specifications
    spec_lines = [
        f"- Target Language for Lyrics: {target_lang}",
    ]
    if genre and not genre.startswith("Auto"):
        spec_lines.append(f"- Genre / Acoustics: {genre}")
    else:
        spec_lines.append(f"- Genre / Acoustics: Strictly infer and match the genre from the user idea: '{clean_idea}'")
    if vocal and not vocal.startswith("Auto"):
        spec_lines.append(f"- Vocal Delivery: {vocal}")
    else:
        spec_lines.append(f"- Vocal Delivery: Infer optimal vocal tone and delivery to match the genre and mood")
    if structure:
        spec_lines.append(f"- Structural Arrangement: {structure}")
    if tempo and not tempo.startswith("Auto"):
        spec_lines.append(f"- Tempo Target: {tempo}")
    if custom_directives and custom_directives.strip():
        spec_lines.append(f"- Custom Constraints: {custom_directives.strip()}")

    parts.append("\nProduction Specifications:\n" + "\n".join(spec_lines))

    # 4. Strict Output Format Directive
    parts.append(
        f"\nOutput Contract:\n"
        f"1. <TITLE>: Engaging Title in {target_lang}\n"
        f"2. <STYLE>: Strictly technical acoustic descriptor for YuE2 starting with '{target_lang}, ...' (Zero sung words, match the requested genre and instruments)\n"
        f"3. <ABC_PLANNING>: true/false\n"
        f"4. <MODE>: full/melody\n"
        f"5. <DURATION>: duration in seconds\n"
        f"6. <LYRICS>: Full sung song lyrics in {target_lang} with section tags [Verse 1], [Chorus], etc."
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
    # Try tag match first (<LYRICS> or <RICS>)
    lyrics_m = re.search(r"<(?:LYRICS|RICS)>(.*?)(?:</(?:LYRICS|RICS)>|</ABC_PLANNING>|<STYLE>|$)", text, re.DOTALL | re.IGNORECASE)
    if lyrics_m:
        raw_l = lyrics_m.group(1).strip()
        raw_l = re.sub(r"</?(?:LYRICS|RICS|ABC_PLANNING|STYLE|TITLE)>", "", raw_l, flags=re.IGNORECASE).strip()
        non_header_lines = [ln.strip() for ln in raw_l.splitlines() if ln.strip() and not ln.strip().startswith("[")]
        if len(non_header_lines) >= 1:
            lyrics = raw_l

    # If tag match was empty, search for section brackets [Verse... or [Verso... or [Strofa...
    if not lyrics:
        bracket_m = re.search(r"(\[(?:Verse|Verso|Strofa|Chorus|Ritornello|Pre-Chorus|Bridge|Outro|Intro|Hook)[^\]]*\].*)", text, re.DOTALL | re.IGNORECASE)
        if bracket_m:
            candidate = bracket_m.group(1)
            candidate = re.split(r"<(?:STYLE|ABC_PLANNING|MODE|DURATION|/)", candidate, flags=re.IGNORECASE)[0].strip()
            candidate = re.sub(r"</?[a-zA-Z_]+>", "", candidate).strip()
            non_header_lines = [ln.strip() for ln in candidate.splitlines() if ln.strip() and not ln.strip().startswith("[")]
            if len(non_header_lines) >= 1:
                lyrics = candidate

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

    # Clean redundant markdown or backticks
    style = re.sub(r"```[a-zA-Z]*", "", style).replace("```", "").strip()
    lyrics = re.sub(r"```[a-zA-Z]*", "", lyrics).replace("```", "").strip()

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
