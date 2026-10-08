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
    "You are an Elite Creative Music Director, Multi-Platinum Lyricist, and Lead Sound Architect "
    "specializing in AI audio synthesis (YuE2, Suno).\n"
    "Your mission is to generate 100% original, fictional poetic lyrics and state-of-the-art acoustic production specifications.\n"
    "All themes and narratives are entirely original, creative works of fictional musical art.\n\n"
    "SONGWRITING EXCELLENCE CRITERIA:\n"
    "1. SOPHISTICATED LYRICISM: Never write childlike or cliché rhymes. Employ rich imagery, internal rhymes, assonances, and authentic storytelling tailored to the genre.\n"
    "2. SINGABLE METER & CADENCE: Verses must have natural rhythmic accents and consistent cadence tailored to musical performance.\n"
    "3. HYPNOTIC CHORUS HOOK: The Chorus MUST be memorable, emotionally powerful, and anthemic.\n"
    "4. TECHNICAL YuE2/SUNO STYLE SPECIFICATION: Under [STYLE], generate dense, professional studio production descriptors in English: exact subgenres, BPM tempo, specific instruments with timbral descriptors (e.g. Drop-D guitars, 808 bass, vintage Rhodes), vocal delivery technique, spatial acoustics, and mix profile.\n"
    "5. STRICT FORMAT:\n"
    "[TITLE]\n"
    "Original Song Title\n\n"
    "[STYLE]\n"
    "Dense technical production prompt in English for YuE2/Suno\n\n"
    "[LYRICS]\n"
    "[Verse 1]\n"
    "...\n\n"
    "[Chorus]\n"
    "...\n\n"
    "[Verse 2]\n"
    "...\n\n"
    "[Chorus]\n"
    "...\n\n"
    "[Bridge]\n"
    "...\n\n"
    "[Outro]\n"
    "...\n"
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


