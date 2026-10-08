import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";
import { StoiqoSectionDividerWidget } from "../utils/core.js";

/**
 * [STOIQO] Trio Image Loader Node — Interactive Gallery Widget
 * Features:
 * - Single Hero Preview with smooth aspect fit & HUD telemetry
 * - 3 Clickable Thumbnails below for instant slot switching
 * - Suppresses all native ComfyUI output previews (Zero Duplicate Previews)
 * - Robust path & subfolder resolution supporting both ComfyUI v1 and modern v2 formats
 * - Full mouse interaction with both LiteGraph widget.mouse and node.onMouseDown fallbacks
 */

export function setupTrioLoaderNode(nodeType, nodeData, appInstance) {
    const targetNames = [
        "StoiqoTripleImageLoaderNode",
        "[STOIQO] Trio Image Loader (Hero & Thumbs)",
    ];

    if (!targetNames.includes(nodeData.name)) return;

    const MIN_WIDTH = 460;
    const MIN_HEIGHT = 740;

    function parseImageDescriptor(val) {
        if (!val || typeof val !== "string" || val === "none") return null;

        // Strip trailing tags like " [input]", " [output]", " [temp]"
        let clean = val.replace(/\s*\[(input|output|temp)\]\s*$/i, "").trim();
        if (!clean || clean === "none") return null;

        let subfolder = "";
        let filename = clean;

        // Normalize separators
        clean = clean.replace(/\\/g, "/");
        const lastSlash = clean.lastIndexOf("/");
        if (lastSlash !== -1) {
            subfolder = clean.substring(0, lastSlash);
            filename = clean.substring(lastSlash + 1);
        }

        return { filename, subfolder, type: "input" };
    }

    function toImageUrl(rawVal) {
        const desc = parseImageDescriptor(rawVal);
        if (!desc) return "";

        const params = new URLSearchParams();
        params.set("filename", desc.filename);
        params.set("type", desc.type || "input");
        if (desc.subfolder) {
            params.set("subfolder", desc.subfolder);
        }
        params.set("t", Date.now().toString());

        return api.apiURL(`/view?${params.toString()}`);
    }

    class StoiqoTrioGalleryWidget {
        constructor(node) {
            this.type = "custom";
            this.name = "_stoiqo_trio_gallery";
            this.value = {};
            this.options = { serialize: false };
            this.node = node;

            this.activeFocus = 1; // 1, 2, or 3
            this.images = [null, null, null]; // Image objects for slot 1, 2, 3
            this.rawValues = ["", "", ""]; // Stored raw widget values
            this.meta = [null, null, null]; // { width, height }
            this.thumbRects = []; // Hit areas for thumbnails
            this.heroRect = { x: 0, y: 0, w: 0, h: 0 };
        }

        serializeValue() {
            return undefined;
        }

        computeSize(width) {
            const pad = 12;
            const availableWidth = (width || 460) - pad * 2;
            // Vertical portrait ratio ~1.15 to 1.25 for large Hero preview
            const heroHeight = Math.max(360, Math.round(availableWidth * 1.15));
            const thumbsHeight = 96;
            return [width, heroHeight + thumbsHeight + 36];
        }

        setSlotImage(slotIndex, rawVal) {
            if (slotIndex < 0 || slotIndex > 2) return;
            if (this.rawValues[slotIndex] === rawVal && this.images[slotIndex]) return;

            this.rawValues[slotIndex] = rawVal;
            const url = toImageUrl(rawVal);

            if (!url) {
                this.images[slotIndex] = null;
                this.meta[slotIndex] = null;
                if (this.node) this.node.setDirtyCanvas(true, true);
                return;
            }

            const img = new Image();
            img.onload = () => {
                this.meta[slotIndex] = { width: img.naturalWidth, height: img.naturalHeight };
                if (this.node) this.node.setDirtyCanvas(true, true);
            };
            img.onerror = () => {
                this.images[slotIndex] = null;
                this.meta[slotIndex] = null;
                if (this.node) this.node.setDirtyCanvas(true, true);
            };
            img.src = url;
            this.images[slotIndex] = img;
        }

        syncFromWidgets() {
            if (!this.node || !this.node.widgets) return;
            const w1 = this.node.widgets.find((w) => w.name === "image_1");
            const w2 = this.node.widgets.find((w) => w.name === "image_2");
            const w3 = this.node.widgets.find((w) => w.name === "image_3");
            const wFocus = this.node.widgets.find((w) => w.name === "active_focus");

            const v1 = w1 ? String(w1.value || "") : "";
            const v2 = w2 ? String(w2.value || "") : "";
            const v3 = w3 ? String(w3.value || "") : "";

            if (v1 !== this.rawValues[0]) this.setSlotImage(0, v1);
            if (v2 !== this.rawValues[1]) this.setSlotImage(1, v2);
            if (v3 !== this.rawValues[2]) this.setSlotImage(2, v3);

            if (wFocus && wFocus.value) {
                if (wFocus.value === "Slot 2") this.activeFocus = 2;
                else if (wFocus.value === "Slot 3") this.activeFocus = 3;
                else this.activeFocus = 1;
            }
        }

        handlePointerDown(localPos, node) {
            const [x, y] = localPos;
            for (const r of this.thumbRects) {
                if (x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h) {
                    this.activeFocus = r.slot;
                    if (this.node && this.node.widgets) {
                        const wFocus = this.node.widgets.find((w) => w.name === "active_focus");
                        if (wFocus) {
                            wFocus.value = `Slot ${r.slot}`;
                            if (wFocus.callback) {
                                wFocus.callback(wFocus.value);
                            }
                        }
                    }
                    if (this.node) this.node.setDirtyCanvas(true, true);
                    return true;
                }
            }
            return false;
        }

        mouse(event, pos, node) {
            if (event.type === "mousedown" || event.type === "pointerdown") {
                return this.handlePointerDown(pos, node);
            }
            return false;
        }

        draw(ctx, node, width, posY, height) {
            const nodeWidth = (node && node.size) ? node.size[0] : width;
            const pad = 12;
            const availableWidth = nodeWidth - pad * 2;

            // Sync with current dropdown values
            this.syncFromWidgets();

            const heroHeight = Math.max(360, Math.round(availableWidth * 1.15));
            const heroY = posY + 6;
            this.heroRect = { x: pad, y: heroY, w: availableWidth, h: heroHeight };

            ctx.save();

            // 1. HERO CONTAINER (Main Large Preview)
            ctx.fillStyle = "#0c0f17";
            ctx.strokeStyle = "#1e2638";
            ctx.lineWidth = 1.2;
            this._roundRect(ctx, pad, heroY, availableWidth, heroHeight, 8, true, true);

            const activeIdx = this.activeFocus - 1;
            const activeImg = this.images[activeIdx];
            const activeMeta = this.meta[activeIdx];
            const activeRaw = this.rawValues[activeIdx];

            if (activeImg && activeImg.complete && activeImg.naturalWidth > 0) {
                // Clip image within hero container
                ctx.save();
                this._roundRect(ctx, pad, heroY, availableWidth, heroHeight, 8, false, false);
                ctx.clip();

                // Aspect Fit calculation
                const imgW = activeImg.naturalWidth;
                const imgH = activeImg.naturalHeight;
                const scale = Math.min((availableWidth - 8) / imgW, (heroHeight - 8) / imgH);
                const drawW = imgW * scale;
                const drawH = imgH * scale;
                const drawX = pad + (availableWidth - drawW) / 2;
                const drawY = heroY + (heroHeight - drawH) / 2;

                ctx.drawImage(activeImg, drawX, drawY, drawW, drawH);
                ctx.restore();

                // Top-Left Badge: SLOT HERO
                const slotColors = ["#a855f7", "#38bdf8", "#10b981"];
                const slotColor = slotColors[activeIdx] || "#a855f7";

                ctx.fillStyle = "rgba(12, 15, 23, 0.88)";
                this._roundRect(ctx, pad + 8, heroY + 8, 86, 22, 4, true, false);
                ctx.fillStyle = slotColor;
                ctx.font = "bold 10px Inter, system-ui, sans-serif";
                ctx.textAlign = "left";
                ctx.fillText(`★ SLOT ${this.activeFocus} HERO`, pad + 14, heroY + 23);

                // Top-Right Badge: Resolution
                if (activeMeta) {
                    const resStr = `${activeMeta.width}×${activeMeta.height}`;
                    ctx.font = "10px monospace";
                    const tw = ctx.measureText(resStr).width;
                    ctx.fillStyle = "rgba(12, 15, 23, 0.88)";
                    this._roundRect(ctx, pad + availableWidth - tw - 18, heroY + 8, tw + 12, 22, 4, true, false);
                    ctx.fillStyle = "#38bdf8";
                    ctx.fillText(resStr, pad + availableWidth - tw - 12, heroY + 23);
                }
            } else {
                // Empty state placeholder
                ctx.fillStyle = "#475569";
                ctx.font = "bold 12px Inter, system-ui, sans-serif";
                ctx.textAlign = "center";
                const isNone = !activeRaw || activeRaw === "none";
                const emptyMsg = isNone
                    ? `[Slot ${this.activeFocus}: Nessuna immagine selezionata]`
                    : `[Slot ${this.activeFocus}: Caricamento in corso...]`;
                ctx.fillText(emptyMsg, pad + availableWidth / 2, heroY + heroHeight / 2 - 8);

                ctx.font = "10px Inter, system-ui, sans-serif";
                ctx.fillStyle = "#334155";
                ctx.fillText("Seleziona un'immagine dal menu sopra per visualizzarla", pad + availableWidth / 2, heroY + heroHeight / 2 + 12);
                ctx.textAlign = "left";
            }

            // 2. THUMBNAILS STRIP BELOW
            const thumbsY = heroY + heroHeight + 12;
            const thumbHeight = 96;
            const gap = 8;
            const thumbWidth = Math.floor((availableWidth - gap * 2) / 3);

            this.thumbRects = [];

            for (let i = 0; i < 3; i++) {
                const tx = pad + i * (thumbWidth + gap);
                const ty = thumbsY;
                this.thumbRects.push({ x: tx, y: ty, w: thumbWidth, h: thumbHeight, slot: i + 1 });

                const isFocused = this.activeFocus === (i + 1);
                const thumbImg = this.images[i];
                const rawName = this.rawValues[i];

                // Card background & Active Glow
                ctx.fillStyle = isFocused ? "#1a162b" : "#0d111a";
                ctx.strokeStyle = isFocused ? "#c084fc" : "#242d42";
                ctx.lineWidth = isFocused ? 2 : 1;
                this._roundRect(ctx, tx, ty, thumbWidth, thumbHeight, 6, true, true);

                if (thumbImg && thumbImg.complete && thumbImg.naturalWidth > 0) {
                    ctx.save();
                    this._roundRect(ctx, tx + 2, ty + 2, thumbWidth - 4, thumbHeight - 24, 4, false, false);
                    ctx.clip();

                    // Aspect Cover in thumbnail area
                    const iw = thumbImg.naturalWidth;
                    const ih = thumbImg.naturalHeight;
                    const areaW = thumbWidth - 4;
                    const areaH = thumbHeight - 24;
                    const scale = Math.max(areaW / iw, areaH / ih);
                    const sw = iw * scale;
                    const sh = ih * scale;
                    const sx = tx + 2 + (areaW - sw) / 2;
                    const sy = ty + 2 + (areaH - sh) / 2;

                    ctx.globalAlpha = isFocused ? 1.0 : 0.60;
                    ctx.drawImage(thumbImg, sx, sy, sw, sh);
                    ctx.restore();
                } else {
                    ctx.fillStyle = "#334155";
                    ctx.font = "10px Inter, system-ui, sans-serif";
                    ctx.textAlign = "center";
                    ctx.fillText(rawName === "none" || !rawName ? "(Vuoto)" : "...", tx + thumbWidth / 2, ty + (thumbHeight - 24) / 2 + 3);
                    ctx.textAlign = "left";
                }

                // Bottom Slot Label & Indicator
                ctx.fillStyle = isFocused ? "#c084fc" : "#64748b";
                ctx.font = isFocused ? "bold 10px Inter, system-ui, sans-serif" : "10px Inter, system-ui, sans-serif";
                ctx.textAlign = "center";
                const slotLabels = ["1: Main", "2: Sec", "3: Ref"];
                const labelText = isFocused ? `▶ ${slotLabels[i]}` : slotLabels[i];
                ctx.fillText(labelText, tx + thumbWidth / 2, ty + thumbHeight - 7);
                ctx.textAlign = "left";
            }

            ctx.restore();
        }

        _roundRect(ctx, x, y, width, height, radius, fill, stroke) {
            ctx.beginPath();
            ctx.moveTo(x + radius, y);
            ctx.lineTo(x + width - radius, y);
            ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
            ctx.lineTo(x + width, y + height - radius);
            ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
            ctx.lineTo(x + radius, y + height);
            ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
            ctx.lineTo(x, y + radius);
            ctx.quadraticCurveTo(x, y, x + radius, y);
            ctx.closePath();
            if (fill) ctx.fill();
            if (stroke) ctx.stroke();
        }
    }

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
        const ret = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

        // Suppress native ComfyUI output preview images to prevent double previews
        this.hideOutputImages = true;
        this.imgs = null;
        this.images = null;

        this.size = this.size || [MIN_WIDTH, MIN_HEIGHT];
        if (this.size[0] < MIN_WIDTH) this.size[0] = MIN_WIDTH;
        if (this.size[1] < MIN_HEIGHT) this.size[1] = MIN_HEIGHT;

        // Visual header divider
        this.addCustomWidget(new StoiqoSectionDividerWidget(1, "MULTI-IMAGE TRIO LOADER", "#a855f7"));

        // Interactive Gallery Widget
        const galleryWidget = new StoiqoTrioGalleryWidget(this);
        this.addCustomWidget(galleryWidget);
        this._trio_gallery = galleryWidget;

        // Hook onExecuted
        const origOnExecuted = this.onExecuted;
        this.onExecuted = function (message) {
            // Prevent ComfyUI from injecting redundant preview boxes
            this.hideOutputImages = true;
            this.imgs = null;
            this.images = null;

            if (origOnExecuted) origOnExecuted.apply(this, arguments);

            if (message && message.trio_info) {
                for (const imgData of message.trio_info) {
                    if (imgData.slot && imgData.filename) {
                        galleryWidget.setSlotImage(imgData.slot - 1, imgData.filename);
                    }
                }
            }
            if (message && message.active_slot && message.active_slot.length > 0) {
                galleryWidget.activeFocus = message.active_slot[0];
                this.setDirtyCanvas(true, true);
            }
        };

        // Hook onMouseDown as fallback
        const origOnMouseDown = this.onMouseDown;
        this.onMouseDown = function (event, localPos, graphCanvas) {
            if (galleryWidget && galleryWidget.handlePointerDown(localPos, this)) {
                return true;
            }
            return origOnMouseDown ? origOnMouseDown.apply(this, arguments) : false;
        };

        return ret;
    };

    // Override onDrawBackground to suppress native ComfyUI preview rendering
    const origDrawBackground = nodeType.prototype.onDrawBackground;
    nodeType.prototype.onDrawBackground = function (ctx) {
        this.hideOutputImages = true;
        this.imgs = null;
        this.images = null;
        if (origDrawBackground) {
            origDrawBackground.apply(this, arguments);
        }
    };
}
