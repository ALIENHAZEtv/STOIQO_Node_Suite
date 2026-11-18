import { app } from "../../../scripts/app.js";

/**
 * [STOIQO] Text Concatenate & Clean — Interactive UI
 * Features:
 * - Resizable Text Boxes: Freely resize any text box vertically using native drag or 1-click height presets!
 * - Reorderable Slots: Move boxes UP (▲) or DOWN (▼) with instant text, height, and wire link swapping!
 * - Interactive Slot Headers: Sleek OLED dark header per slot with status dot, height badge, and quick actions
 * - Dynamic Slots with Native LiteGraph Button Widgets (100% click reliability)
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
    const DEFAULT_BOX_HEIGHT = 56;
    const HEIGHT_PRESETS = [44, 72, 120, 200];

    // ── Helper: Swap Slots (Text values, heights, and link wires) ────────────
    function swapSlots(node, slotA, slotB) {
        const visibleCount = node._stoiqoVisibleSlots || 2;
        if (slotA < 1 || slotA > visibleCount || slotB < 1 || slotB > visibleCount) return;
        if (slotA === slotB) return;

        const nameA = `text_${slotA}`;
        const nameB = `text_${slotB}`;
        const wA = node.widgets ? node.widgets.find((x) => x.name === nameA) : null;
        const wB = node.widgets ? node.widgets.find((x) => x.name === nameB) : null;
        if (!wA || !wB) return;

        // 1. Swap Text Values
        const tempVal = wA.value || "";
        wA.value = wB.value || "";
        wB.value = tempVal;
        if (wA.inputEl) wA.inputEl.value = wA.value;
        if (wB.inputEl) wB.inputEl.value = wB.value;
        if (wA.callback) wA.callback(wA.value);
        if (wB.callback) wB.callback(wB.value);

        // 2. Swap Custom Heights
        node.properties = node.properties || {};
        node.properties.box_heights = node.properties.box_heights || {};
        const tempH = wA._boxHeight || DEFAULT_BOX_HEIGHT;
        wA._boxHeight = wB._boxHeight || DEFAULT_BOX_HEIGHT;
        wB._boxHeight = tempH;
        node.properties.box_heights[nameA] = wA._boxHeight;
        node.properties.box_heights[nameB] = wB._boxHeight;
        if (wA.inputEl) wA.inputEl.style.height = `${wA._boxHeight}px`;
        if (wB.inputEl) wB.inputEl.style.height = `${wB._boxHeight}px`;

        // 3. Swap Incoming Link Wires
        if (node.inputs) {
            const inpA = node.inputs.find((inp) => inp.name === nameA);
            const inpB = node.inputs.find((inp) => inp.name === nameB);
            if (inpA && inpB) {
                const linkAId = inpA.link;
                const linkBId = inpB.link;

                inpA.link = linkBId;
                inpB.link = linkAId;

                const idxA = node.inputs.indexOf(inpA);
                const idxB = node.inputs.indexOf(inpB);

                const graphLinks = app.graph ? app.graph.links : null;
                if (graphLinks) {
                    if (linkAId != null && graphLinks[linkAId]) {
                        graphLinks[linkAId].target_slot = idxB;
                    }
                    if (linkBId != null && graphLinks[linkBId]) {
                        graphLinks[linkBId].target_slot = idxA;
                    }
                }
            }
        }

        if (node._stoiqoRefreshSlots) {
            node._stoiqoRefreshSlots();
        } else {
            if (typeof node.computeSize === "function") {
                node.setSize(node.computeSize());
            }
            node.setDirtyCanvas(true, true);
        }
        if (app.graph && app.graph.setDirtyCanvas) {
            app.graph.setDirtyCanvas(true, true);
        }
    }

    // ── Helper: Cycle Height Preset for a Slot ─────────────────────────────
    function cycleSlotHeight(node, slotIndex) {
        const name = `text_${slotIndex}`;
        const w = node.widgets ? node.widgets.find((x) => x.name === name) : null;
        if (!w) return;

        const currentH = w._boxHeight || DEFAULT_BOX_HEIGHT;
        let nextH = HEIGHT_PRESETS[0];

        for (let i = 0; i < HEIGHT_PRESETS.length; i++) {
            if (currentH < HEIGHT_PRESETS[i] - 6) {
                nextH = HEIGHT_PRESETS[i];
                break;
            }
            if (i === HEIGHT_PRESETS.length - 1) {
                nextH = HEIGHT_PRESETS[0];
            }
        }

        w._boxHeight = nextH;
        node.properties = node.properties || {};
        node.properties.box_heights = node.properties.box_heights || {};
        node.properties.box_heights[name] = nextH;

        if (w.inputEl) {
            w.inputEl.style.height = `${nextH}px`;
        }

        if (node._stoiqoRefreshSlots) {
            node._stoiqoRefreshSlots();
        } else {
            if (typeof node.computeSize === "function") {
                node.setSize(node.computeSize());
            }
            node.setDirtyCanvas(true, true);
        }
    }

    // ── Helper: Clear a Slot ───────────────────────────────────────────────
    function clearSlot(node, slotIndex) {
        const name = `text_${slotIndex}`;
        const w = node.widgets ? node.widgets.find((x) => x.name === name) : null;
        if (!w) return;
        w.value = "";
        if (w.inputEl) w.inputEl.value = "";
        if (w.callback) w.callback("");
        node.setDirtyCanvas(true, true);
    }

    // ── Interactive Slot Header Widget ─────────────────────────────────────
    class StoiqoSlotHeaderWidget {
        constructor(node, slotIndex) {
            this.type = "custom";
            this.name = `_stoiqo_slot_hdr_${slotIndex}`;
            this.slotIndex = slotIndex;
            this.node = node;
            this.serialize = false;
            this.options = { serialize: false };
            this.hitAreas = [];
        }

        serializeValue() {
            return undefined;
        }

        computeSize(width) {
            const isVisible = this.slotIndex <= (this.node._stoiqoVisibleSlots || 2);
            return isVisible ? [width, 20] : [0, -4];
        }

        draw(ctx, node, width, posY, height) {
            const isVisible = this.slotIndex <= (node._stoiqoVisibleSlots || 2);
            if (!isVisible) return;

            this.hitAreas = [];
            const nodeW = (node && node.size) ? node.size[0] : width;
            const pad = 12;
            const barW = nodeW - pad * 2;
            const barH = 18;
            const barY = posY + 2;

            ctx.save();

            const wName = `text_${this.slotIndex}`;
            const w = node.widgets ? node.widgets.find((x) => x.name === wName) : null;
            const inp = node.inputs ? node.inputs.find((x) => x.name === wName) : null;
            const isConnected = inp && inp.link != null;
            const hasText = Boolean(w && w.value && String(w.value).trim().length > 0);
            const currentH = w ? (w._boxHeight || DEFAULT_BOX_HEIGHT) : DEFAULT_BOX_HEIGHT;

            // Frame background
            ctx.fillStyle = isConnected ? "rgba(41, 151, 255, 0.08)" : (hasText ? "rgba(255, 255, 255, 0.04)" : "rgba(15, 23, 42, 0.65)");
            ctx.strokeStyle = isConnected ? "rgba(41, 151, 255, 0.35)" : (hasText ? "rgba(255, 255, 255, 0.12)" : "rgba(255, 255, 255, 0.06)");
            ctx.lineWidth = 1;

            if (ctx.roundRect) {
                ctx.beginPath();
                ctx.roundRect(pad, barY, barW, barH, 4);
                ctx.fill();
                ctx.stroke();
            } else {
                ctx.fillRect(pad, barY, barW, barH);
                ctx.strokeRect(pad, barY, barW, barH);
            }

            // Dot indicator
            const dotColor = isConnected ? "#2997ff" : (hasText ? "#30d158" : "#64748b");
            ctx.fillStyle = dotColor;
            ctx.beginPath();
            ctx.arc(pad + 8, barY + barH / 2, 2.5, 0, Math.PI * 2);
            ctx.fill();

            // Label
            ctx.font = "bold 9px 'JetBrains Mono', SFMono-Regular, Consolas, monospace";
            ctx.fillStyle = isConnected ? "#58b0ff" : "#f1f5f9";
            ctx.textAlign = "left";
            ctx.textBaseline = "middle";
            ctx.fillText(`BOX #${this.slotIndex}`, pad + 16, barY + barH / 2 + 0.5);

            let nextLeftX = pad + 66;
            if (isConnected) {
                ctx.font = "bold 8px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif";
                ctx.fillStyle = "#2997ff";
                ctx.fillText("[LINKED WIRE]", nextLeftX, barY + barH / 2 + 0.5);
                nextLeftX += 66;
            }

            // Height tag
            ctx.font = "8px 'JetBrains Mono', monospace";
            ctx.fillStyle = "#64748b";
            ctx.fillText(`${currentH}px`, nextLeftX, barY + barH / 2 + 0.5);

            // Action Buttons
            const visibleSlots = node._stoiqoVisibleSlots || 2;
            const canMoveUp = this.slotIndex > 1;
            const canMoveDown = this.slotIndex < visibleSlots;

            let rightX = pad + barW - 4;
            const btnH = 14;
            const btnY = barY + (barH - btnH) / 2;

            // 1. Clear button [✕] (if text present)
            if (hasText) {
                const btnW = 16;
                rightX -= btnW;
                this.drawMiniBtn(ctx, rightX, btnY, btnW, btnH, "✕", "#94a3b8", "rgba(255,255,255,0.06)", "rgba(255,255,255,0.12)");
                this.hitAreas.push({ key: "clear", x: rightX, y: btnY, w: btnW, h: btnH });
                rightX -= 4;
            }

            // 2. Height Preset Cycle button [↕]
            const hBtnW = 20;
            rightX -= hBtnW;
            this.drawMiniBtn(ctx, rightX, btnY, hBtnW, btnH, "↕", "#94a3b8", "rgba(255,255,255,0.06)", "rgba(255,255,255,0.15)");
            this.hitAreas.push({ key: "height", x: rightX, y: btnY, w: hBtnW, h: btnH });
            rightX -= 4;

            // 3. Move Down button [▼]
            const navBtnW = 18;
            rightX -= navBtnW;
            this.drawMiniBtn(
                ctx, rightX, btnY, navBtnW, btnH, "▼",
                canMoveDown ? "#38bdf8" : "#475569",
                canMoveDown ? "rgba(56, 189, 248, 0.12)" : "rgba(255,255,255,0.02)",
                canMoveDown ? "rgba(56, 189, 248, 0.40)" : "rgba(255,255,255,0.05)"
            );
            if (canMoveDown) {
                this.hitAreas.push({ key: "down", x: rightX, y: btnY, w: navBtnW, h: btnH });
            }
            rightX -= 4;

            // 4. Move Up button [▲]
            rightX -= navBtnW;
            this.drawMiniBtn(
                ctx, rightX, btnY, navBtnW, btnH, "▲",
                canMoveUp ? "#38bdf8" : "#475569",
                canMoveUp ? "rgba(56, 189, 248, 0.12)" : "rgba(255,255,255,0.02)",
                canMoveUp ? "rgba(56, 189, 248, 0.40)" : "rgba(255,255,255,0.05)"
            );
            if (canMoveUp) {
                this.hitAreas.push({ key: "up", x: rightX, y: btnY, w: navBtnW, h: btnH });
            }

            ctx.restore();
        }

        drawMiniBtn(ctx, x, y, w, h, text, color, bg, border) {
            ctx.fillStyle = bg;
            ctx.strokeStyle = border;
            ctx.lineWidth = 1;
            if (ctx.roundRect) {
                ctx.beginPath();
                ctx.roundRect(x, y, w, h, 3);
                ctx.fill();
                ctx.stroke();
            } else {
                ctx.fillRect(x, y, w, h);
                ctx.strokeRect(x, y, w, h);
            }
            ctx.font = "bold 8.5px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif";
            ctx.fillStyle = color;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(text, x + w / 2, y + h / 2 + 0.5);
        }

        mouse(event, pos, node) {
            if (!event || (event.type !== "pointerdown" && event.type !== "mousedown")) return false;
            const [mx, my] = pos;

            for (const hit of this.hitAreas) {
                if (mx >= hit.x && mx <= hit.x + hit.w && my >= hit.y && my <= hit.y + hit.h) {
                    if (hit.key === "up") {
                        swapSlots(node, this.slotIndex, this.slotIndex - 1);
                    } else if (hit.key === "down") {
                        swapSlots(node, this.slotIndex, this.slotIndex + 1);
                    } else if (hit.key === "height") {
                        cycleSlotHeight(node, this.slotIndex);
                    } else if (hit.key === "clear") {
                        clearSlot(node, this.slotIndex);
                    }
                    return true;
                }
            }
            return false;
        }
    }

    // ── Token HUD Widget ───────────────────────────────────────────────────
    class StoiqoTokenHudWidget {
        constructor(node) {
            this.type = "custom";
            this.name = "_stoiqo_token_hud";
            this.value = {};
            this.serialize = false;
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
            ctx.fillStyle = "#2997ff";
            ctx.textAlign = "left";
            ctx.fillText("📊 STATS", pad + 8, posY + 15);

            ctx.font = "9px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
            ctx.fillStyle = "#94a3b8";
            const statText = `Parole: ${this.stats.words}   •   Caratteri: ${this.stats.chars}   •   Est. Token: ~${this.stats.tokens}`;
            ctx.fillText(statText, pad + 60, posY + 15);

            ctx.restore();
        }
    }

    // ── Configure Text Box Widget with Vertical Resize & Observer ──────────
    function configureTextBoxWidget(node, w, isVisible) {
        if (!w) return;

        if (isVisible) {
            w.hidden = false;
            const currentH = w._boxHeight || (node.properties?.box_heights?.[w.name]) || DEFAULT_BOX_HEIGHT;
            w._boxHeight = currentH;

            w.computeSize = function (width) {
                return [width, w._boxHeight || DEFAULT_BOX_HEIGHT];
            };

            const styleInputEl = (el) => {
                if (!el) return;
                const h = w._boxHeight || DEFAULT_BOX_HEIGHT;
                el.style.boxSizing = "border-box";
                el.style.height = `${h}px`;
                el.style.minHeight = "36px";
                el.style.maxHeight = "600px";
                el.style.resize = "vertical";
                el.style.margin = "0px";
                el.style.padding = "6px 8px";
                el.style.fontSize = "11px";
                el.style.lineHeight = "1.4";
                el.hidden = false;
                el.style.display = "";

                // Attach ResizeObserver to capture native manual corner dragging
                if (window.ResizeObserver && !el._stoiqoResizeObserver) {
                    el._stoiqoResizeObserver = new ResizeObserver((entries) => {
                        for (const entry of entries) {
                            const newH = Math.max(36, Math.min(600, Math.round(el.offsetHeight)));
                            if (Math.abs(newH - (w._boxHeight || DEFAULT_BOX_HEIGHT)) >= 4) {
                                w._boxHeight = newH;
                                node.properties = node.properties || {};
                                node.properties.box_heights = node.properties.box_heights || {};
                                node.properties.box_heights[w.name] = newH;

                                if (typeof node.computeSize === "function") {
                                    const sz = node.computeSize();
                                    node.setSize([Math.max(node.size[0] || 0, MIN_WIDTH), Math.max(Math.ceil(sz[1]), 220)]);
                                }
                                node.setDirtyCanvas(true, true);
                                if (app.graph && app.graph.setDirtyCanvas) {
                                    app.graph.setDirtyCanvas(true, true);
                                }
                            }
                        }
                    });
                    el._stoiqoResizeObserver.observe(el);
                }
            };

            if (w.inputEl) {
                styleInputEl(w.inputEl);
            } else {
                let rawInputEl = null;
                Object.defineProperty(w, "inputEl", {
                    configurable: true,
                    enumerable: true,
                    get() { return rawInputEl; },
                    set(val) {
                        rawInputEl = val;
                        if (val) styleInputEl(val);
                    }
                });
            }
        } else {
            w.hidden = true;
            w.computeSize = function () {
                return [0, -4];
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

    // ── Initialize or Reconfigure Concat Node ──────────────────────────────
    function initConcatNode(node) {
        if (!node || !node.widgets) return;

        // Ensure minimum dimensions
        node.size = node.size || [MIN_WIDTH, 360];
        if (node.size[0] < MIN_WIDTH) node.size[0] = MIN_WIDTH;

        node.properties = node.properties || {};
        node.properties.box_heights = node.properties.box_heights || {};

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

        // Create interactive header widgets for all 8 slots
        for (let i = 1; i <= MAX_SLOTS; i++) {
            const hdrName = `_stoiqo_slot_hdr_${i}`;
            let hdr = node.widgets.find((w) => w.name === hdrName);
            if (!hdr) {
                hdr = new StoiqoSlotHeaderWidget(node, i);
                node.addCustomWidget(hdr);
            }
        }

        // Configure text_1 and text_2
        configureTextBoxWidget(node, node.widgets.find((w) => w.name === "text_1"), true);
        configureTextBoxWidget(node, node.widgets.find((w) => w.name === "text_2"), true);

        function refreshSlots() {
            const visibleCount = node._stoiqoVisibleSlots || 2;

            // Apply visibility and sizing to slots 1..8 and headers
            for (let i = 1; i <= MAX_SLOTS; i++) {
                const isVisible = i <= visibleCount;
                const hdr = node.widgets.find((x) => x.name === `_stoiqo_slot_hdr_${i}`);
                if (hdr) {
                    hdr.hidden = !isVisible;
                }
                const w = node.widgets.find((x) => x.name === `text_${i}`);
                if (w) {
                    configureTextBoxWidget(node, w, isVisible);
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
                    : `[✓] Maximum ${MAX_SLOTS} Boxes Reached`;
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
                ctx.fillStyle = canAdd ? "rgba(41, 151, 255, 0.20)" : "rgba(255, 255, 255, 0.05)";
                ctx.strokeStyle = canAdd ? "#2997ff" : "rgba(255, 255, 255, 0.12)";
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

        // Add Token HUD Widget (deduplicated by name)
        const hudDups = node.widgets.filter((w) => w.name === "_stoiqo_token_hud");
        for (const extra of hudDups.slice(1)) {
            node.widgets.splice(node.widgets.indexOf(extra), 1);
        }
        let tokenHud = node.widgets.find((w) => w.name === "_stoiqo_token_hud");
        if (!tokenHud) {
            tokenHud = new StoiqoTokenHudWidget(node);
            node.addCustomWidget(tokenHud);
            node._stoiqo_hud = tokenHud;
        }

        // Widget Sorting: Slot Header immediately precedes each Text Box
        const orderPriority = {
            "_stoiqo_slot_hdr_1": 1.0,
            "text_1": 1.5,
            "_stoiqo_slot_hdr_2": 2.0,
            "text_2": 2.5,
            "_stoiqo_slot_hdr_3": 3.0,
            "text_3": 3.5,
            "_stoiqo_slot_hdr_4": 4.0,
            "text_4": 4.5,
            "_stoiqo_slot_hdr_5": 5.0,
            "text_5": 5.5,
            "_stoiqo_slot_hdr_6": 6.0,
            "text_6": 6.5,
            "_stoiqo_slot_hdr_7": 7.0,
            "text_7": 7.5,
            "_stoiqo_slot_hdr_8": 8.0,
            "text_8": 8.5,
            "_stoiqo_add_btn": 9,
            "_stoiqo_rem_btn": 10,
            "separator": 11,
            "custom_separator": 12,
            "_stoiqo_settings_drawer": 13,
            "template": 14,
            "prefix": 15,
            "suffix": 16,
            "deduplicate_tags": 17,
            "clean_whitespace": 18,
            "convert_underscores": 19,
            "skip_empty": 20,
            "_stoiqo_token_hud": 25,
        };

        node._stoiqoAddBtn.name_key = "_stoiqo_add_btn";
        node._stoiqoRemBtn.name_key = "_stoiqo_rem_btn";

        node.widgets.sort((a, b) => {
            const pa = orderPriority[a.name_key || a.name] || 99;
            const pb = orderPriority[b.name_key || b.name] || 99;
            return pa - pb;
        });

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

        // Hook onConnectionsChange to auto-expand slots if a wire is plugged into higher slots
        const origConnectionsChange = node.onConnectionsChange;
        node.onConnectionsChange = function (type, index, isConnected, link_info) {
            if (origConnectionsChange) origConnectionsChange.apply(this, arguments);
            if (isConnected && node.inputs && node.inputs[index]) {
                const inpName = node.inputs[index].name;
                const m = inpName && inpName.match(/^text_(\d+)$/);
                if (m) {
                    const slotNum = parseInt(m[1], 10);
                    if (slotNum > (node._stoiqoVisibleSlots || 2)) {
                        node._stoiqoVisibleSlots = slotNum;
                        refreshSlots();
                    }
                }
            }
            node.setDirtyCanvas(true, true);
        };

        // Hook onMouseDown fallback to guarantee hit detection on custom headers
        const origMouseDown = node.onMouseDown;
        node.onMouseDown = function (event, localPos, graphCanvas) {
            for (const w of this.widgets || []) {
                if (w.mouse && w.mouse(event, localPos, this)) {
                    return true;
                }
            }
            return origMouseDown ? origMouseDown.apply(this, arguments) : false;
        };

        node._stoiqoRefreshSlots = refreshSlots;
        refreshSlots();
    }

    // ── Right-Click Context Menu Options ───────────────────────────────────
    const origGetExtraMenuOptions = nodeType.prototype.getExtraMenuOptions;
    nodeType.prototype.getExtraMenuOptions = function (_, options) {
        if (origGetExtraMenuOptions) origGetExtraMenuOptions.apply(this, arguments);

        options.push(
            null, // divider
            {
                content: "↕ Set All Boxes: Compact (44px)",
                callback: () => {
                    this.properties = this.properties || {};
                    this.properties.box_heights = this.properties.box_heights || {};
                    for (let i = 1; i <= MAX_SLOTS; i++) {
                        const w = this.widgets?.find((x) => x.name === `text_${i}`);
                        if (w) {
                            w._boxHeight = 44;
                            this.properties.box_heights[w.name] = 44;
                            if (w.inputEl) w.inputEl.style.height = "44px";
                        }
                    }
                    if (this._stoiqoRefreshSlots) this._stoiqoRefreshSlots();
                },
            },
            {
                content: "↕ Set All Boxes: Standard (72px)",
                callback: () => {
                    this.properties = this.properties || {};
                    this.properties.box_heights = this.properties.box_heights || {};
                    for (let i = 1; i <= MAX_SLOTS; i++) {
                        const w = this.widgets?.find((x) => x.name === `text_${i}`);
                        if (w) {
                            w._boxHeight = 72;
                            this.properties.box_heights[w.name] = 72;
                            if (w.inputEl) w.inputEl.style.height = "72px";
                        }
                    }
                    if (this._stoiqoRefreshSlots) this._stoiqoRefreshSlots();
                },
            },
            {
                content: "↕ Set All Boxes: Large (120px)",
                callback: () => {
                    this.properties = this.properties || {};
                    this.properties.box_heights = this.properties.box_heights || {};
                    for (let i = 1; i <= MAX_SLOTS; i++) {
                        const w = this.widgets?.find((x) => x.name === `text_${i}`);
                        if (w) {
                            w._boxHeight = 120;
                            this.properties.box_heights[w.name] = 120;
                            if (w.inputEl) w.inputEl.style.height = "120px";
                        }
                    }
                    if (this._stoiqoRefreshSlots) this._stoiqoRefreshSlots();
                },
            },
            {
                content: "🔄 Reset All Box Heights (Default)",
                callback: () => {
                    this.properties = this.properties || {};
                    this.properties.box_heights = {};
                    for (let i = 1; i <= MAX_SLOTS; i++) {
                        const w = this.widgets?.find((x) => x.name === `text_${i}`);
                        if (w) {
                            w._boxHeight = DEFAULT_BOX_HEIGHT;
                            if (w.inputEl) w.inputEl.style.height = `${DEFAULT_BOX_HEIGHT}px`;
                        }
                    }
                    if (this._stoiqoRefreshSlots) this._stoiqoRefreshSlots();
                },
            }
        );
    };

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

    // Receive execution telemetry & maintain visible text in textareas
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
                            w.inputEl.style.borderColor = "#2997ff";
                            w.inputEl.style.backgroundColor = "rgba(41, 151, 255, 0.08)";
                        }
                    }
                }
            }
            this.setDirtyCanvas(true, true);
        }
    };
}
