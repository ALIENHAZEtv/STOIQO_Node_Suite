import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

/**
 * [STOIQO] Universal Model Loader Stack — Canvas UI
 * Identical architectural pattern to loraStackNode.js:
 *   - `mouse()` for click handling (not node onMouseDown)
 *   - `hits[]` for hit-testing canvas-rendered buttons
 *   - Legacy widgets hidden with hidden + computeSize → [0, -4]
 */

const MODEL_NODE_NAMES = [
    "StoiqoUniversalModelLoaderNode",
    "[STOIQO] Universal Model Loader (All-in-One)",
];

// Backend legacy widgets to hide completely
const LEGACY_WIDGET_NAMES = [
    "model_name",
    "clip_type",
    "precision",
    "attention",
    "flow_shift_preset",
    "custom_shift",
    "custom_path",
];

const MIN_WIDTH = 440;
const PAD       = 6;
const HEAD_H    = 24;
const ROW_H     = 28;
const BTN_H     = 30;

const PRECISIONS = ["default", "fp8_e4m3fn", "fp8_e4m3fn_fast", "fp8_e5m2", "4bit - NF4", "8bit", "fp16", "bf16"];
const ATTENTIONS = ["sdpa", "flash_attention_2", "eager"];
const CLIP_TYPES = ["auto", "krea2", "flux", "wan", "sd3", "ace", "qwen_image", "lumina2", "mochi", "ltxv", "minimax", "stable_diffusion"];
const DEFAULT_PRESET = "None (Standard / SD1.5 / SDXL / Krea 2)";
let _presets = [DEFAULT_PRESET];

let _modelListCache = null;

async function fetchModelList(force = false) {
    if (_modelListCache && !force) return _modelListCache;
    try {
        const resp = await api.fetchApi("/stoiqo/models");
        const data = await resp.json();
        if (Array.isArray(data.presets) && data.presets.length) _presets = data.presets;
        _modelListCache = Array.isArray(data.models) ? data.models : [];
    } catch (err) {
        console.warn("[STOIQO Model Stack] Unable to load models list:", err);
        _modelListCache = [];
    }
    return _modelListCache;
}

// ── Helpers canvas ────────────────────────────────────────────────────────────

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
    const parts = String(path).split(/[\\\/]/);
    const file  = parts[parts.length - 1] || "";
    return file.replace(/\.(safetensors|ckpt|pt|pth|bin|gguf)$/i, "");
}

function fitText(ctx, text, maxW) {
    if (ctx.measureText(text).width <= maxW) return text;
    let t = text;
    while (t.length > 1 && ctx.measureText(t + "…").width > maxW) {
        t = t.slice(0, -1);
    }
    return t + "…";
}

function newModel(name, src = {}) {
    const sh = Number(src.custom_shift);
    return {
        name,
        enabled: src.enabled !== false,
        precision: String(src.precision || "default"),
        attention: String(src.attention || "sdpa"),
        clip_type: String(src.clip_type || "auto"),
        flow_shift_preset: String(src.flow_shift_preset || DEFAULT_PRESET),
        custom_shift: Number.isFinite(sh) ? sh : 3.0,
        custom_path: String(src.custom_path || ""),
    };
}

// ── Widget class ──────────────────────────────────────────────────────────────

class ModelStackWidget {
    constructor(node, storeWidget) {
        this.type    = "custom";
        this.name    = "_stoiqo_model_stack";
        this.node    = node;
        this.store   = storeWidget;
        this.serialize = false;
        this.options = { serialize: false };
        this.models  = [];
        this.hits    = [];
        this.lastClick = 0;
    }

    // Nessun valore proprio; tutto vive nel widget storage JSON.
    get value() { return ""; }
    set value(_v) {}

    // ── Persistence ───────────────────────────────────────────────────────────

    loadFromStore() {
        let parsed = [];
        try {
            const raw  = this.store ? this.store.value : "[]";
            const data = JSON.parse(raw || "[]");
            if (Array.isArray(data)) parsed = data;
        } catch (e) {
            parsed = [];
        }
        this.models = parsed
            .filter(m => m && typeof m.name === "string" && m.name)
            .map(m => newModel(m.name, m));
        this.enforceSingleActive();
    }

