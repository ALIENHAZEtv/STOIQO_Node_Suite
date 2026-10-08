"""
[STOIQO] Prompt Generator Engine — Layer 3: Artistic Styles (Visual Aesthetics)
Defines authentic visual aesthetics and style directives (Photorealistic, Anime, CGI, etc.).
"""

# ── LAYER 3: ARTISTIC STYLES (GENUINE VISUAL AESTHETICS) ───────────────────
# ── LAYER 3: ARTISTIC STYLES (GENUINE VISUAL AESTHETICS & MEDIUMS) ─────────
ARTISTIC_STYLES = [
    # 0. Neutral / Auto
    "Auto-Detect / Preserve Original",
    # 1-4. Photographic Family
    "Photorealistic (Modern Digital RAW)",
    "Analog Film (35mm Vintage Stock)",
    "Cinematic Still (Anamorphic Movie)",
    "Studio Portrait & Editorial Fashion",
    # 5-7. Cartoon, 2D & Drawing Family
    "Anime & Manga (2D Cel-shaded)",
    "Comic Book & Graphic Novel (Ink & Halftone)",
    "Pencil Sketch & Charcoal Drawing",
    # 8-10. 3D, Digital Concept & Fine Art Family
    "3D Digital Render & CGI (PBR)",
    "Digital Concept Art & Illustration",
    "Oil Painting & Classical Fine Art",
]

