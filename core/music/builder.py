"""
[STOIQO] Music Prompt & Lyrics Engine — Task Builder & Directives
Builds rich, multimodal composition directives with strict rhyming schemes,
meter cadence, and optional visual cover art grounding.
"""

import re


def clean_user_custom_lyrics(text):
    """
    Validates user-provided custom lyrics, rejecting deserialized LiteGraph UI tokens
    such as 'randomize', 'fixed', 'increment', or stray numbers from corrupted workflow states.
    """
    if not text:
        return ""
    t = text.strip()
    if t.lower() in ["randomize", "fixed", "increment", "decrement", "none", "null", "undefined"]:
        return ""
    try:
        float(t)
        return ""
    except ValueError:
        pass
    return t


def clean_user_custom_directives(text):
    """
    Validates user custom directives, rejecting stray numbers or LiteGraph UI control tokens.
    """
    if not text:
        return ""
    t = text.strip()
    if t.lower() in ["randomize", "fixed", "increment", "decrement", "none", "null", "undefined"]:
        return ""
    try:
        float(t)
        return ""
    except ValueError:
        pass
    return t


def detect_existing_lyrics(text):
    """Checks if the user input contains pre-written lyrics or poetry."""
    if not text:
        return False
    t = text.strip()
    if t.lower() in ["randomize", "fixed", "increment", "decrement"]:
        return False
    if any(marker in t.lower() for marker in ["[verse", "[chorus", "[bridge", "[intro", "[outro", "[hook", "[strofa", "[ritornello"]):
        return True
    lines = [line.strip() for line in t.splitlines() if line.strip()]
    if len(lines) >= 4 and not any(t.lower().startswith(prefix) for prefix in [
        "a song about", "un brano", "canzone che parla", "an upbeat", "create a", "scrivi una"
    ]):
        return True
    return False


