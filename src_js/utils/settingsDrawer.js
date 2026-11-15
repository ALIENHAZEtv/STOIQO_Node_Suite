/**
 * [STOIQO] Progressive Disclosure (`⚙` Settings Drawer) & Dynamic Conditional Visibility
 * Keeps all ComfyUI nodes compact on the canvas by hiding advanced parameters behind
 * an interactive `⚙ Impostazioni Avanzate` toggle bar and evaluating conditional rules.
 */

const DRAWER_WIDGET_NAME = "_stoiqo_settings_drawer";

const PROMPT_PRESET_VALUES = {
    "Balanced Synthesizer (Recommended)": { temperature: 0.65, max_new_tokens: 1024, top_p: 0.90, top_k: 50, repetition_penalty: 1.15 },
    "Maximum Creativity (Wild Ideation)": { temperature: 0.95, max_new_tokens: 1536, top_p: 0.95, top_k: 80, repetition_penalty: 1.10 },
    "Scientific / Accurate Visual Description": { temperature: 0.20, max_new_tokens: 768, top_p: 0.80, top_k: 30, repetition_penalty: 1.20 },
    "Synthetic Captioning for LoRA / Training": { temperature: 0.35, max_new_tokens: 512, top_p: 0.85, top_k: 40, repetition_penalty: 1.15 },
    "Deterministic / Exact Logic (Greedy)": { temperature: 0.0, max_new_tokens: 512, top_p: 0.0, top_k: 1, repetition_penalty: 1.20 },
    "Cinematic Storyteller": { temperature: 0.75, max_new_tokens: 1280, top_p: 0.92, top_k: 60, repetition_penalty: 1.12 },
};

function getVal(node, name) {
    const w = node?.widgets?.find(x => x.name === name);
    return w ? w.value : undefined;
}

/**
 * Per-node progressive disclosure rules:
 * - `advanced`: list of widget names tucked inside the `⚙` drawer.
 * - `conditions`: map of widgetName -> (node) => boolean (evaluated whether in core or inside open `⚙`).
 * - `drawerWhen`: optional (node) => boolean to hide the entire `⚙` button when not applicable.
 * - `alwaysHidden`: widgets controlled directly by custom canvas UI.
 */
