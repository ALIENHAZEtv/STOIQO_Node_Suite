"""
[STOIQO] Character Memory Bank & Visual Lorebook Node
Persistent character identity module that stores visual DNA (face, eyes, hair, scars, physique)
and signature wardrobe/lore. Seamlessly injects physical constraints and consistency rules
into prompt generation pipelines and LoRA loaders.
Supports fast load/save of .character.json presets on disk.
"""

import os
import json
import re
import glob
import logging
import torch

logger = logging.getLogger("STOIQO")

try:
    from ..core.telemetry import NodeTelemetryTimer, inject_telemetry
except (ImportError, ValueError):
    from core.telemetry import NodeTelemetryTimer, inject_telemetry


PRESETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "presets", "characters")
os.makedirs(PRESETS_DIR, exist_ok=True)


def _scan_character_presets():
    """Scans presets/characters directory for .character.json profiles."""
    presets = {}
    if os.path.isdir(PRESETS_DIR):
        for filepath in sorted(glob.glob(os.path.join(PRESETS_DIR, "*.character.json"))):
            try:
                base = os.path.basename(filepath)
                label = base.replace(".character.json", "").replace("_", " ").title()
                presets[f"💾 {label}"] = filepath
            except Exception:
                pass
    return presets


PRESETS = {
    "Custom (User Defined)": {},
    "Custom (Manual Edit)": {},
    "Cyberpunk Netrunner (Neon / Chrome / Micro-circuits)": {
        "character_name": "Aria Vance",
        "trigger_tag": "aria_vance",
        "gender_age": "young woman in her early 20s",
        "face_and_skin": "delicate oval face, pale porcelain skin, slight scar through left eyebrow, sharp cheekbones",
        "eye_color_style": "piercing electric violet eyes with luminous micro-reflections",
        "hair_style_color": "asymmetrical silver bob haircut with undercut and subtle teal highlights",
        "body_build": "athletic lean build, confident agile posture",
        "distinctive_marks": "small chrome neural port at right temple, geometric circuit tattoo on collarbone",
        "signature_outfit": "matte black techwear jacket with luminous cyan trim, tactical harness, fitted cargo pants, combat boots",
        "accessories_props": "fingerless carbon-fiber gloves, modular cyber-deck holster at hip",
        "personality_vibe": "sharp, enigmatic, analytical gaze, subtle smirk",
        "negative_constraints": "wrong eye color, missing eyebrow scar, brown hair, blonde hair, long hair, generic clothing",
    },
    "Dark Fantasy Knight (Battle-scarred / Mythic Armor)": {
        "character_name": "Kaelen the Black",
        "trigger_tag": "kaelen_knight",
        "gender_age": "rugged battle-tested man in his mid 30s",
        "face_and_skin": "weathered rugged features, stubble beard, jagged scar running across right cheek",
        "eye_color_style": "intense slate-grey eyes, piercing hawk-like stare",
        "hair_style_color": "shoulder-length raven-black hair tied back in a warrior half-knot",
        "body_build": "broad-shouldered muscular warrior physique, battle-hardened",
        "distinctive_marks": "ancient runic brand etched on left jawline, calloused scarred hands",
        "signature_outfit": "blackened damascus steel plate armor with embossed dragon motifs, fur-trimmed mantle, chainmail",
        "accessories_props": "runic longsword sheathed at back, worn leather gauntlets with silver studs",
        "personality_vibe": "stoic, commanding, brooding presence, unwavering resolve",
        "negative_constraints": "clean-shaven, baby face, missing cheek scar, blue eyes, modern clothing, thin build",
    },
    "Modern Streetwear Protagonist (Urban Chic / Casual)": {
        "character_name": "Leo Chen",
        "trigger_tag": "leo_street",
        "gender_age": "charismatic young adult in early 20s",
        "face_and_skin": "youthful expressive face, warm sun-kissed skin, dimples when smiling, clear complexion",
        "eye_color_style": "warm amber-brown eyes, lively sparkling gaze",
        "hair_style_color": "tousled wavy dark brown textured crop with caramel highlights",
        "body_build": "slender athletic build, relaxed effortless posture",
        "distinctive_marks": "subtle silver hoop earring in left ear, faint birthmark near collarbone",
        "signature_outfit": "oversized vintage distressed hoodie in washed olive, wide-leg utility skate trousers, retro chunky sneakers",
        "accessories_props": "chunky silver chain necklace, vintage camera slung over shoulder",
        "personality_vibe": "approachable, artistic, vibrant creative energy",
        "negative_constraints": "formal suit, medieval armor, shaved head, wrong eye color, pale skin",
    },
    "Anime / Manga Heroine (Vivid Eyes / Stylized Hair)": {
        "character_name": "Hikari Hoshino",
        "trigger_tag": "hikari_anime",
        "gender_age": "youthful anime heroine, 18-20 years old",
        "face_and_skin": "flawless porcelain skin, big expressive anime eyes, soft rounded chin, gentle blush",
        "eye_color_style": "large brilliant sapphire-blue eyes with sparkling starlight highlights",
        "hair_style_color": "twin-tail flowing pastel pink hair reaching waist with star-shaped hairpins",
        "body_build": "petite graceful build, cheerful dynamic pose",
        "distinctive_marks": "tiny golden heart decal below right eye",
        "signature_outfit": "sailor-inspired modern urban dress with pleated skirt and oversized ribbon, thigh-high socks",
        "accessories_props": "glowing magical crystal pendant, mechanical wrist cuff",
        "personality_vibe": "cheerful, spirited, determined hero's determination",
        "negative_constraints": "realistic wrinkled skin, brown eyes, short hair, dark gothic clothing",
    },
    "Film Noir Detective (Trenchcoat / Shadowed / Cynical)": {
        "character_name": "Vincent Cross",
        "trigger_tag": "vincent_cross",
        "gender_age": "weary middle-aged man in his late 40s",
        "face_and_skin": "lined weary face, five o'clock shadow, heavy eyelids, cigarette smoke haze",
        "eye_color_style": "tired hazel eyes, cynical perceptive gaze",
        "hair_style_color": "receding salt-and-pepper hair, slicked back under fedora brim",
        "body_build": "heavy-set tall frame, slightly slumped weary posture",
        "distinctive_marks": "crooked broken nose from past brawls, faded tattoo on forearm",
        "signature_outfit": "wrinkled beige trenchcoat over charcoal three-piece suit, loosened dark tie, fedora hat",
        "accessories_props": "brass lighter, worn leather notebook, unlit cigarette between fingers",
        "personality_vibe": "melancholic, sharp-witted, cynical, world-weary",
        "negative_constraints": "youthful face, smooth skin, smiling, bright neon colors, modern streetwear",
    },
    "Sci-Fi Starship Commander (Tactical Fleet Uniform / Hologram)": {
        "character_name": "Commander Valen Hawke",
        "trigger_tag": "valen_hawke",
        "gender_age": "distinguished commander in late 30s",
        "face_and_skin": "structured aristocratic jawline, golden-tan skin, clean sharp contours",
        "eye_color_style": "cold glacial-blue eyes, unwavering calculating gaze",
        "hair_style_color": "jet-black military undercut, neatly groomed with clean side-part",
        "body_build": "tall commanding military stature, rigid disciplined posture",
        "distinctive_marks": "subtle silver sub-dermal communication implant behind left ear",
        "signature_outfit": "crisp dark navy fleet officer uniform with gold command trim, high stiff collar, magnetic rank insignia",
        "accessories_props": "wrist-mounted holographic command interface emitting faint blue HUD",
        "personality_vibe": "authoritative, brilliant strategist, calm under extreme pressure",
        "negative_constraints": "casual clothing, messy hair, beard, slouching, civilian attire",
    },
}

