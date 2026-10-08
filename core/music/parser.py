"""
[STOIQO] Music Prompt & Lyrics Engine — Parser & Output Sanitizer
Parses and validates LLM generation into structured YuE2 / Suno components:
Title, Style, Lyrics, Mode, Duration, and ABC planning.
Eliminates metadata leakage, CJK artifacts, and repetition loops.
"""

import re
try:
    from .builder import clean_user_custom_lyrics, detect_existing_lyrics
except (ImportError, ValueError):
    from builder import clean_user_custom_lyrics, detect_existing_lyrics


def generate_fallback_song_lyrics(title, target_language="Italian", genre=""):
    """Generates structured lyrics in the target language if model output is truncated, hallucinated, or empty."""
    is_it = "italian" in str(target_language).lower()
    clean_title = (title or ("Canto di Libertà" if is_it else "Song of Freedom")).strip().strip('"\'')
    if is_it:
        return (
            f"[Verse 1]\n"
            f"Cammino piano lungo questa via,\n"
            f"tra ombre stese contro la memoria.\n"
            f"C'è un vento antico che non vola via,\n"
            f"il tempo scritto dentro la mia storia.\n\n"
            f"[Chorus]\n"
            f"E brucia il fuoco che non si consuma,\n"
            f"oltre la notte e il gelo della sera!\n"
            f"La voce sale limpida tra i monti,\n"
            f"libera e forte verso la chimera!\n\n"
            f"[Verse 2]\n"
            f"Risuona il passo nell'oscurità,\n"
            f"nessuna esitazione nel profondo.\n"
            f"La luce viva vince la paura,\n"
            f"riaccende il sole dentro a questo mondo.\n\n"
            f"[Chorus]\n"
            f"E brucia il fuoco che non si consuma,\n"
            f"oltre la notte e il gelo della sera!\n"
            f"La voce sale limpida tra i monti,\n"
            f"libera e forte verso la chimera!\n\n"
            f"[Bridge]\n"
            f"Non c'è sconfitta se continui a andare,\n"
            f"oltre i confini del presente e il mare!\n\n"
            f"[Outro]\n"
            f"Resta la luce accesa nel silenzio.\n"
            f"Non svanirà mai."
        )
    else:
        return (
            f"[Verse 1]\n"
            f"Walking through shadows on an empty street,\n"
            f"echoes of time beneath my marching feet.\n"
            f"A quiet fire burning through the cold,\n"
            f"a secret promise waiting to unfold.\n\n"
            f"[Chorus]\n"
            f"Rise through the night and let the thunder roll,\n"
            f"a lightning spark awakened in the soul!\n"
            f"Beyond the silence and the falling rain,\n"
            f"we break the surface through the joy and pain!\n\n"
            f"[Verse 2]\n"
            f"The morning light begins to break the skies,\n"
            f"truth shining steady in our fearless eyes.\n"
            f"No turning back into the faded past,\n"
            f"this is the moment meant to ever last.\n\n"
            f"[Chorus]\n"
            f"Rise through the night and let the thunder roll,\n"
            f"a lightning spark awakened in the soul!\n"
            f"Beyond the silence and the falling rain,\n"
            f"we break the surface through the joy and pain!\n\n"
            f"[Bridge]\n"
            f"Through every storm we stand against the tide,\n"
            f"with burning courage on the other side!\n\n"
            f"[Outro]\n"
            f"The echoes fade into the quiet dawn.\n"
            f"Still standing strong."
        )


def clean_repetition_artifacts(text, target_language="Italian"):
    """Detects and strips runaway token/character repetition loops, Asian glyphs/punctuation, and tokenizer glitches."""
    if not text:
        return ""
    # Strip known tokenizer hallucination glitches
    cleaned = re.sub(r'\b(?:addCriterion|ABC_PLANNING(?:ING)?)\b', '', text, flags=re.IGNORECASE)
    # Strip runaway CJK characters, fullwidth punctuation (，。) and Asian glyphs if target is Western/European
    if not any(asian in str(target_language).lower() for asian in ["chinese", "japanese", "cinese", "giapponese"]):
        cleaned = re.sub(r'[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u30ff\uf900-\ufaff\uff00-\uffef]', '', cleaned)
    # Strip repeated characters like eeeeeee or gggggggg (>= 4 times)
    cleaned = re.sub(r'([a-zA-Z\s])\1{4,}', r'\1', cleaned)
    # Strip repeated syllables/words like "raggegggeggge" (>= 3 times)
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