export const NODE_UX_SPECS = {
    StoiqoPromptGeneratorNode: {
        label: "LLM & Multi-Image Settings",
        advanced: [
            "preset",
            "fusion_mode",
            "system_prompt",
            "custom_system_prompt",
            "negative_prompt_prefix",
            "temperature",
            "max_new_tokens",
            "top_p",
            "top_k",
            "repetition_penalty",
        ],
        conditions: {
            custom_system_prompt: (node) => String(getVal(node, "system_prompt") || "").includes("Custom"),
        },
        onWidgetChange: (node, name, val) => {
            if (name === "preset" && PROMPT_PRESET_VALUES[val]) {
                const pv = PROMPT_PRESET_VALUES[val];
                for (const [k, v] of Object.entries(pv)) {
                    const tw = node.widgets?.find(w => w.name === k);
                    if (tw) {
                        tw.value = v;
                        if (tw.inputEl) tw.inputEl.value = String(v);
                    }
                }
            }
        },
    },

    StoiqoDatasetWriterNode: {
        label: "Dataset, Tag & Deduplication Options",
        advanced: [
            "blacklist_tags",
            "tag_separator",
            "shuffle_tags",
            "keep_tokens",
            "save_txt",
            "save_json_metadata",
            "use_original_filename",
            "fallback_prefix",
            "deduplicate_images",
            "similarity_threshold",
            "seed",
        ],
        conditions: {
            image_format: (node) => Boolean(getVal(node, "save_image")),
            keep_tokens: (node) => Boolean(getVal(node, "shuffle_tags")),
            fallback_prefix: (node) => !Boolean(getVal(node, "use_original_filename")),
            similarity_threshold: (node) => Boolean(getVal(node, "deduplicate_images")),
        },
    },

    StoiqoSmartFolderImageIterator: {
        label: "Folder Filters & Batch Options",
        advanced: [
            "loop_folder",
            "recursive",
            "skip_captioned",
            "caption_extension",
        ],
        conditions: {
            index: (node) => String(getVal(node, "load_mode") || "").startsWith("Single"),
            max_batch_images: (node) => String(getVal(node, "load_mode") || "").startsWith("Batch"),
            seed: (node) => String(getVal(node, "iteration_mode") || "").includes("Random"),
            loop_folder: (node) => String(getVal(node, "load_mode") || "").startsWith("Single"),
            caption_extension: (node) => Boolean(getVal(node, "skip_captioned")),
        },
    },

    StoiqoSeedControllerNode: {
        label: "Seed Variance & VAE Multiple Options",
        advanced: [
            "multiple_of",
            "variance_strength",
            "variance_seed",
            "seed_prefix",
        ],
        conditions: {
            custom_width: (node) => String(getVal(node, "aspect_ratio") || "").includes("Custom"),
            custom_height: (node) => String(getVal(node, "aspect_ratio") || "").includes("Custom"),
        },
    },

    StoiqoTurboSamplerNode: {
        label: "Sampler & Denoise Options",
        advanced: [
            "sampler_name",
            "scheduler",
            "denoise",
        ],
    },

    StoiqoWatermarkNode: {
        label: "Border, Chroma Key & Text Color Options",
        advanced: [
            "margin_percent",
            "text_color",
            "remove_bg_mode",
            "chroma_tolerance",
            "feather_radius",
        ],
        conditions: {
            custom_scale: (node) => String(getVal(node, "scale_mode") || "").includes("Custom"),
            chroma_tolerance: (node) => !String(getVal(node, "remove_bg_mode") || "").startsWith("None"),
        },
    },

    StoiqoTextConcatenateNode: {
        label: "Template, Prefix/Suffix & Tag Sanitization",
        advanced: [
            "template",
            "prefix",
            "suffix",
            "deduplicate_tags",
            "clean_whitespace",
            "convert_underscores",
            "skip_empty",
        ],
    },

    StoiqoMusicPromptEngineNode: {
        label: "AI Producer & Sampling Settings",
        advanced: [
            "system_prompt",
            "custom_system_prompt",
            "custom_directives",
            "seed",
            "temperature",
            "repetition_penalty",
            "max_new_tokens",
        ],
        conditions: {
            custom_system_prompt: (node) => String(getVal(node, "system_prompt") || "").includes("Custom"),
        },
    },

    StoiqoCharacterMemoryNode: {
        label: "Lorebook Options, Constraints & JSON Export",
        advanced: [
            "injection_mode",
            "personality_vibe",
            "negative_constraints",
            "user_prompt",
            "save_profile_as",
            "custom_json_data",
        ],
    },

    StoiqoSpatialCropperNode: {
        label: "Manual Coordinates & Mask Options",
        advanced: [
            "manual_bbox",
            "invert_mask",
            "target_megapixel",
            "coord_order",
        ],
    },

    StoiqoInpaintStitcherNode: {
        label: "BBox Options, Padding & Beauty Polish",
        advanced: [
            "bbox_info",
            "crop_padding_percent",
            "skin_smoothing",
            "detail_clarity",
        ],
        conditions: {
            color_match_strength: (node) => Boolean(getVal(node, "color_match")),
        },
    },

    StoiqoFrequencySeparationNode: {
        label: "High-Pass Options & Soft-Knee Limiter",
        advanced: [
            "texture_boost",
            "high_pass_mode",
            "soft_knee_limiter",
            "split_meta",
        ],
    },

    StoiqoProImageSaverNode: {
        label: "Folder, Metadata & Privacy Options",
        advanced: [
            "quality",
            "subfolder",
            "sidecar_metadata",
            "save_workflow",
            "privacy_mode",
        ],
    },

    StoiqoVideoSaverNode: {
        label: "Quality, Folder & Video Sidecars",
        advanced: [
            "quality",
            "subfolder",
            "motion_prompt",
            "sidecar_metadata",
        ],
    },

    StoiqoAudioSaverNode: {
        label: "ID3 Tags, Lyrics & Audio Metadata",
        advanced: [
            "subfolder",
            "genre",
            "bpm",
            "style",
            "lyrics",
            "sidecar_metadata",
        ],
    },

    StoiqoImageCompareNode: {
        alwaysHidden: ["initial_mode"],
        label: "Heatmap Options & Diff Mask Threshold",
        advanced: [
            "heatmap_colormap",
            "diff_gain",
            "mask_threshold",
        ],
    },

    StoiqoImageLoaderNode: {
        label: "Batch Aspect Ratio Options",
        alwaysHidden: ["active_focus"],
        advanced: ["fit_mode"],
    },

    StoiqoVideoEnhancerNode: {
        label: "Deflicker Options & Motion Curve",
        advanced: [
            "window_size",
            "luminance_tolerance",
            "stabilization_strength",
            "motion_smoothness",
            "blend_curve",
        ],
        conditions: {
            window_size: (node) => Boolean(getVal(node, "enable_deflicker")),
            luminance_tolerance: (node) => Boolean(getVal(node, "enable_deflicker")),
            stabilization_strength: (node) => Boolean(getVal(node, "enable_deflicker")),
            motion_smoothness: (node) => !String(getVal(node, "fps_multiplier") || "").startsWith("1x"),
            blend_curve: (node) => !String(getVal(node, "fps_multiplier") || "").startsWith("1x"),
        },
    },
};

