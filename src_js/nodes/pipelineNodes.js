/**
 * [STOIQO] Pipeline & Utility Nodes — Visual Standards & Ergonomics
 * Clean, lightweight, minimal layout sizing across all pipeline nodes.
 * Zero custom divider bloat, 100% native ComfyUI performance.
 */

const CONFIGURATIONS = {
    // 1. Watermark & Logo Stamp
    StoiqoWatermarkNode: {
        minWidth: 380,
    },
    // 2. Turbo Sampler & Direct Decoder
    StoiqoTurboSamplerNode: {
        minWidth: 420,
        multilineHeights: {
            positive_prompt: 72,
            negative_prompt: 48,
        },
    },
    // 3. Tri-Model Loader Hub
    StoiqoTriLoaderHubNode: {
        minWidth: 380,
    },
    // 4. Smart Seed & Variance Controller
    StoiqoSeedControllerNode: {
        minWidth: 340,
    },
    // 5. Inpaint Stitcher & Composite
    StoiqoInpaintStitcherNode: {
        minWidth: 360,
    },
    // 6. Pro Audio Saver (YuE2)
    StoiqoAudioSaverNode: {
        minWidth: 400,
        multilineHeights: {
            lyrics: 68,
            style: 48,
        },
    },
    // 7. Pro Video Saver (MiniMax)
    StoiqoVideoSaverNode: {
        minWidth: 400,
        multilineHeights: {
            motion_prompt: 56,
        },
    },
    // 8. Modular Prompt Synthesizer Engine
    StoiqoPromptSynthesizerNode: {
        minWidth: 420,
        multilineHeights: {
            user_directives: 68,
        },
    },
    // 9. AI Persona & Style Directives
    StoiqoStyleDirectivesNode: {
        minWidth: 380,
        multilineHeights: {
            custom_system_prompt: 52,
        },
    },
    // 10. LLM Sampling & Precision
    StoiqoSamplingOptionsNode: {
        minWidth: 360,
    },
    // 11. Multi-Image Context Hub
    StoiqoMultiImageContextNode: {
        minWidth: 380,
    },
    // 12. Character Consistency Memory Bank (Lorebook & DNA)
    StoiqoCharacterMemoryNode: {
        minWidth: 420,
        multilineHeights: {
            face_and_skin: 52,
            signature_outfit: 52,
            negative_constraints: 48,
            user_prompt: 48,
        },
    },
    // 13. Universal Context Pipe (In / Bus)
    StoiqoUniversalPipeInNode: {
        minWidth: 320,
    },
    // 14. Universal Context Pipe (Out / Unpack)
    StoiqoUniversalPipeOutNode: {
        minWidth: 320,
    },
    // 15. Webhook Notifier & Pipeline Exporter
    StoiqoWebhookNotifierNode: {
        minWidth: 400,
        multilineHeights: {
            message: 56,
        },
    },
};