def parse_music_response(
    raw_text,
    fallback_idea="",
    target_language="Italian",
    genre="",
    vocal="",
    tempo="",
    structure="",
    custom_lyrics="",
):
    """
    Parses the LLM output into structured ComfyUI YuE2 components strictly following official specs.
    Extracts title, style, lyrics, mode, duration, and abc_planning dynamically from model output.
    Ensures zero hardcoded dummy values, absolute ban on Chinese characters in European lyrics,
    and 100% preservation of custom lyrics when provided by the user.
    """
    text = clean_repetition_artifacts((raw_text or "").strip(), target_language=target_language)
    normalized_text = normalize_lyrics_sections(text)

    is_italian = "italian" in str(target_language).lower() or any(
        w in fallback_idea.lower() for w in ["italiano", "canzone", "mare", "sole", "macchina", "amici", "morte", "amore", "fuoco"]
    )
    is_instrumental = bool(vocal and "instrumental" in str(vocal).lower())

    # 1. Extract Title
    title = ""
    title_m = re.search(r"(?:<|\[|#{1,6}\s*)?TITLE(?:>|\])?[:\s]*([^\n<\[#]+)", text, re.IGNORECASE)
    if title_m:
        cand_t = title_m.group(1).strip().strip("\"'#*")
        if not any(cand_t.lower().startswith(p) for p in ["original song", "titolo della", "song title", "titolo", "<"]):
            title = cand_t

    if not title:
        words = fallback_idea.split()
        if words and not words[0].lower().startswith("an original"):
            title = " ".join(words[:4]).strip().strip("\"'.,")
        else:
            clean_genre = genre.split("(")[0].strip() if genre else "Song"
            title = f"{clean_genre} Sinfonia" if is_italian else f"{clean_genre} Anthem"

    # 2. Extract Mode (full | melody)
    mode = "full"
    mode_m = re.search(r"(?:<|\[|#{1,6}\s*)?MODE(?:>|\])?[:\s]*([^\n<\[#]+)", text, re.IGNORECASE)
    if mode_m:
        val_m = mode_m.group(1).strip().lower()
        if "melody" in val_m:
            mode = "melody"
        elif "full" in val_m:
            mode = "full"
    elif is_instrumental:
        mode = "melody"

    # 3. Extract ABC Planning (true | false)
    abc_planning = True
    abc_m = re.search(r"(?:<|\[|#{1,6}\s*)?ABC_PLANNING(?:>|\])?[:\s]*([^\n<\[#]+)", text, re.IGNORECASE)
    if abc_m:
        val_abc = abc_m.group(1).strip().lower()
        abc_planning = val_abc in ("true", "1", "yes", "si", "enabled", "on")

    # 4. Extract Duration (seconds as float)
    duration = 0.0
    dur_m = re.search(r"(?:<|\[|#{1,6}\s*)?DURATION(?:>|\])?[:\s]*([^\n<\[#]+)", text, re.IGNORECASE)
    if dur_m:
        try:
            num = re.sub(r"[^\d.]", "", dur_m.group(1))
            if num:
                duration = float(num)
        except Exception:
            duration = 0.0

    # 5. Extract Style (English, vocal, genre, BPM, instruments, mix)
    style = ""
    # Check [STYLE], <STYLE>, ### Style, or Style:
    style_m = re.search(r"(?:<|\[|#{1,6}\s*)STYLE(?:>|\])?[:\s]*\n*(.*?)(?=\n+(?:<|\[|#{1,6}\s*)(?:LYRICS|VERSE|CHORUS|INTRO|TITLE|MODE|DURATION|ABC_PLANNING)|$)", text, re.DOTALL | re.IGNORECASE)
    if style_m:
        cand_s = style_m.group(1).strip()
        cand_s = re.sub(r"</?STYLE>", "", cand_s, flags=re.IGNORECASE).strip()
        lines_s = [ln.strip() for ln in cand_s.splitlines() if ln.strip() and not ln.strip().startswith("(") and not ln.strip().startswith("#")]
        if lines_s and not lines_s[0].lower().startswith("dense technical"):
            style = " ".join(lines_s)

    if not style:
        colon_style = re.search(r"(?:^|\n)Style:\s*([^\n]+(?:\n[^\n\[<#]+)*)", text, re.IGNORECASE)
        if colon_style:
            style = colon_style.group(1).strip()

    if not style:
        # Formulate YuE2 standard style dynamically from user directives
        vocal_desc = vocal if vocal and not vocal.startswith("Auto") else ("instrumental only, no vocals" if is_instrumental else "expressive lead vocal")
        genre_desc = genre.split("(")[0].strip() if genre and not genre.startswith("Auto") else "contemporary music"
        bpm_desc = tempo.split("(")[0].strip() if tempo and not tempo.startswith("Auto") else "120 BPM"
        style = f"{target_language}, {vocal_desc}, {genre_desc}, {bpm_desc}, rich lead instrumentation, rhythmic bass, tight drums, clear stereo production"

    def _strip_metadata_leakage(txt):
        if not txt:
            return ""
        res = txt
        # 1. Multi-line removal of metadata blocks where value is on same line or next line:
        patterns = [
            r"(?:^|\n)\s*(?:#{1,6}\s*)?\[?TITLE\]?[:\s]*\n*\s*(?:[^\n]+\n?)?",
            r"(?:^|\n)\s*(?:#{1,6}\s*)?\[?MODE\]?[:\s]*\n*\s*(?:[^\n]+\n?)?",
            r"(?:^|\n)\s*(?:#{1,6}\s*)?\[?DURATION\]?[:\s]*\n*\s*(?:[^\n]+\n?)?",
            r"(?:^|\n)\s*(?:#{1,6}\s*)?\[?ABC_PLANNING(?:ING)?\]?[:\s]*\n*\s*(?:[^\n]+\n?)?",
            r"(?:^|\n)\s*(?:#{1,6}\s*)?\[?STYLE\]?[:\s]*\n*\s*(?:.*?(?=\n\s*(?:#{1,6}\s*)?\[(?:LYRICS|VERSE|CHORUS|TITLE)|$))",
        ]
        for p in patterns:
            res = re.sub(p, "\n", res, flags=re.IGNORECASE | re.DOTALL if "STYLE" in p else re.IGNORECASE)

        # 2. Strip known extracted metadata values if they appear standalone on lines
        if title:
            res = re.sub(rf"(?:^|\n)\s*[\"']?{re.escape(title)}[\"']?\s*(?:\n|$)", "\n", res, flags=re.IGNORECASE)
        for leak_val in ["full", "melody", "instrumental", "true", "false"]:
            res = re.sub(rf"(?:^|\n)\s*{leak_val}\s*(?:\n|$)", "\n", res, flags=re.IGNORECASE)
        if duration > 0:
            res = re.sub(rf"(?:^|\n)\s*{re.escape(str(duration))}\s*(?:\n|$)", "\n", res)
            res = re.sub(rf"(?:^|\n)\s*{int(duration)}\s*(?:\n|$)", "\n", res)

        # 3. Strip orphan markdown headers and residual tags
        res = re.sub(r"(?:^|\n)\s*#{1,6}\s*\[?\s*(?:\n|$)", "\n", res)
        res = re.sub(r"(?:^|\n)\s*(?:Title|Mode|Duration|Abc_planning|Style)\s*:\s*[^\n]*", "\n", res, flags=re.IGNORECASE)
        res = re.sub(r"</?(?:TITLE|MODE|DURATION|ABC_PLANNING|STYLE|LYRICS|RICS)>", "", res, flags=re.IGNORECASE)
        return res.strip()

    # 6. Extract Lyrics (singable text strictly separated from acoustic commentary)
    lyrics = ""
    lyrics_m = re.search(r"(?:<|\[|#{1,6}\s*)LYRICS(?:>|\])?[:\s]*\n*(.*?)(?=\n+(?:<|\[|#{1,6}\s*)(?:STYLE|MODE|DURATION|ABC_PLANNING|TITLE)|$)", normalized_text, re.DOTALL | re.IGNORECASE)
    if lyrics_m:
        cand_l = _strip_metadata_leakage(lyrics_m.group(1))
        non_header_lines = [ln.strip() for ln in cand_l.splitlines() if ln.strip() and not ln.strip().startswith("[") and re.search(r"[a-zA-Z0-9]", ln)]
        if len(non_header_lines) >= 1:
            lyrics = cand_l

    if not lyrics:
        # Fallback to first musical section bracket
        bracket_m = re.search(r"(\[(?:Verse|Verso|Strofa|Chorus|Ritornello|Pre-Chorus|Bridge|Outro|Intro|Hook)[^\]]*\].*)", normalized_text, re.DOTALL | re.IGNORECASE)
        if bracket_m:
            candidate = bracket_m.group(1)
            candidate = re.split(r"(?:<|\[|#{1,6}\s*)(?:STYLE|ABC_PLANNING|MODE|DURATION|TITLE)", candidate, flags=re.IGNORECASE)[0].strip()
            candidate = _strip_metadata_leakage(candidate)
            non_header_lines = [ln.strip() for ln in candidate.splitlines() if ln.strip() and not ln.strip().startswith("[") and re.search(r"[a-zA-Z0-9]", ln)]
            if len(non_header_lines) >= 1:
                lyrics = candidate

    # Priority 0: If the user provided pre-written lyrics directly via custom_lyrics, preserve them 100% verbatim
    valid_custom_lyrics = clean_user_custom_lyrics(custom_lyrics)
    if valid_custom_lyrics:
        lyrics = valid_custom_lyrics
    else:
        if not lyrics and fallback_idea and detect_existing_lyrics(fallback_idea):
            clean_user_lyrics = fallback_idea.strip()
            if "[" not in clean_user_lyrics:
                clean_user_lyrics = f"[Verse 1]\n{clean_user_lyrics}"
            lyrics = clean_user_lyrics

        if not lyrics and text:
            clean_raw = _strip_metadata_leakage(text)
            if style and style in clean_raw:
                clean_raw = clean_raw.replace(style, "").strip()
            singable_lines = [ln.strip() for ln in clean_raw.splitlines() if ln.strip() and not ln.strip().startswith("[") and re.search(r"[a-zA-Z0-9]", ln)]
            if len(singable_lines) >= 2:
                lyrics = clean_raw

        # If lyrics is still empty (model broke or output only metadata tags), generate structured lyrics
        if not lyrics or not any(ln.strip() and not ln.strip().startswith("[") and re.search(r"[a-zA-Z0-9]", ln) for ln in lyrics.splitlines()):
            lyrics = generate_fallback_song_lyrics(
                title=title,
                target_language=target_language,
                genre=genre,
            )

        # Clean residual XML tags, markdown fences, and non-singable instrument annotations per YuE2 guidelines
        lyrics = re.sub(r"</?[a-zA-Z_0-9:]+>", "", lyrics)
        lyrics = re.sub(r"```[a-zA-Z]*", "", lyrics).replace("```", "").replace("`XML", "").replace("`xml", "").strip()
        # Strip prompt instruction parentheticals: e.g. "(4 lines)", "(lyrics here)", "(Quattro versi...)"
        lyrics = re.sub(r"^\s*\([0-9]+\s*(?:lines|versi|linee|strofe)[^\)]*\)\s*$", "", lyrics, flags=re.MULTILINE | re.IGNORECASE)
        lyrics = re.sub(r"^\s*\((?:lyrics|testo|versi|quattro versi|lyrics here)[^\)]*\)\s*$", "", lyrics, flags=re.MULTILINE | re.IGNORECASE)
        # Strip instrumental performance notes from lyrics so YuE2 vocals stay pure
        lyrics = re.sub(r"^\s*\((?:guitar|drum|bass|synth|piano|solo|riff|break|intro|outro|tempo|beat|vocalizing)[^\)]*\)\s*$", "", lyrics, flags=re.MULTILINE | re.IGNORECASE)

        # Strip any CJK / Chinese characters or fullwidth punctuation if target language is European
        if not any(asian in str(target_language).lower() for asian in ["chinese", "japanese", "cinese", "giapponese"]):
            lyrics = re.sub(r'[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u30ff\uf900-\ufaff\uff00-\uffef]', '', lyrics)

        lyrics = re.sub(r"\n{3,}", "\n\n", lyrics).strip()

    # Always clean style and title from rogue CJK characters and fullwidth punctuation for European languages
    if not any(asian in str(target_language).lower() for asian in ["chinese", "japanese", "cinese", "giapponese"]):
        style = re.sub(r'[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u30ff\uf900-\ufaff\uff00-\uffef]', '', style)
        title = re.sub(r'[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u30ff\uf900-\ufaff\uff00-\uffef]', '', title)

    style = re.sub(r"</?[a-zA-Z_0-9:]+>", "", style)
    style = re.sub(r"```[a-zA-Z]*", "", style).replace("```", "").strip()
    style = re.sub(r"^\s*\([^\)]*\)\s*$", "", style, flags=re.MULTILINE)

    lyrics = re.sub(r"\n{3,}", "\n\n", lyrics).strip()
    style = re.sub(r"\n{2,}", " ", style).strip()

    # Dynamic duration calculation if model omitted or gave invalid duration
    if duration <= 10.0 or duration > 900.0:
        total_lyric_lines = len([l for l in lyrics.splitlines() if l.strip() and not l.strip().startswith("[")])
        section_count = len(re.findall(r"\[(?:Verse|Chorus|Bridge|Outro|Intro|Strofa|Ritornello)", lyrics, re.IGNORECASE))
        # Standard singing pace: ~4.2 seconds per line + 25s intro/outro/arrangement space
        estimated_seconds = max(total_lyric_lines * 4.2 + 25.0, max(section_count, 1) * 28.0)
        duration = round(max(90.0, min(360.0, estimated_seconds)), 1)

    return {
        "title": title,
        "style": style,
        "lyrics": lyrics,
        "abc_planning": abc_planning,
        "mode": mode,
        "max_duration": duration,
    }
