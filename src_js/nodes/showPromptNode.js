import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";
import { StoiqoSectionDividerWidget, currentDownloadProgress } from "../utils/core.js";

export function setupShowPromptNode(nodeType, nodeData, app) {
        // 2. SHOW PROMPT NODE ENHANCEMENTS
        // ══════════════════════════════════════════════════════════════════════
        const showPromptTargetNames = [
            "StoiqoShowPromptNode",
            "QwenVLTextDisplayNode",
            "[STOIQO] Show Prompt",
            "[STOIQO] Show Prompt (Legacy)",
        ];
        if (showPromptTargetNames.includes(nodeData.name)) {
            const SHOW_MIN_WIDTH = 460;
            const SHOW_MIN_HEIGHT = 220;

            function setupShowPromptNode(node) {
                if (!node) return;

                // Clean up any previously hardcoded background/color to restore native ComfyUI defaults
                if (node.bgcolor === "#0e1218" || node.bgcolor === "#0b1411") {
                    delete node.bgcolor;
                }
                if (node.color === "#18202c" || node.color === "#14251f") {
                    delete node.color;
                }

                if (node.size) {
                    if (node.size[0] < SHOW_MIN_WIDTH) node.size[0] = SHOW_MIN_WIDTH;
                    if (node.size[1] < SHOW_MIN_HEIGHT) node.size[1] = SHOW_MIN_HEIGHT;
                }

                // 1. Ensure multiline display text widget exists
                node.widgets = node.widgets || [];
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
                    textWidget.options = textWidget.options || {};
                    textWidget.options.serialize = false;

                    const styleInput = (el) => {
                        if (!el) return;
                        el.readOnly = true;
                        el.placeholder = "Generated prompt will be displayed here...";
                        el.style.boxSizing = "border-box";
                        el.style.opacity = "0.92";
                        el.style.fontSize = "11.5px";
                        el.style.lineHeight = "1.45";
                        el.style.fontFamily = "monospace, -apple-system, sans-serif";
                        el.style.resize = "vertical";
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

                // 2. Add convenient Copy Prompt button if not already present
                let copyBtn = node.widgets.find(w => w._isCopyButton);
                if (!copyBtn) {
                    copyBtn = node.addWidget(
                        "button",
                        "📋 Copy Prompt to Clipboard",
                        null,
                        function() {
                            const tw = node.widgets?.find(w => w.name === "display_text" || w.name === "text");
                            const textVal = tw ? (tw.value || (tw.inputEl && tw.inputEl.value) || "") : "";
                            if (textVal && navigator.clipboard) {
                                navigator.clipboard.writeText(String(textVal));
                                const origLabel = this.name;
                                this.name = "✓ Copied to Clipboard!";
                                node.setDirtyCanvas(true);
                                setTimeout(() => {
                                    this.name = origLabel;
                                    node.setDirtyCanvas(true);
                                }, 1800);
                            }
                        },
                        { serialize: false }
                    );
                    copyBtn._isCopyButton = true;
                    copyBtn.options = { serialize: false };
                }

                // Keep copyBtn positioned right under the text widget
                const textIdx = node.widgets.findIndex(w => w.name === "display_text");
                if (textIdx !== -1 && copyBtn) {
                    const curBtnIdx = node.widgets.indexOf(copyBtn);
                    if (curBtnIdx !== -1 && curBtnIdx < textIdx) {
                        node.widgets.splice(curBtnIdx, 1);
                        node.widgets.splice(textIdx, 0, copyBtn);
                    }
                }

                node.setDirtyCanvas(true, true);
            }

            const origShowCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                if (origShowCreated) origShowCreated.apply(this, arguments);
                setupShowPromptNode(this);
            };

            const origShowConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function() {
                if (origShowConfigure) origShowConfigure.apply(this, arguments);
                setupShowPromptNode(this);
            };

            // Intercept execution result from backend to populate canvas text box
            const origShowExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                if (origShowExecuted) origShowExecuted.apply(this, arguments);
                if (message && message.text) {
                    let tw = this.widgets?.find(w => w.name === "display_text");
                    if (!tw) {
                        setupShowPromptNode(this);
                        tw = this.widgets?.find(w => w.name === "display_text");
                    }
                    if (tw) {
                        let textStr = "";
                        if (Array.isArray(message.text)) {
                            textStr = message.text.join("\n\n---\n\n");
                        } else {
                            textStr = String(message.text || "");
                        }
                        tw.value = textStr;
                        if (tw.inputEl) {
                            tw.inputEl.value = textStr;
                        }
                    }
                    this.setDirtyCanvas(true, true);
                }
            };
        }

        
}
