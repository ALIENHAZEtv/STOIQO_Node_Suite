import { app } from "../../../scripts/app.js";

/**
 * [STOIQO] Prompt Generator — Mode HUD Badge
 * 
 * Displays a persistent, dynamic HUD status bar directly inside the
 * StoiqoPromptGeneratorNode card.
 * 
 * Operating Modes:
 *   📝 TEXT EXPANSION       — No image connected, generating rich visual concept from text directives
 *   🖼️ SINGLE IMAGE VISION  — 1 reference image, vision-language analysis & deep captioning
 *   🔀 MULTI-IMAGE FUSION   — 2-4 images, cross-generation reasoning fusing multiple visual references
 *   📦 BATCH CAPTION        — >4 images, captions each image independently for dataset export
 * 
 * Reactivity:
 *   - Updates instantly when the "image" input wire is connected/disconnected.
 *   - Displays active Prompt Type and Artistic Style from node dropdowns.
 *   - Receives post-execution runtime telemetry & verified image count from Python.
 */

const TARGET_NODE_NAMES = [
    "StoiqoPromptGeneratorNode",
    "[STOIQO] Prompt Generator",
];

const MODE_CONFIG = {
    "text_expansion": {
        icon: "📝",
        badgeText: "TEXT EXPANSION",
        color: "#58b0ff",
        bg: "rgba(41, 151, 255, 0.16)",
        border: "rgba(41, 151, 255, 0.50)",
        dot: "#2997ff",
    },
    "single_image": {
        icon: "🖼️",
        badgeText: "SINGLE IMAGE VISION",
        color: "#30d158",
        bg: "rgba(48, 209, 88, 0.16)",
        border: "rgba(48, 209, 88, 0.50)",
        dot: "#30d158",
    },
    "multi_fusion": {
        icon: "🔀",
        badgeText: "MULTI-IMAGE FUSION",
        color: "#ff9f0a",
        bg: "rgba(255, 159, 10, 0.18)",
        border: "rgba(255, 159, 10, 0.55)",
        dot: "#ff9f0a",
    },
    "batch_caption": {
        icon: "📦",
        badgeText: "BATCH CAPTION",
        color: "#2997ff",
        bg: "rgba(41, 151, 255, 0.16)",
        border: "rgba(41, 151, 255, 0.50)",
        dot: "#2997ff",
    },
};

function drawRoundRect(ctx, x, y, w, h, r) {
    if (ctx.roundRect) {
        ctx.beginPath();
        ctx.roundRect(x, y, w, h, r);
    } else {
        ctx.beginPath();
        ctx.rect(x, y, w, h);
    }
}

function truncateText(ctx, text, maxW) {
    if (!text) return "";
    if (ctx.measureText(text).width <= maxW) return text;
    let t = text;
    while (t.length > 1 && ctx.measureText(t + "…").width > maxW) {
        t = t.slice(0, -1);
    }
    return t + "…";
}

export class StoiqoPromptHUDWidget {
    constructor(node) {
        this.node = node;
        this.type = "custom";
        this.name = "_stoiqo_mode_hud";
        this.value = {};
        this.serialize = false;
        this.options = { serialize: false };
        this.isStoiqoHUD = true;
        this.height = 36;
    }

    serializeValue() {
        return undefined; // Not saved to workflow JSON / not sent to backend
    }

    computeSize(width) {
        return [width, this.height];
    }

