import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

/**
 * [STOIQO] Prompt Generator Engine — Visual & Ergonomics Suite
 * Provides clean section dividers, non-overlapping widget layouts,
 * tuned multiline text boxes, and polished canvas aesthetics.
 */

// Global download progress tracker received via WebSocket from backend
export let currentDownloadProgress = null;
let downloadClearTimer = null;

const comfyApi = api || (typeof app !== "undefined" && app.api);
if (comfyApi && comfyApi.addEventListener) {
    comfyApi.addEventListener("stoiqo_download_progress", (event) => {
        const data = event.detail;
        if (!data) return;
        currentDownloadProgress = data;

        if (data.status === "complete") {
            if (downloadClearTimer) clearTimeout(downloadClearTimer);
            downloadClearTimer = setTimeout(() => {
                currentDownloadProgress = null;
                if (app && app.graph) app.graph.setDirtyCanvas(true, true);
            }, 6000);
        }
        if (app && app.graph) app.graph.setDirtyCanvas(true, true);
    });
}

// Standalone Divider Widget compatible with LiteGraph & ComfyUI
export class StoiqoSectionDividerWidget {
    constructor(sectionNum, sectionTitle, accentColor) {
        this.type = "custom";
        this.name = `_stoiqo_divider_${sectionNum}`;
        this.value = {};
        this.options = { serialize: false };
        this.sectionNum = sectionNum;
        this.sectionTitle = sectionTitle;
        this.accentColor = accentColor;
        this.isStoiqoDivider = true;
        this.height = 30;
    }

    serializeValue() {
        return undefined; // Never serialized or sent to backend
    }

    computeSize(width) {
        return [width, this.height];
    }

    draw(ctx, node, width, posY, height) {
        const nodeWidth = (node && node.size) ? node.size[0] : width;
        const accent = this.accentColor;
        const bannerY = posY + 5;

        ctx.save();

        // Glowing separator hairline across node width
        const lineY = bannerY + 10;
        const grad = ctx.createLinearGradient(12, lineY, nodeWidth - 12, lineY);
        grad.addColorStop(0, accent + "08");
        grad.addColorStop(0.2, accent + "88");
        grad.addColorStop(0.8, accent + "88");
        grad.addColorStop(1, accent + "08");
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(12, lineY);
        ctx.lineTo(nodeWidth - 12, lineY);
        ctx.stroke();

        // Pill Badge
        const label = `§ ${this.sectionNum}. ${this.sectionTitle}`;
        ctx.font = "bold 9px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif";
        const textMetrics = ctx.measureText(label);
        const badgeX = 14;
        const badgeY = bannerY + 2;
        const badgeW = Math.ceil(textMetrics.width) + 18;
        const badgeH = 16;

        // Badge background with subtle border (adapts to any node color)
        ctx.fillStyle = "rgba(0, 0, 0, 0.35)";
        if (ctx.roundRect) {
            ctx.beginPath();
            ctx.roundRect(badgeX, badgeY, badgeW, badgeH, 3);
            ctx.fill();
            ctx.strokeStyle = accent + "aa";
            ctx.lineWidth = 1;
            ctx.stroke();
        } else {
            ctx.fillRect(badgeX, badgeY, badgeW, badgeH);
            ctx.strokeStyle = accent + "aa";
            ctx.lineWidth = 1;
            ctx.strokeRect(badgeX, badgeY, badgeW, badgeH);
        }

        // Dot indicator
        ctx.fillStyle = accent;
        ctx.beginPath();
        ctx.arc(badgeX + 7, badgeY + badgeH / 2, 2, 0, Math.PI * 2);
        ctx.fill();

        // Badge Text
        ctx.fillStyle = "#f8fafc";
        ctx.textAlign = "left";
        ctx.textBaseline = "middle";
        ctx.fillText(label, badgeX + 13, badgeY + badgeH / 2 + 0.5);

        // Download Progress Indicator Badge on Section 1
        if (this.sectionNum === "1" && currentDownloadProgress) {
            const dp = currentDownloadProgress;
            const isDone = dp.status === "complete" || dp.percent >= 100;
            const dlLabel = isDone
                ? "✓ Model Ready"
                : `⬇ DL ${dp.percent}% (${dp.downloaded_str || ""})`;
            const dlColor = isDone ? "#22c55e" : "#38bdf8";

            ctx.font = "bold 9px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif";
            const dlMetrics = ctx.measureText(dlLabel);
            const dlBadgeW = Math.ceil(dlMetrics.width) + 16;
            const dlBadgeX = nodeWidth - 14 - dlBadgeW;
            const dlBadgeY = badgeY;
            const dlBadgeH = badgeH;

            if (dlBadgeX > badgeX + badgeW + 8) {
                // Background
                ctx.fillStyle = "rgba(15, 23, 42, 0.9)";
                if (ctx.roundRect) {
                    ctx.beginPath();
                    ctx.roundRect(dlBadgeX, dlBadgeY, dlBadgeW, dlBadgeH, 3);
                    ctx.fill();
                } else {
                    ctx.fillRect(dlBadgeX, dlBadgeY, dlBadgeW, dlBadgeH);
                }

                // Inner progress bar fill
                if (!isDone && dp.percent > 0) {
                    const progressW = Math.max(0, Math.min(dlBadgeW - 2, ((dlBadgeW - 2) * dp.percent) / 100));
                    ctx.fillStyle = "rgba(56, 189, 248, 0.28)";
                    if (ctx.roundRect) {
                        ctx.beginPath();
                        ctx.roundRect(dlBadgeX + 1, dlBadgeY + 1, progressW, dlBadgeH - 2, 2);
                        ctx.fill();
                    } else {
                        ctx.fillRect(dlBadgeX + 1, dlBadgeY + 1, progressW, dlBadgeH - 2);
                    }
                }

                // Border
                ctx.strokeStyle = dlColor + "bb";
                ctx.lineWidth = 1;
                if (ctx.roundRect) {
                    ctx.beginPath();
                    ctx.roundRect(dlBadgeX, dlBadgeY, dlBadgeW, dlBadgeH, 3);
                    ctx.stroke();
                } else {
                    ctx.strokeRect(dlBadgeX, dlBadgeY, dlBadgeW, dlBadgeH);
                }

                // Text
                ctx.fillStyle = dlColor;
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(dlLabel, dlBadgeX + dlBadgeW / 2, dlBadgeY + dlBadgeH / 2 + 0.5);
            }
        }

        ctx.restore();
    }
}


    
    
        const engineTargetNames = [
            "StoiqoPromptGeneratorEngineNode",
            "QwenVLCaptionerNode",
            "[STOIQO] Prompt Generator Engine",
            "[STOIQO] Prompt Generator Engine (Legacy)",
        ];

        const showPromptTargetNames = [
            "StoiqoShowPromptNode",
            "QwenVLTextDisplayNode",
            "[STOIQO] Show Prompt",
            "[STOIQO] Show Prompt (Legacy)",
        ];