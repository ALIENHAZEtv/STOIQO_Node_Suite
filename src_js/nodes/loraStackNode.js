import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

/**
 * [STOIQO] LoRA Stack — canvas UI
 * "+ Add LoRA" appends rows; each row has an on/off toggle, name picker, strength (-/value/+) and remove.
 * State is persisted as JSON in the hidden `lora_stack` STRING widget.
 */

const LORA_NODE_NAMES = ["StoiqoLoraStackNode", "[STOIQO] LoRA Stack"];
const MIN_WIDTH = 400;
const PAD = 6;
const HEAD_H = 24;
const ROW_H = 28;
const BTN_H = 30;
const STEP = 0.05;

let _loraListCache = null;

async function fetchLoraList(force = false) {
    if (_loraListCache && !force) return _loraListCache;
    try {
        const resp = await api.fetchApi("/stoiqo/loras");
        const data = await resp.json();
        _loraListCache = Array.isArray(data.loras) ? data.loras : [];
    } catch (err) {
        console.warn("[STOIQO LoRA Stack] Impossibile leggere la lista LoRA:", err);
        _loraListCache = [];
    }
    return _loraListCache;
}

function roundRect(ctx, x, y, w, h, r) {
    if (ctx.roundRect) {
        ctx.beginPath();
        ctx.roundRect(x, y, w, h, r);
    } else {
        ctx.beginPath();
        ctx.rect(x, y, w, h);
    }
}

function baseName(path) {
    const parts = String(path).split(/[\\/]/);
    const file = parts[parts.length - 1] || "";
    return file.replace(/\.(safetensors|ckpt|pt|pth|bin)$/i, "");
}

function fitText(ctx, text, maxW) {
    if (ctx.measureText(text).width <= maxW) return text;
    let t = text;
    while (t.length > 1 && ctx.measureText(t + "…").width > maxW) {
        t = t.slice(0, -1);
    }
    return t + "…";
}

class StoiqoLoraStackWidget {
    constructor(node, storeWidget) {
        this.type = "custom";
        this.name = "_stoiqo_lora_stack";
        this.node = node;
        this.store = storeWidget;
        this.options = { serialize: false };
        this.loras = [];
        this.hits = [];
        this.lastClick = 0;
    }

    // The UI state lives in the hidden store widget; this widget carries no value of its own.
    get value() { return ""; }
    set value(_v) { /* ignore: restored from the store widget */ }

    rowsCount() {
        return Math.max(this.loras.length, 1);
    }

    totalHeight() {
        return PAD + HEAD_H + this.rowsCount() * ROW_H + 6 + BTN_H + PAD;
    }

    computeSize(width) {
        return [width, this.totalHeight()];
    }

    computeLayoutSize() {
        const h = this.totalHeight();
        return { minHeight: h, maxHeight: h, minWidth: MIN_WIDTH };
    }

    loadFromStore() {
        let parsed = [];
        try {
            const raw = this.store ? this.store.value : "[]";
            const data = JSON.parse(raw || "[]");
            if (Array.isArray(data)) parsed = data;
        } catch (e) {
            parsed = [];
        }
        this.loras = parsed
            .filter(it => it && typeof it.name === "string" && it.name)
            .map(it => {
                const sm = Number.isFinite(Number(it.strength)) ? Number(it.strength) : 1.0;
                const sc = Number.isFinite(Number(it.strength_clip)) ? Number(it.strength_clip) : sm;
                return {
                    name: it.name,
                    strength: sm,
                    strength_clip: sc,
                    enabled: it.enabled !== false,
                    block_filter: it.block_filter || "All Blocks (Standard)",
                };
            });
    }

    sync() {
        if (this.store) {
            this.store.value = JSON.stringify(
                this.loras.map(l => ({
                    name: l.name,
                    strength: l.strength,
                    strength_clip: l.strength_clip !== undefined ? l.strength_clip : l.strength,
                    enabled: l.enabled,
                    block_filter: l.block_filter || "All Blocks (Standard)",
                }))
            );
        }
        this.resizeNode();
        if (this.node) this.node.setDirtyCanvas(true, true);
    }

    resizeNode() {
        const node = this.node;
        if (!node) return;
        const sz = node.computeSize();
        node.setSize([Math.max(node.size[0], MIN_WIDTH), sz[1]]);
    }

