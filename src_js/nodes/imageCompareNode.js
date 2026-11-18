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
                if (!data || !data.filename) return "";
                const params = new URLSearchParams();
                params.set("filename", data.filename);
                params.set("type", data.type || "temp");
                if (data.subfolder) {
                    params.set("subfolder", data.subfolder);
                }
                const fmt = app.getPreviewFormatParam ? app.getPreviewFormatParam() : "";
                if (fmt) {
                    const clean = fmt.replace(/^&/, "");
                    const parts = clean.split("=");
                    if (parts.length === 2) params.set(parts[0], parts[1]);
                }
                params.set("t", Date.now().toString());
                return api.apiURL(`/view?${params.toString()}`);
            }

            class StoiqoCompareCanvasWidget {
                constructor(node) {
                    this.type = "custom";
                    this.name = "_stoiqo_compare_canvas";
                    this.value = [];
                    this.serialize = false;
                    this.options = { serialize: false };
                    this.node = node;
                    this.imgA = null;
                    this.imgB = null;
                    this.imgDiff = null;
                    this.imagesData = null;
                    this.availableA = [];
                    this.availableB = [];
                    this.selectedA = null;
                    this.selectedB = null;
                    this.diffData = null;
                    this.metricsData = null;
                    this.labelA = "Image A";
                    this.labelB = "Image B";
                    this.splitX = 0.5;
                    this.zoom = 1.0;
                    this.panX = 0;
                    this.panY = 0;
                    this.mode = "hover_slide"; // "hover_slide", "split", "toggle", "side", "diff_heat", "only_a", "only_b"
                    this.toggleShowB = false;
                    this.isHoldingPointer = false;
                    this.isDraggingSplit = false;
                    this.isPanning = false;
                    this.isHoveringViewport = false;
                    this.lastMouse = [0, 0];
                    this.btnHitAreas = [];
                    this.chipHitAreas = [];
                    this.viewportRect = { x: 0, y: 0, w: 0, h: 0 };
                    this.loadError = null;
                    this._activePointerCleanup = null;
                }

                serializeValue() {
                    return undefined;
                }

                computeSize(width) {
                    if (this.node && this.node.size && this.node.size[1] > 360) {
                        return [width, Math.max(460, this.node.size[1] - 80)];
                    }
                    return [width, 460];
                }

                computeLayoutSize() {
                    return { minHeight: 360, minWidth: 440 };
                }

                setImages(dataList) {
                    if (!dataList || dataList.length === 0) return;
                    this.imagesData = dataList;
                    this.value = dataList;
                    if (this.node) {
                        this.node.properties = this.node.properties || {};
                        this.node.properties.stoiqo_images = dataList;
                    }

                    // Categorize images into Side A, Side B, and Diff Heatmap
                    const listA = dataList.filter(d => d.side === "A" || (d.name && d.name.startsWith("A")));
                    const listB = dataList.filter(d => d.side === "B" || (d.name && d.name.startsWith("B")));
                    const diffItem = dataList.find(d => d.side === "DIFF" || d.name === "HEATMAP");
                    this.diffData = diffItem || null;

                    this.availableA = listA.length > 0 ? listA : [dataList[0]];
                    this.availableB = listB.length > 0 ? listB : (dataList.length > 1 ? [dataList[1]] : [dataList[0]]);

                    // Select active image for each side
                    if (!this.selectedA || !this.availableA.some(x => x.filename === this.selectedA.filename)) {
                        this.selectedA = this.availableA[0];
                    }
                    if (!this.selectedB || !this.availableB.some(x => x.filename === this.selectedB.filename)) {
                        this.selectedB = this.availableB[0];
                    }

                    this.loadSelectedImages();
                    this.resetView();
                }

                loadSelectedImages() {
                    if (this.imgA) { this.imgA.onload = null; this.imgA.onerror = null; this.imgA.src = ""; this.imgA = null; }
                    if (this.imgB) { this.imgB.onload = null; this.imgB.onerror = null; this.imgB.src = ""; this.imgB = null; }
                    if (this.imgDiff) { this.imgDiff.onload = null; this.imgDiff.onerror = null; this.imgDiff.src = ""; this.imgDiff = null; }

                    this.loadError = null;
                    if (!this.selectedA || !this.selectedB) return;

                    const urlA = imageDataToUrl(this.selectedA);
                    const urlB = imageDataToUrl(this.selectedB);

                    this.imgA = new Image();
                    this.imgB = new Image();

                    this.imgA.onload = () => { if (this.node) this.node.setDirtyCanvas(true, true); };
                    this.imgB.onload = () => { if (this.node) this.node.setDirtyCanvas(true, true); };
                    this.imgA.onerror = () => {
                        this.loadError = "Unable to load image A";
                        if (this.node) this.node.setDirtyCanvas(true, true);
                    };
                    this.imgB.onerror = () => {
                        this.loadError = "Unable to load image B";
                        if (this.node) this.node.setDirtyCanvas(true, true);
                    };

                    this.imgA.src = urlA;
                    this.imgB.src = urlB;
                    this.labelA = this.selectedA.label || this.selectedA.name || "Image A";
                    this.labelB = this.selectedB.label || this.selectedB.name || "Image B";

                    if (this.diffData) {
                        this.imgDiff = new Image();
                        this.imgDiff.onload = () => { if (this.node) this.node.setDirtyCanvas(true, true); };
                        this.imgDiff.src = imageDataToUrl(this.diffData);
                    }
                }

                resetView() {
                    this.zoom = 1.0;
                    this.panX = 0;
                    this.panY = 0;
                    this.splitX = 0.5;
                    this.toggleShowB = false;
                    this.isHoldingPointer = false;
                    if (this.node) this.node.setDirtyCanvas(true, true);
                }

                attachWindowDragListeners() {
                    if (this._activePointerCleanup) {
                        this._activePointerCleanup();
                    }

                    const cleanup = () => {
                        this.isDraggingSplit = false;
                        this.isPanning = false;
                        this.isHoldingPointer = false;
                        window.removeEventListener("pointermove", onPointerMove, true);
                        window.removeEventListener("pointerup", onPointerUp, true);
                        window.removeEventListener("pointercancel", onPointerUp, true);
                        if (this._activePointerCleanup === cleanup) {
                            this._activePointerCleanup = null;
                        }
                        if (this.node) this.node.setDirtyCanvas(true, true);
                    };

                    this._activePointerCleanup = cleanup;

                    const onPointerMove = (moveEv) => {
                        if (!this.node) return;
                        const canvas = app.canvas;
                        let localX = 0, localY = 0;

                        if (canvas && typeof canvas.convertEventToCanvasOffset === "function") {
                            const cOffset = canvas.convertEventToCanvasOffset(moveEv);
                            localX = cOffset[0] - this.node.pos[0];
                            localY = cOffset[1] - this.node.pos[1];
                        } else {
                            const ds = canvas?.ds || { scale: 1, offset: [0, 0] };
                            const rect = canvas?.canvas?.getBoundingClientRect() || { left: 0, top: 0 };
                            const clientX = moveEv.clientX - rect.left;
                            const clientY = moveEv.clientY - rect.top;
                            localX = (clientX - ds.offset[0]) / ds.scale - this.node.pos[0];
                            localY = (clientY - ds.offset[1]) / ds.scale - this.node.pos[1];
                        }

                        if (this.isDraggingSplit) {
                            const vp = this.viewportRect;
                            if (vp.w > 0) {
                                const relX = (localX - vp.x) / vp.w;
                                this.splitX = Math.max(0.01, Math.min(0.99, relX));
                                this.node.setDirtyCanvas(true, true);
                            }
                        } else if (this.isPanning) {
                            const dx = localX - this.lastMouse[0];
                            const dy = localY - this.lastMouse[1];
                            this.panX += dx / this.zoom;
                            this.panY += dy / this.zoom;
                            this.lastMouse = [localX, localY];
                            this.node.setDirtyCanvas(true, true);
                        }

                        if (moveEv.stopPropagation) moveEv.stopPropagation();
                        if (moveEv.preventDefault) moveEv.preventDefault();
                    };

                    const onPointerUp = (upEv) => {
                        cleanup();
                        if (upEv.stopPropagation) upEv.stopPropagation();
                    };

                    window.addEventListener("pointermove", onPointerMove, { capture: true, passive: false });
                    window.addEventListener("pointerup", onPointerUp, { capture: true, passive: false });
                    window.addEventListener("pointercancel", onPointerUp, { capture: true, passive: false });
                }

                draw(ctx, node, width, posY, height) {
                    const nodeW = width || (node.size ? node.size[0] : MIN_WIDTH);
                    const nodeH = (node && node.size) ? node.size[1] : 560;
                    const slotH = Math.max(280, nodeH - posY - 16);
                    const vY = posY + 6;
                    const vW = nodeW - 24;
                    const vX = 12;

                    this.btnHitAreas = [];
                    this.chipHitAreas = [];

                    ctx.save();

                    // ── 1. Mini Toolbar ───────────────────────────────────────
                    const barY = vY;
                    const barH = 26;

                    ctx.fillStyle = "rgba(15, 23, 42, 0.75)";
                    if (ctx.roundRect) {
                        ctx.beginPath();
                        ctx.roundRect(vX, barY, vW, barH, 4);
                        ctx.fill();
                    } else {
                        ctx.fillRect(vX, barY, vW, barH);
                    }

                    // Mode buttons: Hover (rgthree), Drag Split, Toggle, Side, Diff Heatmap, Solo A, Solo B
                    const modes = [
                        { key: "hover_slide", label: "⚡ Hover (rgthree)", activeColor: "#2997ff" },
                        { key: "split", label: "↔ Drag Split", activeColor: "#2dd4bf" },
                        { key: "toggle", label: this.mode === "toggle" ? (this.toggleShowB ? "👁 B (Click A)" : "👁 A (Click B)") : "👁 Toggle (Space)", activeColor: "#ff9f0a" },
                        { key: "side", label: "◫ Side-by-Side", activeColor: "#30d158" },
                        { key: "diff_heat", label: "🔥 Diff Heatmap", activeColor: "#ff453a" },
                        { key: "only_a", label: "Solo A", activeColor: "#58b0ff" },
                        { key: "only_b", label: "Solo B", activeColor: "#ff9f0a" },
                    ];

                    let btnX = vX + 6;
                    ctx.font = "bold 9px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
                    ctx.textBaseline = "middle";

                    modes.forEach(m => {
                        const active = this.mode === m.key;
                        const textW = ctx.measureText(m.label).width;
                        const bW = textW + 12;
                        const bH = 18;
                        const bY = barY + 4;
                        const col = m.activeColor || "#2dd4bf";

                        ctx.fillStyle = active
                            ? (m.key === "hover_slide" ? "rgba(56, 189, 248, 0.25)" :
                               m.key === "only_a" ? "rgba(147, 197, 253, 0.22)" :
                               m.key === "only_b" ? "rgba(192, 132, 252, 0.22)" :
                               m.key === "toggle" ? "rgba(245, 158, 11, 0.25)" :
                               m.key === "side" ? "rgba(16, 185, 129, 0.22)" :
                               "rgba(45, 212, 191, 0.25)")
                            : "rgba(255, 255, 255, 0.06)";
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
                        ctx.fillText(m.label, btnX + 6, bY + bH / 2);

                        this.btnHitAreas.push({
                            x: btnX, y: bY, w: bW, h: bH,
                            action: () => {
                                if (this.mode === m.key && m.key === "toggle") {
                                    this.toggleShowB = !this.toggleShowB;
                                } else {
                                    this.mode = m.key;
                                }
                                node.setDirtyCanvas(true, true);
                            }
                        });

                        btnX += bW + 4;
                    });

                    // Reset Zoom button on the right
                    const resetLabel = "⟲ Reset";
                    const rTextW = ctx.measureText(resetLabel).width;
                    const rW = rTextW + 12;
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
                    ctx.fillText(resetLabel, rX + 6, rY + 9);

                    this.btnHitAreas.push({
                        x: rX, y: rY, w: rW, h: 18,
                        action: () => { this.resetView(); }
                    });

                    // Zoom Indicator badge next to reset
                    const zoomPct = Math.round(this.zoom * 100);
                    const zoomLabel = `🔍 ${zoomPct}%`;
                    const zTextW = ctx.measureText(zoomLabel).width;
                    const zX = rX - zTextW - 12;
                    ctx.fillStyle = this.zoom > 1.01 ? "#2997ff" : "#64748b";
                    ctx.fillText(zoomLabel, zX, rY + 9);

                    // ── 2. Batch Selector Chips (Multi-Frame Support) ─────────
                    let currentTopY = barY + barH + 4;
                    const hasMultiFrames = (this.availableA && this.availableA.length > 1) || (this.availableB && this.availableB.length > 1);

                    if (hasMultiFrames) {
                        const chipBarH = 22;
                        ctx.fillStyle = "rgba(15, 23, 42, 0.55)";
                        if (ctx.roundRect) {
                            ctx.beginPath();
                            ctx.roundRect(vX, currentTopY, vW, chipBarH, 3);
                            ctx.fill();
                        } else {
                            ctx.fillRect(vX, currentTopY, vW, chipBarH);
                        }

                        let chipX = vX + 8;
                        ctx.font = "bold 9px monospace";
                        ctx.textBaseline = "middle";

                        // Side A label & chips
                        ctx.fillStyle = "#2997ff";
                        ctx.fillText("Side A:", chipX, currentTopY + chipBarH / 2);
                        chipX += ctx.measureText("Side A:").width + 6;

                        this.availableA.forEach((item, idx) => {
                            const name = item.name || `A${idx + 1}`;
                            const isSel = this.selectedA && this.selectedA.filename === item.filename;
                            const cW = ctx.measureText(name).width + 8;
                            const cH = 16;
                            const cY = currentTopY + 3;

                            ctx.fillStyle = isSel ? "#1d4ed8" : "rgba(255, 255, 255, 0.08)";
                            ctx.strokeStyle = isSel ? "#2997ff" : "rgba(255, 255, 255, 0.15)";
                            if (ctx.roundRect) {
                                ctx.beginPath();
                                ctx.roundRect(chipX, cY, cW, cH, 3);
                                ctx.fill();
                                ctx.stroke();
                            } else {
                                ctx.fillRect(chipX, cY, cW, cH);
                                ctx.strokeRect(chipX, cY, cW, cH);
                            }
                            ctx.fillStyle = isSel ? "#ffffff" : "#94a3b8";
                            ctx.fillText(name, chipX + 4, cY + cH / 2);

                            this.chipHitAreas.push({
                                x: chipX, y: cY, w: cW, h: cH,
                                action: () => {
                                    this.selectedA = item;
                                    this.loadSelectedImages();
                                    node.setDirtyCanvas(true, true);
                                }
                            });

                            chipX += cW + 4;
                        });

                        chipX += 10;
                        // Side B label & chips
                        ctx.fillStyle = "#ff9f0a";
                        ctx.fillText("Side B:", chipX, currentTopY + chipBarH / 2);
                        chipX += ctx.measureText("Side B:").width + 6;

                        this.availableB.forEach((item, idx) => {
                            const name = item.name || `B${idx + 1}`;
                            const isSel = this.selectedB && this.selectedB.filename === item.filename;
                            const cW = ctx.measureText(name).width + 8;
                            const cH = 16;
                            const cY = currentTopY + 3;

                            ctx.fillStyle = isSel ? "#b45309" : "rgba(255, 255, 255, 0.08)";
                            ctx.strokeStyle = isSel ? "#ff9f0a" : "rgba(255, 255, 255, 0.15)";
                            if (ctx.roundRect) {
                                ctx.beginPath();
                                ctx.roundRect(chipX, cY, cW, cH, 3);
                                ctx.fill();
                                ctx.stroke();
                            } else {
                                ctx.fillRect(chipX, cY, cW, cH);
                                ctx.strokeRect(chipX, cY, cW, cH);
                            }
                            ctx.fillStyle = isSel ? "#ffffff" : "#94a3b8";
                            ctx.fillText(name, chipX + 4, cY + cH / 2);

                            this.chipHitAreas.push({
                                x: chipX, y: cY, w: cW, h: cH,
                                action: () => {
                                    this.selectedB = item;
                                    this.loadSelectedImages();
                                    node.setDirtyCanvas(true, true);
                                }
                            });

                            chipX += cW + 4;
                        });

                        currentTopY += chipBarH + 4;
                    }

                    // ── 3. Viewport Canvas Setup ──────────────────────────────
                    const vH = Math.max(240, Math.min(slotH - (currentTopY - vY) - 10, 1600));
                    this.viewportRect = { x: vX, y: currentTopY, w: vW, h: vH };
                    const vp = this.viewportRect;

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

                    // Validate images loaded status
                    const hasValidA = this.imgA && this.imgA.complete && this.imgA.naturalWidth > 0 && this.imgA.naturalHeight > 0;
                    const hasValidB = this.imgB && this.imgB.complete && this.imgB.naturalWidth > 0 && this.imgB.naturalHeight > 0;

                    if (!hasValidA || !hasValidB) {
                        ctx.fillStyle = this.loadError ? "#f87171" : "#94a3b8";
                        ctx.font = "bold 12px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
                        ctx.textAlign = "center";
                        ctx.textBaseline = "middle";

                        if (this.loadError) {
                            ctx.fillText(this.loadError, vp.x + vp.w / 2, vp.y + vp.h / 2);
                        } else if (this.imgA && !this.imgA.complete) {
                            ctx.fillText("⏳ Loading image preview...", vp.x + vp.w / 2, vp.y + vp.h / 2);
                        } else {
                            ctx.fillText("Connect image_a and image_b, then click Queue Prompt to inspect", vp.x + vp.w / 2, vp.y + vp.h / 2 - 10);
                            ctx.font = "10px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
                            ctx.fillStyle = "#64748b";
                            ctx.fillText("Hover Slider • Zero Stretch • Zero Crop • Precise Centering", vp.x + vp.w / 2, vp.y + vp.h / 2 + 12);
                        }
                        ctx.restore();
                        return;
                    }

                    // ── 4. Core Geometry: Shared Anchor & Proportional Scaling ─
                    // Strict Rule: Center is shared, 0 stretch, 0 crop, native aspect ratio preserved.
                    const centerX = vp.x + vp.w / 2;
                    const centerY = vp.y + vp.h / 2;

                    const natWA = this.imgA.naturalWidth;
                    const natHA = this.imgA.naturalHeight;
                    const natWB = this.imgB.naturalWidth;
                    const natHB = this.imgB.naturalHeight;

                    // Uniform aspect-fit scaling: preserves native proportions 100% without crop
                    const scaleA = Math.min(vp.w / natWA, vp.h / natHA);
                    const fitWA = natWA * scaleA;
                    const fitHA = natHA * scaleA;

                    const scaleB = Math.min(vp.w / natWB, vp.h / natHB);
                    const fitWB = natWB * scaleB;
                    const fitHB = natHB * scaleB;

                    const curZoom = this.zoom;
                    const curCX = centerX + this.panX * curZoom;
                    const curCY = centerY + this.panY * curZoom;

                    const drawWA = fitWA * curZoom;
                    const drawHA = fitHA * curZoom;
                    const drawXA = curCX - drawWA / 2;
                    const drawYA = curCY - drawHA / 2;

                    const drawWB = fitWB * curZoom;
                    const drawHB = fitHB * curZoom;
                    const drawXB = curCX - drawWB / 2;
                    const drawYB = curCY - drawHB / 2;

                    const renderImageA = () => {
                        ctx.drawImage(this.imgA, drawXA, drawYA, drawWA, drawHA);
                    };

                    const renderImageB = () => {
                        ctx.drawImage(this.imgB, drawXB, drawYB, drawWB, drawHB);
                    };

                    const renderImageDiff = () => {
                        if (this.imgDiff && this.imgDiff.complete && this.imgDiff.naturalWidth > 0) {
                            ctx.drawImage(this.imgDiff, drawXA, drawYA, drawWA, drawHA);
                        } else {
                            renderImageB();
                        }
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
                    // ── Mode 2b: Diff Heatmap (Solo or Split vs A) ─────────────
                    else if (this.mode === "diff_heat") {
                        ctx.save();
                        ctx.beginPath();
                        ctx.rect(vp.x, vp.y, vp.w, vp.h);
                        ctx.clip();
                        renderImageDiff();
                        ctx.restore();
                    }
                    // ── Mode 3 & 4: Split Slider & Hover Slider ───────────────
                    else if (this.mode === "split" || this.mode === "hover_slide") {
                        const splitScreenX = Math.round(vp.x + this.splitX * vp.w);

                        // 1. Draw Image A (Left side of divider)
                        ctx.save();
                        ctx.beginPath();
                        ctx.rect(vp.x, vp.y, splitScreenX - vp.x, vp.h);
                        ctx.clip();
                        renderImageA();
                        ctx.restore();

                        // 2. Draw Image B (Right side of divider)
                        ctx.save();
                        ctx.beginPath();
                        ctx.rect(splitScreenX, vp.y, (vp.x + vp.w) - splitScreenX, vp.h);
                        ctx.clip();
                        renderImageB();
                        ctx.restore();

                        // 3. Draw Splitter Line
                        ctx.save();
                        ctx.strokeStyle = "#2dd4bf";
                        ctx.lineWidth = 2;
                        ctx.beginPath();
                        ctx.moveTo(splitScreenX, vp.y);
                        ctx.lineTo(splitScreenX, vp.y + vp.h);
                        ctx.stroke();

                        // Center Handle Pill
                        const pillW = 34;
                        const pillH = 22;
                        const pillY = centerY - pillH / 2;
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

                        ctx.fillStyle = "#2dd4bf";
                        ctx.font = "bold 10px sans-serif";
                        ctx.textAlign = "center";
                        ctx.textBaseline = "middle";
                        ctx.fillText("◄►", splitScreenX, pillY + pillH / 2 + 1);
                        ctx.restore();
                    }
                    // ── Mode 5: Toggle A/B (Flicker / Click / Hold) ────────────
                    else if (this.mode === "toggle") {
                        const showB = this.isHoldingPointer ? !this.toggleShowB : this.toggleShowB;
                        ctx.save();
                        ctx.beginPath();
                        ctx.rect(vp.x, vp.y, vp.w, vp.h);
                        ctx.clip();
                        if (showB) {
                            renderImageB();
                        } else {
                            renderImageA();
                        }
                        ctx.restore();
                    }
                    // ── Mode 6: Side-by-Side (Synchronized) ────────────────────
                    else if (this.mode === "side") {
                        const halfW = (vp.w - 2) / 2;
                        const midX = vp.x + halfW;

                        // Fit Image A in Left Half
                        const scaleSideA = Math.min(halfW / natWA, vp.h / natHA);
                        const fitSideWA = natWA * scaleSideA;
                        const fitSideHA = natHA * scaleSideA;
                        const centerSideAX = vp.x + halfW / 2 + this.panX * curZoom;
                        const drawSideWA = fitSideWA * curZoom;
                        const drawSideHA = fitSideHA * curZoom;

                        ctx.save();
                        ctx.beginPath();
                        ctx.rect(vp.x, vp.y, halfW, vp.h);
                        ctx.clip();
                        ctx.drawImage(this.imgA, centerSideAX - drawSideWA / 2, curCY - drawSideHA / 2, drawSideWA, drawSideHA);
                        ctx.restore();

                        // Fit Image B in Right Half
                        const scaleSideB = Math.min(halfW / natWB, vp.h / natHB);
                        const fitSideWB = natWB * scaleSideB;
                        const fitSideHB = natHB * scaleSideB;
                        const centerSideBX = (midX + 2) + halfW / 2 + this.panX * curZoom;
                        const drawSideWB = fitSideWB * curZoom;
                        const drawSideHB = fitSideHB * curZoom;

                        ctx.save();
                        ctx.beginPath();
                        ctx.rect(midX + 2, vp.y, halfW, vp.h);
                        ctx.clip();
                        ctx.drawImage(this.imgB, centerSideBX - drawSideWB / 2, curCY - drawSideHB / 2, drawSideWB, drawSideHB);
                        ctx.restore();

                        // Divider line
                        ctx.strokeStyle = "rgba(255, 255, 255, 0.25)";
                        ctx.lineWidth = 1;
                        ctx.beginPath();
                        ctx.moveTo(midX + 1, vp.y);
                        ctx.lineTo(midX + 1, vp.y + vp.h);
                        ctx.stroke();
                    }

                    // ── 5. Overlay Labels & Badges ────────────────────────────
                    ctx.font = "bold 9px sans-serif";
                    ctx.textAlign = "left";
                    ctx.textBaseline = "middle";

                    if (this.mode === "toggle") {
                        const showB = this.isHoldingPointer ? !this.toggleShowB : this.toggleShowB;
                        const tText = showB
                            ? `👁 B: ${this.labelB} (${natWB}×${natHB}) • Click / Space for A`
                            : `👁 A: ${this.labelA} (${natWA}×${natHA}) • Click / Space for B`;
                        const tW = ctx.measureText(tText).width + 16;
                        ctx.fillStyle = "rgba(15, 23, 42, 0.88)";
                        ctx.strokeStyle = showB ? "#ff9f0a" : "#2997ff";
                        ctx.lineWidth = 1;
                        if (ctx.roundRect) {
                            ctx.beginPath();
                            ctx.roundRect(vp.x + 8, vp.y + 8, tW, 20, 3);
                            ctx.fill();
                            ctx.stroke();
                        } else {
                            ctx.fillRect(vp.x + 8, vp.y + 8, tW, 20);
                            ctx.strokeRect(vp.x + 8, vp.y + 8, tW, 20);
                        }
                        ctx.fillStyle = showB ? "#ff9f0a" : "#2997ff";
                        ctx.fillText(tText, vp.x + 16, vp.y + 18);
                    } else {
                        // Label A (Top Left)
                        if (this.mode !== "only_b" && this.mode !== "diff_heat") {
                            const labelAText = `◄ A: ${this.labelA} (${natWA}×${natHA})`;
                            const lAW = ctx.measureText(labelAText).width + 14;
                            ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
                            ctx.fillRect(vp.x + 8, vp.y + 8, lAW, 18);
                            ctx.fillStyle = "#2997ff";
                            ctx.fillText(labelAText, vp.x + 14, vp.y + 17);
                        } else if (this.mode === "diff_heat") {
                            const m = this.metricsData || {};
                            const ssimStr = m.ssim !== undefined ? `SSIM: ${m.ssim}` : "";
                            const psnrStr = m.psnr_db !== undefined ? `PSNR: ${m.psnr_db}dB` : "";
                            const deltaStr = m.changed_pixels_pct !== undefined ? `Δ: ${m.changed_pixels_pct}%` : "";
                            const diffTxt = `🔥 Thermal Diff • ${[ssimStr, psnrStr, deltaStr].filter(Boolean).join(" • ") || "Delta Map"}`;
                            const lDW = ctx.measureText(diffTxt).width + 16;
                            ctx.fillStyle = "rgba(15, 23, 42, 0.90)";
                            ctx.strokeStyle = "#ff453a";
                            ctx.lineWidth = 1;
                            if (ctx.roundRect) {
                                ctx.beginPath();
                                ctx.roundRect(vp.x + 8, vp.y + 8, lDW, 20, 3);
                                ctx.fill();
                                ctx.stroke();
                            } else {
                                ctx.fillRect(vp.x + 8, vp.y + 8, lDW, 20);
                                ctx.strokeRect(vp.x + 8, vp.y + 8, lDW, 20);
                            }
                            ctx.fillStyle = "#ff6961";
                            ctx.fillText(diffTxt, vp.x + 16, vp.y + 18);
                        }

                        // Label B (Top Right)
                        if (this.mode !== "only_a") {
                            const labelBText = `B: ${this.labelB} (${natWB}×${natHB}) ►`;
                            const lBW = ctx.measureText(labelBText).width + 14;
                            ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
                            ctx.fillRect(vp.x + vp.w - lBW - 8, vp.y + 8, lBW, 18);
                            ctx.fillStyle = "#ff9f0a";
                            ctx.fillText(labelBText, vp.x + vp.w - lBW - 2, vp.y + 17);
                        }
                    }

                    // Instruction pill if zoomed in
                    if (this.zoom > 1.05) {
                        const hint = "🔍 Drag to Pan • Wheel to Zoom • Space to Toggle A/B";
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
                        ctx.fillText(hint, vp.x + vp.w / 2, hintY + 8);
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

                    // 2. Check batch chips
                    for (const chip of this.chipHitAreas) {
                        if (mx >= chip.x && mx <= chip.x + chip.w && my >= chip.y && my <= chip.y + chip.h) {
                            chip.action();
                            if (this.node) this.node.setDirtyCanvas(true, true);
                            if (e && e.stopPropagation) e.stopPropagation();
                            return true;
                        }
                    }

                    // 3. Check viewport click
                    const vp = this.viewportRect;
                    if (mx >= vp.x && mx <= vp.x + vp.w && my >= vp.y && my <= vp.y + vp.h) {
                        if (this.mode === "toggle") {
                            this.isHoldingPointer = true;
                            this.attachWindowDragListeners();
                            if (this.node) this.node.setDirtyCanvas(true, true);
                            if (e && e.stopPropagation) e.stopPropagation();
                            return true;
                        }

                        if (this.mode === "split" || this.mode === "hover_slide") {
                            const splitPixelX = vp.x + this.splitX * vp.w;
                            if (this.zoom <= 1.05 || Math.abs(mx - splitPixelX) < 35) {
                                const relX = (mx - vp.x) / vp.w;
                                this.splitX = Math.max(0.01, Math.min(0.99, relX));
                                this.isDraggingSplit = true;
                                this.attachWindowDragListeners();
                                if (this.node) this.node.setDirtyCanvas(true, true);
                                if (e && e.stopPropagation) e.stopPropagation();
                                return true;
                            }
                        }

                        // Otherwise start panning when zoomed
                        this.isPanning = true;
                        this.lastMouse = [mx, my];
                        this.attachWindowDragListeners();
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

                    const insideViewport = mx >= vp.x && mx <= vp.x + vp.w && my >= vp.y && my <= vp.y + vp.h;
                    this.isHoveringViewport = insideViewport;

                    // Hover Slider mode (rgthree style): curtain follows mouse automatically
                    if (this.mode === "hover_slide" && insideViewport && !this.isPanning && !this.isDraggingSplit) {
                        if (this.zoom <= 1.05) {
                            const relX = (mx - vp.x) / vp.w;
                            this.splitX = Math.max(0.01, Math.min(0.99, relX));
                            if (this.node) this.node.setDirtyCanvas(true, true);
                            return true;
                        }
                    }

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
                    const wasHolding = this.isHoldingPointer;
                    const wasActive = this.isDraggingSplit || this.isPanning || wasHolding;

                    if (this.mode === "toggle" && wasHolding) {
                        this.isHoldingPointer = false;
                        this.toggleShowB = !this.toggleShowB;
                    }

                    this.isDraggingSplit = false;
                    this.isPanning = false;
                    this.isHoldingPointer = false;

                    if (this._activePointerCleanup) {
                        this._activePointerCleanup();
                    }
                    if (wasActive && this.node) {
                        this.node.setDirtyCanvas(true, true);
                    }
                    return wasActive;
                }

                mouse(event, pos, node) {
                    if (event && event._stoiqoCompareHandled) return true;
                    if (event.type === "pointerdown" || event.type === "mousedown") {
                        const handled = this.handleMouseDown(event, pos);
                        if (handled && event) event._stoiqoCompareHandled = true;
                        return handled;
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

                // Sync initial_mode dropdown widget with canvas widget
                const modeWidget = node.widgets?.find(w => w.name === "initial_mode");
                if (modeWidget && !modeWidget._stoiqoHooked) {
                    modeWidget._stoiqoHooked = true;
                    const origCallback = modeWidget.callback;
                    modeWidget.callback = function(val) {
                        if (origCallback) origCallback.apply(this, arguments);
                        if (cmpWidget) {
                            const vStr = String(val || "").toLowerCase();
                            if (vStr.includes("hover")) {
                                cmpWidget.mode = "hover_slide";
                            } else if (vStr.includes("toggle") || vStr.includes("flicker")) {
                                cmpWidget.mode = "toggle";
                            } else if (vStr.includes("side")) {
                                cmpWidget.mode = "side";
                            } else {
                                cmpWidget.mode = "split";
                            }
                            node.setDirtyCanvas(true, true);
                        }
                    };
                }

                // Attach mouse event hooks to the node
                const origMouseDown = node.onMouseDown;
                node.onMouseDown = function(e, localPos, graphCanvas) {
                    if (e && e._stoiqoCompareHandled) return true;
                    if (cmpWidget && cmpWidget.handleMouseDown(e, localPos)) {
                        if (e) e._stoiqoCompareHandled = true;
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
                    if (cmpWidget) {
                        cmpWidget.handleMouseMove(e, localPos);
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

                // Native LiteGraph mouse wheel handler
                node.onMouseWheel = function(e, localPos, graphCanvas) {
                    if (cmpWidget && cmpWidget.handleWheel(e, localPos)) {
                        if (e && e.preventDefault) e.preventDefault();
                        if (e && e.stopPropagation) e.stopPropagation();
                        return true;
                    }
                    return false;
                };

                // High-priority capture wheel hook on canvas DOM element
                if (app.canvas && app.canvas.canvas && !node._stoiqoWheelAttached) {
                    node._stoiqoWheelAttached = true;
                    node._stoiqoWheelHandler = (e) => {
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
                    };
                    app.canvas.canvas.addEventListener("wheel", node._stoiqoWheelHandler, { capture: true, passive: false });
                }

                // Spacebar keyboard shortcut hook to toggle A/B when mouse is over this node
                if (!node._stoiqoSpaceAttached) {
                    node._stoiqoSpaceAttached = true;
                    node._stoiqoSpaceHandler = (e) => {
                        if (e.code === "Space" && !e.repeat && !e.target.matches("input, textarea, select")) {
                            if (!node.cmpWidget || !node.cmpWidget.isHoveringViewport) return;
                            node.cmpWidget.toggleShowB = !node.cmpWidget.toggleShowB;
                            node.setDirtyCanvas(true, true);
                            e.preventDefault();
                            e.stopPropagation();
                        }
                    };
                    window.addEventListener("keydown", node._stoiqoSpaceHandler, { capture: true });
                }

                node.setDirtyCanvas(true, true);
            }

            const origCmpCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                this.hideOutputImages = true;
                this.imgs = null;
                this.images = null;
                if (origCmpCreated) origCmpCreated.apply(this, arguments);
                this.hideOutputImages = true;
                this.imgs = null;
                this.images = null;
                setupImageCompareNodeUI(this);
            };

            const origCmpConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function(info) {
                this.hideOutputImages = true;
                this.imgs = null;
                this.images = null;
                if (origCmpConfigure) origCmpConfigure.apply(this, arguments);
                this.hideOutputImages = true;
                this.imgs = null;
                this.images = null;
                setupImageCompareNodeUI(this);

                // Restore cached images if available across reloads
                const cachedImages = this.properties?.stoiqo_images ||
                                     info?.properties?.stoiqo_images ||
                                     this.cmpWidget?.imagesData ||
                                     this.cmpWidget?.value;
                if (cachedImages && Array.isArray(cachedImages) && cachedImages.length > 0 && this.cmpWidget) {
                    this.cmpWidget.setImages(cachedImages);
                }
            };

            const origCmpRemoved = nodeType.prototype.onRemoved;
            nodeType.prototype.onRemoved = function() {
                if (app.canvas && app.canvas.canvas && this._stoiqoWheelHandler) {
                    app.canvas.canvas.removeEventListener("wheel", this._stoiqoWheelHandler, { capture: true, passive: false });
                    this._stoiqoWheelHandler = null;
                }
                if (this._stoiqoSpaceHandler) {
                    window.removeEventListener("keydown", this._stoiqoSpaceHandler, { capture: true });
                    this._stoiqoSpaceHandler = null;
                }
                this.cmpWidget = null;
                if (origCmpRemoved) origCmpRemoved.apply(this, arguments);
            };

            // Suppress default LiteGraph background image rendering
            const origCmpDrawBg = nodeType.prototype.onDrawBackground;
            nodeType.prototype.onDrawBackground = function(ctx) {
                this.hideOutputImages = true;
                this.imgs = null;
                this.images = null;
                if (origCmpDrawBg) origCmpDrawBg.apply(this, arguments);
            };

            // Intercept backend output images and populate canvas widget
            const origCmpExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                this.hideOutputImages = true;
                this.imgs = null;
                this.images = null;
                if (origCmpExecuted) origCmpExecuted.apply(this, arguments);
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
                            if (mStr.includes("hover")) {
                                w.mode = "hover_slide";
                            } else if (mStr.includes("toggle") || mStr.includes("flicker")) {
                                w.mode = "toggle";
                            } else if (mStr.includes("side")) {
                                w.mode = "side";
                            } else {
                                w.mode = "split";
                            }
                        }
                        const cmpImages = message.stoiqo_images || message.images;
                        if (cmpImages) {
                            w.setImages(cmpImages);
                        }
                        if (message.metrics && message.metrics[0]) {
                            w.metricsData = message.metrics[0];
                        }
                    }

                    // Remove any unwanted preview widgets ComfyUI or extensions might inject
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

            class StoiqoResolutionHUDWidget {
                constructor(node) {
                    this.node = node;
                    this.type = "custom";
                    this.name = "_stoiqo_res_hud";
                    this.value = {};
                    this.serialize = false;
                    this.options = { serialize: false };
                    this.isStoiqoHUD = true;
                    this.height = 44;
                }

                serializeValue() {
                    return undefined;
                }

                computeSize(width) {
                    return [width, this.height];
                }

                draw(ctx, node, width, y, height) {
                    if (node.flags && node.flags.collapsed) return;

                    const aspectW = node.widgets.find(w => w.name === "aspect_ratio");
                    const scaleW = node.widgets.find(w => w.name === "scale_target");
                    const swapW = node.widgets.find(w => w.name === "swap_dimensions");
                    const multW = node.widgets.find(w => w.name === "multiple_of");
                    const customW = node.widgets.find(w => w.name === "custom_width");
                    const customH = node.widgets.find(w => w.name === "custom_height");

                    const aspect = aspectW ? String(aspectW.value || "") : "1:1 Square (1024 x 1024)";
                    const scale = scaleW ? String(scaleW.value || "") : "1.0 MP";
                    const swap = swapW ? Boolean(swapW.value) : false;
                    const step = multW ? Math.max(8, Number(multW.value) || 16) : 16;
                    const cW = customW ? Number(customW.value) || 1024 : 1024;
                    const cH = customH ? Number(customH.value) || 1024 : 1024;

                    const isMatchImage = aspect.includes("Match Input Image") || aspect.toLowerCase() === "image";
                    const isCustom = aspect.includes("Custom");

                    let w = 1024, h = 1024;
                    const PRESET_DIMS = {
                        "1:1 Square (1024 x 1024)": [1024, 1024],
                        "16:9 Landscape Widescreen (1344 x 768)": [1344, 768],
                        "9:16 Portrait / Story (768 x 1344)": [768, 1344],
                        "4:3 Standard Photo (1152 x 896)": [1152, 896],
                        "3:4 Classic Portrait (896 x 1152)": [896, 1152],
                        "3:2 Classic 35mm (1216 x 832)": [1216, 832],
                        "2:3 Portrait 35mm (832 x 1216)": [832, 1216],
                        "21:9 Ultrawide Cinema (1536 x 640)": [1536, 640],
                        "9:21 Ultrawide Vertical (640 x 1536)": [640, 1536],
                        "4:5 Social Media Portrait (960 x 1200)": [960, 1200],
                        "5:4 Social Media Landscape (1200 x 960)": [1200, 960],
                    };

                    const RATIO_VALS = {
                        "1:1 Square (1024 x 1024)": 1.0,
                        "16:9 Landscape Widescreen (1344 x 768)": 16.0 / 9.0,
                        "9:16 Portrait / Story (768 x 1344)": 9.0 / 16.0,
                        "4:3 Standard Photo (1152 x 896)": 4.0 / 3.0,
                        "3:4 Classic Portrait (896 x 1152)": 3.0 / 4.0,
                        "3:2 Classic 35mm (1216 x 832)": 3.0 / 2.0,
                        "2:3 Portrait 35mm (832 x 1216)": 2.0 / 3.0,
                        "21:9 Ultrawide Cinema (1536 x 640)": 21.0 / 9.0,
                        "9:21 Ultrawide Vertical (640 x 1536)": 9.0 / 21.0,
                        "4:5 Social Media Portrait (960 x 1200)": 4.0 / 5.0,
                        "5:4 Social Media Landscape (1200 x 960)": 5.0 / 4.0,
                    };

                    let targetPixels = 1024 * 1024;
                    if (scale.includes("0.26 MP")) targetPixels = 512 * 512;
                    else if (scale.includes("0.9 MP")) targetPixels = 1280 * 720;
                    else if (scale.includes("1.5 MP")) targetPixels = 1280 * 1280;
                    else if (scale.includes("2.0 MP")) targetPixels = 1440 * 1440;
                    else if (scale.includes("2.1 MP")) targetPixels = 1920 * 1080;
                    else if (scale.includes("4.0 MP")) targetPixels = 2160 * 2160;

                    let note = "";
                    if (isMatchImage) {
                        const imgSlot = node.inputs ? node.inputs.find(i => i.name === "image") : null;
                        if (!imgSlot || imgSlot.link === null) {
                            note = "⚠️ No Image (fallback 1024×1024)";
                            w = 1024; h = 1024;
                        } else {
                            note = "📷 Auto-match proporzioni immagine";
                            w = 1024; h = 1024;
                        }
                    } else if (isCustom) {
                        w = Math.round(cW / step) * step;
                        h = Math.round(cH / step) * step;
                    } else if (scale.includes("Exact Preset") && PRESET_DIMS[aspect]) {
                        [w, h] = PRESET_DIMS[aspect];
                        w = Math.round(w / step) * step;
                        h = Math.round(h / step) * step;
                    } else {
                        const ratio = RATIO_VALS[aspect] || 1.0;
                        const rawH = Math.sqrt(targetPixels / ratio);
                        const rawW = rawH * ratio;
                        w = Math.max(step, Math.round(rawW / step) * step);
                        h = Math.max(step, Math.round(rawH / step) * step);
                    }

                    if (swap) {
                        const temp = w; w = h; h = temp;
                    }

                    const calcRatio = h > 0 ? (w / h).toFixed(2) : "1.00";
                    const mpx = ((w * h) / 1000000).toFixed(2);
                    const tensorMb = ((w * h * 12) / (1024 * 1024)).toFixed(1);
                    const latentMb = ((w * h * 0.5) / (1024 * 1024)).toFixed(1);

                    const margin = 12;
                    const cardW = width - margin * 2;
                    const cardH = this.height;

                    ctx.save();
                    ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
                    ctx.strokeStyle = "rgba(56, 189, 248, 0.40)";
                    ctx.lineWidth = 1;
                    if (ctx.roundRect) {
                        ctx.beginPath();
                        ctx.roundRect(margin, y, cardW, cardH, 6);
                        ctx.fill();
                        ctx.stroke();
                    } else {
                        ctx.fillRect(margin, y, cardW, cardH);
                        ctx.strokeRect(margin, y, cardW, cardH);
                    }

                    // Left accent bar
                    ctx.fillStyle = "#2997ff";
                    if (ctx.roundRect) {
                        ctx.beginPath();
                        ctx.roundRect(margin, y, 4, cardH, [6, 0, 0, 6]);
                        ctx.fill();
                    } else {
                        ctx.fillRect(margin, y, 4, cardH);
                    }

                    // Line 1: Dimensions, aspect ratio, MP
                    ctx.font = "bold 11px Inter, sans-serif";
                    ctx.fillStyle = "#f8fafc";
                    ctx.textAlign = "left";
                    ctx.textBaseline = "middle";
                    ctx.fillText(`📐 ${w} × ${h}  •  ${calcRatio}:1  •  ${mpx} MP`, margin + 12, y + 14);

                    // Line 2: VRAM & Latent estimate
                    ctx.font = "10px Inter, monospace, sans-serif";
                    ctx.fillStyle = "#94a3b8";
                    let line2 = `💾 ~${tensorMb} MB VRAM (Flux Latent: ~${latentMb} MB)`;
                    if (note) {
                        line2 += ` • ${note}`;
                    }
                    ctx.fillText(line2, margin + 12, y + 30);

                    ctx.restore();
                }
            }

            function setupResNode(node) {
                if (!node || !node.widgets) return;
                if (!node.size || node.size[0] < MIN_RES_WIDTH) {
                    node.size = [MIN_RES_WIDTH, node.size ? node.size[1] : 240];
                }

                function ensureResHUD() {
                    if (!node.widgets.some(w => w.name === "_stoiqo_res_hud")) {
                        node.widgets.push(new StoiqoResolutionHUDWidget(node));
                    }
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

                    ensureResHUD();

                    if (typeof node.computeSize === "function") {
                        const computed = node.computeSize();
                        node.size[0] = Math.max(node.size[0] || 0, MIN_RES_WIDTH);
                        node.size[1] = Math.max(Math.ceil(computed[1]), 80);
                    }
                    node.setDirtyCanvas(true, true);
                }

                node.widgets.forEach(w => {
                    if (w.name !== "_stoiqo_res_hud" && !w._stoiqoResHooked) {
                        w._stoiqoResHooked = true;
                        const origCallback = w.callback;
                        w.callback = function() {
                            if (origCallback) origCallback.apply(this, arguments);
                            updateCustomDimsVisibility();
                            node.setDirtyCanvas(true, true);
                        };
                    }
                });

                const origConnChange = node.onConnectionsChange;
                node.onConnectionsChange = function(type, index, isConnected, link_info) {
                    if (origConnChange) origConnChange.apply(this, arguments);
                    node.setDirtyCanvas(true, true);
                };

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