    // Una sola uscita: un solo modello attivo alla volta.
    enforceSingleActive(prefer = null) {
        let keep = prefer && prefer.enabled ? prefer : this.models.find(m => m.enabled);
        this.models.forEach(m => { m.enabled = (m === keep); });
    }

    sync() {
        if (this.store) {
            this.store.value = JSON.stringify(this.models.map(m => ({ ...m })));
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

    // ── Size ──────────────────────────────────────────────────────────────────

    totalHeight() {
        return PAD + HEAD_H + this.models.length * ROW_H + 6 + BTN_H + PAD;
    }

    computeSize(width) {
        return [width, this.totalHeight()];
    }

    computeLayoutSize() {
        const h = this.totalHeight();
        return { minHeight: h, maxHeight: h, minWidth: MIN_WIDTH };
    }

    // ── Draw ──────────────────────────────────────────────────────────────────

    draw(ctx, node, width, posY) {
        this.hits = [];
        const x0  = 10;
        const w   = width - 20;
        let   y   = posY + PAD;

        ctx.save();
        ctx.textBaseline = "middle";

        // ── Header ────────────────────────────────────────────────────────────
        // Header: active model (single output)
        const active = this.models.find(m => m.enabled);
        ctx.font      = "bold 11px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
        ctx.textAlign = "left";
        ctx.fillStyle = "#2997ff";
        ctx.fillText(`Model Stack · ${this.models.length} models · active: ${active ? baseName(active.name) : "none"}`.slice(0, 70), x0 + 2, y + HEAD_H / 2);
        y += HEAD_H;

        // ── Model rows ────────────────────────────────────────────────────────
        if (this.models.length === 0) {
            ctx.font      = "italic 11px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
            ctx.fillStyle = "#64748b";
            ctx.textAlign = "center";
            ctx.fillText("No models — click \"+ Add Model to Stack\"", x0 + w / 2, y + ROW_H / 2);
            y += ROW_H;
        } else {
            this.models.forEach((model, idx) => {
                const rY = y + 2;
                const rH = ROW_H - 4;
                const on = model.enabled;

                // Sfondo riga
                ctx.fillStyle   = on ? "rgba(41, 151, 255, 0.08)" : "rgba(255,255,255,0.03)";
                ctx.strokeStyle = on ? "rgba(41, 151, 255, 0.35)" : "rgba(255,255,255,0.08)";
                ctx.lineWidth   = 1;
                roundRect(ctx, x0, rY, w, rH, 5);
                ctx.fill();
                ctx.stroke();

                // Toggle pill
                const tW = 28, tH = 14;
                const tX = x0 + 6, tY = rY + (rH - tH) / 2;
                ctx.fillStyle = on ? "#2997ff" : "#475569";
                roundRect(ctx, tX, tY, tW, tH, 7);
                ctx.fill();
                ctx.fillStyle = "#0f172a";
                ctx.beginPath();
                ctx.arc(on ? tX + tW - 7 : tX + 7, tY + tH / 2, 5, 0, Math.PI * 2);
                ctx.fill();
                this.hits.push({
                    x: tX - 2, y: rY, w: tW + 4, h: rH,
                    action: () => {
                        model.enabled = !model.enabled;
                        this.enforceSingleActive(model);
                        this.sync();
                    },
                });

                // Pulsante rimuovi [✕]
                const xW = 18;
                const xX = x0 + w - xW - 4;
                const xY = rY + (rH - xW) / 2;

                // Opzioni avanzate [⚙]
                const gX = xX - xW - 3;
                ctx.fillStyle = "rgba(255,255,255,0.08)";
                roundRect(ctx, gX, xY, xW, xW, 3);
                ctx.fill();
                ctx.fillStyle = "#cbd5e1";
                ctx.font      = "12px sans-serif";
                ctx.textAlign = "center";
                ctx.fillText("⚙", gX + xW / 2, xY + xW / 2 + 0.5);
                this.hits.push({ x: gX, y: xY, w: xW, h: xW, action: (ev) => this.showAdvancedMenu(ev, model) });

                // Chip precisione
                ctx.font = "10px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
                const pLabel = model.precision;
                const pW = 84;
                const pX = gX - pW - 3;
                ctx.fillStyle = "rgba(0,0,0,0.3)";
                roundRect(ctx, pX, xY, pW, xW, 3);
                ctx.fill();
                ctx.fillStyle = on ? "#f1f5f9" : "#64748b";
                ctx.textAlign = "center";
                ctx.fillText(fitText(ctx, pLabel, pW - 6), pX + pW / 2, xY + xW / 2 + 0.5);
                this.hits.push({
                    x: pX, y: xY, w: pW, h: xW,
                    action: (ev) => this.pickFrom(ev, "Precisione", PRECISIONS, model.precision, v => { model.precision = v; this.sync(); }),
                });

                ctx.fillStyle   = "rgba(239, 68, 68, 0.12)";
                ctx.strokeStyle = "rgba(239, 68, 68, 0.35)";
                ctx.lineWidth   = 1;
                roundRect(ctx, xX, xY, xW, xW, 3);
                ctx.fill();
                ctx.stroke();
                ctx.fillStyle = "#f87171";
                ctx.font      = "bold 11px sans-serif";
                ctx.textAlign = "center";
                ctx.fillText("✕", xX + xW / 2, xY + xW / 2);
                this.hits.push({
                    x: xX, y: xY, w: xW, h: xW,
                    action: () => { this.models.splice(idx, 1); this.sync(); },
                });

                // Model name (click to pick)
                const nX   = tX + tW + 8;
                const nW   = pX - nX - 8;
                ctx.font      = "12px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
                ctx.textAlign = "left";
                ctx.fillStyle = on ? "#e2e8f0" : "#64748b";
                const disp = baseName(model.name || "(select model)");
                ctx.fillText(fitText(ctx, disp, nW), nX, rY + rH / 2 + 0.5);
                this.hits.push({
                    x: nX, y: rY, w: nW, h: rH,
                    action: (ev) => this.pickModel(ev, model),
                });

                y += ROW_H;
            });
        }

        // ── "+ Add Model to Stack" button ─────────────────────────────────────
        y += 6;
        ctx.fillStyle   = "rgba(41, 151, 255, 0.12)";
        ctx.strokeStyle = "rgba(41, 151, 255, 0.5)";
        ctx.lineWidth   = 1;
        roundRect(ctx, x0, y, w, BTN_H - 4, 6);
        ctx.fill();
        ctx.stroke();
        ctx.fillStyle = "#2997ff";
        ctx.font      = "bold 12px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("+ Add Model to Stack", x0 + w / 2, y + (BTN_H - 4) / 2 + 0.5);
        this.hits.push({
            x: x0, y, w, h: BTN_H - 4,
            action: (ev) => this.addModel(ev),
        });

        ctx.restore();
    }

    // ── Actions ───────────────────────────────────────────────────────────────

    async addModel(ev) {
        await this.pickModel(ev, null);
    }

    async pickModel(ev, targetModel) {
        const list = await fetchModelList(true);
        const LG   = window.LiteGraph;
        if (!LG || !LG.ContextMenu) return;

        if (!list.length) {
            new LG.ContextMenu(
                [{ content: "No models found in ComfyUI directories", disabled: true }],
                { event: ev }
            );
            return;
        }

        const onPick = (chosen) => {
            if (!chosen || typeof chosen.value !== "string") return;
            if (targetModel) {
                targetModel.name = chosen.value;
            } else {
                const nm = newModel(chosen.value);
                this.models.push(nm);
                this.enforceSingleActive(nm);
            }
            this.sync();
        };

        // Raggruppa per sub-cartella (stesso pattern LoRA stack)
        const hasFolders = list.some(n => /[\\\/]/.test(n));
        if (!hasFolders) {
            new LG.ContextMenu(
                list.map(n => ({ content: baseName(n), value: n })),
                { event: ev, title: "Modello", callback: onPick }
            );
            return;
        }

        const groups    = new Map();
        const rootFiles = [];
        for (const n of list) {
            const parts = n.split(/[\\\/]/);
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
                        { event: e, parentMenu: menu, callback: onPick }
                    );
                    return true;
                },
            });
        }
        rootFiles.forEach(n => items.push({ content: baseName(n), value: n }));

        new LG.ContextMenu(items, { event: ev, title: "Model", callback: onPick });
    }

    pickFrom(ev, title, options, current, onChoose) {
        const LG = window.LiteGraph;
        if (!LG || !LG.ContextMenu) return;
        new LG.ContextMenu(
            options.map(o => ({ content: o === current ? `✓ ${o}` : o, value: o })),
            { event: ev, title, callback: (c) => { if (c && c.value !== undefined) onChoose(c.value); } }
        );
    }

    showAdvancedMenu(ev, model) {
        const LG = window.LiteGraph;
        if (!LG || !LG.ContextMenu) return;
        const sub = (title, options, key) => ({
            content: `${title}: ${model[key]}`,
            has_submenu: true,
            callback: (_v, _o, e, menu) => {
                new LG.ContextMenu(
                    options.map(o => ({ content: o === model[key] ? `✓ ${o}` : o, value: o })),
                    { event: e, parentMenu: menu, callback: (c) => { if (c && c.value !== undefined) { model[key] = c.value; this.sync(); } } }
                );
                return true;
            },
        });
        const items = [
            sub("Attention", ATTENTIONS, "attention"),
            sub("Clip type", CLIP_TYPES, "clip_type"),
            sub("Flow shift", _presets, "flow_shift_preset"),
            {
                content: `Custom shift: ${model.custom_shift.toFixed(2)}`,
                callback: (_v, _o, e) => app.canvas.prompt("Custom shift", model.custom_shift, (val) => {
                    const n = parseFloat(val);
                    if (Number.isFinite(n)) { model.custom_shift = Math.max(0, Math.min(100, n)); this.sync(); }
                }, e),
            },
            {
                content: `Custom Path / API: ${model.custom_path || "—"}`,
                callback: (_v, _o, e) => app.canvas.prompt("Folder path or API endpoint", model.custom_path, (val) => {
                    model.custom_path = String(val || "").trim();
                    this.sync();
                }, e),
            },
        ];
        new LG.ContextMenu(items, { event: ev, title: baseName(model.name) });
    }

    // ── Mouse handler (API LiteGraph corretta) ────────────────────────────────

    mouse(event, pos, node) {
        if (!event || (event.type !== "pointerdown" && event.type !== "mousedown")) return false;
        if (!pos) return false;

        const now = performance.now();
        if (now - this.lastClick < 150) return true; // de-dup pointerdown + mousedown

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

// ── Setup nodo ────────────────────────────────────────────────────────────────

function hideWidget(w) {
    if (!w) return;
    w.hidden      = true;
    w.computeSize = () => [0, -4];
    w.draw        = () => {};
    if (w.inputEl) {
        w.inputEl.hidden            = true;
        w.inputEl.style.display     = "none";
    }
}

function setupModelLoaderNodeUI(node) {
    if (!node) return;
    if (node.size && node.size[0] < MIN_WIDTH) node.size[0] = MIN_WIDTH;

    // Già inizializzato? (controllo per nome: robusto anche se il bundle viene caricato due volte)
    const STACK_NAME = "_stoiqo_model_stack";
    if (node.widgets) {
        const dups = node.widgets.filter(w => w.name === STACK_NAME);
        for (const extra of dups.slice(1)) {
            node.widgets.splice(node.widgets.indexOf(extra), 1);
        }
    }
    let stackWidget = node.widgets ? node.widgets.find(w => w.name === STACK_NAME) : null;
    if (stackWidget && !stackWidget.loadFromStore) stackWidget = null;
    if (!stackWidget) {
        // Trova e nasconde il widget storage JSON
        const store = node.widgets ? node.widgets.find(w => w.name === "model_stack") : null;
        if (store) {
            hideWidget(store);
        }

        // Nasconde tutti i widget legacy del backend
        if (node.widgets) {
            for (const w of node.widgets) {
                if (LEGACY_WIDGET_NAMES.includes(w.name)) hideWidget(w);
            }
        }

        stackWidget = new ModelStackWidget(node, store);
        node.addCustomWidget(stackWidget);
        node.stoiqoModelWidget = stackWidget;
    }

    stackWidget.loadFromStore();
    stackWidget.resizeNode();
    node.setDirtyCanvas(true, true);
}

export function setupModelLoaderNode(nodeType, nodeData, appInstance) {
    if (!MODEL_NODE_NAMES.includes(nodeData.name)) return;

    const origCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
        if (origCreated) origCreated.apply(this, arguments);
        setupModelLoaderNodeUI(this);
    };

    const origConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
        if (origConfigure) origConfigure.apply(this, arguments);
        setupModelLoaderNodeUI(this);
    };
}
