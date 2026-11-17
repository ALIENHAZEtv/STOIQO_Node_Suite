/**
 * [STOIQO] Smart Seed & Variance Controller — Frontend History HUD Widget
 * Features:
 * - Live display of active seed and micro-variance effective seed
 * - Interactive 📋 Copy button with visual feedback
 * - Interactive History Chips of the last 5 seeds used in session
 * - One-click recall: clicking any seed chip automatically restores that seed into the widget
 *   and sets control_mode to "fixed" so the user can freeze their favorite generation immediately.
 */

export function setupSeedNode(nodeType, nodeData, appInstance) {
    const targetNames = [
        "StoiqoSeedControllerNode",
        "[STOIQO] Seed & Resolution Controller",
        "[STOIQO] Smart Seed & Variance Controller",
    ];

    if (!targetNames.includes(nodeData.name)) return;

    class StoiqoSeedHistoryWidget {
        constructor(node) {
            this.node = node;
            this.type = "custom";
            this.name = "_stoiqo_seed_history_hud";
            this.value = {};
            this.serialize = false;
            this.options = { serialize: false };
            this.isStoiqoHUD = true;
            this.height = 70;

            this.activeSeed = null;
            this.effectiveSeed = null;
            this.resolution = null;
            this.seedHistory = [];
            this.flashStatus = null;
            this.flashTimeout = null;

            this.buttonRects = {};
            this.chipRects = [];
        }

        serializeValue() {
            return undefined;
        }

        computeSize(width) {
            return [width, this.height];
        }

        setExecutionData(data) {
            if (!data) return;
            if (data.active_seed && data.active_seed.length > 0) {
                this.activeSeed = data.active_seed[0];
            }
            if (data.effective_seed && data.effective_seed.length > 0) {
                this.effectiveSeed = data.effective_seed[0];
            }
            if (data.resolution && data.resolution.length > 0) {
                this.resolution = data.resolution[0];
            }
            if (data.seed_history && Array.isArray(data.seed_history)) {
                this.seedHistory = data.seed_history;
            }
            if (this.node) {
                this.node.setDirtyCanvas(true, true);
            }
        }

        copyToClipboard(text, flashLabel) {
            if (text === null || text === undefined) return;
            const strVal = String(text);
            try {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(strVal);
                } else {
                    const ta = document.createElement("textarea");
                    ta.value = strVal;
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand("copy");
                    document.body.removeChild(ta);
                }
                this.triggerFlash(flashLabel || "✓ COPIED");
            } catch (err) {
                console.error("[STOIQO Seed] Copy failed:", err);
            }
        }

        triggerFlash(label) {
            this.flashStatus = label;
            if (this.flashTimeout) clearTimeout(this.flashTimeout);
            this.flashTimeout = setTimeout(() => {
                this.flashStatus = null;
                if (this.node) this.node.setDirtyCanvas(true, false);
            }, 1800);
            if (this.node) this.node.setDirtyCanvas(true, false);
        }

        recallSeed(seedVal) {
            if (!this.node || !this.node.widgets) return;
            const seedWidget = this.node.widgets.find(w => w.name === "seed");
            const modeWidget = this.node.widgets.find(
                w => w.name === "control_after_generate" || w.name === "control_mode"
            );

            if (seedWidget) {
                seedWidget.value = Number(seedVal);
                if (seedWidget.callback) seedWidget.callback(seedWidget.value);
            }
            if (modeWidget) {
                modeWidget.value = "fixed";
                if (modeWidget.callback) modeWidget.callback(modeWidget.value);
            }

            this.copyToClipboard(seedVal, `✓ RECALLED ${seedVal} (MODE: FIXED)`);
            this.node.setDirtyCanvas(true, true);
        }

        draw(ctx, node, width, y, height) {
            if (node.flags && node.flags.collapsed) return;

            const padX = 12;
            const cardX = padX;
            const cardY = y + 4;
            const cardW = width - (padX * 2);
            const cardH = this.height - 8;

            this.buttonRects = {};
            this.chipRects = [];

            ctx.save();

            // Background Card
            ctx.fillStyle = "rgba(18, 20, 26, 0.95)";
            ctx.strokeStyle = "rgba(41, 151, 255, 0.40)";
            ctx.lineWidth = 1.2;

            if (ctx.roundRect) {
                ctx.beginPath();
                ctx.roundRect(cardX, cardY, cardW, cardH, 7);
                ctx.fill();
                ctx.stroke();
            } else {
                ctx.fillRect(cardX, cardY, cardW, cardH);
                ctx.strokeRect(cardX, cardY, cardW, cardH);
            }

            // Left decorative accent bar
            ctx.fillStyle = "#2997ff";
            if (ctx.roundRect) {
                ctx.beginPath();
                ctx.roundRect(cardX, cardY, 4, cardH, [7, 0, 0, 7]);
                ctx.fill();
            } else {
                ctx.fillRect(cardX, cardY, 4, cardH);
            }

            // ── Row 1: Active Seed & Copy Button ──
            const row1Y = cardY + 18;
            ctx.font = "bold 10px Inter, sans-serif";
            ctx.textAlign = "left";
            ctx.textBaseline = "middle";
            ctx.fillStyle = "#58b0ff"; // Precision Blue highlight
            ctx.fillText("🎲 SEED:", cardX + 12, row1Y);

            // Display Seed
            const currentDisplay = this.activeSeed !== null ? String(this.activeSeed) : (node.widgets.find(w => w.name === "seed") ? String(node.widgets.find(w => w.name === "seed").value) : "0");
            ctx.font = "bold 11px monospace, sans-serif";
            ctx.fillStyle = "#ffffff";
            ctx.fillText(currentDisplay, cardX + 62, row1Y);

            // If effective seed differs (micro-variance) or resolution is available
            let extraX = cardX + 62 + ctx.measureText(currentDisplay).width + 8;
            if (this.effectiveSeed !== null && this.effectiveSeed !== this.activeSeed) {
                ctx.font = "9px monospace";
                ctx.fillStyle = "#58b0ff";
                const effTxt = `(Eff: ${this.effectiveSeed})`;
                ctx.fillText(effTxt, extraX, row1Y);
                extraX += ctx.measureText(effTxt).width + 8;
            }
            if (this.resolution) {
                ctx.font = "bold 9.5px monospace";
                ctx.fillStyle = "#30d158";
                ctx.fillText(`📐 ${this.resolution}`, extraX, row1Y);
            }

            // Copy Button (Right aligned)
            const copyBtnW = 68;
            const copyBtnH = 20;
            const copyBtnX = cardX + cardW - copyBtnW - 8;
            const copyBtnY = cardY + 8;
            this.buttonRects["copy_active"] = { x: copyBtnX, y: copyBtnY, w: copyBtnW, h: copyBtnH, data: currentDisplay };

            ctx.fillStyle = this.flashStatus ? "#12301d" : "#182234";
            ctx.strokeStyle = this.flashStatus ? "#30d158" : "#2997ff";
            ctx.lineWidth = 1;
            if (ctx.roundRect) {
                ctx.beginPath();
                ctx.roundRect(copyBtnX, copyBtnY, copyBtnW, copyBtnH, 4);
                ctx.fill();
                ctx.stroke();
            } else {
                ctx.fillRect(copyBtnX, copyBtnY, copyBtnW, copyBtnH);
                ctx.strokeRect(copyBtnX, copyBtnY, copyBtnW, copyBtnH);
            }

            ctx.font = "bold 9px Inter, sans-serif";
            ctx.textAlign = "center";
            ctx.fillStyle = this.flashStatus ? "#30d158" : "#d8e6f5";
            ctx.fillText(this.flashStatus || "📋 COPIA", copyBtnX + copyBtnW / 2, copyBtnY + copyBtnH / 2 + 0.5);

            // ── Row 2: Recent History Chips ──
            const row2Y = cardY + 44;
            ctx.font = "bold 9px Inter, sans-serif";
            ctx.textAlign = "left";
            ctx.fillStyle = "#94a3b8";
            ctx.fillText("📜 STORICO:", cardX + 12, row2Y);

            const startChipsX = cardX + 76;
            let curChipX = startChipsX;
            const chipH = 18;
            const chipGap = 6;

            const historyList = (this.seedHistory && this.seedHistory.length > 0)
                ? this.seedHistory
                : (this.activeSeed !== null ? [{ seed: this.activeSeed }] : []);

            if (historyList.length === 0) {
                ctx.font = "9px Inter, italic";
                ctx.fillStyle = "#64748b";
                ctx.fillText("No seeds generated in current session", startChipsX, row2Y);
            } else {
                // Show up to the last 5 seeds in chronological order
                const displayItems = historyList.slice(-5);
                displayItems.forEach((item, idx) => {
                    const seedNum = String(item.seed);
                    ctx.font = "9.5px monospace";
                    const seedW = ctx.measureText(seedNum).width + 12;

                    if (curChipX + seedW <= cardX + cardW - 8) {
                        const chipY = row2Y - chipH / 2;
                        this.chipRects.push({
                            x: curChipX,
                            y: chipY,
                            w: seedW,
                            h: chipH,
                            seed: item.seed,
                        });

                        // Chip background
                        ctx.fillStyle = "#121318";
                        ctx.strokeStyle = "rgba(41, 151, 255, 0.35)";
                        ctx.lineWidth = 1;
                        if (ctx.roundRect) {
                            ctx.beginPath();
                            ctx.roundRect(curChipX, chipY, seedW, chipH, 3);
                            ctx.fill();
                            ctx.stroke();
                        } else {
                            ctx.fillRect(curChipX, chipY, seedW, chipH);
                            ctx.strokeRect(curChipX, chipY, seedW, chipH);
                        }

                        // Chip text
                        ctx.fillStyle = "#cbd5e1";
                        ctx.textAlign = "center";
                        ctx.fillText(seedNum, curChipX + seedW / 2, row2Y + 0.5);

                        curChipX += seedW + chipGap;
                    }
                });
            }

            ctx.restore();
        }

        mouse(event, pos, node) {
            if (event.type === "pointerdown" || event.type === "mousedown") {
                const x = pos[0];
                const y = pos[1];

                // 1. Check Copy Button
                for (const [btnId, rect] of Object.entries(this.buttonRects)) {
                    if (x >= rect.x && x <= rect.x + rect.w && y >= rect.y && y <= rect.y + rect.h) {
                        this.copyToClipboard(rect.data, "✓ COPIED");
                        return true;
                    }
                }

                // 2. Check History Chips
                for (const chip of this.chipRects) {
                    if (x >= chip.x && x <= chip.x + chip.w && y >= chip.y && y <= chip.y + chip.h) {
                        this.recallSeed(chip.seed);
                        return true;
                    }
                }
            }
            return false;
        }
    }

    function ensureSeedHUD(node) {
        if (!node || !node.widgets) return;
        const existing = node.widgets.filter(w => w.name === "_stoiqo_seed_history_hud");
        for (const extra of existing.slice(1)) {
            node.widgets.splice(node.widgets.indexOf(extra), 1);
        }
        let hud = existing[0];
        if (!hud) {
            hud = new StoiqoSeedHistoryWidget(node);
            node.addCustomWidget(hud);
        }
        node._stoiqo_seed_hud = hud;
    }

    const origOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
        if (origOnNodeCreated) origOnNodeCreated.apply(this, arguments);

        if (!this.size || this.size[0] < 380) {
            this.size = [380, Math.max(this.size ? this.size[1] : 200, 220)];
        }

        ensureSeedHUD(this);
    };

    const origOnConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
        if (origOnConfigure) origOnConfigure.apply(this, arguments);
        ensureSeedHUD(this);
    };

    const origOnExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
        if (origOnExecuted) origOnExecuted.apply(this, arguments);

        if (this._stoiqo_seed_hud) {
            this._stoiqo_seed_hud.setExecutionData(message);
        }
    };
}