    draw(ctx, node, width, posY) {
        this.hits = [];
        const x0 = 10;
        const w = width - 20;
        let y = posY + PAD;

        ctx.save();
        ctx.textBaseline = "middle";

        // ── Header ────────────────────────────────────────────
        const activeCount = this.loras.filter(l => l.enabled).length;
        ctx.font = "bold 11px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
        ctx.textAlign = "left";
        ctx.fillStyle = "#94a3b8";
        ctx.fillText(`LoRA Stack · ${activeCount}/${this.loras.length} attivi`, x0 + 2, y + HEAD_H / 2);

        const allLabel = activeCount > 0 ? "Disattiva tutti" : "Attiva tutti";
        ctx.font = "10px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
        const allW = ctx.measureText(allLabel).width + 16;
        const allX = x0 + w - allW;
        if (this.loras.length > 0) {
            ctx.fillStyle = "rgba(255,255,255,0.07)";
            roundRect(ctx, allX, y + 3, allW, HEAD_H - 6, 4);
            ctx.fill();
            ctx.fillStyle = "#cbd5e1";
            ctx.textAlign = "center";
            ctx.fillText(allLabel, allX + allW / 2, y + HEAD_H / 2);
            this.hits.push({
                x: allX, y: y + 3, w: allW, h: HEAD_H - 6,
                action: () => {
                    const target = activeCount === 0;
                    this.loras.forEach(l => { l.enabled = target; });
                    this.sync();
                },
            });
        }
        y += HEAD_H;

        // ── Rows ──────────────────────────────────────────────
        if (this.loras.length === 0) {
            ctx.font = "italic 11px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
            ctx.fillStyle = "#64748b";
            ctx.textAlign = "center";
            ctx.fillText("Nessun LoRA — premi “+ Aggiungi LoRA”", x0 + w / 2, y + ROW_H / 2);
            y += ROW_H;
        } else {
            this.loras.forEach((lora, idx) => {
                const rY = y + 2;
                const rH = ROW_H - 4;
                const on = lora.enabled;

                // Row background
                ctx.fillStyle = on ? "rgba(45, 212, 191, 0.08)" : "rgba(255, 255, 255, 0.04)";
                roundRect(ctx, x0, rY, w, rH, 5);
                ctx.fill();
                ctx.strokeStyle = on ? "rgba(45, 212, 191, 0.35)" : "rgba(255, 255, 255, 0.08)";
                ctx.lineWidth = 1;
                ctx.stroke();

                // Toggle pill
                const tW = 28, tH = 14;
                const tX = x0 + 6, tY = rY + (rH - tH) / 2;
                ctx.fillStyle = on ? "#2dd4bf" : "#475569";
                roundRect(ctx, tX, tY, tW, tH, 7);
                ctx.fill();
                ctx.fillStyle = "#0f172a";
                ctx.beginPath();
                ctx.arc(on ? tX + tW - 7 : tX + 7, tY + tH / 2, 5, 0, Math.PI * 2);
                ctx.fill();
                this.hits.push({
                    x: tX - 2, y: rY, w: tW + 4, h: rH,
                    action: () => { lora.enabled = !lora.enabled; this.sync(); },
                });

                // Right controls: [▲] [▼] [−] value [+] [⚙] [✕]
                const upW = 15, dnW = 15, btnW = 16, valW = 52, gearW = 18, xW = 16, gap = 2;
                const ctrlW = upW + gap + dnW + gap + btnW + valW + btnW + gap + gearW + gap + xW;
                const cX = x0 + w - ctrlW - 4;
                const cY = rY + 3;
                const cH = rH - 6;

                const drawBtn = (bx, bw, label, color, bg = "rgba(255,255,255,0.08)", font = "bold 11px sans-serif") => {
                    ctx.fillStyle = bg;
                    roundRect(ctx, bx, cY, bw, cH, 3);
                    ctx.fill();
                    ctx.fillStyle = color;
                    ctx.font = font;
                    ctx.textAlign = "center";
                    ctx.fillText(label, bx + bw / 2, cY + cH / 2 + 0.5);
                };

                // Move Up [▲]
                drawBtn(cX, upW, "▲", idx > 0 ? "#cbd5e1" : "#475569", "rgba(255,255,255,0.05)", "9px sans-serif");
                this.hits.push({
                    x: cX, y: cY, w: upW, h: cH,
                    action: () => {
                        if (idx > 0) {
                            const tmp = this.loras[idx - 1];
                            this.loras[idx - 1] = this.loras[idx];
                            this.loras[idx] = tmp;
                            this.sync();
                        }
                    },
                });

                // Move Down [▼]
                const dnX = cX + upW + gap;
                drawBtn(dnX, dnW, "▼", idx < this.loras.length - 1 ? "#cbd5e1" : "#475569", "rgba(255,255,255,0.05)", "9px sans-serif");
                this.hits.push({
                    x: dnX, y: cY, w: dnW, h: cH,
                    action: () => {
                        if (idx < this.loras.length - 1) {
                            const tmp = this.loras[idx + 1];
                            this.loras[idx + 1] = this.loras[idx];
                            this.loras[idx] = tmp;
                            this.sync();
                        }
                    },
                });

                // Decrement [−]
                const minusX = dnX + dnW + gap;
                drawBtn(minusX, btnW, "−", "#e2e8f0");
                this.hits.push({
                    x: minusX, y: cY, w: btnW, h: cH,
                    action: (ev) => {
                        if (ev && ev.shiftKey) {
                            lora.strength_clip = Math.round(((lora.strength_clip ?? lora.strength) - STEP) * 100) / 100;
                        } else {
                            lora.strength = Math.round((lora.strength - STEP) * 100) / 100;
                            if (lora.strength_clip === undefined) lora.strength_clip = lora.strength;
                        }
                        this.sync();
                    },
                });

                // Value box
                const vX = minusX + btnW;
                ctx.fillStyle = "rgba(0,0,0,0.3)";
                ctx.fillRect(vX, cY, valW, cH);
                ctx.fillStyle = on ? "#f1f5f9" : "#64748b";
                ctx.font = "10px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
                ctx.textAlign = "center";
                const isDecoupled = lora.strength_clip !== undefined && Math.abs(lora.strength_clip - lora.strength) > 0.001;
                const valLabel = isDecoupled ? `${lora.strength.toFixed(1)}|${lora.strength_clip.toFixed(1)}` : lora.strength.toFixed(2);
                ctx.fillText(valLabel, vX + valW / 2, cY + cH / 2 + 0.5);
                this.hits.push({
                    x: vX, y: cY, w: valW, h: cH,
                    action: (ev) => {
                        const isShift = ev && ev.shiftKey;
                        const promptTitle = isShift ? "CLIP Strength" : "Model Strength (Shift+click for CLIP)";
                        const curVal = isShift ? (lora.strength_clip ?? lora.strength) : lora.strength;
                        app.canvas.prompt(promptTitle, curVal, (v) => {
                            const num = parseFloat(v);
                            if (Number.isFinite(num)) {
                                const rounded = Math.round(Math.max(-10, Math.min(10, num)) * 100) / 100;
                                if (isShift) {
                                    lora.strength_clip = rounded;
                                } else {
                                    lora.strength = rounded;
                                }
                                this.sync();
                            }
                        }, ev);
                    },
                });

                // Increment [+]
                const plusX = vX + valW;
                drawBtn(plusX, btnW, "+", "#e2e8f0");
                this.hits.push({
                    x: plusX, y: cY, w: btnW, h: cH,
                    action: (ev) => {
                        if (ev && ev.shiftKey) {
                            lora.strength_clip = Math.round(((lora.strength_clip ?? lora.strength) + STEP) * 100) / 100;
                        } else {
                            lora.strength = Math.round((lora.strength + STEP) * 100) / 100;
                            if (lora.strength_clip === undefined) lora.strength_clip = lora.strength;
                        }
                        this.sync();
                    },
                });

                // Row Settings [⚙]
                const hasCustomBlock = Boolean(lora.block_filter && !lora.block_filter.startsWith("All Blocks"));
                const hasCustomRowCfg = isDecoupled || hasCustomBlock;
                const gearX = plusX + btnW + gap;
                drawBtn(
                    gearX,
                    gearW,
                    "⚙",
                    hasCustomRowCfg ? "#58b0ff" : "#cbd5e1",
                    hasCustomRowCfg ? "rgba(41,151,255,0.18)" : "rgba(255,255,255,0.06)",
                    "11px sans-serif"
                );
                this.hits.push({
                    x: gearX, y: cY, w: gearW, h: cH,
                    action: (ev) => this.showRowMenu(ev, lora, idx),
                });

                // Delete [✕]
                const xX = gearX + gearW + gap;
                drawBtn(xX, xW, "✕", "#f87171");
                this.hits.push({
                    x: xX, y: cY, w: xW, h: cH,
                    action: () => { this.loras.splice(idx, 1); this.sync(); },
                });

                // LoRA name (click to pick LoRA directly; [⚙] opens advanced row menu)
                const nX = tX + tW + 8;
                const nW = cX - nX - 6;
                ctx.font = "12px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
                ctx.textAlign = "left";
                ctx.fillStyle = on ? "#e2e8f0" : "#64748b";
                const blockTag = hasCustomBlock
                    ? (lora.block_filter.includes("OUT") ? " [OUT]" : (lora.block_filter.includes("IN/MID") ? " [IN/MID]" : " [MID]"))
                    : "";
                ctx.fillText(fitText(ctx, baseName(lora.name) + blockTag, nW), nX, rY + rH / 2 + 0.5);
                this.hits.push({
                    x: nX, y: rY, w: nW, h: rH,
                    action: (ev) => {
                        if (ev && ev.button === 2) {
                            this.showRowMenu(ev, lora, idx);
                        } else {
                            this.pickLora(ev, (picked) => {
                                lora.name = picked;
                                this.sync();
                            });
                        }
                    },
                });

                y += ROW_H;
            });
        }

        // ── "+ Add LoRA" button ───────────────────────────────
        y += 6;
        ctx.fillStyle = "rgba(45, 212, 191, 0.14)";
        roundRect(ctx, x0, y, w, BTN_H - 4, 6);
        ctx.fill();
        ctx.strokeStyle = "rgba(45, 212, 191, 0.55)";
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.fillStyle = "#2dd4bf";
        ctx.font = "bold 12px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("+ Aggiungi LoRA", x0 + w / 2, y + (BTN_H - 4) / 2 + 0.5);
        this.hits.push({
            x: x0, y, w, h: BTN_H - 4,
            action: (ev) => this.pickLora(ev, (picked) => {
                this.loras.push({ name: picked, strength: 1.0, enabled: true });
                this.sync();
            }),
        });

        ctx.restore();
    }

