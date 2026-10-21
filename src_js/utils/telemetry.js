/**
 * [STOIQO] Node Execution Telemetry & Performance Badge
 * Displays execution time in ms/s and peak VRAM allocation directly
 * in the node header (e.g. ⚡ 182ms | 4.2 GB VRAM).
 */

import { api } from "../../scripts/api.js";

// Global WebSocket listener for real-time telemetry events
let listenerAttached = false;

export function initGlobalTelemetryListener(appInstance) {
    if (listenerAttached) return;
    listenerAttached = true;

    if (api && api.addEventListener) {
        api.addEventListener("stoiqo_node_telemetry", (event) => {
            const data = event.detail;
            if (!data) return;

            if (appInstance && appInstance.graph && data.node_id) {
                const node = appInstance.graph.getNodeById(data.node_id);
                if (node) {
                    node.stoiqo_telemetry = data;
                    if (node.setDirtyCanvas) node.setDirtyCanvas(true, false);
                }
            }
        });
    }
}

export function setupTelemetryBadge(nodeType, nodeData, appInstance) {
    initGlobalTelemetryListener(appInstance);

    const origOnExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function(message) {
        if (origOnExecuted) origOnExecuted.apply(this, arguments);

        if (message && message.stoiqo_telemetry && message.stoiqo_telemetry.length > 0) {
            this.stoiqo_telemetry = message.stoiqo_telemetry[0];
            if (this.setDirtyCanvas) this.setDirtyCanvas(true, false);
        }
    };

    const origOnDrawForeground = nodeType.prototype.onDrawForeground;
    nodeType.prototype.onDrawForeground = function(ctx) {
        if (origOnDrawForeground) origOnDrawForeground.apply(this, arguments);

        if (this.stoiqo_telemetry) {
            drawTelemetryBadge(this, ctx);
        }
    };
}

function drawTelemetryBadge(node, ctx) {
    const stats = node.stoiqo_telemetry;
    if (!stats || typeof stats.time_ms !== "number") return;

    const timeStr = stats.time_ms < 1000
        ? `${Math.round(stats.time_ms)}ms`
        : `${(stats.time_ms / 1000).toFixed(2)}s`;

    const vramStr = stats.vram_gb && stats.vram_gb > 0
        ? `${stats.vram_gb.toFixed(1)} GB`
        : "0 GB";

    const badgeText = `${timeStr} | ${vramStr}`;

    ctx.save();
    ctx.font = "bold 9.5px 'JetBrains Mono', SFMono-Regular, Consolas, monospace";

    const textMetrics = ctx.measureText(badgeText);
    const iconWidth = 12;
    const paddingX = 7;
    const badgeW = textMetrics.width + iconWidth + (paddingX * 2);
    const badgeH = 16;

    // Position at top-right of node header
    const nodeWidth = (node.flags?.collapsed && node._collapsed_width) 
        ? node._collapsed_width 
        : (node.size ? node.size[0] : 200);
    const posX = Math.max(8, nodeWidth - badgeW - 8);
    const posY = -24;


    // Badge pill background
    ctx.fillStyle = "rgba(10, 14, 22, 0.88)";
    ctx.strokeStyle = "rgba(6, 182, 212, 0.45)";
    ctx.lineWidth = 1;

    if (ctx.roundRect) {
        ctx.beginPath();
        ctx.roundRect(posX, posY, badgeW, badgeH, 4);
        ctx.fill();
        ctx.stroke();
    } else {
        ctx.fillRect(posX, posY, badgeW, badgeH);
        ctx.strokeRect(posX, posY, badgeW, badgeH);
    }

    // Lightning bolt icon (⚡)
    ctx.fillStyle = "#06b6d4";
    ctx.fillText("⚡", posX + paddingX, posY + 12);

    // Text metrics
    ctx.fillStyle = "#cbd5e1";
    ctx.fillText(badgeText, posX + paddingX + iconWidth, posY + 12);

    ctx.restore();
}
