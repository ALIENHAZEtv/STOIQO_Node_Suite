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
        { targetWidget: "system_prompt", num: "2", title: "PRODUCER PERSONA & AI AGENT", color: "#ec4899" },
        { targetWidget: "genre", num: "3", title: "GENRE & ACOUSTICS", color: "#a855f7" },
        { targetWidget: "vocal_type", num: "4", title: "VOCALS & LANGUAGE", color: "#38bdf8" },
        { targetWidget: "structure", num: "5", title: "STRUCTURE & TEMPO", color: "#eab308" },
        { targetWidget: "custom_lyrics", num: "6", title: "CUSTOM LYRICS & DIRECTIVES (OPTIONAL)", color: "#818cf8" },
        { targetWidget: "seed", num: "7", title: "GENERATION & SAMPLING", color: "#10b981" },
    ];

    const MULTILINE_HEIGHTS = {
        "idea": 76,
        "custom_system_prompt": 68,
        "custom_lyrics": 72,
        "custom_directives": 54,
    };

    const PLACEHOLDERS = {
        "idea": "Describe ANY musical vision, emotion, story, artist/band influence, or concept in free natural language (e.g. 'un brano baroque pop in italiano con clavicembalo e archi', 'cyberpunk industrial synthwave', 'fuga per organo')...",
        "custom_system_prompt": "Active only when system_prompt = 'Custom'. Write your custom AI music producer system instructions here...",
        "custom_lyrics": "Optional: Write or paste your own lyrics. Leave blank for full AI lyric generation...",
        "custom_directives": "Optional constraints (e.g. 'acoustic cello solo', 'no drums in verse 1')...",
    };

    function setupNodeInstance(node) {
        if (!node || !node.widgets) return;

        // Restore clean native styling
        if (node.bgcolor === "#0e1218" || node.bgcolor === "#0b1411") delete node.bgcolor;
        if (node.color === "#18202c" || node.color === "#14251f") delete node.color;

        if (node.size && node.size[0] < MIN_NODE_WIDTH) {
            node.size[0] = MIN_NODE_WIDTH;
        }

        // 0. Sanitize shifted LiteGraph deserialization tokens (e.g. "randomize", "fixed", numbers)
        for (const wName of ["custom_lyrics", "custom_directives", "custom_system_prompt"]) {
            const w = node.widgets?.find(item => item.name === wName);
            if (w) {
                const rawVal = String(w.value || "").trim().toLowerCase();
                if (["randomize", "fixed", "increment", "decrement"].includes(rawVal) || (!isNaN(Number(rawVal)) && rawVal.length > 0)) {
                    w.value = "";
                    if (w.inputEl) w.inputEl.value = "";
                }
            }
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
                    if (PLACEHOLDERS[wName]) {
                        el.placeholder = PLACEHOLDERS[wName];
                    }
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

        // 2. Dynamic Visibility Toggle for Custom System Prompt
        function updateSystemPromptVisibility() {
            const sysPromptWidget = node.widgets.find(w => w.name === "system_prompt");
            const customWidget = node.widgets.find(w => w.name === "custom_system_prompt");
            if (!customWidget) return;

            const isCustomSelected = sysPromptWidget && String(sysPromptWidget.value || "").includes("Custom");

            if (!customWidget._stoiqoOrigComputeSize) {
                customWidget._stoiqoOrigComputeSize = customWidget.computeSize;
                customWidget._stoiqoOrigDraw = customWidget.draw;
            }

            if (isCustomSelected) {
                customWidget.hidden = false;
                customWidget.computeSize = function(width) {
                    return [width, MULTILINE_HEIGHTS["custom_system_prompt"] || 68];
                };
                if (customWidget._stoiqoOrigDraw) {
                    customWidget.draw = customWidget._stoiqoOrigDraw;
                }
                if (customWidget.inputEl) {
                    customWidget.inputEl.hidden = false;
                    customWidget.inputEl.style.display = "";
                }
            } else {
                customWidget.hidden = true;
                customWidget.computeSize = function() {
                    return [0, -4]; // Collapse slot cleanly
                };
                customWidget.draw = function() {};
                if (customWidget.inputEl) {
                    customWidget.inputEl.hidden = true;
                    customWidget.inputEl.style.display = "none";
                }
            }

            if (typeof node.computeSize === "function") {
                const computed = node.computeSize();
                node.size[0] = Math.max(node.size[0] || 0, MIN_NODE_WIDTH);
                node.size[1] = Math.max(node.size[1] || 0, Math.ceil(computed[1]));
            }
            node.setDirtyCanvas(true, true);
        }

        const sysPromptWidget = node.widgets.find(w => w.name === "system_prompt");
        if (sysPromptWidget && !sysPromptWidget._stoiqoVisibilityHooked) {
            sysPromptWidget._stoiqoVisibilityHooked = true;
            const origSysCallback = sysPromptWidget.callback;
            sysPromptWidget.callback = function(val) {
                if (origSysCallback) origSysCallback.apply(this, arguments);
                updateSystemPromptVisibility();
            };
        }

        updateSystemPromptVisibility();

        // 3. Remove legacy section dividers (clean UI managed by ⚙ settings drawer)
        node.widgets = node.widgets.filter(w => !w.isStoiqoDivider);

        // 4. Ensure Live Preview Widgets Exist (Style & Lyrics HUD)
        let trackInfoDisplay = node.widgets.find(w => w.name === "preview_track_info");
        if (!trackInfoDisplay) {
            const trackDivider = new StoiqoSectionDividerWidget("8", "YUE2 OUTPUT: TRACK TELEMETRY & STYLE", "#06b6d4");
            node.widgets.push(trackDivider);

            trackInfoDisplay = node.addWidget(
                "text",
                "preview_track_info",
                "🎵 Waiting for generation...",
                function() {},
                { serialize: false }
            );
            if (trackInfoDisplay) {
                trackInfoDisplay.name = "preview_track_info";
                trackInfoDisplay.serialize = false;
                trackInfoDisplay.options = trackInfoDisplay.options || {};
                trackInfoDisplay.options.serialize = false;
                trackInfoDisplay.computeSize = function(width) { return [width, 24]; };
            }
        }

        let styleDisplay = node.widgets.find(w => w.name === "preview_style");
        if (!styleDisplay) {
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
                styleDisplay.serialize = false;
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
            const lyricsDivider = new StoiqoSectionDividerWidget("9", "YUE2 OUTPUT: STRUCTURED LYRICS", "#ec4899");
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
                lyricsDisplay.serialize = false;
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
            copyStyleBtn.serialize = false;
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
            copyLyricsBtn.serialize = false;
            copyLyricsBtn.options = { serialize: false };
        }

        let copyMetricsBtn = node.widgets.find(w => w._isMusicCopyMetrics);
        if (!copyMetricsBtn) {
            copyMetricsBtn = node.addWidget(
                "button",
                "📐 Copia Analisi Metrica Sillabica",
                null,
                function() {
                    const lastInfo = node._lastMusicInfo;
                    let report = "";
                    if (lastInfo && lastInfo.metric_summary) {
                        report = `🎵 ${lastInfo.title || "Song"} — Lyrical Metric Analysis\n` +
                                 `Dominant Meter: ${lastInfo.dominant_meter || "N/A"}\n` +
                                 `Rhythmic Cadence Score: ${lastInfo.rhythmic_score || 85}%\n` +
                                 `Summary: ${lastInfo.metric_summary}\n\n`;
                        if (lastInfo.metrics && lastInfo.metrics.sections) {
                            report += "Section Breakdown:\n";
                            for (const sec of lastInfo.metrics.sections) {
                                report += `  ${sec.section_name} (${sec.line_count} lines, avg ${sec.avg_syllables} syl/line — ${sec.dominant_meter})\n`;
                                for (const ln of sec.lines) {
                                    report += `    • [${ln.syllables} syl] ${ln.text}\n`;
                                }
                            }
                        }
                    } else {
                        const tw = node.widgets?.find(w => w.name === "preview_track_info");
                        report = tw ? (tw.value || "") : "No metrics available.";
                    }
                    if (report && navigator.clipboard) {
                        navigator.clipboard.writeText(report);
                        const orig = this.name;
                        this.name = "✓ Metrica Copiata!";
                        node.setDirtyCanvas(true);
                        setTimeout(() => { this.name = orig; node.setDirtyCanvas(true); }, 1800);
                    }
                },
                { serialize: false }
            );
            copyMetricsBtn._isMusicCopyMetrics = true;
            copyMetricsBtn.serialize = false;
            copyMetricsBtn.options = { serialize: false };
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
            this._lastMusicInfo = info;
            const tw = this.widgets?.find(w => w.name === "preview_track_info");
            const sw = this.widgets?.find(w => w.name === "preview_style");
            const lw = this.widgets?.find(w => w.name === "preview_lyrics");

            if (tw) {
                const durSec = Math.round(info.max_duration || 0);
                const durMin = Math.floor(durSec / 60);
                const durRemSec = String(durSec % 60).padStart(2, '0');
                const durStr = durSec > 0 ? `${durSec}s (~${durMin}:${durRemSec}m)` : "Dynamic";
                const modeStr = info.mode === "full" ? "Full Song" : (info.mode === "melody" ? "Melody Lead" : "Vocal");
                const meterTag = info.dominant_meter ? ` | 📐 ${info.dominant_meter}` : "";
                const cadenceTag = info.rhythmic_score ? ` (${info.rhythmic_score}%)` : "";
                const summaryText = `🎵 ${info.title || "Untitled"} | ⏱️ ${durStr} | 🥁 ${info.bpm || 120} BPM | 🎹 ${info.musical_key || "N/A"} | 🎚️ ${modeStr}${meterTag}${cadenceTag}`;
                tw.value = summaryText;
                if (tw.inputEl) tw.inputEl.value = summaryText;
            }

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
