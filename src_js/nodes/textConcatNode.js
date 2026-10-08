import { app } from "../../../scripts/app.js";

/**
 * [STOIQO] Text Concatenate & Clean — Interactive UI
 * Features:
 * - Dynamic Slots with Native LiteGraph Button Widgets (100% click reliability)
 * - Strict pixel-perfect height synchronization prevents textarea DOM overlapping
 * - Starts compact with 2 text slots, expandable up to 8 slots
 * - Instant collapse / expansion with smooth node re-sizing
 * - Persistent Text Display: incoming connected texts stay visible in the node!
 * - Clean HUD Token & Word Counter
 */

export function setupConcatNode(nodeType, nodeData, appInstance) {
    const concatTargetNames = [
        "StoiqoTextConcatenateNode",
        "[STOIQO] Text Concatenate & Clean",
    ];

    if (!concatTargetNames.includes(nodeData.name)) return;

    const MIN_WIDTH = 420;
    const MAX_SLOTS = 8;
    const TEXT_BOX_HEIGHT = 56; // Standardized pixel height for all text boxes

    class StoiqoTokenHudWidget {
        constructor(node) {
            this.type = "custom";
            this.name = "_stoiqo_token_hud";
            this.value = {};
            this.options = { serialize: false };
            this.node = node;
            this.stats = { words: 0, chars: 0, tokens: 0 };
        }

        serializeValue() {
            return undefined;
        }

        computeSize(width) {
            return [width, 26];
        }

        updateStats(words, chars, tokens) {
            this.stats = { words, chars, tokens };
            if (this.node) this.node.setDirtyCanvas(true, true);
        }

        draw(ctx, node, width, posY, height) {
            const nodeW = (node && node.size) ? node.size[0] : width;
            const pad = 12;
            const boxW = nodeW - pad * 2;
            const boxH = 22;

            ctx.save();
            ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
            ctx.strokeStyle = "rgba(56, 189, 248, 0.35)";
            ctx.lineWidth = 1;

            if (ctx.roundRect) {
                ctx.beginPath();
                ctx.roundRect(pad, posY, boxW, boxH, 4);
                ctx.fill();
                ctx.stroke();
            } else {
                ctx.fillRect(pad, posY, boxW, boxH);
                ctx.strokeRect(pad, posY, boxW, boxH);
            }

            ctx.font = "bold 9px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
            ctx.fillStyle = "#38bdf8";
            ctx.textAlign = "left";
            ctx.fillText("📊 STATS", pad + 8, posY + 15);

            ctx.font = "9px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
            ctx.fillStyle = "#94a3b8";
            const statText = `Parole: ${this.stats.words}   •   Caratteri: ${this.stats.chars}   •   Est. Token: ~${this.stats.tokens}`;
            ctx.fillText(statText, pad + 60, posY + 15);

            ctx.restore();
        }
    }

    function configureTextBoxWidget(w, isVisible) {
        if (!w) return;

        if (isVisible) {
            w.hidden = false;
            w.computeSize = function (width) {
                return [width, TEXT_BOX_HEIGHT];
            };

            const styleInputEl = (el) => {
                if (!el) return;
                el.style.boxSizing = "border-box";
                el.style.height = `${TEXT_BOX_HEIGHT}px`;
                el.style.minHeight = `${TEXT_BOX_HEIGHT}px`;
                el.style.maxHeight = `${TEXT_BOX_HEIGHT}px`;
                el.style.resize = "none";
                el.style.margin = "0px";
                el.style.padding = "4px 8px";
                el.style.fontSize = "11px";
                el.style.lineHeight = "1.4";
                el.hidden = false;
                el.style.display = "";
            };

            if (w.inputEl) {
                styleInputEl(w.inputEl);
            }
        } else {
            w.hidden = true;
            w.computeSize = function () {
                return [0, -4]; // Completely collapse without extra margin
            };
            w.draw = function () {};
            if (w.inputEl) {
                w.inputEl.hidden = true;
                w.inputEl.style.display = "none";
                w.inputEl.style.height = "0px";
                w.inputEl.style.minHeight = "0px";
            }
        }
    }

    function initConcatNode(node) {
        if (!node || !node.widgets) return;

        // Ensure minimum dimensions
        node.size = node.size || [MIN_WIDTH, 360];
        if (node.size[0] < MIN_WIDTH) node.size[0] = MIN_WIDTH;

        // Determine currently needed visible slots
        let initialVisible = 2;
        for (let i = 3; i <= MAX_SLOTS; i++) {
            const wName = `text_${i}`;
            const w = node.widgets.find((x) => x.name === wName);
            const inputSlot = node.inputs ? node.inputs.find((inp) => inp.name === wName) : null;
            const hasLink = inputSlot && inputSlot.link != null;
            const hasVal = w && w.value && String(w.value).trim().length > 0;
            if (hasLink || hasVal) {
                initialVisible = Math.max(initialVisible, i);
            }
        }
        node._stoiqoVisibleSlots = node._stoiqoVisibleSlots || initialVisible;

        // Configure text_1 and text_2 explicitly to match exact pixel metrics
        configureTextBoxWidget(node.widgets.find((w) => w.name === "text_1"), true);
        configureTextBoxWidget(node.widgets.find((w) => w.name === "text_2"), true);

        function refreshSlots() {
            const visibleCount = node._stoiqoVisibleSlots || 2;

            // Apply visibility and exact pixel sizing to slots 3..8
            for (let i = 3; i <= MAX_SLOTS; i++) {
                const w = node.widgets.find((x) => x.name === `text_${i}`);
                if (w) {
                    configureTextBoxWidget(w, i <= visibleCount);
                }
            }

            // Custom separator toggle
            const sepWidget = node.widgets.find((w) => w.name === "separator");
            const customSep = node.widgets.find((w) => w.name === "custom_separator");
            if (customSep && sepWidget) {
                const isCustom = String(sepWidget.value || "").includes("Custom");
                if (isCustom) {
                    customSep.hidden = false;
                    customSep.computeSize = function (w) { return [w, 24]; };
                    if (customSep.inputEl) {
                        customSep.inputEl.hidden = false;
                        customSep.inputEl.style.display = "";
                    }
                } else {
                    customSep.hidden = true;
                    customSep.computeSize = function () { return [0, -4]; };
                    customSep.draw = function () {};
                    if (customSep.inputEl) {
                        customSep.inputEl.hidden = true;
                        customSep.inputEl.style.display = "none";
                    }
                }
            }

            // Update Add button label
            if (node._stoiqoAddBtn) {
                const canAdd = visibleCount < MAX_SLOTS;
                node._stoiqoAddBtn.name = canAdd
                    ? `[+] Aggiungi Box Testo (${visibleCount}/${MAX_SLOTS})`
                    : `[✓] Massimo ${MAX_SLOTS} Box Raggiunto`;
            }

            // Update Remove button visibility
            if (node._stoiqoRemBtn) {
                const canRemove = visibleCount > 2;
                node._stoiqoRemBtn.hidden = !canRemove;
                node._stoiqoRemBtn.computeSize = canRemove
                    ? function (w) { return [w, 24]; }
                    : function () { return [0, -4]; };
            }

            // Resize node smoothly
            if (typeof node.computeSize === "function") {
                const sz = node.computeSize();
                node.setSize([Math.max(node.size[0] || 0, MIN_WIDTH), Math.max(Math.ceil(sz[1]), 220)]);
            }

            node.setDirtyCanvas(true, true);
            if (app.graph && app.graph.setDirtyCanvas) {
                app.graph.setDirtyCanvas(true, true);
            }
        }

        // Add native LiteGraph button for adding slots
        if (!node._stoiqoAddBtn) {
            const addBtn = node.addWidget(
                "button",
                `[+] Aggiungi Box Testo (${node._stoiqoVisibleSlots}/${MAX_SLOTS})`,
                null,
                function () {
                    if (node._stoiqoVisibleSlots < MAX_SLOTS) {
                        node._stoiqoVisibleSlots++;
                        refreshSlots();
                    }
                }
            );
            addBtn.serialize = false;
            node._stoiqoAddBtn = addBtn;

            addBtn.draw = function (ctx, n, width, posY, height) {
                const canAdd = (node._stoiqoVisibleSlots || 2) < MAX_SLOTS;
                const pad = 12;
                const btnW = width - pad * 2;
                const btnH = 24;

                ctx.save();
                ctx.fillStyle = canAdd ? "rgba(168, 85, 247, 0.20)" : "rgba(255, 255, 255, 0.05)";
                ctx.strokeStyle = canAdd ? "#a855f7" : "rgba(255, 255, 255, 0.12)";
                ctx.lineWidth = 1.2;

                if (ctx.roundRect) {
                    ctx.beginPath();
                    ctx.roundRect(pad, posY + 2, btnW, btnH, 5);
                    ctx.fill();
                    ctx.stroke();
                } else {
                    ctx.fillRect(pad, posY + 2, btnW, btnH);
                    ctx.strokeRect(pad, posY + 2, btnW, btnH);
                }

                ctx.font = "bold 10px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
                ctx.fillStyle = canAdd ? "#f3e8ff" : "#64748b";
                ctx.textAlign = "center";
                ctx.fillText(this.name, pad + btnW / 2, posY + 17);
                ctx.restore();
            };
        }

        // Add native LiteGraph button for removing slots
        if (!node._stoiqoRemBtn) {
            const remBtn = node.addWidget(
                "button",
                "[-] Rimuovi Ultimo Box Testo",
                null,
                function () {
                    if (node._stoiqoVisibleSlots > 2) {
                        const wName = `text_${node._stoiqoVisibleSlots}`;
                        const w = node.widgets.find((x) => x.name === wName);
                        if (w) w.value = "";
                        node._stoiqoVisibleSlots--;
                        refreshSlots();
                    }
                }
            );
            remBtn.serialize = false;
            node._stoiqoRemBtn = remBtn;

            remBtn.draw = function (ctx, n, width, posY, height) {
                if (this.hidden) return;
                const pad = 12;
                const btnW = width - pad * 2;
                const btnH = 22;

                ctx.save();
                ctx.fillStyle = "rgba(239, 68, 68, 0.15)";
                ctx.strokeStyle = "#ef4444";
                ctx.lineWidth = 1;

                if (ctx.roundRect) {
                    ctx.beginPath();
                    ctx.roundRect(pad, posY + 2, btnW, btnH, 4);
                    ctx.fill();
                    ctx.stroke();
                } else {
                    ctx.fillRect(pad, posY + 2, btnW, btnH);
                    ctx.strokeRect(pad, posY + 2, btnW, btnH);
                }

                ctx.font = "bold 10px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
                ctx.fillStyle = "#fca5a5";
                ctx.textAlign = "center";
                ctx.fillText("[-] Rimuovi Ultimo Box Testo", pad + btnW / 2, posY + 16);
                ctx.restore();
            };
        }

        // Reorder widgets so buttons appear directly under text slots and before separators
        // Ideal order: [text_1..text_8, addBtn, remBtn, separator, custom_sep, prefix, suffix, dedup, convert_underscores, skip_empty, tokenHud]
        const orderPriority = {
            "text_1": 1,
            "text_2": 2,
            "text_3": 3,
            "text_4": 4,
            "text_5": 5,
            "text_6": 6,
            "text_7": 7,
            "text_8": 8,
            "_stoiqo_add_btn": 9,
            "_stoiqo_rem_btn": 10,
            "separator": 11,
            "custom_separator": 12,
            "prefix": 13,
            "suffix": 14,
            "deduplicate_tags": 15,
            "clean_whitespace": 16,
            "convert_underscores": 17,
            "skip_empty": 18,
            "_stoiqo_token_hud": 19,
        };

        node._stoiqoAddBtn.name_key = "_stoiqo_add_btn";
        node._stoiqoRemBtn.name_key = "_stoiqo_rem_btn";

        node.widgets.sort((a, b) => {
            const pa = orderPriority[a.name_key || a.name] || 99;
            const pb = orderPriority[b.name_key || b.name] || 99;
            return pa - pb;
        });

        // Add Token HUD Widget
        let tokenHud = node.widgets.find((w) => w instanceof StoiqoTokenHudWidget);
        if (!tokenHud) {
            tokenHud = new StoiqoTokenHudWidget(node);
            node.addCustomWidget(tokenHud);
            node._stoiqo_hud = tokenHud;
        }

        // Hook separator callback
        const sepW = node.widgets.find((w) => w.name === "separator");
        if (sepW && !sepW._stoiqoHooked) {
            sepW._stoiqoHooked = true;
            const origSepCb = sepW.callback;
            sepW.callback = function () {
                if (origSepCb) origSepCb.apply(this, arguments);
                refreshSlots();
            };
        }

        node._stoiqoRefreshSlots = refreshSlots;
        refreshSlots();
    }

    const origCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
        if (origCreated) origCreated.apply(this, arguments);
        initConcatNode(this);
    };

    const origConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
        if (origConfigure) origConfigure.apply(this, arguments);
        initConcatNode(this);
    };

    // Receive execution telemetry
    const origExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
        if (origExecuted) origExecuted.apply(this, arguments);

        if (message) {
            // Update Token HUD stats
            if (message.token_info && message.token_info.length > 0) {
                const info = message.token_info[0];
                if (this._stoiqo_hud) {
                    this._stoiqo_hud.updateStats(info.words || 0, info.chars || 0, info.tokens || 0);
                }
            }

            // Keep incoming connected text values visible in textareas
            if (message.slot_values && message.slot_values.length > 0) {
                const slotMap = message.slot_values[0];
                for (let i = 1; i <= MAX_SLOTS; i++) {
                    const wName = `text_${i}`;
                    const val = slotMap[wName];
                    const w = this.widgets?.find((x) => x.name === wName);
                    const inp = this.inputs ? this.inputs.find((x) => x.name === wName) : null;
                    const isConnected = inp && inp.link != null;

                    if (w && isConnected && val !== undefined) {
                        w.value = val;
                        if (w.inputEl) {
                            w.inputEl.value = val;
                            w.inputEl.style.borderColor = "#a855f7";
                            w.inputEl.style.backgroundColor = "rgba(168, 85, 247, 0.08)";
                        }
                    }
                }
            }
            this.setDirtyCanvas(true, true);
        }
    };
}
