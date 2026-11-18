// src_js/index.js
import { app as app10 } from "../../scripts/app.js";

// src_js/nodes/showPromptNode.js
import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";
var _streamListenersRegistered = false;
function ensureStreamListeners() {
  if (_streamListenersRegistered || typeof api === "undefined" || !api.addEventListener) return;
  _streamListenersRegistered = true;
  api.addEventListener("stoiqo_stream_start", (evt) => {
    const detail = evt.detail || {};
    const nodeId = detail.node_id;
    if (!nodeId || !app.graph) return;
    const node = app.graph.getNodeById(nodeId);
    if (!node) return;
    let tw = node.widgets?.find((w) => w.name === "display_text" || w.name === "text" || w.name === "synthesized_prompt");
    if (tw) {
      tw.value = "";
      if (tw.inputEl) tw.inputEl.value = "";
      if (node._batchTexts) {
        node._batchTexts = [""];
        node._batchIndex = 0;
      }
      node.setDirtyCanvas(true);
    }
  });
  api.addEventListener("stoiqo_stream_token", (evt) => {
    const detail = evt.detail || {};
    const nodeId = detail.node_id;
    const token = detail.token;
    if (!nodeId || token === void 0 || !app.graph) return;
    const node = app.graph.getNodeById(nodeId);
    if (!node) return;
    let tw = node.widgets?.find((w) => w.name === "display_text" || w.name === "text" || w.name === "synthesized_prompt");
    if (tw) {
      tw.value = (tw.value || "") + token;
      if (tw.inputEl) {
        tw.inputEl.value = tw.value;
        tw.inputEl.scrollTop = tw.inputEl.scrollHeight;
      }
      if (node._batchTexts && node._batchTexts.length > 0) {
        node._batchTexts[node._batchIndex || 0] = tw.value;
      }
      node.setDirtyCanvas(true);
    }
  });
  api.addEventListener("stoiqo_stream_complete", (evt) => {
    const detail = evt.detail || {};
    const nodeId = detail.node_id;
    if (!nodeId || !app.graph) return;
    const node = app.graph.getNodeById(nodeId);
    if (node) {
      node.setDirtyCanvas(true, true);
    }
  });
}
function syncDisplayWidgetText(node) {
  const tw = node.widgets?.find((w) => w.name === "display_text");
  if (!tw) return;
  let targetText = "";
  if (node._viewAll && node._batchTexts && node._batchTexts.length > 0) {
    targetText = node._batchTexts.map((t, idx) => `=== PROMPT #${idx + 1} ===
${t}`).join("\n\n");
  } else if (node._batchTexts && node._batchTexts.length > 0) {
    targetText = node._batchTexts[node._batchIndex || 0] || "";
  } else {
    targetText = tw.value || "";
  }
  tw.value = targetText;
  if (tw.inputEl) {
    tw.inputEl.value = targetText;
  }
  node.setDirtyCanvas(true, true);
}
function drawChipButton(ctx, rect, label, bg, border, textColor, icon) {
  ctx.save();
  ctx.fillStyle = bg;
  ctx.strokeStyle = border;
  ctx.lineWidth = 1;
  ctx.beginPath();
  if (ctx.roundRect) {
    ctx.roundRect(rect.x, rect.y, rect.w, rect.h, 4);
  } else {
    ctx.rect(rect.x, rect.y, rect.w, rect.h);
  }
  ctx.fill();
  ctx.stroke();
  ctx.font = "bold 10px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
  ctx.fillStyle = textColor;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  const text = (icon ? icon + " " : "") + label;
  ctx.fillText(text, rect.x + rect.w / 2, rect.y + rect.h / 2);
  ctx.restore();
}
function createPromptViewerWidget(node) {
  const widget = {
    type: "STOIQO_PROMPT_VIEWER",
    name: "prompt_viewer_hud",
    serialize: false,
    options: { serialize: false },
    _feedbackText: null,
    _feedbackAllText: null,
    _rects: {},
    computeSize(width) {
      const isBatch = node._batchTexts && node._batchTexts.length > 1;
      return [width, isBatch ? 66 : 40];
    },
    draw(ctx, node2, width, y, height) {
      const padX = 10;
      const cardW = width - padX * 2;
      const isBatch = node2._batchTexts && node2._batchTexts.length > 1;
      const cardH = isBatch ? 64 : 38;
      this._rects = {};
      ctx.save();
      ctx.fillStyle = "rgba(15, 23, 42, 0.88)";
      ctx.strokeStyle = "rgba(148, 163, 184, 0.22)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      if (ctx.roundRect) {
        ctx.roundRect(padX, y, cardW, cardH, 6);
      } else {
        ctx.rect(padX, y, cardW, cardH);
      }
      ctx.fill();
      ctx.stroke();
      const currentText = node2._batchTexts && node2._batchTexts.length > 0 && !node2._viewAll ? node2._batchTexts[node2._batchIndex || 0] || "" : node2.widgets?.find((w) => w.name === "display_text")?.value || "";
      const words = currentText.trim() ? currentText.trim().split(/\s+/).length : 0;
      const chars = currentText.length;
      const estTokens = words > 0 ? Math.max(1, Math.round(words * 1.33)) : 0;
      let rowY = y + 6;
      if (isBatch) {
        const total = node2._batchTexts.length;
        const idx = (node2._batchIndex || 0) + 1;
        const prevRect = { x: padX + 8, y: rowY, w: 26, h: 22 };
        this._rects.prev = prevRect;
        drawChipButton(ctx, prevRect, "\u25C0", "rgba(30, 41, 59, 0.85)", "rgba(148, 163, 184, 0.35)", "#e2e8f0");
        const badgeLabel = node2._viewAll ? `\u{1F4D1} Batch View (${total})` : `Item ${idx} of ${total}`;
        const badgeRect = { x: padX + 38, y: rowY, w: 104, h: 22 };
        drawChipButton(
          ctx,
          badgeRect,
          badgeLabel,
          node2._viewAll ? "rgba(41, 151, 255, 0.25)" : "rgba(30, 41, 59, 0.6)",
          node2._viewAll ? "rgba(41, 151, 255, 0.45)" : "rgba(148, 163, 184, 0.25)",
          node2._viewAll ? "#2997ff" : "#94a3b8"
        );
        const nextRect = { x: padX + 146, y: rowY, w: 26, h: 22 };
        this._rects.next = nextRect;
        drawChipButton(ctx, nextRect, "\u25B6", "rgba(30, 41, 59, 0.85)", "rgba(148, 163, 184, 0.35)", "#e2e8f0");
        const toggleRect = { x: padX + 178, y: rowY, w: 78, h: 22 };
        this._rects.toggle = toggleRect;
        drawChipButton(
          ctx,
          toggleRect,
          node2._viewAll ? "\u{1F4C4} Singolo" : "\u{1F4D1} Tutti",
          "rgba(30, 41, 59, 0.85)",
          "rgba(148, 163, 184, 0.35)",
          "#cbd5e1"
        );
        rowY += 28;
      }
      ctx.font = "11px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
      ctx.fillStyle = "#94a3b8";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      const statsText = node2._viewAll ? `Totale: ${chars} car. \u2022 ${words} par.` : `${chars} car. \u2022 ${words} par. \u2022 ~${estTokens} tok`;
      ctx.fillText(statsText, padX + 10, rowY + 12);
      const copyLabel = this._feedbackText || (isBatch && node2._viewAll ? "Copia Tutti" : "Copia Prompt");
      const copyW = this._feedbackText ? 110 : isBatch && node2._viewAll ? 85 : 95;
      const copyRect = { x: padX + cardW - copyW - 8, y: rowY + 1, w: copyW, h: 22 };
      this._rects.copy = copyRect;
      const isCopied = !!this._feedbackText;
      drawChipButton(
        ctx,
        copyRect,
        copyLabel,
        isCopied ? "rgba(16, 185, 129, 0.3)" : "rgba(30, 41, 59, 0.9)",
        isCopied ? "rgba(52, 211, 153, 0.6)" : "rgba(148, 163, 184, 0.4)",
        isCopied ? "#34d399" : "#f1f5f9",
        isCopied ? "\u2713" : "\u{1F4CB}"
      );
      if (isBatch && !node2._viewAll) {
        const copyAllLabel = this._feedbackAllText || `Tutti (${node2._batchTexts.length})`;
        const copyAllW = this._feedbackAllText ? 95 : 68;
        const copyAllRect = { x: copyRect.x - copyAllW - 6, y: rowY + 1, w: copyAllW, h: 22 };
        this._rects.copyAll = copyAllRect;
        const isAllCopied = !!this._feedbackAllText;
        drawChipButton(
          ctx,
          copyAllRect,
          copyAllLabel,
          isAllCopied ? "rgba(16, 185, 129, 0.3)" : "rgba(30, 41, 59, 0.75)",
          isAllCopied ? "rgba(52, 211, 153, 0.6)" : "rgba(148, 163, 184, 0.3)",
          isAllCopied ? "#34d399" : "#cbd5e1",
          isAllCopied ? "\u2713" : "\u{1F4D1}"
        );
      }
      ctx.restore();
    },
    mouse(event, pos, node2) {
      if (event.type !== "pointerdown" && event.type !== "mousedown") return false;
      const [clickX, clickY] = pos;
      const isInside = (r) => r && clickX >= r.x && clickX <= r.x + r.w && clickY >= r.y && clickY <= r.y + r.h;
      if (isInside(this._rects.prev)) {
        const total = node2._batchTexts?.length || 1;
        node2._batchIndex = ((node2._batchIndex || 0) - 1 + total) % total;
        node2._viewAll = false;
        syncDisplayWidgetText(node2);
        return true;
      }
      if (isInside(this._rects.next)) {
        const total = node2._batchTexts?.length || 1;
        node2._batchIndex = ((node2._batchIndex || 0) + 1) % total;
        node2._viewAll = false;
        syncDisplayWidgetText(node2);
        return true;
      }
      if (isInside(this._rects.toggle)) {
        node2._viewAll = !node2._viewAll;
        syncDisplayWidgetText(node2);
        return true;
      }
      if (isInside(this._rects.copy)) {
        const tw = node2.widgets?.find((w) => w.name === "display_text");
        const textToCopy = tw?.value || "";
        if (navigator.clipboard && textToCopy) {
          navigator.clipboard.writeText(textToCopy);
          this._feedbackText = "Copiato!";
          node2.setDirtyCanvas(true);
          setTimeout(() => {
            this._feedbackText = null;
            node2.setDirtyCanvas(true);
          }, 1800);
        }
        return true;
      }
      if (isInside(this._rects.copyAll)) {
        if (node2._batchTexts && node2._batchTexts.length > 0 && navigator.clipboard) {
          const allText = node2._batchTexts.map((t, idx) => `=== PROMPT #${idx + 1} ===
${t}`).join("\n\n");
          navigator.clipboard.writeText(allText);
          this._feedbackAllText = "Copiati!";
          node2.setDirtyCanvas(true);
          setTimeout(() => {
            this._feedbackAllText = null;
            node2.setDirtyCanvas(true);
          }, 1800);
        }
        return true;
      }
      return false;
    }
  };
  return widget;
}
function setupShowPromptNode(nodeType, nodeData, app11) {
  ensureStreamListeners();
  const showPromptTargetNames = [
    "StoiqoShowPromptNode",
    "[STOIQO] Show Prompt"
  ];
  if (showPromptTargetNames.includes(nodeData.name)) {
    let configureShowPromptNode = function(node) {
      if (!node) return;
      if (node.bgcolor === "#0e1218" || node.bgcolor === "#0b1411") delete node.bgcolor;
      if (node.color === "#18202c" || node.color === "#14251f") delete node.color;
      if (node.size) {
        if (node.size[0] < SHOW_MIN_WIDTH) node.size[0] = SHOW_MIN_WIDTH;
        if (node.size[1] < SHOW_MIN_HEIGHT) node.size[1] = SHOW_MIN_HEIGHT;
      }
      node.widgets = node.widgets || [];
      let textWidget = node.widgets.find((w) => w.name === "display_text");
      if (!textWidget) {
        if (typeof ComfyWidgets !== "undefined" && ComfyWidgets["STRING"]) {
          textWidget = ComfyWidgets["STRING"](
            node,
            "display_text",
            ["STRING", { multiline: true }],
            app11
          ).widget;
        } else {
          textWidget = node.addWidget(
            "customtext",
            "display_text",
            "",
            function() {
            },
            { multiline: true }
          );
        }
      }
      if (textWidget) {
        textWidget.name = "display_text";
        textWidget.serialize = false;
        textWidget.options = textWidget.options || {};
        textWidget.options.serialize = false;
        const styleInput = (el) => {
          if (!el) return;
          el.readOnly = false;
          el.placeholder = "Waiting for generated prompt or input text...";
          el.style.boxSizing = "border-box";
          el.style.opacity = "0.95";
          el.style.fontSize = "12px";
          el.style.lineHeight = "1.5";
          el.style.fontFamily = "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace";
          el.style.resize = "vertical";
          el.oninput = (e) => {
            if (node._batchTexts && node._batchTexts.length > 0 && !node._viewAll) {
              node._batchTexts[node._batchIndex || 0] = e.target.value;
            }
            node.setDirtyCanvas(true);
          };
        };
        if (textWidget.inputEl) {
          styleInput(textWidget.inputEl);
        } else {
          let rawInputEl = null;
          Object.defineProperty(textWidget, "inputEl", {
            configurable: true,
            enumerable: true,
            get() {
              return rawInputEl;
            },
            set(val) {
              rawInputEl = val;
              styleInput(val);
            }
          });
        }
      }
      const legacyBtnIdx = node.widgets.findIndex((w) => w._isCopyButton || w.name === "\u{1F4CB} Copy Prompt to Clipboard");
      if (legacyBtnIdx !== -1) {
        node.widgets.splice(legacyBtnIdx, 1);
      }
      const existingViewers = node.widgets.filter((w) => w.name === "prompt_viewer_hud");
      for (const extra of existingViewers.slice(1)) {
        node.widgets.splice(node.widgets.indexOf(extra), 1);
      }
      let viewerWidget = existingViewers[0];
      if (!viewerWidget) {
        viewerWidget = createPromptViewerWidget(node);
        node.widgets.unshift(viewerWidget);
      } else {
        const curIdx = node.widgets.indexOf(viewerWidget);
        if (curIdx > 0) {
          node.widgets.splice(curIdx, 1);
          node.widgets.unshift(viewerWidget);
        }
      }
      if (typeof node.computeSize === "function") {
        const sz = node.computeSize();
        const w = Math.max(node.size ? node.size[0] : SHOW_MIN_WIDTH, SHOW_MIN_WIDTH, Math.ceil(sz[0] || 0));
        const h = Math.max(node.size ? node.size[1] : SHOW_MIN_HEIGHT, SHOW_MIN_HEIGHT, Math.ceil(sz[1] || 0));
        if (typeof node.setSize === "function") {
          node.setSize([w, h]);
        } else {
          node.size = [w, h];
        }
      }
      node.setDirtyCanvas(true, true);
    };
    const SHOW_MIN_WIDTH = 460;
    const SHOW_MIN_HEIGHT = 230;
    const origShowCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function() {
      if (origShowCreated) origShowCreated.apply(this, arguments);
      this._batchTexts = [];
      this._batchIndex = 0;
      this._viewAll = false;
      configureShowPromptNode(this);
    };
    const origShowConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function() {
      if (origShowConfigure) origShowConfigure.apply(this, arguments);
      const tw = this.widgets?.find((w) => w.name === "display_text");
      if (tw && tw.value && (!this._batchTexts || this._batchTexts.length === 0)) {
        this._batchTexts = [tw.value];
        this._batchIndex = 0;
        this._viewAll = false;
      }
      configureShowPromptNode(this);
    };
    const origShowExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function(message) {
      if (origShowExecuted) origShowExecuted.apply(this, arguments);
      if (message && message.text) {
        let texts = [];
        if (Array.isArray(message.text)) {
          texts = message.text.map((t) => String(t || ""));
        } else {
          texts = [String(message.text || "")];
        }
        this._batchTexts = texts;
        this._batchIndex = 0;
        this._viewAll = false;
        syncDisplayWidgetText(this);
      }
    };
  }
}

// src_js/nodes/modelLoaderNode.js
import { app as app2 } from "../../../scripts/app.js";
import { api as api2 } from "../../../scripts/api.js";