PRESET_CHOICES = list(PRESETS.keys())

INJECTION_MODES = [
    "Smart Detect (Inject only when Name or Trigger is in Prompt)",
    "Always Prepend (Force Character DNA)",
    "Pass-through / Standalone Profile",
]


def _matches_token(token: str, text: str) -> bool:
    """Whole-word, case-insensitive match (avoids false positives like 'Mia' in 'Miami')."""
    if not token or not text:
        return False
    clean = token.strip()
    if not clean:
        return False
    pattern = r"(?<!\w)" + re.escape(clean) + r"(?!\w)"
    return bool(re.search(pattern, text, re.IGNORECASE))


class StoiqoCharacterMemoryNode:
    """
    [STOIQO] Character Memory Bank (Lorebook & DNA)
    Stores persistent visual DNA and wardrobe constraints for consistent multi-shot characters.
    Supports quick load/save of .character.json profiles and seamless LoRA trigger pairing.
    """

    INJECTION_MODES = INJECTION_MODES

    @classmethod
    def INPUT_TYPES(cls):
        discovered = _scan_character_presets()
        preset_choices = ["Custom (Manual Edit)"] + list(discovered.keys()) + [
            "Cyberpunk Netrunner (Neon / Chrome / Micro-circuits)",
            "Dark Fantasy Knight (Battle-scarred / Mythic Armor)",
            "Modern Streetwear Protagonist (Urban Chic / Casual)",
            "Anime / Manga Heroine (Vivid Eyes / Stylized Hair)",
            "Film Noir Detective (Trenchcoat / Shadowed / Cynical)",
            "Sci-Fi Starship Commander (Tactical Fleet Uniform / Hologram)",
            "Custom (User Defined)",
        ]
        # Deduplicate while preserving order
        unique_choices = []
        for c in preset_choices:
            if c not in unique_choices:
                unique_choices.append(c)

        return {
            "required": {
                "character_profile": (
                    unique_choices,
                    {
                        "default": unique_choices[0],
                        "tooltip": "Select a saved .character.json profile, built-in archetype, or Custom.",
                    },
                ),
                "character_name": (
                    "STRING",
                    {
                        "default": "Aria Vance",
                        "tooltip": "Character name (e.g. 'Aria Vance', 'Kaelen').",
                    },
                ),
                "trigger_tag": (
                    "STRING",
                    {
                        "default": "aria_vance",
                        "tooltip": "Trigger tag used for LoRA activation or prompt evoke token (e.g. 'aria_vance').",
                    },
                ),
                "physical_dna": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "young woman in early 20s, delicate oval face, pale porcelain skin, slight scar through left eyebrow, piercing electric violet eyes, asymmetrical silver bob haircut with undercut, athletic lean build",
                        "tooltip": "Core physical appearance (face, eyes, hair, scars, build, skin). Kept consistent across all scenes.",
                    },
                ),
                "outfit_and_gear": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "matte black techwear jacket with luminous cyan trim, tactical harness, fitted cargo pants, combat boots",
                        "tooltip": "Signature clothing, armor, and gear. Can be cleared or swapped per scene.",
                    },
                ),
                "injection_mode": (
                    cls.INJECTION_MODES,
                    {
                        "default": cls.INJECTION_MODES[0],
                        "tooltip": "Smart Detect activates only when character name or trigger tag is mentioned in the prompt.",
                    },
                ),
            },
            "optional": {
                "negative_constraints": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "wrong eye color, missing eyebrow scar, brown hair, blonde hair, long hair, generic clothing",
                        "tooltip": "Negative prompt rules to prevent visual drift.",
                    },
                ),
                "personality_vibe": (
                    "STRING",
                    {
                        "default": "sharp, enigmatic, analytical gaze, subtle smirk",
                        "tooltip": "Expressive mood, attitude, and vibe.",
                    },
                ),
                "user_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Optional prompt to inject character DNA into directly.",
                    },
                ),
                "reference_image": (
                    "IMAGE",
                    {
                        "tooltip": "Optional reference portrait or character turnaround sheet.",
                    },
                ),
                "save_profile_as": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Type a name (e.g. 'aria_stealth') to save the current profile as a .character.json on disk.",
                    },
                ),
                "custom_json_data": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Optional raw JSON string or absolute path to a .json character file.",
                    },
                ),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING", "*", "STRING", "STRING", "STRING", "IMAGE")
    RETURN_NAMES = ("full_prompt", "character_context", "character_dna", "trigger_tag", "negative_constraints", "reference_image")
    FUNCTION = "process_character"
    CATEGORY = "STOIQO"

    def process_character(
        self,
        character_name: str = "Aria Vance",
        trigger_tag: str = "aria_vance",
        character_profile: str = "Custom (Manual Edit)",
        physical_dna: str = "",
        outfit_and_gear: str = "",
        negative_constraints: str = "",
        injection_mode: str = INJECTION_MODES[0],
        personality_vibe: str = "",
        user_prompt: str = "",
        reference_image: torch.Tensor = None,
        save_profile_as: str = "",
        custom_json_data: str = "",
        unique_id: str = None,
        **kwargs,
    ):
        with NodeTelemetryTimer(node_id=unique_id, node_name="CharacterMemory") as timer:
            # ── Backward Compatibility with legacy positional/keyword parameters ──
            # Map legacy preset_profile parameter
            chosen_profile = kwargs.get("preset_profile", character_profile)

            # Check if user provided granular legacy fields
            legacy_gender = kwargs.get("gender_age", "").strip()
            legacy_face = kwargs.get("face_and_skin", "").strip()
            legacy_eyes = kwargs.get("eye_color_style", "").strip()
            legacy_hair = kwargs.get("hair_style_color", "").strip()
            legacy_body = kwargs.get("body_build", "").strip()
            legacy_marks = kwargs.get("distinctive_marks", "").strip()
            legacy_outfit = kwargs.get("signature_outfit", "").strip()
            legacy_props = kwargs.get("accessories_props", "").strip()

            # ── 1. Resolve Preset Data (from disk or memory) ──────────────────────
            loaded_data = {}

            # Strategy A: custom_json_data input (raw string or file path)
            if custom_json_data and custom_json_data.strip():
                raw = custom_json_data.strip()
                if os.path.isfile(raw):
                    try:
                        with open(raw, "r", encoding="utf-8") as jf:
                            loaded_data = json.load(jf)
                    except Exception as e:
                        logger.warning(f"[Character Memory] Error reading custom JSON file: {e}")
                else:
                    try:
                        loaded_data = json.loads(raw)
                    except Exception as e:
                        logger.warning(f"[Character Memory] Error parsing custom JSON string: {e}")

            # Strategy B: Disk profile from scanned presets
            if not loaded_data and chosen_profile and chosen_profile not in ("Custom (Manual Edit)", "Custom (User Defined)"):
                discovered = _scan_character_presets()
                if chosen_profile in discovered:
                    try:
                        with open(discovered[chosen_profile], "r", encoding="utf-8") as jf:
                            loaded_data = json.load(jf)
                    except Exception as e:
                        logger.warning(f"[Character Memory] Error reading preset '{chosen_profile}': {e}")
                elif chosen_profile in PRESETS:
                    loaded_data = PRESETS[chosen_profile]

            # ── 2. Overlay loaded data if present ─────────────────────────────────
            if loaded_data:
                # If physical_dna was not explicitly filled, extract from loaded data
                if not physical_dna.strip():
                    if "physical_dna" in loaded_data and loaded_data["physical_dna"]:
                        physical_dna = loaded_data["physical_dna"]
                    else:
                        # Compile from granular preset fields
                        parts = []
                        for k in ["gender_age", "face_and_skin", "eye_color_style", "hair_style_color", "body_build"]:
                            val = loaded_data.get(k, "")
                            if val:
                                parts.append(val)
                        if loaded_data.get("distinctive_marks"):
                            parts.append(f"distinctive marks: {loaded_data['distinctive_marks']}")
                        physical_dna = ", ".join(parts)

                if not outfit_and_gear.strip():
                    if "outfit_and_gear" in loaded_data and loaded_data["outfit_and_gear"]:
                        outfit_and_gear = loaded_data["outfit_and_gear"]
                    else:
                        outfit_parts = []
                        if loaded_data.get("signature_outfit"):
                            outfit_parts.append(loaded_data["signature_outfit"])
                        if loaded_data.get("accessories_props"):
                            outfit_parts.append(loaded_data["accessories_props"])
                        outfit_and_gear = ", ".join(outfit_parts)

                if not negative_constraints.strip() and loaded_data.get("negative_constraints"):
                    negative_constraints = loaded_data["negative_constraints"]
                if not personality_vibe.strip() and loaded_data.get("personality_vibe"):
                    personality_vibe = loaded_data["personality_vibe"]

                # Only override name/trigger if default or blank
                if (not character_name.strip() or character_name == "Aria Vance") and loaded_data.get("character_name"):
                    character_name = loaded_data["character_name"]
                if (not trigger_tag.strip() or trigger_tag == "aria_vance") and loaded_data.get("trigger_tag"):
                    trigger_tag = loaded_data["trigger_tag"]

            # ── 3. Compile Legacy Granular Overrides if passed ────────────────────
            if any([legacy_gender, legacy_face, legacy_eyes, legacy_hair, legacy_body, legacy_marks]):
                legacy_parts = []
                if legacy_gender: legacy_parts.append(legacy_gender)
                if legacy_face: legacy_parts.append(legacy_face)
                if legacy_eyes: legacy_parts.append(legacy_eyes)
                if legacy_hair: legacy_parts.append(legacy_hair)
                if legacy_body: legacy_parts.append(legacy_body)
                if legacy_marks: legacy_parts.append(f"distinctive marks: {legacy_marks}")
                compiled_legacy_dna = ", ".join(legacy_parts)
                if not physical_dna.strip() or physical_dna == StoiqoCharacterMemoryNode.INPUT_TYPES()["required"]["physical_dna"][1]["default"]:
                    physical_dna = compiled_legacy_dna

            if legacy_outfit or legacy_props:
                compiled_outfit = ", ".join([p for p in [legacy_outfit, legacy_props] if p])
                if not outfit_and_gear.strip() or outfit_and_gear == StoiqoCharacterMemoryNode.INPUT_TYPES()["required"]["outfit_and_gear"][1]["default"]:
                    outfit_and_gear = compiled_outfit

            # ── 4. Save Profile to Disk if Requested ──────────────────────────────
            if save_profile_as and save_profile_as.strip():
                clean_filename = re.sub(r"[<>:\"/\\|?*]", "_", save_profile_as.strip())
                if not clean_filename.endswith(".character.json"):
                    clean_filename = f"{clean_filename}.character.json"
                save_path = os.path.join(PRESETS_DIR, clean_filename)
                save_payload = {
                    "character_name": character_name.strip(),
                    "trigger_tag": trigger_tag.strip(),
                    "physical_dna": physical_dna.strip(),
                    "outfit_and_gear": outfit_and_gear.strip(),
                    "negative_constraints": negative_constraints.strip(),
                    "personality_vibe": personality_vibe.strip(),
                }
                try:
                    with open(save_path, "w", encoding="utf-8") as out_f:
                        json.dump(save_payload, out_f, indent=2, ensure_ascii=False)
                    logger.info(f"[Character Memory] Saved profile to '{save_path}'")
                except Exception as e:
                    logger.warning(f"[Character Memory] Error saving profile: {e}")

            # ── 5. Build Structured Profile Lines ─────────────────────────────────
            character_dna = physical_dna.strip()
            profile_lines = []
            if character_name.strip():
                name_line = f"Character: {character_name.strip()}"
                if trigger_tag.strip():
                    name_line += f" [{trigger_tag.strip()}]"
                profile_lines.append(name_line)

            if character_dna:
                profile_lines.append(f"Visual DNA: {character_dna}")
            if outfit_and_gear.strip():
                profile_lines.append(f"Wardrobe & Gear: {outfit_and_gear.strip()}")
            if personality_vibe.strip():
                profile_lines.append(f"Attitude/Vibe: {personality_vibe.strip()}")

            full_profile = "\n".join(profile_lines)

            # ── 6. Context Object for Downstream Synthesizer & Modular Nodes ───────
            character_context = {
                "character_name": character_name.strip(),
                "trigger_tag": trigger_tag.strip(),
                "preset_profile": chosen_profile,
                "character_profile": chosen_profile,
                "character_dna": character_dna,
                "physical_dna": character_dna,
                "signature_outfit": outfit_and_gear.strip(),
                "outfit_and_gear": outfit_and_gear.strip(),
                "accessories_props": "",
                "personality_vibe": personality_vibe.strip(),
                "negative_constraints": negative_constraints.strip(),
                "injection_mode": injection_mode,
                "full_profile": full_profile,
            }

            # ── 7. Smart Detection & Prompt Injection ─────────────────────────────
            prompt_input = user_prompt.strip()
            should_inject = False

            if injection_mode == "Always Prepend (Force Character DNA)":
                should_inject = True
            elif "Smart Detect" in injection_mode:
                if not prompt_input:
                    should_inject = True
                else:
                    # Check character name tokens and trigger tag with word-boundary safety
                    name_tokens = [t.strip() for t in character_name.split() if len(t.strip()) > 1]
                    name_tokens.append(character_name.strip())
                    if trigger_tag.strip():
                        name_tokens.append(trigger_tag.strip())

                    for tok in name_tokens:
                        if _matches_token(tok, prompt_input):
                            should_inject = True
                            break
            else:
                # Pass-through / Standalone Profile
                should_inject = False

            if should_inject:
                char_id = character_name.strip()
                if trigger_tag.strip() and trigger_tag.strip().lower() != character_name.strip().lower():
                    char_id = f"{char_id} [{trigger_tag.strip()}]"

                injection_block = f"[{char_id} | {character_dna}"
                if outfit_and_gear.strip():
                    injection_block += f", wearing {outfit_and_gear.strip()}"
                if personality_vibe.strip():
                    injection_block += f", {personality_vibe.strip()}"
                injection_block += "]"

                if prompt_input:
                    full_prompt = f"{injection_block}, {prompt_input}"
                else:
                    full_prompt = f"{injection_block}, cinematic lighting, high-end photography, 8k resolution"
            else:
                full_prompt = prompt_input if prompt_input else character_dna

            # Fallback mock tensor if reference_image is None
            out_image = reference_image if reference_image is not None else torch.zeros((1, 64, 64, 3), dtype=torch.float32)

            logger.info(f"[Character Memory] Processed profile '{character_name}' (Mode: {injection_mode}, Injected: {should_inject})")

            return inject_telemetry(
                (
                    full_prompt,
                    character_context,
                    character_dna,
                    trigger_tag.strip(),
                    negative_constraints.strip(),
                    out_image,
                ),
                timer.get_stats(),
            )