function setWidgetVisibility(w, visible) {
    if (!w) return;
    if (!w._stoiqoSavedOrig) {
        w._stoiqoSavedOrig = {
            computeSize: w.computeSize,
            draw: w.draw,
        };
    }

    if (visible) {
        w.hidden = false;
        if (w._stoiqoSavedOrig.computeSize) {
            w.computeSize = w._stoiqoSavedOrig.computeSize;
        } else {
            delete w.computeSize;
        }
        if (w._stoiqoSavedOrig.draw) {
            w.draw = w._stoiqoSavedOrig.draw;
        } else {
            delete w.draw;
        }
        if (w.inputEl) {
            w.inputEl.hidden = false;
            w.inputEl.style.display = "";
        }
    } else {
        w.hidden = true;
        w.computeSize = () => [0, -4];
        w.draw = () => {};
        if (w.inputEl) {
            w.inputEl.hidden = true;
            w.inputEl.style.display = "none";
        }
    }
}

class StoiqoSettingsDrawerWidget {
    constructor(node, spec) {
        this.type = "custom";
        this.name = DRAWER_WIDGET_NAME;
        this.node = node;
        this.spec = spec;
        this.serialize = false;
        this.options = { serialize: false };
        this.lastClick = 0;
        this.hitBox = null;
    }

    get value() { return ""; }
    set value(_v) {}
    serializeValue() { return undefined; }

    isVisible() {
        if (this.spec.drawerWhen && !this.spec.drawerWhen(this.node)) {
            return false;
        }
        return Array.isArray(this.spec.advanced) && this.spec.advanced.length > 0;
    }

    computeSize(width) {
        if (!this.isVisible()) return [0, -4];
        return [width, 28];
    }