// src_js/utils/searchablePickerModal.js
var modalBackdrop = null;
var currentItems = [];
var filteredItems = [];
var highlightedIndex = 0;
var activeFolderFilter = "ALL";
var onPickCallback = null;
var onRefreshCallback = null;
var activeItemIcon = "\u{1F4E6}";
var currentSelectedValue = "";
function ensureStyles() {
  if (document.getElementById("stoiqo-searchable-picker-styles")) return;
  const styleEl = document.createElement("style");
  styleEl.id = "stoiqo-searchable-picker-styles";
  styleEl.textContent = `
        .stoiqo-picker-backdrop {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(3, 5, 8, 0.80);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            z-index: 10005;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.18s cubic-bezier(0.16, 1, 0.3, 1);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #f1f5f9;
        }
        .stoiqo-picker-backdrop.open {
            opacity: 1;
            pointer-events: auto;
        }
        .stoiqo-picker-box {
            background: #090b10;
            border: 1px solid rgba(255, 255, 255, 0.11);
            border-radius: 12px;
            width: 700px;
            max-width: 94vw;
            height: 580px;
            max-height: 86vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 30px 90px rgba(0, 0, 0, 0.88), 0 0 1px 1px rgba(255, 255, 255, 0.06);
            overflow: hidden;
            transform: scale(0.96);
            transition: transform 0.18s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .stoiqo-picker-backdrop.open .stoiqo-picker-box {
            transform: scale(1);
        }
        .stoiqo-picker-header {
            padding: 14px 18px 12px;
            background: rgba(16, 20, 30, 0.75);
            border-bottom: 1px solid rgba(255, 255, 255, 0.07);
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .stoiqo-picker-topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .stoiqo-picker-title {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -0.2px;
        }
        .stoiqo-picker-count {
            font-size: 10px;
            font-weight: 700;
            padding: 2px 7px;
            border-radius: 4px;
            background: rgba(41, 151, 255, 0.15);
            border: 1px solid rgba(41, 151, 255, 0.38);
            color: #58b0ff;
        }
        .stoiqo-picker-top-actions {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .stoiqo-picker-btn-icon {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #94a3b8;
            font-size: 12.5px;
            cursor: pointer;
            padding: 5px 9px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            gap: 5px;
            transition: background 0.15s, color 0.15s;
        }
        .stoiqo-picker-btn-icon:hover {
            background: rgba(255, 255, 255, 0.12);
            color: #ffffff;
        }
        .stoiqo-picker-search-wrap {
            position: relative;
            display: flex;
            align-items: center;
        }
        .stoiqo-picker-search-icon {
            position: absolute;
            left: 12px;
            font-size: 14px;
            color: #64748b;
            pointer-events: none;
        }
        .stoiqo-picker-input {
            width: 100%;
            background: #11141e;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 8px;
            color: #ffffff;
            padding: 10px 36px 10px 36px;
            font-size: 13.5px;
            outline: none;
            transition: border-color 0.15s, background 0.15s;
            box-sizing: border-box;
        }
        .stoiqo-picker-input:focus {
            border-color: #2997ff;
            background: #141824;
            box-shadow: 0 0 0 1px #2997ff;
        }
        .stoiqo-picker-clear-btn {
            position: absolute;
            right: 10px;
            background: transparent;
            border: none;
            color: #64748b;
            font-size: 14px;
            cursor: pointer;
            padding: 4px;
            border-radius: 4px;
            display: none;
        }
        .stoiqo-picker-clear-btn:hover {
            color: #ffffff;
        }
        .stoiqo-picker-chips-bar {
            display: flex;
            gap: 6px;
            overflow-x: auto;
            padding: 2px 0 2px;
            max-width: 100%;
            scrollbar-width: none;
        }
        .stoiqo-picker-chips-bar::-webkit-scrollbar {
            display: none;
        }
        .stoiqo-picker-chip {
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #94a3b8;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.15s;
        }
        .stoiqo-picker-chip:hover {
            background: rgba(255, 255, 255, 0.10);
            color: #f1f5f9;
        }
        .stoiqo-picker-chip.active {
            background: rgba(41, 151, 255, 0.18);
            border-color: rgba(41, 151, 255, 0.50);
            color: #58b0ff;
        }
        .stoiqo-picker-list {
            flex: 1;
            overflow-y: auto;
            padding: 8px 10px;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        .stoiqo-picker-list::-webkit-scrollbar {
            width: 6px;
        }
        .stoiqo-picker-list::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.14);
            border-radius: 3px;
        }
        .stoiqo-picker-item {
            padding: 8px 12px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            cursor: pointer;
            background: transparent;
            border: 1px solid transparent;
            transition: background 0.1s, border-color 0.1s;
        }
        .stoiqo-picker-item:hover, .stoiqo-picker-item.highlighted {
            background: rgba(41, 151, 255, 0.14);
            border-color: rgba(41, 151, 255, 0.40);
        }
        .stoiqo-picker-item.active-selected {
            background: rgba(48, 209, 88, 0.10);
            border-color: rgba(48, 209, 88, 0.35);
        }
        .stoiqo-picker-item-left {
            display: flex;
            align-items: center;
            gap: 10px;
            overflow: hidden;
            flex: 1;
        }
        .stoiqo-picker-item-icon {
            font-size: 14px;
            flex-shrink: 0;
        }
        .stoiqo-picker-item-info {
            display: flex;
            flex-direction: column;
            overflow: hidden;
            gap: 2px;
        }
        .stoiqo-picker-item-name {
            font-size: 13px;
            font-weight: 600;
            color: #f1f5f9;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .stoiqo-picker-item-path {
            font-size: 10.5px;
            color: #64748b;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-family: 'JetBrains Mono', SFMono-Regular, Consolas, monospace;
        }
        .stoiqo-picker-item-right {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-shrink: 0;
        }
        .stoiqo-picker-item-ext {
            font-size: 9.5px;
            font-weight: 700;
            text-transform: uppercase;
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #94a3b8;
            font-family: 'JetBrains Mono', monospace;
        }
        .stoiqo-picker-item-active-tag {
            font-size: 10px;
            font-weight: 700;
            color: #30d158;
            background: rgba(48, 209, 88, 0.15);
            border: 1px solid rgba(48, 209, 88, 0.35);
            border-radius: 4px;
            padding: 1px 5px;
        }
        .stoiqo-picker-empty {
            padding: 40px 20px;
            text-align: center;
            color: #64748b;
            font-size: 13px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }
        .stoiqo-picker-footer {
            padding: 10px 18px;
            background: rgba(14, 18, 28, 0.85);
            border-top: 1px solid rgba(255, 255, 255, 0.07);
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 11.5px;
            color: #64748b;
        }
        .stoiqo-picker-kbd-hints {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .stoiqo-picker-kbd {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 4px;
            padding: 1px 5px;
            font-size: 10px;
            color: #cbd5e1;
            font-family: monospace;
        }
    `;
  document.head.appendChild(styleEl);
}
function parseItemMeta(rawPath) {
  const norm = String(rawPath || "").replace(/\\/g, "/");
  const parts = norm.split("/");
  const filename = parts[parts.length - 1];
  const folder = parts.length > 1 ? parts.slice(0, -1).join("/") : "";
  const dotIdx = filename.lastIndexOf(".");
  const baseName3 = dotIdx !== -1 ? filename.slice(0, dotIdx) : filename;
  const ext = dotIdx !== -1 ? filename.slice(dotIdx + 1) : "";
  return {
    raw: rawPath,
    norm,
    filename,
    baseName: baseName3,
    folder: folder || "Root",
    ext
  };
}
function buildPickerDOM() {
  modalBackdrop = document.createElement("div");
  modalBackdrop.className = "stoiqo-picker-backdrop";
  modalBackdrop.innerHTML = `
        <div class="stoiqo-picker-box">
            <div class="stoiqo-picker-header">
                <div class="stoiqo-picker-topbar">
                    <div class="stoiqo-picker-title">
                        <span id="stoiqo-picker-icon">\u{1F4E6}</span>
                        <span id="stoiqo-picker-heading">Seleziona File</span>
                        <span class="stoiqo-picker-count" id="stoiqo-picker-total">0</span>
                    </div>
                    <div class="stoiqo-picker-top-actions">
                        <button class="stoiqo-picker-btn-icon" id="stoiqo-picker-refresh-btn" title="Ricarica lista da disco">
                            <span>\u{1F504}</span> Ricarica
                        </button>
                        <button class="stoiqo-picker-btn-icon" id="stoiqo-picker-close-btn" style="padding: 4px 7px;">
                            \u2715
                        </button>
                    </div>
                </div>

                <div class="stoiqo-picker-search-wrap">
                    <span class="stoiqo-picker-search-icon">\u{1F50D}</span>
                    <input class="stoiqo-picker-input" id="stoiqo-picker-search-input" placeholder="Cerca file o cartella... (es. sdxl, flux, anime, v2)" autocomplete="off" spellcheck="false" />
                    <button class="stoiqo-picker-clear-btn" id="stoiqo-picker-clear-search">\u2715</button>
                </div>

                <div class="stoiqo-picker-chips-bar" id="stoiqo-picker-chips"></div>
            </div>

            <div class="stoiqo-picker-list" id="stoiqo-picker-items-list"></div>

            <div class="stoiqo-picker-footer">
                <div class="stoiqo-picker-kbd-hints">
                    <span><span class="stoiqo-picker-kbd">\u2191</span> <span class="stoiqo-picker-kbd">\u2193</span> Naviga</span>
                    <span><span class="stoiqo-picker-kbd">\u21B5</span> Seleziona</span>
                    <span><span class="stoiqo-picker-kbd">Esc</span> Chiudi</span>
                </div>
                <div id="stoiqo-picker-status-info">STOIQO Universal Picker</div>
            </div>
        </div>
    `;
  document.body.appendChild(modalBackdrop);
  const searchInput = modalBackdrop.querySelector("#stoiqo-picker-search-input");
  const clearBtn = modalBackdrop.querySelector("#stoiqo-picker-clear-search");
  const closeBtn = modalBackdrop.querySelector("#stoiqo-picker-close-btn");
  const refreshBtn = modalBackdrop.querySelector("#stoiqo-picker-refresh-btn");
  modalBackdrop.addEventListener("click", (e) => {
    if (e.target === modalBackdrop) closeSearchablePicker();
  });
  closeBtn.addEventListener("click", closeSearchablePicker);
  clearBtn.addEventListener("click", () => {
    searchInput.value = "";
    clearBtn.style.display = "none";
    filterList();
    searchInput.focus();
  });
  searchInput.addEventListener("input", () => {
    clearBtn.style.display = searchInput.value ? "block" : "none";
    filterList();
  });
  refreshBtn.addEventListener("click", async () => {
    if (onRefreshCallback) {
      refreshBtn.disabled = true;
      refreshBtn.innerHTML = `<span>\u23F3</span> Scansione...`;
      try {
        const newList = await onRefreshCallback();
        if (Array.isArray(newList)) {
          currentItems = newList;
          renderFolderChips();
          filterList();
        }
      } catch (err) {
        console.error("[STOIQO Picker] Refresh error:", err);
      } finally {
        refreshBtn.disabled = false;
        refreshBtn.innerHTML = `<span>\u{1F504}</span> Ricarica`;
      }
    }
  });
  modalBackdrop.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeSearchablePicker();
      e.preventDefault();
      return;
    }
    if (e.key === "ArrowDown") {
      if (filteredItems.length > 0) {
        highlightedIndex = (highlightedIndex + 1) % filteredItems.length;
        updateHighlightedRow();
      }
      e.preventDefault();
      return;
    }
    if (e.key === "ArrowUp") {
      if (filteredItems.length > 0) {
        highlightedIndex = (highlightedIndex - 1 + filteredItems.length) % filteredItems.length;
        updateHighlightedRow();
      }
      e.preventDefault();
      return;
    }
    if (e.key === "Enter") {
      if (filteredItems.length > 0 && filteredItems[highlightedIndex]) {
        const chosen = filteredItems[highlightedIndex].raw;
        if (onPickCallback) onPickCallback(chosen);
        closeSearchablePicker();
      }
      e.preventDefault();
      return;
    }
  });
}
function renderFolderChips() {
  const chipsBar = modalBackdrop.querySelector("#stoiqo-picker-chips");
  chipsBar.innerHTML = "";
  const folderCounts = /* @__PURE__ */ new Map();
  let totalCount = currentItems.length;
  currentItems.forEach((it) => {
    const meta = parseItemMeta(it);
    folderCounts.set(meta.folder, (folderCounts.get(meta.folder) || 0) + 1);
  });
  if (folderCounts.size <= 1) {
    chipsBar.style.display = "none";
    return;
  }
  chipsBar.style.display = "flex";
  const allChip = document.createElement("button");
  allChip.className = `stoiqo-picker-chip ${activeFolderFilter === "ALL" ? "active" : ""}`;
  allChip.textContent = `Tutti (${totalCount})`;
  allChip.addEventListener("click", () => {
    activeFolderFilter = "ALL";
    renderFolderChips();
    filterList();
  });
  chipsBar.appendChild(allChip);
  const sortedFolders = [...folderCounts.keys()].sort((a, b) => {
    if (a === "Root") return -1;
    if (b === "Root") return 1;
    return a.localeCompare(b);
  });
  sortedFolders.forEach((folder) => {
    const count = folderCounts.get(folder);
    const chip = document.createElement("button");
    chip.className = `stoiqo-picker-chip ${activeFolderFilter === folder ? "active" : ""}`;
    chip.textContent = `${folder === "Root" ? "\u{1F4C1} Root" : folder} (${count})`;
    chip.addEventListener("click", () => {
      activeFolderFilter = folder;
      renderFolderChips();
      filterList();
    });
    chipsBar.appendChild(chip);
  });
}
function filterList() {
  const searchInput = modalBackdrop.querySelector("#stoiqo-picker-search-input");
  const query = (searchInput.value || "").trim().toLowerCase();
  const queryTokens = query.split(/\s+/).filter(Boolean);
  filteredItems = currentItems.map((it) => parseItemMeta(it)).filter((meta) => {
    if (activeFolderFilter !== "ALL" && meta.folder !== activeFolderFilter) {
      return false;
    }
    if (queryTokens.length > 0) {
      const targetText = `${meta.norm} ${meta.baseName}`.toLowerCase();
      return queryTokens.every((token) => targetText.includes(token));
    }
    return true;
  });
  highlightedIndex = 0;
  renderList();
}
function renderList() {
  const listEl = modalBackdrop.querySelector("#stoiqo-picker-items-list");
  const countEl = modalBackdrop.querySelector("#stoiqo-picker-total");
  listEl.innerHTML = "";
  countEl.textContent = `${filteredItems.length} di ${currentItems.length}`;
  if (filteredItems.length === 0) {
    listEl.innerHTML = `
            <div class="stoiqo-picker-empty">
                <span style="font-size: 28px;">\u{1F50D}</span>
                <span style="font-weight: 600;">Nessun elemento corrispondente alla ricerca.</span>
                <span style="font-size: 11px; opacity: 0.7;">Prova con una parola chiave diversa o premi Ricarica.</span>
            </div>
        `;
    return;
  }
  const renderLimit = Math.min(filteredItems.length, 200);
  for (let i = 0; i < renderLimit; i++) {
    const meta = filteredItems[i];
    const isCurrent = Boolean(
      currentSelectedValue && (meta.raw === currentSelectedValue || meta.norm === currentSelectedValue || meta.filename === currentSelectedValue)
    );
    const row = document.createElement("div");
    row.className = `stoiqo-picker-item ${i === highlightedIndex ? "highlighted" : ""} ${isCurrent ? "active-selected" : ""}`;
    row.dataset.index = i;
    row.innerHTML = `
            <div class="stoiqo-picker-item-left">
                <span class="stoiqo-picker-item-icon">${activeItemIcon}</span>
                <div class="stoiqo-picker-item-info">
                    <span class="stoiqo-picker-item-name" title="${meta.filename}">${meta.baseName}</span>
                    <span class="stoiqo-picker-item-path" title="${meta.norm}">${meta.folder !== "Root" ? `\u{1F4C1} ${meta.folder}/` : "Root"}</span>
                </div>
            </div>
            <div class="stoiqo-picker-item-right">
                ${isCurrent ? `<span class="stoiqo-picker-item-active-tag">ATTIVO</span>` : ""}
                ${meta.ext ? `<span class="stoiqo-picker-item-ext">.${meta.ext}</span>` : ""}
            </div>
        `;
    row.addEventListener("mouseenter", () => {
      highlightedIndex = i;
      updateHighlightedRow(false);
    });
    row.addEventListener("click", () => {
      if (onPickCallback) onPickCallback(meta.raw);
      closeSearchablePicker();
    });
    listEl.appendChild(row);
  }
  if (filteredItems.length > renderLimit) {
    const moreNotice = document.createElement("div");
    moreNotice.style.padding = "10px 14px";
    moreNotice.style.fontSize = "11.5px";
    moreNotice.style.color = "#64748b";
    moreNotice.style.textAlign = "center";
    moreNotice.textContent = `... altri ${filteredItems.length - renderLimit} file disponibili. Digita per affinare la ricerca.`;
    listEl.appendChild(moreNotice);
  }
}
function updateHighlightedRow(scrollIntoView = true) {
  const listEl = modalBackdrop.querySelector("#stoiqo-picker-items-list");
  const rows = listEl.querySelectorAll(".stoiqo-picker-item");
  rows.forEach((r, idx) => {
    const isCurrent = idx === highlightedIndex;
    r.classList.toggle("highlighted", isCurrent);
    if (isCurrent && scrollIntoView) {
      r.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  });
}
function openSearchablePicker(options = {}) {
  ensureStyles();
  if (!modalBackdrop) {
    buildPickerDOM();
  }
  const {
    title = "Seleziona File",
    icon = "\u{1F4E6}",
    items = [],
    current = "",
    onPick = null,
    onRefresh = null
  } = options;
  activeItemIcon = icon;
  currentItems = Array.isArray(items) ? [...items] : [];
  currentSelectedValue = current || "";
  activeFolderFilter = "ALL";
  onPickCallback = onPick;
  onRefreshCallback = onRefresh;
  modalBackdrop.querySelector("#stoiqo-picker-heading").textContent = title;
  modalBackdrop.querySelector("#stoiqo-picker-icon").textContent = icon;
  const searchInput = modalBackdrop.querySelector("#stoiqo-picker-search-input");
  searchInput.value = "";
  modalBackdrop.querySelector("#stoiqo-picker-clear-search").style.display = "none";
  renderFolderChips();
  filterList();
  modalBackdrop.classList.add("open");
  setTimeout(() => {
    searchInput.focus();
    searchInput.select();
  }, 40);
}
function closeSearchablePicker() {
  if (modalBackdrop) {
    modalBackdrop.classList.remove("open");
  }
}

// src_js/nodes/modelLoaderNode.js
var MODEL_NODE_NAMES = [
  "StoiqoUniversalModelLoaderNode",
  "[STOIQO] Universal Model Loader (All-in-One)"
];
var LEGACY_WIDGET_NAMES = [
  "model_name",
  "clip_type",
  "precision",
  "attention",
  "flow_shift_preset",
  "custom_shift",
  "custom_path"
];
var MIN_WIDTH = 440;
var PAD = 6;
var HEAD_H = 24;
var ROW_H = 28;
var BTN_H = 30;
var PRECISIONS = ["default", "fp8_e4m3fn", "fp8_e4m3fn_fast", "fp8_e5m2", "4bit - NF4", "8bit", "fp16", "bf16"];
var ATTENTIONS = ["sdpa", "flash_attention_2", "eager"];
var CLIP_TYPES = ["auto", "krea2", "flux", "wan", "sd3", "ace", "qwen_image", "lumina2", "mochi", "ltxv", "minimax", "stable_diffusion"];
var DEFAULT_PRESET = "None (Standard / SD1.5 / SDXL / Krea 2)";
var _presets = [DEFAULT_PRESET];
var _modelListCache = null;
async function fetchModelList(force = false) {
  if (_modelListCache && !force) return _modelListCache;
  try {
    const resp = await api2.fetchApi("/stoiqo/models");
    const data = await resp.json();
    if (Array.isArray(data.presets) && data.presets.length) _presets = data.presets;
    _modelListCache = Array.isArray(data.models) ? data.models : [];
  } catch (err) {
    console.warn("[STOIQO Model Stack] Unable to load models list:", err);
    _modelListCache = [];
  }
  return _modelListCache;
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
  const parts = String(path).split(/[\\\/]/);
  const file = parts[parts.length - 1] || "";
  return file.replace(/\.(safetensors|ckpt|pt|pth|bin|gguf)$/i, "");
}
function fitText(ctx, text, maxW) {
  if (ctx.measureText(text).width <= maxW) return text;
  let t = text;
  while (t.length > 1 && ctx.measureText(t + "\u2026").width > maxW) {
    t = t.slice(0, -1);
  }
  return t + "\u2026";
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
    custom_shift: Number.isFinite(sh) ? sh : 3,
    custom_path: String(src.custom_path || "")
  };
}
var ModelStackWidget = class {
  constructor(node, storeWidget) {
    this.type = "custom";
    this.name = "_stoiqo_model_stack";
    this.node = node;
    this.store = storeWidget;
    this.serialize = false;
    this.options = { serialize: false };
    this.models = [];
    this.hits = [];
    this.lastClick = 0;
  }
  // Nessun valore proprio; tutto vive nel widget storage JSON.
  get value() {
    return "";
  }
  set value(_v) {
  }
  // ── Persistence ───────────────────────────────────────────────────────────
  loadFromStore() {
    let parsed = [];
    try {
      const raw = this.store ? this.store.value : "[]";
      const data = JSON.parse(raw || "[]");
      if (Array.isArray(data)) parsed = data;
    } catch (e) {
      parsed = [];
    }
    this.models = parsed.filter((m) => m && typeof m.name === "string" && m.name).map((m) => newModel(m.name, m));
    this.enforceSingleActive();
  }
  // Una sola uscita: un solo modello attivo alla volta.
  enforceSingleActive(prefer = null) {
    let keep = prefer && prefer.enabled ? prefer : this.models.find((m) => m.enabled);
    this.models.forEach((m) => {
      m.enabled = m === keep;
    });
  }
  sync() {
    if (this.store) {
      this.store.value = JSON.stringify(this.models.map((m) => ({ ...m })));
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
    const x0 = 10;
    const w = width - 20;
    let y = posY + PAD;
    ctx.save();
    ctx.textBaseline = "middle";
    const active = this.models.find((m) => m.enabled);
    ctx.font = "bold 11px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
    ctx.textAlign = "left";
    ctx.fillStyle = "#2997ff";
    ctx.fillText(`Model Stack \xB7 ${this.models.length} models \xB7 active: ${active ? baseName(active.name) : "none"}`.slice(0, 70), x0 + 2, y + HEAD_H / 2);
    y += HEAD_H;
    if (this.models.length === 0) {
      ctx.font = "italic 11px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
      ctx.fillStyle = "#64748b";
      ctx.textAlign = "center";
      ctx.fillText('No models \u2014 click "+ Add Model to Stack"', x0 + w / 2, y + ROW_H / 2);
      y += ROW_H;
    } else {
      this.models.forEach((model, idx) => {
        const rY = y + 2;
        const rH = ROW_H - 4;
        const on = model.enabled;
        ctx.fillStyle = on ? "rgba(41, 151, 255, 0.08)" : "rgba(255,255,255,0.03)";
        ctx.strokeStyle = on ? "rgba(41, 151, 255, 0.35)" : "rgba(255,255,255,0.08)";
        ctx.lineWidth = 1;
        roundRect(ctx, x0, rY, w, rH, 5);
        ctx.fill();
        ctx.stroke();
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
          x: tX - 2,
          y: rY,
          w: tW + 4,
          h: rH,
          action: () => {
            model.enabled = !model.enabled;
            this.enforceSingleActive(model);
            this.sync();
          }
        });
        const xW = 18;
        const xX = x0 + w - xW - 4;
        const xY = rY + (rH - xW) / 2;
        const gX = xX - xW - 3;
        ctx.fillStyle = "rgba(255,255,255,0.08)";
        roundRect(ctx, gX, xY, xW, xW, 3);
        ctx.fill();
        ctx.fillStyle = "#cbd5e1";
        ctx.font = "12px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("\u2699", gX + xW / 2, xY + xW / 2 + 0.5);
        this.hits.push({ x: gX, y: xY, w: xW, h: xW, action: (ev) => this.showAdvancedMenu(ev, model) });
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
          x: pX,
          y: xY,
          w: pW,
          h: xW,
          action: (ev) => this.pickFrom(ev, "Precisione", PRECISIONS, model.precision, (v) => {
            model.precision = v;
            this.sync();
          })
        });
        ctx.fillStyle = "rgba(239, 68, 68, 0.12)";
        ctx.strokeStyle = "rgba(239, 68, 68, 0.35)";
        ctx.lineWidth = 1;
        roundRect(ctx, xX, xY, xW, xW, 3);
        ctx.fill();
        ctx.stroke();
        ctx.fillStyle = "#f87171";
        ctx.font = "bold 11px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("\u2715", xX + xW / 2, xY + xW / 2);
        this.hits.push({
          x: xX,
          y: xY,
          w: xW,
          h: xW,
          action: () => {
            this.models.splice(idx, 1);
            this.sync();
          }
        });
        const nX = tX + tW + 8;
        const nW = pX - nX - 8;
        ctx.font = "12px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
        ctx.textAlign = "left";
        ctx.fillStyle = on ? "#e2e8f0" : "#64748b";
        const disp = baseName(model.name || "(select model)");
        ctx.fillText(fitText(ctx, disp, nW), nX, rY + rH / 2 + 0.5);
        this.hits.push({
          x: nX,
          y: rY,
          w: nW,
          h: rH,
          action: (ev) => this.pickModel(ev, model)
        });
        y += ROW_H;
      });
    }
    y += 6;
    ctx.fillStyle = "rgba(41, 151, 255, 0.12)";
    ctx.strokeStyle = "rgba(41, 151, 255, 0.5)";
    ctx.lineWidth = 1;
    roundRect(ctx, x0, y, w, BTN_H - 4, 6);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#2997ff";
    ctx.font = "bold 12px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("+ Add Model to Stack", x0 + w / 2, y + (BTN_H - 4) / 2 + 0.5);
    this.hits.push({
      x: x0,
      y,
      w,
      h: BTN_H - 4,
      action: (ev) => this.addModel(ev)
    });
    ctx.restore();
  }
  // ── Actions ───────────────────────────────────────────────────────────────
  async addModel(ev) {
    await this.pickModel(ev, null);
  }
  async pickModel(ev, targetModel) {
    const list = await fetchModelList(false);
    const LG = window.LiteGraph;
    if (!list || !list.length) {
      if (LG && LG.ContextMenu) {
        new LG.ContextMenu(
          [{ content: "Nessun modello trovato nelle cartelle di ComfyUI", disabled: true }],
          { event: ev }
        );
      }
      return;
    }
    openSearchablePicker({
      title: "Scegli Modello (Checkpoints / GGUF / Diffusion)",
      icon: "\u{1F4E6}",
      items: list,
      current: targetModel ? targetModel.name : "",
      onRefresh: async () => {
        return await fetchModelList(true);
      },
      onPick: (chosen) => {
        if (!chosen) return;
        if (targetModel) {
          targetModel.name = chosen;
        } else {
          const nm = newModel(chosen);
          this.models.push(nm);
          this.enforceSingleActive(nm);
        }
        this.sync();
      }
    });
  }
  pickFrom(ev, title, options, current, onChoose) {
    const LG = window.LiteGraph;
    if (!LG || !LG.ContextMenu) return;
    new LG.ContextMenu(
      options.map((o) => ({ content: o === current ? `\u2713 ${o}` : o, value: o })),
      { event: ev, title, callback: (c) => {
        if (c && c.value !== void 0) onChoose(c.value);
      } }
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
          options.map((o) => ({ content: o === model[key] ? `\u2713 ${o}` : o, value: o })),
          { event: e, parentMenu: menu, callback: (c) => {
            if (c && c.value !== void 0) {
              model[key] = c.value;
              this.sync();
            }
          } }
        );
        return true;
      }
    });
    const items = [
      sub("Attention", ATTENTIONS, "attention"),
      sub("Clip type", CLIP_TYPES, "clip_type"),
      sub("Flow shift", _presets, "flow_shift_preset"),
      {
        content: `Custom shift: ${model.custom_shift.toFixed(2)}`,
        callback: (_v, _o, e) => app2.canvas.prompt("Custom shift", model.custom_shift, (val) => {
          const n = parseFloat(val);
          if (Number.isFinite(n)) {
            model.custom_shift = Math.max(0, Math.min(100, n));
            this.sync();
          }
        }, e)
      },
      {
        content: `Custom Path / API: ${model.custom_path || "\u2014"}`,
        callback: (_v, _o, e) => app2.canvas.prompt("Folder path or API endpoint", model.custom_path, (val) => {
          model.custom_path = String(val || "").trim();
          this.sync();
        }, e)
      }
    ];
    new LG.ContextMenu(items, { event: ev, title: baseName(model.name) });
  }
  // ── Mouse handler (API LiteGraph corretta) ────────────────────────────────
  mouse(event, pos, node) {
    if (!event || event.type !== "pointerdown" && event.type !== "mousedown") return false;
    if (!pos) return false;
    const now = performance.now();
    if (now - this.lastClick < 150) return true;
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
};
function hideWidget(w) {
  if (!w) return;
  w.hidden = true;
  w.computeSize = () => [0, -4];
  w.draw = () => {
  };
  if (w.inputEl) {
    w.inputEl.hidden = true;
    w.inputEl.style.display = "none";
  }
}
function setupModelLoaderNodeUI(node) {
  if (!node) return;
  if (node.size && node.size[0] < MIN_WIDTH) node.size[0] = MIN_WIDTH;
  const STACK_NAME = "_stoiqo_model_stack";
  if (node.widgets) {
    const dups = node.widgets.filter((w) => w.name === STACK_NAME);
    for (const extra of dups.slice(1)) {
      node.widgets.splice(node.widgets.indexOf(extra), 1);
    }
  }
  let stackWidget = node.widgets ? node.widgets.find((w) => w.name === STACK_NAME) : null;
  if (stackWidget && !stackWidget.loadFromStore) stackWidget = null;
  if (!stackWidget) {
    const store = node.widgets ? node.widgets.find((w) => w.name === "model_stack") : null;
    if (store) {
      hideWidget(store);
    }
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
function setupModelLoaderNode(nodeType, nodeData, appInstance) {
  if (!MODEL_NODE_NAMES.includes(nodeData.name)) return;
  const origCreated = nodeType.prototype.onNodeCreated;
  nodeType.prototype.onNodeCreated = function() {
    if (origCreated) origCreated.apply(this, arguments);
    setupModelLoaderNodeUI(this);
  };
  const origConfigure = nodeType.prototype.onConfigure;
  nodeType.prototype.onConfigure = function() {
    if (origConfigure) origConfigure.apply(this, arguments);
    setupModelLoaderNodeUI(this);
  };
}

// src_js/nodes/imageCompareNode.js
import { app as app4 } from "../../../scripts/app.js";
import { api as api4 } from "../../../scripts/api.js";
import { ComfyWidgets as ComfyWidgets3 } from "../../../scripts/widgets.js";

// src_js/utils/core.js
import { app as app3 } from "../../scripts/app.js";
import { api as api3 } from "../../scripts/api.js";
import { ComfyWidgets as ComfyWidgets2 } from "../../scripts/widgets.js";
var currentDownloadProgress = null;
var downloadClearTimer = null;
var comfyApi = api3 || typeof app3 !== "undefined" && app3.api;
if (comfyApi && comfyApi.addEventListener) {
  comfyApi.addEventListener("stoiqo_download_progress", (event) => {
    const data = event.detail;
    if (!data) return;
    currentDownloadProgress = data;
    if (data.status === "complete") {
      if (downloadClearTimer) clearTimeout(downloadClearTimer);
      downloadClearTimer = setTimeout(() => {
        currentDownloadProgress = null;
        if (app3 && app3.graph) app3.graph.setDirtyCanvas(true, true);
      }, 6e3);
    }
    if (app3 && app3.graph) app3.graph.setDirtyCanvas(true, true);
  });
}
var StoiqoSectionDividerWidget = class {
  constructor(sectionNum, sectionTitle, accentColor) {
    this.type = "custom";
    this.name = `_stoiqo_divider_${sectionNum}`;
    this.value = {};
    this.serialize = false;
    this.options = { serialize: false };
    this.sectionNum = sectionNum;
    this.sectionTitle = sectionTitle;
    this.accentColor = accentColor;
    this.isStoiqoDivider = true;
    this.height = 30;
  }
  serializeValue() {
    return void 0;
  }
  computeSize(width) {
    return [width, this.height];
  }
  draw(ctx, node, width, posY, height) {
    const nodeWidth = node && node.size ? node.size[0] : width;
    const accent = this.accentColor;
    const bannerY = posY + 5;
    ctx.save();
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
    const label = `\xA7 ${this.sectionNum}. ${this.sectionTitle}`;
    ctx.font = "bold 9px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif";
    const textMetrics = ctx.measureText(label);
    const badgeX = 14;
    const badgeY = bannerY + 2;
    const badgeW = Math.ceil(textMetrics.width) + 18;
    const badgeH = 16;
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
    ctx.fillStyle = accent;
    ctx.beginPath();
    ctx.arc(badgeX + 7, badgeY + badgeH / 2, 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#f8fafc";
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText(label, badgeX + 13, badgeY + badgeH / 2 + 0.5);
    if (this.sectionNum === "1" && currentDownloadProgress) {
      const dp = currentDownloadProgress;
      const isDone = dp.status === "complete" || dp.percent >= 100;
      const dlLabel = isDone ? "\u2713 Model Ready" : `\u2B07 DL ${dp.percent}% (${dp.downloaded_str || ""})`;
      const dlColor = isDone ? "#30d158" : "#2997ff";
      ctx.font = "bold 9px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif";
      const dlMetrics = ctx.measureText(dlLabel);
      const dlBadgeW = Math.ceil(dlMetrics.width) + 16;
      const dlBadgeX = nodeWidth - 14 - dlBadgeW;
      const dlBadgeY = badgeY;
      const dlBadgeH = badgeH;
      if (dlBadgeX > badgeX + badgeW + 8) {
        ctx.fillStyle = "rgba(15, 23, 42, 0.9)";
        if (ctx.roundRect) {
          ctx.beginPath();
          ctx.roundRect(dlBadgeX, dlBadgeY, dlBadgeW, dlBadgeH, 3);
          ctx.fill();
        } else {
          ctx.fillRect(dlBadgeX, dlBadgeY, dlBadgeW, dlBadgeH);
        }
        if (!isDone && dp.percent > 0) {
          const progressW = Math.max(0, Math.min(dlBadgeW - 2, (dlBadgeW - 2) * dp.percent / 100));
          ctx.fillStyle = "rgba(56, 189, 248, 0.28)";
          if (ctx.roundRect) {
            ctx.beginPath();
            ctx.roundRect(dlBadgeX + 1, dlBadgeY + 1, progressW, dlBadgeH - 2, 2);
            ctx.fill();
          } else {
            ctx.fillRect(dlBadgeX + 1, dlBadgeY + 1, progressW, dlBadgeH - 2);
          }
        }
        ctx.strokeStyle = dlColor + "bb";
        ctx.lineWidth = 1;
        if (ctx.roundRect) {
          ctx.beginPath();
          ctx.roundRect(dlBadgeX, dlBadgeY, dlBadgeW, dlBadgeH, 3);
          ctx.stroke();
        } else {
          ctx.strokeRect(dlBadgeX, dlBadgeY, dlBadgeW, dlBadgeH);
        }
        ctx.fillStyle = dlColor;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(dlLabel, dlBadgeX + dlBadgeW / 2, dlBadgeY + dlBadgeH / 2 + 0.5);
      }
    }
    ctx.restore();
  }
};

// src_js/nodes/imageCompareNode.js
function setupImageCompareNode(nodeType, nodeData, app11) {
  const compareTargetNames = [
    "StoiqoImageCompareNode",
    "[STOIQO] Visual Compare Slider & Zoom"
  ];
  if (compareTargetNames.includes(nodeData.name)) {
    let imageDataToUrl = function(data) {
      if (!data || !data.filename) return "";
      const params = new URLSearchParams();
      params.set("filename", data.filename);
      params.set("type", data.type || "temp");
      if (data.subfolder) {
        params.set("subfolder", data.subfolder);
      }
      const fmt = app11.getPreviewFormatParam ? app11.getPreviewFormatParam() : "";
      if (fmt) {
        const clean = fmt.replace(/^&/, "");
        const parts = clean.split("=");
        if (parts.length === 2) params.set(parts[0], parts[1]);
      }
      params.set("t", Date.now().toString());
      return api4.apiURL(`/view?${params.toString()}`);
    }, setupImageCompareNodeUI = function(node) {
      if (!node) return;
      node.hideOutputImages = true;
      node.imgs = null;
      node.images = null;
      if (!node.size || node.size[0] < MIN_WIDTH3) node.size = [MIN_WIDTH3, MIN_HEIGHT];
      let cmpWidget = node.widgets ? node.widgets.find((w) => w instanceof StoiqoCompareCanvasWidget) : null;
      if (!cmpWidget) {
        cmpWidget = new StoiqoCompareCanvasWidget(node);
        node.addCustomWidget(cmpWidget);
        node.cmpWidget = cmpWidget;
      }
      const modeWidget = node.widgets?.find((w) => w.name === "initial_mode");
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
      node.onMouseWheel = function(e, localPos, graphCanvas) {
        if (cmpWidget && cmpWidget.handleWheel(e, localPos)) {
          if (e && e.preventDefault) e.preventDefault();
          if (e && e.stopPropagation) e.stopPropagation();
          return true;
        }
        return false;
      };
      if (app11.canvas && app11.canvas.canvas && !node._stoiqoWheelAttached) {
        node._stoiqoWheelAttached = true;
        node._stoiqoWheelHandler = (e) => {
          if (!node.cmpWidget || !app11.canvas) return;
          const canvasPos = app11.canvas.convertEventToCanvasOffset ? app11.canvas.convertEventToCanvasOffset(e) : [e.canvasX, e.canvasY];
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
        app11.canvas.canvas.addEventListener("wheel", node._stoiqoWheelHandler, { capture: true, passive: false });
      }
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
    };
    const MIN_WIDTH3 = 520;
    const MIN_HEIGHT = 560;
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
        this.zoom = 1;
        this.panX = 0;
        this.panY = 0;
        this.mode = "hover_slide";
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
        return void 0;
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
        const listA = dataList.filter((d) => d.side === "A" || d.name && d.name.startsWith("A"));
        const listB = dataList.filter((d) => d.side === "B" || d.name && d.name.startsWith("B"));
        const diffItem = dataList.find((d) => d.side === "DIFF" || d.name === "HEATMAP");
        this.diffData = diffItem || null;
        this.availableA = listA.length > 0 ? listA : [dataList[0]];
        this.availableB = listB.length > 0 ? listB : dataList.length > 1 ? [dataList[1]] : [dataList[0]];
        if (!this.selectedA || !this.availableA.some((x) => x.filename === this.selectedA.filename)) {
          this.selectedA = this.availableA[0];
        }
        if (!this.selectedB || !this.availableB.some((x) => x.filename === this.selectedB.filename)) {
          this.selectedB = this.availableB[0];
        }
        this.loadSelectedImages();
        this.resetView();
      }
      loadSelectedImages() {
        if (this.imgA) {
          this.imgA.onload = null;
          this.imgA.onerror = null;
          this.imgA.src = "";
          this.imgA = null;
        }
        if (this.imgB) {
          this.imgB.onload = null;
          this.imgB.onerror = null;
          this.imgB.src = "";
          this.imgB = null;
        }
        if (this.imgDiff) {
          this.imgDiff.onload = null;
          this.imgDiff.onerror = null;
          this.imgDiff.src = "";
          this.imgDiff = null;
        }
        this.loadError = null;
        if (!this.selectedA || !this.selectedB) return;
        const urlA = imageDataToUrl(this.selectedA);
        const urlB = imageDataToUrl(this.selectedB);
        this.imgA = new Image();
        this.imgB = new Image();
        this.imgA.onload = () => {
          if (this.node) this.node.setDirtyCanvas(true, true);
        };
        this.imgB.onload = () => {
          if (this.node) this.node.setDirtyCanvas(true, true);
        };
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
          this.imgDiff.onload = () => {
            if (this.node) this.node.setDirtyCanvas(true, true);
          };
          this.imgDiff.src = imageDataToUrl(this.diffData);
        }
      }
      resetView() {
        this.zoom = 1;
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
          const canvas = app11.canvas;
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
        const nodeW = width || (node.size ? node.size[0] : MIN_WIDTH3);
        const nodeH = node && node.size ? node.size[1] : 560;
        const slotH = Math.max(280, nodeH - posY - 16);
        const vY = posY + 6;
        const vW = nodeW - 24;
        const vX = 12;
        this.btnHitAreas = [];
        this.chipHitAreas = [];
        ctx.save();
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
        const modes = [
          { key: "hover_slide", label: "\u26A1 Hover (rgthree)", activeColor: "#2997ff" },
          { key: "split", label: "\u2194 Drag Split", activeColor: "#2dd4bf" },
          { key: "toggle", label: this.mode === "toggle" ? this.toggleShowB ? "\u{1F441} B (Click A)" : "\u{1F441} A (Click B)" : "\u{1F441} Toggle (Space)", activeColor: "#ff9f0a" },
          { key: "side", label: "\u25EB Side-by-Side", activeColor: "#30d158" },
          { key: "diff_heat", label: "\u{1F525} Diff Heatmap", activeColor: "#ff453a" },
          { key: "only_a", label: "Solo A", activeColor: "#58b0ff" },
          { key: "only_b", label: "Solo B", activeColor: "#ff9f0a" }
        ];
        let btnX = vX + 6;
        ctx.font = "bold 9px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
        ctx.textBaseline = "middle";
        modes.forEach((m) => {
          const active = this.mode === m.key;
          const textW = ctx.measureText(m.label).width;
          const bW = textW + 12;
          const bH = 18;
          const bY = barY + 4;
          const col = m.activeColor || "#2dd4bf";
          ctx.fillStyle = active ? m.key === "hover_slide" ? "rgba(56, 189, 248, 0.25)" : m.key === "only_a" ? "rgba(147, 197, 253, 0.22)" : m.key === "only_b" ? "rgba(192, 132, 252, 0.22)" : m.key === "toggle" ? "rgba(245, 158, 11, 0.25)" : m.key === "side" ? "rgba(16, 185, 129, 0.22)" : "rgba(45, 212, 191, 0.25)" : "rgba(255, 255, 255, 0.06)";
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
            x: btnX,
            y: bY,
            w: bW,
            h: bH,
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
        const resetLabel = "\u27F2 Reset";
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
          x: rX,
          y: rY,
          w: rW,
          h: 18,
          action: () => {
            this.resetView();
          }
        });
        const zoomPct = Math.round(this.zoom * 100);
        const zoomLabel = `\u{1F50D} ${zoomPct}%`;
        const zTextW = ctx.measureText(zoomLabel).width;
        const zX = rX - zTextW - 12;
        ctx.fillStyle = this.zoom > 1.01 ? "#2997ff" : "#64748b";
        ctx.fillText(zoomLabel, zX, rY + 9);
        let currentTopY = barY + barH + 4;
        const hasMultiFrames = this.availableA && this.availableA.length > 1 || this.availableB && this.availableB.length > 1;
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
              x: chipX,
              y: cY,
              w: cW,
              h: cH,
              action: () => {
                this.selectedA = item;
                this.loadSelectedImages();
                node.setDirtyCanvas(true, true);
              }
            });
            chipX += cW + 4;
          });
          chipX += 10;
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
              x: chipX,
              y: cY,
              w: cW,
              h: cH,
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
            ctx.fillText("\u23F3 Loading image preview...", vp.x + vp.w / 2, vp.y + vp.h / 2);
          } else {
            ctx.fillText("Connect image_a and image_b, then click Queue Prompt to inspect", vp.x + vp.w / 2, vp.y + vp.h / 2 - 10);
            ctx.font = "10px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
            ctx.fillStyle = "#64748b";
            ctx.fillText("Hover Slider \u2022 Zero Stretch \u2022 Zero Crop \u2022 Precise Centering", vp.x + vp.w / 2, vp.y + vp.h / 2 + 12);
          }
          ctx.restore();
          return;
        }
        const centerX = vp.x + vp.w / 2;
        const centerY = vp.y + vp.h / 2;
        const natWA = this.imgA.naturalWidth;
        const natHA = this.imgA.naturalHeight;
        const natWB = this.imgB.naturalWidth;
        const natHB = this.imgB.naturalHeight;
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
        if (this.mode === "only_a") {
          ctx.save();
          ctx.beginPath();
          ctx.rect(vp.x, vp.y, vp.w, vp.h);
          ctx.clip();
          renderImageA();
          ctx.restore();
        } else if (this.mode === "only_b") {
          ctx.save();
          ctx.beginPath();
          ctx.rect(vp.x, vp.y, vp.w, vp.h);
          ctx.clip();
          renderImageB();
          ctx.restore();
        } else if (this.mode === "diff_heat") {
          ctx.save();
          ctx.beginPath();
          ctx.rect(vp.x, vp.y, vp.w, vp.h);
          ctx.clip();
          renderImageDiff();
          ctx.restore();
        } else if (this.mode === "split" || this.mode === "hover_slide") {
          const splitScreenX = Math.round(vp.x + this.splitX * vp.w);
          ctx.save();
          ctx.beginPath();
          ctx.rect(vp.x, vp.y, splitScreenX - vp.x, vp.h);
          ctx.clip();
          renderImageA();
          ctx.restore();
          ctx.save();
          ctx.beginPath();
          ctx.rect(splitScreenX, vp.y, vp.x + vp.w - splitScreenX, vp.h);
          ctx.clip();
          renderImageB();
          ctx.restore();
          ctx.save();
          ctx.strokeStyle = "#2dd4bf";
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.moveTo(splitScreenX, vp.y);
          ctx.lineTo(splitScreenX, vp.y + vp.h);
          ctx.stroke();
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
          ctx.fillText("\u25C4\u25BA", splitScreenX, pillY + pillH / 2 + 1);
          ctx.restore();
        } else if (this.mode === "toggle") {
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
        } else if (this.mode === "side") {
          const halfW = (vp.w - 2) / 2;
          const midX = vp.x + halfW;
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
          const scaleSideB = Math.min(halfW / natWB, vp.h / natHB);
          const fitSideWB = natWB * scaleSideB;
          const fitSideHB = natHB * scaleSideB;
          const centerSideBX = midX + 2 + halfW / 2 + this.panX * curZoom;
          const drawSideWB = fitSideWB * curZoom;
          const drawSideHB = fitSideHB * curZoom;
          ctx.save();
          ctx.beginPath();
          ctx.rect(midX + 2, vp.y, halfW, vp.h);
          ctx.clip();
          ctx.drawImage(this.imgB, centerSideBX - drawSideWB / 2, curCY - drawSideHB / 2, drawSideWB, drawSideHB);
          ctx.restore();
          ctx.strokeStyle = "rgba(255, 255, 255, 0.25)";
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(midX + 1, vp.y);
          ctx.lineTo(midX + 1, vp.y + vp.h);
          ctx.stroke();
        }
        ctx.font = "bold 9px sans-serif";
        ctx.textAlign = "left";
        ctx.textBaseline = "middle";
        if (this.mode === "toggle") {
          const showB = this.isHoldingPointer ? !this.toggleShowB : this.toggleShowB;
          const tText = showB ? `\u{1F441} B: ${this.labelB} (${natWB}\xD7${natHB}) \u2022 Click / Space for A` : `\u{1F441} A: ${this.labelA} (${natWA}\xD7${natHA}) \u2022 Click / Space for B`;
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
          if (this.mode !== "only_b" && this.mode !== "diff_heat") {
            const labelAText = `\u25C4 A: ${this.labelA} (${natWA}\xD7${natHA})`;
            const lAW = ctx.measureText(labelAText).width + 14;
            ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
            ctx.fillRect(vp.x + 8, vp.y + 8, lAW, 18);
            ctx.fillStyle = "#2997ff";
            ctx.fillText(labelAText, vp.x + 14, vp.y + 17);
          } else if (this.mode === "diff_heat") {
            const m = this.metricsData || {};
            const ssimStr = m.ssim !== void 0 ? `SSIM: ${m.ssim}` : "";
            const psnrStr = m.psnr_db !== void 0 ? `PSNR: ${m.psnr_db}dB` : "";
            const deltaStr = m.changed_pixels_pct !== void 0 ? `\u0394: ${m.changed_pixels_pct}%` : "";
            const diffTxt = `\u{1F525} Thermal Diff \u2022 ${[ssimStr, psnrStr, deltaStr].filter(Boolean).join(" \u2022 ") || "Delta Map"}`;
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
          if (this.mode !== "only_a") {
            const labelBText = `B: ${this.labelB} (${natWB}\xD7${natHB}) \u25BA`;
            const lBW = ctx.measureText(labelBText).width + 14;
            ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
            ctx.fillRect(vp.x + vp.w - lBW - 8, vp.y + 8, lBW, 18);
            ctx.fillStyle = "#ff9f0a";
            ctx.fillText(labelBText, vp.x + vp.w - lBW - 2, vp.y + 17);
          }
        }
        if (this.zoom > 1.05) {
          const hint = "\u{1F50D} Drag to Pan \u2022 Wheel to Zoom \u2022 Space to Toggle A/B";
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
        for (const btn of this.btnHitAreas) {
          if (mx >= btn.x && mx <= btn.x + btn.w && my >= btn.y && my <= btn.y + btn.h) {
            btn.action();
            if (this.node) this.node.setDirtyCanvas(true, true);
            if (e && e.stopPropagation) e.stopPropagation();
            return true;
          }
        }
        for (const chip of this.chipHitAreas) {
          if (mx >= chip.x && mx <= chip.x + chip.w && my >= chip.y && my <= chip.y + chip.h) {
            chip.action();
            if (this.node) this.node.setDirtyCanvas(true, true);
            if (e && e.stopPropagation) e.stopPropagation();
            return true;
          }
        }
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
          const newZoom = Math.max(1, Math.min(10, this.zoom * delta));
          if (newZoom === 1) {
            this.panX = 0;
            this.panY = 0;
          } else {
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
      const cachedImages = this.properties?.stoiqo_images || info?.properties?.stoiqo_images || this.cmpWidget?.imagesData || this.cmpWidget?.value;
      if (cachedImages && Array.isArray(cachedImages) && cachedImages.length > 0 && this.cmpWidget) {
        this.cmpWidget.setImages(cachedImages);
      }
    };
    const origCmpRemoved = nodeType.prototype.onRemoved;
    nodeType.prototype.onRemoved = function() {
      if (app11.canvas && app11.canvas.canvas && this._stoiqoWheelHandler) {
        app11.canvas.canvas.removeEventListener("wheel", this._stoiqoWheelHandler, { capture: true, passive: false });
        this._stoiqoWheelHandler = null;
      }
      if (this._stoiqoSpaceHandler) {
        window.removeEventListener("keydown", this._stoiqoSpaceHandler, { capture: true });
        this._stoiqoSpaceHandler = null;
      }
      this.cmpWidget = null;
      if (origCmpRemoved) origCmpRemoved.apply(this, arguments);
    };
    const origCmpDrawBg = nodeType.prototype.onDrawBackground;
    nodeType.prototype.onDrawBackground = function(ctx) {
      this.hideOutputImages = true;
      this.imgs = null;
      this.images = null;
      if (origCmpDrawBg) origCmpDrawBg.apply(this, arguments);
    };
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
        let w = this.widgets?.find((x) => x instanceof StoiqoCompareCanvasWidget);
        if (!w) {
          setupImageCompareNodeUI(this);
          w = this.widgets?.find((x) => x instanceof StoiqoCompareCanvasWidget);
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
        if (this.widgets) {
          this.widgets = this.widgets.filter(
            (x) => x === w || x.name !== "preview" && x.type !== "image" && !x._is_preview
          );
        }
        this.imgs = null;
        this.images = null;
        this.setDirtyCanvas(true, true);
      }
    };
  }
  const resTargetNames = [
    "StoiqoResolutionNode",
    "[STOIQO] Image Resolution & Aspect Ratio"
  ];
  if (resTargetNames.includes(nodeData.name)) {
    let setupResNode = function(node) {
      if (!node || !node.widgets) return;
      if (!node.size || node.size[0] < MIN_RES_WIDTH) {
        node.size = [MIN_RES_WIDTH, node.size ? node.size[1] : 240];
      }
      function ensureResHUD() {
        if (!node.widgets.some((w) => w.name === "_stoiqo_res_hud")) {
          node.widgets.push(new StoiqoResolutionHUDWidget(node));
        }
      }
      function updateCustomDimsVisibility() {
        const aspectWidget = node.widgets.find((w) => w.name === "aspect_ratio");
        const wWidget = node.widgets.find((w) => w.name === "custom_width");
        const hWidget = node.widgets.find((w) => w.name === "custom_height");
        if (!wWidget || !hWidget) return;
        const isCustom = aspectWidget && String(aspectWidget.value || "").includes("Custom");
        [wWidget, hWidget].forEach((widget) => {
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
            widget.computeSize = function() {
              return [0, -4];
            };
            widget.draw = function() {
            };
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
      node.widgets.forEach((w) => {
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
    };
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
        return void 0;
      }
      computeSize(width) {
        return [width, this.height];
      }
      draw(ctx, node, width, y, height) {
        if (node.flags && node.flags.collapsed) return;
        const aspectW = node.widgets.find((w2) => w2.name === "aspect_ratio");
        const scaleW = node.widgets.find((w2) => w2.name === "scale_target");
        const swapW = node.widgets.find((w2) => w2.name === "swap_dimensions");
        const multW = node.widgets.find((w2) => w2.name === "multiple_of");
        const customW = node.widgets.find((w2) => w2.name === "custom_width");
        const customH = node.widgets.find((w2) => w2.name === "custom_height");
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
          "5:4 Social Media Landscape (1200 x 960)": [1200, 960]
        };
        const RATIO_VALS = {
          "1:1 Square (1024 x 1024)": 1,
          "16:9 Landscape Widescreen (1344 x 768)": 16 / 9,
          "9:16 Portrait / Story (768 x 1344)": 9 / 16,
          "4:3 Standard Photo (1152 x 896)": 4 / 3,
          "3:4 Classic Portrait (896 x 1152)": 3 / 4,
          "3:2 Classic 35mm (1216 x 832)": 3 / 2,
          "2:3 Portrait 35mm (832 x 1216)": 2 / 3,
          "21:9 Ultrawide Cinema (1536 x 640)": 21 / 9,
          "9:21 Ultrawide Vertical (640 x 1536)": 9 / 21,
          "4:5 Social Media Portrait (960 x 1200)": 4 / 5,
          "5:4 Social Media Landscape (1200 x 960)": 5 / 4
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
          const imgSlot = node.inputs ? node.inputs.find((i) => i.name === "image") : null;
          if (!imgSlot || imgSlot.link === null) {
            note = "\u26A0\uFE0F No Image (fallback 1024\xD71024)";
            w = 1024;
            h = 1024;
          } else {
            note = "\u{1F4F7} Auto-match proporzioni immagine";
            w = 1024;
            h = 1024;
          }
        } else if (isCustom) {
          w = Math.round(cW / step) * step;
          h = Math.round(cH / step) * step;
        } else if (scale.includes("Exact Preset") && PRESET_DIMS[aspect]) {
          [w, h] = PRESET_DIMS[aspect];
          w = Math.round(w / step) * step;
          h = Math.round(h / step) * step;
        } else {
          const ratio = RATIO_VALS[aspect] || 1;
          const rawH = Math.sqrt(targetPixels / ratio);
          const rawW = rawH * ratio;
          w = Math.max(step, Math.round(rawW / step) * step);
          h = Math.max(step, Math.round(rawH / step) * step);
        }
        if (swap) {
          const temp = w;
          w = h;
          h = temp;
        }
        const calcRatio = h > 0 ? (w / h).toFixed(2) : "1.00";
        const mpx = (w * h / 1e6).toFixed(2);
        const tensorMb = (w * h * 12 / (1024 * 1024)).toFixed(1);
        const latentMb = (w * h * 0.5 / (1024 * 1024)).toFixed(1);
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
        ctx.fillStyle = "#2997ff";
        if (ctx.roundRect) {
          ctx.beginPath();
          ctx.roundRect(margin, y, 4, cardH, [6, 0, 0, 6]);
          ctx.fill();
        } else {
          ctx.fillRect(margin, y, 4, cardH);
        }
        ctx.font = "bold 11px Inter, sans-serif";
        ctx.fillStyle = "#f8fafc";
        ctx.textAlign = "left";
        ctx.textBaseline = "middle";
        ctx.fillText(`\u{1F4D0} ${w} \xD7 ${h}  \u2022  ${calcRatio}:1  \u2022  ${mpx} MP`, margin + 12, y + 14);
        ctx.font = "10px Inter, monospace, sans-serif";
        ctx.fillStyle = "#94a3b8";
        let line2 = `\u{1F4BE} ~${tensorMb} MB VRAM (Flux Latent: ~${latentMb} MB)`;
        if (note) {
          line2 += ` \u2022 ${note}`;
        }
        ctx.fillText(line2, margin + 12, y + 30);
        ctx.restore();
      }
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

// src_js/nodes/datasetNode.js
import { api as api5 } from "../../../scripts/api.js";
function setupDatasetNode(nodeType, nodeData, app11) {
  const targetNames = [
    "StoiqoDatasetWriterNode",
    "[STOIQO] Dataset & LoRA Toolkit"
  ];
  if (targetNames.includes(nodeData.name)) {
    let configureDatasetNode = function(node) {
      if (!node || !node.widgets) return;
      if (node.size && node.size[0] < MIN_NODE_WIDTH) {
        node.size[0] = MIN_NODE_WIDTH;
      }
      const outputDirWidget = node.widgets.find((w) => w.name === "output_dir");
      const hasBrowseBtn = node.widgets.some((w) => w._isStoiqoBrowse);
      if (outputDirWidget && !hasBrowseBtn) {
        const browseBtn = node.addWidget("button", "\u{1F4C1} Browse Output Folder", null, async () => {
          try {
            const resp = await api5.fetchApi("/stoiqo/browse_folder", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ initial_dir: outputDirWidget.value || "" })
            });
            const data = await resp.json();
            const selected = data && (data.path || data.folder_path);
            if (data && data.status === "ok" && selected) {
              outputDirWidget.value = selected;
              if (outputDirWidget.inputEl) {
                outputDirWidget.inputEl.value = selected;
              }
              if (outputDirWidget.callback) {
                outputDirWidget.callback(selected);
              }
              node.setDirtyCanvas(true, true);
            }
          } catch (err) {
            console.error("[STOIQO Dataset Toolkit] Folder selection error:", err);
          }
        });
        browseBtn.serialize = false;
        browseBtn._isStoiqoBrowse = true;
        const btnIdx = node.widgets.indexOf(browseBtn);
        const dirIdx = node.widgets.indexOf(outputDirWidget);
        if (btnIdx > -1 && dirIdx > -1 && btnIdx !== dirIdx + 1) {
          node.widgets.splice(btnIdx, 1);
          node.widgets.splice(dirIdx + 1, 0, browseBtn);
        }
      }
      const blacklistWidget = node.widgets.find((w) => w.name === "blacklist_tags");
      if (blacklistWidget) {
        blacklistWidget.computeSize = function(width) {
          return [width, 50];
        };
        const applyInputStyles = (el) => {
          if (!el) return;
          el.style.boxSizing = "border-box";
          el.style.height = "50px";
          el.style.minHeight = "50px";
          el.style.maxHeight = "50px";
          el.style.resize = "none";
          el.style.fontSize = "11.5px";
          el.style.lineHeight = "1.45";
        };
        if (blacklistWidget.inputEl) {
          applyInputStyles(blacklistWidget.inputEl);
        } else {
          let rawInputEl = null;
          Object.defineProperty(blacklistWidget, "inputEl", {
            configurable: true,
            enumerable: true,
            get() {
              return rawInputEl;
            },
            set(val) {
              rawInputEl = val;
              applyInputStyles(val);
            }
          });
        }
      }
    };
    const MIN_NODE_WIDTH = 460;
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function() {
      if (onNodeCreated) {
        onNodeCreated.apply(this, arguments);
      }
      configureDatasetNode(this);
    };
    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function() {
      if (onConfigure) {
        onConfigure.apply(this, arguments);
      }
      configureDatasetNode(this);
    };
  }
}

// src_js/nodes/iteratorNode.js
import { api as api6 } from "../../../scripts/api.js";
var StoiqoIteratorHUDWidget = class {
  constructor(node) {
    this.node = node;
    this.type = "custom";
    this.name = "_stoiqo_iterator_hud";
    this.serialize = false;
    this.options = { serialize: false };
  }
  serializeValue() {
    return void 0;
  }
  isVisible() {
    return Boolean(this.node?.properties?._stoiqo_progress && !this.node?.flags?.collapsed);
  }
  computeSize(width) {
    if (!this.isVisible()) return [0, -4];
    return [width, 28];
  }
  draw(ctx, node, width, y) {
    if (!this.isVisible()) return;
    const prog = node?.properties?._stoiqo_progress;
    const fname = node?.properties?._stoiqo_filename;
    const badgeH = 22;
    const badgeY = y + 3;
    const badgeX = 10;
    const nodeW = node && node.size ? node.size[0] : width;
    const badgeW = nodeW - 20;
    ctx.save();
    ctx.fillStyle = "rgba(15, 23, 42, 0.88)";
    ctx.strokeStyle = "#2dd4bf";
    ctx.lineWidth = 1;
    if (ctx.roundRect) {
      ctx.beginPath();
      ctx.roundRect(badgeX, badgeY, badgeW, badgeH, 4);
      ctx.fill();
      ctx.stroke();
    } else {
      ctx.fillRect(badgeX, badgeY, badgeW, badgeH);
      ctx.strokeRect(badgeX, badgeY, badgeW, badgeH);
    }
    ctx.font = "bold 9.5px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, monospace";
    ctx.textBaseline = "middle";
    ctx.fillStyle = "#2dd4bf";
    const pText = `\u{1F4C1} ${prog}`;
    ctx.fillText(pText, badgeX + 8, badgeY + badgeH / 2);
    const pW = ctx.measureText(pText).width;
    if (fname) {
      ctx.fillStyle = "#94a3b8";
      const maxChars = Math.max(15, Math.floor((badgeW - pW - 30) / 6.5));
      const truncFname = fname.length > maxChars ? "\u2026" + fname.slice(-maxChars) : fname;
      ctx.fillText(`\u2022 ${truncFname}`, badgeX + pW + 16, badgeY + badgeH / 2);
    }
    ctx.restore();
  }
};
function setupIteratorNode(nodeType, nodeData, app11) {
  const targetNames = [
    "StoiqoSmartFolderImageIterator",
    "[STOIQO] Smart Folder Image Iterator"
  ];
  if (targetNames.includes(nodeData.name)) {
    let setupIteratorNodeUI = function(node) {
      if (!node || !node.widgets) return;
      if (node.size && node.size[0] < MIN_NODE_WIDTH) {
        node.size[0] = MIN_NODE_WIDTH;
      }
      const folderPathWidget = node.widgets.find((w) => w.name === "folder_path");
      let browseBtn = node.widgets.find((w) => w._isStoiqoBrowse);
      if (!browseBtn) {
        browseBtn = node.addWidget(
          "button",
          "\u{1F4C1} Browse Dataset Folder",
          null,
          async function() {
            const currentPath = folderPathWidget ? folderPathWidget.value || "" : "";
            const origLabel = this.name;
            this.name = "\u23F3 Selecting folder in Windows...";
            node.setDirtyCanvas(true);
            try {
              const resp = await api6.fetchApi("/stoiqo/browse_folder", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ initial_dir: currentPath })
              });
              if (resp.ok) {
                const res = await resp.json();
                if (res && res.path) {
                  if (folderPathWidget) {
                    folderPathWidget.value = res.path;
                    if (folderPathWidget.inputEl) {
                      folderPathWidget.inputEl.value = res.path;
                    }
                  }
                  this.name = "\u2713 Folder Selected!";
                  setTimeout(() => {
                    this.name = origLabel;
                    node.setDirtyCanvas(true);
                  }, 1800);
                } else {
                  this.name = origLabel;
                }
              } else {
                this.name = origLabel;
              }
            } catch (err) {
              console.warn("[Stoiqo] Browse folder error:", err);
              this.name = origLabel;
            }
            node.setDirtyCanvas(true);
          },
          { serialize: false }
        );
        browseBtn._isStoiqoBrowse = true;
        browseBtn.serialize = false;
        browseBtn.options = { serialize: false };
        const pathIdx = node.widgets.findIndex((w) => w.name === "folder_path");
        if (pathIdx !== -1) {
          const curIdx = node.widgets.indexOf(browseBtn);
          if (curIdx !== -1) {
            node.widgets.splice(curIdx, 1);
            node.widgets.splice(pathIdx + 1, 0, browseBtn);
          }
        }
      }
      let refreshBtn = node.widgets.find((w) => w._isStoiqoRefresh);
      if (!refreshBtn) {
        refreshBtn = node.addWidget(
          "button",
          "\u27F2 Rescan / Invalidate Cache",
          null,
          function() {
            const origLabel = this.name;
            this.name = "\u2713 Cache Re-indexed!";
            if (node.properties) {
              delete node.properties._stoiqo_progress;
              delete node.properties._stoiqo_filename;
            }
            node.setDirtyCanvas(true, true);
            setTimeout(() => {
              this.name = origLabel;
              node.setDirtyCanvas(true);
            }, 1500);
          },
          { serialize: false }
        );
        refreshBtn._isStoiqoRefresh = true;
        refreshBtn.serialize = false;
        refreshBtn.options = { serialize: false };
        const browseIdx = node.widgets.indexOf(browseBtn);
        if (browseIdx !== -1) {
          const curIdx = node.widgets.indexOf(refreshBtn);
          if (curIdx !== -1) {
            node.widgets.splice(curIdx, 1);
            node.widgets.splice(browseIdx + 1, 0, refreshBtn);
          }
        }
      }
      const existingHuds = node.widgets.filter((w) => w.name === "_stoiqo_iterator_hud");
      for (const extra of existingHuds.slice(1)) {
        node.widgets.splice(node.widgets.indexOf(extra), 1);
      }
      let iterHud = existingHuds[0];
      if (!iterHud) {
        iterHud = new StoiqoIteratorHUDWidget(node);
        node.widgets.push(iterHud);
      }
      if (refreshBtn && iterHud) {
        const curIdx = node.widgets.indexOf(iterHud);
        const refIdx = node.widgets.indexOf(refreshBtn);
        if (curIdx !== -1 && refIdx !== -1 && curIdx !== refIdx + 1) {
          node.widgets.splice(curIdx, 1);
          const newTarget = curIdx < refIdx + 1 ? refIdx : refIdx + 1;
          node.widgets.splice(newTarget, 0, iterHud);
        }
      }
    };
    const MIN_NODE_WIDTH = 460;
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function() {
      if (onNodeCreated) {
        onNodeCreated.apply(this, arguments);
      }
      setupIteratorNodeUI(this);
    };
    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function() {
      if (onConfigure) {
        onConfigure.apply(this, arguments);
      }
      setupIteratorNodeUI(this);
    };
    const onExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function(message) {
      if (onExecuted) {
        onExecuted.apply(this, arguments);
      }
      if (message) {
        this.properties = this.properties || {};
        if (message.progress && message.progress[0]) {
          this.properties._stoiqo_progress = String(message.progress[0]);
        }
        if (message.filename && message.filename[0]) {
          this.properties._stoiqo_filename = String(message.filename[0]);
        }
        if (typeof this.setSize === "function" && typeof this.computeSize === "function") {
          const sz = this.computeSize();
          this.setSize([Math.max(MIN_NODE_WIDTH, this.size ? this.size[0] : sz[0]), Math.max(this.size ? this.size[1] : sz[1], sz[1])]);
        }
        this.setDirtyCanvas(true, true);
      }
    };
  }
}

