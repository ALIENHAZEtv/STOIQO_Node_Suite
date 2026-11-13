"""
[STOIQO] Music Prompt & Lyrics Engine — Syllable & Rhythmic Metric Analysis
Provides poetic syllable counting, synalepha (sinalefe) calculation,
meter identification (Endecasillabo, Settenario, Iambic Tetrameter/Pentameter),
rhythmic variance scoring, and automatic stanza structuring for YuE2 & Suno.
"""

import re
import math


# ── Poetic & Phonetic Syllable Counting ───────────────────────────────────────

ROMANCE_VOWELS = set("aeiouyàèéìòóùáéíóúäëïöü")
ENGLISH_VOWELS = set("aeiouy")


def count_syllables_word_italian(word):
    """
    Counts phonetic syllables in an Italian / Romance word based on vowel clusters.
    Treats diphthongs as single metric units by default.
    """
    clean = re.sub(r"[^a-zA-Zàèéìòóùáéíóúäëïöü]", "", word.lower())
    if not clean:
        return 0
    # Group consecutive vowels into single syllable nucleus
    clusters = re.findall(r"[aeiouyàèéìòóùáéíóúäëïöü]+", clean)
    return max(1, len(clusters))


def count_syllables_word_english(word):
    """
    Counts phonetic syllables in an English word using morphology and phonetic rules:
    - Silent 'e' (love, make, time)
    - Consonant + 'le' endings (little, table, bottle)
    - Past tense '-ed' and plural '-es' phonetic variations
    """
    clean = re.sub(r"[^a-z]", "", word.lower())
    if not clean:
        return 0
    if len(clean) <= 3:
        return 1

    # Endings with syllabic 'le' after a consonant (e.g., bot-tle, ta-ble, lit-tle)
    if clean.endswith("le") and len(clean) > 2 and clean[-3] not in ENGLISH_VOWELS:
        base = clean[:-2]
        return count_syllables_word_english(base) + 1

    w = clean
    # Suffix '-ed' after 't' or 'd' is voiced (wai-ted, star-ted = 2 syl), else silent (walked, carved = 1 syl)
    if w.endswith("ed"):
        if not (w.endswith("ted") or w.endswith("ded")):
            w = w[:-2]

    # Suffix '-es' after sibilants adds syllable (box-es, match-es), else silent (makes, comes)
    elif w.endswith("es"):
        if not any(w.endswith(s) for s in ["ses", "zes", "ches", "shes", "xes"]):
            w = w[:-2]

    # Silent 'e' at word boundary (except words ending in 'ee')
    elif w.endswith("e") and not w.endswith("ee") and len(w) > 3:
        w = w[:-1]

    clusters = re.findall(r"[aeiouy]+", w)
    return max(1, len(clusters))


def count_poetic_syllables_line(line, language="Italian"):
    """
    Calculates metric poetic syllables of a single lyric line.
    For Italian and Romance poetry, applies Sinalefe (synalepha):
    When a word ends with a vowel and the next word starts with a vowel,
    they coalesce into a single metric beat in singable lyrics.
    """
    raw_line = re.sub(r"^\[[^\]]+\]", "", line).strip()
    if not raw_line:
        return 0

    is_italian = any(x in str(language).lower() for x in ["italian", "it", "spanish", "es", "romance"])

    if is_italian:
        words = re.findall(r"[a-zA-Zàèéìòóùáéíóúäëïöü]+", raw_line.lower())
        if not words:
            return 0

        raw_syllables = sum(count_syllables_word_italian(w) for w in words)

        # Count Sinalefe (synalepha) occurrences between adjacent words
        sinalefe_count = 0
        for i in range(len(words) - 1):
            w1 = words[i]
            w2 = words[i + 1]
            if w1[-1] in ROMANCE_VOWELS and w2[0] in ROMANCE_VOWELS:
                sinalefe_count += 1

        metric_syllables = max(1, raw_syllables - sinalefe_count)
        return metric_syllables
    else:
        words = re.findall(r"[a-zA-Z]+", raw_line.lower())
        if not words:
            return 0
        return sum(count_syllables_word_english(w) for w in words)


# ── Meter Classification ──────────────────────────────────────────────────────