export function setupPipelineNodes(nodeType, nodeData, appInstance) {
    const nodeName = nodeData.name;
    const config = CONFIGURATIONS[nodeName];
    if (!config) return;

    const origOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function() {
        if (origOnNodeCreated) origOnNodeCreated.apply(this, arguments);

        const node = this;
        if (!node || !node.widgets) return;

        // Clean out any leftover divider widgets
        node.widgets = node.widgets.filter(w => !w.isStoiqoDivider);

        // Apply comfortable minimum width
        if (config.minWidth && node.size && node.size[0] < config.minWidth) {
            node.size[0] = config.minWidth;
        }

        // Standardize multiline text box heights without overlap
        if (config.multilineHeights) {
            for (const [widgetName, hVal] of Object.entries(config.multilineHeights)) {
                const w = node.widgets.find(w => w.name === widgetName);
                if (w) {
                    w.computeSize = function(width) {
                        return [width, hVal];
                    };
                    if (w.inputEl) {
                        w.inputEl.style.boxSizing = "border-box";
                        w.inputEl.style.height = `${hVal}px`;
                        w.inputEl.style.minHeight = `${hVal}px`;
                        w.inputEl.style.maxHeight = `${hVal}px`;
                        w.inputEl.style.resize = "none";
                        w.inputEl.style.fontSize = "11.5px";
                        w.inputEl.style.lineHeight = "1.45";
                    }
                }
            }
        }

        if (nodeName === "StoiqoPromptSynthesizerNode") {
            let tw = node.widgets.find(w => w.name === "synthesized_prompt");
            if (!tw) {
                tw = node.addWidget(
                    "customtext",
                    "synthesized_prompt",
                    "",
                    function() {},
                    { multiline: true }
                );
                tw.options = { serialize: false };
                tw.computeSize = function(width) {
                    return [width, 100];
                };
                const styleTw = (el) => {
                    if (!el) return;
                    el.readOnly = true;
                    el.placeholder = "Prompt stream output...";
                    el.style.boxSizing = "border-box";
                    el.style.fontSize = "11.5px";
                    el.style.lineHeight = "1.45";
                    el.style.fontFamily = "monospace, -apple-system, sans-serif";
                    el.style.opacity = "0.92";
                };
                if (tw.inputEl) {
                    styleTw(tw.inputEl);
                } else {
                    let rawEl = null;
                    Object.defineProperty(tw, "inputEl", {
                        configurable: true,
                        enumerable: true,
                        get() { return rawEl; },
                        set(v) { rawEl = v; styleTw(v); }
                    });
                }
            }
        }

        if (nodeName === "StoiqoStyleDirectivesNode") {
            const updateCustomPromptVisibility = () => {
                const sys = node.widgets.find(w => w.name === "system_prompt");
                const custom = node.widgets.find(w => w.name === "custom_system_prompt");
                if (!custom) return;
                if (!custom._stoiqoOrig) {
                    custom._stoiqoOrig = { computeSize: custom.computeSize, draw: custom.draw };
                }
                const show = !!sys && String(sys.value || "").includes("Custom");
                custom.hidden = !show;
                custom.computeSize = show ? custom._stoiqoOrig.computeSize : () => [0, -4];
                custom.draw = show ? custom._stoiqoOrig.draw : () => {};
                if (custom.inputEl) {
                    custom.inputEl.hidden = !show;
                    custom.inputEl.style.display = show ? "" : "none";
                }
                if (typeof node.computeSize === "function") {
                    const computed = node.computeSize();
                    node.size[1] = Math.max(Math.ceil(computed[1]), 60);
                }
                node.setDirtyCanvas?.(true, true);
            };
            const sysWidget = node.widgets.find(w => w.name === "system_prompt");
            if (sysWidget && !sysWidget._stoiqoHooked) {
                sysWidget._stoiqoHooked = true;
                const origCb = sysWidget.callback;
                sysWidget.callback = function() {
                    if (origCb) origCb.apply(this, arguments);
                    updateCustomPromptVisibility();
                };
            }
            node._stoiqoUpdateCustomPrompt = updateCustomPromptVisibility;
            setTimeout(updateCustomPromptVisibility, 50);
        }

        if (nodeName === "StoiqoAudioSaverNode") {
            createAudioPlayerWidget(node, null);
        }

        if (nodeName === "StoiqoVideoSaverNode") {
            createVideoPlayerWidget(node, null);
        }

        if (node.setDirtyCanvas) {
            node.setDirtyCanvas(true, true);
        }
    };

    if (nodeName === "StoiqoStyleDirectivesNode") {
        const origOnConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function() {
            if (origOnConfigure) origOnConfigure.apply(this, arguments);
            if (this._stoiqoUpdateCustomPrompt) setTimeout(this._stoiqoUpdateCustomPrompt, 50);
        };
    }

    if (nodeName === "StoiqoPromptSynthesizerNode") {
        const origOnExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function(message) {
            if (origOnExecuted) origOnExecuted.apply(this, arguments);
            if (message && message.text) {
                const tw = this.widgets?.find(w => w.name === "synthesized_prompt");
                if (tw) {
                    const txt = Array.isArray(message.text) ? message.text.join("\n") : String(message.text || "");
                    tw.value = txt;
                    if (tw.inputEl) tw.inputEl.value = txt;
                }
                this.setDirtyCanvas(true, true);
            }
        };
    }

    if (nodeName === "StoiqoAudioSaverNode") {
        const origOnExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function(message) {
            if (origOnExecuted) origOnExecuted.apply(this, arguments);
            if (message && message.audio && message.audio.length > 0) {
                createAudioPlayerWidget(this, message.audio[0]);
            }
        };
    }

    if (nodeName === "StoiqoVideoSaverNode") {
        const origOnExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function(message) {
            if (origOnExecuted) origOnExecuted.apply(this, arguments);
            const vData = (message?.videos && message.videos[0]) || (message?.gifs && message.gifs[0]) || (message?.images && message.images[0]);
            if (vData) {
                createVideoPlayerWidget(this, vData);
            }
        };
    }
}


