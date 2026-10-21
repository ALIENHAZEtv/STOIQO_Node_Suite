/**
 * [STOIQO] Pro Image Saver & Metadata Hub — Frontend Widget
 * Features:
 * - Suppresses bulky default ComfyUI output previews to keep workspace clean
 * - Sleek, cyber-styled compact HUD card showing export status, format, size & resolution
 * - Interactive action buttons: Copy Full Path, Copy Filename, Copy Folder
 * - Zero preview clutter, 100% focused on workflow telemetry & file management
 */

export function setupProSaverNode(nodeType, nodeData, appInstance) {
    const targetNames = [
        "StoiqoProImageSaverNode",
        "[STOIQO] Pro Image Saver & Metadata Hub",
    ];

    if (!targetNames.includes(nodeData.name)) return;

    class StoiqoSaverStatusWidget {
        constructor(node) {
            this.type = "custom";
            this.name = "_stoiqo_saver_hud";
            this.value = {};
            this.options = { serialize: false };
            this.node = node;

            this.lastSaveInfo = null; // Array or single object from python execution
            this.copiedButton = null; // Key of button temporarily flashing copied status
            this.copyTimeout = null;

            this.buttonRects = {}; // Hit areas for interactive buttons
        }

        serializeValue() {
            return undefined;
        }

        computeSize(width) {
            return [width, 130];
        }

        setSaveInfo(infos) {
            if (Array.isArray(infos) && infos.length > 0) {
                this.lastSaveInfo = infos;
            } else if (infos && typeof infos === "object") {
                this.lastSaveInfo = [infos];
            } else {
                this.lastSaveInfo = null;
            }
            this.node.setDirtyCanvas(true, true);
        }

        copyToClipboard(text, buttonKey) {
            if (!text) return;
            try {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(text);
                } else {
                    const ta = document.createElement("textarea");
                    ta.value = text;
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand("copy");
                    document.body.removeChild(ta);
                }
                this.copiedButton = buttonKey;
                if (this.copyTimeout) clearTimeout(this.copyTimeout);
                this.copyTimeout = setTimeout(() => {
                    this.copiedButton = null;
                    if (this.node) this.node.setDirtyCanvas(true, false);
                }, 2000);
                this.node.setDirtyCanvas(true, false);
            } catch (err) {
                console.error("[STOIQO Pro Saver] Clipboard copy failed:", err);
            }
        }

        draw(ctx, node, width, y, height) {
            const padX = 14;
            const cardX = padX;
            const cardY = y + 4;
            const cardW = width - (padX * 2);
            const cardH = 120;

            this.buttonRects = {};

            ctx.save();

            // Background card
            ctx.fillStyle = "#12141a";
            ctx.strokeStyle = "#252b3b";
            ctx.lineWidth = 1.2;

            if (ctx.roundRect) {
                ctx.beginPath();
                ctx.roundRect(cardX, cardY, cardW, cardH, 8);
                ctx.fill();
                ctx.stroke();
            } else {
                ctx.fillRect(cardX, cardY, cardW, cardH);
                ctx.strokeRect(cardX, cardY, cardW, cardH);
            }

            if (!this.lastSaveInfo || this.lastSaveInfo.length === 0) {
                // Standby State
                ctx.fillStyle = "#4a5568";
                ctx.font = "bold 11px system-ui, -apple-system, sans-serif";
                ctx.textAlign = "center";
                ctx.fillText("READY / IN ATTESA DI GENERAZIONE", cardX + cardW / 2, cardY + 50);

                ctx.fillStyle = "#2d3748";
                ctx.font = "10px monospace";
                ctx.fillText("I file salvati e i metadati appariranno qui", cardX + cardW / 2, cardY + 74);
                ctx.restore();
                return;
            }

            const info = this.lastSaveInfo[0];
            const batchCount = this.lastSaveInfo.length;

            // Status Badge (Top Row)
            const badgeY = cardY + 16;
            ctx.fillStyle = "#10b981"; // Emerald green
            ctx.font = "bold 10px system-ui, -apple-system, sans-serif";
            ctx.textAlign = "left";
            ctx.fillText("✓ SALVATO", cardX + 12, badgeY);

            // Format & Size Badges
            const tagText = `${info.format || "IMG"} • ${info.width}x${info.height} • ${info.size_str || ""}${batchCount > 1 ? ` (+${batchCount - 1} altri)` : ""}`;
            ctx.fillStyle = "#00e5ff"; // Cyan highlight
            ctx.font = "bold 10px monospace";
            ctx.textAlign = "right";
            ctx.fillText(tagText, cardX + cardW - 12, badgeY);

            // Filename (Middle Row)
            const fileY = cardY + 40;
            ctx.fillStyle = "#ffffff";
            ctx.font = "bold 11px monospace";
            ctx.textAlign = "left";

            let displayFilename = info.filename || "file_output";
            const maxNameLen = Math.floor((cardW - 24) / 7.5);
            if (displayFilename.length > maxNameLen) {
                displayFilename = displayFilename.substring(0, maxNameLen - 3) + "...";
            }
            ctx.fillText(displayFilename, cardX + 12, fileY);

            // Subfolder / Path label
            const subfolderY = cardY + 58;
            ctx.fillStyle = "#718096";
            ctx.font = "10px monospace";
            let displaySub = `📁 ${info.subfolder || "output"}`;
            if (displaySub.length > maxNameLen + 4) {
                displaySub = displaySub.substring(0, maxNameLen + 1) + "...";
            }
            ctx.fillText(displaySub, cardX + 12, subfolderY);

            // Action Buttons Row (Bottom)
            const btnY = cardY + 76;
            const btnH = 26;
            const btnGap = 8;
            const btnCount = 3;
            const totalGap = btnGap * (btnCount - 1);
            const btnW = Math.floor((cardW - 24 - totalGap) / btnCount);

            const buttons = [
                {
                    id: "copy_path",
                    text: this.copiedButton === "copy_path" ? "✓ COPIATO" : "📋 COPIA PATH",
                    active: this.copiedButton === "copy_path",
                    actionText: info.filepath,
                },
                {
                    id: "copy_name",
                    text: this.copiedButton === "copy_name" ? "✓ COPIATO" : "📄 COPIA NOME",
                    active: this.copiedButton === "copy_name",
                    actionText: info.filename,
                },
                {
                    id: "copy_folder",
                    text: this.copiedButton === "copy_folder" ? "✓ COPIATO" : "📁 COPIA DIR",
                    active: this.copiedButton === "copy_folder",
                    actionText: info.filepath ? info.filepath.substring(0, info.filepath.lastIndexOf(info.filename || "") - 1) : info.subfolder,
                },
            ];

            buttons.forEach((btn, idx) => {
                const bX = cardX + 12 + idx * (btnW + btnGap);
                this.buttonRects[btn.id] = { x: bX, y: btnY, w: btnW, h: btnH, data: btn.actionText };

                // Button Fill
                ctx.fillStyle = btn.active ? "#065f46" : "#1a202c";
                ctx.strokeStyle = btn.active ? "#10b981" : "#2d3748";
                ctx.lineWidth = 1;

                if (ctx.roundRect) {
                    ctx.beginPath();
                    ctx.roundRect(bX, btnY, btnW, btnH, 5);
                    ctx.fill();
                    ctx.stroke();
                } else {
                    ctx.fillRect(bX, btnY, btnW, btnH);
                    ctx.strokeRect(bX, btnY, btnW, btnH);
                }

                // Button Text
                ctx.fillStyle = btn.active ? "#6ee7b7" : "#cbd5e1";
                ctx.font = "bold 9px system-ui, -apple-system, sans-serif";
                ctx.textAlign = "center";
                ctx.fillText(btn.text, bX + btnW / 2, btnY + 16);
            });

            ctx.restore();
        }

        onMouseDown(event, localPos) {
            const x = localPos[0];
            const y = localPos[1];

            for (const [btnId, rect] of Object.entries(this.buttonRects)) {
                if (x >= rect.x && x <= rect.x + rect.w && y >= rect.y && y <= rect.y + rect.h) {
                    this.copyToClipboard(rect.data, btnId);
                    return true;
                }
            }
            return false;
        }
    }

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
        if (onNodeCreated) onNodeCreated.apply(this, arguments);

        // Suppress bulky output preview rectangles
        this.hideOutputImages = true;
        this.imgs = null;
        this.images = null;

        // Add custom HUD status widget
        const hudWidget = new StoiqoSaverStatusWidget(this);
        this.addCustomWidget(hudWidget);
        this._stoiqo_saver_hud = hudWidget;

        // Ensure comfortable node dimensions
        if (!this.size || this.size[0] < 380) {
            this.size = [380, Math.max(this.size ? this.size[1] : 300, 360)];
        }

        // Intercept execution results
        const origOnExecuted = this.onExecuted;
        this.onExecuted = function (message) {
            if (origOnExecuted) {
                origOnExecuted.apply(this, arguments);
            }

            // Suppress bulky output preview rendering on canvas while preserving metadata for sidebar
            this.hideOutputImages = true;
            this.imgs = null;
            if (message && message.images) {
                this.images = message.images;
            }

            if (message && message.saved_info && this._stoiqo_saver_hud) {
                this._stoiqo_saver_hud.setSaveInfo(message.saved_info);
            }
            this.setDirtyCanvas(true, true);
        };
    };

    // Override onDrawBackground to avoid default preview image rendering on canvas
    const origDrawBackground = nodeType.prototype.onDrawBackground;
    nodeType.prototype.onDrawBackground = function (ctx) {
        this.hideOutputImages = true;
        this.imgs = null;
        if (origDrawBackground) {
            origDrawBackground.apply(this, arguments);
        }
    };
}
