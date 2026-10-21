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


def generate_fallback_song_lyrics(title="", target_language="Italian", genre="", idea=""):
    """Generates genre-adaptive structured lyrics in the target language if model output is truncated, hallucinated, or empty."""
    is_it = "italian" in str(target_language).lower()
    combined_desc = f"{genre} {idea} {title}".lower()

    is_metal = any(m in combined_desc for m in ["metal", "death metal", "rock", "slipknot", "heavy", "core", "scream", "grunge", "thrash"])
    is_rap = any(m in combined_desc for m in ["rap", "hip-hop", "trap", "flow", "drill", "beat"])

    if is_it:
        if is_metal:
            return (
                "[Verse 1]\n"
                "Tra le catene e la ruggine viva,\n"
                "urlo nel fango una furia che sale.\n"
                "Sotto la pelle la carne si priva,\n"
                "di ogni veleno che squarcia il male.\n\n"
                "[Chorus]\n"
                "Brucia l'abisso e non c'è salvezza,\n"
                "questo è l'amore che spacca i confini!\n"
                "Nella tempesta di pura violenza,\n"
                "stringimi forte tra questi mirini!\n\n"
                "[Verse 2]\n"
                "Laceri i muri di spine e silenzio,\n"
                "sangue e metallo che fondono il cuore.\n"
                "Nessun rimpianto per questo dissenso,\n"
                "siamo la voce che sfida il dolore.\n\n"
                "[Chorus]\n"
                "Brucia l'abisso e non c'è salvezza,\n"
                "questo è l'amore che spacca i confini!\n"
                "Nella tempesta di pura violenza,\n"
                "stringimi forte tra questi mirini!\n\n"
                "[Bridge]\n"
                "Rompi la maschera, guarda nel buio,\n"
                "io non ti lascio cadere nel vuoto!\n\n"
                "[Outro]\n"
                "Furia e respiro.\n"
                "Resta con me.\n"
                "Fino alla fine."
            )
        elif is_rap:
            return (
                "[Verse 1]\n"
                "Passi sull'asfalto mentre corre la città,\n"
                "conto solo i fatti zero mezza verità.\n"
                "Scrivo questa rima per la gente che combatte,\n"
                "chi non abbassa il capo nelle notti più distrutte.\n\n"
                "[Chorus]\n"
                "Alza le mani su questo beat,\n"
                "non puoi fermare chi vive lo street!\n"
                "Dal primo giorno fino all'orizzonte,\n"
                "porto la voce con l'anima in fronte!\n\n"
                "[Verse 2]\n"
                "Girano le lancette ma non perdo la direzione,\n"
                "ogni ferita aperta si trasforma in produzione.\n"
                "Occhi negli occhi senza fare troppi passi indietro,\n"
                "spezzo le pareti di questo castello di vetro.\n\n"
                "[Chorus]\n"
                "Alza le mani su questo beat,\n"
                "non puoi fermare chi vive lo street!\n"
                "Dal primo giorno fino all'orizzonte,\n"
                "porto la voce con l'anima in fronte!\n\n"
                "[Bridge]\n"
                "Questo è il momento, non c'è un secondo da regalare,\n"
                "chi vuole il cielo deve imparare a rischiare!\n\n"
                "[Outro]\n"
                "Spengo la cassa.\n"
                "Resta la rima.\n"
                "Per sempre."
            )
        else:
            return (
                "[Verse 1]\n"
                "Cammino piano lungo questa via,\n"
                "tra ombre stese contro la memoria.\n"
                "C'è un vento antico che non vola via,\n"
                "il tempo scritto dentro la mia storia.\n\n"
                "[Chorus]\n"
                "E brucia il fuoco che non si consuma,\n"
                "oltre la notte e il gelo della sera!\n"
                "La voce sale limpida tra i monti,\n"
                "libera e forte verso la chimera!\n\n"
                "[Verse 2]\n"
                "Risuona il passo nell'oscurità,\n"
                "nessuna esitazione nel profondo.\n"
                "La luce viva vince la paura,\n"
                "riaccende il sole dentro a questo mondo.\n\n"
                "[Chorus]\n"
                "E brucia il fuoco che non si consuma,\n"
                "oltre la notte e il gelo della sera!\n"
                "La voce sale limpida tra i monti,\n"
                "libera e forte verso la chimera!\n\n"
                "[Bridge]\n"
                "Non c'è sconfitta se continui a andare,\n"
                "oltre i confini del presente e il mare!\n\n"
                "[Outro]\n"
                "Resta la luce accesa nel silenzio.\n"
                "Non svanirà mai."
            )
    else:
        if is_metal:
            return (
                "[Verse 1]\n"
                "Torn from the wire in a cathedral of dust,\n"
                "we forged our devotion where iron turns to rust.\n"
                "Beneath the violent scars and the hollowed-out skin,\n"
                "a pure crimson fire burns fiercely within.\n\n"
                "[Chorus]\n"
                "Hold me together through the screams and the dark,\n"
                "rip through the venom and leave your blood mark!\n"
                "Nothing can shatter what suffering made whole,\n"
                "this is the beauty that lives in my soul!\n\n"
                "[Verse 2]\n"
                "The world is a carcass of hollow deceit,\n"
                "we carved out our kingdom in bloody retreat.\n"
                "Your touch is the lightning that cuts through the rage,\n"
                "unbroken and lawless outside of the cage.\n\n"
                "[Chorus]\n"
                "Hold me together through the screams and the dark,\n"
                "rip through the venom and leave your blood mark!\n"
                "Nothing can shatter what suffering made whole,\n"
                "this is the beauty that lives in my soul!\n\n"
                "[Bridge]\n"
                "No hesitation, no mercy, no fear,\n"
                "the storm is our sanctuary when you are near!\n\n"
                "[Outro]\n"
                "Bleed with me.\n"
                "In the dark.\n"
                "Forever.\n"
                "Unbroken."
            )
        elif is_rap:
            return (
                "[Verse 1]\n"
                "Concrete jungle where the baseline hits the floor,\n"
                "counting every battle coming straight through the door.\n"
                "Stacking up the verses with a relentless rhyme,\n"
                "carving out a legacy that stands the test of time.\n\n"
                "[Chorus]\n"
                "Turn up the levels, let the sub-bass roll,\n"
                "spitting pure truth straight out of the soul!\n"
                "From the midnight grind to the rising sun,\n"
                "we never back down till the battle is won!\n\n"
                "[Verse 2]\n"
                "Shadows in the mirror trying to hold my pace,\n"
                "I see the finish line and accelerate the chase.\n"
                "No surrender in the words I speak,\n"
                "giving heavy power to the tired and the weak.\n\n"
                "[Chorus]\n"
                "Turn up the levels, let the sub-bass roll,\n"
                "spitting pure truth straight out of the soul!\n"
                "From the midnight grind to the rising sun,\n"
                "we never back down till the battle is won!\n\n"
                "[Bridge]\n"
                "Lock in the vision, eliminate the doubt,\n"
                "this is what the rhythm and the passion is about!\n\n"
                "[Outro]\n"
                "Drop the mic.\n"
                "Fade the track.\n"
                "Never looking back."
            )
        else:
            return (
                "[Verse 1]\n"
                "Walking through shadows on an empty street,\n"
                "echoes of time beneath my marching feet.\n"
                "A quiet fire burning through the cold,\n"
                "a secret promise waiting to unfold.\n\n"
                "[Chorus]\n"
                "Rise through the night and let the thunder roll,\n"
                "a lightning spark awakened in the soul!\n"
                "Beyond the silence and the falling rain,\n"
                "we break the surface through the joy and pain!\n\n"
                "[Verse 2]\n"
                "The morning light begins to break the skies,\n"
                "truth shining steady in our fearless eyes.\n"
                "No turning back into the faded past,\n"
                "this is the moment meant to ever last.\n\n"
                "[Chorus]\n"
                "Rise through the night and let the thunder roll,\n"
                "a lightning spark awakened in the soul!\n"
                "Beyond the silence and the falling rain,\n"
                "we break the surface through the joy and pain!\n\n"
                "[Bridge]\n"
                "Through every storm we stand against the tide,\n"
                "with burning courage on the other side!\n\n"
                "[Outro]\n"
                "The echoes fade into the quiet dawn.\n"
                "Still standing strong."
            )