function createAudioPlayerWidget(node, audioData) {
    if (!node || !node.addDOMWidget) return;
    let widget = node.widgets?.find(w => w.name === "audio_player");

    if (!widget) {
        const container = document.createElement("div");
        container.className = "stoiqo-audio-player";
        container.style.display = "flex";
        container.style.flexDirection = "column";
        container.style.gap = "6px";
        container.style.padding = "8px 10px";
        container.style.background = "linear-gradient(135deg, rgba(18, 20, 29, 0.95), rgba(10, 12, 18, 0.98))";
        container.style.border = "1px solid rgba(0, 229, 255, 0.25)";
        container.style.borderRadius = "8px";
        container.style.boxShadow = "0 4px 16px rgba(0, 0, 0, 0.4)";
        container.style.fontFamily = "system-ui, -apple-system, sans-serif";
        container.style.color = "#e2e8f0";
        container.style.userSelect = "none";
        container.style.marginTop = "4px";

        // HTML5 Audio element
        const audio = document.createElement("audio");
        audio.preload = "metadata";

        // Header: Track Name & Status
        const header = document.createElement("div");
        header.style.display = "flex";
        header.style.justifyContent = "space-between";
        header.style.alignItems = "center";
        header.style.fontSize = "11px";
        header.style.fontWeight = "600";
        header.style.color = "#00e5ff";

        const titleEl = document.createElement("span");
        titleEl.textContent = audioData?.filename || "YuE2 / Suno Track Preview";
        titleEl.style.overflow = "hidden";
        titleEl.style.textOverflow = "ellipsis";
        titleEl.style.whiteSpace = "nowrap";
        titleEl.style.maxWidth = "220px";

        const timeEl = document.createElement("span");
        timeEl.textContent = "0:00 / 0:00";
        timeEl.style.fontFamily = "monospace";
        timeEl.style.color = "#94a3b8";

        header.appendChild(titleEl);
        header.appendChild(timeEl);

        // Controls Row
        const controls = document.createElement("div");
        controls.style.display = "flex";
        controls.style.alignItems = "center";
        controls.style.gap = "8px";

        // Play/Pause button
        const playBtn = document.createElement("button");
        playBtn.type = "button";
        playBtn.style.background = "linear-gradient(135deg, #00e5ff, #7928ca)";
        playBtn.style.border = "none";
        playBtn.style.borderRadius = "50%";
        playBtn.style.width = "28px";
        playBtn.style.height = "28px";
        playBtn.style.display = "flex";
        playBtn.style.alignItems = "center";
        playBtn.style.justifyContent = "center";
        playBtn.style.cursor = "pointer";
        playBtn.style.color = "#ffffff";
        playBtn.style.flexShrink = "0";
        playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`;

        // Scrubber / Progress Bar
        const progress = document.createElement("input");
        progress.type = "range";
        progress.min = "0";
        progress.max = "100";
        progress.value = "0";
        progress.style.flex = "1";
        progress.style.accentColor = "#00e5ff";
        progress.style.cursor = "pointer";
        progress.style.height = "4px";

        controls.appendChild(playBtn);
        controls.appendChild(progress);

        container.appendChild(header);
        container.appendChild(controls);
        container.appendChild(audio);

        const formatTime = (secs) => {
            if (!secs || isNaN(secs)) return "0:00";
            const m = Math.floor(secs / 60);
            const s = Math.floor(secs % 60);
            return `${m}:${s < 10 ? '0' : ''}${s}`;
        };

        playBtn.onclick = (e) => {
            e.stopPropagation();
            if (audio.paused) {
                audio.play();
                playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>`;
            } else {
                audio.pause();
                playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`;
            }
        };

        audio.ontimeupdate = () => {
            if (!audio.duration) return;
            progress.value = (audio.currentTime / audio.duration) * 100;
            timeEl.textContent = `${formatTime(audio.currentTime)} / ${formatTime(audio.duration)}`;
        };

        audio.onended = () => {
            playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`;
            progress.value = 0;
        };

        progress.oninput = (e) => {
            e.stopPropagation();
            if (audio.duration) {
                audio.currentTime = (progress.value / 100) * audio.duration;
            }
        };

        widget = node.addDOMWidget("audio_player", "AUDIO_PLAYER", container, {
            serialize: false,
            hideOnZoom: false,
        });
        widget.computeSize = function(width) {
            return [width, 68];
        };
        widget.audioEl = audio;
        widget.titleEl = titleEl;
    }

    if (audioData && widget && widget.audioEl) {
        const url = `/view?filename=${encodeURIComponent(audioData.filename)}&subfolder=${encodeURIComponent(audioData.subfolder || "")}&type=${encodeURIComponent(audioData.type || "output")}`;
        widget.audioEl.src = url;
        if (widget.titleEl) widget.titleEl.textContent = audioData.filename;
        if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
    }
}