    async showRowMenu(event, lora, idx) {
        const LG = window.LiteGraph;
        if (!LG || !LG.ContextMenu) {
            this.pickLora(event, (picked) => {
                lora.name = picked;
                this.sync();
            });
            return;
        }

        const items = [
            {
                content: `🔍 Cambia LoRA...`,
                callback: (v, opts, e) => {
                    this.pickLora(e, (picked) => {
                        lora.name = picked;
                        this.sync();
                    });
                },
            },
            {
                content: `⚖️ Modifica CLIP Strength (${(lora.strength_clip ?? lora.strength).toFixed(2)})`,
                callback: (_v, _opts, e) => {
                    app.canvas.prompt("CLIP Strength", lora.strength_clip ?? lora.strength, (val) => {
                        const num = parseFloat(val);
                        if (Number.isFinite(num)) {
                            lora.strength_clip = Math.round(Math.max(-10, Math.min(10, num)) * 100) / 100;
                            this.sync();
                        }
                    }, e);
                },
            },
            {
                content: `🧱 Filtro Blocchi (${lora.block_filter || "All Blocks"})`,
                has_submenu: true,
                callback: (_v, _opts, e, menu) => {
                    const filters = [
                        "All Blocks (Standard)",
                        "Style / Texture Only (OUT Blocks)",
                        "Character / Structure Only (IN/MID Blocks)",
                        "Face & Pose Focused (MID Block)",
                    ];
                    new LG.ContextMenu(
                        filters.map(f => ({
                            content: (lora.block_filter === f || (!lora.block_filter && f.startsWith("All"))) ? `✓ ${f}` : f,
                            value: f,
                        })),
                        {
                            event: e,
                            parentMenu: menu,
                            callback: (chosen) => {
                                if (chosen && chosen.value) {
                                    lora.block_filter = chosen.value;
                                    this.sync();
                                }
                            },
                        }
                    );
                    return true;
                },
            },
            {
                content: `🏷️ Mostra / Copia Trigger Words`,
                callback: async (_v, _opts, e) => {
                    try {
                        const resp = await api.fetchApi(`/stoiqo/lora_info?name=${encodeURIComponent(lora.name)}`);
                        const data = await resp.json();
                        const triggers = Array.isArray(data.triggers) ? data.triggers : [];
                        if (triggers.length > 0) {
                            const trigStr = triggers.join(", ");
                            if (navigator.clipboard) {
                                navigator.clipboard.writeText(trigStr).catch(() => {});
                            }
                            alert(`Trigger words per '${baseName(lora.name)}':\n\n${trigStr}\n\n(Copiate negli appunti!)`);
                        } else {
                            alert(`Nessuna trigger word trovata nei metadati o sidecar per '${baseName(lora.name)}'.`);
                        }
                    } catch (err) {
                        alert(`Errore lettura metadati per '${baseName(lora.name)}'.`);
                    }
                },
            },
            {
                content: `✕ Rimuovi`,
                callback: () => {
                    this.loras.splice(idx, 1);
                    this.sync();
                },
            },
        ];

        new LG.ContextMenu(items, { event, title: baseName(lora.name) });
    }

