import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";
import { StoiqoSectionDividerWidget, currentDownloadProgress } from "../utils/core.js";

export function setupImageCompareNode(nodeType, nodeData, app) {
        // 5. VISUAL COMPARE SLIDER & SYNCHRONIZED ZOOM ENHANCEMENTS
        // ══════════════════════════════════════════════════════════════════════
        const compareTargetNames = [
            "StoiqoImageCompareNode",
            "[STOIQO] Visual Compare Slider & Zoom",
        ];

        if (compareTargetNames.includes(nodeData.name)) {
            const MIN_WIDTH = 520;
            const MIN_HEIGHT = 560;

            function imageDataToUrl(data) {
                if (!data) return "";
                const sub = data.subfolder ? `&subfolder=${encodeURIComponent(data.subfolder)}` : "";
                const typ = data.type ? `&type=${encodeURIComponent(data.type)}` : "&type=temp";
                const fmt = app.getPreviewFormatParam ? app.getPreviewFormatParam() : "";
                const rnd = app.getRandParam ? app.getRandParam() : "";
                return api.apiURL(`/view?filename=${encodeURIComponent(data.filename)}${typ}${sub}${fmt}${rnd}`);
            }

            class StoiqoCompareCanvasWidget {
                constructor(node) {
                    this.type = "custom";
                    this.name = "_stoiqo_compare_canvas";
                    this.value = {};
                    this.options = { serialize: false };
                    this.node = node;
                    this.imgA = null;
                    this.imgB = null;
                    this.labelA = "Original";
                    this.labelB = "Upscaled";
                    this.splitX = 0.5;
                    this.zoom = 1.0;
                    this.panX = 0;
                    this.panY = 0;
                    this.mode = "split"; // "split", "toggle", "side"
                    this.toggleShowB = false;
                    this.isDraggingSplit = false;
                    this.isPanning = false;
                    this.lastMouse = [0, 0];
                    this.btnHitAreas = [];
                    this.viewportRect = { x: 0, y: 0, w: 0, h: 0 };
                }

                serializeValue() {
                    return undefined;
                }

                computeSize(width) {
                    return [width, 440];
                }

                setImages(dataList) {
                    if (!dataList || dataList.length < 2) return;
                    this.imgA = new Image();
                    this.imgB = new Image();
                    this.imgA.onload = () => { if (this.node) this.node.setDirtyCanvas(true, true); };
                    this.imgB.onload = () => { if (this.node) this.node.setDirtyCanvas(true, true); };
                    this.imgA.src = imageDataToUrl(dataList[0]);
                    this.imgB.src = imageDataToUrl(dataList[1]);
                    this.labelA = dataList[0].label || "Original";
                    this.labelB = dataList[1].label || "Upscaled";
                    this.resetView();
                }

                resetView() {
                    this.zoom = 1.0;
                    this.panX = 0;
                    this.panY = 0;
                    this.splitX = 0.5;
                    this.toggleShowB = false;
                    if (this.node) this.node.setDirtyCanvas(true, true);
                }

                draw(ctx, node, width, posY, height) {
                    const nodeW = node.size ? node.size[0] : width;
                    const nodeH = node.size ? node.size[1] : MIN_HEIGHT;
                    const vY = posY + 6;
                    const vH = Math.max(260, nodeH - vY - 14);
                    const vW = nodeW - 24;
                    const vX = 12;

                    this.viewportRect = { x: vX, y: vY + 32, w: vW, h: vH - 32 };
                    this.btnHitAreas = [];

                    ctx.save();

                    // ── 1. Mini Toolbar ───────────────────────────────────────
                    const barY = vY;
                    const barH = 26;

                    // Toolbar background
                    ctx.fillStyle = "rgba(15, 23, 42, 0.65)";
                    if (ctx.roundRect) {
                        ctx.beginPath();
                        ctx.roundRect(vX, barY, vW, barH, 4);
                        ctx.fill();
                    } else {
                        ctx.fillRect(vX, barY, vW, barH);
                    }

                    // Mode buttons: Solo A, Solo B, Slider A-B, Side-by-Side
                    const modes = [
                        { key: "only_a", label: "Solo A", activeColor: "#38bdf8" },
                        { key: "only_b", label: "Solo B", activeColor: "#c084fc" },
                        { key: "split", label: "↔ Slider A-B", activeColor: "#2dd4bf" },
                        { key: "side", label: "◫ Side-by-Side", activeColor: "#2dd4bf" },
                    ];

                    let btnX = vX + 6;
                    ctx.font = "bold 9px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";

                    modes.forEach(m => {
                        const active = this.mode === m.key;
                        const textW = ctx.measureText(m.label).width;
                        const bW = textW + 14;
                        const bH = 18;
                        const bY = barY + 4;
                        const col = m.activeColor || "#2dd4bf";

                        ctx.fillStyle = active ? (m.key === "only_a" ? "rgba(56, 189, 248, 0.22)" : (m.key === "only_b" ? "rgba(192, 132, 252, 0.22)" : "rgba(45, 212, 191, 0.22)")) : "rgba(255, 255, 255, 0.06)";
                        ctx.strokeStyle = active ? col : "rgba(255, 255, 255, 0.12)";
                        ctx.lineWidth = 1;

                        if (ctx.roundRect) {
                            ctx.beginPath();
                            ctx.roundRect(btnX, bY, bW, bH, 3);
                            ctx.fill();
                            ctx.stroke();
                        } else {
                            ctx.fillRect(btnX, bY, bW, bH);
                            ctx.strokeRect(btnX, bY, bW, bH);
                        }

                        ctx.fillStyle = active ? col : "#94a3b8";
                        ctx.fillText(m.label, btnX + 7, bY + 12);

                        this.btnHitAreas.push({
                            x: btnX, y: bY, w: bW, h: bH,
                            action: () => { this.mode = m.key; node.setDirtyCanvas(true, true); }
                        });

                        btnX += bW + 6;
                    });

                    // Reset button on the right
                    const resetLabel = "⟲ Reset Zoom";
                    const rTextW = ctx.measureText(resetLabel).width;
                    const rW = rTextW + 14;
                    const rX = vX + vW - rW - 6;
                    const rY = barY + 4;

                    ctx.fillStyle = "rgba(255, 255, 255, 0.08)";
                    ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
                    if (ctx.roundRect) {
                        ctx.beginPath();
                        ctx.roundRect(rX, rY, rW, 18, 3);
                        ctx.fill();
                        ctx.stroke();
                    } else {
                        ctx.fillRect(rX, rY, rW, 18);
                        ctx.strokeRect(rX, rY, rW, 18);
                    }
                    ctx.fillStyle = "#cbd5e1";
                    ctx.fillText(resetLabel, rX + 7, rY + 12);

                    this.btnHitAreas.push({
                        x: rX, y: rY, w: rW, h: 18,
                        action: () => { this.resetView(); }
                    });

                    // Zoom Indicator badge next to reset
                    const zoomPct = Math.round(this.zoom * 100);
                    const zoomLabel = `🔍 ${zoomPct}%`;
                    const zTextW = ctx.measureText(zoomLabel).width;
                    const zX = rX - zTextW - 14;
                    ctx.fillStyle = this.zoom > 1.01 ? "#38bdf8" : "#64748b";
                    ctx.fillText(zoomLabel, zX, rY + 12);

                    // ── 2. Viewport Canvas Rendering ──────────────────────────
                    const vp = this.viewportRect;

                    // Viewport border & background
                    ctx.fillStyle = "#090d14";
                    ctx.strokeStyle = "rgba(255, 255, 255, 0.12)";
                    ctx.lineWidth = 1;
                    if (ctx.roundRect) {
                        ctx.beginPath();
                        ctx.roundRect(vp.x, vp.y, vp.w, vp.h, 4);
                        ctx.fill();
                        ctx.stroke();
                    } else {
                        ctx.fillRect(vp.x, vp.y, vp.w, vp.h);
                        ctx.strokeRect(vp.x, vp.y, vp.w, vp.h);
                    }

                    // Placeholder if images are not yet loaded
                    if (!this.imgA || !this.imgB || !this.imgA.complete || !this.imgB.complete) {
                        ctx.fillStyle = "#64748b";
                        ctx.font = "12px sans-serif";
                        ctx.textAlign = "center";
                        ctx.fillText("Connect image_a and image_b and click Queue Prompt to compare", vp.x + vp.w / 2, vp.y + vp.h / 2);
                        ctx.restore();
                        return;
                    }

                    // Helper to compute aspect-fit bounding box within an arbitrary container
                    const computeFit = (natW, natH, boxW, boxH) => {
                        if (!natW || !natH || !boxW || !boxH) return { w: boxW, h: boxH };
                        const aspect = natW / natH;
                        const boxAspect = boxW / boxH;
                        let w, h;
                        if (aspect > boxAspect) {
                            w = boxW;
                            h = boxW / aspect;
                        } else {
                            h = boxH;
                            w = boxH * aspect;
                        }
                        return { w, h };
                    };

                    const natWA = this.imgA.naturalWidth || 1024;
                    const natHA = this.imgA.naturalHeight || 1024;
                    const natWB = this.imgB.naturalWidth || 1024;
                    const natHB = this.imgB.naturalHeight || 1024;

                    // Viewport Center: Fixed anchor point shared by BOTH images
                    const centerX = vp.x + vp.w / 2;
                    const centerY = vp.y + vp.h / 2;

                    // Compute INDEPENDENT natural aspect-fit sizes for A and B within the viewport
                    const fitA = computeFit(natWA, natHA, vp.w, vp.h);
                    const fitB = computeFit(natWB, natHB, vp.w, vp.h);

                    const halfWA = fitA.w / 2;
                    const halfHA = fitA.h / 2;
                    const halfWB = fitB.w / 2;
                    const halfHB = fitB.h / 2;

                    // Independent render functions: centered at the exact same point with synchronized pan & zoom
                    const renderImageA = (targetCtx = ctx) => {
                        targetCtx.save();
                        targetCtx.translate(centerX + this.panX * this.zoom, centerY + this.panY * this.zoom);
                        targetCtx.scale(this.zoom, this.zoom);
                        targetCtx.drawImage(this.imgA, -halfWA, -halfHA, fitA.w, fitA.h);
                        targetCtx.restore();
                    };

                    const renderImageB = (targetCtx = ctx) => {
                        targetCtx.save();
                        targetCtx.translate(centerX + this.panX * this.zoom, centerY + this.panY * this.zoom);
                        targetCtx.scale(this.zoom, this.zoom);
                        targetCtx.drawImage(this.imgB, -halfWB, -halfHB, fitB.w, fitB.h);
                        targetCtx.restore();
                    };

                    // ── Mode 1: Solo A ─────────────────────────────────────────
                    if (this.mode === "only_a") {
                        ctx.save();
                        ctx.beginPath();
                        ctx.rect(vp.x, vp.y, vp.w, vp.h);
                        ctx.clip();
                        renderImageA();
                        ctx.restore();
                    }
                    // ── Mode 2: Solo B ─────────────────────────────────────────
                    else if (this.mode === "only_b") {
                        ctx.save();
                        ctx.beginPath();
                        ctx.rect(vp.x, vp.y, vp.w, vp.h);
                        ctx.clip();
                        renderImageB();
                        ctx.restore();
                    }
                    // ── Mode 3: Split Slider (Viewport-Anchored Curtain) ──────
                    else if (this.mode === "split") {
                        const splitScreenX = vp.x + this.splitX * vp.w;

                        // 1. Draw Image A (Left side of curtain with its own natural aspect ratio)
                        ctx.save();
                        ctx.beginPath();
                        ctx.rect(vp.x, vp.y, this.splitX * vp.w, vp.h);
                        ctx.clip();
                        renderImageA();
                        ctx.restore();

                        // 2. Draw Image B (Right side of curtain with its own natural aspect ratio)
                        ctx.save();
                        ctx.beginPath();
                        ctx.rect(splitScreenX, vp.y, (1 - this.splitX) * vp.w, vp.h);
                        ctx.clip();
                        renderImageB();
                        ctx.restore();

                        // 3. Draw Splitter Line in Viewport space (Crisp, always visible regardless of zoom)
                        ctx.save();
                        ctx.strokeStyle = "#2dd4bf";
                        ctx.lineWidth = 2;
                        ctx.beginPath();
                        ctx.moveTo(splitScreenX, vp.y);
                        ctx.lineTo(splitScreenX, vp.y + vp.h);
                        ctx.stroke();

                        // Splitter Handle (Centered on split line)
                        const pillW = 32;
                        const pillH = 22;
                        const pillY = vp.y + vp.h / 2 - pillH / 2;
                        ctx.fillStyle = "#0f172a";
                        ctx.strokeStyle = "#2dd4bf";
                        ctx.lineWidth = 1.5;
                        if (ctx.roundRect) {
                            ctx.beginPath();
                            ctx.roundRect(splitScreenX - pillW / 2, pillY, pillW, pillH, 4);
                            ctx.fill();
                            ctx.stroke();
                        } else {
                            ctx.fillRect(splitScreenX - pillW / 2, pillY, pillW, pillH);
                            ctx.strokeRect(splitScreenX - pillW / 2, pillY, pillW, pillH);
                        }

                        // Arrow glyphs inside pill
                        ctx.fillStyle = "#2dd4bf";
                        ctx.font = "bold 10px sans-serif";
                        ctx.textAlign = "center";
                        ctx.textBaseline = "middle";
                        ctx.fillText("◄►", splitScreenX, pillY + pillH / 2 + 1);
                        ctx.restore();
                    }
                    // ── Mode 4: Side-by-Side (Synchronized) ────────────────────
                    else if (this.mode === "side") {
                        const midX = vp.x + vp.w / 2;
                        const halfW = vp.w / 2 - 1;

                        // Left half: Image A centered in left half with natural aspect ratio
                        const centerSideA_X = vp.x + halfW / 2;
                        const fitSideA = computeFit(natWA, natHA, halfW, vp.h);

                        ctx.save();
                        ctx.beginPath();
                        ctx.rect(vp.x, vp.y, halfW, vp.h);
                        ctx.clip();
                        ctx.translate(centerSideA_X + this.panX * this.zoom, centerY + this.panY * this.zoom);
                        ctx.scale(this.zoom, this.zoom);
                        ctx.drawImage(this.imgA, -fitSideA.w / 2, -fitSideA.h / 2, fitSideA.w, fitSideA.h);
                        ctx.restore();

                        // Right half: Image B centered in right half with natural aspect ratio
                        const centerSideB_X = (midX + 1) + halfW / 2;
                        const fitSideB = computeFit(natWB, natHB, halfW, vp.h);

                        ctx.save();
                        ctx.beginPath();
                        ctx.rect(midX + 1, vp.y, halfW, vp.h);
                        ctx.clip();
                        ctx.translate(centerSideB_X + this.panX * this.zoom, centerY + this.panY * this.zoom);
                        ctx.scale(this.zoom, this.zoom);
                        ctx.drawImage(this.imgB, -fitSideB.w / 2, -fitSideB.h / 2, fitSideB.w, fitSideB.h);
                        ctx.restore();

                        // Divider line
                        ctx.strokeStyle = "rgba(255, 255, 255, 0.25)";
                        ctx.lineWidth = 1;
                        ctx.beginPath();
                        ctx.moveTo(midX, vp.y);
                        ctx.lineTo(midX, vp.y + vp.h);
                        ctx.stroke();
                    }

                    // ── 3. Overlay Labels & Badges ────────────────────────────
                    ctx.font = "bold 9px sans-serif";
                    ctx.textAlign = "left";

                    // Label A (Top Left with natural resolution)
                    if (this.mode === "only_a" || this.mode === "split" || this.mode === "side") {
                        const labelAText = `◄ A: ${this.labelA.slice(0, 8)} (${natWA}×${natHA})`;
                        const lAW = ctx.measureText(labelAText).width + 12;
                        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
                        ctx.fillRect(vp.x + 8, vp.y + 8, lAW, 18);
                        ctx.fillStyle = "#38bdf8";
                        ctx.fillText(labelAText, vp.x + 14, vp.y + 20);
                    }

                    // Label B (Top Right with natural resolution)
                    if (this.mode === "only_b" || this.mode === "split" || this.mode === "side") {
                        const labelBText = `B: ${this.labelB.slice(0, 8)} (${natWB}×${natHB}) ►`;
                        const lBW = ctx.measureText(labelBText).width + 12;
                        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
                        ctx.fillRect(vp.x + vp.w - lBW - 8, vp.y + 8, lBW, 18);
                        ctx.fillStyle = "#c084fc";
                        ctx.fillText(labelBText, vp.x + vp.w - lBW - 2, vp.y + 20);
                    }

                    // Instruction pill if zoomed in
                    if (this.zoom > 1.05) {
                        const hint = "🔍 Drag to Pan • Scroll to Zoom";
                        const hintW = ctx.measureText(hint).width + 16;
                        const hintX = vp.x + (vp.w - hintW) / 2;
                        const hintY = vp.y + vp.h - 22;
                        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
                        if (ctx.roundRect) {
                            ctx.beginPath();
                            ctx.roundRect(hintX, hintY, hintW, 16, 3);
                            ctx.fill();
                        } else {
                            ctx.fillRect(hintX, hintY, hintW, 16);
                        }
                        ctx.fillStyle = "#94a3b8";
                        ctx.textAlign = "center";
                        ctx.fillText(hint, vp.x + vp.w / 2, hintY + 11);
                    }

                    ctx.restore();
                }

                handleMouseDown(e, localPos) {
                    if (!localPos) return false;
                    const [mx, my] = localPos;

                    // 1. Check toolbar buttons
                    for (const btn of this.btnHitAreas) {
                        if (mx >= btn.x && mx <= btn.x + btn.w && my >= btn.y && my <= btn.y + btn.h) {
                            btn.action();
                            if (this.node) this.node.setDirtyCanvas(true, true);
                            if (e && e.stopPropagation) e.stopPropagation();
                            return true;
                        }
                    }

                    // 2. Check viewport click
                    const vp = this.viewportRect;
                    if (mx >= vp.x && mx <= vp.x + vp.w && my >= vp.y && my <= vp.y + vp.h) {
                        if (this.mode === "split") {
                            const splitPixelX = vp.x + this.splitX * vp.w;
                            // If not zoomed in, or within 40px of split line: drag split curtain
                            if (this.zoom <= 1.05 || Math.abs(mx - splitPixelX) < 40) {
                                const relX = (mx - vp.x) / vp.w;
                                this.splitX = Math.max(0.01, Math.min(0.99, relX));
                                this.isDraggingSplit = true;
                                if (this.node) this.node.setDirtyCanvas(true, true);
                                if (e && e.stopPropagation) e.stopPropagation();
                                return true;
                            }
                        }

                        // Otherwise start panning (e.g. solo modes, side mode or zoomed in)
                        this.isPanning = true;
                        this.lastMouse = [mx, my];
                        if (this.node) this.node.setDirtyCanvas(true, true);
                        if (e && e.stopPropagation) e.stopPropagation();
                        return true;
                    }
                    return false;
                }

                handleMouseMove(e, localPos) {
                    if (!localPos) return false;
                    const [mx, my] = localPos;
                    const vp = this.viewportRect;

                    if (this.isDraggingSplit) {
                        const relX = (mx - vp.x) / vp.w;
                        this.splitX = Math.max(0.01, Math.min(0.99, relX));
                        if (this.node) this.node.setDirtyCanvas(true, true);
                        return true;
                    }

                    if (this.isPanning) {
                        const dx = mx - this.lastMouse[0];
                        const dy = my - this.lastMouse[1];
                        this.panX += dx / this.zoom;
                        this.panY += dy / this.zoom;
                        this.lastMouse = [mx, my];
                        if (this.node) this.node.setDirtyCanvas(true, true);
                        return true;
                    }

                    return false;
                }

                handleMouseUp(e, localPos) {
                    const wasActive = this.isDraggingSplit || this.isPanning;
                    this.isDraggingSplit = false;
                    this.isPanning = false;
                    if (wasActive && this.node) {
                        this.node.setDirtyCanvas(true, true);
                    }
                    return wasActive;
                }

                mouse(event, pos, node) {
                    if (event.type === "pointerdown" || event.type === "mousedown") {
                        return this.handleMouseDown(event, pos);
                    }
                    if (event.type === "pointermove" || event.type === "mousemove") {
                        return this.handleMouseMove(event, pos);
                    }
                    if (event.type === "pointerup" || event.type === "mouseup") {
                        return this.handleMouseUp(event, pos);
                    }
                    return false;
                }

                handleWheel(e, localPos) {
                    const vp = this.viewportRect;
                    const [mx, my] = localPos;
                    if (mx >= vp.x && mx <= vp.x + vp.w && my >= vp.y && my <= vp.y + vp.h) {
                        const delta = e.deltaY < 0 ? 1.15 : 0.85;
                        const oldZoom = this.zoom;
                        const newZoom = Math.max(1.0, Math.min(10.0, this.zoom * delta));

                        if (newZoom === 1.0) {
                            this.panX = 0;
                            this.panY = 0;
                        } else {
                            // Keep point under cursor stable during zoom
                            const cursorRelX = (mx - (vp.x + vp.w / 2)) / oldZoom - this.panX;
                            const cursorRelY = (my - (vp.y + vp.h / 2)) / oldZoom - this.panY;
                            this.panX = (mx - (vp.x + vp.w / 2)) / newZoom - cursorRelX;
                            this.panY = (my - (vp.y + vp.h / 2)) / newZoom - cursorRelY;
                        }

                        this.zoom = newZoom;
                        this.node.setDirtyCanvas(true, true);
                        return true;
                    }
                    return false;
                }
            }

            function setupImageCompareNodeUI(node) {
                if (!node) return;
                node.hideOutputImages = true;
                node.imgs = null;
                node.images = null;
                if (!node.size || node.size[0] < MIN_WIDTH) node.size = [MIN_WIDTH, MIN_HEIGHT];

                let cmpWidget = node.widgets ? node.widgets.find(w => w instanceof StoiqoCompareCanvasWidget) : null;
                if (!cmpWidget) {
                    cmpWidget = new StoiqoCompareCanvasWidget(node);
                    node.addCustomWidget(cmpWidget);
                    node.cmpWidget = cmpWidget;
                }

                // Attach mouse event hooks to the node
                const origMouseDown = node.onMouseDown;
                node.onMouseDown = function(e, localPos, graphCanvas) {
                    if (cmpWidget && cmpWidget.handleMouseDown(e, localPos)) {
                        if (graphCanvas) {
                            graphCanvas.node_capturing_input = this;
                            graphCanvas.widget_capturing_input = cmpWidget;
                        }
                        return true;
                    }
                    if (origMouseDown) return origMouseDown.apply(this, arguments);
                };

                const origMouseMove = node.onMouseMove;
                node.onMouseMove = function(e, localPos, graphCanvas) {
                    if (cmpWidget && (cmpWidget.isDraggingSplit || cmpWidget.isPanning)) {
                        if (cmpWidget.handleMouseMove(e, localPos)) {
                            return true;
                        }
                    }
                    if (origMouseMove) return origMouseMove.apply(this, arguments);
                };

                const origMouseUp = node.onMouseUp;
                node.onMouseUp = function(e, localPos, graphCanvas) {
                    if (cmpWidget) {
                        cmpWidget.handleMouseUp(e, localPos);
                    }
                    if (graphCanvas && (graphCanvas.node_capturing_input === this || graphCanvas.widget_capturing_input === cmpWidget)) {
                        graphCanvas.node_capturing_input = null;
                        graphCanvas.widget_capturing_input = null;
                    }
                    if (origMouseUp) return origMouseUp.apply(this, arguments);
                };

                // Native LiteGraph mouse wheel handler: returns true to stop LiteGraph global canvas zooming
                node.onMouseWheel = function(e, localPos, graphCanvas) {
                    if (cmpWidget && cmpWidget.handleWheel(e, localPos)) {
                        if (e && e.preventDefault) e.preventDefault();
                        if (e && e.stopPropagation) e.stopPropagation();
                        return true;
                    }
                    return false;
                };

                // High-priority capture wheel hook on canvas DOM element to stop canvas zoom before LiteGraph processMouseWheel
                if (app.canvas && app.canvas.canvas && !node._stoiqoWheelAttached) {
                    node._stoiqoWheelAttached = true;
                    app.canvas.canvas.addEventListener("wheel", (e) => {
                        if (!node.cmpWidget || !app.canvas) return;
                        const canvasPos = app.canvas.convertEventToCanvasOffset ? app.canvas.convertEventToCanvasOffset(e) : [e.canvasX, e.canvasY];
                        const localX = canvasPos[0] - node.pos[0];
                        const localY = canvasPos[1] - node.pos[1];
                        if (localX >= 0 && localX <= node.size[0] && localY >= 0 && localY <= node.size[1]) {
                            if (node.cmpWidget.handleWheel(e, [localX, localY])) {
                                e.preventDefault();
                                e.stopPropagation();
                                e.stopImmediatePropagation();
                                return false;
                            }
                        }
                    }, { capture: true, passive: false });
                }

                node.setDirtyCanvas(true, true);
            }

            const origCmpCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                this.hideOutputImages = true;
                this.imgs = null;
                this.images = null;
                if (origCmpCreated) origCmpCreated.apply(this, arguments);
                setupImageCompareNodeUI(this);
            };

            const origCmpConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function() {
                this.hideOutputImages = true;
                this.imgs = null;
                this.images = null;
                if (origCmpConfigure) origCmpConfigure.apply(this, arguments);
                setupImageCompareNodeUI(this);
            };

            // Suppress default LiteGraph background image rendering
            nodeType.prototype.onDrawBackground = function(ctx) {
                this.hideOutputImages = true;
                this.imgs = null;
                this.images = null;
            };

            // Intercept backend output images and suppress native preview creation
            nodeType.prototype.onExecuted = function(message) {
                this.hideOutputImages = true;
                this.imgs = null;
                this.images = null;

                if (message) {
                    let w = this.widgets?.find(x => x instanceof StoiqoCompareCanvasWidget);
                    if (!w) {
                        setupImageCompareNodeUI(this);
                        w = this.widgets?.find(x => x instanceof StoiqoCompareCanvasWidget);
                    }
                    if (w) {
                        if (message.mode && message.mode[0]) {
                            const mStr = String(message.mode[0]).toLowerCase();
                            if (mStr.includes("toggle") || mStr.includes("flicker")) {
                                w.mode = "toggle";
                            } else if (mStr.includes("side")) {
                                w.mode = "side";
                            } else {
                                w.mode = "split";
                            }
                        }
                        if (message.images) {
                            w.setImages(message.images);
                        }
                    }

                    // Remove any preview/image widgets ComfyUI or extensions might have injected
                    if (this.widgets) {
                        this.widgets = this.widgets.filter(
                            x => x === w || (x.name !== "preview" && x.type !== "image" && !x._is_preview)
                        );
                    }
                    this.imgs = null;
                    this.images = null;
                    this.setDirtyCanvas(true, true);
                }
            };
        }

        // ══════════════════════════════════════════════════════════════════════
        // 7. IMAGE RESOLUTION NODE ENHANCEMENTS
        // ══════════════════════════════════════════════════════════════════════
        const resTargetNames = [
            "StoiqoResolutionNode",
            "[STOIQO] Image Resolution & Aspect Ratio",
        ];

        if (resTargetNames.includes(nodeData.name)) {
            const MIN_RES_WIDTH = 380;

            function setupResNode(node) {
                if (!node || !node.widgets) return;
                if (!node.size || node.size[0] < MIN_RES_WIDTH) {
                    node.size = [MIN_RES_WIDTH, node.size ? node.size[1] : 240];
                }

                function updateCustomDimsVisibility() {
                    const aspectWidget = node.widgets.find(w => w.name === "aspect_ratio");
                    const wWidget = node.widgets.find(w => w.name === "custom_width");
                    const hWidget = node.widgets.find(w => w.name === "custom_height");
                    if (!wWidget || !hWidget) return;

                    const isCustom = aspectWidget && String(aspectWidget.value || "").includes("Custom");

                    [wWidget, hWidget].forEach(widget => {
                        if (!widget._stoiqoOrigComputeSize) {
                            widget._stoiqoOrigComputeSize = widget.computeSize;
                            widget._stoiqoOrigDraw = widget.draw;
                        }

                        if (isCustom) {
                            widget.hidden = false;
                            if (widget._stoiqoOrigComputeSize) widget.computeSize = widget._stoiqoOrigComputeSize;
                            if (widget._stoiqoOrigDraw) widget.draw = widget._stoiqoOrigDraw;
                            if (widget.inputEl) {
                                widget.inputEl.hidden = false;
                                widget.inputEl.style.display = "";
                            }
                        } else {
                            widget.hidden = true;
                            widget.computeSize = function() { return [0, -4]; };
                            widget.draw = function() {};
                            if (widget.inputEl) {
                                widget.inputEl.hidden = true;
                                widget.inputEl.style.display = "none";
                            }
                        }
                    });

                    if (typeof node.computeSize === "function") {
                        const computed = node.computeSize();
                        node.size[0] = Math.max(node.size[0] || 0, MIN_RES_WIDTH);
                        node.size[1] = Math.max(Math.ceil(computed[1]), 80);
                    }
                    node.setDirtyCanvas(true, true);
                }

                const aspectWidget = node.widgets.find(w => w.name === "aspect_ratio");
                if (aspectWidget && !aspectWidget._stoiqoHooked) {
                    aspectWidget._stoiqoHooked = true;
                    const origCallback = aspectWidget.callback;
                    aspectWidget.callback = function(val) {
                        if (origCallback) origCallback.apply(this, arguments);
                        updateCustomDimsVisibility();
                    };
                }

                updateCustomDimsVisibility();
            }

            const origResCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                if (origResCreated) origResCreated.apply(this, arguments);
                setupResNode(this);
            };

            const origResConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function() {
                if (origResConfigure) origResConfigure.apply(this, arguments);
                setupResNode(this);
            };
        }

}
