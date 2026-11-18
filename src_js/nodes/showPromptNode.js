import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";

let _streamListenersRegistered = false;

function ensureStreamListeners() {
    if (_streamListenersRegistered || typeof api === "undefined" || !api.addEventListener) return;
    _streamListenersRegistered = true;

    api.addEventListener("stoiqo_stream_start", (evt) => {
        const detail = evt.detail || {};
        const nodeId = detail.node_id;
        if (!nodeId || !app.graph) return;
        const node = app.graph.getNodeById(nodeId);
        if (!node) return;
        let tw = node.widgets?.find(w => w.name === "display_text" || w.name === "text" || w.name === "synthesized_prompt");
        if (tw) {
            tw.value = "";
            if (tw.inputEl) tw.inputEl.value = "";
            if (node._batchTexts) {
                node._batchTexts = [""];
                node._batchIndex = 0;
            }
            node.setDirtyCanvas(true);
        }
    });

    api.addEventListener("stoiqo_stream_token", (evt) => {
        const detail = evt.detail || {};
        const nodeId = detail.node_id;
        const token = detail.token;
        if (!nodeId || token === undefined || !app.graph) return;
        const node = app.graph.getNodeById(nodeId);
        if (!node) return;
        let tw = node.widgets?.find(w => w.name === "display_text" || w.name === "text" || w.name === "synthesized_prompt");
        if (tw) {
            tw.value = (tw.value || "") + token;
            if (tw.inputEl) {
                tw.inputEl.value = tw.value;
                tw.inputEl.scrollTop = tw.inputEl.scrollHeight;
            }
            if (node._batchTexts && node._batchTexts.length > 0) {
                node._batchTexts[node._batchIndex || 0] = tw.value;
            }
            node.setDirtyCanvas(true);
        }
    });

    api.addEventListener("stoiqo_stream_complete", (evt) => {
        const detail = evt.detail || {};
        const nodeId = detail.node_id;
        if (!nodeId || !app.graph) return;
        const node = app.graph.getNodeById(nodeId);
        if (node) {
            node.setDirtyCanvas(true, true);
        }
    });
}

function syncDisplayWidgetText(node) {
    const tw = node.widgets?.find(w => w.name === "display_text");
    if (!tw) return;
    let targetText = "";
    if (node._viewAll && node._batchTexts && node._batchTexts.length > 0) {
        targetText = node._batchTexts.map((t, idx) => `=== PROMPT #${idx + 1} ===\n${t}`).join("\n\n");
    } else if (node._batchTexts && node._batchTexts.length > 0) {
        targetText = node._batchTexts[node._batchIndex || 0] || "";
    } else {
        targetText = tw.value || "";
    }
    tw.value = targetText;
    if (tw.inputEl) {
        tw.inputEl.value = targetText;
    }
    node.setDirtyCanvas(true, true);
}

function drawChipButton(ctx, rect, label, bg, border, textColor, icon) {
    ctx.save();
    ctx.fillStyle = bg;
    ctx.strokeStyle = border;
    ctx.lineWidth = 1;
    ctx.beginPath();
    if (ctx.roundRect) {
        ctx.roundRect(rect.x, rect.y, rect.w, rect.h, 4);
    } else {
        ctx.rect(rect.x, rect.y, rect.w, rect.h);
    }
    ctx.fill();
    ctx.stroke();

    ctx.font = "bold 10px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
    ctx.fillStyle = textColor;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const text = (icon ? icon + " " : "") + label;
    ctx.fillText(text, rect.x + rect.w / 2, rect.y + rect.h / 2);
    ctx.restore();
}