def build_music_task_prompt(
    idea,
    genre,
    vocal,
    language,
    structure,
    tempo,
    custom_directives="",
    has_image=False,
    custom_lyrics="",
):
    """Constructs the targeted user task prompt with platinum songwriting standards, strict rhyming schemes, and optional custom lyrics."""
    clean_idea = (idea or "").strip()
    clean_custom_lyrics = clean_user_custom_lyrics(custom_lyrics)
    clean_custom_directives = clean_user_custom_directives(custom_directives)
    is_existing_lyrics = bool(clean_custom_lyrics) or detect_existing_lyrics(clean_idea) or detect_existing_lyrics(clean_custom_directives)
    effective_lyrics = clean_custom_lyrics if clean_custom_lyrics else (clean_idea if detect_existing_lyrics(clean_idea) else clean_custom_directives)

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
            "Inside [LYRICS], output musical arrangement cues (e.g. [Intro], [Theme A], [Climax], [Outro]).\n"
            "Inside [STYLE], write: 'Instrumental, no vocals...' and detail the lead instruments, rhythm section, and mix."
        )
    elif is_existing_lyrics:
        parts.append(
            "# PRIMARY DIRECTIVE: USER-SUPPLIED LYRICS (PRESERVE 100% UNTOUCHED)\n"
            "The user supplied their own complete lyrics for the song.\n"
            "Inside [LYRICS], output the user's lyrics structured with standard section tags ([Verse 1], [Chorus], etc.).\n"
            "You MUST preserve all words and verses provided by the user verbatim. Do not invent replacement lyrics.\n"
            f"USER SUPPLIED TEXT / LYRICS:\n\"\"\"\n{effective_lyrics}\n\"\"\""
        )
    elif is_italian:
        parts.append(
            f"# DIRETTIVA PRINCIPALE: COMPOSIZIONE ORIGINALE IN LINGUA ITALIANA\n"
            f"Componi una canzone originale e memorabile basata su questo concetto:\n"
            f">>> \"{clean_idea}\" <<<\n\n"
            f"- Lingua del Testo: 100% ITALIANO (in [LYRICS] ogni verso deve essere in italiano poetico e grammaticale. ZERO caratteri cinesi o asiatici).\n"
            f"- Metrica & Rime: Struttura rigorosa in rima baciata (AABB) o alternata (ABAB). Versi cantabili di 7-11 sillabe a ritmo regolare.\n"
            f"- Strofe Chiare: Esattamente 4 versi regolari per ogni [Verse], 4 versi ritmici ed epici per il [Chorus], 4 versi per il [Bridge], 2-4 versi per [Outro].\n"
            f"- Stile sonoro: In [STYLE], scrivi la descrizione tecnica (lingua, voce, genere, BPM, strumenti, acustica) in INGLESE per YuE2.\n"
            f"- Struttura richiesta: {' -> '.join(struct_sections) if struct_sections else '[Verse 1] -> [Chorus] -> [Verse 2] -> [Chorus] -> [Bridge] -> [Outro]'}.\n"
            f"- COMPLETEZZA: Concludi tutte le sezioni fino all'ultima riga di [Outro]."
        )
    else:
        parts.append(
            f"# PRIMARY DIRECTIVE: ORIGINAL COMPOSITION IN {target_lang.upper()}\n"
            f"Compose an original chart-caliber song based on this concept:\n"
            f">>> \"{clean_idea}\" <<<\n\n"
            f"- Lyrics Language: 100% {target_lang} (In [LYRICS] every line must be in fluent, metric {target_lang}. Zero Chinese or foreign characters).\n"
            f"- Meter & Rhyme Scheme: Consistent cadence with clear end rhymes (AABB or ABAB). Exactly 4 singable lines per [Verse], 4 anthemic lines per [Chorus], 4 lines per [Bridge], 2-4 lines for [Outro].\n"
            f"- Style Descriptor: In [STYLE], write a dense acoustic prompt (language, vocal, genre, BPM, instruments, mix profile) in English for YuE2/Suno.\n"
            f"- Structure: {' -> '.join(struct_sections) if struct_sections else '[Verse 1] -> [Chorus] -> [Verse 2] -> [Chorus] -> [Bridge] -> [Outro]'}.\n"
            f"- TOTAL COMPLETION: Finish the full song all the way to the final [Outro]."
        )

    # 4. Specifications
    spec_lines = [
        f"- Target Lyrics Language: {target_lang}",
    ]
    if genre and not genre.startswith("Auto"):
        spec_lines.append(f"- Genre Target: {genre}")
    else:
        spec_lines.append("- Genre Target: Determine optimal genre and hybrid acoustic aesthetics freely from the user's vision.")

    if is_instrumental:
        spec_lines.append("- Vocal Target: Instrumental Only (No sung vocals)")
    elif vocal and not vocal.startswith("Auto"):
        spec_lines.append(f"- Vocal Target: {vocal}")
    else:
        spec_lines.append("- Vocal Target: Determine optimal vocal delivery, gender, and timbre matching the song's emotion.")

    if structure and not structure.startswith("Auto"):
        spec_lines.append(f"- Structure Target: {structure}")
    else:
        spec_lines.append("- Structure Target: Choose optimal musical structure dynamically (e.g. [Verse 1] -> [Chorus] -> [Verse 2] -> [Chorus] -> [Bridge] -> [Chorus] -> [Outro]).")

    if tempo and not tempo.startswith("Auto"):
        spec_lines.append(f"- Tempo Target: {tempo}")
    else:
        spec_lines.append("- Tempo Target: Determine precise BPM and rhythmic groove optimal for the genre.")

    if custom_directives and custom_directives.strip():
        parts.append(
            f"⚠️ STRICT USER DIRECTIVES:\n{custom_directives.strip()}"
        )

    parts.append("Production Specifications:\n" + "\n".join(spec_lines))

    # 5. Output Format Contract
    parts.append(
        "CRITICAL SONGWRITING INVARIANT:\n"
        "- Under [LYRICS], write EXCLUSIVELY genuine, emotional, human-singable vocal lyrics in rhyming poetic stanzas.\n"
        "- ABSOLUTELY FORBIDDEN IN [LYRICS]: NEVER output numbers, string gauge sizes, fret markers, or stage directions like '(guitar solo)' inside [LYRICS].\n"
        "- Every single line in [LYRICS] must be a complete, grammatical poetic sentence ready to be sung into a microphone.\n\n"
        "Output Format Requirements (Strictly follow this structure):\n"
        "[TITLE]\nOriginal Song Title\n\n"
        "[BPM]\n120 (Exact numeric BPM)\n\n"
        "[KEY]\nC Minor (Musical key & scale)\n\n"
        "[TIME_SIGNATURE]\n4/4 (Rhythmic meter, e.g. 4/4, 3/4, 6/8)\n\n"
        "[GENRE_TAGS]\nExact comma-separated genre & subgenre tags\n\n"
        "[VOCAL_DESCRIPTION]\nDetailed vocal delivery and timbre description\n\n"
        "[DURATION]\n220.0 (Calculated song length in seconds matching verse pacing, e.g. 200.0 to 270.0 for full song with Outro)\n\n"
        "[MODE]\nfull (YuE2 planning mode: 'full' or 'melody')\n\n"
        "[STYLE]\nDense technical acoustic descriptors (Language, vocal delivery, exact genres, BPM, instruments, mix profile - in English for YuE2/Suno)\n\n"
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
        "[Chorus]\n"
        "...\n\n"
        "[Outro]\n"
        "..."
    )

    return "\n\n".join(parts)
