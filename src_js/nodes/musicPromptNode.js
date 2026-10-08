import { app } from "../../../scripts/app.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";
import { StoiqoSectionDividerWidget } from "../utils/core.js";

/**
 * [STOIQO] Music Prompt & Lyrics Engine (YuE2 / Suno)
 * UI Enhancement: Section dividers, tuned multiline inputs, live Style & Lyrics HUD display,
 * and one-click clipboard copy buttons for YuE2 audio workflows.
 */
export function setupMusicPromptNode(nodeType, nodeData, app) {
    const musicTargetNames = [
        "StoiqoMusicPromptEngineNode",
        "[STOIQO] Music Prompt & Lyrics Engine (YuE2)",
        "[STOIQO] Music Prompt & Lyrics Engine",
    ];

    if (!musicTargetNames.includes(nodeData.name)) return;

    const MIN_NODE_WIDTH = 480;

    const SECTIONS = [
        { targetWidget: "idea", num: "1", title: "CONCEPT & CORE THEME", color: "#f43f5e" },
        { targetWidget: "genre", num: "2", title: "GENRE & ACOUSTICS", color: "#a855f7" },
        { targetWidget: "vocal_type", num: "3", title: "VOCALS & LANGUAGE", color: "#38bdf8" },
        { targetWidget: "structure", num: "4", title: "STRUCTURE & TEMPO", color: "#eab308" },
        { targetWidget: "seed", num: "5", title: "GENERATION & SAMPLING", color: "#10b981" },
    ];

    const MULTILINE_HEIGHTS = {
        "idea": 76,
        "custom_directives": 54,
    };

    function setupNodeInstance(node) {
        if (!node || !node.widgets) return;

        // Restore clean native styling
        if (node.bgcolor === "#0e1218" || node.bgcolor === "#0b1411") delete node.bgcolor;
        if (node.color === "#18202c" || node.color === "#14251f") delete node.color;

        if (node.size && node.size[0] < MIN_NODE_WIDTH) {
            node.size[0] = MIN_NODE_WIDTH;
        }

        // 1. Style multiline inputs
        for (const [wName, hVal] of Object.entries(MULTILINE_HEIGHTS)) {
            const w = node.widgets.find(item => item.name === wName);
            if (w) {
                w.computeSize = function(width) {
                    return [width, hVal];
                };

                const applyInputStyles = (el) => {
                    if (!el) return;
                    el.style.boxSizing = "border-box";
                    el.style.height = `${hVal}px`;
                    el.style.minHeight = `${hVal}px`;
                    el.style.maxHeight = `${hVal}px`;
                    el.style.resize = "none";
                    el.style.fontSize = "11.5px";
                    el.style.lineHeight = "1.45";
                };

                if (w.inputEl) {
                    applyInputStyles(w.inputEl);
                } else {
                    let rawEl = null;
                    Object.defineProperty(w, "inputEl", {
                        configurable: true,
                        enumerable: true,
                        get() { return rawEl; },
                        set(val) {
                            rawEl = val;
                            applyInputStyles(val);
                        }
                    });
                }
            }
        }

        // 2. Insert Section Dividers Idempotently
        node.widgets = node.widgets.filter(w => !w.isStoiqoDivider);
        for (const sec of SECTIONS) {
            const targetIdx = node.widgets.findIndex(w => w.name === sec.targetWidget);
            if (targetIdx !== -1) {
                const divider = new StoiqoSectionDividerWidget(sec.num, sec.title, sec.color);
                node.widgets.splice(targetIdx, 0, divider);
            }
        }

        // 3. Ensure Live Preview Widgets Exist (Style & Lyrics HUD)
        let styleDisplay = node.widgets.find(w => w.name === "preview_style");
        if (!styleDisplay) {
            const styleDivider = new StoiqoSectionDividerWidget("6", "YUE2 OUTPUT: STYLE DESCRIPTOR", "#06b6d4");
            node.widgets.push(styleDivider);

            if (typeof ComfyWidgets !== "undefined" && ComfyWidgets["STRING"]) {
                styleDisplay = ComfyWidgets["STRING"](
                    node,
                    "preview_style",
                    ["STRING", { multiline: true }],
                    app
                ).widget;
            } else {
                styleDisplay = node.addWidget(
                    "customtext",
                    "preview_style",
                    "",
                    function() {},
                    { multiline: true }
                );
            }

            if (styleDisplay) {
                styleDisplay.name = "preview_style";
                styleDisplay.options = styleDisplay.options || {};
                styleDisplay.options.serialize = false;
                styleDisplay.computeSize = function(width) { return [width, 64]; };

                const styleBox = (el) => {
                    if (!el) return;
                    el.readOnly = true;
                    el.placeholder = "YuE2 Style (Acoustic descriptors only, no lyrics) will appear here...";
                    el.style.boxSizing = "border-box";
                    el.style.height = "64px";
                    el.style.minHeight = "64px";
                    el.style.fontSize = "11px";
                    el.style.lineHeight = "1.4";
                    el.style.color = "#38bdf8";
                    el.style.background = "rgba(15, 23, 42, 0.65)";
                    el.style.fontFamily = "monospace, -apple-system, sans-serif";
                };

                if (styleDisplay.inputEl) styleBox(styleDisplay.inputEl);
                else {
                    let rawEl = null;
                    Object.defineProperty(styleDisplay, "inputEl", {
                        configurable: true,
                        enumerable: true,
                        get() { return rawEl; },
                        set(val) { rawEl = val; styleBox(val); }
                    });
                }
            }
        }

        let lyricsDisplay = node.widgets.find(w => w.name === "preview_lyrics");
        if (!lyricsDisplay) {
            const lyricsDivider = new StoiqoSectionDividerWidget("7", "YUE2 OUTPUT: STRUCTURED LYRICS", "#ec4899");
            node.widgets.push(lyricsDivider);

            if (typeof ComfyWidgets !== "undefined" && ComfyWidgets["STRING"]) {
                lyricsDisplay = ComfyWidgets["STRING"](
                    node,
                    "preview_lyrics",
                    ["STRING", { multiline: true }],
                    app
                ).widget;
            } else {
                lyricsDisplay = node.addWidget(
                    "customtext",
                    "preview_lyrics",
                    "",
                    function() {},
                    { multiline: true }
                );
            }

            if (lyricsDisplay) {
                lyricsDisplay.name = "preview_lyrics";
                lyricsDisplay.options = lyricsDisplay.options || {};
                lyricsDisplay.options.serialize = false;
                lyricsDisplay.computeSize = function(width) { return [width, 110]; };

                const lyricsBox = (el) => {
                    if (!el) return;
                    el.readOnly = true;
                    el.placeholder = "YuE2 Lyrics ([Verse], [Chorus], [Bridge]) will appear here...";
                    el.style.boxSizing = "border-box";
                    el.style.height = "110px";
                    el.style.minHeight = "110px";
                    el.style.fontSize = "11px";
                    el.style.lineHeight = "1.4";
                    el.style.color = "#f472b6";
                    el.style.background = "rgba(15, 23, 42, 0.65)";
                    el.style.fontFamily = "monospace, -apple-system, sans-serif";
                };

                if (lyricsDisplay.inputEl) lyricsBox(lyricsDisplay.inputEl);
                else {
                    let rawEl = null;
                    Object.defineProperty(lyricsDisplay, "inputEl", {
                        configurable: true,
                        enumerable: true,
                        get() { return rawEl; },
                        set(val) { rawEl = val; lyricsBox(val); }
                    });
                }
            }
        }

        // 4. Quick Action Copy Buttons
        let copyStyleBtn = node.widgets.find(w => w._isMusicCopyStyle);
        if (!copyStyleBtn) {
            copyStyleBtn = node.addWidget(
                "button",
                "📋 Copia Style (YuE2 Descriptor)",
                null,
                function() {
                    const sw = node.widgets?.find(w => w.name === "preview_style");
                    const val = sw ? (sw.value || (sw.inputEl && sw.inputEl.value) || "") : "";
                    if (val && navigator.clipboard) {
                        navigator.clipboard.writeText(String(val));
                        const orig = this.name;
                        this.name = "✓ Style Copiato!";
                        node.setDirtyCanvas(true);
                        setTimeout(() => { this.name = orig; node.setDirtyCanvas(true); }, 1800);
                    }
                },
                { serialize: false }
            );
            copyStyleBtn._isMusicCopyStyle = true;
            copyStyleBtn.options = { serialize: false };
        }

        let copyLyricsBtn = node.widgets.find(w => w._isMusicCopyLyrics);
        if (!copyLyricsBtn) {
            copyLyricsBtn = node.addWidget(
                "button",
                "📋 Copia Lyrics (YuE2 Stanza)",
                null,
                function() {
                    const lw = node.widgets?.find(w => w.name === "preview_lyrics");
                    const val = lw ? (lw.value || (lw.inputEl && lw.inputEl.value) || "") : "";
                    if (val && navigator.clipboard) {
                        navigator.clipboard.writeText(String(val));
                        const orig = this.name;
                        this.name = "✓ Lyrics Copiate!";
                        node.setDirtyCanvas(true);
                        setTimeout(() => { this.name = orig; node.setDirtyCanvas(true); }, 1800);
                    }
                },
                { serialize: false }
            );
            copyLyricsBtn._isMusicCopyLyrics = true;
            copyLyricsBtn.options = { serialize: false };
        }

        // Adjust dimensions
        if (typeof node.computeSize === "function") {
            const computed = node.computeSize();
            node.size[0] = Math.max(node.size[0] || 0, MIN_NODE_WIDTH);
            node.size[1] = Math.max(node.size[1] || 0, Math.ceil(computed[1]));
        }

        node.setDirtyCanvas(true, true);
    }

    const origOnCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function() {
        if (origOnCreated) origOnCreated.apply(this, arguments);
        setupNodeInstance(this);
    };

    const origOnConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function() {
        if (origOnConfigure) origOnConfigure.apply(this, arguments);
        setupNodeInstance(this);
    };

    // Update preview widgets upon execution
    const origOnExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function(message) {
        if (origOnExecuted) origOnExecuted.apply(this, arguments);

        if (message && message.music_info && message.music_info.length > 0) {
            const info = message.music_info[0];
            const sw = this.widgets?.find(w => w.name === "preview_style");
            const lw = this.widgets?.find(w => w.name === "preview_lyrics");

            if (sw && info.style) {
                sw.value = info.style;
                if (sw.inputEl) sw.inputEl.value = info.style;
            }

            if (lw && info.lyrics) {
                lw.value = info.lyrics;
                if (lw.inputEl) lw.inputEl.value = info.lyrics;
            }

            this.setDirtyCanvas(true, true);
        }
    };
}