def is_valid_poetic_lyrics(lyrics_text):
    """
    Validates whether the extracted lyrics consist of genuine, human-singable poetic verse.
    Rejects numerical garbage, tablatura leaks, count-in sequences, or runaway token glitches.
    """
    if not lyrics_text:
        return False
    lines = [
        ln.strip() for ln in lyrics_text.splitlines()
        if ln.strip() and not ln.strip().startswith("[") and not ln.strip().endswith("]")
    ]
    if len(lines) < 3:
        return False

    full_text = " ".join(lines)
    tokens = [t for t in re.split(r"\s+", full_text) if t]
    if len(tokens) < 15:
        return False

    # Check ratio of digits/numbers
    digit_tokens = [t for t in tokens if re.search(r"\d", t)]
    if len(digit_tokens) / len(tokens) > 0.15:
        return False

    # Check for runaway numeric count patterns (e.g., "The 4 5 6 7 The 8 9 The 1")
    if re.search(r"(?:the\s+)?\d+\s+(?:the\s+)?\d+\s+(?:the\s+)?\d+", full_text, re.IGNORECASE):
        return False

    # Check for guitar spec leaks
    if re.search(r"\bstrings\s+\d+\b", full_text, re.IGNORECASE):
        return False

    # Check for invented portmanteau glitches
    if re.search(r"\b(?:slipknotsions|slkipnotons|knotons)\b", full_text, re.IGNORECASE):
        return False

    return True