    async pickLora(event, onPick) {
        const list = await fetchLoraList(true);
        const LG = window.LiteGraph;
        if (!LG || !LG.ContextMenu) return;

        if (!list.length) {
            new LG.ContextMenu([{ content: "Nessun LoRA trovato in models/loras", disabled: true }], { event });
            return;
        }

        const choose = (v) => {
            if (v && typeof v.value === "string") onPick(v.value);
        };

        const hasFolders = list.some(n => /[\\/]/.test(n));
        if (!hasFolders) {
            new LG.ContextMenu(
                list.map(n => ({ content: baseName(n), value: n })),
                { event, title: "LoRA", callback: choose }
            );
            return;
        }

        // Group by sub-folder: root files first, then one submenu per folder.
        const groups = new Map();
        const rootFiles = [];
        for (const n of list) {
            const parts = n.split(/[\\/]/);
            if (parts.length === 1) {
                rootFiles.push(n);
            } else {
                const folder = parts.slice(0, -1).join("/");
                if (!groups.has(folder)) groups.set(folder, []);
                groups.get(folder).push(n);
            }
        }

        const items = [];
        for (const [folder, files] of [...groups.entries()].sort((a, b) => a[0].localeCompare(b[0]))) {
            items.push({
                content: `📁 ${folder}`,
                has_submenu: true,
                callback: (_value, _options, e, menu) => {
                    new LG.ContextMenu(
                        files.map(n => ({ content: baseName(n), value: n })),
                        { event: e, parentMenu: menu, callback: choose }
                    );
                    return true;
                },
            });
        }
        rootFiles.forEach(n => items.push({ content: baseName(n), value: n }));

        new LG.ContextMenu(items, { event, title: "LoRA", callback: choose });
    }

