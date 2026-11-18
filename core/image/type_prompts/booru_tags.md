---
name: "Booru Tags (Danbooru)"
aliases:
  - "Danbooru"
  - "Booru"
order: 5
---
STRUCTURAL FORMAT (Apply to <PROMPT> only): Booru Tags (Danbooru).
Format the <PROMPT> block strictly using authentic Danbooru / Booru taxonomy optimized for anime, illustration, and Booru-trained diffusion models (Pony, Animagine, NAI).
- CANONICAL TAG HIERARCHY:
[Entity Count & Solo status] -> [Facial Features, Eyes & Hair specs] -> [Complete Outfit, Garments & Accessories] -> [Action, Pose, Expression & Gaze] -> [Shot Framing & Camera Angle] -> [Environment, Setting & Props] -> [Atmosphere & Visual FX].
- ADAPTIVE TAXONOMY:
• With characters: Start with count ('1girl, solo', '1boy, solo', '2girls'). Then hair/eyes ('blue_hair, twintails, green_eyes'), expression ('smile, parted_lips'), garments ('white_shirt, pleated_skirt, thighhighs'), pose ('sitting, arms_behind_back'), gaze ('looking_at_viewer'), framing ('upper_body', 'cowboy_shot', 'dutch_angle'), setting ('classroom, sunlight, indoors').
• Without humans (Landscape/Scenery): Must open with 'no_humans, scenery'. Follow with setting ('outdoors', 'cityscape', 'ruins'), nature/sky ('cloudy_sky, sunset, cherry_blossoms'), and optics ('depth_of_field, wide_shot').
- SYNTAX DISCIPLINE:
• STRICT LOWERCASE & UNDERSCORES: All tags must be strictly lowercase. Multi-word concepts must be joined by underscores (e.g., 'school_uniform', 'wind_blown_hair').
• ZERO NATURAL LANGUAGE: Never include articles ('a', 'the'), prepositions ('in', 'on'), conjugated verbs ('is standing'), punctuation marks (except tag commas), or conversational words.
