"""
[STOIQO] Character Memory Bank & Visual Lorebook Node
Persistent character identity module that stores visual DNA (face, eyes, hair, scars, physique)
and signature wardrobe/lore. Seamlessly injects physical constraints and consistency rules
into prompt generation pipelines to ensure 100% character coherence across batches.
"""

import json
import torch

try:
    from ..core.telemetry import NodeTelemetryTimer, inject_telemetry
except (ImportError, ValueError):
    from core.telemetry import NodeTelemetryTimer, inject_telemetry


PRESETS = {
    "Custom (User Defined)": {},
    "Cyberpunk Netrunner (Neon / Chrome / Micro-circuits)": {
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


class StoiqoCharacterMemoryNode:
    """
    [STOIQO] Character Memory Bank (Lorebook & DNA)
    Stores persistent visual DNA and wardrobe constraints for consistent multi-shot characters.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character_name": (
                    "STRING",
                    {
                        "default": "Aria Vance",
                        "tooltip": "Character name or unique identifier (e.g. 'Aria Vance', 'Kaelen').",
                    },
                ),
                "trigger_tag": (
                    "STRING",
                    {
                        "default": "aria_vance",
                        "tooltip": "Trigger tag used for LoRA activation or prompt evoke token.",
                    },
                ),
                "preset_profile": (
                    PRESET_CHOICES,
                    {
                        "default": PRESET_CHOICES[0],
                        "tooltip": "Preconfigured character archetype or Custom.",
                    },
                ),
                "gender_age": (
                    "STRING",
                    {
                        "default": "young woman in her early 20s",
                        "tooltip": "Gender, age, and core demographics.",
                    },
                ),
                "face_and_skin": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "delicate oval face, pale porcelain skin, slight scar through left eyebrow, sharp cheekbones",
                        "tooltip": "Facial structure, skin tone, scars, and facial features.",
                    },
                ),
                "eye_color_style": (
                    "STRING",
                    {
                        "default": "piercing electric violet eyes with luminous micro-reflections",
                        "tooltip": "Eye color, pupil details, and gaze intensity.",
                    },
                ),
                "hair_style_color": (
                    "STRING",
                    {
                        "default": "asymmetrical silver bob haircut with undercut and subtle teal highlights",
                        "tooltip": "Hairstyle, hair length, and hair color.",
                    },
                ),
                "body_build": (
                    "STRING",
                    {
                        "default": "athletic lean build, confident agile posture",
                        "tooltip": "Body physique, height, and posture.",
                    },
                ),
                "distinctive_marks": (
                    "STRING",
                    {
                        "default": "small chrome neural port at right temple, geometric circuit tattoo on collarbone",
                        "tooltip": "Scars, tattoos, cyberware, birthmarks, or unique visual anchors.",
                    },
                ),
            },
            "optional": {
                "signature_outfit": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "matte black techwear jacket with luminous cyan trim, tactical harness, fitted cargo pants, combat boots",
                        "tooltip": "Signature outfit and clothing constraints.",
                    },
                ),
                "accessories_props": (
                    "STRING",
                    {
                        "default": "fingerless carbon-fiber gloves, modular cyber-deck holster at hip",
                        "tooltip": "Iconic accessories, jewelry, gear, or props.",
                    },
                ),
                "personality_vibe": (
                    "STRING",
                    {
                        "default": "sharp, enigmatic, analytical gaze, subtle smirk",
                        "tooltip": "Expressive mood, attitude, and vibe.",
                    },
                ),
                "negative_constraints": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "wrong eye color, missing eyebrow scar, brown hair, blonde hair, long hair, generic clothing",
                        "tooltip": "Negative prompt rules to prevent visual drift.",
                    },
                ),
                "injection_mode": (
                    INJECTION_MODES,
                    {
                        "default": INJECTION_MODES[0],
                        "tooltip": "Smart Detect activates only when character name/trigger is mentioned in the prompt.",
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
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING", "STOIQO_CHARACTER", "STRING", "STRING", "STRING", "IMAGE")
    RETURN_NAMES = ("full_prompt", "character_context", "character_dna", "trigger_tag", "negative_constraints", "reference_image")
    FUNCTION = "process_character"
    CATEGORY = "STOIQO"

    def process_character(
        self,
        character_name: str,
        trigger_tag: str,
        preset_profile: str,
        gender_age: str,
        face_and_skin: str,
        eye_color_style: str,
        hair_style_color: str,
        body_build: str,
        distinctive_marks: str,
        signature_outfit: str = "",
        accessories_props: str = "",
        personality_vibe: str = "",
        negative_constraints: str = "",
        injection_mode: str = INJECTION_MODES[0],
        user_prompt: str = "",
        reference_image: torch.Tensor = None,
        unique_id: str = None,
    ):
        with NodeTelemetryTimer(node_id=unique_id, node_name="CharacterMemory") as timer:
            # 1. Overlay preset if user selected a non-custom preset and left fields blank
            preset_data = PRESETS.get(preset_profile, {})
            if preset_data and preset_profile != "Custom (User Defined)":
                if not gender_age.strip():
                    gender_age = preset_data.get("gender_age", gender_age)
                if not face_and_skin.strip():
                    face_and_skin = preset_data.get("face_and_skin", face_and_skin)
                if not eye_color_style.strip():
                    eye_color_style = preset_data.get("eye_color_style", eye_color_style)
                if not hair_style_color.strip():
                    hair_style_color = preset_data.get("hair_style_color", hair_style_color)
                if not body_build.strip():
                    body_build = preset_data.get("body_build", body_build)
                if not distinctive_marks.strip():
                    distinctive_marks = preset_data.get("distinctive_marks", distinctive_marks)
                if not signature_outfit.strip():
                    signature_outfit = preset_data.get("signature_outfit", signature_outfit)
                if not accessories_props.strip():
                    accessories_props = preset_data.get("accessories_props", accessories_props)
                if not personality_vibe.strip():
                    personality_vibe = preset_data.get("personality_vibe", personality_vibe)
                if not negative_constraints.strip():
                    negative_constraints = preset_data.get("negative_constraints", negative_constraints)

            # 2. Compile Physical DNA (pure bodily features)
            dna_parts = []
            if gender_age.strip():
                dna_parts.append(gender_age.strip())
            if face_and_skin.strip():
                dna_parts.append(face_and_skin.strip())
            if eye_color_style.strip():
                dna_parts.append(eye_color_style.strip())
            if hair_style_color.strip():
                dna_parts.append(hair_style_color.strip())
            if body_build.strip():
                dna_parts.append(body_build.strip())
            if distinctive_marks.strip():
                dna_parts.append(f"distinctive marks: {distinctive_marks.strip()}")

            character_dna = ", ".join(dna_parts)

            # 3. Compile Full Lorebook Profile
            profile_lines = []
            if character_name.strip():
                name_line = f"Character: {character_name.strip()}"
                if trigger_tag.strip():
                    name_line += f" [{trigger_tag.strip()}]"
                profile_lines.append(name_line)

            if character_dna:
                profile_lines.append(f"Visual DNA: {character_dna}")
            if signature_outfit.strip():
                profile_lines.append(f"Signature Wardrobe: {signature_outfit.strip()}")
            if accessories_props.strip():
                profile_lines.append(f"Gear & Props: {accessories_props.strip()}")
            if personality_vibe.strip():
                profile_lines.append(f"Attitude/Vibe: {personality_vibe.strip()}")

            full_profile = "\n".join(profile_lines)

            # 4. Context Object for Downstream Synthesizer & Modular Nodes
            character_context = {
                "character_name": character_name.strip(),
                "trigger_tag": trigger_tag.strip(),
                "preset_profile": preset_profile,
                "character_dna": character_dna,
                "signature_outfit": signature_outfit.strip(),
                "accessories_props": accessories_props.strip(),
                "personality_vibe": personality_vibe.strip(),
                "negative_constraints": negative_constraints.strip(),
                "injection_mode": injection_mode,
                "full_profile": full_profile,
            }

            # 5. Smart Injection into user_prompt
            prompt_input = user_prompt.strip()
            should_inject = False

            if injection_mode == "Always Prepend (Force Character DNA)":
                should_inject = True
            elif injection_mode == "Smart Detect (Inject only when Name or Trigger is in Prompt)":
                if not prompt_input:
                    # If prompt is empty, inject character profile by default
                    should_inject = True
                else:
                    c_name_lower = character_name.lower().strip()
                    c_tag_lower = trigger_tag.lower().strip()
                    p_lower = prompt_input.lower()
                    if (c_name_lower and c_name_lower in p_lower) or (c_tag_lower and c_tag_lower in p_lower):
                        should_inject = True
            else:
                # Pass-through / Standalone Profile
                should_inject = False

            if should_inject:
                char_id = character_name.strip()
                if trigger_tag.strip() and trigger_tag.strip().lower() != character_name.strip().lower():
                    char_id = f"{char_id} [{trigger_tag.strip()}]"

                injection_block = f"[{char_id} | {character_dna}"
                if signature_outfit.strip():
                    injection_block += f", wearing {signature_outfit.strip()}"
                if accessories_props.strip():
                    injection_block += f", with {accessories_props.strip()}"
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

            print(f"[STOIQO] Character Memory Bank: Processed profile '{character_name}' (Mode: {injection_mode}, Injected: {should_inject})")

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