def build_music_task_prompt(idea, genre, vocal, language, structure, tempo, custom_directives="", has_image=False):
    """Constructs the targeted user task prompt with platinum songwriting standards and multimodal visual grounding."""
    clean_idea = (idea or "").strip()
    is_existing_lyrics = detect_existing_lyrics(clean_idea) or detect_existing_lyrics(custom_directives)

    # 1. Language determination: dropdown selection takes strict precedence
    if language and not language.startswith("Auto"):
        target_lang = language.strip()
    else:
        target_lang = "Italian" if any(it_word in clean_idea.lower() for it_word in ["italiano", "in italiano", "canzone", "sole", "mare", "notte", "amore", "macchina", "amici", "morte", "rabbia", "fuoco"]) else "English"

    is_italian = "italian" in target_lang.lower()
    is_instrumental = bool(vocal and "instrumental" in vocal.lower())

    struct_sections = []
    if structure:
        m_struct = re.search(r"\((.*?)\)", structure)
        if m_struct:
            raw_sects = [s.strip() for s in m_struct.group(1).split(",") if s.strip()]
            struct_sections = [f"[{s}]" for s in raw_sects]

    parts = []

    # 2. Multimodal Visual Grounding (VLM) if image is attached
    if has_image:
        if is_italian:
            parts.append(
                "# ANALISI MULTIMODALE DELL'IMMAGINE DI COPERTINA (VLM):\n"
                "Un'immagine di copertina / concept visivo è stata fornita.\n"
                "Come direttore artistico e audio producer d'élite:\n"
                "1. Analizza la composizione visiva: colori dominanti, contrasti di luce/ombra, texture ed emozione espressa.\n"
                "2. Trasponi l'estetica visiva nel sound design in [STYLE] (es. tinte cupe e fredde -> distorsioni pesanti, riverberi cavernosi; tinte solari e calde -> chitarre acustiche brillanti e groove aperto).\n"
                "3. Integra simboli ed elementi visivi dell'immagine come metafore liriche all'interno delle lyrics in [LYRICS]."
            )
        else:
            parts.append(
                "# MULTIMODAL VISUAL GROUNDING (VLM ARTWORK ANALYSIS):\n"
                "A cover artwork / concept image is provided.\n"
                "As an elite visual and acoustic producer:\n"
                "1. Analyze the visual atmosphere: color temperature, lighting contrast, textures, palette, and emotional tension.\n"
                "2. Translate visual elements into acoustic architecture in [STYLE].\n"
                "3. Embed visual metaphors, symbolic objects, and scenery from the image directly into the lyrics in [LYRICS]."
            )

    # 3. Main Composition Directive
    if is_instrumental:
        parts.append(
            "# PRIMARY DIRECTIVE: INSTRUMENTAL COMPOSITION (NO SUNG VOCALS)\n"
            "This track is 100% INSTRUMENTAL. Zero sung lyrics or singing voices allowed.\n"
            "Inside [LYRICS], output musical arrangement cues (e.g. [Intro] (Lead synth motif), [Theme A], [Climax], [Outro]).\n"
            "Inside [STYLE], write: 'Instrumental, no vocals...' and detail the lead instruments, rhythm section, and mix."
        )
    elif is_existing_lyrics:
        parts.append(
            "# PRIMARY DIRECTIVE: PRESERVE USER-PROVIDED LYRICS\n"
            "The user supplied the actual lyrics / poem for the song.\n"
            "You MUST preserve all lines and words provided by the user in [LYRICS].\n"
            "Format the lines into clean musical sections.\n"
            f"USER PROVIDED TEXT / LYRICS:\n\"\"\"\n{clean_idea}\n\"\"\""
        )
    elif is_italian:
        parts.append(
            f"# DIRETTIVA PRINCIPALE: COMPOSIZIONE ORIGINALE IN LINGUA ITALIANA\n"
            f"Componi una canzone originale e memorabile basata su questo concetto:\n"
            f">>> \"{clean_idea}\" <<<\n\n"
            f"- Lingua del Testo: 100% ITALIANO (in [LYRICS] ogni strofa, ritornello e bridge deve essere in italiano poetico, maturo e impeccabile).\n"
            f"- Stile sonoro: In [STYLE], scrivi la descrizione tecnica in INGLESE per sintetizzatori AI (YuE2, Suno).\n"
            f"- Struttura richiesta: {' -> '.join(struct_sections) if struct_sections else '[Verse 1] -> [Chorus] -> [Verse 2] -> [Chorus] -> [Bridge] -> [Outro]'}.\n"
            f"- Scrivi versi completi, autentici e cantabili sotto ogni sezione. Zero segnaposto o istruzioni tra parentesi."
        )
    else:
        parts.append(
            f"# PRIMARY DIRECTIVE: ORIGINAL COMPOSITION IN {target_lang.upper()}\n"
            f"Compose an original chart-caliber song based on this concept:\n"
            f">>> \"{clean_idea}\" <<<\n\n"
            f"- Lyrics Language: 100% {target_lang} (Every line under [LYRICS] must be written in {target_lang} with top-tier poetic standards).\n"
            f"- Style Descriptor: In [STYLE], write the technical acoustic prompt in English for YuE2/Suno.\n"
            f"- Structure: {' -> '.join(struct_sections) if struct_sections else '[Verse 1] -> [Chorus] -> [Verse 2] -> [Chorus] -> [Bridge] -> [Outro]'}.\n"
            f"- Write complete, metric, authentic lines under each section tag. No placeholders."
        )

    # 4. Specifications
    spec_lines = [
        f"- Target Lyrics Language: {target_lang}",
    ]
    if genre and not genre.startswith("Auto"):
        spec_lines.append(f"- Genre Target: {genre}")
    else:
        spec_lines.append(f"- Genre Target: Inferred directly from concept: '{clean_idea}'")

    if is_instrumental:
        spec_lines.append("- Vocal Target: Instrumental Only (No vocals)")
    elif vocal and not vocal.startswith("Auto"):
        spec_lines.append(f"- Vocal Target: {vocal}")
    else:
        spec_lines.append("- Vocal Target: Inferred optimal delivery matching genre")

    if structure:
        spec_lines.append(f"- Structure: {structure}")

    if tempo and not tempo.startswith("Auto"):
        spec_lines.append(f"- Tempo Target: {tempo}")
    else:
        spec_lines.append("- Tempo Target: Optimal BPM tailored to genre")

    if custom_directives and custom_directives.strip():
        parts.append(
            f"⚠️ STRICT USER DIRECTIVES:\n{custom_directives.strip()}"
        )

    parts.append("Production Specifications:\n" + "\n".join(spec_lines))

    # 5. Output Format Contract
    parts.append(
        "Output Format Requirements:\n"
        "[TITLE]\nSong Title\n\n"
        "[STYLE]\nSubgenre, BPM, vocal delivery, lead instruments, rhythm section, acoustics & mix (in English for YuE2/Suno)\n\n"
        "[LYRICS]\nOrganized strictly by section headers ([Verse 1], [Chorus], etc.) with complete singing lines."
    )

    return "\n\n".join(parts)