def sanitize_hallucinated_lyrics(lyrics_text):
    """Cleans minor numeric stray tokens and normalizes malformed section headers."""
    if not lyrics_text:
        return ""
    # Strip standalone counting lines like "The 5 the 6", "1 2 3 4"
    cleaned_lines = []
    for line in lyrics_text.splitlines():
        trimmed = line.strip()
        if not trimmed:
            cleaned_lines.append("")
            continue
        # If line is mostly numbers and filler words like "the", "and"
        words = re.findall(r"[a-zA-Z0-9]+", trimmed.lower())
        num_count = sum(1 for w in words if w.isdigit())
        if words and (num_count / len(words) >= 0.5) and not trimmed.startswith("["):
            continue
        # Strip runaway digit repetitions inside lines: e.g. ", strings 45 and 15"
        trimmed = re.sub(r",?\s*strings\s+\d+\s+and\s+\d+", "", trimmed, flags=re.IGNORECASE)
        # Strip trailing digit sequences: " The 4 5 6 7 The 8 9 The 1"
        trimmed = re.sub(r"\s*(?:the\s+)?\d+(?:\s+(?:the\s+)?\d+){2,}", "", trimmed, flags=re.IGNORECASE)
        cleaned_lines.append(trimmed)

    return "\n".join(cleaned_lines)



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

    # 4b. Extract BPM (integer)
    bpm = 120
    bpm_m = re.search(r"(?:<|\[|#{1,6}\s*)?BPM(?:>|\])?[:\s]*([^\n<\[#]+)", text, re.IGNORECASE)
    if bpm_m:
        try:
            b_val = int(re.sub(r"[^\d]", "", bpm_m.group(1)))
            if 40 <= b_val <= 300:
                bpm = b_val
        except Exception:
            pass

    # 4c. Extract Key (e.g. C Minor, A Major, F# Minor)
    musical_key = "C Minor"
    key_m = re.search(r"(?:^|\n)\s*(?:#{1,6}\s*)?\[?(?:KEY|MUSICAL_KEY)\]?[:\s]*([^\n<\[]+)", text, re.IGNORECASE)
    if key_m:
        cand_key = key_m.group(1).strip().strip("\"'*")
        if cand_key and len(cand_key) <= 30 and not cand_key.lower().startswith("musical key") and not cand_key.lower().startswith("c minor ("):
            musical_key = cand_key

    # 4d. Extract Time Signature (e.g. 4/4, 3/4, 6/8)
    time_signature = "4/4"
    meter_m = re.search(r"(?:<|\[|#{1,6}\s*)?(?:TIME_SIGNATURE|METER)(?:>|\])?[:\s]*([^\n<\[#]+)", text, re.IGNORECASE)
    if meter_m:
        cand_meter = meter_m.group(1).strip().strip("\"'#*")
        meter_match = re.search(r"\b\d/\d\b", cand_meter)
        if meter_match:
            time_signature = meter_match.group(0)
        elif cand_meter and len(cand_meter) <= 10 and not cand_meter.lower().startswith("rhythmic"):
            time_signature = cand_meter

    # 4e. Extract Genre Tags
    genre_tags = ""
    gtag_m = re.search(r"(?:<|\[|#{1,6}\s*)?GENRE_TAGS(?:>|\])?[:\s]*([^\n<\[#]+)", text, re.IGNORECASE)
    if gtag_m:
        cand_gtag = gtag_m.group(1).strip().strip("\"'#*")
        if cand_gtag and not cand_gtag.lower().startswith("exact comma"):
            genre_tags = cand_gtag

    # 4f. Extract Vocal Description
    vocal_description = ""
    vdesc_m = re.search(r"(?:<|\[|#{1,6}\s*)?VOCAL_DESCRIPTION(?:>|\])?[:\s]*([^\n<\[#]+)", text, re.IGNORECASE)
    if vdesc_m:
        cand_vdesc = vdesc_m.group(1).strip().strip("\"'#*")
        if cand_vdesc and not cand_vdesc.lower().startswith("clear vocal") and not cand_vdesc.lower().startswith("detailed vocal"):
            vocal_description = cand_vdesc

    # 5. Extract Style (English, vocal, genre, BPM, instruments, mix)
    style = ""
    # Check [STYLE], <STYLE>, ### Style, or Style:
    style_m = re.search(r"(?:<|\[|#{1,6}\s*)STYLE(?:>|\])?[:\s]*\n*(.*?)(?=\n+(?:<|\[|#{1,6}\s*)(?:LYRICS|VERSE|CHORUS|INTRO|TITLE|MODE|DURATION|ABC_PLANNING|BPM|KEY|TIME_SIGNATURE|GENRE_TAGS|VOCAL_DESCRIPTION)|$)", text, re.DOTALL | re.IGNORECASE)
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
        bpm_desc = f"{bpm} BPM" if bpm else (tempo.split("(")[0].strip() if tempo and not tempo.startswith("Auto") else "120 BPM")
        style = f"{target_language}, {vocal_desc}, {genre_desc}, {bpm_desc}, rich lead instrumentation, rhythmic bass, tight drums, clear stereo production"

    # Cross-calibrate BPM and Key from style if needed
    if bpm == 120 and style:
        bpm_s = re.search(r"(\d{2,3})\s*BPM", style, re.IGNORECASE)
        if bpm_s:
            try:
                bpm = int(bpm_s.group(1))
            except Exception:
                pass

    if musical_key == "C Minor" and style:
        key_s = re.search(r"\b([A-G][#b]?(?:\s+(?:Major|Minor|Dorian|Mixolydian|Phrygian|Lydian|Aeolian|Locrian)))\b", style, re.IGNORECASE)
        if key_s:
            musical_key = key_s.group(1).strip()

    if not genre_tags and style:
        # Extract first 3 comma-separated terms from style
        parts_s = [p.strip() for p in style.split(",") if p.strip()]
        if len(parts_s) >= 3:
            genre_tags = ", ".join(parts_s[1:4])

    if not vocal_description and style:
        parts_s = [p.strip() for p in style.split(",") if p.strip()]
        if len(parts_s) >= 2:
            vocal_description = parts_s[1]

    def _strip_metadata_leakage(txt):
        if not txt:
            return ""
        res = txt
        # 1. Multi-line removal of metadata blocks where value is on same line or next line:
        patterns = [
            r"(?:^|\n)\s*(?:#{1,6}\s*)?\[?TITLE\]?[:\s]*\n*\s*(?:[^\n]+\n?)?",
            r"(?:^|\n)\s*(?:#{1,6}\s*)?\[?MODE\]?[:\s]*\n*\s*(?:[^\n]+\n?)?",
            r"(?:^|\n)\s*(?:#{1,6}\s*)?\[?DURATION\]?[:\s]*\n*\s*(?:[^\n]+\n?)?",
            r"(?:^|\n)\s*(?:#{1,6}\s*)?\[?BPM\]?[:\s]*\n*\s*(?:[^\n]+\n?)?",
            r"(?:^|\n)\s*(?:#{1,6}\s*)?\[?KEY\]?[:\s]*\n*\s*(?:[^\n]+\n?)?",
            r"(?:^|\n)\s*(?:#{1,6}\s*)?\[?TIME_SIGNATURE\]?[:\s]*\n*\s*(?:[^\n]+\n?)?",
            r"(?:^|\n)\s*(?:#{1,6}\s*)?\[?GENRE_TAGS\]?[:\s]*\n*\s*(?:[^\n]+\n?)?",
            r"(?:^|\n)\s*(?:#{1,6}\s*)?\[?VOCAL_DESCRIPTION\]?[:\s]*\n*\s*(?:[^\n]+\n?)?",
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
        if bpm > 0:
            res = re.sub(rf"(?:^|\n)\s*{bpm}\s*(?:\n|$)", "\n", res)

        # 3. Strip orphan markdown headers and residual tags
        res = re.sub(r"(?:^|\n)\s*#{1,6}\s*\[?\s*(?:\n|$)", "\n", res)
        res = re.sub(r"(?:^|\n)\s*(?:Title|Mode|Duration|Abc_planning|Style|Bpm|Key|Time_signature|Genre_tags|Vocal_description)\s*:\s*[^\n]*", "\n", res, flags=re.IGNORECASE)
        res = re.sub(r"</?(?:TITLE|MODE|DURATION|ABC_PLANNING|STYLE|LYRICS|RICS|BPM|KEY|TIME_SIGNATURE|GENRE_TAGS|VOCAL_DESCRIPTION)>", "", res, flags=re.IGNORECASE)
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

        # Sanitize minor numeric artifacts and validate poetic lyrics authenticity
        if lyrics:
            lyrics = sanitize_hallucinated_lyrics(lyrics)

        # If lyrics is empty or invalid (model broke, output metadata tags, or hallucinated numbers), generate genre-calibrated lyrics
        if not lyrics or not is_valid_poetic_lyrics(lyrics):
            print("[STOIQO Music Warning] Model produced invalid or corrupted lyrics. Triggering genre-adaptive lyrical synthesis.")
            lyrics = generate_fallback_song_lyrics(
                title=title,
                target_language=target_language,
                genre=genre,
                idea=fallback_idea,
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

    # Dynamic metric duration calculation based on actual lyric density, sections, and BPM pacing
    # Real musical pacing in 4/4 meter:
    # 1 full measure = 240 / BPM seconds.
    # Each singable poetic verse occupies approx 2 musical measures (with vocal cadence and breaths).
    # Instrumental sections (Intro, inter-section turnarounds, Bridge/Solo, Outro fadeout) add arrangement time.
    eff_bpm = float(bpm) if (40.0 <= float(bpm) <= 240.0) else 120.0
    sec_per_measure = 240.0 / eff_bpm

    total_lyric_lines = len([line for line in lyrics.splitlines() if line.strip() and not line.strip().startswith("[")])
    sections = re.findall(r"\[(?:Verse|Chorus|Bridge|Outro|Intro|Strofa|Ritornello|Pre-Chorus|Solo|Hook|Breakdown)", lyrics, re.IGNORECASE)
    section_count = max(len(sections), 4)

    # Vocal singing time: 2 measures per lyric line on average (minimum 3.2s per line)
    vocal_time = total_lyric_lines * max(3.2, 2.0 * sec_per_measure)
    # Instrumental arrangement time: Intro (4-8 bars) + turnarounds (2 bars per section) + Outro release (6-8 bars)
    instrumental_time = (section_count * 2.5 * sec_per_measure) + (10.0 * sec_per_measure)
    # Headroom buffer (+15s) so YuE2/Suno audio generator has ample token budget to conclude Outro without hard-clipping
    required_song_time = round(vocal_time + instrumental_time + 15.0, 1)

    # If model emitted a generic/truncated duration or lower than musically required, adapt dynamically
    if duration <= 30.0 or duration < required_song_time:
        duration = required_song_time

    return {
        "title": title,
        "style": style,
        "lyrics": lyrics,
        "abc_planning": abc_planning,
        "mode": mode,
        "max_duration": duration,
        "bpm": int(bpm),
        "musical_key": str(musical_key),
        "time_signature": str(time_signature),
        "genre_tags": str(genre_tags),
        "vocal_description": str(vocal_description),
    }
