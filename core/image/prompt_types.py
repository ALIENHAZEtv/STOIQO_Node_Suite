"""
[STOIQO] Prompt Generator Engine — Layer 2: Prompt Types & Structural Formats
Defines the structural shape and syntax of generated prompts (Narrative, Categories, Short, Tags, etc.).
"""

# ── LAYER 2: PROMPT TYPES / FORMATS (STRUCTURAL SHAPE) ─────────────────────
PROMPT_TYPES = [
    "Structured Categories",
    "Detailed Narrative",
    "Short Summary",
    "Tags & Keywords",
    "Booru Tags (Danbooru)",
    "Cinematic & Video Script",
]

PROMPT_TYPE_DIRECTIVES = {
    "Structured Categories": (
        "STRUCTURAL FORMAT (Apply to <PROMPT> only): Structured Categories.\n"
        "Deconstruct the visual input into clean, standardized categorical key-value lines without introductory text or bullet points. "
        "Adapt seamlessly whether the scene contains a single person, multiple subjects, complex crowds, or pure landscapes/architecture:\n"
        "Subject(s) & Focal Entity: [If people/beings: enumerate entities, gender/age, physical anatomy, facial features, and relative canvas positions (left/center/right). If landscape/still-life/architecture: state 'None (Landscape/Still-Life/Architecture) - Primary focal anchor: [describe dominant natural or structural monument]']\n"
        "Action, Dynamics & Gaze: [If beings: exact body posture, gesture mechanics, gaze vector, and interpersonal interactions. If landscape/still-life: physical nature dynamics (crashing waves, drifting cloud velocity, swaying trees, or absolute glass-like stillness)]\n"
        "Attire & Gear: [If characters: detailed breakdown of garments, footwear, wearable gear, weapons, or accessories. If pure landscape/objects: state 'None (Natural Scene)' or catalog man-made decorative props present in the scene]\n"
        "Tactile Textures & Materials: [Micro-surface materiality: skin pores, fabric weaves, weathered stone, rusted iron, polished lacquer, mossy bark, wet slick asphalt, reflective puddles]\n"
        "Spatial Staging & Planes: [Explicit depth breakdown: Foreground elements (close to lens) -> Midground action stage -> Distant Background horizon and sky]\n"
        "Environment & Atmospheric Setting: [Indoor/outdoor world context, architectural era/style, biome, and atmospheric weather (volumetric fog, rainfall, God rays, dust motes, haze, humidity)]\n"
        "Lighting Physics & Shadows: [Key light direction and source, fill light ratio, rim/backlight separation, shadow hardness/softness, specular reflections, and ambient occlusion]\n"
        "Color Science & Palette: [Dominant color harmony, color temperature (warm Kelvin golden hues vs cool cyan/blue), saturation levels, chromatic contrast, and film grading tone]\n"
        "Camera Optics & Framing: [Shot scale (e.g., Extreme Close-up, Medium Close-up, Wide Vista), lens focal length (e.g., 24mm wide, 50mm natural, 85mm portrait), elevation angle (eye-level, low-angle, aerial drone), and depth of field (bokeh blur vs deep focus)]\n"
        "OUTPUT SYNTAX: Output strictly each category name followed by colon and detailed description on its own line."
    ),
    "Detailed Narrative": (
        "STRUCTURAL FORMAT (Apply to <PROMPT> only): Detailed Narrative.\n"
        "Compose a single, continuous, highly immersive descriptive prose paragraph for the <PROMPT> block, written in dense, vivid natural English without line breaks or bullet points. Allow the description to expand freely in depth and richness as required to fully realize the scene:\n"
        "- SYNTACTIC ARCHITECTURE & FLOW: Open immediately with the primary visual anchor and shot perspective, then expand smoothly in a single cohesive narrative arc:\n"
        "[Focal Subject & Spatial Staging] -> [Kinematics, Pose & Gaze / Natural Dynamics] -> [Garments, Wearable Props & Micro-Textures] -> [Lighting Interaction, Specularity & Shadows] -> [Atmosphere, Depth Planes & Optical Characteristics].\n"
        "- ADAPTIVE LOGIC:\n"
        "• If characters/creatures are present: Detail facial anatomy, gaze direction, exact physical posture, fabric folds, and anatomical interaction with the surrounding environment.\n"
        "• If landscape/architecture/still-life: Open with the monumental focal element, spatial topography, materials (weathered stone, water bodies, foliage), and receding depth planes into the horizon.\n"
        "- CORE PRINCIPLES:\n"
        "• PHYSICALIZE ALL MOODS: Never use abstract emotional adjectives ('mysterious', 'epic'). Translate every mood into concrete optical reality, shadow depth, color temperature, and atmospheric conditions.\n"
        "• PRECISE SPATIAL ANCHORS: Bind every color, texture, and prop strictly to its specific noun using spatial prepositions to eliminate color bleeding across scene elements.\n"
        "• LIGHT-TO-SURFACE PHYSICS: Explicitly describe how the light source interacts with distinct materials (subsurface scattering, matte absorption, specular sheen, wet reflections).\n"
        "• DIRECT DESCRIPTIVE PURITY: Start directly with the scene content. Never use meta-framing phrases like 'In this image', 'We see', 'A photograph of', or empty buzzwords."
    ),
    "Short Summary": (
        "STRUCTURAL FORMAT (Apply to <PROMPT> only): Short Summary.\n"
        "Compose a high-impact, telegraphic 1-to-2 sentence prompt (strictly bounded under 25 to 30 words) for the <PROMPT> block, engineered for maximum semantic density and diffusion clarity.\n"
        "- THE ESSENTIAL QUADRILATERAL (Syntactic Sequence):\n"
        "[Focal Entity & Signature Trait] -> [Active Physical Kinematics / Posture] -> [Concrete Environment / Grounding] -> [Dominant Light Vector & Mood].\n"
        "- ADAPTIVE FORMULA:\n"
        "• If characters/creatures: Anchor identity and single defining garment/feature, immediate physical action or gaze, direct environment, and primary directional light.\n"
        "• If landscape/architecture/still-life: Anchor the monumental natural or structural centerpiece, dynamic environmental conditions, depth plane, and solar/ambient illumination.\n"
        "- CORE PRINCIPLES:\n"
        "• POWERFUL NOUNS & ACTIVE VERBS: Replace strings of weak adjectives with dense, visually charged nouns and kinetic verbs. Strip all transitional padding ('there is', 'standing peacefully').\n"
        "• STRICT CONCISENESS: Every single word must contribute directly to the generated pixels. Strictly 1 to 2 sentences, never exceeding 30 words."
    ),
    "Tags & Keywords": (
        "STRUCTURAL FORMAT (Apply to <PROMPT> only): Tags & Keywords.\n"
        "Format the <PROMPT> block strictly as a dense, comprehensive, comma-separated sequence of natural English descriptive keywords and short compound phrases.\n"
        "- HIERARCHICAL TOKEN SEQUENCE:\n"
        "[Core Subject & Entity Count] -> [Distinctive Anatomical / Physical Traits] -> [Specific Garments & Wearable Props] -> [Kinematics, Pose & Gaze] -> [Environment Staging & Depth Elements] -> [Lighting Physics, Reflections & Atmosphere] -> [Camera Optics & Lens Specifications].\n"
        "- ADAPTIVE BEHAVIOR:\n"
        "• With characters/beings: Prioritize subject count, facial features, hair, atomic garment phrases (e.g., 'black leather moto jacket', 'white cotton tank top'), pose ('leaning against wall'), gaze ('looking at viewer'), setting, lighting, and camera.\n"
        "• With landscapes/architecture: Prioritize primary monument/topography (e.g., 'ancient stone castle ruins'), foreground elements, background sky/horizon, weather/time ('golden hour', 'overcast drizzle'), ambient light, and wide lens ('24mm lens', 'deep focus').\n"
        "- CORE PRINCIPLES:\n"
        "• ATOMIC COMPOUND PHRASES: Always bind colors and materials directly to their respective nouns (e.g., 'worn brown leather boots' instead of 'worn, brown, leather, boots') to completely eliminate color bleeding.\n"
        "• TELEGRAPHIC GRAMMAR: Use active participles and nouns. Never use conjugated verbs or filler ('sitting' instead of 'is sitting'; 'wet asphalt' instead of 'there is wet asphalt').\n"
        "• SYNTAX DISCIPLINE: Separate every entry strictly with a comma and space. No periods, no line breaks, no bullet points, and no underscores."
    ),
    "Booru Tags (Danbooru)": (
        "STRUCTURAL FORMAT (Apply to <PROMPT> only): Booru Tags (Danbooru).\n"
        "Format the <PROMPT> block strictly using authentic Danbooru / Booru taxonomy optimized for anime, illustration, and Booru-trained diffusion models (Pony, Animagine, NAI).\n"
        "- CANONICAL TAG HIERARCHY:\n"
        "[Entity Count & Solo status] -> [Facial Features, Eyes & Hair specs] -> [Complete Outfit, Garments & Accessories] -> [Action, Pose, Expression & Gaze] -> [Shot Framing & Camera Angle] -> [Environment, Setting & Props] -> [Atmosphere & Visual FX].\n"
        "- ADAPTIVE TAXONOMY:\n"
        "• With characters: Start with count ('1girl, solo', '1boy, solo', '2girls'). Then hair/eyes ('blue_hair, twintails, green_eyes'), expression ('smile, parted_lips'), garments ('white_shirt, pleated_skirt, thighhighs'), pose ('sitting, arms_behind_back'), gaze ('looking_at_viewer'), framing ('upper_body', 'cowboy_shot', 'dutch_angle'), setting ('classroom, sunlight, indoors').\n"
        "• Without humans (Landscape/Scenery): Must open with 'no_humans, scenery'. Follow with setting ('outdoors', 'cityscape', 'ruins'), nature/sky ('cloudy_sky, sunset, cherry_blossoms'), and optics ('depth_of_field, wide_shot').\n"
        "- SYNTAX DISCIPLINE:\n"
        "• STRICT LOWERCASE & UNDERSCORES: All tags must be strictly lowercase. Multi-word concepts must be joined by underscores (e.g., 'school_uniform', 'wind_blown_hair').\n"
        "• ZERO NATURAL LANGUAGE: Never include articles ('a', 'the'), prepositions ('in', 'on'), conjugated verbs ('is standing'), punctuation marks (except tag commas), or conversational words."
    ),
    "Cinematic & Video Script": (
        "STRUCTURAL FORMAT (Apply to <PROMPT> only): Cinematic & Video Script.\n"
        "Format the <PROMPT> block as a professional Director of Photography (DP) shot specification, engineered for cinematic stills and temporal video generation models (Wan 2.1, Kling, CogVideoX, SVD, HunyuanVideo).\n"
        "- SHOT SPECIFICATION SEQUENCE:\n"
        "[Camera Rig & Optical Setup] -> [Subject Blocking & Physical Kinematics] -> [Dynamic Camera Trajectory] -> [Three-Point Cinematic Lighting & Color Grade] -> [Atmospheric Dynamics & Particle Physics].\n"
        "- ADAPTIVE FORMULA:\n"
        "• With characters/vehicles: Define lens and angle ('Low-angle medium close-up, 50mm anamorphic lens'), exact actor trajectory and velocity ('walking determinedly forward toward camera while turning collar up'), camera motion ('slow stabilized dolly-in keeping subject in sharp focus'), lighting ('dramatic key light with strong cyan rim lighting'), and temporal effects ('wind turbulence rustling heavy wool coat, rain streaks catching backlight').\n"
        "• With landscape/environment: Define panoramic staging ('Wide establishing aerial shot, 24mm cinema prime'), natural dynamics ('roaring ocean waves crashing against jagged sea cliffs, low cloud velocity drifting right-to-left'), camera vector ('slow forward tracking drone push descending toward the shoreline'), and solar lighting ('warm low-angle sunset raking across the water with anamorphic horizontal lens flare').\n"
        "- CORE PRINCIPLES:\n"
        "• ACTIVE KINEMATICS OVER STATIC ADJECTIVES: Never use passive descriptions ('he is standing'). Use active physical motion vectors ('paces forward', 'glances abruptly off-frame', 'surges').\n"
        "• AUTHENTIC CINEMA TERMINOLOGY: Use real camera movements (dolly, tracking pan, crane pedestal, tilt) and lighting setups (chiaroscuro, rim light, volumetric haze) to give the diffusion/video model explicit temporal direction."
    ),
}

LEGACY_PROMPT_TYPE_ALIASES = {
    "Detailed Narrative (Long)": "Detailed Narrative",
    "Short Summary (Concise)": "Short Summary",
    "Custom Directives Only": "Structured Categories",
    "Dual Prompt (CLIP-L + T5-XXL)": "Detailed Narrative",
    "Negative Prompt & Flaw List": "Detailed Narrative",
    "Visual Differences Comparison": "Detailed Narrative",
    "Cinematic Shot Script": "Cinematic & Video Script",
}


def resolve_prompt_type(prompt_type):
    """Resolves legacy prompt types to active standardized prompt types."""
    return LEGACY_PROMPT_TYPE_ALIASES.get(prompt_type, prompt_type)


# Backward-compatibility aliases
CAPTION_STYLES = PROMPT_TYPES
STYLE_PROMPTS = PROMPT_TYPE_DIRECTIVES