    mouse(event, pos, node) {
        if (!event || (event.type !== "pointerdown" && event.type !== "mousedown")) return false;
        if (!pos) return false;
        const now = performance.now();
        if (now - this.lastClick < 150) return true; // pointerdown + mousedown de-dup
        const [mx, my] = pos;
        for (const h of this.hits) {
            if (mx >= h.x && mx <= h.x + h.w && my >= h.y && my <= h.y + h.h) {
                this.lastClick = now;
                h.action(event);
                return true;
            }
        }
        return false;
    }
}

function setupLoraStackNodeUI(node) {
    if (!node) return;
    if (node.size && node.size[0] < MIN_WIDTH) node.size[0] = MIN_WIDTH;

    if (node.widgets) {
        const dups = node.widgets.filter(w => w.name === "_stoiqo_lora_stack");
        for (const extra of dups.slice(1)) {
            node.widgets.splice(node.widgets.indexOf(extra), 1);
        }
    }
    let loraWidget = node.widgets ? node.widgets.find(w => w.name === "_stoiqo_lora_stack") : null;
    if (!loraWidget) {
        const store = node.widgets ? node.widgets.find(w => w.name === "lora_stack") : null;
        for (const wName of ["lora_stack", "block_filter"]) {
            const hw = node.widgets ? node.widgets.find(w => w.name === wName) : null;
            if (hw) {
                hw.hidden = true;
                hw.computeSize = () => [0, -4];
                hw.draw = () => {};
                if (hw.inputEl) {
                    hw.inputEl.hidden = true;
                    hw.inputEl.style.display = "none";
                }
            }
        }
        loraWidget = new StoiqoLoraStackWidget(node, store);
        node.addCustomWidget(loraWidget);
        node.stoiqoLoraWidget = loraWidget;
    }
    loraWidget.loadFromStore();
    loraWidget.resizeNode();
    node.setDirtyCanvas(true, true);
}

export function setupLoraStackNode(nodeType, nodeData, appInstance) {
    if (!LORA_NODE_NAMES.includes(nodeData.name)) return;

    const origCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
        if (origCreated) origCreated.apply(this, arguments);
        setupLoraStackNodeUI(this);
    };

    const origConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
        if (origConfigure) origConfigure.apply(this, arguments);
        setupLoraStackNodeUI(this);
    };
}