function createVideoPlayerWidget(node, videoData) {
    if (!node || !node.addDOMWidget) return;
    let widget = node.widgets?.find(w => w.name === "video_player");

    if (!widget) {
        const container = document.createElement("div");
        container.className = "stoiqo-video-player";
        container.style.display = "flex";
        container.style.flexDirection = "column";
        container.style.gap = "6px";
        container.style.padding = "8px 10px";
        container.style.background = "linear-gradient(135deg, rgba(16, 20, 30, 0.96), rgba(8, 10, 16, 0.98))";
        container.style.border = "1px solid rgba(0, 229, 255, 0.3)";
        container.style.borderRadius = "8px";
        container.style.boxShadow = "0 4px 16px rgba(0, 0, 0, 0.5)";
        container.style.fontFamily = "system-ui, -apple-system, sans-serif";
        container.style.color = "#e2e8f0";
        container.style.userSelect = "none";
        container.style.marginTop = "4px";

        // HTML5 Video element
        const video = document.createElement("video");
        video.preload = "auto";
        video.playsInline = true;
        video.muted = true;
        video.loop = true;
        video.style.width = "100%";
        video.style.maxHeight = "190px";
        video.style.objectFit = "contain";
        video.style.display = "block";
        video.style.borderRadius = "6px";
        video.style.background = "#040608";
        video.style.border = "1px solid rgba(255, 255, 255, 0.08)";

        // Header: Video Name & Time/Frame Counter
        const header = document.createElement("div");
        header.style.display = "flex";
        header.style.justifyContent = "space-between";
        header.style.alignItems = "center";
        header.style.fontSize = "11px";
        header.style.fontWeight = "600";
        header.style.color = "#00e5ff";

        const titleEl = document.createElement("span");
        titleEl.textContent = videoData?.filename || "MiniMax / Wan Video Preview";
        titleEl.style.overflow = "hidden";
        titleEl.style.textOverflow = "ellipsis";
        titleEl.style.whiteSpace = "nowrap";
        titleEl.style.maxWidth = "200px";

        const timeEl = document.createElement("span");
        timeEl.textContent = "00:00.00 / 00:00.00 (F: 0/0)";
        timeEl.style.fontFamily = "monospace";
        timeEl.style.fontSize = "10.5px";
        timeEl.style.color = "#94a3b8";

        header.appendChild(titleEl);
        header.appendChild(timeEl);

        // Scrubber / Progress Bar
        const progress = document.createElement("input");
        progress.type = "range";
        progress.min = "0";
        progress.max = "1000";
        progress.value = "0";
        progress.style.width = "100%";
        progress.style.accentColor = "#00e5ff";
        progress.style.cursor = "pointer";
        progress.style.height = "5px";
        progress.style.margin = "2px 0";

        // Controls Toolbar
        const controls = document.createElement("div");
        controls.style.display = "flex";
        controls.style.alignItems = "center";
        controls.style.justifyContent = "space-between";
        controls.style.gap = "6px";
        controls.style.fontSize = "11px";

        // Left Controls: Prev Frame, Play/Pause, Next Frame, Loop
        const leftControls = document.createElement("div");
        leftControls.style.display = "flex";
        leftControls.style.alignItems = "center";
        leftControls.style.gap = "6px";

        const createBtn = (text, title, padding = "3px 8px") => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.title = title;
            btn.textContent = text;
            btn.style.background = "rgba(255, 255, 255, 0.06)";
            btn.style.border = "1px solid rgba(255, 255, 255, 0.15)";
            btn.style.borderRadius = "4px";
            btn.style.padding = padding;
            btn.style.cursor = "pointer";
            btn.style.color = "#cbd5e1";
            btn.style.fontSize = "10.5px";
            btn.style.fontFamily = "inherit";
            btn.style.transition = "all 0.15s ease";
            btn.onmouseenter = () => btn.style.background = "rgba(0, 229, 255, 0.15)";
            btn.onmouseleave = () => {
                if (!btn.dataset.active) btn.style.background = "rgba(255, 255, 255, 0.06)";
            };
            return btn;
        };

        const prevFrameBtn = createBtn("⏮ -1F", "Step backward 1 frame");
        const nextFrameBtn = createBtn("+1F ⏭", "Step forward 1 frame");

        // Play/Pause button
        const playBtn = document.createElement("button");
        playBtn.type = "button";
        playBtn.title = "Play / Pause";
        playBtn.style.background = "linear-gradient(135deg, #00e5ff, #7928ca)";
        playBtn.style.border = "none";
        playBtn.style.borderRadius = "50%";
        playBtn.style.width = "28px";
        playBtn.style.height = "28px";
        playBtn.style.display = "flex";
        playBtn.style.alignItems = "center";
        playBtn.style.justifyContent = "center";
        playBtn.style.cursor = "pointer";
        playBtn.style.color = "#ffffff";
        playBtn.style.flexShrink = "0";
        playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`;

        const loopBtn = createBtn("🔁 Loop", "Toggle Continuous Loop");
        loopBtn.dataset.active = "true";
        loopBtn.style.background = "rgba(0, 229, 255, 0.2)";
        loopBtn.style.borderColor = "rgba(0, 229, 255, 0.5)";
        loopBtn.style.color = "#00e5ff";

        leftControls.appendChild(prevFrameBtn);
        leftControls.appendChild(playBtn);
        leftControls.appendChild(nextFrameBtn);
        leftControls.appendChild(loopBtn);

        // Right Controls: Speed Toggle, Mute Toggle, Popout
        const rightControls = document.createElement("div");
        rightControls.style.display = "flex";
        rightControls.style.alignItems = "center";
        rightControls.style.gap = "6px";

        const speedBtn = createBtn("1.0x", "Playback Speed (1.0x / 0.5x / 0.25x)", "3px 6px");
        const muteBtn = createBtn("🔇", "Mute / Unmute", "3px 6px");
        const popoutBtn = createBtn("↗", "Open video in new tab", "3px 6px");

        rightControls.appendChild(speedBtn);
        rightControls.appendChild(muteBtn);
        rightControls.appendChild(popoutBtn);

        controls.appendChild(leftControls);
        controls.appendChild(rightControls);

        container.appendChild(header);
        container.appendChild(video);
        container.appendChild(progress);
        container.appendChild(controls);

        let activeFps = 24.0;
        let activeTotalFrames = 0;

        const formatTime = (secs) => {
            if (!secs || isNaN(secs)) return "00:00.00";
            const m = Math.floor(secs / 60);
            const s = Math.floor(secs % 60);
            const ms = Math.floor((secs % 1) * 100);
            return `${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}.${ms < 10 ? '0' : ''}${ms}`;
        };

        const updateDisplay = () => {
            const dur = video.duration || 0;
            const cur = video.currentTime || 0;
            const curFrame = Math.round(cur * activeFps);
            const totFrames = activeTotalFrames || Math.round(dur * activeFps);
            timeEl.textContent = `${formatTime(cur)} / ${formatTime(dur)} (F: ${curFrame}/${totFrames})`;
            if (dur > 0) {
                progress.value = (cur / dur) * 1000;
            }
        };

        playBtn.onclick = (e) => {
            e.stopPropagation();
            if (video.paused) {
                video.play();
                playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>`;
            } else {
                video.pause();
                playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`;
            }
        };

        prevFrameBtn.onclick = (e) => {
            e.stopPropagation();
            video.pause();
            playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`;
            video.currentTime = Math.max(0, video.currentTime - (1.0 / activeFps));
            updateDisplay();
        };

        nextFrameBtn.onclick = (e) => {
            e.stopPropagation();
            video.pause();
            playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`;
            video.currentTime = Math.min(video.duration || 0, video.currentTime + (1.0 / activeFps));
            updateDisplay();
        };

        loopBtn.onclick = (e) => {
            e.stopPropagation();
            video.loop = !video.loop;
            if (video.loop) {
                loopBtn.dataset.active = "true";
                loopBtn.style.background = "rgba(0, 229, 255, 0.2)";
                loopBtn.style.borderColor = "rgba(0, 229, 255, 0.5)";
                loopBtn.style.color = "#00e5ff";
            } else {
                delete loopBtn.dataset.active;
                loopBtn.style.background = "rgba(255, 255, 255, 0.06)";
                loopBtn.style.borderColor = "rgba(255, 255, 255, 0.15)";
                loopBtn.style.color = "#cbd5e1";
            }
        };

        const SPEEDS = [1.0, 0.5, 0.25];
        let speedIdx = 0;
        speedBtn.onclick = (e) => {
            e.stopPropagation();
            speedIdx = (speedIdx + 1) % SPEEDS.length;
            const newSpeed = SPEEDS[speedIdx];
            video.playbackRate = newSpeed;
            speedBtn.textContent = `${newSpeed}x`;
        };

        muteBtn.onclick = (e) => {
            e.stopPropagation();
            video.muted = !video.muted;
            muteBtn.textContent = video.muted ? "🔇" : "🔊";
        };

        popoutBtn.onclick = (e) => {
            e.stopPropagation();
            if (video.src) window.open(video.src, "_blank");
        };

        video.ontimeupdate = () => {
            updateDisplay();
        };

        video.onended = () => {
            if (!video.loop) {
                playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`;
                progress.value = 0;
            }
        };

        progress.oninput = (e) => {
            e.stopPropagation();
            if (video.duration) {
                video.currentTime = (progress.value / 1000) * video.duration;
                updateDisplay();
            }
        };

        widget = node.addDOMWidget("video_player", "VIDEO_PLAYER", container, {
            serialize: false,
            hideOnZoom: false,
        });
        widget.computeSize = function(width) {
            return [width, 275];
        };
        widget.videoEl = video;
        widget.titleEl = titleEl;
        widget.setFps = (fps) => { activeFps = fps || 24.0; };
        widget.setTotalFrames = (tf) => { activeTotalFrames = tf || 0; };
    }

    if (videoData && widget && widget.videoEl) {
        const url = `/view?filename=${encodeURIComponent(videoData.filename)}&subfolder=${encodeURIComponent(videoData.subfolder || "")}&type=${encodeURIComponent(videoData.type || "output")}`;
        widget.videoEl.src = url;
        widget.videoEl.load();
        if (widget.setFps) widget.setFps(videoData.fps);
        if (widget.setTotalFrames) widget.setTotalFrames(videoData.total_frames);
        if (widget.titleEl) widget.titleEl.textContent = videoData.filename;
        if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
    }
}