    draw(ctx, node, width, y) {
        if (!this.isVisible()) {
            this.hitBox = null;
            return;
        }
        const nodeW = (node && node.size) ? node.size[0] : width;
        const padX = 10;
        const barX = padX;
        const barY = y + 2;
        const barW = nodeW - padX * 2;
        const barH = 22;
        const expanded = Boolean(node._stoiqoAdvExpanded);

        this.hitBox = { x: barX, y: barY, w: barW, h: barH };

        ctx.save();
        ctx.beginPath();
        if (ctx.roundRect) {
            ctx.roundRect(barX, barY, barW, barH, 5);
        } else {
            ctx.rect(barX, barY, barW, barH);
        }
        ctx.fillStyle = expanded ? "rgba(41, 151, 255, 0.14)" : "rgba(255, 255, 255, 0.04)";
        ctx.fill();
        ctx.strokeStyle = expanded ? "rgba(41, 151, 255, 0.45)" : "rgba(255, 255, 255, 0.09)";
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.font = "600 10.5px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
        ctx.fillStyle = expanded ? "#58b0ff" : "#98a2b3";
        ctx.textAlign = "left";
        ctx.textBaseline = "middle";
        const label = this.spec.label || "Advanced Settings";
        ctx.fillText(`⚙  ${label}`, barX + 10, barY + barH / 2);

        const advList = this.spec.advanced || [];
        const count = advList.length;
        let modCount = 0;
        if (node && node.widgets) {
            for (const name of advList) {
                const w = node.widgets.find(x => x.name === name);
                if (w && w._stoiqoDefaultVal !== undefined && String(w.value ?? "") !== String(w._stoiqoDefaultVal ?? "")) {
                    modCount++;
                }
            }
        }

        const rightText = expanded ? "Hide ▴" : `Show (${count}) ▾`;
        ctx.font = "500 9.5px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
        ctx.fillStyle = expanded ? "#58b0ff" : "#667085";
        ctx.textAlign = "right";
        ctx.fillText(rightText, barX + barW - 10, barY + barH / 2);

        if (!expanded && modCount > 0) {
            const rightW = ctx.measureText(rightText).width;
            ctx.font = "600 9.5px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
            ctx.fillStyle = "#ff9f0a";
            ctx.fillText(`● ${modCount} edited`, barX + barW - 10 - rightW - 8, barY + barH / 2);
        }
        ctx.restore();
    }

    mouse(event, pos, node) {
        if (!this.isVisible() || !this.hitBox) return false;
        if (!event || (event.type !== "pointerdown" && event.type !== "mousedown")) return false;
        if (!pos) return false;
        const now = performance.now();
        if (now - this.lastClick < 150) return true;
        const [mx, my] = pos;
        const b = this.hitBox;
        if (mx >= b.x && mx <= b.x + b.w && my >= b.y && my <= b.y + b.h) {
            this.lastClick = now;
            node._stoiqoAdvExpanded = !Boolean(node._stoiqoAdvExpanded);
            if (node._stoiqoApplyUX) {
                node._stoiqoApplyUX(true);
            }
            return true;
        }
        return false;
    }
}

export function applyNodeUXSpec(node, spec) {
    if (!node || !node.widgets || !spec) return;

    // 1. Deduplicate any extra drawer widgets
    const existingDrawers = node.widgets.filter(w => w.name === DRAWER_WIDGET_NAME);
    for (const extra of existingDrawers.slice(1)) {
        node.widgets.splice(node.widgets.indexOf(extra), 1);
    }

    // 2. Ensure drawer widget exists if node has advanced settings
    let drawer = node.widgets.find(w => w.name === DRAWER_WIDGET_NAME);
    if (!drawer && spec.advanced && spec.advanced.length > 0) {
        drawer = new StoiqoSettingsDrawerWidget(node, spec);
        const firstAdvIdx = node.widgets.findIndex(w => spec.advanced.includes(w.name));
        if (firstAdvIdx !== -1) {
            node.widgets.splice(firstAdvIdx, 0, drawer);
        } else {
            node.widgets.push(drawer);
        }
    }

    const advSet = new Set(spec.advanced || []);
    const alwaysHiddenSet = new Set(spec.alwaysHidden || []);
    const conditions = spec.conditions || {};

    const refreshUX = (resizeHeight = false) => {
        const expanded = Boolean(node._stoiqoAdvExpanded);
        const drawerAllowed = !spec.drawerWhen || spec.drawerWhen(node);

        for (const w of node.widgets) {
            if (!w || w.name === DRAWER_WIDGET_NAME) continue;

            if (alwaysHiddenSet.has(w.name)) {
                setWidgetVisibility(w, false);
                continue;
            }

            const inAdv = advSet.has(w.name);
            const condFn = conditions[w.name];
            const condOk = condFn ? Boolean(condFn(node)) : true;

            if (inAdv) {
                setWidgetVisibility(w, drawerAllowed && expanded && condOk);
            } else if (condFn) {
                setWidgetVisibility(w, condOk);
            }
        }

        if (typeof node.computeSize === "function") {
            const computed = node.computeSize();
            if (resizeHeight) {
                node.size[1] = Math.max(60, Math.ceil(computed[1]));
            } else {
                node.size[1] = Math.max(node.size[1] || 60, Math.ceil(computed[1]));
            }
        }
        node.setDirtyCanvas?.(true, true);
    };

    node._stoiqoApplyUX = refreshUX;

    // 3. Hook widget callbacks to re-evaluate conditions dynamically & capture defaults
    for (const w of node.widgets) {
        if (!w || w.name === DRAWER_WIDGET_NAME) continue;
        if (w._stoiqoDefaultVal === undefined) {
            w._stoiqoDefaultVal = (w.options && w.options.default !== undefined) ? w.options.default : w.value;
        }
        if (w._stoiqoUXHooked) continue;
        w._stoiqoUXHooked = true;
        const origCb = w.callback;
        w.callback = function (val) {
            if (origCb) origCb.apply(this, arguments);
            if (spec.onWidgetChange) {
                spec.onWidgetChange(node, w.name, val);
            }
            refreshUX(true);
        };
    }

    refreshUX(true);
}

