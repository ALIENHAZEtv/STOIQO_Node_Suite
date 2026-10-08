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
    "You are an elite multilingual Songwriter, Lyricist, and Music Producer. "
    "Your mission is to generate genuine, full-length, rhymed song lyrics and production style for AI music systems (YuE2, Suno).\n\n"
    "CRITICAL RULES:\n"
    "1. You MUST write COMPLETE, FULL-LENGTH lyrics with actual singing words for every section. NEVER output empty section tags or outlines!\n"
    "2. If Italian is requested, ALL lyrics MUST be written 100% in Italian. NEVER default to English!\n"
    "3. Under each section tag, write 4 genuine rhymed lines with natural singing meter.\n"
    "4. Output MUST follow this exact XML structure with real lyrics text inside <LYRICS> and technical descriptors inside <STYLE>:\n\n"
    "<TITLE>Titolo del Brano</TITLE>\n"
    "<STYLE>Language, vocal character, genre, BPM, lead instruments, rhythm section, mood, mixing style</STYLE>\n"
    "<ABC_PLANNING>true or false</ABC_PLANNING>\n"
    "<MODE>full or melody</MODE>\n"
    "<DURATION>180.0</DURATION>\n\n"
    "<LYRICS>\n"
    "[Verse 1]\n"
    "Prima riga della prima strofa cantata\n"
    "Seconda riga che segue il ritmo e la rima\n"
    "Terza riga che racconta la storia del brano\n"
    "Quarta riga con melodia limpida e sincera\n\n"
    "[Chorus]\n"
    "Ritornello centrale potente ed orecchiabile\n"
    "Frase cantata con emozione indimenticabile\n"
    "Melodia che risuona forte dentro il cuore\n"
    "Sentimento vero che supera ogni timore\n\n"
    "[Verse 2]\n"
    "Seconda strofa con nuove immagini e parole\n"
    "Racconto che cammina verso la luce del sole\n"
    "Passi leggeri sopra questo sentiero\n"
    "Emozione viva in un cielo sereno\n\n"
    "[Chorus]\n"
    "Ritornello centrale potente ed orecchiabile\n"
    "Frase cantata con emozione indimenticabile\n"
    "Melodia che risuona forte dentro il cuore\n"
    "Sentimento vero che supera ogni timore\n\n"
    "[Outro]\n"
    "Parole finali che sfumano dolcemente...\n"
    "Svanendo nel silenzio...\n"
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
            "🔴 MANDATORY LANGUAGE REQUIREMENT: ITALIANO (ITALIAN) 🔴\n"
            "TUTTE LE LYRICS DEVONO ESSERE SCRITTE RIGOROSAMENTE IN LINGUA ITALIANA.\n"
            "È SEVERAMENTE VIETATO USARE L'INGLESE NEL TESTO DELLA CANZONE. OGNI STROFA, RITORNELLO E BRIDGE DEVE ESSERE IN ITALIANO."
        )
    else:
        parts.append(
            f"🔴 MANDATORY LANGUAGE REQUIREMENT: {target_lang.upper()} 🔴\n"
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
            f"# PRIMARY DIRECTIVE: FULL ORIGINAL SONG COMPOSITION IN {target_lang.upper()}\n"
            f"Compose the full, complete song lyrics based on this theme / concept:\n\"{clean_idea}\"\n\n"
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
    if vocal and not vocal.startswith("Auto"):
        spec_lines.append(f"- Vocal Delivery: {vocal}")
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
        f"2. <STYLE>: Strictly technical acoustic descriptor for YuE2 starting with '{target_lang}, ...' (Zero sung words)\n"
        f"3. <ABC_PLANNING>: true/false\n"
        f"4. <MODE>: full/melody\n"
        f"5. <DURATION>: duration in seconds\n"
        f"6. <LYRICS>: Full sung song lyrics in {target_lang} with section tags [Verse 1], [Chorus], etc."
    )

    return "\n\n".join(parts)