    draw(ctx, node, width, posY, height) {
        const nodeWidth = (node && node.size) ? node.size[0] : width;
        const totalW = nodeWidth - 20;
        const startX = 10;
        const startY = posY + 3;
        const barH = 30;

        ctx.save();

        // 1. Determine active mode and status
        const executedData = node.stoiqo_mode_data;
        const isExecuted = Boolean(executedData && executedData.mode);

        const imageInput = node.inputs ? node.inputs.find(i => i.name === "image_input" || i.name === "image") : null;
        const textInput = node.inputs ? node.inputs.find(i => i.name === "text_input" || i.name === "text") : null;
        const hasImageLink = imageInput && imageInput.link != null;
        const hasTextLink = textInput && textInput.link != null;

        let modeKey = "text_expansion";
        let displayCount = 0;

        if (isExecuted) {
            modeKey = executedData.mode;
            displayCount = executedData.count || 0;
        } else if (hasImageLink) {
            modeKey = "single_image";
            displayCount = 1;
        } else {
            modeKey = "text_expansion";
            displayCount = 0;
        }

        const cfg = MODE_CONFIG[modeKey] || MODE_CONFIG["text_expansion"];

        // Read active prompt_type and prompt_style (with fallback to artistic_style)
        const ptWidget = node.widgets ? node.widgets.find(w => w.name === "prompt_type") : null;
        const asWidget = node.widgets ? node.widgets.find(w => w.name === "prompt_style" || w.name === "artistic_style") : null;
        let promptType = executedData?.prompt_type || (ptWidget ? ptWidget.value : "Detailed Narrative");
        let artisticStyle = executedData?.prompt_style || executedData?.artistic_style || (asWidget ? asWidget.value : "Auto-Detect");

        // Clean up display strings (e.g. strip "(Long)" or "Auto-Detect / ")
        promptType = String(promptType).replace(/\s*\(Long\)/i, "").trim();
        artisticStyle = String(artisticStyle).replace(/Auto-Detect\s*\/\s*/i, "").trim();

        // 2. Outer HUD Frame (Glassmorphism dark container)
        drawRoundRect(ctx, startX, startY, totalW, barH, 5);
        ctx.fillStyle = "rgba(10, 14, 23, 0.85)";
        ctx.fill();
        ctx.strokeStyle = "rgba(255, 255, 255, 0.09)";
        ctx.lineWidth = 1;
        ctx.stroke();

        // Subtle glowing accent hairline on the top of HUD
        const lineGrad = ctx.createLinearGradient(startX, startY, startX + totalW, startY);
        lineGrad.addColorStop(0, cfg.color + "11");
        lineGrad.addColorStop(0.3, cfg.color + "aa");
        lineGrad.addColorStop(0.7, cfg.color + "aa");
        lineGrad.addColorStop(1, cfg.color + "11");
        ctx.strokeStyle = lineGrad;
        ctx.beginPath();
        ctx.moveTo(startX + 2, startY);
        ctx.lineTo(startX + totalW - 2, startY);
        ctx.stroke();

        // 3. Left Pill: Mode Badge
        let badgeLabel = cfg.badgeText;
        if (displayCount > 1) {
            badgeLabel += ` (${displayCount})`;
        }

        ctx.font = "bold 9px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";
        const badgeTextW = ctx.measureText(badgeLabel).width;
        const pillW = badgeTextW + 28;
        const pillH = 18;
        const pillX = startX + 6;
        const pillY = startY + 6;

        drawRoundRect(ctx, pillX, pillY, pillW, pillH, 4);
        ctx.fillStyle = cfg.bg;
        ctx.fill();
        ctx.strokeStyle = cfg.border;
        ctx.lineWidth = 1;
        ctx.stroke();

        // Status glowing dot
        ctx.fillStyle = cfg.dot;
        ctx.beginPath();
        ctx.arc(pillX + 8, pillY + pillH / 2, 2.5, 0, Math.PI * 2);
        ctx.fill();

        // Mode text
        ctx.fillStyle = cfg.color;
        ctx.textAlign = "left";
        ctx.textBaseline = "middle";
        ctx.fillText(badgeLabel, pillX + 16, pillY + pillH / 2 + 0.5);

        // 4. Middle / Right: Breadcrumbs (Prompt Type + Style)
        const leftOccupied = pillX + pillW + 10;
        const rightStatusW = isExecuted ? 50 : 44;
        const availInfoW = totalW - (leftOccupied - startX) - rightStatusW - 12;

        if (availInfoW > 60) {
            ctx.font = "9px 'JetBrains Mono', SFMono-Regular, Consolas, -apple-system, sans-serif";
            const infoText = `${promptType} • ${artisticStyle}`;
            const fittedInfo = truncateText(ctx, infoText, availInfoW);

            ctx.fillStyle = "#94a3b8";
            ctx.textAlign = "left";
            ctx.textBaseline = "middle";
            ctx.fillText(fittedInfo, leftOccupied, startY + barH / 2 + 0.5);
        }

        // 5. Far Right: State Indicator (READY vs ACTIVE)
        const statusLabel = isExecuted ? "● ACTIVE" : (hasImageLink ? "● LINKED" : "● READY");
        const statusColor = isExecuted ? "#30d158" : (hasImageLink ? "#2997ff" : "#64748b");

        ctx.font = "bold 8.5px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
        ctx.fillStyle = statusColor;
        ctx.textAlign = "right";
        ctx.textBaseline = "middle";
        ctx.fillText(statusLabel, startX + totalW - 8, startY + barH / 2 + 0.5);

        ctx.restore();
    }
}

function ensureHUDWidget(node) {
    if (!node || !node.widgets) return;
    const existing = node.widgets.filter(w => w.name === "_stoiqo_mode_hud" || w.isStoiqoHUD);
    for (const extra of existing.slice(1)) {
        node.widgets.splice(node.widgets.indexOf(extra), 1);
    }
    let hud = existing[0];
    if (!hud) {
        hud = new StoiqoPromptHUDWidget(node);
        node.widgets.push(hud);
        if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
    }
}

export function setupPromptGeneratorNode(nodeType, nodeData, app) {
    if (!TARGET_NODE_NAMES.includes(nodeData.name)) return;

    // 1. Hook onNodeCreated
    const origOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function() {
        if (origOnNodeCreated) origOnNodeCreated.apply(this, arguments);

        if (this.size && this.size[0] < 380) {
            this.size[0] = 380;
        }

        ensureHUDWidget(this);

        // React immediately when connections change (e.g. image wire plugged or unplugged)
        const origOnConnectionsChange = this.onConnectionsChange;
        this.onConnectionsChange = function(type, index, isConnected, link_info) {
            if (origOnConnectionsChange) origOnConnectionsChange.apply(this, arguments);
            if (this.setDirtyCanvas) this.setDirtyCanvas(true, false);
        };
    };

    // 2. Hook onConfigure (when loading existing workflow)
    const origOnConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function() {
        if (origOnConfigure) origOnConfigure.apply(this, arguments);
        ensureHUDWidget(this);
    };

    // 3. Hook onExecuted (receive runtime telemetry & mode payload from Python)
    const origOnExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function(message) {
        if (origOnExecuted) origOnExecuted.apply(this, arguments);

        if (message && message.stoiqo_mode && message.stoiqo_mode.length > 0) {
            this.stoiqo_mode_data = message.stoiqo_mode[0];
            if (this.setDirtyCanvas) this.setDirtyCanvas(true, false);
        }
    };
}