// src_js/nodes/trioLoaderNode.js
import { app as app5 } from "../../../scripts/app.js";
import { api as api7 } from "../../../scripts/api.js";
function setupTrioLoaderNode(nodeType, nodeData, appInstance) {
  const targetNames = [
    "StoiqoImageLoaderNode",
    "StoiqoTripleImageLoaderNode",
    "[STOIQO] Image Loader",
    "[STOIQO] Trio Image Loader (Hero & Thumbs)"
  ];
  if (!targetNames.includes(nodeData.name)) return;
  const MIN_WIDTH3 = 460;
  const MIN_HEIGHT = 740;
  function parseImageDescriptor(val) {
    if (!val || typeof val !== "string" || val === "none") return null;
    let clean = val.replace(/\s*\[(input|output|temp)\]\s*$/i, "").trim();
    if (!clean || clean === "none") return null;
    let subfolder = "";
    let filename = clean;
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
    return api7.apiURL(`/view?${params.toString()}`);
  }
  class StoiqoTrioGalleryWidget {
    constructor(node) {
      this.type = "custom";
      this.name = "_stoiqo_trio_gallery";
      this.value = {};
      this.serialize = false;
      this.options = { serialize: false };
      this.node = node;
      this.activeFocus = 1;
      this.images = [null, null, null];
      this.rawValues = ["", "", ""];
      this.meta = [null, null, null];
      this.thumbRects = [];
      this.heroRect = { x: 0, y: 0, w: 0, h: 0 };
    }
    serializeValue() {
      return void 0;
    }
    computeSize(width) {
      const pad = 12;
      const availableWidth = (width || 460) - pad * 2;
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
      const nodeWidth = node && node.size ? node.size[0] : width;
      const pad = 12;
      const availableWidth = nodeWidth - pad * 2;
      this.syncFromWidgets();
      const heroHeight = Math.max(360, Math.round(availableWidth * 1.15));
      const heroY = posY + 6;
      this.heroRect = { x: pad, y: heroY, w: availableWidth, h: heroHeight };
      ctx.save();
      ctx.fillStyle = "#0c0f17";
      ctx.strokeStyle = "#1e2638";
      ctx.lineWidth = 1.2;
      this._roundRect(ctx, pad, heroY, availableWidth, heroHeight, 8, true, true);
      const activeIdx = this.activeFocus - 1;
      const activeImg = this.images[activeIdx];
      const activeMeta = this.meta[activeIdx];
      const activeRaw = this.rawValues[activeIdx];
      if (activeImg && activeImg.complete && activeImg.naturalWidth > 0) {
        ctx.save();
        this._roundRect(ctx, pad, heroY, availableWidth, heroHeight, 8, false, false);
        ctx.clip();
        const imgW = activeImg.naturalWidth;
        const imgH = activeImg.naturalHeight;
        const scale = Math.min((availableWidth - 8) / imgW, (heroHeight - 8) / imgH);
        const drawW = imgW * scale;
        const drawH = imgH * scale;
        const drawX = pad + (availableWidth - drawW) / 2;
        const drawY = heroY + (heroHeight - drawH) / 2;
        ctx.drawImage(activeImg, drawX, drawY, drawW, drawH);
        ctx.restore();
        const slotColors = ["#2997ff", "#58b0ff", "#30d158"];
        const slotColor = slotColors[activeIdx] || "#2997ff";
        ctx.fillStyle = "rgba(12, 15, 23, 0.88)";
        this._roundRect(ctx, pad + 8, heroY + 8, 86, 22, 4, true, false);
        ctx.fillStyle = slotColor;
        ctx.font = "bold 10px Inter, system-ui, sans-serif";
        ctx.textAlign = "left";
        ctx.fillText(`\u2605 SLOT ${this.activeFocus} HERO`, pad + 14, heroY + 23);
        if (activeMeta) {
          const resStr = `${activeMeta.width}\xD7${activeMeta.height}`;
          ctx.font = "10px monospace";
          const tw = ctx.measureText(resStr).width;
          ctx.fillStyle = "rgba(12, 15, 23, 0.88)";
          this._roundRect(ctx, pad + availableWidth - tw - 18, heroY + 8, tw + 12, 22, 4, true, false);
          ctx.fillStyle = "#58b0ff";
          ctx.fillText(resStr, pad + availableWidth - tw - 12, heroY + 23);
        }
      } else {
        ctx.fillStyle = "#475569";
        ctx.font = "bold 12px Inter, system-ui, sans-serif";
        ctx.textAlign = "center";
        const isNone = !activeRaw || activeRaw === "none";
        const emptyMsg = isNone ? `[Slot ${this.activeFocus}: No image selected]` : `[Slot ${this.activeFocus}: Loading image...]`;
        ctx.fillText(emptyMsg, pad + availableWidth / 2, heroY + heroHeight / 2 - 8);
        ctx.font = "10px Inter, system-ui, sans-serif";
        ctx.fillStyle = "#334155";
        ctx.fillText("Select an image from the dropdown above to preview", pad + availableWidth / 2, heroY + heroHeight / 2 + 12);
        ctx.textAlign = "left";
      }
      const thumbsY = heroY + heroHeight + 12;
      const thumbHeight = 96;
      const gap = 8;
      const thumbWidth = Math.floor((availableWidth - gap * 2) / 3);
      this.thumbRects = [];
      for (let i = 0; i < 3; i++) {
        const tx = pad + i * (thumbWidth + gap);
        const ty = thumbsY;
        this.thumbRects.push({ x: tx, y: ty, w: thumbWidth, h: thumbHeight, slot: i + 1 });
        const isFocused = this.activeFocus === i + 1;
        const thumbImg = this.images[i];
        const rawName = this.rawValues[i];
        ctx.fillStyle = isFocused ? "#141923" : "#0d111a";
        ctx.strokeStyle = isFocused ? "#58b0ff" : "#242d42";
        ctx.lineWidth = isFocused ? 2 : 1;
        this._roundRect(ctx, tx, ty, thumbWidth, thumbHeight, 6, true, true);
        if (thumbImg && thumbImg.complete && thumbImg.naturalWidth > 0) {
          ctx.save();
          this._roundRect(ctx, tx + 2, ty + 2, thumbWidth - 4, thumbHeight - 24, 4, false, false);
          ctx.clip();
          const iw = thumbImg.naturalWidth;
          const ih = thumbImg.naturalHeight;
          const areaW = thumbWidth - 4;
          const areaH = thumbHeight - 24;
          const scale = Math.max(areaW / iw, areaH / ih);
          const sw = iw * scale;
          const sh = ih * scale;
          const sx = tx + 2 + (areaW - sw) / 2;
          const sy = ty + 2 + (areaH - sh) / 2;
          ctx.globalAlpha = isFocused ? 1 : 0.6;
          ctx.drawImage(thumbImg, sx, sy, sw, sh);
          ctx.restore();
        } else {
          ctx.fillStyle = "#334155";
          ctx.font = "10px Inter, system-ui, sans-serif";
          ctx.textAlign = "center";
          ctx.fillText(rawName === "none" || !rawName ? "(Vuoto)" : "...", tx + thumbWidth / 2, ty + (thumbHeight - 24) / 2 + 3);
          ctx.textAlign = "left";
        }
        ctx.fillStyle = isFocused ? "#58b0ff" : "#64748b";
        ctx.font = isFocused ? "bold 10px Inter, system-ui, sans-serif" : "10px Inter, system-ui, sans-serif";
        ctx.textAlign = "center";
        const slotLabels = ["1: Main", "2: Sec", "3: Ref"];
        const labelText = isFocused ? `\u25B6 ${slotLabels[i]}` : slotLabels[i];
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
  nodeType.prototype.onNodeCreated = function() {
    const ret = onNodeCreated ? onNodeCreated.apply(this, arguments) : void 0;
    this.hideOutputImages = true;
    this.imgs = null;
    this.images = null;
    this.size = this.size || [MIN_WIDTH3, MIN_HEIGHT];
    if (this.size[0] < MIN_WIDTH3) this.size[0] = MIN_WIDTH3;
    if (this.size[1] < MIN_HEIGHT) this.size[1] = MIN_HEIGHT;
    this.widgets = this.widgets || [];
    const existingDivs = this.widgets.filter(
      (w) => w.name === "_stoiqo_divider_1" || w.name === "divider_1" || w.isStoiqoDivider
    );
    for (const extra of existingDivs.slice(1)) {
      this.widgets.splice(this.widgets.indexOf(extra), 1);
    }
    if (existingDivs.length === 0) {
      this.addCustomWidget(new StoiqoSectionDividerWidget(1, "MULTI-IMAGE TRIO LOADER", "#2997ff"));
    }
    const existingGals = this.widgets.filter((w) => w.name === "_stoiqo_trio_gallery");
    for (const extra of existingGals.slice(1)) {
      this.widgets.splice(this.widgets.indexOf(extra), 1);
    }
    let galleryWidget = existingGals[0];
    if (!galleryWidget) {
      galleryWidget = new StoiqoTrioGalleryWidget(this);
      this.addCustomWidget(galleryWidget);
    }
    this._trio_gallery = galleryWidget;
    const origOnExecuted = this.onExecuted;
    this.onExecuted = function(message) {
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
    const origOnMouseDown = this.onMouseDown;
    this.onMouseDown = function(event, localPos, graphCanvas) {
      if (galleryWidget && galleryWidget.handlePointerDown(localPos, this)) {
        return true;
      }
      return origOnMouseDown ? origOnMouseDown.apply(this, arguments) : false;
    };
    return ret;
  };
  const origDrawBackground = nodeType.prototype.onDrawBackground;
  nodeType.prototype.onDrawBackground = function(ctx) {
    this.hideOutputImages = true;
    this.imgs = null;
    this.images = null;
    if (origDrawBackground) {
      origDrawBackground.apply(this, arguments);
    }
  };
}

// src_js/nodes/textConcatNode.js
import { app as app6 } from "../../../scripts/app.js";
function setupConcatNode(nodeType, nodeData, appInstance) {
  const concatTargetNames = [
    "StoiqoTextConcatenateNode",
    "[STOIQO] Text Concatenate & Clean"
  ];
  if (!concatTargetNames.includes(nodeData.name)) return;
  const MIN_WIDTH3 = 420;
  const MAX_SLOTS = 8;
  const DEFAULT_BOX_HEIGHT = 56;
  const HEIGHT_PRESETS = [44, 72, 120, 200];
  function swapSlots(node, slotA, slotB) {
    const visibleCount = node._stoiqoVisibleSlots || 1;
    if (slotA < 1 || slotA > visibleCount || slotB < 1 || slotB > visibleCount) return;
    if (slotA === slotB) return;
    const nameA = `text_${slotA}`;
    const nameB = `text_${slotB}`;
    const wA = node.widgets ? node.widgets.find((x) => x.name === nameA) : null;
    const wB = node.widgets ? node.widgets.find((x) => x.name === nameB) : null;
    if (!wA || !wB) return;
    const tempVal = wA.value || "";
    wA.value = wB.value || "";
    wB.value = tempVal;
    if (wA.inputEl) wA.inputEl.value = wA.value;
    if (wB.inputEl) wB.inputEl.value = wB.value;
    if (wA.callback) wA.callback(wA.value);
    if (wB.callback) wB.callback(wB.value);
    node.properties = node.properties || {};
    node.properties.box_heights = node.properties.box_heights || {};
    const tempH = wA._boxHeight || DEFAULT_BOX_HEIGHT;
    wA._boxHeight = wB._boxHeight || DEFAULT_BOX_HEIGHT;
    wB._boxHeight = tempH;
    node.properties.box_heights[nameA] = wA._boxHeight;
    node.properties.box_heights[nameB] = wB._boxHeight;
    if (wA.inputEl) wA.inputEl.style.height = `${wA._boxHeight}px`;
    if (wB.inputEl) wB.inputEl.style.height = `${wB._boxHeight}px`;
    if (node.inputs) {
      const inpA = node.inputs.find((inp) => inp.name === nameA);
      const inpB = node.inputs.find((inp) => inp.name === nameB);
      if (inpA && inpB) {
        const linkAId = inpA.link;
        const linkBId = inpB.link;
        inpA.link = linkBId;
        inpB.link = linkAId;
        const idxA = node.inputs.indexOf(inpA);
        const idxB = node.inputs.indexOf(inpB);
        const graphLinks = app6.graph ? app6.graph.links : null;
        if (graphLinks) {
          if (linkAId != null && graphLinks[linkAId]) {
            graphLinks[linkAId].target_slot = idxB;
          }
          if (linkBId != null && graphLinks[linkBId]) {
            graphLinks[linkBId].target_slot = idxA;
          }
        }
      }
    }
    if (node._stoiqoRefreshSlots) {
      node._stoiqoRefreshSlots();
    } else {
      if (typeof node.computeSize === "function") {
        node.setSize(node.computeSize());
      }
      node.setDirtyCanvas(true, true);
    }
    if (app6.graph && app6.graph.setDirtyCanvas) {
      app6.graph.setDirtyCanvas(true, true);
    }
  }
  function cycleSlotHeight(node, slotIndex) {
    const name = `text_${slotIndex}`;
    const w = node.widgets ? node.widgets.find((x) => x.name === name) : null;
    if (!w) return;
    const currentH = w._boxHeight || DEFAULT_BOX_HEIGHT;
    let nextH = HEIGHT_PRESETS[0];
    for (let i = 0; i < HEIGHT_PRESETS.length; i++) {
      if (currentH < HEIGHT_PRESETS[i] - 6) {
        nextH = HEIGHT_PRESETS[i];
        break;
      }
      if (i === HEIGHT_PRESETS.length - 1) {
        nextH = HEIGHT_PRESETS[0];
      }
    }
    w._boxHeight = nextH;
    node.properties = node.properties || {};
    node.properties.box_heights = node.properties.box_heights || {};
    node.properties.box_heights[name] = nextH;
    if (w.inputEl) {
      w.inputEl.style.height = `${nextH}px`;
    }
    if (node._stoiqoRefreshSlots) {
      node._stoiqoRefreshSlots();
    } else {
      if (typeof node.computeSize === "function") {
        node.setSize(node.computeSize());
      }
      node.setDirtyCanvas(true, true);
    }
  }
  function clearSlot(node, slotIndex) {
    const name = `text_${slotIndex}`;
    const w = node.widgets ? node.widgets.find((x) => x.name === name) : null;
    if (!w) return;
    w.value = "";
    if (w.inputEl) w.inputEl.value = "";
    if (w.callback) w.callback("");
    node.setDirtyCanvas(true, true);
  }
  class StoiqoSlotHeaderWidget {
    constructor(node, slotIndex) {
      this.type = "custom";
      this.name = `_stoiqo_slot_hdr_${slotIndex}`;
      this.slotIndex = slotIndex;
      this.node = node;
      this.serialize = false;
      this.options = { serialize: false };
      this.hitAreas = [];
    }
    serializeValue() {
      return void 0;
    }
    computeSize(width) {
      const isVisible = this.slotIndex <= (this.node._stoiqoVisibleSlots || 1);
      return isVisible ? [width, 20] : [0, -4];
    }
    draw(ctx, node, width, posY, height) {
      const isVisible = this.slotIndex <= (node._stoiqoVisibleSlots || 1);
      if (!isVisible) return;
      this.hitAreas = [];
      const nodeW = node && node.size ? node.size[0] : width;
      const pad = 12;
      const barW = nodeW - pad * 2;
      const barH = 18;
      const barY = posY + 2;
      ctx.save();
      const wName = `text_${this.slotIndex}`;
      const w = node.widgets ? node.widgets.find((x) => x.name === wName) : null;
      const inp = node.inputs ? node.inputs.find((x) => x.name === wName) : null;
      const isConnected = inp && inp.link != null;
      const hasText = Boolean(w && w.value && String(w.value).trim().length > 0);
      const currentH = w ? w._boxHeight || DEFAULT_BOX_HEIGHT : DEFAULT_BOX_HEIGHT;
      ctx.fillStyle = isConnected ? "rgba(41, 151, 255, 0.08)" : hasText ? "rgba(255, 255, 255, 0.04)" : "rgba(15, 23, 42, 0.65)";
      ctx.strokeStyle = isConnected ? "rgba(41, 151, 255, 0.35)" : hasText ? "rgba(255, 255, 255, 0.12)" : "rgba(255, 255, 255, 0.06)";
      ctx.lineWidth = 1;
      if (ctx.roundRect) {
        ctx.beginPath();
        ctx.roundRect(pad, barY, barW, barH, 4);
        ctx.fill();
        ctx.stroke();
      } else {
        ctx.fillRect(pad, barY, barW, barH);
        ctx.strokeRect(pad, barY, barW, barH);
      }
      const dotColor = isConnected ? "#2997ff" : hasText ? "#30d158" : "#64748b";
      ctx.fillStyle = dotColor;
      ctx.beginPath();
      ctx.arc(pad + 8, barY + barH / 2, 2.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.font = "bold 9px 'JetBrains Mono', SFMono-Regular, Consolas, monospace";
      ctx.fillStyle = isConnected ? "#58b0ff" : "#f1f5f9";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText(`BOX #${this.slotIndex}`, pad + 16, barY + barH / 2 + 0.5);
      let nextLeftX = pad + 66;
      if (isConnected) {
        ctx.font = "bold 8px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif";
        ctx.fillStyle = "#2997ff";
        ctx.fillText("[LINKED WIRE]", nextLeftX, barY + barH / 2 + 0.5);
        nextLeftX += 66;
      }
      ctx.font = "8px 'JetBrains Mono', monospace";
      ctx.fillStyle = "#64748b";
      ctx.fillText(`${currentH}px`, nextLeftX, barY + barH / 2 + 0.5);
      const visibleSlots = node._stoiqoVisibleSlots || 1;
      const canMoveUp = this.slotIndex > 1;
      const canMoveDown = this.slotIndex < visibleSlots;
      let rightX = pad + barW - 4;
      const btnH = 14;
      const btnY = barY + (barH - btnH) / 2;
      if (hasText) {
        const btnW = 16;
        rightX -= btnW;
        this.drawMiniBtn(ctx, rightX, btnY, btnW, btnH, "\u2715", "#94a3b8", "rgba(255,255,255,0.06)", "rgba(255,255,255,0.12)");
        this.hitAreas.push({ key: "clear", x: rightX, y: btnY, w: btnW, h: btnH });
        rightX -= 4;
      }
      const hBtnW = 20;
      rightX -= hBtnW;
      this.drawMiniBtn(ctx, rightX, btnY, hBtnW, btnH, "\u2195", "#94a3b8", "rgba(255,255,255,0.06)", "rgba(255,255,255,0.15)");
      this.hitAreas.push({ key: "height", x: rightX, y: btnY, w: hBtnW, h: btnH });
      rightX -= 4;
      const navBtnW = 18;
      rightX -= navBtnW;
      this.drawMiniBtn(
        ctx,
        rightX,
        btnY,
        navBtnW,
        btnH,
        "\u25BC",
        canMoveDown ? "#38bdf8" : "#475569",
        canMoveDown ? "rgba(56, 189, 248, 0.12)" : "rgba(255,255,255,0.02)",
        canMoveDown ? "rgba(56, 189, 248, 0.40)" : "rgba(255,255,255,0.05)"
      );
      if (canMoveDown) {
        this.hitAreas.push({ key: "down", x: rightX, y: btnY, w: navBtnW, h: btnH });
      }
      rightX -= 4;
      rightX -= navBtnW;
      this.drawMiniBtn(
        ctx,
        rightX,
        btnY,
        navBtnW,
        btnH,
        "\u25B2",
        canMoveUp ? "#38bdf8" : "#475569",
        canMoveUp ? "rgba(56, 189, 248, 0.12)" : "rgba(255,255,255,0.02)",
        canMoveUp ? "rgba(56, 189, 248, 0.40)" : "rgba(255,255,255,0.05)"
      );
      if (canMoveUp) {
        this.hitAreas.push({ key: "up", x: rightX, y: btnY, w: navBtnW, h: btnH });
      }
      ctx.restore();
    }
    drawMiniBtn(ctx, x, y, w, h, text, color, bg, border) {
      ctx.fillStyle = bg;
      ctx.strokeStyle = border;
      ctx.lineWidth = 1;
      if (ctx.roundRect) {
        ctx.beginPath();
        ctx.roundRect(x, y, w, h, 3);
        ctx.fill();
        ctx.stroke();
      } else {
        ctx.fillRect(x, y, w, h);
        ctx.strokeRect(x, y, w, h);
      }
      ctx.font = "bold 8.5px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif";
      ctx.fillStyle = color;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(text, x + w / 2, y + h / 2 + 0.5);
    }
    mouse(event, pos, node) {
      if (!event || event.type !== "pointerdown" && event.type !== "mousedown") return false;
      const [mx, my] = pos;
      for (const hit of this.hitAreas) {
        if (mx >= hit.x && mx <= hit.x + hit.w && my >= hit.y && my <= hit.y + hit.h) {
          if (hit.key === "up") {
            swapSlots(node, this.slotIndex, this.slotIndex - 1);
          } else if (hit.key === "down") {
            swapSlots(node, this.slotIndex, this.slotIndex + 1);
          } else if (hit.key === "height") {
            cycleSlotHeight(node, this.slotIndex);
          } else if (hit.key === "clear") {
            clearSlot(node, this.slotIndex);
          }
          return true;
        }
      }
      return false;
    }
  }
  class StoiqoTokenHudWidget {
    constructor(node) {
      this.type = "custom";
      this.name = "_stoiqo_token_hud";
      this.value = {};
      this.serialize = false;
      this.options = { serialize: false };
      this.node = node;
      this.stats = { words: 0, chars: 0, tokens: 0 };
    }
    serializeValue() {
      return void 0;
    }
    computeSize(width) {
      return [width, 26];
    }
    updateStats(words, chars, tokens) {
      this.stats = { words, chars, tokens };
      if (this.node) this.node.setDirtyCanvas(true, true);
    }
    draw(ctx, node, width, posY, height) {
      const nodeW = node && node.size ? node.size[0] : width;
      const pad = 12;
      const boxW = nodeW - pad * 2;
      const boxH = 22;
      ctx.save();
      ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
      ctx.strokeStyle = "rgba(56, 189, 248, 0.35)";
      ctx.lineWidth = 1;
      if (ctx.roundRect) {
        ctx.beginPath();
        ctx.roundRect(pad, posY, boxW, boxH, 4);
        ctx.fill();
        ctx.stroke();
      } else {
        ctx.fillRect(pad, posY, boxW, boxH);
        ctx.strokeRect(pad, posY, boxW, boxH);
      }
      ctx.font = "bold 9px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
      ctx.fillStyle = "#2997ff";
      ctx.textAlign = "left";
      ctx.fillText("\u{1F4CA} STATS", pad + 8, posY + 15);
      ctx.font = "9px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
      ctx.fillStyle = "#94a3b8";
      const statText = `Parole: ${this.stats.words}   \u2022   Caratteri: ${this.stats.chars}   \u2022   Est. Token: ~${this.stats.tokens}`;
      ctx.fillText(statText, pad + 60, posY + 15);
      ctx.restore();
    }
  }
  function configureTextBoxWidget(node, w, isVisible) {
    if (!w) return;
    if (isVisible) {
      w.hidden = false;
      const currentH = w._boxHeight || node.properties?.box_heights?.[w.name] || DEFAULT_BOX_HEIGHT;
      w._boxHeight = currentH;
      w.computeSize = function(width) {
        return [width, w._boxHeight || DEFAULT_BOX_HEIGHT];
      };
      const styleInputEl = (el) => {
        if (!el) return;
        const h = w._boxHeight || DEFAULT_BOX_HEIGHT;
        el.style.boxSizing = "border-box";
        el.style.height = `${h}px`;
        el.style.minHeight = "36px";
        el.style.maxHeight = "600px";
        el.style.resize = "vertical";
        el.style.margin = "0px";
        el.style.padding = "6px 8px";
        el.style.fontSize = "11px";
        el.style.lineHeight = "1.4";
        el.hidden = false;
        el.style.display = "";
        if (window.ResizeObserver && !el._stoiqoResizeObserver) {
          el._stoiqoResizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
              const newH = Math.max(36, Math.min(600, Math.round(el.offsetHeight)));
              if (Math.abs(newH - (w._boxHeight || DEFAULT_BOX_HEIGHT)) >= 4) {
                w._boxHeight = newH;
                node.properties = node.properties || {};
                node.properties.box_heights = node.properties.box_heights || {};
                node.properties.box_heights[w.name] = newH;
                if (typeof node.computeSize === "function") {
                  const sz = node.computeSize();
                  node.setSize([Math.max(node.size[0] || 0, MIN_WIDTH3), Math.max(Math.ceil(sz[1]), 220)]);
                }
                node.setDirtyCanvas(true, true);
                if (app6.graph && app6.graph.setDirtyCanvas) {
                  app6.graph.setDirtyCanvas(true, true);
                }
              }
            }
          });
          el._stoiqoResizeObserver.observe(el);
        }
      };
      if (w.inputEl) {
        styleInputEl(w.inputEl);
      } else {
        let rawInputEl = null;
        Object.defineProperty(w, "inputEl", {
          configurable: true,
          enumerable: true,
          get() {
            return rawInputEl;
          },
          set(val) {
            rawInputEl = val;
            if (val) styleInputEl(val);
          }
        });
      }
    } else {
      w.hidden = true;
      w.computeSize = function() {
        return [0, -4];
      };
      w.draw = function() {
      };
      if (w.inputEl) {
        w.inputEl.hidden = true;
        w.inputEl.style.display = "none";
        w.inputEl.style.height = "0px";
        w.inputEl.style.minHeight = "0px";
      }
    }
  }
  function initConcatNode(node) {
    if (!node || !node.widgets) return;
    node.size = node.size || [MIN_WIDTH3, 260];
    if (node.size[0] < MIN_WIDTH3) node.size[0] = MIN_WIDTH3;
    node.properties = node.properties || {};
    node.properties.box_heights = node.properties.box_heights || {};
    let initialVisible = 1;
    for (let i = 2; i <= MAX_SLOTS; i++) {
      const wName = `text_${i}`;
      const w = node.widgets.find((x) => x.name === wName);
      const inputSlot = node.inputs ? node.inputs.find((inp) => inp.name === wName) : null;
      const hasLink = inputSlot && inputSlot.link != null;
      const hasVal = w && w.value && String(w.value).trim().length > 0;
      if (hasLink || hasVal) {
        initialVisible = Math.max(initialVisible, i);
      }
    }
    node._stoiqoVisibleSlots = node._stoiqoVisibleSlots || initialVisible;
    for (let i = 1; i <= MAX_SLOTS; i++) {
      const hdrName = `_stoiqo_slot_hdr_${i}`;
      let hdr = node.widgets.find((w) => w.name === hdrName);
      if (!hdr) {
        hdr = new StoiqoSlotHeaderWidget(node, i);
        node.addCustomWidget(hdr);
      }
    }
    configureTextBoxWidget(node, node.widgets.find((w) => w.name === "text_1"), true);
    function refreshSlots() {
      const visibleCount = node._stoiqoVisibleSlots || 1;
      for (let i = 1; i <= MAX_SLOTS; i++) {
        const isVisible = i <= visibleCount;
        const hdr = node.widgets.find((x) => x.name === `_stoiqo_slot_hdr_${i}`);
        if (hdr) {
          hdr.hidden = !isVisible;
        }
        const w = node.widgets.find((x) => x.name === `text_${i}`);
        if (w) {
          configureTextBoxWidget(node, w, isVisible);
        }
      }
      const sepWidget = node.widgets.find((w) => w.name === "separator");
      const customSep = node.widgets.find((w) => w.name === "custom_separator");
      if (customSep && sepWidget) {
        const isCustom = String(sepWidget.value || "").includes("Custom");
        if (isCustom) {
          customSep.hidden = false;
          customSep.computeSize = function(w) {
            return [w, 24];
          };
          if (customSep.inputEl) {
            customSep.inputEl.hidden = false;
            customSep.inputEl.style.display = "";
          }
        } else {
          customSep.hidden = true;
          customSep.computeSize = function() {
            return [0, -4];
          };
          customSep.draw = function() {
          };
          if (customSep.inputEl) {
            customSep.inputEl.hidden = true;
            customSep.inputEl.style.display = "none";
          }
        }
      }
      if (node._stoiqoAddBtn) {
        const canAdd = visibleCount < MAX_SLOTS;
        node._stoiqoAddBtn.name = canAdd ? `[+] Aggiungi Box Testo (${visibleCount}/${MAX_SLOTS})` : `[\u2713] Maximum ${MAX_SLOTS} Boxes Reached`;
      }
      if (node._stoiqoRemBtn) {
        const canRemove = visibleCount > 1;
        node._stoiqoRemBtn.hidden = !canRemove;
        node._stoiqoRemBtn.computeSize = canRemove ? function(w) {
          return [w, 24];
        } : function() {
          return [0, -4];
        };
      }
      if (typeof node.computeSize === "function") {
        const sz = node.computeSize();
        node.setSize([Math.max(node.size[0] || 0, MIN_WIDTH3), Math.max(Math.ceil(sz[1]), 180)]);
      }
      node.setDirtyCanvas(true, true);
      if (app6.graph && app6.graph.setDirtyCanvas) {
        app6.graph.setDirtyCanvas(true, true);
      }
    }
    if (!node._stoiqoAddBtn) {
      const addBtn = node.addWidget(
        "button",
        `[+] Aggiungi Box Testo (${node._stoiqoVisibleSlots}/${MAX_SLOTS})`,
        null,
        function() {
          if (node._stoiqoVisibleSlots < MAX_SLOTS) {
            node._stoiqoVisibleSlots++;
            refreshSlots();
          }
        }
      );
      addBtn.serialize = false;
      node._stoiqoAddBtn = addBtn;
      addBtn.draw = function(ctx, n, width, posY, height) {
        const canAdd = (node._stoiqoVisibleSlots || 1) < MAX_SLOTS;
        const pad = 12;
        const btnW = width - pad * 2;
        const btnH = 24;
        ctx.save();
        ctx.fillStyle = canAdd ? "rgba(41, 151, 255, 0.20)" : "rgba(255, 255, 255, 0.05)";
        ctx.strokeStyle = canAdd ? "#2997ff" : "rgba(255, 255, 255, 0.12)";
        ctx.lineWidth = 1.2;
        if (ctx.roundRect) {
          ctx.beginPath();
          ctx.roundRect(pad, posY + 2, btnW, btnH, 5);
          ctx.fill();
          ctx.stroke();
        } else {
          ctx.fillRect(pad, posY + 2, btnW, btnH);
          ctx.strokeRect(pad, posY + 2, btnW, btnH);
        }
        ctx.font = "bold 10px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
        ctx.fillStyle = canAdd ? "#f3e8ff" : "#64748b";
        ctx.textAlign = "center";
        ctx.fillText(this.name, pad + btnW / 2, posY + 17);
        ctx.restore();
      };
    }
    if (!node._stoiqoRemBtn) {
      const remBtn = node.addWidget(
        "button",
        "[-] Rimuovi Ultimo Box Testo",
        null,
        function() {
          if (node._stoiqoVisibleSlots > 1) {
            const wName = `text_${node._stoiqoVisibleSlots}`;
            const w = node.widgets.find((x) => x.name === wName);
            if (w) w.value = "";
            node._stoiqoVisibleSlots--;
            refreshSlots();
          }
        }
      );
      remBtn.serialize = false;
      node._stoiqoRemBtn = remBtn;
      remBtn.draw = function(ctx, n, width, posY, height) {
        if (this.hidden) return;
        const pad = 12;
        const btnW = width - pad * 2;
        const btnH = 22;
        ctx.save();
        ctx.fillStyle = "rgba(239, 68, 68, 0.15)";
        ctx.strokeStyle = "#ef4444";
        ctx.lineWidth = 1;
        if (ctx.roundRect) {
          ctx.beginPath();
          ctx.roundRect(pad, posY + 2, btnW, btnH, 4);
          ctx.fill();
          ctx.stroke();
        } else {
          ctx.fillRect(pad, posY + 2, btnW, btnH);
          ctx.strokeRect(pad, posY + 2, btnW, btnH);
        }
        ctx.font = "bold 10px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
        ctx.fillStyle = "#fca5a5";
        ctx.textAlign = "center";
        ctx.fillText("[-] Rimuovi Ultimo Box Testo", pad + btnW / 2, posY + 16);
        ctx.restore();
      };
    }
    const hudDups = node.widgets.filter((w) => w.name === "_stoiqo_token_hud");
    for (const extra of hudDups.slice(1)) {
      node.widgets.splice(node.widgets.indexOf(extra), 1);
    }
    let tokenHud = node.widgets.find((w) => w.name === "_stoiqo_token_hud");
    if (!tokenHud) {
      tokenHud = new StoiqoTokenHudWidget(node);
      node.addCustomWidget(tokenHud);
      node._stoiqo_hud = tokenHud;
    }
    const orderPriority = {
      "_stoiqo_slot_hdr_1": 1,
      "text_1": 1.5,
      "_stoiqo_slot_hdr_2": 2,
      "text_2": 2.5,
      "_stoiqo_slot_hdr_3": 3,
      "text_3": 3.5,
      "_stoiqo_slot_hdr_4": 4,
      "text_4": 4.5,
      "_stoiqo_slot_hdr_5": 5,
      "text_5": 5.5,
      "_stoiqo_slot_hdr_6": 6,
      "text_6": 6.5,
      "_stoiqo_slot_hdr_7": 7,
      "text_7": 7.5,
      "_stoiqo_slot_hdr_8": 8,
      "text_8": 8.5,
      "_stoiqo_add_btn": 9,
      "_stoiqo_rem_btn": 10,
      "separator": 11,
      "custom_separator": 12,
      "_stoiqo_settings_drawer": 13,
      "template": 14,
      "prefix": 15,
      "suffix": 16,
      "deduplicate_tags": 17,
      "clean_whitespace": 18,
      "convert_underscores": 19,
      "skip_empty": 20,
      "_stoiqo_token_hud": 25
    };
    node._stoiqoAddBtn.name_key = "_stoiqo_add_btn";
    node._stoiqoRemBtn.name_key = "_stoiqo_rem_btn";
    node.widgets.sort((a, b) => {
      const pa = orderPriority[a.name_key || a.name] || 99;
      const pb = orderPriority[b.name_key || b.name] || 99;
      return pa - pb;
    });
    const sepW = node.widgets.find((w) => w.name === "separator");
    if (sepW && !sepW._stoiqoHooked) {
      sepW._stoiqoHooked = true;
      const origSepCb = sepW.callback;
      sepW.callback = function() {
        if (origSepCb) origSepCb.apply(this, arguments);
        refreshSlots();
      };
    }
    const origConnectionsChange = node.onConnectionsChange;
    node.onConnectionsChange = function(type, index, isConnected, link_info) {
      if (origConnectionsChange) origConnectionsChange.apply(this, arguments);
      if (isConnected && node.inputs && node.inputs[index]) {
        const inpName = node.inputs[index].name;
        const m = inpName && inpName.match(/^text_(\d+)$/);
        if (m) {
          const slotNum = parseInt(m[1], 10);
          if (slotNum > (node._stoiqoVisibleSlots || 1)) {
            node._stoiqoVisibleSlots = slotNum;
            refreshSlots();
          }
        }
      }
      node.setDirtyCanvas(true, true);
    };
    const origMouseDown = node.onMouseDown;
    node.onMouseDown = function(event, localPos, graphCanvas) {
      for (const w of this.widgets || []) {
        if (w.mouse && w.mouse(event, localPos, this)) {
          return true;
        }
      }
      return origMouseDown ? origMouseDown.apply(this, arguments) : false;
    };
    node._stoiqoRefreshSlots = refreshSlots;
    refreshSlots();
  }
  const origGetExtraMenuOptions = nodeType.prototype.getExtraMenuOptions;
  nodeType.prototype.getExtraMenuOptions = function(_, options) {
    if (origGetExtraMenuOptions) origGetExtraMenuOptions.apply(this, arguments);
    options.push(
      null,
      // divider
      {
        content: "\u2195 Set All Boxes: Compact (44px)",
        callback: () => {
          this.properties = this.properties || {};
          this.properties.box_heights = this.properties.box_heights || {};
          for (let i = 1; i <= MAX_SLOTS; i++) {
            const w = this.widgets?.find((x) => x.name === `text_${i}`);
            if (w) {
              w._boxHeight = 44;
              this.properties.box_heights[w.name] = 44;
              if (w.inputEl) w.inputEl.style.height = "44px";
            }
          }
          if (this._stoiqoRefreshSlots) this._stoiqoRefreshSlots();
        }
      },
      {
        content: "\u2195 Set All Boxes: Standard (72px)",
        callback: () => {
          this.properties = this.properties || {};
          this.properties.box_heights = this.properties.box_heights || {};
          for (let i = 1; i <= MAX_SLOTS; i++) {
            const w = this.widgets?.find((x) => x.name === `text_${i}`);
            if (w) {
              w._boxHeight = 72;
              this.properties.box_heights[w.name] = 72;
              if (w.inputEl) w.inputEl.style.height = "72px";
            }
          }
          if (this._stoiqoRefreshSlots) this._stoiqoRefreshSlots();
        }
      },
      {
        content: "\u2195 Set All Boxes: Large (120px)",
        callback: () => {
          this.properties = this.properties || {};
          this.properties.box_heights = this.properties.box_heights || {};
          for (let i = 1; i <= MAX_SLOTS; i++) {
            const w = this.widgets?.find((x) => x.name === `text_${i}`);
            if (w) {
              w._boxHeight = 120;
              this.properties.box_heights[w.name] = 120;
              if (w.inputEl) w.inputEl.style.height = "120px";
            }
          }
          if (this._stoiqoRefreshSlots) this._stoiqoRefreshSlots();
        }
      },
      {
        content: "\u{1F504} Reset All Box Heights (Default)",
        callback: () => {
          this.properties = this.properties || {};
          this.properties.box_heights = {};
          for (let i = 1; i <= MAX_SLOTS; i++) {
            const w = this.widgets?.find((x) => x.name === `text_${i}`);
            if (w) {
              w._boxHeight = DEFAULT_BOX_HEIGHT;
              if (w.inputEl) w.inputEl.style.height = `${DEFAULT_BOX_HEIGHT}px`;
            }
          }
          if (this._stoiqoRefreshSlots) this._stoiqoRefreshSlots();
        }
      }
    );
  };
  const origCreated = nodeType.prototype.onNodeCreated;
  nodeType.prototype.onNodeCreated = function() {
    if (origCreated) origCreated.apply(this, arguments);
    initConcatNode(this);
  };
  const origConfigure = nodeType.prototype.onConfigure;
  nodeType.prototype.onConfigure = function() {
    if (origConfigure) origConfigure.apply(this, arguments);
    initConcatNode(this);
  };
  const origExecuted = nodeType.prototype.onExecuted;
  nodeType.prototype.onExecuted = function(message) {
    if (origExecuted) origExecuted.apply(this, arguments);
    if (message) {
      if (message.token_info && message.token_info.length > 0) {
        const info = message.token_info[0];
        if (this._stoiqo_hud) {
          this._stoiqo_hud.updateStats(info.words || 0, info.chars || 0, info.tokens || 0);
        }
      }
      if (message.slot_values && message.slot_values.length > 0) {
        const slotMap = message.slot_values[0];
        for (let i = 1; i <= MAX_SLOTS; i++) {
          const wName = `text_${i}`;
          const val = slotMap[wName];
          const w = this.widgets?.find((x) => x.name === wName);
          const inp = this.inputs ? this.inputs.find((x) => x.name === wName) : null;
          const isConnected = inp && inp.link != null;
          if (w && isConnected && val !== void 0) {
            w.value = val;
            if (w.inputEl) {
              w.inputEl.value = val;
              w.inputEl.style.borderColor = "#2997ff";
              w.inputEl.style.backgroundColor = "rgba(41, 151, 255, 0.08)";
            }
          }
        }
      }
      this.setDirtyCanvas(true, true);
    }
  };
}

// src_js/nodes/proSaverNode.js
import { api as api8 } from "../../../scripts/api.js";
function setupProSaverNode(nodeType, nodeData, appInstance) {
  const targetNames = [
    "StoiqoProImageSaverNode",
    "[STOIQO] Pro Image Saver & Metadata Hub"
  ];
  if (!targetNames.includes(nodeData.name)) return;
  class StoiqoSaverStatusWidget {
    constructor(node) {
      this.type = "custom";
      this.name = "_stoiqo_saver_hud";
      this.value = {};
      this.serialize = false;
      this.options = { serialize: false };
      this.node = node;
      this.lastSaveInfo = null;
      this.copiedButton = null;
      this.copyTimeout = null;
      this.buttonRects = {};
    }
    serializeValue() {
      return void 0;
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
        }, 2e3);
        this.node.setDirtyCanvas(true, false);
      } catch (err) {
        console.error("[STOIQO Pro Saver] Clipboard copy failed:", err);
      }
    }
    draw(ctx, node, width, y, height) {
      const padX = 14;
      const cardX = padX;
      const cardY = y + 4;
      const cardW = width - padX * 2;
      const cardH = 120;
      this.buttonRects = {};
      ctx.save();
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
        ctx.fillStyle = "#4a5568";
        ctx.font = "bold 11px system-ui, -apple-system, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("READY / AWAITING GENERATION", cardX + cardW / 2, cardY + 50);
        ctx.fillStyle = "#2d3748";
        ctx.font = "10px monospace";
        ctx.fillText("Saved files and metadata will appear here", cardX + cardW / 2, cardY + 74);
        ctx.restore();
        return;
      }
      const info = this.lastSaveInfo[0];
      const batchCount = this.lastSaveInfo.length;
      const badgeY = cardY + 16;
      if (info.privacy_mode) {
        ctx.fillStyle = "#f59e0b";
        ctx.font = "bold 10px system-ui, -apple-system, sans-serif";
        ctx.textAlign = "left";
        ctx.fillText("\u2713 SAVED \u2022 \u{1F6E1}\uFE0F PRIVACY (ZERO EXIF)", cardX + 12, badgeY);
      } else {
        ctx.fillStyle = "#10b981";
        ctx.font = "bold 10px system-ui, -apple-system, sans-serif";
        ctx.textAlign = "left";
        ctx.fillText("\u2713 SAVED", cardX + 12, badgeY);
      }
      const tagText = `${info.format || "IMG"} \u2022 ${info.width}x${info.height} \u2022 ${info.size_str || ""}${batchCount > 1 ? ` (+${batchCount - 1} more)` : ""}`;
      ctx.fillStyle = "#2997ff";
      ctx.font = "bold 10px monospace";
      ctx.textAlign = "right";
      ctx.fillText(tagText, cardX + cardW - 12, badgeY);
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
      const subfolderY = cardY + 58;
      ctx.fillStyle = "#718096";
      ctx.font = "10px monospace";
      let displaySub = `\u{1F4C1} ${info.subfolder || "output"}`;
      if (displaySub.length > maxNameLen + 4) {
        displaySub = displaySub.substring(0, maxNameLen + 1) + "...";
      }
      ctx.fillText(displaySub, cardX + 12, subfolderY);
      const btnY = cardY + 76;
      const btnH = 26;
      const btnGap = 6;
      const btnCount = 4;
      const totalGap = btnGap * (btnCount - 1);
      const btnW = Math.floor((cardW - 24 - totalGap) / btnCount);
      const folderDir = info.filepath ? info.filepath.substring(0, info.filepath.lastIndexOf(info.filename || "") - 1) || info.subfolder : info.subfolder || "output";
      const buttons = [
        {
          id: "copy_path",
          text: this.copiedButton === "copy_path" ? "\u2713 COPIED" : "\u{1F4CB} PATH",
          active: this.copiedButton === "copy_path",
          actionText: info.filepath
        },
        {
          id: "copy_name",
          text: this.copiedButton === "copy_name" ? "\u2713 COPIED" : "\u{1F4C4} NAME",
          active: this.copiedButton === "copy_name",
          actionText: info.filename
        },
        {
          id: "copy_folder",
          text: this.copiedButton === "copy_folder" ? "\u2713 COPIED" : "\u{1F4C1} DIR",
          active: this.copiedButton === "copy_folder",
          actionText: folderDir
        },
        {
          id: "open_folder",
          text: this.copiedButton === "open_folder" ? "\u2713 OPENED" : "\u{1F4C2} OPEN",
          active: this.copiedButton === "open_folder",
          actionText: folderDir
        }
      ];
      buttons.forEach((btn, idx) => {
        const bX = cardX + 12 + idx * (btnW + btnGap);
        this.buttonRects[btn.id] = { x: bX, y: btnY, w: btnW, h: btnH, data: btn.actionText };
        ctx.fillStyle = btn.active ? "#065f46" : btn.id === "open_folder" ? "#1e293b" : "#1a202c";
        ctx.strokeStyle = btn.active ? "#10b981" : btn.id === "open_folder" ? "#3b82f6" : "#2d3748";
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
        ctx.fillStyle = btn.active ? "#6ee7b7" : btn.id === "open_folder" ? "#93c5fd" : "#cbd5e1";
        ctx.font = "bold 9px system-ui, -apple-system, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(btn.text, bX + btnW / 2, btnY + 16);
      });
      ctx.restore();
    }
    mouse(event, pos, node) {
      if (event && (event.type === "pointerdown" || event.type === "mousedown")) {
        return this.onMouseDown(event, pos);
      }
      return false;
    }
    onMouseDown(event, localPos) {
      const x = localPos[0];
      const y = localPos[1];
      for (const [btnId, rect] of Object.entries(this.buttonRects)) {
        if (x >= rect.x && x <= rect.x + rect.w && y >= rect.y && y <= rect.y + rect.h) {
          if (btnId === "open_folder") {
            if (api8 && api8.fetchApi) {
              api8.fetchApi("/stoiqo/open_folder", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ folder_path: rect.data })
              }).catch((err) => console.warn("[STOIQO Pro Saver] Open folder error:", err));
            }
            this.copiedButton = "open_folder";
            if (this.copyTimeout) clearTimeout(this.copyTimeout);
            this.copyTimeout = setTimeout(() => {
              this.copiedButton = null;
              if (this.node) this.node.setDirtyCanvas(true, false);
            }, 1800);
            this.node.setDirtyCanvas(true, false);
            return true;
          } else {
            this.copyToClipboard(rect.data, btnId);
            return true;
          }
        }
      }
      return false;
    }
  }
  function ensureSaverHUD(node) {
    if (!node || !node.widgets) return;
    const existing = node.widgets.filter((w) => w.name === "_stoiqo_saver_hud");
    for (const extra of existing.slice(1)) {
      node.widgets.splice(node.widgets.indexOf(extra), 1);
    }
    let hud = existing[0];
    if (!hud) {
      hud = new StoiqoSaverStatusWidget(node);
      node.addCustomWidget(hud);
    }
    node._stoiqo_saver_hud = hud;
    if (!node._stoiqoMouseHooked) {
      node._stoiqoMouseHooked = true;
      const origOnMouseDown = node.onMouseDown;
      node.onMouseDown = function(e, localPos, graphCanvas) {
        if (this._stoiqo_saver_hud && this._stoiqo_saver_hud.onMouseDown(e, localPos)) {
          return true;
        }
        if (origOnMouseDown) {
          return origOnMouseDown.apply(this, arguments);
        }
        return false;
      };
    }
  }
  const onNodeCreated = nodeType.prototype.onNodeCreated;
  nodeType.prototype.onNodeCreated = function() {
    if (onNodeCreated) onNodeCreated.apply(this, arguments);
    this.hideOutputImages = true;
    this.imgs = null;
    this.images = null;
    ensureSaverHUD(this);
    if (!this.size || this.size[0] < 380) {
      this.size = [380, Math.max(this.size ? this.size[1] : 300, 360)];
    }
    const origOnExecuted = this.onExecuted;
    this.onExecuted = function(message) {
      if (origOnExecuted) {
        origOnExecuted.apply(this, arguments);
      }
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
  const onConfigure = nodeType.prototype.onConfigure;
  nodeType.prototype.onConfigure = function() {
    if (onConfigure) onConfigure.apply(this, arguments);
    ensureSaverHUD(this);
  };
  const origDrawBackground = nodeType.prototype.onDrawBackground;
  nodeType.prototype.onDrawBackground = function(ctx) {
    this.hideOutputImages = true;
    this.imgs = null;
    if (origDrawBackground) {
      origDrawBackground.apply(this, arguments);
    }
  };
}

// src_js/nodes/musicPromptNode.js
import { app as app7 } from "../../../scripts/app.js";
import { ComfyWidgets as ComfyWidgets4 } from "../../../scripts/widgets.js";
function setupMusicPromptNode(nodeType, nodeData, app11) {
  const musicTargetNames = [
    "StoiqoMusicPromptEngineNode",
    "[STOIQO] Music Prompt & Lyrics Engine (YuE2)",
    "[STOIQO] Music Prompt & Lyrics Engine"
  ];
  if (!musicTargetNames.includes(nodeData.name)) return;
  const MIN_NODE_WIDTH = 480;
  const SECTIONS = [
    { targetWidget: "idea", num: "1", title: "CONCEPT & CORE THEME", color: "#ff453a" },
    { targetWidget: "system_prompt", num: "2", title: "PRODUCER PERSONA & AI AGENT", color: "#ff9f0a" },
    { targetWidget: "genre", num: "3", title: "GENRE & ACOUSTICS", color: "#2997ff" },
    { targetWidget: "vocal_type", num: "4", title: "VOCALS & LANGUAGE", color: "#58b0ff" },
    { targetWidget: "structure", num: "5", title: "STRUCTURE & TEMPO", color: "#eab308" },
    { targetWidget: "custom_lyrics", num: "6", title: "CUSTOM LYRICS & DIRECTIVES (OPTIONAL)", color: "#ff9f0a" },
    { targetWidget: "seed", num: "7", title: "GENERATION & SAMPLING", color: "#30d158" }
  ];
  const MULTILINE_HEIGHTS = {
    "idea": 76,
    "custom_system_prompt": 68,
    "custom_lyrics": 72,
    "custom_directives": 54
  };
  const PLACEHOLDERS = {
    "idea": "Describe ANY musical vision, emotion, story, artist/band influence, or concept in free natural language (e.g. 'un brano baroque pop in italiano con clavicembalo e archi', 'cyberpunk industrial synthwave', 'fuga per organo')...",
    "custom_system_prompt": "Active only when system_prompt = 'Custom'. Write your custom AI music producer system instructions here...",
    "custom_lyrics": "Optional: Write or paste your own lyrics. Leave blank for full AI lyric generation...",
    "custom_directives": "Optional constraints (e.g. 'acoustic cello solo', 'no drums in verse 1')..."
  };
  function setupNodeInstance(node) {
    if (!node || !node.widgets) return;
    if (node.bgcolor === "#0e1218" || node.bgcolor === "#0b1411") delete node.bgcolor;
    if (node.color === "#18202c" || node.color === "#14251f") delete node.color;
    if (node.size && node.size[0] < MIN_NODE_WIDTH) {
      node.size[0] = MIN_NODE_WIDTH;
    }
    for (const wName of ["custom_lyrics", "custom_directives", "custom_system_prompt"]) {
      const w = node.widgets?.find((item) => item.name === wName);
      if (w) {
        const rawVal = String(w.value || "").trim().toLowerCase();
        if (["randomize", "fixed", "increment", "decrement"].includes(rawVal) || !isNaN(Number(rawVal)) && rawVal.length > 0) {
          w.value = "";
          if (w.inputEl) w.inputEl.value = "";
        }
      }
    }
    for (const [wName, hVal] of Object.entries(MULTILINE_HEIGHTS)) {
      const w = node.widgets.find((item) => item.name === wName);
      if (w) {
        w.computeSize = function(width) {
          return [width, hVal];
        };
        const applyInputStyles = (el) => {
          if (!el) return;
          el.style.boxSizing = "border-box";
          el.style.height = `${hVal}px`;
          el.style.minHeight = `${hVal}px`;
          el.style.maxHeight = `${hVal}px`;
          el.style.resize = "none";
          el.style.fontSize = "11.5px";
          el.style.lineHeight = "1.45";
          if (PLACEHOLDERS[wName]) {
            el.placeholder = PLACEHOLDERS[wName];
          }
        };
        if (w.inputEl) {
          applyInputStyles(w.inputEl);
        } else {
          let rawEl = null;
          Object.defineProperty(w, "inputEl", {
            configurable: true,
            enumerable: true,
            get() {
              return rawEl;
            },
            set(val) {
              rawEl = val;
              applyInputStyles(val);
            }
          });
        }
      }
    }
    function updateSystemPromptVisibility() {
      const sysPromptWidget2 = node.widgets.find((w) => w.name === "system_prompt");
      const customWidget = node.widgets.find((w) => w.name === "custom_system_prompt");
      if (!customWidget) return;
      const isCustomSelected = sysPromptWidget2 && String(sysPromptWidget2.value || "").includes("Custom");
      if (!customWidget._stoiqoOrigComputeSize) {
        customWidget._stoiqoOrigComputeSize = customWidget.computeSize;
        customWidget._stoiqoOrigDraw = customWidget.draw;
      }
      if (isCustomSelected) {
        customWidget.hidden = false;
        customWidget.computeSize = function(width) {
          return [width, MULTILINE_HEIGHTS["custom_system_prompt"] || 68];
        };
        if (customWidget._stoiqoOrigDraw) {
          customWidget.draw = customWidget._stoiqoOrigDraw;
        }
        if (customWidget.inputEl) {
          customWidget.inputEl.hidden = false;
          customWidget.inputEl.style.display = "";
        }
      } else {
        customWidget.hidden = true;
        customWidget.computeSize = function() {
          return [0, -4];
        };
        customWidget.draw = function() {
        };
        if (customWidget.inputEl) {
          customWidget.inputEl.hidden = true;
          customWidget.inputEl.style.display = "none";
        }
      }
      if (typeof node.computeSize === "function") {
        const computed = node.computeSize();
        node.size[0] = Math.max(node.size[0] || 0, MIN_NODE_WIDTH);
        node.size[1] = Math.max(node.size[1] || 0, Math.ceil(computed[1]));
      }
      node.setDirtyCanvas(true, true);
    }
    const sysPromptWidget = node.widgets.find((w) => w.name === "system_prompt");
    if (sysPromptWidget && !sysPromptWidget._stoiqoVisibilityHooked) {
      sysPromptWidget._stoiqoVisibilityHooked = true;
      const origSysCallback = sysPromptWidget.callback;
      sysPromptWidget.callback = function(val) {
        if (origSysCallback) origSysCallback.apply(this, arguments);
        updateSystemPromptVisibility();
      };
    }
    updateSystemPromptVisibility();
    node.widgets = node.widgets.filter((w) => !w.isStoiqoDivider);
    let trackInfoDisplay = node.widgets.find((w) => w.name === "preview_track_info");
    if (!trackInfoDisplay) {
      const trackDivider = new StoiqoSectionDividerWidget("8", "YUE2 OUTPUT: TRACK TELEMETRY & STYLE", "#2997ff");
      node.widgets.push(trackDivider);
      trackInfoDisplay = node.addWidget(
        "text",
        "preview_track_info",
        "\u{1F3B5} Waiting for generation...",
        function() {
        },
        { serialize: false }
      );
      if (trackInfoDisplay) {
        trackInfoDisplay.name = "preview_track_info";
        trackInfoDisplay.serialize = false;
        trackInfoDisplay.options = trackInfoDisplay.options || {};
        trackInfoDisplay.options.serialize = false;
        trackInfoDisplay.computeSize = function(width) {
          return [width, 24];
        };
      }
    }
    let styleDisplay = node.widgets.find((w) => w.name === "preview_style");
    if (!styleDisplay) {
      if (typeof ComfyWidgets4 !== "undefined" && ComfyWidgets4["STRING"]) {
        styleDisplay = ComfyWidgets4["STRING"](
          node,
          "preview_style",
          ["STRING", { multiline: true }],
          app11
        ).widget;
      } else {
        styleDisplay = node.addWidget(
          "customtext",
          "preview_style",
          "",
          function() {
          },
          { multiline: true }
        );
      }
      if (styleDisplay) {
        styleDisplay.name = "preview_style";
        styleDisplay.serialize = false;
        styleDisplay.options = styleDisplay.options || {};
        styleDisplay.options.serialize = false;
        styleDisplay.computeSize = function(width) {
          return [width, 64];
        };
        const styleBox = (el) => {
          if (!el) return;
          el.readOnly = true;
          el.placeholder = "YuE2 Style (Acoustic descriptors only, no lyrics) will appear here...";
          el.style.boxSizing = "border-box";
          el.style.height = "64px";
          el.style.minHeight = "64px";
          el.style.fontSize = "11px";
          el.style.lineHeight = "1.4";
          el.style.color = "#58b0ff";
          el.style.background = "rgba(15, 23, 42, 0.65)";
          el.style.fontFamily = "monospace, -apple-system, sans-serif";
        };
        if (styleDisplay.inputEl) styleBox(styleDisplay.inputEl);
        else {
          let rawEl = null;
          Object.defineProperty(styleDisplay, "inputEl", {
            configurable: true,
            enumerable: true,
            get() {
              return rawEl;
            },
            set(val) {
              rawEl = val;
              styleBox(val);
            }
          });
        }
      }
    }
    let lyricsDisplay = node.widgets.find((w) => w.name === "preview_lyrics");
    if (!lyricsDisplay) {
      const lyricsDivider = new StoiqoSectionDividerWidget("9", "YUE2 OUTPUT: STRUCTURED LYRICS", "#ff9f0a");
      node.widgets.push(lyricsDivider);
      if (typeof ComfyWidgets4 !== "undefined" && ComfyWidgets4["STRING"]) {
        lyricsDisplay = ComfyWidgets4["STRING"](
          node,
          "preview_lyrics",
          ["STRING", { multiline: true }],
          app11
        ).widget;
      } else {
        lyricsDisplay = node.addWidget(
          "customtext",
          "preview_lyrics",
          "",
          function() {
          },
          { multiline: true }
        );
      }
      if (lyricsDisplay) {
        lyricsDisplay.name = "preview_lyrics";
        lyricsDisplay.serialize = false;
        lyricsDisplay.options = lyricsDisplay.options || {};
        lyricsDisplay.options.serialize = false;
        lyricsDisplay.computeSize = function(width) {
          return [width, 110];
        };
        const lyricsBox = (el) => {
          if (!el) return;
          el.readOnly = true;
          el.placeholder = "YuE2 Lyrics ([Verse], [Chorus], [Bridge]) will appear here...";
          el.style.boxSizing = "border-box";
          el.style.height = "110px";
          el.style.minHeight = "110px";
          el.style.fontSize = "11px";
          el.style.lineHeight = "1.4";
          el.style.color = "#f472b6";
          el.style.background = "rgba(15, 23, 42, 0.65)";
          el.style.fontFamily = "monospace, -apple-system, sans-serif";
        };
        if (lyricsDisplay.inputEl) lyricsBox(lyricsDisplay.inputEl);
        else {
          let rawEl = null;
          Object.defineProperty(lyricsDisplay, "inputEl", {
            configurable: true,
            enumerable: true,
            get() {
              return rawEl;
            },
            set(val) {
              rawEl = val;
              lyricsBox(val);
            }
          });
        }
      }
    }
    let copyStyleBtn = node.widgets.find((w) => w._isMusicCopyStyle);
    if (!copyStyleBtn) {
      copyStyleBtn = node.addWidget(
        "button",
        "\u{1F4CB} Copy Style (YuE2 Descriptor)",
        null,
        function() {
          const sw = node.widgets?.find((w) => w.name === "preview_style");
          const val = sw ? sw.value || sw.inputEl && sw.inputEl.value || "" : "";
          if (val && navigator.clipboard) {
            navigator.clipboard.writeText(String(val));
            const orig = this.name;
            this.name = "\u2713 Style Copied!";
            node.setDirtyCanvas(true);
            setTimeout(() => {
              this.name = orig;
              node.setDirtyCanvas(true);
            }, 1800);
          }
        },
        { serialize: false }
      );
      copyStyleBtn._isMusicCopyStyle = true;
      copyStyleBtn.serialize = false;
      copyStyleBtn.options = { serialize: false };
    }
    let copyLyricsBtn = node.widgets.find((w) => w._isMusicCopyLyrics);
    if (!copyLyricsBtn) {
      copyLyricsBtn = node.addWidget(
        "button",
        "\u{1F4CB} Copy Lyrics (YuE2 Stanza)",
        null,
        function() {
          const lw = node.widgets?.find((w) => w.name === "preview_lyrics");
          const val = lw ? lw.value || lw.inputEl && lw.inputEl.value || "" : "";
          if (val && navigator.clipboard) {
            navigator.clipboard.writeText(String(val));
            const orig = this.name;
            this.name = "\u2713 Lyrics Copied!";
            node.setDirtyCanvas(true);
            setTimeout(() => {
              this.name = orig;
              node.setDirtyCanvas(true);
            }, 1800);
          }
        },
        { serialize: false }
      );
      copyLyricsBtn._isMusicCopyLyrics = true;
      copyLyricsBtn.serialize = false;
      copyLyricsBtn.options = { serialize: false };
    }
    let copyMetricsBtn = node.widgets.find((w) => w._isMusicCopyMetrics);
    if (!copyMetricsBtn) {
      copyMetricsBtn = node.addWidget(
        "button",
        "\u{1F4D0} Copy Syllabic Metric Analysis",
        null,
        function() {
          const lastInfo = node._lastMusicInfo;
          let report = "";
          if (lastInfo && lastInfo.metric_summary) {
            report = `\u{1F3B5} ${lastInfo.title || "Song"} \u2014 Lyrical Metric Analysis
Dominant Meter: ${lastInfo.dominant_meter || "N/A"}
Rhythmic Cadence Score: ${lastInfo.rhythmic_score || 85}%
Summary: ${lastInfo.metric_summary}

`;
            if (lastInfo.metrics && lastInfo.metrics.sections) {
              report += "Section Breakdown:\n";
              for (const sec of lastInfo.metrics.sections) {
                report += `  ${sec.section_name} (${sec.line_count} lines, avg ${sec.avg_syllables} syl/line \u2014 ${sec.dominant_meter})
`;
                for (const ln of sec.lines) {
                  report += `    \u2022 [${ln.syllables} syl] ${ln.text}
`;
                }
              }
            }
          } else {
            const tw = node.widgets?.find((w) => w.name === "preview_track_info");
            report = tw ? tw.value || "" : "No metrics available.";
          }
          if (report && navigator.clipboard) {
            navigator.clipboard.writeText(report);
            const orig = this.name;
            this.name = "\u2713 Metrics Copied!";
            node.setDirtyCanvas(true);
            setTimeout(() => {
              this.name = orig;
              node.setDirtyCanvas(true);
            }, 1800);
          }
        },
        { serialize: false }
      );
      copyMetricsBtn._isMusicCopyMetrics = true;
      copyMetricsBtn.serialize = false;
      copyMetricsBtn.options = { serialize: false };
    }
    if (typeof node.computeSize === "function") {
      const computed = node.computeSize();
      node.size[0] = Math.max(node.size[0] || 0, MIN_NODE_WIDTH);
      node.size[1] = Math.max(node.size[1] || 0, Math.ceil(computed[1]));
    }
    node.setDirtyCanvas(true, true);
  }
  const origOnCreated = nodeType.prototype.onNodeCreated;
  nodeType.prototype.onNodeCreated = function() {
    if (origOnCreated) origOnCreated.apply(this, arguments);
    setupNodeInstance(this);
  };
  const origOnConfigure = nodeType.prototype.onConfigure;
  nodeType.prototype.onConfigure = function() {
    if (origOnConfigure) origOnConfigure.apply(this, arguments);
    setupNodeInstance(this);
  };
  const origOnExecuted = nodeType.prototype.onExecuted;
  nodeType.prototype.onExecuted = function(message) {
    if (origOnExecuted) origOnExecuted.apply(this, arguments);
    if (message && message.music_info && message.music_info.length > 0) {
      const info = message.music_info[0];
      this._lastMusicInfo = info;
      const tw = this.widgets?.find((w) => w.name === "preview_track_info");
      const sw = this.widgets?.find((w) => w.name === "preview_style");
      const lw = this.widgets?.find((w) => w.name === "preview_lyrics");
      if (tw) {
        const durSec = Math.round(info.max_duration || 0);
        const durMin = Math.floor(durSec / 60);
        const durRemSec = String(durSec % 60).padStart(2, "0");
        const durStr = durSec > 0 ? `${durSec}s (~${durMin}:${durRemSec}m)` : "Dynamic";
        const modeStr = info.mode === "full" ? "Full Song" : info.mode === "melody" ? "Melody Lead" : "Vocal";
        const meterTag = info.dominant_meter ? ` | \u{1F4D0} ${info.dominant_meter}` : "";
        const cadenceTag = info.rhythmic_score ? ` (${info.rhythmic_score}%)` : "";
        const summaryText = `\u{1F3B5} ${info.title || "Untitled"} | \u23F1\uFE0F ${durStr} | \u{1F941} ${info.bpm || 120} BPM | \u{1F3B9} ${info.musical_key || "N/A"} | \u{1F39A}\uFE0F ${modeStr}${meterTag}${cadenceTag}`;
        tw.value = summaryText;
        if (tw.inputEl) tw.inputEl.value = summaryText;
      }
      if (sw && info.style) {
        sw.value = info.style;
        if (sw.inputEl) sw.inputEl.value = info.style;
      }
      if (lw && info.lyrics) {
        lw.value = info.lyrics;
        if (lw.inputEl) lw.inputEl.value = info.lyrics;
      }
      this.setDirtyCanvas(true, true);
    }
  };
}

// src_js/nodes/pipelineNodes.js
var CONFIGURATIONS = {
  // 1. Watermark & Logo Stamp
  StoiqoWatermarkNode: {
    minWidth: 380
  },
  // 2. Turbo Sampler & Direct Decoder
  StoiqoTurboSamplerNode: {
    minWidth: 420,
    multilineHeights: {
      positive: 72,
      negative: 48
    }
  },
  // 3. Universal Model Loader (All-in-One)
  StoiqoUniversalModelLoaderNode: {
    minWidth: 380
  },
  // 4. Smart Seed & Variance Controller
  StoiqoSeedControllerNode: {
    minWidth: 340
  },
  // 5. Inpaint Stitcher & Spatial Re-Roll
  StoiqoInpaintStitcherNode: {
    minWidth: 360
  },
  // 6. Pro Audio Saver (YuE2)
  StoiqoAudioSaverNode: {
    minWidth: 400,
    multilineHeights: {
      lyrics: 68,
      style: 48
    }
  },
  // 7. Pro Video Saver (MiniMax)
  StoiqoVideoSaverNode: {
    minWidth: 400,
    multilineHeights: {
      motion_prompt: 56
    }
  },
  // 8. Prompt Generator Engine
  StoiqoPromptGeneratorNode: {
    minWidth: 420,
    multilineHeights: {
      custom_modifications: 64,
      custom_system_prompt: 52
    }
  },
  // 9. Character Consistency Memory Bank (Lorebook & DNA)
  StoiqoCharacterMemoryNode: {
    minWidth: 420,
    multilineHeights: {
      physical_dna: 64,
      outfit_and_gear: 56,
      negative_constraints: 48,
      user_prompt: 48,
      custom_json_data: 48
    }
  }
};
function setupPipelineNodes(nodeType, nodeData, appInstance) {
  const nodeName = nodeData.name;
  const config = CONFIGURATIONS[nodeName];
  if (!config) return;
  function applyPipelineNodeLayout(node) {
    if (!node || !node.widgets) return;
    node.widgets = node.widgets.filter((w) => !w.isStoiqoDivider);
    if (config.minWidth && node.size && node.size[0] < config.minWidth) {
      node.size[0] = config.minWidth;
    }
    if (config.multilineHeights) {
      for (const [widgetName, hVal] of Object.entries(config.multilineHeights)) {
        const w = node.widgets.find((w2) => w2.name === widgetName);
        if (w) {
          w.computeSize = function(width) {
            return [width, hVal];
          };
          if (w.inputEl) {
            w.inputEl.style.boxSizing = "border-box";
            w.inputEl.style.height = `${hVal}px`;
            w.inputEl.style.minHeight = `${hVal}px`;
            w.inputEl.style.maxHeight = `${hVal}px`;
            w.inputEl.style.resize = "none";
            w.inputEl.style.fontSize = "11.5px";
            w.inputEl.style.lineHeight = "1.45";
          }
        }
      }
    }
    if (nodeName === "StoiqoPromptGeneratorNode") {
      const synIdx = node.widgets.findIndex((w) => w && w.name === "synthesized_prompt");
      if (synIdx !== -1) {
        const tw = node.widgets[synIdx];
        if (tw.inputEl && tw.inputEl.parentNode) {
          tw.inputEl.parentNode.removeChild(tw.inputEl);
        }
        node.widgets.splice(synIdx, 1);
      }
    }
    if (nodeName === "StoiqoAudioSaverNode") {
      createAudioPlayerWidget(node, null);
    }
    if (nodeName === "StoiqoVideoSaverNode") {
      createVideoPlayerWidget(node, null);
    }
    if (typeof node.computeSize === "function") {
      const computed = node.computeSize();
      const minW = config.minWidth || 360;
      const w = Math.max(node.size ? node.size[0] : minW, minW, Math.ceil(computed[0] || 0));
      const h = Math.max(node.size ? node.size[1] : 60, 60, Math.ceil(computed[1] || 0));
      if (typeof node.setSize === "function") {
        node.setSize([w, h]);
      } else {
        node.size = [w, h];
      }
    }
    if (node.setDirtyCanvas) {
      node.setDirtyCanvas(true, true);
    }
  }
  const origOnNodeCreated = nodeType.prototype.onNodeCreated;
  nodeType.prototype.onNodeCreated = function() {
    if (origOnNodeCreated) origOnNodeCreated.apply(this, arguments);
    applyPipelineNodeLayout(this);
  };
  const origOnConfigure = nodeType.prototype.onConfigure;
  nodeType.prototype.onConfigure = function() {
    if (origOnConfigure) origOnConfigure.apply(this, arguments);
    applyPipelineNodeLayout(this);
    if (this._stoiqoUpdateCustomPrompt) setTimeout(this._stoiqoUpdateCustomPrompt, 50);
  };
  if (nodeName === "StoiqoPromptGeneratorNode") {
    const origOnExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function(message) {
      if (origOnExecuted) origOnExecuted.apply(this, arguments);
      if (message && message.text) {
        const tw = this.widgets?.find((w) => w.name === "synthesized_prompt");
        if (tw) {
          const txt = Array.isArray(message.text) ? message.text.join("\n") : String(message.text || "");
          tw.value = txt;
          if (tw.inputEl) tw.inputEl.value = txt;
        }
        this.setDirtyCanvas(true, true);
      }
    };
  }
  if (nodeName === "StoiqoAudioSaverNode") {
    const origOnExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function(message) {
      if (origOnExecuted) origOnExecuted.apply(this, arguments);
      if (message && message.audio && message.audio.length > 0) {
        createAudioPlayerWidget(this, message.audio[0]);
      }
    };
    const origOnRemoved = nodeType.prototype.onRemoved;
    nodeType.prototype.onRemoved = function() {
      const w = this.widgets?.find((x) => x.name === "audio_player");
      if (w && w.element) {
        const a = w.element.querySelector("audio");
        if (a) {
          a.pause();
          a.src = "";
        }
      }
      if (origOnRemoved) origOnRemoved.apply(this, arguments);
    };
  }
  if (nodeName === "StoiqoVideoSaverNode") {
    const origOnExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function(message) {
      if (origOnExecuted) origOnExecuted.apply(this, arguments);
      const vData = message?.videos && message.videos[0] || message?.gifs && message.gifs[0] || message?.images && message.images[0];
      if (vData) {
        createVideoPlayerWidget(this, vData);
      }
    };
    const origOnRemoved = nodeType.prototype.onRemoved;
    nodeType.prototype.onRemoved = function() {
      const w = this.widgets?.find((x) => x.name === "video_player");
      if (w && w.videoEl) {
        w.videoEl.pause();
        w.videoEl.src = "";
      }
      if (origOnRemoved) origOnRemoved.apply(this, arguments);
    };
  }
}
function createAudioPlayerWidget(node, audioData) {
  if (!node || !node.addDOMWidget) return;
  let widget = node.widgets?.find((w) => w.name === "audio_player");
  if (!widget) {
    const container = document.createElement("div");
    container.className = "stoiqo-audio-player";
    container.style.display = "flex";
    container.style.flexDirection = "column";
    container.style.gap = "6px";
    container.style.padding = "8px 10px";
    container.style.background = "linear-gradient(135deg, rgba(18, 20, 29, 0.95), rgba(10, 12, 18, 0.98))";
    container.style.border = "1px solid rgba(41, 151, 255, 0.25)";
    container.style.borderRadius = "8px";
    container.style.boxShadow = "0 4px 16px rgba(0, 0, 0, 0.4)";
    container.style.fontFamily = "system-ui, -apple-system, sans-serif";
    container.style.color = "#e2e8f0";
    container.style.userSelect = "none";
    container.style.marginTop = "4px";
    const audio = document.createElement("audio");
    audio.preload = "metadata";
    const header = document.createElement("div");
    header.style.display = "flex";
    header.style.justifyContent = "space-between";
    header.style.alignItems = "center";
    header.style.fontSize = "11px";
    header.style.fontWeight = "600";
    header.style.color = "#2997ff";
    const titleEl = document.createElement("span");
    titleEl.textContent = audioData?.filename || "YuE2 / Suno Track Preview";
    titleEl.style.overflow = "hidden";
    titleEl.style.textOverflow = "ellipsis";
    titleEl.style.whiteSpace = "nowrap";
    titleEl.style.maxWidth = "220px";
    const timeEl = document.createElement("span");
    timeEl.textContent = "0:00 / 0:00";
    timeEl.style.fontFamily = "monospace";
    timeEl.style.color = "#94a3b8";
    header.appendChild(titleEl);
    header.appendChild(timeEl);
    const controls = document.createElement("div");
    controls.style.display = "flex";
    controls.style.alignItems = "center";
    controls.style.gap = "8px";
    const playBtn = document.createElement("button");
    playBtn.type = "button";
    playBtn.style.background = "#2997ff";
    playBtn.style.border = "none";
    playBtn.style.borderRadius = "50%";
    playBtn.style.width = "28px";
    playBtn.style.height = "28px";
    playBtn.style.display = "flex";
    playBtn.style.alignItems = "center";
    playBtn.style.justifyContent = "center";
    playBtn.style.cursor = "pointer";
    playBtn.style.color = "#ffffff";
    playBtn.style.flexShrink = "0";
    playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`;
    const progress = document.createElement("input");
    progress.type = "range";
    progress.min = "0";
    progress.max = "100";
    progress.value = "0";
    progress.style.flex = "1";
    progress.style.accentColor = "#2997ff";
    progress.style.cursor = "pointer";
    progress.style.height = "4px";
    controls.appendChild(playBtn);
    controls.appendChild(progress);
    container.appendChild(header);
    container.appendChild(controls);
    container.appendChild(audio);
    const formatTime = (secs) => {
      if (!secs || isNaN(secs)) return "0:00";
      const m = Math.floor(secs / 60);
      const s = Math.floor(secs % 60);
      return `${m}:${s < 10 ? "0" : ""}${s}`;
    };
    playBtn.onclick = (e) => {
      e.stopPropagation();
      if (audio.paused) {
        audio.play();
        playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>`;
      } else {
        audio.pause();
        playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`;
      }
    };
    audio.ontimeupdate = () => {
      if (!audio.duration) return;
      progress.value = audio.currentTime / audio.duration * 100;
      timeEl.textContent = `${formatTime(audio.currentTime)} / ${formatTime(audio.duration)}`;
    };
    audio.onended = () => {
      playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`;
      progress.value = 0;
    };
    progress.oninput = (e) => {
      e.stopPropagation();
      if (audio.duration) {
        audio.currentTime = progress.value / 100 * audio.duration;
      }
    };
    widget = node.addDOMWidget("audio_player", "AUDIO_PLAYER", container, {
      serialize: false,
      hideOnZoom: false
    });
    widget.serialize = false;
    widget.computeSize = function(width) {
      return [width, 68];
    };
    widget.audioEl = audio;
    widget.titleEl = titleEl;
  }
  if (audioData && widget && widget.audioEl) {
    const url = `/view?filename=${encodeURIComponent(audioData.filename)}&subfolder=${encodeURIComponent(audioData.subfolder || "")}&type=${encodeURIComponent(audioData.type || "output")}`;
    widget.audioEl.src = url;
    if (widget.titleEl) widget.titleEl.textContent = audioData.filename;
    if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
  }
}
function createVideoPlayerWidget(node, videoData) {
  if (!node || !node.addDOMWidget) return;
  let widget = node.widgets?.find((w) => w.name === "video_player");
  if (!widget) {
    const container = document.createElement("div");
    container.className = "stoiqo-video-player";
    container.style.display = "flex";
    container.style.flexDirection = "column";
    container.style.gap = "6px";
    container.style.padding = "8px 10px";
    container.style.background = "linear-gradient(135deg, rgba(16, 20, 30, 0.96), rgba(8, 10, 16, 0.98))";
    container.style.border = "1px solid rgba(41, 151, 255, 0.3)";
    container.style.borderRadius = "8px";
    container.style.boxShadow = "0 4px 16px rgba(0, 0, 0, 0.5)";
    container.style.fontFamily = "system-ui, -apple-system, sans-serif";
    container.style.color = "#e2e8f0";
    container.style.userSelect = "none";
    container.style.marginTop = "4px";
    const video = document.createElement("video");
    video.preload = "auto";
    video.playsInline = true;
    video.muted = true;
    video.loop = true;
    video.style.width = "100%";
    video.style.maxHeight = "190px";
    video.style.objectFit = "contain";
    video.style.display = "block";
    video.style.borderRadius = "6px";
    video.style.background = "#040608";
    video.style.border = "1px solid rgba(255, 255, 255, 0.08)";
    const header = document.createElement("div");
    header.style.display = "flex";
    header.style.justifyContent = "space-between";
    header.style.alignItems = "center";
    header.style.fontSize = "11px";
    header.style.fontWeight = "600";
    header.style.color = "#2997ff";
    const titleEl = document.createElement("span");
    titleEl.textContent = videoData?.filename || "MiniMax / Wan Video Preview";
    titleEl.style.overflow = "hidden";
    titleEl.style.textOverflow = "ellipsis";
    titleEl.style.whiteSpace = "nowrap";
    titleEl.style.maxWidth = "200px";
    const timeEl = document.createElement("span");
    timeEl.textContent = "00:00.00 / 00:00.00 (F: 0/0)";
    timeEl.style.fontFamily = "monospace";
    timeEl.style.fontSize = "10.5px";
    timeEl.style.color = "#94a3b8";
    header.appendChild(titleEl);
    header.appendChild(timeEl);
    const progress = document.createElement("input");
    progress.type = "range";
    progress.min = "0";
    progress.max = "1000";
    progress.value = "0";
    progress.style.width = "100%";
    progress.style.accentColor = "#2997ff";
    progress.style.cursor = "pointer";
    progress.style.height = "5px";
    progress.style.margin = "2px 0";
    const controls = document.createElement("div");
    controls.style.display = "flex";
    controls.style.alignItems = "center";
    controls.style.justifyContent = "space-between";
    controls.style.gap = "6px";
    controls.style.fontSize = "11px";
    const leftControls = document.createElement("div");
    leftControls.style.display = "flex";
    leftControls.style.alignItems = "center";
    leftControls.style.gap = "6px";
    const createBtn = (text, title, padding = "3px 8px") => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.title = title;
      btn.textContent = text;
      btn.style.background = "rgba(255, 255, 255, 0.06)";
      btn.style.border = "1px solid rgba(255, 255, 255, 0.15)";
      btn.style.borderRadius = "4px";
      btn.style.padding = padding;
      btn.style.cursor = "pointer";
      btn.style.color = "#cbd5e1";
      btn.style.fontSize = "10.5px";
      btn.style.fontFamily = "inherit";
      btn.style.transition = "all 0.15s ease";
      btn.onmouseenter = () => btn.style.background = "rgba(41, 151, 255, 0.15)";
      btn.onmouseleave = () => {
        if (!btn.dataset.active) btn.style.background = "rgba(255, 255, 255, 0.06)";
      };
      return btn;
    };
    const prevFrameBtn = createBtn("\u23EE -1F", "Step backward 1 frame");
    const nextFrameBtn = createBtn("+1F \u23ED", "Step forward 1 frame");
    const playBtn = document.createElement("button");
    playBtn.type = "button";
    playBtn.title = "Play / Pause";
    playBtn.style.background = "#2997ff";
    playBtn.style.border = "none";
    playBtn.style.borderRadius = "50%";
    playBtn.style.width = "28px";
    playBtn.style.height = "28px";
    playBtn.style.display = "flex";
    playBtn.style.alignItems = "center";
    playBtn.style.justifyContent = "center";
    playBtn.style.cursor = "pointer";
    playBtn.style.color = "#ffffff";
    playBtn.style.flexShrink = "0";
    playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`;
    const loopBtn = createBtn("\u{1F501} Loop", "Toggle Continuous Loop");
    loopBtn.dataset.active = "true";
    loopBtn.style.background = "rgba(41, 151, 255, 0.2)";
    loopBtn.style.borderColor = "rgba(41, 151, 255, 0.5)";
    loopBtn.style.color = "#2997ff";
    leftControls.appendChild(prevFrameBtn);
    leftControls.appendChild(playBtn);
    leftControls.appendChild(nextFrameBtn);
    leftControls.appendChild(loopBtn);
    const rightControls = document.createElement("div");
    rightControls.style.display = "flex";
    rightControls.style.alignItems = "center";
    rightControls.style.gap = "6px";
    const speedBtn = createBtn("1.0x", "Playback Speed (1.0x / 0.5x / 0.25x)", "3px 6px");
    const muteBtn = createBtn("\u{1F507}", "Mute / Unmute", "3px 6px");
    const popoutBtn = createBtn("\u2197", "Open video in new tab", "3px 6px");
    rightControls.appendChild(speedBtn);
    rightControls.appendChild(muteBtn);
    rightControls.appendChild(popoutBtn);
    controls.appendChild(leftControls);
    controls.appendChild(rightControls);
    container.appendChild(header);
    container.appendChild(video);
    container.appendChild(progress);
    container.appendChild(controls);
    let activeFps = 24;
    let activeTotalFrames = 0;
    const formatTime = (secs) => {
      if (!secs || isNaN(secs)) return "00:00.00";
      const m = Math.floor(secs / 60);
      const s = Math.floor(secs % 60);
      const ms = Math.floor(secs % 1 * 100);
      return `${m < 10 ? "0" : ""}${m}:${s < 10 ? "0" : ""}${s}.${ms < 10 ? "0" : ""}${ms}`;
    };
    const updateDisplay = () => {
      const dur = video.duration || 0;
      const cur = video.currentTime || 0;
      const curFrame = Math.round(cur * activeFps);
      const totFrames = activeTotalFrames || Math.round(dur * activeFps);
      timeEl.textContent = `${formatTime(cur)} / ${formatTime(dur)} (F: ${curFrame}/${totFrames})`;
      if (dur > 0) {
        progress.value = cur / dur * 1e3;
      }
    };
    playBtn.onclick = (e) => {
      e.stopPropagation();
      if (video.paused) {
        video.play();
        playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>`;
      } else {
        video.pause();
        playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`;
      }
    };
    prevFrameBtn.onclick = (e) => {
      e.stopPropagation();
      video.pause();
      playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`;
      video.currentTime = Math.max(0, video.currentTime - 1 / activeFps);
      updateDisplay();
    };
    nextFrameBtn.onclick = (e) => {
      e.stopPropagation();
      video.pause();
      playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`;
      video.currentTime = Math.min(video.duration || 0, video.currentTime + 1 / activeFps);
      updateDisplay();
    };
    loopBtn.onclick = (e) => {
      e.stopPropagation();
      video.loop = !video.loop;
      if (video.loop) {
        loopBtn.dataset.active = "true";
        loopBtn.style.background = "rgba(41, 151, 255, 0.2)";
        loopBtn.style.borderColor = "rgba(41, 151, 255, 0.5)";
        loopBtn.style.color = "#2997ff";
      } else {
        delete loopBtn.dataset.active;
        loopBtn.style.background = "rgba(255, 255, 255, 0.06)";
        loopBtn.style.borderColor = "rgba(255, 255, 255, 0.15)";
        loopBtn.style.color = "#cbd5e1";
      }
    };
    const SPEEDS = [1, 0.5, 0.25];
    let speedIdx = 0;
    speedBtn.onclick = (e) => {
      e.stopPropagation();
      speedIdx = (speedIdx + 1) % SPEEDS.length;
      const newSpeed = SPEEDS[speedIdx];
      video.playbackRate = newSpeed;
      speedBtn.textContent = `${newSpeed}x`;
    };
    muteBtn.onclick = (e) => {
      e.stopPropagation();
      video.muted = !video.muted;
      muteBtn.textContent = video.muted ? "\u{1F507}" : "\u{1F50A}";
    };
    popoutBtn.onclick = (e) => {
      e.stopPropagation();
      if (video.src) window.open(video.src, "_blank");
    };
    video.ontimeupdate = () => {
      updateDisplay();
    };
    video.onended = () => {
      if (!video.loop) {
        playBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`;
        progress.value = 0;
      }
    };
    progress.oninput = (e) => {
      e.stopPropagation();
      if (video.duration) {
        video.currentTime = progress.value / 1e3 * video.duration;
        updateDisplay();
      }
    };
    widget = node.addDOMWidget("video_player", "VIDEO_PLAYER", container, {
      serialize: false,
      hideOnZoom: false
    });
    widget.serialize = false;
    widget.computeSize = function(width) {
      return [width, 275];
    };
    widget.videoEl = video;
    widget.titleEl = titleEl;
    widget.setFps = (fps) => {
      activeFps = fps || 24;
    };
    widget.setTotalFrames = (tf) => {
      activeTotalFrames = tf || 0;
    };
  }
  if (videoData && widget && widget.videoEl) {
    const url = `/view?filename=${encodeURIComponent(videoData.filename)}&subfolder=${encodeURIComponent(videoData.subfolder || "")}&type=${encodeURIComponent(videoData.type || "output")}`;
    widget.videoEl.src = url;
    widget.videoEl.load();
    if (widget.setFps) widget.setFps(videoData.fps);
    if (widget.setTotalFrames) widget.setTotalFrames(videoData.total_frames);
    if (widget.titleEl) widget.titleEl.textContent = videoData.filename;
    if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
  }
}

