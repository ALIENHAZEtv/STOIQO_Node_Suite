import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";
import { StoiqoSectionDividerWidget, currentDownloadProgress } from "../utils/core.js";

export function setupEngineNode(nodeType, nodeData, app) {
        // 1. MAIN ENGINE NODE ENHANCEMENTS
        // ══════════════════════════════════════════════════════════════════════
        const engineTargetNames = [
            "StoiqoPromptGeneratorEngineNode",
            "QwenVLCaptionerNode",
            "[STOIQO] Prompt Generator Engine",
            "[STOIQO] Prompt Generator Engine (Legacy)",
        ];
        if (engineTargetNames.includes(nodeData.name)) {
            const MIN_NODE_WIDTH = 460;

            // Section Definitions & Theme Accents
            const SECTIONS = [
                { targetWidget: "model_preset", num: "1", title: "MODEL & HARDWARE ENGINE", color: "#60a5fa" },
                { targetWidget: "batch_mode", num: "2", title: "TASK & DIRECTIVES", color: "#c084fc" },
                { targetWidget: "seed", num: "3", title: "SAMPLING & GENERATION", color: "#facc15" },
                { targetWidget: "enable_dual_prompt", num: "4", title: "DUAL PROMPT & ARTIFACT AUDIT", color: "#2dd4bf" },
            ];

            // Multiline Text Box Heights (px)
            const MULTILINE_HEIGHTS = {
                "user_directives": 88,
                "custom_system_prompt": 68,
                            };

            function setupEngineNode(node) {
                if (!node || !node.widgets) return;

                // Clean up any previously hardcoded background/color to restore native ComfyUI defaults
                if (node.bgcolor === "#0e1218" || node.bgcolor === "#0b1411") {
                    delete node.bgcolor;
                }
                if (node.color === "#18202c" || node.color === "#14251f") {
                    delete node.color;
                }

                // Ensure comfortable node width for labels
                if (node.size && node.size[0] < MIN_NODE_WIDTH) {
                    node.size[0] = MIN_NODE_WIDTH;
                }

                // Collapse legacy model_mode widget if present from backward-compatibility schema
                const legacyModelMode = node.widgets.find(w => w.name === "model_mode");
                if (legacyModelMode) {
                    legacyModelMode.hidden = true;
                    legacyModelMode.computeSize = function() { return [0, -4]; };
                    legacyModelMode.draw = function() {};
                    if (legacyModelMode.inputEl) {
                        legacyModelMode.inputEl.hidden = true;
                        legacyModelMode.inputEl.style.display = "none";
                    }
                }

                // 1. Configure Multiline Text Boxes
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
                            if (w.hidden) {
                                w.inputEl.hidden = true;
                                w.inputEl.style.display = "none";
                            }
                        } else {
                            // In case DOM input element is created asynchronously
                            let rawInputEl = null;
                            Object.defineProperty(w, "inputEl", {
                                configurable: true,
                                enumerable: true,
                                get() { return rawInputEl; },
                                set(val) {
                                    rawInputEl = val;
                                    applyInputStyles(val);
                                    if (w.hidden && val) {
                                        val.hidden = true;
                                        val.style.display = "none";
                                    }
                                }
                            });
                        }
                    }
                }

                // 2. Dynamic Visibility Toggle for Custom System Prompt (Option B)
                function updateSystemPromptVisibility() {
                    const sysPromptWidget = node.widgets.find(w => w.name === "system_prompt");
                    const customWidget = node.widgets.find(w => w.name === "custom_system_prompt");
                    if (!customWidget) return;

                    // Visible ONLY if system_prompt dropdown contains "Custom"
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
                            return [0, -4]; // Collapse slot cleanly (LiteGraph widget vertical gap is 4px)
                        };
                        customWidget.draw = function() {
                            // Do not draw collapsed widget
                        };
                        if (customWidget.inputEl) {
                            customWidget.inputEl.hidden = true;
                            customWidget.inputEl.style.display = "none";
                        }
                    }

                    // Dynamically adapt node height
                    if (typeof node.computeSize === "function") {
                        const computed = node.computeSize();
                        node.size[0] = Math.max(node.size[0] || 0, MIN_NODE_WIDTH);
                        node.size[1] = Math.max(Math.ceil(computed[1]), 100);
                    }
                    node.setDirtyCanvas(true, true);
                }

                // Hook callback to update instantly on dropdown changes
                const sysPromptWidget = node.widgets.find(w => w.name === "system_prompt");
                if (sysPromptWidget && !sysPromptWidget._stoiqoVisibilityHooked) {
                    sysPromptWidget._stoiqoVisibilityHooked = true;
                    const origSysCallback = sysPromptWidget.callback;
                    sysPromptWidget.callback = function(val) {
                        if (origSysCallback) origSysCallback.apply(this, arguments);
                        updateSystemPromptVisibility();
                    };
                }

                // 4. Insert Standalone Section Dividers Idempotently
                // Remove any pre-existing Stoiqo dividers first to avoid accumulation on reconfigure
                node.widgets = node.widgets.filter(w => !w.isStoiqoDivider);

                for (const sec of SECTIONS) {
                    let targetIdx = node.widgets.findIndex(w => w.name === sec.targetWidget);
                    if (targetIdx === -1 && sec.fallbackWidget) {
                        targetIdx = node.widgets.findIndex(w => w.name === sec.fallbackWidget);
                    }
                    if (targetIdx !== -1) {
                        const dividerWidget = new StoiqoSectionDividerWidget(sec.num, sec.title, sec.color);
                        node.widgets.splice(targetIdx, 0, dividerWidget);
                    }
                }

                // Initial visibility checks
                                updateSystemPromptVisibility();
                
                // 4.5 Dynamic Visibility for Pipe Connection
                node.updatePipeVisibility = function() {
                    if (!this.inputs) return;
                    const pipeInput = this.inputs.find(inp => inp.name === "stoiqo_model");
                    const isConnected = pipeInput ? !!pipeInput.link : false;
                    
                    const wNamesToHide = ["model_preset", "local_model_path", "quantization", "attention_mode", "unload_model_after"];
                    
                    this.widgets.forEach(w => {
                        if (wNamesToHide.includes(w.name) || (w.isStoiqoDivider && w.sectionNum === "1")) {
                            if (!w._stoiqoOrigComputeSizePipe) {
                                w._stoiqoOrigComputeSizePipe = w.computeSize;
                                w._stoiqoOrigDrawPipe = w.draw;
                            }
                            
                            if (isConnected) {
                                w.hidden = true;
                                w.computeSize = function() { return [0, -4]; };
                                w.draw = function() {};
                                if (w.inputEl) {
                                    w.inputEl.hidden = true;
                                    w.inputEl.style.display = "none";
                                }
                            } else {
                                w.hidden = false;
                                if (w._stoiqoOrigComputeSizePipe) {
                                    w.computeSize = w._stoiqoOrigComputeSizePipe;
                                } else {
                                    delete w.computeSize;
                                }
                                if (w._stoiqoOrigDrawPipe) {
                                    w.draw = w._stoiqoOrigDrawPipe;
                                } else {
                                    delete w.draw;
                                }
                                if (w.inputEl) {
                                    w.inputEl.hidden = false;
                                    w.inputEl.style.display = "";
                                }
                            }
                        }
                    });
                    
                    if (isConnected) {
                        const browseWidget = this.widgets.find(w => w._isStoiqoBrowse);
                        if (browseWidget) {
                            if (!browseWidget._stoiqoOrigComputeSizePipe) {
                                browseWidget._stoiqoOrigComputeSizePipe = browseWidget.computeSize;
                                browseWidget._stoiqoOrigDrawPipe = browseWidget.draw;
                            }
                            browseWidget.hidden = true;
                            browseWidget.computeSize = function() { return [0, -4]; };
                            browseWidget.draw = function() {};
                        }
                    }
                    
                    if (typeof this.computeSize === "function") {
                        const computed = this.computeSize();
                        this.size[0] = Math.max(this.size[0] || 0, MIN_NODE_WIDTH);
                        this.size[1] = Math.max(Math.ceil(computed[1]), 100);
                    }
                    this.setDirtyCanvas(true, true);
                };
                
                // Trigger initial pipe visibility check
                // We wrap it in setTimeout to ensure inputs are fully populated on graph load
                setTimeout(() => node.updatePipeVisibility(), 50);

                // 5. Update Node Dimensions cleanly
                if (typeof node.computeSize === "function") {
                    const computed = node.computeSize();
                    node.size[0] = Math.max(node.size[0] || 0, MIN_NODE_WIDTH);
                    node.size[1] = Math.max(node.size[1] || 0, Math.ceil(computed[1]));
                }

                node.setDirtyCanvas(true, true);
            }

            const origOnNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                if (origOnNodeCreated) {
                    origOnNodeCreated.apply(this, arguments);
                }
                setupEngineNode(this);
            };

            const origOnConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function() {
                if (origOnConfigure) {
                    origOnConfigure.apply(this, arguments);
                }
                setupEngineNode(this);
            };

            const origOnConnectionsChange = nodeType.prototype.onConnectionsChange;
            nodeType.prototype.onConnectionsChange = function(type, index, connected, link_info) {
                if (origOnConnectionsChange) {
                    origOnConnectionsChange.apply(this, arguments);
                }
                if (type === 1 && this.inputs && this.inputs[index] && this.inputs[index].name === "stoiqo_model") {
                    if (typeof this.updatePipeVisibility === 'function') {
                        this.updatePipeVisibility();
                    }
                }
            };
        }

        
}