function createPromptViewerWidget(node) {
    const widget = {
        type: "STOIQO_PROMPT_VIEWER",
        name: "prompt_viewer_hud",
        serialize: false,
        options: { serialize: false },
        _feedbackText: null,
        _feedbackAllText: null,
        _rects: {},

        computeSize(width) {
            const isBatch = node._batchTexts && node._batchTexts.length > 1;
            return [width, isBatch ? 66 : 40];
        },

        draw(ctx, node, width, y, height) {
            const padX = 10;
            const cardW = width - padX * 2;
            const isBatch = node._batchTexts && node._batchTexts.length > 1;
            const cardH = isBatch ? 64 : 38;

            this._rects = {};

            ctx.save();
            // Background card
            ctx.fillStyle = "rgba(15, 23, 42, 0.88)";
            ctx.strokeStyle = "rgba(148, 163, 184, 0.22)";
            ctx.lineWidth = 1;
            ctx.beginPath();
            if (ctx.roundRect) {
                ctx.roundRect(padX, y, cardW, cardH, 6);
            } else {
                ctx.rect(padX, y, cardW, cardH);
            }
            ctx.fill();
            ctx.stroke();

            // Calculate active text stats
            const currentText = (node._batchTexts && node._batchTexts.length > 0 && !node._viewAll)
                ? (node._batchTexts[node._batchIndex || 0] || "")
                : (node.widgets?.find(w => w.name === "display_text")?.value || "");

            const words = currentText.trim() ? currentText.trim().split(/\s+/).length : 0;
            const chars = currentText.length;
            const estTokens = words > 0 ? Math.max(1, Math.round(words * 1.33)) : 0;

            let rowY = y + 6;

            if (isBatch) {
                // ROW 1: Batch Pagination Bar
                const total = node._batchTexts.length;
                const idx = (node._batchIndex || 0) + 1;

                // Prev button
                const prevRect = { x: padX + 8, y: rowY, w: 26, h: 22 };
                this._rects.prev = prevRect;
                drawChipButton(ctx, prevRect, "◀", "rgba(30, 41, 59, 0.85)", "rgba(148, 163, 184, 0.35)", "#e2e8f0");

                // Badge Item Counter
                const badgeLabel = node._viewAll ? `📑 Batch View (${total})` : `Item ${idx} of ${total}`;
                const badgeRect = { x: padX + 38, y: rowY, w: 104, h: 22 };
                drawChipButton(
                    ctx,
                    badgeRect,
                    badgeLabel,
                    node._viewAll ? "rgba(41, 151, 255, 0.25)" : "rgba(30, 41, 59, 0.6)",
                    node._viewAll ? "rgba(41, 151, 255, 0.45)" : "rgba(148, 163, 184, 0.25)",
                    node._viewAll ? "#2997ff" : "#94a3b8"
                );

                // Next button
                const nextRect = { x: padX + 146, y: rowY, w: 26, h: 22 };
                this._rects.next = nextRect;
                drawChipButton(ctx, nextRect, "▶", "rgba(30, 41, 59, 0.85)", "rgba(148, 163, 184, 0.35)", "#e2e8f0");

                // Toggle View All / Single
                const toggleRect = { x: padX + 178, y: rowY, w: 78, h: 22 };
                this._rects.toggle = toggleRect;
                drawChipButton(
                    ctx,
                    toggleRect,
                    node._viewAll ? "📄 Singolo" : "📑 Tutti",
                    "rgba(30, 41, 59, 0.85)",
                    "rgba(148, 163, 184, 0.35)",
                    "#cbd5e1"
                );

                rowY += 28;
            }

            // ROW 2 (or single ROW): Stats & Copy Button
            ctx.font = "11px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
            ctx.fillStyle = "#94a3b8";
            ctx.textAlign = "left";
            ctx.textBaseline = "middle";

            const statsText = node._viewAll
                ? `Totale: ${chars} car. • ${words} par.`
                : `${chars} car. • ${words} par. • ~${estTokens} tok`;
            ctx.fillText(statsText, padX + 10, rowY + 12);

            // Copy button on right side
            const copyLabel = this._feedbackText || (isBatch && node._viewAll ? "Copia Tutti" : "Copia Prompt");
            const copyW = this._feedbackText ? 110 : (isBatch && node._viewAll ? 85 : 95);
            const copyRect = { x: padX + cardW - copyW - 8, y: rowY + 1, w: copyW, h: 22 };
            this._rects.copy = copyRect;

            const isCopied = !!this._feedbackText;
            drawChipButton(
                ctx,
                copyRect,
                copyLabel,
                isCopied ? "rgba(16, 185, 129, 0.3)" : "rgba(30, 41, 59, 0.9)",
                isCopied ? "rgba(52, 211, 153, 0.6)" : "rgba(148, 163, 184, 0.4)",
                isCopied ? "#34d399" : "#f1f5f9",
                isCopied ? "✓" : "📋"
            );

            // If batch and in single view, add optional "Copia Tutti" button
            if (isBatch && !node._viewAll) {
                const copyAllLabel = this._feedbackAllText || `Tutti (${node._batchTexts.length})`;
                const copyAllW = this._feedbackAllText ? 95 : 68;
                const copyAllRect = { x: copyRect.x - copyAllW - 6, y: rowY + 1, w: copyAllW, h: 22 };
                this._rects.copyAll = copyAllRect;

                const isAllCopied = !!this._feedbackAllText;
                drawChipButton(
                    ctx,
                    copyAllRect,
                    copyAllLabel,
                    isAllCopied ? "rgba(16, 185, 129, 0.3)" : "rgba(30, 41, 59, 0.75)",
                    isAllCopied ? "rgba(52, 211, 153, 0.6)" : "rgba(148, 163, 184, 0.3)",
                    isAllCopied ? "#34d399" : "#cbd5e1",
                    isAllCopied ? "✓" : "📑"
                );
            }

            ctx.restore();
        },

        mouse(event, pos, node) {
            if (event.type !== "pointerdown" && event.type !== "mousedown") return false;
            const [clickX, clickY] = pos;

            const isInside = (r) => r && clickX >= r.x && clickX <= r.x + r.w && clickY >= r.y && clickY <= r.y + r.h;

            if (isInside(this._rects.prev)) {
                const total = node._batchTexts?.length || 1;
                node._batchIndex = ((node._batchIndex || 0) - 1 + total) % total;
                node._viewAll = false;
                syncDisplayWidgetText(node);
                return true;
            }

            if (isInside(this._rects.next)) {
                const total = node._batchTexts?.length || 1;
                node._batchIndex = ((node._batchIndex || 0) + 1) % total;
                node._viewAll = false;
                syncDisplayWidgetText(node);
                return true;
            }

            if (isInside(this._rects.toggle)) {
                node._viewAll = !node._viewAll;
                syncDisplayWidgetText(node);
                return true;
            }

            if (isInside(this._rects.copy)) {
                const tw = node.widgets?.find(w => w.name === "display_text");
                const textToCopy = tw?.value || "";
                if (navigator.clipboard && textToCopy) {
                    navigator.clipboard.writeText(textToCopy);
                    this._feedbackText = "Copiato!";
                    node.setDirtyCanvas(true);
                    setTimeout(() => {
                        this._feedbackText = null;
                        node.setDirtyCanvas(true);
                    }, 1800);
                }
                return true;
            }

            if (isInside(this._rects.copyAll)) {
                if (node._batchTexts && node._batchTexts.length > 0 && navigator.clipboard) {
                    const allText = node._batchTexts.map((t, idx) => `=== PROMPT #${idx + 1} ===\n${t}`).join("\n\n");
                    navigator.clipboard.writeText(allText);
                    this._feedbackAllText = "Copiati!";
                    node.setDirtyCanvas(true);
                    setTimeout(() => {
                        this._feedbackAllText = null;
                        node.setDirtyCanvas(true);
                    }, 1800);
                }
                return true;
            }

            return false;
        },
    };

    return widget;
}