// src_js/nodes/loraStackNode.js
import { app as app8 } from "../../../scripts/app.js";
import { api as api9 } from "../../../scripts/api.js";
var LORA_NODE_NAMES = ["StoiqoLoraStackNode", "[STOIQO] LoRA Stack"];
var MIN_WIDTH2 = 400;
var PAD2 = 6;
var HEAD_H2 = 24;
var ROW_H2 = 28;
var BTN_H2 = 30;
var STEP = 0.05;
var _loraListCache = null;
async function fetchLoraList(force = false) {
  if (_loraListCache && !force) return _loraListCache;
  try {
    const resp = await api9.fetchApi("/stoiqo/loras");
    const data = await resp.json();
    _loraListCache = Array.isArray(data.loras) ? data.loras : [];
  } catch (err) {
    console.warn("[STOIQO LoRA Stack] Unable to load LoRA list:", err);
    _loraListCache = [];
  }
  return _loraListCache;
}
function roundRect2(ctx, x, y, w, h, r) {
  if (ctx.roundRect) {
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, r);
  } else {
    ctx.beginPath();
    ctx.rect(x, y, w, h);
  }
}
function baseName2(path) {
  const parts = String(path).split(/[\\/]/);
  const file = parts[parts.length - 1] || "";
  return file.replace(/\.(safetensors|ckpt|pt|pth|bin)$/i, "");
}
function fitText2(ctx, text, maxW) {
  if (ctx.measureText(text).width <= maxW) return text;
  let t = text;
  while (t.length > 1 && ctx.measureText(t + "\u2026").width > maxW) {
    t = t.slice(0, -1);
  }
  return t + "\u2026";
}
var StoiqoLoraStackWidget = class {
  constructor(node, storeWidget) {
    this.type = "custom";
    this.name = "_stoiqo_lora_stack";
    this.node = node;
    this.store = storeWidget;
    this.serialize = false;
    this.options = { serialize: false };
    this.loras = [];
    this.hits = [];
    this.lastClick = 0;
  }
  // The UI state lives in the hidden store widget; this widget carries no value of its own.
  get value() {
    return "";
  }
  set value(_v) {
  }
  rowsCount() {
    return Math.max(this.loras.length, 1);
  }
  totalHeight() {
    return PAD2 + HEAD_H2 + this.rowsCount() * ROW_H2 + 6 + BTN_H2 + PAD2;
  }
  computeSize(width) {
    return [width, this.totalHeight()];
  }
  computeLayoutSize() {
    const h = this.totalHeight();
    return { minHeight: h, maxHeight: h, minWidth: MIN_WIDTH2 };
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
    this.loras = parsed.filter((it) => it && typeof it.name === "string" && it.name).map((it) => {
      const sm = Number.isFinite(Number(it.strength)) ? Number(it.strength) : 1;
      const sc = Number.isFinite(Number(it.strength_clip)) ? Number(it.strength_clip) : sm;
      return {
        name: it.name,
        strength: sm,
        strength_clip: sc,
        enabled: it.enabled !== false,
        block_filter: it.block_filter || "All Blocks (Standard)"
      };
    });
  }
  sync() {
    if (this.store) {
      this.store.value = JSON.stringify(
        this.loras.map((l) => ({
          name: l.name,
          strength: l.strength,
          strength_clip: l.strength_clip !== void 0 ? l.strength_clip : l.strength,
          enabled: l.enabled,
          block_filter: l.block_filter || "All Blocks (Standard)"
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
    node.setSize([Math.max(node.size[0], MIN_WIDTH2), sz[1]]);
  }
  draw(ctx, node, width, posY) {
    this.hits = [];
    const x0 = 10;
    const w = width - 20;
    let y = posY + PAD2;
    ctx.save();
    ctx.textBaseline = "middle";
    const activeCount = this.loras.filter((l) => l.enabled).length;
    ctx.font = "bold 11px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
    ctx.textAlign = "left";
    ctx.fillStyle = "#94a3b8";
    ctx.fillText(`LoRA Stack \xB7 ${activeCount}/${this.loras.length} active`, x0 + 2, y + HEAD_H2 / 2);
    const allLabel = activeCount > 0 ? "Disable all" : "Enable all";
    ctx.font = "10px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
    const allW = ctx.measureText(allLabel).width + 16;
    const allX = x0 + w - allW;
    if (this.loras.length > 0) {
      ctx.fillStyle = "rgba(255,255,255,0.07)";
      roundRect2(ctx, allX, y + 3, allW, HEAD_H2 - 6, 4);
      ctx.fill();
      ctx.fillStyle = "#cbd5e1";
      ctx.textAlign = "center";
      ctx.fillText(allLabel, allX + allW / 2, y + HEAD_H2 / 2);
      this.hits.push({
        x: allX,
        y: y + 3,
        w: allW,
        h: HEAD_H2 - 6,
        action: () => {
          const target = activeCount === 0;
          this.loras.forEach((l) => {
            l.enabled = target;
          });
          this.sync();
        }
      });
    }
    y += HEAD_H2;
    if (this.loras.length === 0) {
      ctx.font = "italic 11px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
      ctx.fillStyle = "#64748b";
      ctx.textAlign = "center";
      ctx.fillText('No LoRAs \u2014 click "+ Add LoRA"', x0 + w / 2, y + ROW_H2 / 2);
      y += ROW_H2;
    } else {
      this.loras.forEach((lora, idx) => {
        const rY = y + 2;
        const rH = ROW_H2 - 4;
        const on = lora.enabled;
        ctx.fillStyle = on ? "rgba(45, 212, 191, 0.08)" : "rgba(255, 255, 255, 0.04)";
        roundRect2(ctx, x0, rY, w, rH, 5);
        ctx.fill();
        ctx.strokeStyle = on ? "rgba(45, 212, 191, 0.35)" : "rgba(255, 255, 255, 0.08)";
        ctx.lineWidth = 1;
        ctx.stroke();
        const tW = 28, tH = 14;
        const tX = x0 + 6, tY = rY + (rH - tH) / 2;
        ctx.fillStyle = on ? "#2dd4bf" : "#475569";
        roundRect2(ctx, tX, tY, tW, tH, 7);
        ctx.fill();
        ctx.fillStyle = "#0f172a";
        ctx.beginPath();
        ctx.arc(on ? tX + tW - 7 : tX + 7, tY + tH / 2, 5, 0, Math.PI * 2);
        ctx.fill();
        this.hits.push({
          x: tX - 2,
          y: rY,
          w: tW + 4,
          h: rH,
          action: () => {
            lora.enabled = !lora.enabled;
            this.sync();
          }
        });
        const upW = 15, dnW = 15, btnW = 16, valW = 52, gearW = 18, xW = 16, gap = 2;
        const ctrlW = upW + gap + dnW + gap + btnW + valW + btnW + gap + gearW + gap + xW;
        const cX = x0 + w - ctrlW - 4;
        const cY = rY + 3;
        const cH = rH - 6;
        const drawBtn = (bx, bw, label, color, bg = "rgba(255,255,255,0.08)", font = "bold 11px sans-serif") => {
          ctx.fillStyle = bg;
          roundRect2(ctx, bx, cY, bw, cH, 3);
          ctx.fill();
          ctx.fillStyle = color;
          ctx.font = font;
          ctx.textAlign = "center";
          ctx.fillText(label, bx + bw / 2, cY + cH / 2 + 0.5);
        };
        drawBtn(cX, upW, "\u25B2", idx > 0 ? "#cbd5e1" : "#475569", "rgba(255,255,255,0.05)", "9px sans-serif");
        this.hits.push({
          x: cX,
          y: cY,
          w: upW,
          h: cH,
          action: () => {
            if (idx > 0) {
              const tmp = this.loras[idx - 1];
              this.loras[idx - 1] = this.loras[idx];
              this.loras[idx] = tmp;
              this.sync();
            }
          }
        });
        const dnX = cX + upW + gap;
        drawBtn(dnX, dnW, "\u25BC", idx < this.loras.length - 1 ? "#cbd5e1" : "#475569", "rgba(255,255,255,0.05)", "9px sans-serif");
        this.hits.push({
          x: dnX,
          y: cY,
          w: dnW,
          h: cH,
          action: () => {
            if (idx < this.loras.length - 1) {
              const tmp = this.loras[idx + 1];
              this.loras[idx + 1] = this.loras[idx];
              this.loras[idx] = tmp;
              this.sync();
            }
          }
        });
        const minusX = dnX + dnW + gap;
        drawBtn(minusX, btnW, "\u2212", "#e2e8f0");
        this.hits.push({
          x: minusX,
          y: cY,
          w: btnW,
          h: cH,
          action: (ev) => {
            if (ev && ev.shiftKey) {
              lora.strength_clip = Math.round(((lora.strength_clip ?? lora.strength) - STEP) * 100) / 100;
            } else {
              lora.strength = Math.round((lora.strength - STEP) * 100) / 100;
              if (lora.strength_clip === void 0) lora.strength_clip = lora.strength;
            }
            this.sync();
          }
        });
        const vX = minusX + btnW;
        ctx.fillStyle = "rgba(0,0,0,0.3)";
        ctx.fillRect(vX, cY, valW, cH);
        ctx.fillStyle = on ? "#f1f5f9" : "#64748b";
        ctx.font = "10px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
        ctx.textAlign = "center";
        const isDecoupled = lora.strength_clip !== void 0 && Math.abs(lora.strength_clip - lora.strength) > 1e-3;
        const valLabel = isDecoupled ? `${lora.strength.toFixed(1)}|${lora.strength_clip.toFixed(1)}` : lora.strength.toFixed(2);
        ctx.fillText(valLabel, vX + valW / 2, cY + cH / 2 + 0.5);
        this.hits.push({
          x: vX,
          y: cY,
          w: valW,
          h: cH,
          action: (ev) => {
            const isShift = ev && ev.shiftKey;
            const promptTitle = isShift ? "CLIP Strength" : "Model Strength (Shift+click for CLIP)";
            const curVal = isShift ? lora.strength_clip ?? lora.strength : lora.strength;
            app8.canvas.prompt(promptTitle, curVal, (v) => {
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
          }
        });
        const plusX = vX + valW;
        drawBtn(plusX, btnW, "+", "#e2e8f0");
        this.hits.push({
          x: plusX,
          y: cY,
          w: btnW,
          h: cH,
          action: (ev) => {
            if (ev && ev.shiftKey) {
              lora.strength_clip = Math.round(((lora.strength_clip ?? lora.strength) + STEP) * 100) / 100;
            } else {
              lora.strength = Math.round((lora.strength + STEP) * 100) / 100;
              if (lora.strength_clip === void 0) lora.strength_clip = lora.strength;
            }
            this.sync();
          }
        });
        const hasCustomBlock = Boolean(lora.block_filter && !lora.block_filter.startsWith("All Blocks"));
        const hasCustomRowCfg = isDecoupled || hasCustomBlock;
        const gearX = plusX + btnW + gap;
        drawBtn(
          gearX,
          gearW,
          "\u2699",
          hasCustomRowCfg ? "#58b0ff" : "#cbd5e1",
          hasCustomRowCfg ? "rgba(41,151,255,0.18)" : "rgba(255,255,255,0.06)",
          "11px sans-serif"
        );
        this.hits.push({
          x: gearX,
          y: cY,
          w: gearW,
          h: cH,
          action: (ev) => this.showRowMenu(ev, lora, idx)
        });
        const xX = gearX + gearW + gap;
        drawBtn(xX, xW, "\u2715", "#f87171");
        this.hits.push({
          x: xX,
          y: cY,
          w: xW,
          h: cH,
          action: () => {
            this.loras.splice(idx, 1);
            this.sync();
          }
        });
        const nX = tX + tW + 8;
        const nW = cX - nX - 6;
        ctx.font = "12px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
        ctx.textAlign = "left";
        ctx.fillStyle = on ? "#e2e8f0" : "#64748b";
        const blockTag = hasCustomBlock ? lora.block_filter.includes("OUT") ? " [OUT]" : lora.block_filter.includes("IN/MID") ? " [IN/MID]" : " [MID]" : "";
        ctx.fillText(fitText2(ctx, baseName2(lora.name) + blockTag, nW), nX, rY + rH / 2 + 0.5);
        this.hits.push({
          x: nX,
          y: rY,
          w: nW,
          h: rH,
          action: (ev) => {
            if (ev && ev.button === 2) {
              this.showRowMenu(ev, lora, idx);
            } else {
              this.pickLora(ev, (picked) => {
                lora.name = picked;
                this.sync();
              }, lora.name);
            }
          }
        });
        y += ROW_H2;
      });
    }
    y += 6;
    ctx.fillStyle = "rgba(45, 212, 191, 0.14)";
    roundRect2(ctx, x0, y, w, BTN_H2 - 4, 6);
    ctx.fill();
    ctx.strokeStyle = "rgba(45, 212, 191, 0.55)";
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.fillStyle = "#2dd4bf";
    ctx.font = "bold 12px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("+ Aggiungi LoRA", x0 + w / 2, y + (BTN_H2 - 4) / 2 + 0.5);
    this.hits.push({
      x: x0,
      y,
      w,
      h: BTN_H2 - 4,
      action: (ev) => this.pickLora(ev, (picked) => {
        this.loras.push({ name: picked, strength: 1, enabled: true });
        this.sync();
      })
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
        content: `\u{1F50D} Change LoRA...`,
        callback: (v, opts, e) => {
          this.pickLora(e, (picked) => {
            lora.name = picked;
            this.sync();
          }, lora.name);
        }
      },
      {
        content: `\u2696\uFE0F Edit CLIP Strength (${(lora.strength_clip ?? lora.strength).toFixed(2)})`,
        callback: (_v, _opts, e) => {
          app8.canvas.prompt("CLIP Strength", lora.strength_clip ?? lora.strength, (val) => {
            const num = parseFloat(val);
            if (Number.isFinite(num)) {
              lora.strength_clip = Math.round(Math.max(-10, Math.min(10, num)) * 100) / 100;
              this.sync();
            }
          }, e);
        }
      },
      {
        content: `\u{1F9F1} Block Filter (${lora.block_filter || "All Blocks"})`,
        has_submenu: true,
        callback: (_v, _opts, e, menu) => {
          const filters = [
            "All Blocks (Standard)",
            "Style / Texture Only (OUT Blocks)",
            "Character / Structure Only (IN/MID Blocks)",
            "Face & Pose Focused (MID Block)"
          ];
          new LG.ContextMenu(
            filters.map((f) => ({
              content: lora.block_filter === f || !lora.block_filter && f.startsWith("All") ? `\u2713 ${f}` : f,
              value: f
            })),
            {
              event: e,
              parentMenu: menu,
              callback: (chosen) => {
                if (chosen && chosen.value) {
                  lora.block_filter = chosen.value;
                  this.sync();
                }
              }
            }
          );
          return true;
        }
      },
      {
        content: `\u{1F3F7}\uFE0F View / Copy Trigger Words`,
        callback: async (_v, _opts, e) => {
          try {
            const resp = await api9.fetchApi(`/stoiqo/lora_info?name=${encodeURIComponent(lora.name)}`);
            const data = await resp.json();
            const triggers = Array.isArray(data.triggers) ? data.triggers : [];
            if (triggers.length > 0) {
              const trigStr = triggers.join(", ");
              if (navigator.clipboard) {
                navigator.clipboard.writeText(trigStr).catch(() => {
                });
              }
              alert(`Trigger words for '${baseName2(lora.name)}':

${trigStr}

(Copied to clipboard!)`);
            } else {
              alert(`No trigger words found in metadata or sidecars for '${baseName2(lora.name)}'.`);
            }
          } catch (err) {
            alert(`Error reading metadata for '${baseName2(lora.name)}'.`);
          }
        }
      },
      {
        content: `\u2715 Remove`,
        callback: () => {
          this.loras.splice(idx, 1);
          this.sync();
        }
      }
    ];
    new LG.ContextMenu(items, { event, title: baseName2(lora.name) });
  }
  async pickLora(event, onPick, currentName = "") {
    const list = await fetchLoraList(false);
    const LG = window.LiteGraph;
    if (!list || !list.length) {
      if (LG && LG.ContextMenu) {
        new LG.ContextMenu([{ content: "Nessuna LoRA trovata in models/loras", disabled: true }], { event });
      }
      return;
    }
    openSearchablePicker({
      title: "Scegli LoRA",
      icon: "\u26A1",
      items: list,
      current: currentName,
      onRefresh: async () => {
        return await fetchLoraList(true);
      },
      onPick: (chosen) => {
        if (chosen) onPick(chosen);
      }
    });
  }
  mouse(event, pos, node) {
    if (!event || event.type !== "pointerdown" && event.type !== "mousedown") return false;
    if (!pos) return false;
    const now = performance.now();
    if (now - this.lastClick < 150) return true;
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
};
function setupLoraStackNodeUI(node) {
  if (!node) return;
  if (node.size && node.size[0] < MIN_WIDTH2) node.size[0] = MIN_WIDTH2;
  if (node.widgets) {
    const dups = node.widgets.filter((w) => w.name === "_stoiqo_lora_stack");
    for (const extra of dups.slice(1)) {
      node.widgets.splice(node.widgets.indexOf(extra), 1);
    }
  }
  let loraWidget = node.widgets ? node.widgets.find((w) => w.name === "_stoiqo_lora_stack") : null;
  if (!loraWidget) {
    const store = node.widgets ? node.widgets.find((w) => w.name === "lora_stack") : null;
    for (const wName of ["lora_stack", "block_filter"]) {
      const hw = node.widgets ? node.widgets.find((w) => w.name === wName) : null;
      if (hw) {
        hw.hidden = true;
        hw.computeSize = () => [0, -4];
        hw.draw = () => {
        };
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
function setupLoraStackNode(nodeType, nodeData, appInstance) {
  if (!LORA_NODE_NAMES.includes(nodeData.name)) return;
  const origCreated = nodeType.prototype.onNodeCreated;
  nodeType.prototype.onNodeCreated = function() {
    if (origCreated) origCreated.apply(this, arguments);
    setupLoraStackNodeUI(this);
  };
  const origConfigure = nodeType.prototype.onConfigure;
  nodeType.prototype.onConfigure = function() {
    if (origConfigure) origConfigure.apply(this, arguments);
    setupLoraStackNodeUI(this);
  };
}

// src_js/nodes/promptGeneratorNode.js
import { app as app9 } from "../../../scripts/app.js";

// src_js/utils/promptStudioModal.js
import { api as api10 } from "../../../scripts/api.js";
var modalContainer = null;
var activeNodeRef = null;
var currentKind = "styles";
var currentItemList = [];
var currentItemData = null;
var isNewMode = false;
var originalName = "";
var KIND_METADATA = {
  styles: {
    title: "Artistic Styles",
    icon: "\u{1F3A8}",
    badge: "LAYER 3",
    widgetName: "prompt_style",
    fallbackWidgetName: "artistic_style"
  },
  personas: {
    title: "Cognitive Personas",
    icon: "\u{1F9E0}",
    badge: "LAYER 1",
    widgetName: "system_prompt",
    fallbackWidgetName: "system_prompt"
  },
  types: {
    title: "Output Formats",
    icon: "\u{1F4D0}",
    badge: "LAYER 2",
    widgetName: "prompt_type",
    fallbackWidgetName: "prompt_type"
  }
};
function ensureStyles2() {
  if (document.getElementById("stoiqo-prompt-studio-styles")) return;
  const styleEl = document.createElement("style");
  styleEl.id = "stoiqo-prompt-studio-styles";
  styleEl.textContent = `
        .stoiqo-modal-backdrop {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(4, 5, 8, 0.78);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #f1f5f9;
        }
        .stoiqo-modal-backdrop.open {
            opacity: 1;
        }
        .stoiqo-modal-box {
            background: #0a0c12;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            width: 860px;
            max-width: 94vw;
            height: 84vh;
            max-height: 860px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 30px 80px rgba(0, 0, 0, 0.85), 0 0 1px 1px rgba(255, 255, 255, 0.05);
            overflow: hidden;
            transform: scale(0.96);
            transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .stoiqo-modal-backdrop.open .stoiqo-modal-box {
            transform: scale(1);
        }
        .stoiqo-modal-header {
            padding: 14px 20px;
            background: rgba(18, 22, 34, 0.7);
            border-bottom: 1px solid rgba(255, 255, 255, 0.07);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .stoiqo-modal-title {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 15px;
            font-weight: 700;
            letter-spacing: -0.3px;
            color: #ffffff;
        }
        .stoiqo-modal-badge {
            font-size: 10px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
            background: rgba(41, 151, 255, 0.18);
            border: 1px solid rgba(41, 151, 255, 0.45);
            color: #58b0ff;
            letter-spacing: 0.5px;
        }
        .stoiqo-modal-close-btn {
            background: transparent;
            border: none;
            color: #94a3b8;
            font-size: 20px;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 6px;
            line-height: 1;
            transition: background 0.15s, color 0.15s;
        }
        .stoiqo-modal-close-btn:hover {
            background: rgba(255, 255, 255, 0.08);
            color: #ffffff;
        }
        .stoiqo-tabs-bar {
            display: flex;
            background: #0d0f17;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            padding: 0 16px;
            gap: 8px;
        }
        .stoiqo-tab-btn {
            padding: 10px 16px;
            background: transparent;
            border: none;
            border-bottom: 2px solid transparent;
            color: #94a3b8;
            font-size: 12.5px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: color 0.15s, border-color 0.15s;
        }
        .stoiqo-tab-btn:hover {
            color: #f1f5f9;
        }
        .stoiqo-tab-btn.active {
            color: #2997ff;
            border-bottom-color: #2997ff;
        }
        .stoiqo-subnav-toolbar {
            padding: 10px 16px;
            background: rgba(14, 17, 26, 0.6);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            flex-wrap: wrap;
        }
        .stoiqo-search-filter-wrap {
            position: relative;
            width: 220px;
            flex-shrink: 0;
        }
        .stoiqo-search-input {
            width: 100%;
            background: #10141f;
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 6px;
            color: #f1f5f9;
            padding: 6px 10px;
            font-size: 12px;
            box-sizing: border-box;
            outline: none;
            transition: border-color 0.15s, background 0.15s;
        }
        .stoiqo-search-input:focus {
            border-color: #2997ff;
            background: #141926;
        }
        .stoiqo-selector-group {
            display: flex;
            align-items: center;
            gap: 10px;
            flex: 1;
            min-width: 280px;
        }
        .stoiqo-item-select {
            background: #131722;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 6px;
            color: #f1f5f9;
            padding: 6px 12px;
            font-size: 13px;
            outline: none;
            max-width: 420px;
            flex: 1;
            cursor: pointer;
        }
        .stoiqo-item-select optgroup {
            background: #0b0f19;
            color: #58b0ff;
            font-weight: 700;
            padding: 4px 6px;
            font-size: 11.5px;
        }
        .stoiqo-item-select option {
            background: #131722;
            color: #f1f5f9;
            font-weight: normal;
            padding: 3px 6px;
            font-size: 12.5px;
        }
        .stoiqo-item-select:focus {
            border-color: #2997ff;
        }
        .stoiqo-item-type-tag {
            font-size: 10.5px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 4px;
        }
        .stoiqo-item-type-tag.core {
            background: rgba(41, 151, 255, 0.14);
            border: 1px solid rgba(41, 151, 255, 0.4);
            color: #58b0ff;
        }
        .stoiqo-item-type-tag.custom {
            background: rgba(48, 209, 88, 0.14);
            border: 1px solid rgba(48, 209, 88, 0.4);
            color: #30d158;
        }
        .stoiqo-toolbar-actions {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .stoiqo-btn-sm {
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            border: 1px solid transparent;
            transition: background 0.15s, border-color 0.15s;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .stoiqo-btn-secondary {
            background: rgba(255, 255, 255, 0.06);
            border-color: rgba(255, 255, 255, 0.1);
            color: #e2e8f0;
        }
        .stoiqo-btn-secondary:hover:not(:disabled) {
            background: rgba(255, 255, 255, 0.12);
            color: #ffffff;
        }
        .stoiqo-btn-danger {
            background: rgba(255, 69, 58, 0.12);
            border-color: rgba(255, 69, 58, 0.35);
            color: #ff453a;
        }
        .stoiqo-btn-danger:hover:not(:disabled) {
            background: rgba(255, 69, 58, 0.22);
            border-color: #ff453a;
        }
        .stoiqo-btn-danger:disabled, .stoiqo-btn-secondary:disabled {
            opacity: 0.35;
            cursor: not-allowed;
        }
        .stoiqo-modal-content {
            flex: 1;
            overflow-y: auto;
            padding: 18px 22px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .stoiqo-form-row {
            display: flex;
            gap: 14px;
        }
        .stoiqo-field-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
            flex: 1;
        }
        .stoiqo-label {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            color: #94a3b8;
        }
        .stoiqo-input {
            background: #11141e;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            color: #f8fafc;
            padding: 8px 12px;
            font-size: 13px;
            outline: none;
            transition: border-color 0.15s;
        }
        .stoiqo-input:focus {
            border-color: #2997ff;
            background: #141824;
        }
        .stoiqo-textarea-wrap {
            display: flex;
            flex-direction: column;
            gap: 6px;
            flex: 1;
            min-height: 220px;
        }
        .stoiqo-textarea {
            background: #08090d;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            color: #e2e8f0;
            padding: 12px 14px;
            font-family: 'JetBrains Mono', SFMono-Regular, Consolas, Menlo, monospace;
            font-size: 12.5px;
            line-height: 1.55;
            outline: none;
            resize: none;
            flex: 1;
            min-height: 200px;
        }
        .stoiqo-textarea:focus {
            border-color: #2997ff;
        }
        .stoiqo-modal-footer {
            padding: 14px 20px;
            background: rgba(14, 17, 26, 0.7);
            border-top: 1px solid rgba(255, 255, 255, 0.07);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .stoiqo-footer-info {
            font-size: 12px;
            color: #64748b;
        }
        .stoiqo-footer-actions {
            display: flex;
            gap: 10px;
        }
        .stoiqo-btn-primary {
            background: #2997ff;
            color: #ffffff;
            border: 1px solid #0077ed;
            padding: 8px 18px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.15s, transform 0.05s;
        }
        .stoiqo-btn-primary:hover {
            background: #1f87eb;
        }
        .stoiqo-btn-primary:active {
            transform: scale(0.98);
        }
        .stoiqo-toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #111827;
            border: 1px solid rgba(48, 209, 88, 0.45);
            color: #30d158;
            padding: 10px 16px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
            z-index: 10001;
            display: flex;
            align-items: center;
            gap: 8px;
            opacity: 0;
            transform: translateY(10px);
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            pointer-events: none;
        }
        .stoiqo-toast.show {
            opacity: 1;
            transform: translateY(0);
        }
    `;
  document.head.appendChild(styleEl);
}
function showToast(message, isError = false) {
  let toast = document.getElementById("stoiqo-studio-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "stoiqo-studio-toast";
    toast.className = "stoiqo-toast";
    document.body.appendChild(toast);
  }
  toast.textContent = (isError ? "\u26A0\uFE0F " : "\u2705 ") + message;
  toast.style.borderColor = isError ? "rgba(255, 69, 58, 0.45)" : "rgba(48, 209, 88, 0.45)";
  toast.style.color = isError ? "#ff453a" : "#30d158";
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 3200);
}
function openPromptStudioModal({ node = null, kind = "styles", activeName = null, isNew = false }) {
  ensureStyles2();
  activeNodeRef = node;
  currentKind = kind;
  if (!activeName && node && node.widgets) {
    const meta = KIND_METADATA[kind];
    const w = node.widgets.find((item) => item.name === meta.widgetName || item.name === meta.fallbackWidgetName);
    if (w && w.value) {
      activeName = w.value;
    }
  }
  if (!modalContainer) {
    buildModalDOM();
  }
  modalContainer.classList.add("open");
  switchTab(kind, activeName).then(() => {
    if (isNew) {
      startNewItem();
    }
  });
}
function closePromptStudioModal() {
  if (modalContainer) {
    modalContainer.classList.remove("open");
  }
}
function buildModalDOM() {
  modalContainer = document.createElement("div");
  modalContainer.className = "stoiqo-modal-backdrop";
  modalContainer.addEventListener("click", (e) => {
    if (e.target === modalContainer) closePromptStudioModal();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modalContainer && modalContainer.classList.contains("open")) {
      closePromptStudioModal();
    }
  });
  modalContainer.innerHTML = `
        <div class="stoiqo-modal-box">
            <div class="stoiqo-modal-header">
                <div class="stoiqo-modal-title">
                    <span id="stoiqo-modal-icon">\u{1F3A8}</span>
                    <span id="stoiqo-modal-heading">STOIQO Prompt Studio</span>
                    <span class="stoiqo-modal-badge" id="stoiqo-modal-badge">LAYER 3</span>
                </div>
                <button class="stoiqo-modal-close-btn" id="stoiqo-modal-close">\u2715</button>
            </div>

            <div class="stoiqo-tabs-bar">
                <button class="stoiqo-tab-btn" data-kind="styles">\u{1F3A8} Artistic Styles (Layer 3)</button>
                <button class="stoiqo-tab-btn" data-kind="personas">\u{1F9E0} Cognitive Personas (Layer 1)</button>
                <button class="stoiqo-tab-btn" data-kind="types">\u{1F4D0} Output Formats (Layer 2)</button>
            </div>

            <div class="stoiqo-subnav-toolbar">
                <div class="stoiqo-search-filter-wrap">
                    <input class="stoiqo-input stoiqo-search-input" id="stoiqo-filter-search" placeholder="\u{1F50D} Cerca per nome o categoria..." autocomplete="off" />
                </div>
                <div class="stoiqo-selector-group">
                    <select class="stoiqo-item-select" id="stoiqo-item-dropdown"></select>
                    <span class="stoiqo-item-type-tag" id="stoiqo-item-badge">CORE</span>
                </div>
                <div class="stoiqo-toolbar-actions">
                    <button class="stoiqo-btn-sm stoiqo-btn-secondary" id="stoiqo-btn-new">\u2795 Nuovo</button>
                    <button class="stoiqo-btn-sm stoiqo-btn-secondary" id="stoiqo-btn-dup">\u{1F4CB} Duplica</button>
                    <button class="stoiqo-btn-sm stoiqo-btn-danger" id="stoiqo-btn-del">\u{1F5D1}\uFE0F Elimina</button>
                </div>
            </div>

            <div class="stoiqo-modal-content">
                <div class="stoiqo-form-row">
                    <div class="stoiqo-field-group" style="flex: 2;">
                        <label class="stoiqo-label">Display Name (e.g. Category // Style Name)</label>
                        <input class="stoiqo-input" id="stoiqo-input-name" placeholder="Name..." />
                    </div>
                    <div class="stoiqo-field-group" style="flex: 1;">
                        <label class="stoiqo-label">Category</label>
                        <input class="stoiqo-input" id="stoiqo-input-category" placeholder="e.g. Anime, Photo, Custom" />
                    </div>
                    <div class="stoiqo-field-group" style="flex: 0.5;">
                        <label class="stoiqo-label">Priority Order</label>
                        <input class="stoiqo-input" id="stoiqo-input-order" type="number" value="150" />
                    </div>
                </div>

                <!-- Dynamic Layer Specific Form Fields -->
                <div id="stoiqo-extra-fields"></div>

                <div class="stoiqo-textarea-wrap">
                    <label class="stoiqo-label">Prompt Directive Body (Markdown SSOT)</label>
                    <textarea class="stoiqo-textarea" id="stoiqo-textarea-body" placeholder="Markdown instructions, mandates, and prompt engineering directives..."></textarea>
                </div>
            </div>

            <div class="stoiqo-modal-footer">
                <div class="stoiqo-footer-info" id="stoiqo-footer-info">Editing SSOT markdown file.</div>
                <div class="stoiqo-footer-actions">
                    <button class="stoiqo-btn-sm stoiqo-btn-secondary" id="stoiqo-btn-cancel">Cancel</button>
                    <button class="stoiqo-btn-primary" id="stoiqo-btn-save">\u{1F4BE} Save & Apply to Canvas</button>
                </div>
            </div>
        </div>
    `;
  document.body.appendChild(modalContainer);
  modalContainer.querySelector("#stoiqo-modal-close").addEventListener("click", closePromptStudioModal);
  modalContainer.querySelector("#stoiqo-btn-cancel").addEventListener("click", closePromptStudioModal);
  modalContainer.querySelectorAll(".stoiqo-tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      switchTab(btn.getAttribute("data-kind"));
    });
  });
  modalContainer.querySelector("#stoiqo-item-dropdown").addEventListener("change", (e) => {
    loadItemDetails(e.target.value);
  });
  modalContainer.querySelector("#stoiqo-filter-search").addEventListener("input", (e) => {
    populateDropdown(currentItemList, null, e.target.value);
  });
  modalContainer.querySelector("#stoiqo-btn-new").addEventListener("click", () => {
    startNewItem();
  });
  modalContainer.querySelector("#stoiqo-btn-dup").addEventListener("click", () => {
    duplicateCurrentItem();
  });
  modalContainer.querySelector("#stoiqo-btn-del").addEventListener("click", () => {
    deleteCurrentItem();
  });
  modalContainer.querySelector("#stoiqo-btn-save").addEventListener("click", () => {
    saveCurrentItem();
  });
}
async function switchTab(kind, targetItemName = null) {
  currentKind = kind;
  const meta = KIND_METADATA[kind];
  modalContainer.querySelector("#stoiqo-modal-heading").textContent = `STOIQO Prompt Studio \u2014 ${meta.title}`;
  modalContainer.querySelector("#stoiqo-modal-icon").textContent = meta.icon;
  modalContainer.querySelector("#stoiqo-modal-badge").textContent = meta.badge;
  const filterInput = modalContainer.querySelector("#stoiqo-filter-search");
  if (filterInput) filterInput.value = "";
  modalContainer.querySelectorAll(".stoiqo-tab-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.getAttribute("data-kind") === kind);
  });
  renderExtraFields(kind);
  try {
    const resp = await api10.fetchApi(`/stoiqo/api/prompt_engine/list?kind=${kind}`);
    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
    }
    const data = await resp.json();
    if (data && data.status === "ok" && Array.isArray(data.items)) {
      currentItemList = data.items;
      populateDropdown(currentItemList, targetItemName);
      return;
    }
  } catch (err) {
    console.warn("[STOIQO Studio] API route not reached:", err);
    let fallbackChoices = [];
    if (activeNodeRef && activeNodeRef.widgets) {
      const w = activeNodeRef.widgets.find((item) => item.name === meta.widgetName || item.name === meta.fallbackWidgetName);
      if (w && w.options && Array.isArray(w.options.values)) {
        fallbackChoices = w.options.values;
      }
    }
    if (fallbackChoices.length > 0) {
      currentItemList = fallbackChoices.map((name, idx) => ({
        name,
        category: name.includes("//") ? name.split("//")[0].trim() : idx < 10 ? "Core" : "Generale",
        order: idx,
        is_core: idx < 10,
        filename: `${name.toLowerCase().replace(/[^a-z0-9]+/g, "_")}.md`
      }));
      populateDropdown(currentItemList, targetItemName);
      showToast("Server in attesa di riavvio. Riavvia ComfyUI per registrare le nuove route API del backend.", true);
    } else {
      showToast("Server in attesa di riavvio: riavvia ComfyUI per sincronizzare il backend.", true);
    }
  }
}
function renderExtraFields(kind) {
  const container = modalContainer.querySelector("#stoiqo-extra-fields");
  if (kind === "styles") {
    container.innerHTML = `
            <div class="stoiqo-form-row">
                <div class="stoiqo-field-group">
                    <label class="stoiqo-label">Medium Type</label>
                    <input class="stoiqo-input" id="stoiqo-style-medium-type" placeholder="e.g. 2D Japanese Cel Animation or 35mm Film" />
                </div>
                <div class="stoiqo-field-group">
                    <label class="stoiqo-label">Prohibited Terms (for non-photo)</label>
                    <input class="stoiqo-input" id="stoiqo-style-prohibited" placeholder="camera lenses, 35mm, RAW photo, realistic skin pores" />
                </div>
            </div>
            <div class="stoiqo-form-row">
                <div class="stoiqo-field-group">
                    <label class="stoiqo-label">Tag Injection (&lt;TAGS&gt;)</label>
                    <input class="stoiqo-input" id="stoiqo-style-tag-injection" placeholder="e.g. anime, cel shading, 2d illustration" />
                </div>
                <div class="stoiqo-field-group">
                    <label class="stoiqo-label">Negative Injection (&lt;NEGATIVE&gt;)</label>
                    <input class="stoiqo-input" id="stoiqo-style-negative-injection" placeholder="e.g. photograph, realistic, raw photo" />
                </div>
            </div>
        `;
  } else if (kind === "personas") {
    container.innerHTML = `
            <div class="stoiqo-form-row">
                <div class="stoiqo-field-group">
                    <label class="stoiqo-label">Temperature</label>
                    <input class="stoiqo-input" id="stoiqo-persona-temp" type="number" step="0.05" min="0.1" max="1.5" value="0.65" />
                </div>
                <div class="stoiqo-field-group">
                    <label class="stoiqo-label">Max New Tokens</label>
                    <input class="stoiqo-input" id="stoiqo-persona-tokens" type="number" step="64" min="128" max="4096" value="1024" />
                </div>
                <div class="stoiqo-field-group">
                    <label class="stoiqo-label">Top P</label>
                    <input class="stoiqo-input" id="stoiqo-persona-top-p" type="number" step="0.05" min="0.1" max="1.0" value="0.90" />
                </div>
                <div class="stoiqo-field-group">
                    <label class="stoiqo-label">Repetition Penalty</label>
                    <input class="stoiqo-input" id="stoiqo-persona-rep" type="number" step="0.05" min="1.0" max="2.0" value="1.15" />
                </div>
            </div>
        `;
  } else {
    container.innerHTML = "";
  }
}
function populateDropdown(items, targetItemName = null, filterQuery = "") {
  const dropdown = modalContainer.querySelector("#stoiqo-item-dropdown");
  dropdown.innerHTML = "";
  const query = (filterQuery || "").trim().toLowerCase();
  const filtered = query ? items.filter(
    (it) => it.name && it.name.toLowerCase().includes(query) || it.category && it.category.toLowerCase().includes(query) || Array.isArray(it.aliases) && it.aliases.some((a) => String(a).toLowerCase().includes(query))
  ) : items;
  if (filtered.length === 0) {
    const emptyOpt = document.createElement("option");
    emptyOpt.value = "";
    emptyOpt.textContent = `Nessun risultato per "${filterQuery}"`;
    dropdown.appendChild(emptyOpt);
    return;
  }
  const groups = {};
  for (const item of filtered) {
    let cat = item.category ? item.category.trim() : item.is_core ? "Core Presets" : "Stili Generali";
    if (!cat) cat = "Stili Generali";
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(item);
  }
  let selectedVal = null;
  for (const [catName, catItems] of Object.entries(groups)) {
    const optgroup = document.createElement("optgroup");
    optgroup.label = `${catName} (${catItems.length})`;
    for (const item of catItems) {
      const opt = document.createElement("option");
      opt.value = item.name;
      opt.textContent = `${item.is_core ? "\u{1F512}" : "\u2728"} ${item.name}`;
      optgroup.appendChild(opt);
      if (targetItemName && (item.name === targetItemName || item.aliases?.includes(targetItemName))) {
        selectedVal = item.name;
      }
    }
    dropdown.appendChild(optgroup);
  }
  if (!selectedVal && filtered.length > 0) {
    selectedVal = filtered[0].name;
  }
  if (selectedVal) {
    dropdown.value = selectedVal;
    loadItemDetails(selectedVal);
  }
}
async function loadItemDetails(name) {
  if (!name) return;
  try {
    const resp = await api10.fetchApi(`/stoiqo/api/prompt_engine/get?kind=${currentKind}&name=${encodeURIComponent(name)}`);
    if (resp.ok) {
      const data = await resp.json();
      if (data && data.status === "ok") {
        currentItemData = data;
        isNewMode = false;
        originalName = data.name;
        populateForm(data);
        return;
      }
    }
  } catch (err) {
    console.warn("[STOIQO Studio] Failed to fetch item details:", err);
  }
  const item = currentItemList.find((x) => x.name === name) || { name };
  currentItemData = {
    name: item.name,
    filename: item.filename || `${name}.md`,
    is_core: Boolean(item.is_core),
    frontmatter: {
      name: item.name,
      category: item.category || "",
      order: item.order || 100
    },
    body: `Direttive per ${name}...
(Riavvia il server ComfyUI per sincronizzare il file da disco).`
  };
  isNewMode = false;
  originalName = name;
  populateForm(currentItemData);
}
function populateForm(data) {
  const fm = data.frontmatter || {};
  modalContainer.querySelector("#stoiqo-input-name").value = data.name || "";
  modalContainer.querySelector("#stoiqo-input-category").value = fm.category || "";
  modalContainer.querySelector("#stoiqo-input-order").value = fm.order ?? 150;
  modalContainer.querySelector("#stoiqo-textarea-body").value = data.body || "";
  const isCore = Boolean(data.is_core);
  const badge = modalContainer.querySelector("#stoiqo-item-badge");
  badge.textContent = isCore ? "PRESET CORE (MODIFICABILE)" : "STILE UTENTE (MODIFICABILE)";
  badge.className = `stoiqo-item-type-tag ${isCore ? "core" : "custom"}`;
  modalContainer.querySelector("#stoiqo-btn-del").disabled = isCore;
  const kindFolder = currentKind === "styles" ? "styles" : currentKind === "personas" ? "personas" : "types";
  modalContainer.querySelector("#stoiqo-footer-info").textContent = `\u{1F4C4} File su disco: core/image/${kindFolder}/${data.filename || "custom.md"}`;
  if (currentKind === "styles") {
    const medEl = modalContainer.querySelector("#stoiqo-style-medium-type");
    const proEl = modalContainer.querySelector("#stoiqo-style-prohibited");
    const tagEl = modalContainer.querySelector("#stoiqo-style-tag-injection");
    const negEl = modalContainer.querySelector("#stoiqo-style-negative-injection");
    if (medEl) medEl.value = fm.medium_type || "";
    if (proEl) proEl.value = fm.prohibited || "";
    if (tagEl) tagEl.value = fm.tag_injection || "";
    if (negEl) negEl.value = fm.negative_injection || "";
  } else if (currentKind === "personas") {
    const tempEl = modalContainer.querySelector("#stoiqo-persona-temp");
    const tokEl = modalContainer.querySelector("#stoiqo-persona-tokens");
    const topPEl = modalContainer.querySelector("#stoiqo-persona-top-p");
    const repEl = modalContainer.querySelector("#stoiqo-persona-rep");
    if (tempEl) tempEl.value = fm.temperature ?? 0.65;
    if (tokEl) tokEl.value = fm.max_new_tokens ?? 1024;
    if (topPEl) topPEl.value = fm.top_p ?? 0.9;
    if (repEl) repEl.value = fm.repetition_penalty ?? 1.15;
  }
}
function startNewItem() {
  isNewMode = true;
  originalName = "";
  currentItemData = null;
  modalContainer.querySelector("#stoiqo-input-name").value = "";
  modalContainer.querySelector("#stoiqo-input-category").value = "Custom";
  modalContainer.querySelector("#stoiqo-input-order").value = 200;
  modalContainer.querySelector("#stoiqo-textarea-body").value = "";
  const badge = modalContainer.querySelector("#stoiqo-item-badge");
  badge.textContent = "NEW DEFINITION";
  badge.className = "stoiqo-item-type-tag custom";
  modalContainer.querySelector("#stoiqo-btn-del").disabled = true;
  modalContainer.querySelector("#stoiqo-footer-info").textContent = "Creating new definition.";
  modalContainer.querySelector("#stoiqo-input-name").focus();
}
function duplicateCurrentItem() {
  const currentName = modalContainer.querySelector("#stoiqo-input-name").value;
  isNewMode = true;
  originalName = "";
  currentItemData = null;
  modalContainer.querySelector("#stoiqo-input-name").value = currentName ? `${currentName} (Copy)` : "New Style Copy";
  modalContainer.querySelector("#stoiqo-input-order").value = 200;
  const badge = modalContainer.querySelector("#stoiqo-item-badge");
  badge.textContent = "DUPLICATED (NEW)";
  badge.className = "stoiqo-item-type-tag custom";
  modalContainer.querySelector("#stoiqo-btn-del").disabled = true;
  modalContainer.querySelector("#stoiqo-footer-info").textContent = "Duplicate created. Customize and save.";
  modalContainer.querySelector("#stoiqo-input-name").focus();
}
async function deleteCurrentItem() {
  const name = modalContainer.querySelector("#stoiqo-input-name").value;
  if (!name) return;
  if (!confirm(`Are you sure you want to permanently delete '${name}'?`)) {
    return;
  }
  try {
    const resp = await api10.fetchApi("/stoiqo/api/prompt_engine/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kind: currentKind, name })
    });
    const res = await resp.json();
    if (res && res.status === "ok") {
      showToast(`Deleted '${name}'`);
      notifyCanvasUpdates(currentKind, res.choices);
      await switchTab(currentKind);
    } else {
      showToast(res.message || "Could not delete item", true);
    }
  } catch (err) {
    console.error("[STOIQO Studio] Delete error:", err);
    showToast("Error communicating with backend", true);
  }
}
async function saveCurrentItem() {
  const name = modalContainer.querySelector("#stoiqo-input-name").value.trim();
  if (!name) {
    alert("Please enter a name for this definition.");
    return;
  }
  const category = modalContainer.querySelector("#stoiqo-input-category").value.trim();
  const order = parseInt(modalContainer.querySelector("#stoiqo-input-order").value, 10) || 200;
  const body = modalContainer.querySelector("#stoiqo-textarea-body").value.trim();
  const frontmatter = {
    name,
    category,
    order
  };
  if (currentKind === "styles") {
    const med = modalContainer.querySelector("#stoiqo-style-medium-type")?.value.trim();
    const pro = modalContainer.querySelector("#stoiqo-style-prohibited")?.value.trim();
    const tag = modalContainer.querySelector("#stoiqo-style-tag-injection")?.value.trim();
    const neg = modalContainer.querySelector("#stoiqo-style-negative-injection")?.value.trim();
    if (med) frontmatter.medium_type = med;
    if (pro) frontmatter.prohibited = pro;
    if (tag) frontmatter.tag_injection = tag;
    if (neg) frontmatter.negative_injection = neg;
  } else if (currentKind === "personas") {
    frontmatter.temperature = parseFloat(modalContainer.querySelector("#stoiqo-persona-temp")?.value || 0.65);
    frontmatter.max_new_tokens = parseInt(modalContainer.querySelector("#stoiqo-persona-tokens")?.value || 1024, 10);
    frontmatter.top_p = parseFloat(modalContainer.querySelector("#stoiqo-persona-top-p")?.value || 0.9);
    frontmatter.repetition_penalty = parseFloat(modalContainer.querySelector("#stoiqo-persona-rep")?.value || 1.15);
  }
  try {
    const resp = await api10.fetchApi("/stoiqo/api/prompt_engine/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        kind: currentKind,
        name,
        body,
        frontmatter,
        original_name: isNewMode ? "" : originalName
      })
    });
    const res = await resp.json();
    if (res && res.status === "ok") {
      showToast(`Saved '${name}'`);
      notifyCanvasUpdates(currentKind, res.choices, name);
      closePromptStudioModal();
    } else {
      showToast(res.message || "Failed to save definition", true);
    }
  } catch (err) {
    console.error("[STOIQO Studio] Save error:", err);
    showToast("Error saving definition", true);
  }
}
function notifyCanvasUpdates(kind, choices, newlySelectedName = null) {
  if (!choices) return;
  try {
    window.dispatchEvent(new CustomEvent("stoiqo-definitions-updated", {
      detail: { kind, choices, newlySelectedName }
    }));
  } catch (_) {
  }
  if (activeNodeRef && activeNodeRef.widgets) {
    const meta = KIND_METADATA[kind];
    const w = activeNodeRef.widgets.find((item) => item.name === meta.widgetName || item.name === meta.fallbackWidgetName);
    if (w) {
      let choiceList = [];
      if (kind === "styles") choiceList = choices.artistic_styles || [];
      else if (kind === "personas") choiceList = choices.system_personas || [];
      else if (kind === "types") choiceList = choices.prompt_types || [];
      if (choiceList.length > 0) {
        if (w.options) w.options.values = choiceList;
        if (newlySelectedName && choiceList.includes(newlySelectedName)) {
          w.value = newlySelectedName;
          if (w.callback) w.callback(newlySelectedName);
        }
        if (activeNodeRef.setDirtyCanvas) activeNodeRef.setDirtyCanvas(true, true);
      }
    }
  }
}

// src_js/nodes/promptGeneratorNode.js
var TARGET_NODE_NAMES = [
  "StoiqoPromptGeneratorNode",
  "[STOIQO] Prompt Generator"
];
var MODE_CONFIG = {
  "text_expansion": {
    icon: "\u{1F4DD}",
    badgeText: "TEXT EXPANSION",
    color: "#58b0ff",
    bg: "rgba(41, 151, 255, 0.16)",
    border: "rgba(41, 151, 255, 0.50)",
    dot: "#2997ff"
  },
  "single_image": {
    icon: "\u{1F5BC}\uFE0F",
    badgeText: "SINGLE IMAGE VISION",
    color: "#30d158",
    bg: "rgba(48, 209, 88, 0.16)",
    border: "rgba(48, 209, 88, 0.50)",
    dot: "#30d158"
  },
  "multi_fusion": {
    icon: "\u{1F500}",
    badgeText: "MULTI-IMAGE FUSION",
    color: "#ff9f0a",
    bg: "rgba(255, 159, 10, 0.18)",
    border: "rgba(255, 159, 10, 0.55)",
    dot: "#ff9f0a"
  },
  "batch_caption": {
    icon: "\u{1F4E6}",
    badgeText: "BATCH CAPTION",
    color: "#2997ff",
    bg: "rgba(41, 151, 255, 0.16)",
    border: "rgba(41, 151, 255, 0.50)",
    dot: "#2997ff"
  }
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
  while (t.length > 1 && ctx.measureText(t + "\u2026").width > maxW) {
    t = t.slice(0, -1);
  }
  return t + "\u2026";
}
var StoiqoPromptHUDWidget = class {
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
    return void 0;
  }
  computeSize(width) {
    return [width, this.height];
  }
  draw(ctx, node, width, posY, height) {
    const nodeWidth = node && node.size ? node.size[0] : width;
    const totalW = nodeWidth - 20;
    const startX = 10;
    const startY = posY + 3;
    const barH = 30;
    ctx.save();
    const executedData = node.stoiqo_mode_data;
    const isExecuted = Boolean(executedData && executedData.mode);
    const imageInput = node.inputs ? node.inputs.find((i) => i.name === "image_input" || i.name === "image") : null;
    const textInput = node.inputs ? node.inputs.find((i) => i.name === "text_input" || i.name === "text") : null;
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
    const ptWidget = node.widgets ? node.widgets.find((w) => w.name === "prompt_type") : null;
    const asWidget = node.widgets ? node.widgets.find((w) => w.name === "prompt_style" || w.name === "artistic_style") : null;
    let promptType = executedData?.prompt_type || (ptWidget ? ptWidget.value : "Detailed Narrative");
    let artisticStyle = executedData?.prompt_style || executedData?.artistic_style || (asWidget ? asWidget.value : "Auto-Detect");
    promptType = String(promptType).replace(/\s*\(Long\)/i, "").trim();
    artisticStyle = String(artisticStyle).replace(/Auto-Detect\s*\/\s*/i, "").trim();
    drawRoundRect(ctx, startX, startY, totalW, barH, 5);
    ctx.fillStyle = "rgba(10, 14, 23, 0.85)";
    ctx.fill();
    ctx.strokeStyle = "rgba(255, 255, 255, 0.09)";
    ctx.lineWidth = 1;
    ctx.stroke();
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
    ctx.fillStyle = cfg.dot;
    ctx.beginPath();
    ctx.arc(pillX + 8, pillY + pillH / 2, 2.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = cfg.color;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText(badgeLabel, pillX + 16, pillY + pillH / 2 + 0.5);
    const leftOccupied = pillX + pillW + 10;
    const rightStatusW = isExecuted ? 50 : 44;
    const availInfoW = totalW - (leftOccupied - startX) - rightStatusW - 12;
    if (availInfoW > 60) {
      ctx.font = "9px 'JetBrains Mono', SFMono-Regular, Consolas, -apple-system, sans-serif";
      const infoText = `${promptType} \u2022 ${artisticStyle}`;
      const fittedInfo = truncateText(ctx, infoText, availInfoW);
      ctx.fillStyle = "#94a3b8";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText(fittedInfo, leftOccupied, startY + barH / 2 + 0.5);
    }
    const statusLabel = isExecuted ? "\u25CF ACTIVE" : hasImageLink ? "\u25CF LINKED" : "\u25CF READY";
    const statusColor = isExecuted ? "#30d158" : hasImageLink ? "#2997ff" : "#64748b";
    ctx.font = "bold 8.5px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
    ctx.fillStyle = statusColor;
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    ctx.fillText(statusLabel, startX + totalW - 8, startY + barH / 2 + 0.5);
    ctx.restore();
  }
};
function ensureHUDWidget(node) {
  if (!node || !node.widgets) return;
  const existing = node.widgets.filter((w) => w.name === "_stoiqo_mode_hud" || w.isStoiqoHUD);
  for (const extra of existing.slice(1)) {
    node.widgets.splice(node.widgets.indexOf(extra), 1);
  }
  let hud = existing[0];
  if (!hud) {
    hud = new StoiqoPromptHUDWidget(node);
    node.widgets.unshift(hud);
  } else {
    const curIdx = node.widgets.indexOf(hud);
    if (curIdx > 0) {
      node.widgets.splice(curIdx, 1);
      node.widgets.unshift(hud);
    }
  }
  node._stoiqo_mode_hud = hud;
}
function ensureStudioButton(node) {
  if (!node || !node.widgets) return;
  let studioBtn = node.widgets.find((w) => w._isStoiqoStudioBtn);
  if (!studioBtn) {
    studioBtn = node.addWidget("button", "\u{1F3A8} Gestione Stili & Prompt (Studio)...", null, () => {
      openPromptStudioModal({ node, kind: "styles" });
    });
    studioBtn._isStoiqoStudioBtn = true;
    studioBtn.serialize = false;
    studioBtn.options = { serialize: false };
  }
  const curIdx = node.widgets.indexOf(studioBtn);
  const drawerIdx = node.widgets.findIndex((w) => w.name === "_stoiqo_settings_drawer");
  const styleIdx = node.widgets.findIndex((w) => w.name === "prompt_style" || w.name === "artistic_style");
  let targetIdx = -1;
  if (drawerIdx !== -1) {
    targetIdx = drawerIdx;
  } else if (styleIdx !== -1) {
    targetIdx = styleIdx + 1;
  }
  if (targetIdx !== -1 && curIdx !== targetIdx && curIdx !== -1) {
    node.widgets.splice(curIdx, 1);
    const newTarget = curIdx < targetIdx ? targetIdx - 1 : targetIdx;
    node.widgets.splice(newTarget, 0, studioBtn);
  }
}
function setupPromptGeneratorNode(nodeType, nodeData, app11) {
  if (!TARGET_NODE_NAMES.includes(nodeData.name)) return;
  const MIN_WIDTH3 = 420;
  const MIN_HEIGHT = 280;
  function applyPromptNodeSizing(node) {
    if (!node) return;
    if (typeof node.computeSize === "function") {
      const sz = node.computeSize();
      const w = Math.max(node.size ? node.size[0] : MIN_WIDTH3, MIN_WIDTH3, Math.ceil(sz[0] || 0));
      const h = Math.max(node.size ? node.size[1] : MIN_HEIGHT, MIN_HEIGHT, Math.ceil(sz[1] || 0));
      if (typeof node.setSize === "function") {
        node.setSize([w, h]);
      } else {
        node.size = [w, h];
      }
    }
    node.setDirtyCanvas?.(true, true);
  }
  const origOnNodeCreated = nodeType.prototype.onNodeCreated;
  nodeType.prototype.onNodeCreated = function() {
    if (origOnNodeCreated) origOnNodeCreated.apply(this, arguments);
    ensureHUDWidget(this);
    ensureStudioButton(this);
    applyPromptNodeSizing(this);
    const origOnConnectionsChange = this.onConnectionsChange;
    this.onConnectionsChange = function(type, index, isConnected, link_info) {
      if (origOnConnectionsChange) origOnConnectionsChange.apply(this, arguments);
      if (this.setDirtyCanvas) this.setDirtyCanvas(true, false);
    };
  };
  const origOnConfigure = nodeType.prototype.onConfigure;
  nodeType.prototype.onConfigure = function() {
    if (origOnConfigure) origOnConfigure.apply(this, arguments);
    ensureHUDWidget(this);
    ensureStudioButton(this);
    applyPromptNodeSizing(this);
  };
  const origGetExtraMenuOptions = nodeType.prototype.getExtraMenuOptions;
  nodeType.prototype.getExtraMenuOptions = function(_, options) {
    if (origGetExtraMenuOptions) origGetExtraMenuOptions.apply(this, arguments);
    const styleW = this.widgets?.find((x) => x.name === "prompt_style" || x.name === "artistic_style");
    const personaW = this.widgets?.find((x) => x.name === "system_prompt");
    const typeW = this.widgets?.find((x) => x.name === "prompt_type");
    const curStyle = styleW?.value ? String(styleW.value) : "Stile Attivo";
    const curPersona = personaW?.value ? String(personaW.value) : "Persona Attiva";
    const curType = typeW?.value ? String(typeW.value) : "Formato Attivo";
    const shortStyle = curStyle.length > 25 ? curStyle.substring(0, 23) + "\u2026" : curStyle;
    const shortPersona = curPersona.length > 25 ? curPersona.substring(0, 23) + "\u2026" : curPersona;
    const shortType = curType.length > 25 ? curType.substring(0, 23) + "\u2026" : curType;
    options.push(
      null,
      // Menu divider
      {
        content: `\u{1F3A8} Modifica Stile: "${shortStyle}"`,
        callback: () => openPromptStudioModal({ node: this, kind: "styles", activeName: curStyle })
      },
      {
        content: `\u{1F9E0} Modifica Persona: "${shortPersona}"`,
        callback: () => openPromptStudioModal({ node: this, kind: "personas", activeName: curPersona })
      },
      {
        content: `\u{1F4D0} Modifica Formato: "${shortType}"`,
        callback: () => openPromptStudioModal({ node: this, kind: "types", activeName: curType })
      },
      {
        content: "\u2795 Crea Nuovo Stile Personalizzato...",
        callback: () => openPromptStudioModal({ node: this, kind: "styles", isNew: true })
      },
      {
        content: "\u2699\uFE0F STOIQO Prompt Studio (Pannello Completo)...",
        callback: () => openPromptStudioModal({ node: this, kind: "styles" })
      }
    );
  };
  const origOnExecuted = nodeType.prototype.onExecuted;
  nodeType.prototype.onExecuted = function(message) {
    if (origOnExecuted) origOnExecuted.apply(this, arguments);
    if (message && message.stoiqo_mode && message.stoiqo_mode.length > 0) {
      this.stoiqo_mode_data = message.stoiqo_mode[0];
      if (this.setDirtyCanvas) this.setDirtyCanvas(true, false);
    }
  };
  window.addEventListener("stoiqo-definitions-updated", (e) => {
    const { kind, choices, newlySelectedName } = e.detail || {};
    if (!app11.graph) return;
    const nodes = app11.graph.findNodesByType(nodeData.name);
    if (!nodes || !nodes.length) return;
    nodes.forEach((n) => {
      if (!n.widgets) return;
      if (kind === "styles") {
        const w = n.widgets.find((x) => x.name === "prompt_style" || x.name === "artistic_style");
        if (w && choices && choices.artistic_styles) {
          w.options.values = choices.artistic_styles;
          if (newlySelectedName && choices.artistic_styles.includes(newlySelectedName)) {
            w.value = newlySelectedName;
            if (w.callback) w.callback(newlySelectedName);
          }
        }
      } else if (kind === "personas") {
        const w = n.widgets.find((x) => x.name === "system_prompt");
        if (w && choices && choices.system_personas) {
          w.options.values = choices.system_personas;
          if (newlySelectedName && choices.system_personas.includes(newlySelectedName)) {
            w.value = newlySelectedName;
            if (w.callback) w.callback(newlySelectedName);
          }
        }
      } else if (kind === "types") {
        const w = n.widgets.find((x) => x.name === "prompt_type");
        if (w && choices && choices.prompt_types) {
          w.options.values = choices.prompt_types;
          if (newlySelectedName && choices.prompt_types.includes(newlySelectedName)) {
            w.value = newlySelectedName;
            if (w.callback) w.callback(newlySelectedName);
          }
        }
      }
      if (n.setDirtyCanvas) n.setDirtyCanvas(true, true);
    });
  });
}

// src_js/nodes/seedNode.js
function setupSeedNode(nodeType, nodeData, appInstance) {
  const targetNames = [
    "StoiqoSeedControllerNode",
    "[STOIQO] Seed & Resolution Controller",
    "[STOIQO] Smart Seed & Variance Controller"
  ];
  if (!targetNames.includes(nodeData.name)) return;
  class StoiqoSeedHistoryWidget {
    constructor(node) {
      this.node = node;
      this.type = "custom";
      this.name = "_stoiqo_seed_history_hud";
      this.value = {};
      this.serialize = false;
      this.options = { serialize: false };
      this.isStoiqoHUD = true;
      this.height = 70;
      this.activeSeed = null;
      this.effectiveSeed = null;
      this.resolution = null;
      this.seedHistory = [];
      this.flashStatus = null;
      this.flashTimeout = null;
      this.buttonRects = {};
      this.chipRects = [];
    }
    serializeValue() {
      return void 0;
    }
    computeSize(width) {
      return [width, this.height];
    }
    setExecutionData(data) {
      if (!data) return;
      if (data.active_seed && data.active_seed.length > 0) {
        this.activeSeed = data.active_seed[0];
      }
      if (data.effective_seed && data.effective_seed.length > 0) {
        this.effectiveSeed = data.effective_seed[0];
      }
      if (data.resolution && data.resolution.length > 0) {
        this.resolution = data.resolution[0];
      }
      if (data.seed_history && Array.isArray(data.seed_history)) {
        this.seedHistory = data.seed_history;
      }
      if (this.node) {
        this.node.setDirtyCanvas(true, true);
      }
    }
    copyToClipboard(text, flashLabel) {
      if (text === null || text === void 0) return;
      const strVal = String(text);
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(strVal);
        } else {
          const ta = document.createElement("textarea");
          ta.value = strVal;
          document.body.appendChild(ta);
          ta.select();
          document.execCommand("copy");
          document.body.removeChild(ta);
        }
        this.triggerFlash(flashLabel || "\u2713 COPIED");
      } catch (err) {
        console.error("[STOIQO Seed] Copy failed:", err);
      }
    }
    triggerFlash(label) {
      this.flashStatus = label;
      if (this.flashTimeout) clearTimeout(this.flashTimeout);
      this.flashTimeout = setTimeout(() => {
        this.flashStatus = null;
        if (this.node) this.node.setDirtyCanvas(true, false);
      }, 1800);
      if (this.node) this.node.setDirtyCanvas(true, false);
    }
    recallSeed(seedVal) {
      if (!this.node || !this.node.widgets) return;
      const seedWidget = this.node.widgets.find((w) => w.name === "seed");
      const modeWidget = this.node.widgets.find(
        (w) => w.name === "control_after_generate" || w.name === "control_mode"
      );
      if (seedWidget) {
        seedWidget.value = Number(seedVal);
        if (seedWidget.callback) seedWidget.callback(seedWidget.value);
      }
      if (modeWidget) {
        modeWidget.value = "fixed";
        if (modeWidget.callback) modeWidget.callback(modeWidget.value);
      }
      this.copyToClipboard(seedVal, `\u2713 RECALLED ${seedVal} (MODE: FIXED)`);
      this.node.setDirtyCanvas(true, true);
    }
    draw(ctx, node, width, y, height) {
      if (node.flags && node.flags.collapsed) return;
      const padX = 12;
      const cardX = padX;
      const cardY = y + 4;
      const cardW = width - padX * 2;
      const cardH = this.height - 8;
      this.buttonRects = {};
      this.chipRects = [];
      ctx.save();
      ctx.fillStyle = "rgba(18, 20, 26, 0.95)";
      ctx.strokeStyle = "rgba(41, 151, 255, 0.40)";
      ctx.lineWidth = 1.2;
      if (ctx.roundRect) {
        ctx.beginPath();
        ctx.roundRect(cardX, cardY, cardW, cardH, 7);
        ctx.fill();
        ctx.stroke();
      } else {
        ctx.fillRect(cardX, cardY, cardW, cardH);
        ctx.strokeRect(cardX, cardY, cardW, cardH);
      }
      ctx.fillStyle = "#2997ff";
      if (ctx.roundRect) {
        ctx.beginPath();
        ctx.roundRect(cardX, cardY, 4, cardH, [7, 0, 0, 7]);
        ctx.fill();
      } else {
        ctx.fillRect(cardX, cardY, 4, cardH);
      }
      const row1Y = cardY + 18;
      ctx.font = "bold 10px Inter, sans-serif";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillStyle = "#58b0ff";
      ctx.fillText("\u{1F3B2} SEED:", cardX + 12, row1Y);
      const currentDisplay = this.activeSeed !== null ? String(this.activeSeed) : node.widgets.find((w) => w.name === "seed") ? String(node.widgets.find((w) => w.name === "seed").value) : "0";
      ctx.font = "bold 11px monospace, sans-serif";
      ctx.fillStyle = "#ffffff";
      ctx.fillText(currentDisplay, cardX + 62, row1Y);
      let extraX = cardX + 62 + ctx.measureText(currentDisplay).width + 8;
      if (this.effectiveSeed !== null && this.effectiveSeed !== this.activeSeed) {
        ctx.font = "9px monospace";
        ctx.fillStyle = "#58b0ff";
        const effTxt = `(Eff: ${this.effectiveSeed})`;
        ctx.fillText(effTxt, extraX, row1Y);
        extraX += ctx.measureText(effTxt).width + 8;
      }
      if (this.resolution) {
        ctx.font = "bold 9.5px monospace";
        ctx.fillStyle = "#30d158";
        ctx.fillText(`\u{1F4D0} ${this.resolution}`, extraX, row1Y);
      }
      const copyBtnW = 68;
      const copyBtnH = 20;
      const copyBtnX = cardX + cardW - copyBtnW - 8;
      const copyBtnY = cardY + 8;
      this.buttonRects["copy_active"] = { x: copyBtnX, y: copyBtnY, w: copyBtnW, h: copyBtnH, data: currentDisplay };
      ctx.fillStyle = this.flashStatus ? "#12301d" : "#182234";
      ctx.strokeStyle = this.flashStatus ? "#30d158" : "#2997ff";
      ctx.lineWidth = 1;
      if (ctx.roundRect) {
        ctx.beginPath();
        ctx.roundRect(copyBtnX, copyBtnY, copyBtnW, copyBtnH, 4);
        ctx.fill();
        ctx.stroke();
      } else {
        ctx.fillRect(copyBtnX, copyBtnY, copyBtnW, copyBtnH);
        ctx.strokeRect(copyBtnX, copyBtnY, copyBtnW, copyBtnH);
      }
      ctx.font = "bold 9px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.fillStyle = this.flashStatus ? "#30d158" : "#d8e6f5";
      ctx.fillText(this.flashStatus || "\u{1F4CB} COPIA", copyBtnX + copyBtnW / 2, copyBtnY + copyBtnH / 2 + 0.5);
      const row2Y = cardY + 44;
      ctx.font = "bold 9px Inter, sans-serif";
      ctx.textAlign = "left";
      ctx.fillStyle = "#94a3b8";
      ctx.fillText("\u{1F4DC} STORICO:", cardX + 12, row2Y);
      const startChipsX = cardX + 76;
      let curChipX = startChipsX;
      const chipH = 18;
      const chipGap = 6;
      const historyList = this.seedHistory && this.seedHistory.length > 0 ? this.seedHistory : this.activeSeed !== null ? [{ seed: this.activeSeed }] : [];
      if (historyList.length === 0) {
        ctx.font = "9px Inter, italic";
        ctx.fillStyle = "#64748b";
        ctx.fillText("No seeds generated in current session", startChipsX, row2Y);
      } else {
        const displayItems = historyList.slice(-5);
        displayItems.forEach((item, idx) => {
          const seedNum = String(item.seed);
          ctx.font = "9.5px monospace";
          const seedW = ctx.measureText(seedNum).width + 12;
          if (curChipX + seedW <= cardX + cardW - 8) {
            const chipY = row2Y - chipH / 2;
            this.chipRects.push({
              x: curChipX,
              y: chipY,
              w: seedW,
              h: chipH,
              seed: item.seed
            });
            ctx.fillStyle = "#121318";
            ctx.strokeStyle = "rgba(41, 151, 255, 0.35)";
            ctx.lineWidth = 1;
            if (ctx.roundRect) {
              ctx.beginPath();
              ctx.roundRect(curChipX, chipY, seedW, chipH, 3);
              ctx.fill();
              ctx.stroke();
            } else {
              ctx.fillRect(curChipX, chipY, seedW, chipH);
              ctx.strokeRect(curChipX, chipY, seedW, chipH);
            }
            ctx.fillStyle = "#cbd5e1";
            ctx.textAlign = "center";
            ctx.fillText(seedNum, curChipX + seedW / 2, row2Y + 0.5);
            curChipX += seedW + chipGap;
          }
        });
      }
      ctx.restore();
    }
    mouse(event, pos, node) {
      if (event.type === "pointerdown" || event.type === "mousedown") {
        const x = pos[0];
        const y = pos[1];
        for (const [btnId, rect] of Object.entries(this.buttonRects)) {
          if (x >= rect.x && x <= rect.x + rect.w && y >= rect.y && y <= rect.y + rect.h) {
            this.copyToClipboard(rect.data, "\u2713 COPIED");
            return true;
          }
        }
        for (const chip of this.chipRects) {
          if (x >= chip.x && x <= chip.x + chip.w && y >= chip.y && y <= chip.y + chip.h) {
            this.recallSeed(chip.seed);
            return true;
          }
        }
      }
      return false;
    }
  }
  function ensureSeedHUD(node) {
    if (!node || !node.widgets) return;
    const existing = node.widgets.filter((w) => w.name === "_stoiqo_seed_history_hud");
    for (const extra of existing.slice(1)) {
      node.widgets.splice(node.widgets.indexOf(extra), 1);
    }
    let hud = existing[0];
    if (!hud) {
      hud = new StoiqoSeedHistoryWidget(node);
      node.addCustomWidget(hud);
    }
    node._stoiqo_seed_hud = hud;
  }
  function applySeedNodeSizing(node) {
    if (!node) return;
    if (typeof node.computeSize === "function") {
      const sz = node.computeSize();
      const w = Math.max(node.size ? node.size[0] : 380, 380, Math.ceil(sz[0] || 0));
      const h = Math.max(node.size ? node.size[1] : 260, 260, Math.ceil(sz[1] || 0));
      if (typeof node.setSize === "function") {
        node.setSize([w, h]);
      } else {
        node.size = [w, h];
      }
    }
    node.setDirtyCanvas?.(true, true);
  }
  const origOnNodeCreated = nodeType.prototype.onNodeCreated;
  nodeType.prototype.onNodeCreated = function() {
    if (origOnNodeCreated) origOnNodeCreated.apply(this, arguments);
    ensureSeedHUD(this);
    applySeedNodeSizing(this);
  };
  const origOnConfigure = nodeType.prototype.onConfigure;
  nodeType.prototype.onConfigure = function() {
    if (origOnConfigure) origOnConfigure.apply(this, arguments);
    ensureSeedHUD(this);
    applySeedNodeSizing(this);
  };
  const origOnExecuted = nodeType.prototype.onExecuted;
  nodeType.prototype.onExecuted = function(message) {
    if (origOnExecuted) origOnExecuted.apply(this, arguments);
    if (this._stoiqo_seed_hud) {
      this._stoiqo_seed_hud.setExecutionData(message);
    }
  };
}