def clean_repetition_artifacts(text):
    """Detects and strips runaway token/character repetition loops from quantized LLM outputs."""
    if not text:
        return ""
    # Strip known Qwen tokenizer hallucination glitch
    cleaned = re.sub(r'\baddCriterion\b', '', text, flags=re.IGNORECASE)
    # Strip repeated characters like eeeeeee or gggggggg (>= 4 times)
    cleaned = re.sub(r'([a-zA-Z\s])\1{4,}', r'\1', cleaned)
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


def normalize_lyrics_sections(text):
    """Converts any rogue XML section tags (<Verse 1>, <Chorus>, etc.) into standard bracket sections."""
    if not text:
        return ""
    def repl_tag(m):
        tag_type = m.group(1).capitalize()
        num = m.group(2).strip() if m.group(2) else ""
        if len(num) > 1 and num == num[0] * len(num):
            num = num[0]
        if num:
            return f"\n[{tag_type} {num}]\n"
        return f"\n[{tag_type}]\n"

    # Convert opening XML section tags: <Verse 1>, <Verse>, <Chorus>, <Bridge>, etc.
    res = re.sub(r"<\s*(Verse|Chorus|Bridge|Outro|Intro|Pre-Chorus|Hook|Strofa|Ritornello)\s*([0-9]*)\s*>", repl_tag, text, flags=re.IGNORECASE)
    # Convert markdown section tags: #### Verse 1, ### Chorus, ## Bridge, etc.
    res = re.sub(r"(?:^|\n)\s*#{1,6}\s*(Verse|Chorus|Bridge|Outro|Intro|Pre-Chorus|Hook|Strofa|Ritornello)\s*([0-9]*)", repl_tag, res, flags=re.IGNORECASE)
    # Strip all closing tags like </verse>, </chorus>, </lyrics>, etc.
    res = re.sub(r"<\s*/\s*[a-zA-Z0-9_\s:]+>", "", res)
    return res