export function setupShowPromptNode(nodeType, nodeData, app) {
    ensureStreamListeners();

    const showPromptTargetNames = [
        "StoiqoShowPromptNode",
        "[STOIQO] Show Prompt",
    ];

    if (showPromptTargetNames.includes(nodeData.name)) {
        const SHOW_MIN_WIDTH = 460;
        const SHOW_MIN_HEIGHT = 230;

        function configureShowPromptNode(node) {
            if (!node) return;

            // Restore native comfy colors
            if (node.bgcolor === "#0e1218" || node.bgcolor === "#0b1411") delete node.bgcolor;
            if (node.color === "#18202c" || node.color === "#14251f") delete node.color;

            if (node.size) {
                if (node.size[0] < SHOW_MIN_WIDTH) node.size[0] = SHOW_MIN_WIDTH;
                if (node.size[1] < SHOW_MIN_HEIGHT) node.size[1] = SHOW_MIN_HEIGHT;
            }

            node.widgets = node.widgets || [];

            // 1. Ensure multiline display text widget exists
            let textWidget = node.widgets.find(w => w.name === "display_text");
            if (!textWidget) {
                if (typeof ComfyWidgets !== "undefined" && ComfyWidgets["STRING"]) {
                    textWidget = ComfyWidgets["STRING"](
                        node,
                        "display_text",
                        ["STRING", { multiline: true }],
                        app
                    ).widget;
                } else {
                    textWidget = node.addWidget(
                        "customtext",
                        "display_text",
                        "",
                        function() {},
                        { multiline: true }
                    );
                }
            }

            if (textWidget) {
                textWidget.name = "display_text";
                textWidget.serialize = false;
                textWidget.options = textWidget.options || {};
                textWidget.options.serialize = false;

                const styleInput = (el) => {
                    if (!el) return;
                    el.readOnly = false;
                    el.placeholder = "Waiting for generated prompt or input text...";
                    el.style.boxSizing = "border-box";
                    el.style.opacity = "0.95";
                    el.style.fontSize = "12px";
                    el.style.lineHeight = "1.5";
                    el.style.fontFamily = "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace";
                    el.style.resize = "vertical";

                    el.oninput = (e) => {
                        if (node._batchTexts && node._batchTexts.length > 0 && !node._viewAll) {
                            node._batchTexts[node._batchIndex || 0] = e.target.value;
                        }
                        node.setDirtyCanvas(true);
                    };
                };

                if (textWidget.inputEl) {
                    styleInput(textWidget.inputEl);
                } else {
                    let rawInputEl = null;
                    Object.defineProperty(textWidget, "inputEl", {
                        configurable: true,
                        enumerable: true,
                        get() { return rawInputEl; },
                        set(val) {
                            rawInputEl = val;
                            styleInput(val);
                        }
                    });
                }
            }

            // Remove legacy copy buttons if present
            const legacyBtnIdx = node.widgets.findIndex(w => w._isCopyButton || w.name === "📋 Copy Prompt to Clipboard");
            if (legacyBtnIdx !== -1) {
                node.widgets.splice(legacyBtnIdx, 1);
            }

            // 2. Attach or reposition the interactive Prompt Viewer Widget at index 0 (top of node)
            const existingViewers = node.widgets.filter(w => w.name === "prompt_viewer_hud");
            for (const extra of existingViewers.slice(1)) {
                node.widgets.splice(node.widgets.indexOf(extra), 1);
            }
            let viewerWidget = existingViewers[0];
            if (!viewerWidget) {
                viewerWidget = createPromptViewerWidget(node);
                node.widgets.unshift(viewerWidget);
            } else {
                const curIdx = node.widgets.indexOf(viewerWidget);
                if (curIdx > 0) {
                    node.widgets.splice(curIdx, 1);
                    node.widgets.unshift(viewerWidget);
                }
            }

            if (typeof node.computeSize === "function") {
                const sz = node.computeSize();
                const w = Math.max(node.size ? node.size[0] : SHOW_MIN_WIDTH, SHOW_MIN_WIDTH, Math.ceil(sz[0] || 0));
                const h = Math.max(node.size ? node.size[1] : SHOW_MIN_HEIGHT, SHOW_MIN_HEIGHT, Math.ceil(sz[1] || 0));
                if (typeof node.setSize === "function") {
                    node.setSize([w, h]);
                } else {
                    node.size = [w, h];
                }
            }

            node.setDirtyCanvas(true, true);
        }

        const origShowCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function() {
            if (origShowCreated) origShowCreated.apply(this, arguments);
            this._batchTexts = [];
            this._batchIndex = 0;
            this._viewAll = false;
            configureShowPromptNode(this);
        };

        const origShowConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function() {
            if (origShowConfigure) origShowConfigure.apply(this, arguments);
            const tw = this.widgets?.find(w => w.name === "display_text");
            if (tw && tw.value && (!this._batchTexts || this._batchTexts.length === 0)) {
                this._batchTexts = [tw.value];
                this._batchIndex = 0;
                this._viewAll = false;
            }
            configureShowPromptNode(this);
        };

        const origShowExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function(message) {
            if (origShowExecuted) origShowExecuted.apply(this, arguments);
            if (message && message.text) {
                let texts = [];
                if (Array.isArray(message.text)) {
                    texts = message.text.map(t => String(t || ""));
                } else {
                    texts = [String(message.text || "")];
                }
                this._batchTexts = texts;
                this._batchIndex = 0;
                this._viewAll = false;
                syncDisplayWidgetText(this);
            }
        };
    }
}
