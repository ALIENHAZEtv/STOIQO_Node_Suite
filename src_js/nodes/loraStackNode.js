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
            .map(it => ({
                name: it.name,
                strength: Number.isFinite(Number(it.strength)) ? Number(it.strength) : 1.0,
                enabled: it.enabled !== false,
            }));
    }

    sync() {
        if (this.store) {
            this.store.value = JSON.stringify(
                this.loras.map(l => ({
                    name: l.name,
                    strength: l.strength,
                    strength_clip: l.strength,
                    enabled: l.enabled,
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
                const tX = x0 + 8, tY = rY + (rH - tH) / 2;
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

                // Right controls: [−] value [+] [✕]
                const btnW = 18, valW = 46, xW = 18, gap = 3;
                const ctrlW = btnW + valW + btnW + gap + xW;
                const cX = x0 + w - ctrlW - 6;
                const cY = rY + 3;
                const cH = rH - 6;

                const drawBtn = (bx, bw, label, color) => {
                    ctx.fillStyle = "rgba(255,255,255,0.08)";
                    roundRect(ctx, bx, cY, bw, cH, 3);
                    ctx.fill();
                    ctx.fillStyle = color;
                    ctx.font = "bold 12px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
                    ctx.textAlign = "center";
                    ctx.fillText(label, bx + bw / 2, cY + cH / 2 + 0.5);
                };

                drawBtn(cX, btnW, "−", "#e2e8f0");
                this.hits.push({
                    x: cX, y: cY, w: btnW, h: cH,
                    action: () => {
                        lora.strength = Math.round((lora.strength - STEP) * 100) / 100;
                        this.sync();
                    },
                });

                // Value box
                const vX = cX + btnW;
                ctx.fillStyle = "rgba(0,0,0,0.25)";
                ctx.fillRect(vX, cY, valW, cH);
                ctx.fillStyle = on ? "#f1f5f9" : "#64748b";
                ctx.font = "11px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
                ctx.textAlign = "center";
                ctx.fillText(lora.strength.toFixed(2), vX + valW / 2, cY + cH / 2 + 0.5);
                this.hits.push({
                    x: vX, y: cY, w: valW, h: cH,
                    action: (ev) => {
                        app.canvas.prompt("Strength", lora.strength, (v) => {
                            const num = parseFloat(v);
                            if (Number.isFinite(num)) {
                                lora.strength = Math.round(Math.max(-10, Math.min(10, num)) * 100) / 100;
                                this.sync();
                            }
                        }, ev);
                    },
                });

                drawBtn(vX + valW, btnW, "+", "#e2e8f0");
                this.hits.push({
                    x: vX + valW, y: cY, w: btnW, h: cH,
                    action: () => {
                        lora.strength = Math.round((lora.strength + STEP) * 100) / 100;
                        this.sync();
                    },
                });

                const xX = vX + valW + btnW + gap;
                drawBtn(xX, xW, "✕", "#f87171");
                this.hits.push({
                    x: xX, y: cY, w: xW, h: cH,
                    action: () => { this.loras.splice(idx, 1); this.sync(); },
                });

                // LoRA name (click to change) — clipped to the space left of the controls
                const nX = tX + tW + 10;
                const nW = cX - nX - 8;
                ctx.font = "12px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
                ctx.textAlign = "left";
                ctx.fillStyle = on ? "#e2e8f0" : "#64748b";
                ctx.fillText(fitText(ctx, baseName(lora.name), nW), nX, rY + rH / 2 + 0.5);
                this.hits.push({
                    x: nX, y: rY, w: nW, h: rH,
                    action: (ev) => this.pickLora(ev, (picked) => {
                        lora.name = picked;
                        this.sync();
                    }),
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

    let loraWidget = node.widgets ? node.widgets.find(w => w instanceof StoiqoLoraStackWidget) : null;
    if (!loraWidget) {
        const store = node.widgets ? node.widgets.find(w => w.name === "lora_stack") : null;
        if (store) {
            // Hide the raw JSON widget; the canvas widget manages it.
            store.hidden = true;
            store.computeSize = () => [0, -4];
            store.draw = () => {};
            if (store.inputEl) {
                store.inputEl.hidden = true;
                store.inputEl.style.display = "none";
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