def classify_meter(avg_syllables, language="Italian"):
    """Identifies the dominant classical or modern poetic meter for a given syllable count."""
    is_italian = any(x in str(language).lower() for x in ["italian", "it", "spanish", "es"])
    s = round(avg_syllables)

    if is_italian:
        if s == 11:
            return "Endecasillabo (11)"
        elif s == 7:
            return "Settenario (7)"
        elif s == 8:
            return "Ottonario (8)"
        elif s == 10:
            return "Decasillabo (10)"
        elif s == 9:
            return "Novenario (9)"
        elif s == 6:
            return "Senario (6)"
        elif s == 12:
            return "Dodecasillabo (12)"
        elif s == 5:
            return "Quinario (5)"
        elif 7 <= avg_syllables <= 11:
            return f"Endecasillabo / Settenario (~{avg_syllables:.1f})"
        else:
            return f"Verso Libero Cantato (~{avg_syllables:.1f})"
    else:
        if s == 8:
            return "Iambic Tetrameter (8)"
        elif s == 10:
            return "Iambic Pentameter (10)"
        elif s == 6:
            return "Trimeter (6)"
        elif s == 12:
            return "Alexandrine (12)"
        elif 7 <= s <= 9:
            return "Ballad Meter (Common Meter 4/4)"
        elif 9 <= s <= 11:
            return "Heroic / Contemporary Pop Stanza"
        else:
            return f"Modern Lyrical Cadence (~{avg_syllables:.1f})"


# ── Full Metrics Analysis ─────────────────────────────────────────────────────

def analyze_lyrics_metrics(lyrics_text, language="Italian"):
    """
    Performs full lyrical rhythm analysis:
    - Analyzes section by section ([Verse], [Chorus], [Bridge], [Outro])
    - Calculates syllable counts per line
    - Computes average syllable count, standard deviation, and rhythmic consistency score (0-100%)
    - Detects dominant poetic meter
    """
    if not lyrics_text:
        return {
            "total_lines": 0,
            "total_words": 0,
            "total_syllables": 0,
            "avg_syllables_per_line": 0.0,
            "sections": [],
            "dominant_song_meter": "None",
            "rhythmic_balance_score": 0,
            "summary": "No lyrics to analyze.",
        }

    lines = lyrics_text.splitlines()
    current_sec_name = "[General]"
    sections_map = {}
    total_words = 0
    all_syllable_counts = []

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            current_sec_name = stripped
            if current_sec_name not in sections_map:
                sections_map[current_sec_name] = []
            continue

        if current_sec_name not in sections_map:
            sections_map[current_sec_name] = []

        # Count syllables and words
        syl = count_poetic_syllables_line(stripped, language=language)
        words = len(re.findall(r"\w+", stripped))
        total_words += words
        all_syllable_counts.append(syl)

        sections_map[current_sec_name].append({
            "text": stripped,
            "syllables": syl,
            "words": words,
        })

    sections_analysis = []
    for sec_name, sec_lines in sections_map.items():
        if not sec_lines:
            continue
        s_counts = [item["syllables"] for item in sec_lines]
        avg_s = sum(s_counts) / len(s_counts) if s_counts else 0.0

        # Calculate standard deviation
        if len(s_counts) > 1:
            variance = sum((x - avg_s) ** 2 for x in s_counts) / len(s_counts)
            std_dev = math.sqrt(variance)
        else:
            std_dev = 0.0

        is_balanced = std_dev <= 2.2
        sec_meter = classify_meter(avg_s, language=language)

        sections_analysis.append({
            "section_name": sec_name,
            "line_count": len(sec_lines),
            "lines": sec_lines,
            "syllable_counts": s_counts,
            "avg_syllables": round(avg_s, 1),
            "std_dev": round(std_dev, 2),
            "is_balanced": is_balanced,
            "dominant_meter": sec_meter,
        })

    total_lines = len(all_syllable_counts)
    total_syl = sum(all_syllable_counts)
    global_avg = (total_syl / total_lines) if total_lines > 0 else 0.0

    # Rhythmic balance score (100 = perfectly matched cadence across all verses)
    if total_lines > 1:
        global_var = sum((x - global_avg) ** 2 for x in all_syllable_counts) / total_lines
        global_std = math.sqrt(global_var)
        # 0 std dev -> 100%, 1.0 -> 90%, 2.0 -> 80%, 3.0 -> 65%, 5.0+ -> <40%
        score = max(20, min(100, int(100 - (global_std * 11.5))))
    else:
        score = 80

    song_meter = classify_meter(global_avg, language=language)
    summary_desc = f"{total_lines} lines | Avg: {global_avg:.1f} syl/line | {song_meter} | Cadence: {score}%"

    return {
        "total_lines": total_lines,
        "total_words": total_words,
        "total_syllables": total_syl,
        "avg_syllables_per_line": round(global_avg, 1),
        "sections": sections_analysis,
        "dominant_song_meter": song_meter,
        "rhythmic_balance_score": score,
        "summary": summary_desc,
    }