// src_js/utils/telemetry.js
import { api as api11 } from "../../scripts/api.js";
var listenerAttached = false;
function initGlobalTelemetryListener(appInstance) {
  if (listenerAttached) return;
  listenerAttached = true;
  if (api11 && api11.addEventListener) {
    api11.addEventListener("stoiqo_node_telemetry", (event) => {
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
function setupTelemetryBadge(nodeType, nodeData, appInstance) {
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
  const timeStr = stats.time_ms < 1e3 ? `${Math.round(stats.time_ms)}ms` : `${(stats.time_ms / 1e3).toFixed(2)}s`;
  const vramStr = stats.vram_gb && stats.vram_gb > 0 ? `${stats.vram_gb.toFixed(1)} GB` : "0 GB";
  const badgeText = `${timeStr} | ${vramStr}`;
  ctx.save();
  ctx.font = "bold 9.5px 'JetBrains Mono', SFMono-Regular, Consolas, monospace";
  const textMetrics = ctx.measureText(badgeText);
  const iconWidth = 12;
  const paddingX = 7;
  const badgeW = textMetrics.width + iconWidth + paddingX * 2;
  const badgeH = 16;
  const nodeWidth = node.flags?.collapsed && node._collapsed_width ? node._collapsed_width : node.size ? node.size[0] : 200;
  const posX = Math.max(8, nodeWidth - badgeW - 8);
  const posY = -24;
  ctx.fillStyle = "rgba(10, 14, 22, 0.88)";
  ctx.strokeStyle = "rgba(41, 151, 255, 0.45)";
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
  ctx.fillStyle = "#2997ff";
  ctx.fillText("\u26A1", posX + paddingX, posY + 12);
  ctx.fillStyle = "#cbd5e1";
  ctx.fillText(badgeText, posX + paddingX + iconWidth, posY + 12);
  ctx.restore();
}

// src_js/utils/settingsDrawer.js
var DRAWER_WIDGET_NAME = "_stoiqo_settings_drawer";
var PERSONA_SAMPLING_VALUES = {
  "Auto-Detect / Balanced": { temperature: 0.65, max_new_tokens: 1024, top_p: 0.9, top_k: 50, repetition_penalty: 1.15 },
  "None (Raw / No System Prompt)": { temperature: 0.65, max_new_tokens: 1024, top_p: 0.9, top_k: 50, repetition_penalty: 1.15 },
  "Generative Vision Engine": { temperature: 0.65, max_new_tokens: 1024, top_p: 0.9, top_k: 50, repetition_penalty: 1.15 },
  "Text-to-Prompt Expansion Engine": { temperature: 0.7, max_new_tokens: 1024, top_p: 0.9, top_k: 60, repetition_penalty: 1.15 },
  "Multi-Image Synthesis Engine": { temperature: 0.6, max_new_tokens: 1024, top_p: 0.9, top_k: 50, repetition_penalty: 1.15 },
  "Cinematic & Video Director": { temperature: 0.75, max_new_tokens: 1280, top_p: 0.92, top_k: 60, repetition_penalty: 1.12 },
  "Dataset & LoRA Annotator": { temperature: 0.35, max_new_tokens: 512, top_p: 0.85, top_k: 40, repetition_penalty: 1.15 },
  "Minimalist & Literal": { temperature: 0.2, max_new_tokens: 384, top_p: 0.75, top_k: 25, repetition_penalty: 1.2 },
  "SeedVR2 Upscale Guide": { temperature: 0.25, max_new_tokens: 640, top_p: 0.8, top_k: 30, repetition_penalty: 1.2 }
};
function getVal(node, name) {
  const w = node?.widgets?.find((x) => x.name === name);
  return w ? w.value : void 0;
}
var NODE_UX_SPECS = {
  StoiqoPromptGeneratorNode: {
    label: "Advanced Settings & Sampling",
    advanced: [
      "seed",
      "fusion_mode",
      "custom_system_prompt",
      "negative_prompt_prefix",
      "temperature",
      "max_new_tokens",
      "top_p",
      "top_k",
      "repetition_penalty"
    ],
    conditions: {
      custom_system_prompt: (node) => String(getVal(node, "system_prompt") || "").includes("Custom")
    },
    onWidgetChange: (node, name, val) => {
      if (name === "system_prompt" && PERSONA_SAMPLING_VALUES[val]) {
        const pv = PERSONA_SAMPLING_VALUES[val];
        for (const [k, v] of Object.entries(pv)) {
          const tw = node.widgets?.find((w) => w.name === k);
          if (tw) {
            tw.value = v;
            if (tw.inputEl) tw.inputEl.value = String(v);
          }
        }
      }
    }
  },
  StoiqoDatasetWriterNode: {
    label: "Dataset, Tag & Deduplication Options",
    advanced: [
      "blacklist_tags",
      "tag_separator",
      "shuffle_tags",
      "keep_tokens",
      "save_txt",
      "save_json_metadata",
      "use_original_filename",
      "fallback_prefix",
      "deduplicate_images",
      "similarity_threshold",
      "seed"
    ],
    conditions: {
      image_format: (node) => Boolean(getVal(node, "save_image")),
      keep_tokens: (node) => Boolean(getVal(node, "shuffle_tags")),
      fallback_prefix: (node) => !Boolean(getVal(node, "use_original_filename")),
      similarity_threshold: (node) => Boolean(getVal(node, "deduplicate_images"))
    }
  },
  StoiqoSmartFolderImageIterator: {
    label: "Folder Filters & Batch Options",
    advanced: [
      "loop_folder",
      "recursive",
      "skip_captioned",
      "caption_extension"
    ],
    conditions: {
      index: (node) => String(getVal(node, "load_mode") || "").startsWith("Single"),
      max_batch_images: (node) => String(getVal(node, "load_mode") || "").startsWith("Batch"),
      seed: (node) => String(getVal(node, "iteration_mode") || "").includes("Random"),
      loop_folder: (node) => String(getVal(node, "load_mode") || "").startsWith("Single"),
      caption_extension: (node) => Boolean(getVal(node, "skip_captioned"))
    }
  },
  StoiqoSeedControllerNode: {
    label: "Seed Variance & VAE Multiple Options",
    advanced: [
      "multiple_of",
      "variance_strength",
      "variance_seed",
      "seed_prefix"
    ],
    conditions: {
      custom_width: (node) => String(getVal(node, "aspect_ratio") || "").includes("Custom"),
      custom_height: (node) => String(getVal(node, "aspect_ratio") || "").includes("Custom")
    }
  },
  StoiqoTurboSamplerNode: {
    label: "Sampler & Denoise Options",
    advanced: [
      "sampler_name",
      "scheduler",
      "denoise"
    ]
  },
  StoiqoWatermarkNode: {
    label: "Border, Chroma Key & Text Color Options",
    advanced: [
      "margin_percent",
      "text_color",
      "remove_bg_mode",
      "chroma_tolerance",
      "feather_radius"
    ],
    conditions: {
      custom_scale: (node) => String(getVal(node, "scale_mode") || "").includes("Custom"),
      chroma_tolerance: (node) => !String(getVal(node, "remove_bg_mode") || "").startsWith("None")
    }
  },
  StoiqoTextConcatenateNode: {
    label: "Template, Prefix/Suffix & Tag Sanitization",
    advanced: [
      "template",
      "prefix",
      "suffix",
      "deduplicate_tags",
      "clean_whitespace",
      "convert_underscores",
      "skip_empty"
    ]
  },
  StoiqoMusicPromptEngineNode: {
    label: "AI Producer & Sampling Settings",
    advanced: [
      "system_prompt",
      "custom_system_prompt",
      "custom_directives",
      "seed",
      "temperature",
      "repetition_penalty",
      "max_new_tokens"
    ],
    conditions: {
      custom_system_prompt: (node) => String(getVal(node, "system_prompt") || "").includes("Custom")
    }
  },
  StoiqoCharacterMemoryNode: {
    label: "Lorebook Options, Constraints & JSON Export",
    advanced: [
      "injection_mode",
      "personality_vibe",
      "negative_constraints",
      "user_prompt",
      "save_profile_as",
      "custom_json_data"
    ]
  },
  StoiqoSpatialCropperNode: {
    label: "Manual Coordinates & Mask Options",
    advanced: [
      "manual_bbox",
      "invert_mask",
      "target_megapixel",
      "coord_order"
    ]
  },
  StoiqoInpaintStitcherNode: {
    label: "BBox Options, Padding & Beauty Polish",
    advanced: [
      "bbox_info",
      "crop_padding_percent",
      "skin_smoothing",
      "detail_clarity"
    ],
    conditions: {
      color_match_strength: (node) => Boolean(getVal(node, "color_match"))
    }
  },
  StoiqoFrequencySeparationNode: {
    label: "High-Pass Options & Soft-Knee Limiter",
    advanced: [
      "texture_boost",
      "high_pass_mode",
      "soft_knee_limiter",
      "split_meta"
    ]
  },
  StoiqoProImageSaverNode: {
    label: "Folder, Metadata & Privacy Options",
    advanced: [
      "quality",
      "subfolder",
      "sidecar_metadata",
      "save_workflow",
      "privacy_mode"
    ]
  },
  StoiqoVideoSaverNode: {
    label: "Quality, Folder & Video Sidecars",
    advanced: [
      "quality",
      "subfolder",
      "motion_prompt",
      "sidecar_metadata"
    ]
  },
  StoiqoAudioSaverNode: {
    label: "ID3 Tags, Lyrics & Audio Metadata",
    advanced: [
      "subfolder",
      "genre",
      "bpm",
      "style",
      "lyrics",
      "sidecar_metadata"
    ]
  },
  StoiqoImageCompareNode: {
    alwaysHidden: ["initial_mode"],
    label: "Heatmap Options & Diff Mask Threshold",
    advanced: [
      "heatmap_colormap",
      "diff_gain",
      "mask_threshold"
    ]
  },
  StoiqoImageLoaderNode: {
    label: "Batch Aspect Ratio Options",
    alwaysHidden: ["active_focus"],
    advanced: ["fit_mode"]
  },
  StoiqoVideoEnhancerNode: {
    label: "Deflicker Options & Motion Curve",
    advanced: [
      "window_size",
      "luminance_tolerance",
      "stabilization_strength",
      "motion_smoothness",
      "blend_curve"
    ],
    conditions: {
      window_size: (node) => Boolean(getVal(node, "enable_deflicker")),
      luminance_tolerance: (node) => Boolean(getVal(node, "enable_deflicker")),
      stabilization_strength: (node) => Boolean(getVal(node, "enable_deflicker")),
      motion_smoothness: (node) => !String(getVal(node, "fps_multiplier") || "").startsWith("1x"),
      blend_curve: (node) => !String(getVal(node, "fps_multiplier") || "").startsWith("1x")
    }
  }
};
var KNOWN_MULTILINE_WIDGET_NAMES = /* @__PURE__ */ new Set([
  "template",
  "custom_system_prompt",
  "custom_modifications",
  "blacklist_tags",
  "lyrics",
  "style",
  "motion_prompt",
  "physical_dna",
  "outfit_and_gear",
  "negative_constraints",
  "user_prompt",
  "custom_json_data",
  "custom_directives",
  "positive",
  "negative",
  "idea",
  "custom_lyrics"
]);
function isWidgetMultiline(w) {
  if (!w) return false;
  if (w.options && (w.options.multiline || w.options.multiline === true)) return true;
  if (w.type === "customtext") return true;
  if (w.inputEl && w.inputEl.tagName === "TEXTAREA") return true;
  if (KNOWN_MULTILINE_WIDGET_NAMES.has(w.name)) return true;
  return false;
}
function getMultilineTargetHeight(w) {
  if (w._boxHeight && w._boxHeight > 30) return w._boxHeight;
  if (w.inputEl && parseInt(w.inputEl.style.height, 10) > 30) {
    return parseInt(w.inputEl.style.height, 10);
  }
  if (w.name === "template") return 56;
  if (w.name === "custom_system_prompt") return 52;
  if (w.name === "custom_modifications") return 64;
  if (w.name === "blacklist_tags") return 50;
  if (w.name === "lyrics") return 68;
  if (w.name === "motion_prompt") return 56;
  if (w.name === "idea") return 76;
  return 56;
}
function setWidgetVisibility(w, visible) {
  if (!w) return;
  if (!w._stoiqoSavedOrig) {
    w._stoiqoSavedOrig = {
      computeSize: w.computeSize,
      draw: w.draw
    };
  }
  if (visible) {
    w.hidden = false;
    if (w._stoiqoSavedOrig.computeSize) {
      w.computeSize = w._stoiqoSavedOrig.computeSize;
    } else if (isWidgetMultiline(w)) {
      const h = getMultilineTargetHeight(w);
      w.computeSize = (width) => [width, h];
    } else {
      delete w.computeSize;
    }
    if (w._stoiqoSavedOrig.draw) {
      w.draw = w._stoiqoSavedOrig.draw;
    } else {
      delete w.draw;
    }
    if (w.inputEl) {
      w.inputEl.hidden = false;
      w.inputEl.style.display = "";
      if (isWidgetMultiline(w)) {
        const h = getMultilineTargetHeight(w);
        w.inputEl.style.height = `${h}px`;
        w.inputEl.style.boxSizing = "border-box";
      }
    }
  } else {
    w.hidden = true;
    w.computeSize = () => [0, -4];
    w.draw = () => {
    };
    if (w.inputEl) {
      w.inputEl.hidden = true;
      w.inputEl.style.display = "none";
    }
  }
}
var StoiqoSettingsDrawerWidget = class {
  constructor(node, spec) {
    this.type = "custom";
    this.name = DRAWER_WIDGET_NAME;
    this.node = node;
    this.spec = spec;
    this.serialize = false;
    this.options = { serialize: false };
    this.lastClick = 0;
    this.hitBox = null;
  }
  get value() {
    return "";
  }
  set value(_v) {
  }
  serializeValue() {
    return void 0;
  }
  isVisible() {
    if (this.spec.drawerWhen && !this.spec.drawerWhen(this.node)) {
      return false;
    }
    return Array.isArray(this.spec.advanced) && this.spec.advanced.length > 0;
  }
  computeSize(width) {
    if (!this.isVisible()) return [0, -4];
    return [width, 28];
  }
  draw(ctx, node, width, y) {
    if (!this.isVisible()) {
      this.hitBox = null;
      return;
    }
    const nodeW = node && node.size ? node.size[0] : width;
    const padX = 10;
    const barX = padX;
    const barY = y + 2;
    const barW = nodeW - padX * 2;
    const barH = 22;
    const expanded = Boolean(node._stoiqoAdvExpanded);
    this.hitBox = { x: barX, y: barY, w: barW, h: barH };
    ctx.save();
    ctx.beginPath();
    if (ctx.roundRect) {
      ctx.roundRect(barX, barY, barW, barH, 5);
    } else {
      ctx.rect(barX, barY, barW, barH);
    }
    ctx.fillStyle = expanded ? "rgba(41, 151, 255, 0.14)" : "rgba(255, 255, 255, 0.04)";
    ctx.fill();
    ctx.strokeStyle = expanded ? "rgba(41, 151, 255, 0.45)" : "rgba(255, 255, 255, 0.09)";
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.font = "600 10.5px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
    ctx.fillStyle = expanded ? "#58b0ff" : "#98a2b3";
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    const label = this.spec.label || "Advanced Settings";
    ctx.fillText(`\u2699  ${label}`, barX + 10, barY + barH / 2);
    const advList = this.spec.advanced || [];
    const count = advList.length;
    let modCount = 0;
    if (node && node.widgets) {
      for (const name of advList) {
        const w = node.widgets.find((x) => x.name === name);
        if (w && w._stoiqoDefaultVal !== void 0 && String(w.value ?? "") !== String(w._stoiqoDefaultVal ?? "")) {
          modCount++;
        }
      }
    }
    const rightText = expanded ? "Hide \u25B4" : `Show (${count}) \u25BE`;
    ctx.font = "500 9.5px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
    ctx.fillStyle = expanded ? "#58b0ff" : "#667085";
    ctx.textAlign = "right";
    ctx.fillText(rightText, barX + barW - 10, barY + barH / 2);
    if (!expanded && modCount > 0) {
      const rightW = ctx.measureText(rightText).width;
      ctx.font = "600 9.5px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
      ctx.fillStyle = "#ff9f0a";
      ctx.fillText(`\u25CF ${modCount} edited`, barX + barW - 10 - rightW - 8, barY + barH / 2);
    }
    ctx.restore();
  }
  mouse(event, pos, node) {
    if (!this.isVisible() || !this.hitBox) return false;
    if (!event || event.type !== "pointerdown" && event.type !== "mousedown") return false;
    if (!pos) return false;
    const now = performance.now();
    if (now - this.lastClick < 150) return true;
    const [mx, my] = pos;
    const b = this.hitBox;
    if (mx >= b.x && mx <= b.x + b.w && my >= b.y && my <= b.y + b.h) {
      this.lastClick = now;
      node._stoiqoAdvExpanded = !Boolean(node._stoiqoAdvExpanded);
      if (node._stoiqoApplyUX) {
        node._stoiqoApplyUX(true);
      }
      return true;
    }
    return false;
  }
};
function applyNodeUXSpec(node, spec) {
  if (!node || !node.widgets || !spec) return;
  const synIdx = node.widgets.findIndex((w) => w && w.name === "synthesized_prompt");
  if (synIdx !== -1) {
    const tw = node.widgets[synIdx];
    if (tw.inputEl && tw.inputEl.parentNode) {
      tw.inputEl.parentNode.removeChild(tw.inputEl);
    }
    node.widgets.splice(synIdx, 1);
  }
  const existingDrawers = node.widgets.filter((w) => w.name === DRAWER_WIDGET_NAME);
  for (const extra of existingDrawers.slice(1)) {
    node.widgets.splice(node.widgets.indexOf(extra), 1);
  }
  const advSet = new Set(spec.advanced || []);
  if (advSet.has("seed")) {
    advSet.add("control_after_generate");
    advSet.add("control_mode");
  }
  for (const w of node.widgets) {
    if (!w) continue;
    if (w.name === "control_after_generate" || w.name === "control_mode") {
      w.label = "Control After Generate";
    }
  }
  let drawer = node.widgets.find((w) => w.name === DRAWER_WIDGET_NAME);
  if (spec.advanced && spec.advanced.length > 0) {
    if (!drawer) {
      drawer = new StoiqoSettingsDrawerWidget(node, spec);
      const firstAdvIdx = node.widgets.findIndex((w) => advSet.has(w.name));
      if (firstAdvIdx !== -1) {
        node.widgets.splice(firstAdvIdx, 0, drawer);
      } else {
        node.widgets.push(drawer);
      }
    } else {
      const currentDrawerIdx = node.widgets.indexOf(drawer);
      const firstAdvIdx = node.widgets.findIndex((w) => w !== drawer && advSet.has(w.name));
      if (firstAdvIdx !== -1 && currentDrawerIdx > firstAdvIdx) {
        node.widgets.splice(currentDrawerIdx, 1);
        node.widgets.splice(firstAdvIdx, 0, drawer);
      }
    }
  }
  const alwaysHiddenSet = new Set(spec.alwaysHidden || []);
  const conditions = spec.conditions || {};
  const refreshUX = (resizeHeight = false) => {
    const expanded = Boolean(node._stoiqoAdvExpanded);
    const drawerAllowed = !spec.drawerWhen || spec.drawerWhen(node);
    for (const w of node.widgets) {
      if (!w || w.name === DRAWER_WIDGET_NAME) continue;
      if (w.name === "control_after_generate" || w.name === "control_mode") {
        w.label = "Control After Generate";
      }
      if (alwaysHiddenSet.has(w.name)) {
        setWidgetVisibility(w, false);
        continue;
      }
      const inAdv = advSet.has(w.name);
      const condFn = conditions[w.name];
      const condOk = condFn ? Boolean(condFn(node)) : true;
      if (inAdv) {
        setWidgetVisibility(w, drawerAllowed && expanded && condOk);
      } else if (condFn) {
        setWidgetVisibility(w, condOk);
      }
    }
    if (typeof node.computeSize === "function") {
      const computed = node.computeSize();
      const minW = node.size && node.size[0] ? Math.max(node.size[0], 360) : 360;
      const targetH = resizeHeight ? Math.max(60, Math.ceil(computed[1])) : Math.max(node.size ? node.size[1] : 60, Math.ceil(computed[1]));
      if (typeof node.setSize === "function") {
        node.setSize([minW, targetH]);
      } else {
        node.size = [minW, targetH];
      }
    }
    node.setDirtyCanvas?.(true, true);
  };
  node._stoiqoApplyUX = refreshUX;
  for (const w of node.widgets) {
    if (!w || w.name === DRAWER_WIDGET_NAME) continue;
    if (w._stoiqoDefaultVal === void 0) {
      w._stoiqoDefaultVal = w.options && w.options.default !== void 0 ? w.options.default : w.value;
    }
    if (w._stoiqoUXHooked) continue;
    w._stoiqoUXHooked = true;
    const origCb = w.callback;
    w.callback = function(val) {
      if (origCb) origCb.apply(this, arguments);
      if (spec.onWidgetChange) {
        spec.onWidgetChange(node, w.name, val);
      }
      refreshUX(true);
    };
  }
  refreshUX(true);
}
function sanitizeNodeWidgetValues(node, info) {
  if (!node || !node.widgets) return;
  if (info && info.widgets_values_named && typeof info.widgets_values_named === "object") {
    for (const w of node.widgets) {
      if (!w || w.name === DRAWER_WIDGET_NAME || w.serialize === false) continue;
      const namedVal = info.widgets_values_named[w.name];
      if (namedVal !== void 0 && namedVal !== null && namedVal !== "") {
        w.value = namedVal;
        if (w.inputEl) w.inputEl.value = String(namedVal);
      }
    }
  }
  for (const w of node.widgets) {
    if (!w || w.name === DRAWER_WIDGET_NAME || w.serialize === false) continue;
    if (w.name === "subfolder") {
      if (typeof w.value === "number" || w.value === 90 || w.value === "90" || typeof w.value === "string" && !isNaN(Number(w.value.trim())) && w.value.trim() !== "" || w.value === "%data") {
        w.value = "StoiqoCreations/%date%";
        if (w.inputEl) w.inputEl.value = w.value;
      }
    }
    if (w.name === "text_watermark") {
      if (w.value === "Normal (Alpha)" || w.value === "Normal" || w.value === "Screen" || w.value === "Multiply") {
        w.value = "STOIQO";
        if (w.inputEl) w.inputEl.value = "STOIQO";
      }
    }
    if (w.type === "combo" && w.options && Array.isArray(w.options.values)) {
      if (!w.options.values.includes(w.value)) {
        let def = w.options.default !== void 0 && w.options.values.includes(w.options.default) ? w.options.default : w._stoiqoDefaultVal !== void 0 && w.options.values.includes(w._stoiqoDefaultVal) ? w._stoiqoDefaultVal : w.options.values[0];
        if (w.name === "sampler_name" && w.options.values.includes("euler")) def = "euler";
        if (w.name === "scheduler" && w.options.values.includes("beta")) def = "beta";
        if (w.name === "sidecar_metadata" && w.options.values.includes("None")) def = "None";
        if (w.name === "fusion_mode" && w.options.values.includes("Auto (Fuse 2-4 images, Batch if >4)")) def = "Auto (Fuse 2-4 images, Batch if >4)";
        if (w.name === "system_prompt" && w.options.values.includes("Auto-Detect / Balanced")) def = "Auto-Detect / Balanced";
        if (w.name === "deduplicate_tags" && w.options.values.includes("None")) def = "None";
        if (w.name === "format" && w.options.values.includes("PNG (Lossless)")) def = "PNG (Lossless)";
        w.value = def;
        if (w.inputEl) w.inputEl.value = String(def);
      }
    }
    if (w.type === "number" || w.options && (w.options.min !== void 0 || w.options.max !== void 0 || w.options.step !== void 0)) {
      let num = Number(w.value);
      const isInt = w.options && w.options.step && Number.isInteger(w.options.step) && (w.options.round === void 0 || w.options.round === 0);
      if (typeof w.value !== "number" || isNaN(num) || String(w.value).trim() === "") {
        if (w.name === "temperature") num = 0.65;
        else if (w.name === "max_new_tokens") num = 1024;
        else if (w.name === "top_p") num = 0.9;
        else if (w.name === "top_k") num = 50;
        else if (w.name === "repetition_penalty") num = 1.15;
        else if (w.name === "denoise") num = 1;
        else if (w.name === "variance_strength") num = 0;
        else if (w.name === "quality") num = 90;
        else {
          num = w.options && w.options.default !== void 0 ? Number(w.options.default) : w._stoiqoDefaultVal !== void 0 ? Number(w._stoiqoDefaultVal) : 0;
        }
      }
      if (w.name === "denoise" && num > 1) num = 1;
      if (w.name === "variance_strength" && num > 1) num = 0;
      if (w.name === "top_p" && num > 1) num = 0.9;
      if (w.name === "repetition_penalty" && (num < 1 || num > 2)) num = 1.15;
      if (w.name === "max_new_tokens" && (num < 128 || num > 4096)) num = 1024;
      if (w.name === "top_k" && (num < 1 || num > 100)) num = 50;
      if (w.name === "quality" && (num < 1 || num > 100)) num = 90;
      if (w.name === "opacity" && num <= 0.05) num = 0.85;
      if (w.name === "custom_scale" && num < 0.01) num = 0.125;
      if (w.options) {
        if (w.options.min !== void 0 && num < w.options.min) {
          num = w.options.default !== void 0 && w.options.default >= w.options.min ? w.options.default : w.options.min;
        }
        if (w.options.max !== void 0 && num > w.options.max) {
          num = w.options.default !== void 0 && w.options.default <= w.options.max ? w.options.default : w.options.max;
        }
      }
      w.value = isInt ? Math.round(num) : num;
      if (w.inputEl) w.inputEl.value = String(w.value);
    }
    if (w.type === "toggle" || typeof w.value === "boolean") {
      if (typeof w.value !== "boolean") {
        if (w.name === "save_workflow") w.value = true;
        else if (w.name === "privacy_mode") w.value = false;
        else w.value = w.options && w.options.default !== void 0 ? Boolean(w.options.default) : Boolean(w.value);
      }
    }
  }
}
function setupSettingsDrawers(nodeType, nodeData) {
  const spec = NODE_UX_SPECS[nodeData.name];
  if (!spec) return;
  const origCreated = nodeType.prototype.onNodeCreated;
  nodeType.prototype.onNodeCreated = function() {
    if (origCreated) origCreated.apply(this, arguments);
    const node = this;
    if (node.widgets) {
      for (const w of node.widgets) {
        if (w && w._stoiqoDefaultVal === void 0) {
          w._stoiqoDefaultVal = w.options && w.options.default !== void 0 ? w.options.default : w.value;
        }
      }
    }
    applyNodeUXSpec(node, spec);
  };
  const origConfigure = nodeType.prototype.onConfigure;
  nodeType.prototype.onConfigure = function(info) {
    if (origConfigure) origConfigure.apply(this, arguments);
    const node = this;
    applyNodeUXSpec(node, spec);
    sanitizeNodeWidgetValues(node, info);
  };
  const origSerialize = nodeType.prototype.serialize;
  nodeType.prototype.serialize = function() {
    sanitizeNodeWidgetValues(this);
    return origSerialize ? origSerialize.apply(this, arguments) : {};
  };
}

// src_js/index.js
app10.registerExtension({
  name: "Stoiqo.PromptGeneratorEngine.Dividers",
  async beforeQueue() {
    if (app10.graph && Array.isArray(app10.graph._nodes)) {
      for (const n of app10.graph._nodes) {
        if (n && (n.type?.startsWith("Stoiqo") || n.category === "STOIQO")) {
          sanitizeNodeWidgetValues(n);
        }
      }
    }
  },
  async beforeRegisterNodeDef(nodeType, nodeData, app11) {
    if (nodeData.category === "STOIQO" || nodeData.name && nodeData.name.startsWith("Stoiqo")) {
      setupTelemetryBadge(nodeType, nodeData, app11);
      const origConfigure = nodeType.prototype.onConfigure;
      nodeType.prototype.onConfigure = function(info) {
        if (origConfigure) origConfigure.apply(this, arguments);
        sanitizeNodeWidgetValues(this, info);
      };
      const origSerialize = nodeType.prototype.serialize;
      nodeType.prototype.serialize = function() {
        sanitizeNodeWidgetValues(this);
        return origSerialize ? origSerialize.apply(this, arguments) : {};
      };
    }
    setupShowPromptNode(nodeType, nodeData, app11);
    setupModelLoaderNode(nodeType, nodeData, app11);
    setupImageCompareNode(nodeType, nodeData, app11);
    setupDatasetNode(nodeType, nodeData, app11);
    setupIteratorNode(nodeType, nodeData, app11);
    setupTrioLoaderNode(nodeType, nodeData, app11);
    setupConcatNode(nodeType, nodeData, app11);
    setupProSaverNode(nodeType, nodeData, app11);
    setupMusicPromptNode(nodeType, nodeData, app11);
    setupPipelineNodes(nodeType, nodeData, app11);
    setupLoraStackNode(nodeType, nodeData, app11);
    setupPromptGeneratorNode(nodeType, nodeData, app11);
    setupSeedNode(nodeType, nodeData, app11);
    setupSettingsDrawers(nodeType, nodeData);
  }
});