export function sanitizeNodeWidgetValues(node, info) {
    if (!node || !node.widgets) return;

    // A. If named restoration dictionary is available from workflow, restore by exact key first
    if (info && info.widgets_values_named && typeof info.widgets_values_named === "object") {
        for (const w of node.widgets) {
            if (!w || w.name === DRAWER_WIDGET_NAME || w.serialize === false) continue;
            const namedVal = info.widgets_values_named[w.name];
            if (namedVal !== undefined && namedVal !== null && namedVal !== "") {
                w.value = namedVal;
                if (w.inputEl) w.inputEl.value = String(namedVal);
            }
        }
    }

    // B. Deep invariant sanitation & validation across all widget types
    for (const w of node.widgets) {
        if (!w || w.name === DRAWER_WIDGET_NAME || w.serialize === false) continue;

        // Specific named heuristics for corrupted shifted parameters
        if (w.name === "subfolder") {
            if (typeof w.value === "number" || w.value === 90 || w.value === "90" || (typeof w.value === "string" && !isNaN(Number(w.value.trim())) && w.value.trim() !== "") || w.value === "%data") {
                w.value = "StoiqoCreations/%date%";
                if (w.inputEl) w.inputEl.value = w.value;
            }
        }

        if (w.name === "sidecar_metadata") {
            const valid = ["None", "Both (.json + .txt)", "JSON (.json)", "TXT Caption (.txt)"];
            if (!valid.includes(w.value)) {
                w.value = "None";
                if (w.inputEl) w.inputEl.value = "None";
            }
        }

        if (w.name === "text_watermark") {
            if (w.value === "Normal (Alpha)" || w.value === "Normal" || w.value === "Screen" || w.value === "Multiply") {
                w.value = "STOIQO";
                if (w.inputEl) w.inputEl.value = "STOIQO";
            }
        }

        // 1. Combo validation
        if (w.type === "combo" && w.options && Array.isArray(w.options.values)) {
            if (!w.options.values.includes(w.value)) {
                let def = (w.options.default !== undefined && w.options.values.includes(w.options.default))
                    ? w.options.default
                    : (w._stoiqoDefaultVal !== undefined && w.options.values.includes(w._stoiqoDefaultVal)
                        ? w._stoiqoDefaultVal
                        : w.options.values[0]);

                // Node-specific defaults for common combos
                if (w.name === "sampler_name" && w.options.values.includes("euler")) def = "euler";
                if (w.name === "scheduler" && w.options.values.includes("beta")) def = "beta";
                if (w.name === "sidecar_metadata" && w.options.values.includes("None")) def = "None";
                if (w.name === "preset" && w.options.values.includes("Balanced Synthesizer (Recommended)")) def = "Balanced Synthesizer (Recommended)";
                if (w.name === "fusion_mode" && w.options.values.includes("Auto (Fuse 2-4 images, Batch if >4)")) def = "Auto (Fuse 2-4 images, Batch if >4)";
                if (w.name === "system_prompt" && w.options.values.includes("Auto-Detect / Balanced")) def = "Auto-Detect / Balanced";
                if (w.name === "deduplicate_tags" && w.options.values.includes("None")) def = "None";
                if (w.name === "format" && w.options.values.includes("PNG (Lossless)")) def = "PNG (Lossless)";

                w.value = def;
                if (w.inputEl) w.inputEl.value = String(def);
            }
        }

        // 2. Numeric validation (FLOAT / INT)
        if (w.type === "number" || (w.options && (w.options.min !== undefined || w.options.max !== undefined || w.options.step !== undefined))) {
            let num = Number(w.value);
            const isInt = w.options && w.options.step && Number.isInteger(w.options.step) && (w.options.round === undefined || w.options.round === 0);

            if (typeof w.value !== "number" || isNaN(num) || String(w.value).trim() === "") {
                if (w.name === "temperature") num = 0.65;
                else if (w.name === "max_new_tokens") num = 1024;
                else if (w.name === "top_p") num = 0.90;
                else if (w.name === "top_k") num = 50;
                else if (w.name === "repetition_penalty") num = 1.15;
                else if (w.name === "denoise") num = 1.0;
                else if (w.name === "variance_strength") num = 0.0;
                else if (w.name === "quality") num = 90;
                else {
                    num = (w.options && w.options.default !== undefined)
                        ? Number(w.options.default)
                        : (w._stoiqoDefaultVal !== undefined ? Number(w._stoiqoDefaultVal) : 0);
                }
            }

            // Named limits check
            if (w.name === "denoise" && num > 1.0) num = 1.0;
            if (w.name === "variance_strength" && num > 1.0) num = 0.0;
            if (w.name === "top_p" && num > 1.0) num = 0.90;
            if (w.name === "repetition_penalty" && (num < 1.0 || num > 2.0)) num = 1.15;
            if (w.name === "max_new_tokens" && (num < 64 || num > 4096)) num = 1024;
            if (w.name === "top_k" && (num < 1 || num > 100)) num = 50;
            if (w.name === "quality" && (num < 1 || num > 100)) num = 90;
            if (w.name === "opacity" && num <= 0.05) num = 0.85;
            if (w.name === "custom_scale" && num < 0.01) num = 0.125;

            if (w.options) {
                if (w.options.min !== undefined && num < w.options.min) {
                    num = (w.options.default !== undefined && w.options.default >= w.options.min) ? w.options.default : w.options.min;
                }
                if (w.options.max !== undefined && num > w.options.max) {
                    num = (w.options.default !== undefined && w.options.default <= w.options.max) ? w.options.default : w.options.max;
                }
            }
            w.value = isInt ? Math.round(num) : num;
            if (w.inputEl) w.inputEl.value = String(w.value);
        }

        // 3. Boolean / Toggle validation
        if (w.type === "toggle" || typeof w.value === "boolean") {
            if (typeof w.value !== "boolean") {
                if (w.name === "save_workflow") w.value = true;
                else if (w.name === "privacy_mode") w.value = false;
                else w.value = (w.options && w.options.default !== undefined) ? Boolean(w.options.default) : Boolean(w.value);
            }
        }
    }
}

export function setupSettingsDrawers(nodeType, nodeData) {
    const spec = NODE_UX_SPECS[nodeData.name];
    if (!spec) return;

    const origCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
        if (origCreated) origCreated.apply(this, arguments);
        const node = this;
        if (node.widgets) {
            for (const w of node.widgets) {
                if (w && w._stoiqoDefaultVal === undefined) {
                    w._stoiqoDefaultVal = (w.options && w.options.default !== undefined) ? w.options.default : w.value;
                }
            }
        }
        applyNodeUXSpec(node, spec);
    };

    const origConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function (info) {
        if (origConfigure) origConfigure.apply(this, arguments);
        const node = this;
        applyNodeUXSpec(node, spec);
        sanitizeNodeWidgetValues(node, info);
    };

    const origSerialize = nodeType.prototype.serialize;
    nodeType.prototype.serialize = function () {
        sanitizeNodeWidgetValues(this);
        return origSerialize ? origSerialize.apply(this, arguments) : {};
    };
}