ARTISTIC_STYLE_DIRECTIVES = {
    "Auto-Detect / Preserve Original": "",

    # ── PHOTOGRAPHIC FAMILY ──────────────────────────────────────────────
    "Photorealistic (Modern Digital RAW)": (
        "AESTHETIC INJECTION (Apply to <PROMPT> only): Modern High-End Digital Photorealism.\n"
        "Infuse tangible physical authenticity captured on a contemporary 100MP digital sensor without outputting directive labels or bullet points:\n"
        "- OPTICALS: Integrate natural prime lens characteristics (50mm/85mm f/1.4), crisp natural focus falloff, subtle depth of field, and zero synthetic over-sharpening.\n"
        "- SURFACE PHYSICS: Ground human subjects with authentic epidermal micro-textures, delicate skin pores, natural subsurface scattering, and realistic corneal catchlights.\n"
        "- LIGHTING & SHADOWS: Maintain balanced environmental dynamic range with unclipped specular highlights and clean, noise-free shadow details.\n"
        "- LAYER 2 ADAPTATION: If narrative, describe these traits as fluid physical prose; if categories, populate Tactile Textures, Lighting, and Camera; if tags, append 'photorealistic, 35mm photo, detailed skin, soft focus'."
    ),

    "Analog Film (35mm Vintage Stock)": (
        "AESTHETIC INJECTION (Apply to <PROMPT> only): Authentic 35mm Vintage Analog Film.\n"
        "Infuse the genuine photochemical aesthetics of classic film stocks (Kodak Portra 400 or Fuji Provia) without outputting directive labels or bullet points:\n"
        "- EMULSION & TEXTURE: Embed organic silver halide film grain, gentle highlight halation glow, slightly lifted warm blacks, and nostalgic color grading.\n"
        "- OPTICAL IMPERFECTIONS: Subtle chromatic fringe at frame edges, gentle lens vignetting, and natural optical soft roll-off in bright areas.\n"
        "- LAYER 2 ADAPTATION: If narrative, integrate tactile film textures seamlessly; if categories, enrich Textures and Optics; if tags, append '35mm film photograph, Kodak Portra aesthetic, organic film grain, halation'."
    ),

    "Cinematic Still (Anamorphic Movie)": (
        "AESTHETIC INJECTION (Apply to <PROMPT> only): High-Budget Theatrical Movie Still.\n"
        "Infuse the production staging of cinema cameras (Arri Alexa LF, Panavision anamorphic lenses) without outputting directive labels or bullet points:\n"
        "- OPTICALS & FRAMING: Anamorphic widescreen 2.39:1 framing, oval bokeh balls, subtle horizontal streak lens flare, and dramatic shallow focal plane.\n"
        "- PRODUCTION LIGHTING: Sculpted cinematic three-point lighting (motivated key, diffused fill, crisp rim/kicker edge) with volumetric haze or atmosphere catching the beams.\n"
        "- COLOR SCIENCE: Cohesive narrative film color grade (teal-amber contrast, bleach bypass, or rich chiaroscuro drama).\n"
        "- LAYER 2 ADAPTATION: If narrative, weave cinematic lighting and framing into the flow; if categories, populate Lighting and Camera Optics; if tags, append 'cinematic film still, anamorphic lens, 35mm movie, rim lighting, atmospheric haze'."
    ),

    "Studio Portrait & Editorial Fashion": (
        "AESTHETIC INJECTION (Apply to <PROMPT> only): High-Fashion Editorial Studio Photography.\n"
        "Infuse the lighting and styling of luxury magazine covers (Vogue, Vanity Fair) without outputting directive labels or bullet points:\n"
        "- STUDIO LIGHT RIG: Professional flash setup using large octabox softboxes, beauty dishes with honeycomb grids, and sculpted catchlights in the eyes.\n"
        "- EDITORIAL STYLING: High-definition tailoring, clean garment draping, couture styling, and flawless studio skin texture.\n"
        "- STAGING: Seamless studio cyclorama backdrop, neutral muslin, or clean architectural studio staging with elegant negative space.\n"
        "- LAYER 2 ADAPTATION: If narrative, describe studio lighting geometry directly; if categories, enrich Lighting Physics and Attire; if tags, append 'editorial photography, studio lighting, beauty dish catchlight, cyclorama backdrop'."
    ),

    # ── CARTOON, 2D & DRAWING FAMILY ─────────────────────────────────────
    "Anime & Manga (2D Cel-shaded)": (
        "AESTHETIC INJECTION (Apply to <PROMPT> only): High-Budget Modern Japanese Anime & Manga.\n"
        "Infuse the distinctive 2D visual craft of premier animation studios (Ufotable, Kyoto Animation) without outputting directive labels or bullet points:\n"
        "- LINEART & COLORING: Razor-sharp clean dynamic lineart, multi-toned cel-shading with geometric shadow lines, and soft digital gradient glows.\n"
        "- EYES & HAIR: Highly expressive stylized anime eyes with multi-layered specular reflections and clumped dynamic hair silhouettes.\n"
        "- BACKGROUND: Vibrant hand-painted 2D scenic illustration with glowing light dust and atmospheric bloom.\n"
        "- LAYER 2 ADAPTATION: If narrative, describe clean 2D anime visuals; if booru/tags, enforce 'anime_coloring, cel_shading, clean_lineart, 2d_illustration'."
    ),

    "Comic Book & Graphic Novel (Ink & Halftone)": (
        "AESTHETIC INJECTION (Apply to <PROMPT> only): Classic Graphic Novel & Comic Book Illustration.\n"
        "Infuse the graphic power of indie and modern western comics (Dark Horse, DC Black Label) without outputting directive labels or bullet points:\n"
        "- INKWORK: Bold India ink contour linework with dynamic variable line weight, deep black shadow blocks, and volumetric crosshatching.\n"
        "- PRINT TEXTURE: Visible Ben-Day halftone screen dot patterns, vintage offset pulp newsprint texture, and striking high-contrast graphic color plates.\n"
        "- LAYER 2 ADAPTATION: If narrative, detail the inking and graphic stylization; if categories, specify heavy inkwork under Textures; if tags, append 'comic book illustration, bold ink outlines, crosshatching, halftone dots'."
    ),

    "Pencil Sketch & Charcoal Drawing": (
        "AESTHETIC INJECTION (Apply to <PROMPT> only): Traditional Fine Art Pencil & Charcoal Drawing.\n"
        "Infuse authentic classical atelier draftsmanship on heavyweight textured paper without outputting directive labels or bullet points:\n"
        "- MEDIUM & MARKS: Graphite pencil lines (ranging from light 2H construction lines to rich 6B accents), smudged charcoal shading, and energetic hand gestures.\n"
        "- PAPER TEXTURE: Visible tooth and grain of rough vellum paper, kneaded eraser negative highlights, and organic graphite dust.\n"
        "- LAYER 2 ADAPTATION: If narrative, describe the hand-drawn marks and textured paper; if categories, set materials to graphite and paper; if tags, append 'pencil sketch, charcoal drawing, hand drawn, paper texture, crosshatching'."
    ),

    # ── 3D, DIGITAL CONCEPT & FINE ART FAMILY ────────────────────────────
    "3D Digital Render & CGI (PBR)": (
        "AESTHETIC INJECTION (Apply to <PROMPT> only): High-End 3D Computer Graphics & PBR Rendering.\n"
        "Infuse cutting-edge 3D graphics rendering (Unreal Engine 5 Lumen, Octane Render) without outputting directive labels or bullet points:\n"
        "- SHADER PHYSICS: Physically based shader materials (anisotropic metal, dispersive caustics glass, subsurface scattering polymers, micro-roughness).\n"
        "- COMPUTATIONAL LIGHT: Raytraced global illumination, diffuse light bounces, crisp ambient occlusion crevice shadows, and geometric polygonal precision.\n"
        "- LAYER 2 ADAPTATION: If narrative, emphasize 3D material interaction; if categories, specify PBR shaders; if tags, append '3D render, octane render, raytracing, PBR materials, global illumination'."
    ),

    "Digital Concept Art & Illustration": (
        "AESTHETIC INJECTION (Apply to <PROMPT> only): Epic Digital Concept Art & Keyframe Illustration.\n"
        "Infuse production keyframe matte painting aesthetics (ArtStation trending) without outputting directive labels or bullet points:\n"
        "- BRUSHWORK: Painterly digital brushwork balancing loose atmospheric background block-ins with razor-sharp focal details.\n"
        "- ATMOSPHERICS: Cinematic volumetric God rays, airborne particles, deep atmospheric perspective, and epic visual storytelling drama.\n"
        "- LAYER 2 ADAPTATION: If narrative, weave dramatic painterly brushwork into the scene; if categories, specify matte painting under Optics; if tags, append 'digital concept art, painterly illustration, volumetric light, matte painting'."
    ),

    "Oil Painting & Classical Fine Art": (
        "AESTHETIC INJECTION (Apply to <PROMPT> only): Classical Master Oil Painting on Canvas.\n"
        "Infuse the physical mastery of historic oil painting (Caravaggio, Rembrandt, Sargent) without outputting directive labels or bullet points:\n"
        "- PAINT IMPASTO: Thick raised impasto brushstrokes catching raking light, luminous multi-layered oil glazes, and fluid wet-on-wet alla prima strokes.\n"
        "- CANVAS & AGING: Coarse woven linen canvas texture visible through paint layers, aged varnish sheen, and delicate craquelure micro-cracks.\n"
        "- LIGHTING: Dramatic high-contrast chiaroscuro with deep glowing umber shadows and rich traditional mineral pigment palette.\n"
        "- LAYER 2 ADAPTATION: If narrative, describe the physical impasto oil paint on canvas; if categories, set materials to oil paint and linen; if tags, append 'oil painting, canvas texture, impasto brushstrokes, chiaroscuro'."
    ),
}