# ── Auto-Structuring & Cadence Balancing ──────────────────────────────────────

def auto_structure_unstructured_lyrics(raw_text, structure_preset="Standard"):
    """
    Transforms tagless prose or unformatted lyrics into standard YuE2 / Suno
    musical sections ([Verse 1], [Chorus], [Verse 2], [Bridge], [Outro]).
    Ensures 4 lines per standard verse/chorus and 2-4 lines for outro.
    """
    if not raw_text:
        return ""

    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    if not lines:
        return ""

    # If the text already has recognized section headers, leave intact
    if any(re.search(r"^\s*\[(?:Verse|Chorus|Bridge|Outro|Intro|Pre-Chorus|Hook|Strofa|Ritornello)", ln, re.IGNORECASE) for ln in lines):
        return raw_text

    # Default 4-line block sequencing
    section_sequence = [
        "[Verse 1]",
        "[Chorus]",
        "[Verse 2]",
        "[Chorus]",
        "[Bridge]",
        "[Outro]",
    ]

    structured_output = []
    line_idx = 0
    sec_idx = 0

    while line_idx < len(lines):
        sec_name = section_sequence[min(sec_idx, len(section_sequence) - 1)]
        if sec_idx >= len(section_sequence) - 1 and (len(lines) - line_idx) > 4:
            # If still many lines remaining, loop verse/chorus
            sec_name = f"[Verse {((sec_idx // 2) + 1)}]" if sec_idx % 2 == 0 else "[Chorus]"

        structured_output.append(sec_name)
        # Take 4 lines for verse/chorus, or remaining lines if outro
        take_count = 2 if sec_name == "[Outro]" and (len(lines) - line_idx) <= 4 else min(4, len(lines) - line_idx)
        for _ in range(take_count):
            structured_output.append(lines[line_idx])
            line_idx += 1
        structured_output.append("")  # Blank line separator
        sec_idx += 1

    return "\n".join(structured_output).strip()


def auto_balance_long_lines(lyrics_text, max_syllables=18, language="Italian"):
    """
    Detects runaway poetic lines (>18 syllables) that cause audio models
    (YuE2 / Suno) to clip, hallucinate or rush vocal delivery.
    Splits them gracefully at natural grammatical pauses (commas, semicolons,
    dashes, or conjunctions) into balanced hemistiches.
    """
    if not lyrics_text:
        return ""

    conjunctions = [" e ", " ed ", " ma ", " and ", " but ", " or ", " while ", " quando ", " mentre "]
    out_lines = []

    for line in lyrics_text.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("["):
            out_lines.append(trimmed)
            continue

        syl = count_poetic_syllables_line(trimmed, language=language)
        if syl <= max_syllables:
            out_lines.append(trimmed)
            continue

        # Look for natural splitting point near middle: comma, semicolon, dash, or conjunction
        split_done = False
        for delim in [";", ",", " — ", " - "]:
            if delim in trimmed:
                parts = trimmed.split(delim)
                if len(parts) == 2:
                    p1 = parts[0].strip() + ("," if delim in [",", ";"] else "")
                    p2 = parts[1].strip()
                    if count_poetic_syllables_line(p1, language=language) >= 4 and count_poetic_syllables_line(p2, language=language) >= 4:
                        out_lines.append(p1)
                        out_lines.append(p2)
                        split_done = True
                        break

        if not split_done:
            for conj in conjunctions:
                if conj in trimmed.lower():
                    idx = trimmed.lower().find(conj)
                    p1 = trimmed[:idx].strip()
                    p2 = trimmed[idx:].strip()
                    if count_poetic_syllables_line(p1, language=language) >= 4 and count_poetic_syllables_line(p2, language=language) >= 4:
                        out_lines.append(p1)
                        out_lines.append(p2)
                        split_done = True
                        break

        if not split_done:
            out_lines.append(trimmed)

    return "\n".join(out_lines)