def parse_music_response(raw_text, fallback_idea="", target_language="Italian"):
    """
    Parses the LLM output into structured YuE2 components with maximum resilience.
    Supports both bracket sections ([TITLE], [STYLE], [LYRICS]) and XML tags (<TITLE>, <STYLE>, <LYRICS>).
    Never invents fake lyrics or fallback placeholder templates.
    """
    text = clean_repetition_artifacts((raw_text or "").strip())
    normalized_text = normalize_lyrics_sections(text)

    is_italian = "italian" in str(target_language).lower() or any(
        w in fallback_idea.lower() for w in ["italiano", "canzone", "mare", "sole", "macchina", "amici", "morte", "amore", "fuoco"]
    )

    # 1. Extract Title
    title = ""
    # Check XML <TITLE>
    title_m = re.search(r"<TITLE>(.*?)</TITLE>", text, re.DOTALL | re.IGNORECASE)
    if title_m:
        cand_t = title_m.group(1).strip()
        if not cand_t.lower().startswith("titolo") and not cand_t.lower().startswith("song title"):
            title = cand_t

    # Check Bracket [TITLE] or Markdown ### Title
    if not title:
        brack_title = re.search(r"(?:#{1,6}\s*)?\[?TITLE\]?\s*\n+([^\n\[<#]+)", text, re.IGNORECASE)
        if brack_title:
            cand_t = brack_title.group(1).strip().strip("\"'#*")
            if not any(cand_t.lower().startswith(p) for p in ["original song", "titolo della", "song title", "titolo"]):
                title = cand_t

    # Check "Title: ..."
    if not title:
        colon_title = re.search(r"(?:^|\n)Title:\s*([^\n\[<#]+)", text, re.IGNORECASE)
        if colon_title:
            cand_t = colon_title.group(1).strip().strip("\"'#*")
            if not any(cand_t.lower().startswith(p) for p in ["original song", "titolo della", "song title"]):
                title = cand_t

    if not title:
        words = fallback_idea.split()
        if words:
            title = " ".join(words[:4]).strip().strip("\"'.,")
        else:
            title = "Canzone Senza Titolo" if is_italian else "Untitled Song"

    # 2. Extract Style
    style = ""
    # Check XML <STYLE>
    style_m = re.search(r"<STYLE>(.*?)(?:</STYLE>|<LYRICS>|<RICS>|\[LYRICS\]|\[Verse|$)", text, re.DOTALL | re.IGNORECASE)
    if style_m:
        cand_s = style_m.group(1).strip()
        cand_s = re.sub(r"</?STYLE>", "", cand_s, flags=re.IGNORECASE).strip()
        if not cand_s.lower().startswith("dense technical") and not cand_s.lower().startswith("language, vocal"):
            style = cand_s

    # Check Bracket [STYLE] or Markdown ### Style
    if not style:
        brack_style = re.search(r"(?:#{1,6}\s*)?\[?STYLE\]?\s*\n+(.*?)(?=\n+(?:#{1,6}\s*)?\[?LYRICS\]?|\n+(?:#{1,6}\s*)?\[?(?:Verse|Intro|Chorus|Strofa)|<LYRICS>|$)", text, re.DOTALL | re.IGNORECASE)
        if brack_style:
            cand_s = brack_style.group(1).strip()
            # Clean instruction boilerplate if model repeated prompt headers
            lines_s = [ln.strip() for ln in cand_s.splitlines() if ln.strip() and not ln.strip().startswith("(")]
            if lines_s:
                style = " ".join(lines_s)

    # Check "Style: ..."
    if not style:
        colon_style = re.search(r"(?:^|\n)Style:\s*([^\n]+(?:\n[^\n\[<#]+)*)", text, re.IGNORECASE)
        if colon_style:
            style = colon_style.group(1).strip()

    if not style:
        style = f"{target_language}, authentic vocals, {fallback_idea[:60]}, 120 BPM, rich instrumentation, dynamic mix, high fidelity production"

    # 3. Extract Lyrics
    lyrics = ""
    # Priority A: Look inside <LYRICS> or <RICS> in normalized text
    lyrics_m = re.search(r"<(?:LYRICS|RICS)>(.*?)(?:</(?:LYRICS|RICS)>|<ABC_PLANNING>|<STYLE>|$)", normalized_text, re.DOTALL | re.IGNORECASE)
    if lyrics_m:
        cand_l = lyrics_m.group(1).strip()
        cand_l = re.sub(r"</?(?:LYRICS|RICS|ABC_PLANNING|STYLE|TITLE)>", "", cand_l, flags=re.IGNORECASE).strip()
        non_header_lines = [ln.strip() for ln in cand_l.splitlines() if ln.strip() and not ln.strip().startswith("[")]
        if len(non_header_lines) >= 1:
            lyrics = cand_l

    # Priority B: Look inside [LYRICS] block
    if not lyrics:
        brack_lyrics = re.search(r"(?:###\s*)?\[LYRICS\]\s*\n+(.*)", normalized_text, re.DOTALL | re.IGNORECASE)
        if brack_lyrics:
            cand_l = brack_lyrics.group(1).strip()
            cand_l = re.split(r"<(?:STYLE|ABC_PLANNING|MODE|DURATION)", cand_l, flags=re.IGNORECASE)[0].strip()
            non_header_lines = [ln.strip() for ln in cand_l.splitlines() if ln.strip() and not ln.strip().startswith("[")]
            if len(non_header_lines) >= 1:
                lyrics = cand_l

    # Priority C: Look for first musical section bracket ([Verse..., [Intro..., [Chorus..., [Strofa...)
    if not lyrics:
        bracket_m = re.search(r"(\[(?:Verse|Verso|Strofa|Chorus|Ritornello|Pre-Chorus|Bridge|Outro|Intro|Hook)[^\]]*\].*)", normalized_text, re.DOTALL | re.IGNORECASE)
        if bracket_m:
            candidate = bracket_m.group(1)
            candidate = re.split(r"<(?:STYLE|ABC_PLANNING|MODE|DURATION|/LYRICS|/RICS)", candidate, flags=re.IGNORECASE)[0].strip()
            non_header_lines = [ln.strip() for ln in candidate.splitlines() if ln.strip() and not ln.strip().startswith("[")]
            if len(non_header_lines) >= 1:
                lyrics = candidate

    # Priority D: If user provided pre-written lyrics in fallback_idea, preserve them
    if not lyrics and fallback_idea:
        if detect_existing_lyrics(fallback_idea):
            clean_user_lyrics = fallback_idea.strip()
            if "[" not in clean_user_lyrics:
                clean_user_lyrics = f"[Verse 1]\n{clean_user_lyrics}"
            lyrics = clean_user_lyrics

    # Priority E: Extract any raw generated lines if model omitted headers
    if not lyrics and text:
        clean_raw = re.sub(r"<[a-zA-Z_0-9:]+>.*?</[a-zA-Z_0-9:]+>", "", text, flags=re.DOTALL)
        clean_raw = re.sub(r"</?[a-zA-Z_0-9:]+>", "", clean_raw).strip()
        # Filter out Style block if style was found
        if style and style in clean_raw:
            clean_raw = clean_raw.replace(style, "").strip()
        if clean_raw:
            lyrics = clean_raw

    # 4. Clean residual XML tags, markdown fences, and parenthetical instructions like "(4 lines)"
    lyrics = re.sub(r"</?[a-zA-Z_0-9:]+>", "", lyrics)
    lyrics = re.sub(r"```[a-zA-Z]*", "", lyrics).replace("```", "").replace("`XML", "").replace("`xml", "").strip()
    # Strip prompt instruction parentheticals: e.g. "(4 lines)", "(lyrics here)", "(Quattro versi...)", "(lyrics)"
    lyrics = re.sub(r"^\s*\([0-9]+\s*(?:lines|versi|linee|strofe)[^\)]*\)\s*$", "", lyrics, flags=re.MULTILINE | re.IGNORECASE)
    lyrics = re.sub(r"^\s*\((?:lyrics|testo|versi|quattro versi|lyrics here)[^\)]*\)\s*$", "", lyrics, flags=re.MULTILINE | re.IGNORECASE)

    style = re.sub(r"</?[a-zA-Z_0-9:]+>", "", style)
    style = re.sub(r"```[a-zA-Z]*", "", style).replace("```", "").strip()
    style = re.sub(r"^\s*\([^\)]*\)\s*$", "", style, flags=re.MULTILINE)

    # Clean multiple consecutive empty lines
    lyrics = re.sub(r"\n{3,}", "\n\n", lyrics).strip()
    style = re.sub(r"\n{2,}", " ", style).strip()

    # 5. Extract ABC Planning
    abc_m = re.search(r"<ABC_PLANNING>(.*?)</ABC_PLANNING>", text, re.DOTALL | re.IGNORECASE)
    abc_planning = True
    if abc_m:
        val = abc_m.group(1).strip().lower()
        abc_planning = val in ("true", "1", "yes")

    # 6. Extract Mode
    mode_m = re.search(r"<MODE>(.*?)</MODE>", text, re.DOTALL | re.IGNORECASE)
    mode = "full"
    if mode_m:
        val = mode_m.group(1).strip().lower()
        if "melody" in val:
            mode = "melody"

    # 7. Extract Duration
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