# ── LEGACY BACKWARD-COMPATIBILITY ALIASES ─────────────────────────────────
LEGACY_ARTISTIC_STYLE_ALIASES = {
    # Direct mappings from previous or legacy styles to new standardized styles
    "Photorealistic & Cinematic": "Photorealistic (Modern Digital RAW)",
    "Vintage Film (35mm Analog, Grain)": "Analog Film (35mm Vintage Stock)",
    "Anime & Manga (2D / Cel-shaded)": "Anime & Manga (2D Cel-shaded)",
    "Comic Book & Graphic Novel": "Comic Book & Graphic Novel (Ink & Halftone)",
    "Pencil Sketch & Traditional Ink": "Pencil Sketch & Charcoal Drawing",
    "3D Digital Render & CGI": "3D Digital Render & CGI (PBR)",
    "3D CGI & Octane Render": "3D Digital Render & CGI (PBR)",
    "Digital Concept Art & Illustration": "Digital Concept Art & Illustration",
    "Digital Concept Art (ArtStation)": "Digital Concept Art & Illustration",
    "Oil Painting & Fine Art": "Oil Painting & Classical Fine Art",
    "Cyberpunk & Sci-Fi": "Cinematic Still (Anamorphic Movie)",
}


def resolve_artistic_style(artistic_style):
    """Resolves legacy or partial artistic styles to active standardized artistic styles."""
    return LEGACY_ARTISTIC_STYLE_ALIASES.get(artistic_style, artistic_style)