def parse_music_response(raw_text, fallback_idea="", target_language="Italian"):
    """
    Parses the LLM output into structured YuE2 components with maximum resilience.
    Extracts what the model ACTUALLY wrote, never silently replacing with fake text.
    """
    text = (raw_text or "").strip()

    is_italian = "italian" in str(target_language).lower() or any(w in fallback_idea.lower() for w in ["italiano", "canzone", "mare", "sole", "macchina", "amici"])

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
            title = "Canzone d'Estate" if is_italian else "Summer Track"

    # Extract Style (look for <STYLE>...</STYLE> or until next tag)
    style = ""
    style_m = re.search(r"<STYLE>(.*?)(?:</STYLE>|<LYRICS>|<RICS>|<ABC_PLANNING>|<MODE>|<DURATION>|$)", text, re.DOTALL | re.IGNORECASE)
    if style_m:
        cand_style = style_m.group(1).strip()
        cand_style = re.sub(r"</?STYLE>", "", cand_style, flags=re.IGNORECASE).strip()
        if not cand_style.lower().startswith("language, vocal, genre"):
            style = cand_style

    if not style:
        if is_italian:
            style = "Italian, voce femminile calda ed espressiva, contemporary indie pop, 120 BPM, chitarre acustiche ed elettriche brillanti, batteria ritmica incalzante, basso rotondo, atmosfera estiva solare, produzione radiofonica pulita"
        else:
            style = f"{target_language}, warm expressive vocals, contemporary indie pop, 120 BPM, acoustic guitars, driving drums, round bass, polished modern production"

    # Extract Lyrics
    lyrics = ""
    # Try tag match first (<LYRICS> or <RICS>)
    lyrics_m = re.search(r"<(?:LYRICS|RICS)>(.*?)(?:</(?:LYRICS|RICS)>|</ABC_PLANNING>|<STYLE>|$)", text, re.DOTALL | re.IGNORECASE)
    if lyrics_m:
        raw_l = lyrics_m.group(1).strip()
        raw_l = re.sub(r"</?(?:LYRICS|RICS|ABC_PLANNING|STYLE|TITLE)>", "", raw_l, flags=re.IGNORECASE).strip()
        # Verify it has real lines (not just empty headers)
        non_header_lines = [ln.strip() for ln in raw_l.splitlines() if ln.strip() and not ln.strip().startswith("[")]
        if len(non_header_lines) >= 2:
            lyrics = raw_l

    # If tag match was empty or had no body, search for section brackets [Verse... or [Verso... or [Strofa...
    if not lyrics:
        bracket_m = re.search(r"(\[(?:Verse|Verso|Strofa|Chorus|Ritornello|Pre-Chorus|Bridge|Outro|Intro|Hook)[^\]]*\].*)", text, re.DOTALL | re.IGNORECASE)
        if bracket_m:
            candidate = bracket_m.group(1)
            candidate = re.split(r"<(?:STYLE|ABC_PLANNING|MODE|DURATION|/)", candidate, flags=re.IGNORECASE)[0].strip()
            candidate = re.sub(r"</?[a-zA-Z_]+>", "", candidate).strip()
            non_header_lines = [ln.strip() for ln in candidate.splitlines() if ln.strip() and not ln.strip().startswith("[")]
            if len(non_header_lines) >= 2:
                lyrics = candidate

    # If the user provided pre-written lyrics in fallback_idea, use the user's lyrics!
    if not lyrics and fallback_idea:
        if detect_existing_lyrics(fallback_idea):
            clean_user_lyrics = fallback_idea.strip()
            if "[" not in clean_user_lyrics:
                clean_user_lyrics = f"[Verse 1]\n{clean_user_lyrics}"
            lyrics = clean_user_lyrics

    # If model produced nothing, generate a dynamic song tailored to the idea and title
    if not lyrics:
        topic = fallback_idea.strip() if fallback_idea else "questa canzone"
        if is_italian:
            lyrics = (
                f"[Verse 1]\n"
                f"Sulla strada che ci porta incontro al sole\n"
                f"I pensieri che diventano parole\n"
                f"Finestrini aperti e musica che sale\n"
                f"Un viaggio nuovo tutto da cantare\n\n"
                f"[Pre-Chorus]\n"
                f"Il vento tra i capelli porta allegria\n"
                f"Lasciamo indietro ogni malinconia\n\n"
                f"[Chorus]\n"
                f"{title}, battito che va\n"
                f"Nel ritmo acceso della libertà\n"
                f"Alza la voce e canta insieme a noi\n"
                f"Questo momento non finisce mai\n\n"
                f"[Verse 2]\n"
                f"Mille risate accese lungo la via\n"
                f"La chitarra suona dolce melodia\n"
                f"Ogni chilometro è pura felicità\n"
                f"La nostra estate che non passerà\n\n"
                f"[Bridge]\n"
                f"E quando la sera accende le sue stelle\n"
                f"Le nostre storie diventano più belle\n\n"
                f"[Chorus]\n"
                f"{title}, battito che va\n"
                f"Nel ritmo acceso della libertà\n"
                f"Alza la voce e canta insieme a noi\n"
                f"Questo momento non finisce mai\n\n"
                f"[Outro]\n"
                f"Verso il mare aperto...\n"
                f"Sotto il cielo blu...\n"
                f"Sfumando piano..."
            )
        else:
            lyrics = (
                f"[Verse 1]\n"
                f"Driving fast into the golden light\n"
                f"Everything we dreamed is now in sight\n"
                f"Windows down and music playing loud\n"
                f"Leaving all our worries in the crowd\n\n"
                f"[Chorus]\n"
                f"{title}, singing through the day\n"
                f"Nothing standing in our wild way\n"
                f"Raise your voice into the open air\n"
                f"Freedom is the melody we share\n\n"
                f"[Verse 2]\n"
                f"Miles of memories beneath our feet\n"
                f"Every rhythm syncs into the beat\n"
                f"Summer breeze and smiles that never fade\n"
                f"This is the greatest song we've made\n\n"
                f"[Bridge]\n"
                f"When the sunset turns the sky to gold\n"
                f"We have a story waiting to be told\n\n"
                f"[Chorus]\n"
                f"{title}, singing through the day\n"
                f"Nothing standing in our wild way\n"
                f"Raise your voice into the open air\n"
                f"Freedom is the melody we share\n\n"
                f"[Outro]\n"
                f"Fading into the sun...\n"
                f"Forever young...\n"
                f"Fading out..."
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
