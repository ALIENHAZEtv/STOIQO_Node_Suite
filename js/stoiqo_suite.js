// src_js/index.js
import { app as app10 } from "../../scripts/app.js";

// src_js/nodes/showPromptNode.js
import { app as app2 } from "../../../scripts/app.js";
import { api as api2 } from "../../../scripts/api.js";
import { ComfyWidgets as ComfyWidgets2 } from "../../../scripts/widgets.js";

// src_js/utils/core.js
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";
import { ComfyWidgets } from "../../scripts/widgets.js";
var currentDownloadProgress = null;
var downloadClearTimer = null;
var comfyApi = api || typeof app !== "undefined" && app.api;
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
      }, 6e3);
    }
    if (app && app.graph) app.graph.setDirtyCanvas(true, true);
  });
}
var StoiqoSectionDividerWidget = class {
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
      const dlColor = isDone ? "#22c55e" : "#38bdf8";
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

// src_js/nodes/showPromptNode.js
var _streamListenersRegistered = false;
function ensureStreamListeners() {
  if (_streamListenersRegistered || typeof api2 === "undefined" || !api2.addEventListener) return;
  _streamListenersRegistered = true;
  api2.addEventListener("stoiqo_stream_start", (evt) => {
    const detail = evt.detail || {};
    const nodeId = detail.node_id;
    if (!nodeId || !app2.graph) return;
    const node = app2.graph.getNodeById(nodeId);
    if (!node) return;
    let tw = node.widgets?.find((w) => w.name === "display_text" || w.name === "text" || w.name === "synthesized_prompt");
    if (tw) {
      tw.value = "";
      if (tw.inputEl) tw.inputEl.value = "";
      node.setDirtyCanvas(true);
    }
  });
  api2.addEventListener("stoiqo_stream_token", (evt) => {
    const detail = evt.detail || {};
    const nodeId = detail.node_id;
    const token = detail.token;
    if (!nodeId || token === void 0 || !app2.graph) return;
    const node = app2.graph.getNodeById(nodeId);
    if (!node) return;
    let tw = node.widgets?.find((w) => w.name === "display_text" || w.name === "text" || w.name === "synthesized_prompt");
    if (tw) {
      tw.value = (tw.value || "") + token;
      if (tw.inputEl) {
        tw.inputEl.value = tw.value;
        tw.inputEl.scrollTop = tw.inputEl.scrollHeight;
      }
      node.setDirtyCanvas(true);
    }
  });
  api2.addEventListener("stoiqo_stream_complete", (evt) => {
    const detail = evt.detail || {};
    const nodeId = detail.node_id;
    if (!nodeId || !app2.graph) return;
    const node = app2.graph.getNodeById(nodeId);
    if (node) {
      node.setDirtyCanvas(true, true);
    }
  });
}
function setupShowPromptNode(nodeType, nodeData, app11) {
  ensureStreamListeners();
  const showPromptTargetNames = [
    "StoiqoShowPromptNode",
    "[STOIQO] Show Prompt"
  ];
  if (showPromptTargetNames.includes(nodeData.name)) {
    let setupShowPromptNode2 = function(node) {
      if (!node) return;
      if (node.bgcolor === "#0e1218" || node.bgcolor === "#0b1411") {
        delete node.bgcolor;
      }
      if (node.color === "#18202c" || node.color === "#14251f") {
        delete node.color;
      }
      if (node.size) {
        if (node.size[0] < SHOW_MIN_WIDTH) node.size[0] = SHOW_MIN_WIDTH;
        if (node.size[1] < SHOW_MIN_HEIGHT) node.size[1] = SHOW_MIN_HEIGHT;
      }
      node.widgets = node.widgets || [];
      let textWidget = node.widgets.find((w) => w.name === "display_text");
      if (!textWidget) {
        if (typeof ComfyWidgets2 !== "undefined" && ComfyWidgets2["STRING"]) {
          textWidget = ComfyWidgets2["STRING"](
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
        textWidget.options = textWidget.options || {};
        textWidget.options.serialize = false;
        const styleInput = (el) => {
          if (!el) return;
          el.readOnly = true;
          el.placeholder = "Generated prompt will be displayed here...";
          el.style.boxSizing = "border-box";
          el.style.opacity = "0.92";
          el.style.fontSize = "11.5px";
          el.style.lineHeight = "1.45";
          el.style.fontFamily = "monospace, -apple-system, sans-serif";
          el.style.resize = "vertical";
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
      let copyBtn = node.widgets.find((w) => w._isCopyButton);
      if (!copyBtn) {
        copyBtn = node.addWidget(
          "button",
          "\u{1F4CB} Copy Prompt to Clipboard",
          null,
          function() {
            const tw = node.widgets?.find((w) => w.name === "display_text" || w.name === "text");
            const textVal = tw ? tw.value || tw.inputEl && tw.inputEl.value || "" : "";
            if (textVal && navigator.clipboard) {
              navigator.clipboard.writeText(String(textVal));
              const origLabel = this.name;
              this.name = "\u2713 Copied to Clipboard!";
              node.setDirtyCanvas(true);
              setTimeout(() => {
                this.name = origLabel;
                node.setDirtyCanvas(true);
              }, 1800);
            }
          },
          { serialize: false }
        );
        copyBtn._isCopyButton = true;
        copyBtn.options = { serialize: false };
      }
      const textIdx = node.widgets.findIndex((w) => w.name === "display_text");
      if (textIdx !== -1 && copyBtn) {
        const curBtnIdx = node.widgets.indexOf(copyBtn);
        if (curBtnIdx !== -1 && curBtnIdx < textIdx) {
          node.widgets.splice(curBtnIdx, 1);
          node.widgets.splice(textIdx, 0, copyBtn);
        }
      }
      node.setDirtyCanvas(true, true);
    };
    const SHOW_MIN_WIDTH = 460;
    const SHOW_MIN_HEIGHT = 220;
    const origShowCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function() {
      if (origShowCreated) origShowCreated.apply(this, arguments);
      setupShowPromptNode2(this);
    };
    const origShowConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function() {
      if (origShowConfigure) origShowConfigure.apply(this, arguments);
      setupShowPromptNode2(this);
    };
    const origShowExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function(message) {
      if (origShowExecuted) origShowExecuted.apply(this, arguments);
      if (message && message.text) {
        let tw = this.widgets?.find((w) => w.name === "display_text");
        if (!tw) {
          setupShowPromptNode2(this);
          tw = this.widgets?.find((w) => w.name === "display_text");
        }
        if (tw) {
          let textStr = "";
          if (Array.isArray(message.text)) {
            textStr = message.text.join("\n\n---\n\n");
          } else {
            textStr = String(message.text || "");
          }
          tw.value = textStr;
          if (tw.inputEl) {
            tw.inputEl.value = textStr;
          }
        }
        this.setDirtyCanvas(true, true);
      }
    };
  }
}

// src_js/nodes/modelLoaderNode.js
import { app as app3 } from "../../../scripts/app.js";
import { api as api3 } from "../../../scripts/api.js";
import { ComfyWidgets as ComfyWidgets3 } from "../../../scripts/widgets.js";
function setupModelLoaderNode(nodeType, nodeData, app11) {
  const loaderTargetNames = [
    "StoiqoVLMModelLoaderNode",
    "[STOIQO] VLM Model Loader"
  ];
  if (loaderTargetNames.includes(nodeData.name)) {
    let setupModelLoader = function(node) {
      if (!node || !node.widgets) return;
      if (node.size && node.size[0] < MIN_NODE_WIDTH) node.size[0] = MIN_NODE_WIDTH;
      node.widgets = node.widgets.filter((w) => !w.isStoiqoDivider);
      SECTIONS.forEach((sec) => {
        const idx = node.widgets.findIndex((w) => w.name === sec.targetWidget);
        if (idx !== -1) {
          const div = new StoiqoSectionDividerWidget(sec.num, sec.title, sec.color);
          node.widgets.splice(idx, 0, div);
        }
      });
      let browseBtn = node.widgets.find((w) => w._isStoiqoBrowse);
      if (!browseBtn) {
        browseBtn = node.addWidget(
          "button",
          "\u{1F4C1} Browse Model Folder on Disk",
          null,
          async function() {
            const pathWidget = node.widgets.find((w) => w.name === "local_model_path");
            const currentPath = pathWidget ? pathWidget.value || "" : "";
            const origLabel = this.name;
            this.name = "\u23F3 Selecting folder in Windows...";
            node.setDirtyCanvas(true);
            try {
              const resp = await api3.fetchApi("/stoiqo/browse_folder", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ initial_dir: currentPath })
              });
              if (resp.ok) {
                const res = await resp.json();
                if (res && res.path) {
                  if (pathWidget) {
                    pathWidget.value = res.path;
                    if (pathWidget.inputEl) pathWidget.inputEl.value = res.path;
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
        browseBtn.options = { serialize: false };
        const pathIdx = node.widgets.findIndex((w) => w.name === "local_model_path");
        if (pathIdx !== -1) {
          const curIdx = node.widgets.indexOf(browseBtn);
          if (curIdx !== -1) {
            node.widgets.splice(curIdx, 1);
            node.widgets.splice(pathIdx + 1, 0, browseBtn);
          }
        }
      }
      function updateVisibility() {
        const presetW = node.widgets.find((w) => w.name === "model_preset");
        const pathW = node.widgets.find((w) => w.name === "local_model_path");
        const btnW = node.widgets.find((w) => w._isStoiqoBrowse);
        const isCustom = presetW && String(presetW.value).includes("Custom Model");
        if (pathW) {
          pathW.hidden = !isCustom;
          if (!isCustom) {
            pathW.computeSize = () => [0, -4];
            if (!pathW._origDraw) pathW._origDraw = pathW.draw;
            pathW.draw = () => {
            };
          } else {
            delete pathW.computeSize;
            if (pathW._origDraw) pathW.draw = pathW._origDraw;
          }
        }
        if (btnW) {
          btnW.hidden = !isCustom;
          if (!isCustom) {
            btnW.computeSize = () => [0, -4];
            if (!btnW._origDraw) btnW._origDraw = btnW.draw;
            btnW.draw = () => {
            };
          } else {
            delete btnW.computeSize;
            if (btnW._origDraw) btnW.draw = btnW._origDraw;
          }
        }
        node.setDirtyCanvas(true, true);
      }
      const presetWidget = node.widgets.find((w) => w.name === "model_preset");
      if (presetWidget) {
        const origCallback = presetWidget.callback;
        presetWidget.callback = function() {
          if (origCallback) origCallback.apply(this, arguments);
          updateVisibility();
        };
      }
      updateVisibility();
      node.setDirtyCanvas(true, true);
    };
    const MIN_NODE_WIDTH = 440;
    const SECTIONS = [
      { targetWidget: "model_preset", num: "1", title: "ENGINE & HARDWARE", color: "#38bdf8" }
    ];
    const origCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function() {
      if (origCreated) origCreated.apply(this, arguments);
      setupModelLoader(this);
    };
    const origConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function() {
      if (origConfigure) origConfigure.apply(this, arguments);
      setupModelLoader(this);
    };
  }
}

// src_js/nodes/visualDiffNode.js
import { app as app4 } from "../../../scripts/app.js";
import { api as api4 } from "../../../scripts/api.js";
import { ComfyWidgets as ComfyWidgets4 } from "../../../scripts/widgets.js";
function setupVisualDiffNode(nodeType, nodeData, app11) {
  const diffTargetNames = [
    "StoiqoVisualDiffNode",
    "[STOIQO] Visual Diff & Forensic Inspector"
  ];
  if (diffTargetNames.includes(nodeData.name)) {
    let setupVisualDiff = function(node) {
      if (!node || !node.widgets) return;
      if (node.size && node.size[0] < MIN_NODE_WIDTH) node.size[0] = MIN_NODE_WIDTH;
      const dirW = node.widgets.find((w) => w.name === "custom_directives");
      if (dirW) {
        dirW.computeSize = function(width) {
          return [width, 76];
        };
      }
      node.widgets = node.widgets.filter((w) => !w.isStoiqoDivider);
      SECTIONS.forEach((sec) => {
        const idx = node.widgets.findIndex((w) => w.name === sec.targetWidget);
        if (idx !== -1) {
          const div = new StoiqoSectionDividerWidget(sec.num, sec.title, sec.color);
          node.widgets.splice(idx, 0, div);
        }
      });
      let browseBtn = node.widgets.find((w) => w._isStoiqoBrowse);
      if (!browseBtn) {
        browseBtn = node.addWidget(
          "button",
          "\u{1F4C1} Browse Model Folder on Disk",
          null,
          async function() {
            const pathWidget = node.widgets.find((w) => w.name === "local_model_path");
            const currentPath = pathWidget ? pathWidget.value || "" : "";
            const origLabel = this.name;
            this.name = "\u23F3 Selecting folder in Windows...";
            node.setDirtyCanvas(true);
            try {
              const resp = await api4.fetchApi("/stoiqo/browse_folder", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ initial_dir: currentPath })
              });
              if (resp.ok) {
                const res = await resp.json();
                if (res && res.path) {
                  if (pathWidget) {
                    pathWidget.value = res.path;
                    if (pathWidget.inputEl) pathWidget.inputEl.value = res.path;
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
        browseBtn.options = { serialize: false };
        const pathIdx = node.widgets.findIndex((w) => w.name === "local_model_path");
        if (pathIdx !== -1) {
          const curIdx = node.widgets.indexOf(browseBtn);
          if (curIdx !== -1) {
            node.widgets.splice(curIdx, 1);
            node.widgets.splice(pathIdx + 1, 0, browseBtn);
          }
        }
      }
      function updateDiffVisibility() {
        const presetW = node.widgets.find((w) => w.name === "model_preset");
        const pathW = node.widgets.find((w) => w.name === "local_model_path");
        const btnW = node.widgets.find((w) => w._isStoiqoBrowse);
        const isCustom = presetW && String(presetW.value).includes("Custom Model");
        if (pathW) {
          pathW.hidden = !isCustom;
          if (!isCustom) {
            pathW.computeSize = () => [0, -4];
            if (!pathW._origDraw) pathW._origDraw = pathW.draw;
            pathW.draw = () => {
            };
          } else {
            delete pathW.computeSize;
            if (pathW._origDraw) pathW.draw = pathW._origDraw;
          }
        }
        if (btnW) {
          btnW.hidden = !isCustom;
          if (!isCustom) {
            btnW.computeSize = () => [0, -4];
            if (!btnW._origDraw) btnW._origDraw = btnW.draw;
            btnW.draw = () => {
            };
          } else {
            delete btnW.computeSize;
            if (btnW._origDraw) btnW.draw = btnW._origDraw;
          }
        }
        node.setDirtyCanvas(true, true);
      }
      const presetWidget = node.widgets.find((w) => w.name === "model_preset");
      if (presetWidget) {
        const origCallback = presetWidget.callback;
        presetWidget.callback = function() {
          if (origCallback) origCallback.apply(this, arguments);
          updateDiffVisibility();
        };
      }
      updateDiffVisibility();
      node.setDirtyCanvas(true, true);
    };
    const MIN_NODE_WIDTH = 460;
    const SECTIONS = [
      { targetWidget: "analysis_focus", num: "1", title: "FORENSIC DIRECTIVES", color: "#c084fc" },
      { targetWidget: "seed", num: "2", title: "SAMPLING & RESOLUTION", color: "#facc15" },
      { targetWidget: "model_preset", num: "3", title: "STANDALONE ENGINE FALLBACK", color: "#38bdf8" }
    ];
    const origDiffCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function() {
      if (origDiffCreated) origDiffCreated.apply(this, arguments);
      setupVisualDiff(this);
    };
    const origDiffConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function() {
      if (origDiffConfigure) origDiffConfigure.apply(this, arguments);
      setupVisualDiff(this);
    };
  }
}

// src_js/nodes/imageCompareNode.js
import { app as app5 } from "../../../scripts/app.js";
import { api as api5 } from "../../../scripts/api.js";
import { ComfyWidgets as ComfyWidgets5 } from "../../../scripts/widgets.js";
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
      return api5.apiURL(`/view?${params.toString()}`);
    }, setupImageCompareNodeUI = function(node) {
      if (!node) return;
      node.hideOutputImages = true;
      node.imgs = null;
      node.images = null;
      if (!node.size || node.size[0] < MIN_WIDTH2) node.size = [MIN_WIDTH2, MIN_HEIGHT];
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
            if (vStr.includes("toggle") || vStr.includes("flicker")) {
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
        app11.canvas.canvas.addEventListener("wheel", (e) => {
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
        }, { capture: true, passive: false });
      }
      node.setDirtyCanvas(true, true);
    };
    const MIN_WIDTH2 = 520;
    const MIN_HEIGHT = 560;
    class StoiqoCompareCanvasWidget {
      constructor(node) {
        this.type = "custom";
        this.name = "_stoiqo_compare_canvas";
        this.value = [];
        this.options = { serialize: false };
        this.node = node;
        this.imgA = null;
        this.imgB = null;
        this.imagesData = null;
        this.labelA = "Original";
        this.labelB = "Upscaled";
        this.splitX = 0.5;
        this.zoom = 1;
        this.panX = 0;
        this.panY = 0;
        this.mode = "split";
        this.toggleShowB = false;
        this.isDraggingSplit = false;
        this.isPanning = false;
        this.lastMouse = [0, 0];
        this.btnHitAreas = [];
        this.viewportRect = { x: 0, y: 0, w: 0, h: 0 };
        this.loadError = null;
        this._activePointerCleanup = null;
      }
      serializeValue() {
        return void 0;
      }
      computeSize(width) {
        return [width, 440];
      }
      computeLayoutSize() {
        return { minHeight: 340, minWidth: 420 };
      }
      setImages(dataList) {
        if (!dataList || dataList.length < 2) return;
        const latestData = dataList.slice(-2);
        this.imagesData = latestData;
        this.value = latestData;
        if (this.node) {
          this.node.properties = this.node.properties || {};
          this.node.properties.stoiqo_images = latestData;
        }
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
        this.loadError = null;
        const urlA = imageDataToUrl(latestData[0]);
        const urlB = imageDataToUrl(latestData[1]);
        this.imgA = new Image();
        this.imgB = new Image();
        this.imgA.onload = () => {
          if (this.node) this.node.setDirtyCanvas(true, true);
        };
        this.imgB.onload = () => {
          if (this.node) this.node.setDirtyCanvas(true, true);
        };
        this.imgA.onerror = () => {
          this.loadError = "Impossibile caricare immagine A";
          if (this.node) this.node.setDirtyCanvas(true, true);
        };
        this.imgB.onerror = () => {
          this.loadError = "Impossibile caricare immagine B";
          if (this.node) this.node.setDirtyCanvas(true, true);
        };
        this.imgA.src = urlA;
        this.imgB.src = urlB;
        this.labelA = latestData[0].label || "Original";
        this.labelB = latestData[1].label || "Upscaled";
        this.resetView();
      }
      resetView() {
        this.zoom = 1;
        this.panX = 0;
        this.panY = 0;
        this.splitX = 0.5;
        this.toggleShowB = false;
        if (this.node) this.node.setDirtyCanvas(true, true);
      }
      attachWindowDragListeners() {
        if (this._activePointerCleanup) {
          this._activePointerCleanup();
        }
        const cleanup = () => {
          this.isDraggingSplit = false;
          this.isPanning = false;
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
        const nodeW = width || (node.size ? node.size[0] : MIN_WIDTH2);
        const slotH = typeof height === "number" && height > 0 ? height : 440;
        const vY = posY + 6;
        const vH = Math.max(260, Math.min(slotH - 12, 1600));
        const vW = nodeW - 24;
        const vX = 12;
        this.viewportRect = { x: vX, y: vY + 32, w: vW, h: vH - 32 };
        this.btnHitAreas = [];
        ctx.save();
        const barY = vY;
        const barH = 26;
        ctx.fillStyle = "rgba(15, 23, 42, 0.65)";
        if (ctx.roundRect) {
          ctx.beginPath();
          ctx.roundRect(vX, barY, vW, barH, 4);
          ctx.fill();
        } else {
          ctx.fillRect(vX, barY, vW, barH);
        }
        const modes = [
          { key: "only_a", label: "Solo A", activeColor: "#38bdf8" },
          { key: "only_b", label: "Solo B", activeColor: "#c084fc" },
          { key: "split", label: "\u2194 Slider A-B", activeColor: "#2dd4bf" },
          { key: "toggle", label: this.mode === "toggle" ? this.toggleShowB ? "\u{1F441} B (Click A)" : "\u{1F441} A (Click B)" : "\u{1F441} Toggle A/B", activeColor: "#f59e0b" },
          { key: "side", label: "\u25EB Side-by-Side", activeColor: "#10b981" }
        ];
        let btnX = vX + 6;
        ctx.font = "bold 9px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
        ctx.textBaseline = "middle";
        modes.forEach((m) => {
          const active = this.mode === m.key;
          const textW = ctx.measureText(m.label).width;
          const bW = textW + 14;
          const bH = 18;
          const bY = barY + 4;
          const col = m.activeColor || "#2dd4bf";
          ctx.fillStyle = active ? m.key === "only_a" ? "rgba(56, 189, 248, 0.22)" : m.key === "only_b" ? "rgba(192, 132, 252, 0.22)" : m.key === "toggle" ? "rgba(245, 158, 11, 0.25)" : m.key === "side" ? "rgba(16, 185, 129, 0.22)" : "rgba(45, 212, 191, 0.22)" : "rgba(255, 255, 255, 0.06)";
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
          ctx.fillText(m.label, btnX + 7, bY + bH / 2);
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
          btnX += bW + 6;
        });
        const resetLabel = "\u27F2 Reset Zoom";
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
        ctx.fillText(resetLabel, rX + 7, rY + 9);
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
        const zX = rX - zTextW - 14;
        ctx.fillStyle = this.zoom > 1.01 ? "#38bdf8" : "#64748b";
        ctx.fillText(zoomLabel, zX, rY + 9);
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
            ctx.fillText("\u23F3 Caricamento anteprima immagini...", vp.x + vp.w / 2, vp.y + vp.h / 2);
          } else {
            ctx.fillText("Collega image_a e image_b, poi clicca Queue Prompt per visualizzare", vp.x + vp.w / 2, vp.y + vp.h / 2 - 10);
            ctx.font = "10px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
            ctx.fillStyle = "#64748b";
            ctx.fillText("Slider A-B \u2022 Synchronized Pan & Zoom \u2022 Toggle A/B \u2022 Side-by-Side", vp.x + vp.w / 2, vp.y + vp.h / 2 + 12);
          }
          ctx.restore();
          return;
        }
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
        const natWA = this.imgA.naturalWidth;
        const natHA = this.imgA.naturalHeight;
        const natWB = this.imgB.naturalWidth;
        const natHB = this.imgB.naturalHeight;
        const centerX = vp.x + vp.w / 2;
        const centerY = vp.y + vp.h / 2;
        const fitA = computeFit(natWA, natHA, vp.w, vp.h);
        const fitB = computeFit(natWB, natHB, vp.w, vp.h);
        const halfWA = fitA.w / 2;
        const halfHA = fitA.h / 2;
        const halfWB = fitB.w / 2;
        const halfHB = fitB.h / 2;
        const renderImageA = (targetCtx = ctx) => {
          try {
            targetCtx.save();
            targetCtx.translate(centerX + this.panX * this.zoom, centerY + this.panY * this.zoom);
            targetCtx.scale(this.zoom, this.zoom);
            targetCtx.drawImage(this.imgA, -halfWA, -halfHA, fitA.w, fitA.h);
            targetCtx.restore();
          } catch (err) {
            console.warn("[STOIQO Compare] Errore renderImageA:", err);
          }
        };
        const renderImageB = (targetCtx = ctx) => {
          try {
            targetCtx.save();
            targetCtx.translate(centerX + this.panX * this.zoom, centerY + this.panY * this.zoom);
            targetCtx.scale(this.zoom, this.zoom);
            targetCtx.drawImage(this.imgB, -halfWB, -halfHB, fitB.w, fitB.h);
            targetCtx.restore();
          } catch (err) {
            console.warn("[STOIQO Compare] Errore renderImageB:", err);
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
        } else if (this.mode === "split") {
          const splitScreenX = vp.x + this.splitX * vp.w;
          ctx.save();
          ctx.beginPath();
          ctx.rect(vp.x, vp.y, this.splitX * vp.w, vp.h);
          ctx.clip();
          renderImageA();
          ctx.restore();
          ctx.save();
          ctx.beginPath();
          ctx.rect(splitScreenX, vp.y, (1 - this.splitX) * vp.w, vp.h);
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
          ctx.fillStyle = "#2dd4bf";
          ctx.font = "bold 10px sans-serif";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText("\u25C4\u25BA", splitScreenX, pillY + pillH / 2 + 1);
          ctx.restore();
        } else if (this.mode === "toggle") {
          ctx.save();
          ctx.beginPath();
          ctx.rect(vp.x, vp.y, vp.w, vp.h);
          ctx.clip();
          if (this.toggleShowB) {
            renderImageB();
          } else {
            renderImageA();
          }
          ctx.restore();
        } else if (this.mode === "side") {
          const midX = vp.x + vp.w / 2;
          const halfW = vp.w / 2 - 1;
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
          const centerSideB_X = midX + 1 + halfW / 2;
          const fitSideB = computeFit(natWB, natHB, halfW, vp.h);
          ctx.save();
          ctx.beginPath();
          ctx.rect(midX + 1, vp.y, halfW, vp.h);
          ctx.clip();
          ctx.translate(centerSideB_X + this.panX * this.zoom, centerY + this.panY * this.zoom);
          ctx.scale(this.zoom, this.zoom);
          ctx.drawImage(this.imgB, -fitSideB.w / 2, -fitSideB.h / 2, fitSideB.w, fitSideB.h);
          ctx.restore();
          ctx.strokeStyle = "rgba(255, 255, 255, 0.25)";
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(midX, vp.y);
          ctx.lineTo(midX, vp.y + vp.h);
          ctx.stroke();
        }
        ctx.font = "bold 9px sans-serif";
        ctx.textAlign = "left";
        ctx.textBaseline = "middle";
        if (this.mode === "toggle") {
          const showingB = this.toggleShowB;
          const tText = showingB ? `\u{1F441} B: ${this.labelB} (${natWB}\xD7${natHB}) \u2022 Clicca per A` : `\u{1F441} A: ${this.labelA} (${natWA}\xD7${natHA}) \u2022 Clicca per B`;
          const tW = ctx.measureText(tText).width + 16;
          ctx.fillStyle = "rgba(15, 23, 42, 0.88)";
          ctx.strokeStyle = showingB ? "#c084fc" : "#38bdf8";
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
          ctx.fillStyle = showingB ? "#c084fc" : "#38bdf8";
          ctx.fillText(tText, vp.x + 16, vp.y + 18);
        } else {
          if (this.mode === "only_a" || this.mode === "split" || this.mode === "side") {
            const labelAText = `\u25C4 A: ${this.labelA.slice(0, 10)} (${natWA}\xD7${natHA})`;
            const lAW = ctx.measureText(labelAText).width + 12;
            ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
            ctx.fillRect(vp.x + 8, vp.y + 8, lAW, 18);
            ctx.fillStyle = "#38bdf8";
            ctx.fillText(labelAText, vp.x + 14, vp.y + 17);
          }
          if (this.mode === "only_b" || this.mode === "split" || this.mode === "side") {
            const labelBText = `B: ${this.labelB.slice(0, 10)} (${natWB}\xD7${natHB}) \u25BA`;
            const lBW = ctx.measureText(labelBText).width + 12;
            ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
            ctx.fillRect(vp.x + vp.w - lBW - 8, vp.y + 8, lBW, 18);
            ctx.fillStyle = "#c084fc";
            ctx.fillText(labelBText, vp.x + vp.w - lBW - 2, vp.y + 17);
          }
        }
        if (this.zoom > 1.05) {
          const hint = "\u{1F50D} Trascina per Pan \u2022 Rotella per Zoom";
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
        const vp = this.viewportRect;
        if (mx >= vp.x && mx <= vp.x + vp.w && my >= vp.y && my <= vp.y + vp.h) {
          if (this.mode === "toggle") {
            this.toggleShowB = !this.toggleShowB;
            if (this.node) this.node.setDirtyCanvas(true, true);
            if (e && e.stopPropagation) e.stopPropagation();
            return true;
          }
          if (this.mode === "split") {
            const splitPixelX = vp.x + this.splitX * vp.w;
            if (this.zoom <= 1.05 || Math.abs(mx - splitPixelX) < 40) {
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
      if (cachedImages && Array.isArray(cachedImages) && cachedImages.length >= 2 && this.cmpWidget) {
        this.cmpWidget.setImages(cachedImages.slice(-2));
      }
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
            if (mStr.includes("toggle") || mStr.includes("flicker")) {
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
      function updateCustomDimsVisibility() {
        const aspectWidget2 = node.widgets.find((w) => w.name === "aspect_ratio");
        const wWidget = node.widgets.find((w) => w.name === "custom_width");
        const hWidget = node.widgets.find((w) => w.name === "custom_height");
        if (!wWidget || !hWidget) return;
        const isCustom = aspectWidget2 && String(aspectWidget2.value || "").includes("Custom");
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
        if (typeof node.computeSize === "function") {
          const computed = node.computeSize();
          node.size[0] = Math.max(node.size[0] || 0, MIN_RES_WIDTH);
          node.size[1] = Math.max(Math.ceil(computed[1]), 80);
        }
        node.setDirtyCanvas(true, true);
      }
      const aspectWidget = node.widgets.find((w) => w.name === "aspect_ratio");
      if (aspectWidget && !aspectWidget._stoiqoHooked) {
        aspectWidget._stoiqoHooked = true;
        const origCallback = aspectWidget.callback;
        aspectWidget.callback = function(val) {
          if (origCallback) origCallback.apply(this, arguments);
          updateCustomDimsVisibility();
        };
      }
      updateCustomDimsVisibility();
    };
    const MIN_RES_WIDTH = 380;
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
function setupDatasetNode(nodeType, nodeData, app11) {
  const targetNames = [
    "StoiqoDatasetWriterNode",
    "[STOIQO] Dataset & LoRA Toolkit"
  ];
  if (targetNames.includes(nodeData.name)) {
    let setupDatasetNode2 = function(node) {
      if (!node || !node.widgets) return;
      if (node.size && node.size[0] < MIN_NODE_WIDTH) {
        node.size[0] = MIN_NODE_WIDTH;
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
      setupDatasetNode2(this);
    };
  }
}

// src_js/nodes/iteratorNode.js
import { api as api6 } from "../../../scripts/api.js";
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
    };
    const MIN_NODE_WIDTH = 460;
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function() {
      if (onNodeCreated) {
        onNodeCreated.apply(this, arguments);
      }
      setupIteratorNodeUI(this);
    };
  }
}

// src_js/nodes/trioLoaderNode.js
import { app as app6 } from "../../../scripts/app.js";
import { api as api7 } from "../../../scripts/api.js";
function setupTrioLoaderNode(nodeType, nodeData, appInstance) {
  const targetNames = [
    "StoiqoTripleImageLoaderNode",
    "[STOIQO] Trio Image Loader (Hero & Thumbs)"
  ];
  if (!targetNames.includes(nodeData.name)) return;
  const MIN_WIDTH2 = 460;
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
        const slotColors = ["#a855f7", "#38bdf8", "#10b981"];
        const slotColor = slotColors[activeIdx] || "#a855f7";
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
          ctx.fillStyle = "#38bdf8";
          ctx.fillText(resStr, pad + availableWidth - tw - 12, heroY + 23);
        }
      } else {
        ctx.fillStyle = "#475569";
        ctx.font = "bold 12px Inter, system-ui, sans-serif";
        ctx.textAlign = "center";
        const isNone = !activeRaw || activeRaw === "none";
        const emptyMsg = isNone ? `[Slot ${this.activeFocus}: Nessuna immagine selezionata]` : `[Slot ${this.activeFocus}: Caricamento in corso...]`;
        ctx.fillText(emptyMsg, pad + availableWidth / 2, heroY + heroHeight / 2 - 8);
        ctx.font = "10px Inter, system-ui, sans-serif";
        ctx.fillStyle = "#334155";
        ctx.fillText("Seleziona un'immagine dal menu sopra per visualizzarla", pad + availableWidth / 2, heroY + heroHeight / 2 + 12);
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
        ctx.fillStyle = isFocused ? "#1a162b" : "#0d111a";
        ctx.strokeStyle = isFocused ? "#c084fc" : "#242d42";
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
        ctx.fillStyle = isFocused ? "#c084fc" : "#64748b";
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
    this.size = this.size || [MIN_WIDTH2, MIN_HEIGHT];
    if (this.size[0] < MIN_WIDTH2) this.size[0] = MIN_WIDTH2;
    if (this.size[1] < MIN_HEIGHT) this.size[1] = MIN_HEIGHT;
    this.addCustomWidget(new StoiqoSectionDividerWidget(1, "MULTI-IMAGE TRIO LOADER", "#a855f7"));
    const galleryWidget = new StoiqoTrioGalleryWidget(this);
    this.addCustomWidget(galleryWidget);
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
import { app as app7 } from "../../../scripts/app.js";
function setupConcatNode(nodeType, nodeData, appInstance) {
  const concatTargetNames = [
    "StoiqoTextConcatenateNode",
    "[STOIQO] Text Concatenate & Clean"
  ];
  if (!concatTargetNames.includes(nodeData.name)) return;
  const MIN_WIDTH2 = 420;
  const MAX_SLOTS = 8;
  const TEXT_BOX_HEIGHT = 56;
  class StoiqoTokenHudWidget {
    constructor(node) {
      this.type = "custom";
      this.name = "_stoiqo_token_hud";
      this.value = {};
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
      ctx.fillStyle = "#38bdf8";
      ctx.textAlign = "left";
      ctx.fillText("\u{1F4CA} STATS", pad + 8, posY + 15);
      ctx.font = "9px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
      ctx.fillStyle = "#94a3b8";
      const statText = `Parole: ${this.stats.words}   \u2022   Caratteri: ${this.stats.chars}   \u2022   Est. Token: ~${this.stats.tokens}`;
      ctx.fillText(statText, pad + 60, posY + 15);
      ctx.restore();
    }
  }
  function configureTextBoxWidget(w, isVisible) {
    if (!w) return;
    if (isVisible) {
      w.hidden = false;
      w.computeSize = function(width) {
        return [width, TEXT_BOX_HEIGHT];
      };
      const styleInputEl = (el) => {
        if (!el) return;
        el.style.boxSizing = "border-box";
        el.style.height = `${TEXT_BOX_HEIGHT}px`;
        el.style.minHeight = `${TEXT_BOX_HEIGHT}px`;
        el.style.maxHeight = `${TEXT_BOX_HEIGHT}px`;
        el.style.resize = "none";
        el.style.margin = "0px";
        el.style.padding = "4px 8px";
        el.style.fontSize = "11px";
        el.style.lineHeight = "1.4";
        el.hidden = false;
        el.style.display = "";
      };
      if (w.inputEl) {
        styleInputEl(w.inputEl);
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
    node.size = node.size || [MIN_WIDTH2, 360];
    if (node.size[0] < MIN_WIDTH2) node.size[0] = MIN_WIDTH2;
    let initialVisible = 2;
    for (let i = 3; i <= MAX_SLOTS; i++) {
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
    configureTextBoxWidget(node.widgets.find((w) => w.name === "text_1"), true);
    configureTextBoxWidget(node.widgets.find((w) => w.name === "text_2"), true);
    function refreshSlots() {
      const visibleCount = node._stoiqoVisibleSlots || 2;
      for (let i = 3; i <= MAX_SLOTS; i++) {
        const w = node.widgets.find((x) => x.name === `text_${i}`);
        if (w) {
          configureTextBoxWidget(w, i <= visibleCount);
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
        node._stoiqoAddBtn.name = canAdd ? `[+] Aggiungi Box Testo (${visibleCount}/${MAX_SLOTS})` : `[\u2713] Massimo ${MAX_SLOTS} Box Raggiunto`;
      }
      if (node._stoiqoRemBtn) {
        const canRemove = visibleCount > 2;
        node._stoiqoRemBtn.hidden = !canRemove;
        node._stoiqoRemBtn.computeSize = canRemove ? function(w) {
          return [w, 24];
        } : function() {
          return [0, -4];
        };
      }
      if (typeof node.computeSize === "function") {
        const sz = node.computeSize();
        node.setSize([Math.max(node.size[0] || 0, MIN_WIDTH2), Math.max(Math.ceil(sz[1]), 220)]);
      }
      node.setDirtyCanvas(true, true);
      if (app7.graph && app7.graph.setDirtyCanvas) {
        app7.graph.setDirtyCanvas(true, true);
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
        const canAdd = (node._stoiqoVisibleSlots || 2) < MAX_SLOTS;
        const pad = 12;
        const btnW = width - pad * 2;
        const btnH = 24;
        ctx.save();
        ctx.fillStyle = canAdd ? "rgba(168, 85, 247, 0.20)" : "rgba(255, 255, 255, 0.05)";
        ctx.strokeStyle = canAdd ? "#a855f7" : "rgba(255, 255, 255, 0.12)";
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
          if (node._stoiqoVisibleSlots > 2) {
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
    const orderPriority = {
      "text_1": 1,
      "text_2": 2,
      "text_3": 3,
      "text_4": 4,
      "text_5": 5,
      "text_6": 6,
      "text_7": 7,
      "text_8": 8,
      "_stoiqo_add_btn": 9,
      "_stoiqo_rem_btn": 10,
      "separator": 11,
      "custom_separator": 12,
      "prefix": 13,
      "suffix": 14,
      "deduplicate_tags": 15,
      "clean_whitespace": 16,
      "convert_underscores": 17,
      "skip_empty": 18,
      "_stoiqo_token_hud": 19
    };
    node._stoiqoAddBtn.name_key = "_stoiqo_add_btn";
    node._stoiqoRemBtn.name_key = "_stoiqo_rem_btn";
    node.widgets.sort((a, b) => {
      const pa = orderPriority[a.name_key || a.name] || 99;
      const pb = orderPriority[b.name_key || b.name] || 99;
      return pa - pb;
    });
    let tokenHud = node.widgets.find((w) => w instanceof StoiqoTokenHudWidget);
    if (!tokenHud) {
      tokenHud = new StoiqoTokenHudWidget(node);
      node.addCustomWidget(tokenHud);
      node._stoiqo_hud = tokenHud;
    }
    const sepW = node.widgets.find((w) => w.name === "separator");
    if (sepW && !sepW._stoiqoHooked) {
      sepW._stoiqoHooked = true;
      const origSepCb = sepW.callback;
      sepW.callback = function() {
        if (origSepCb) origSepCb.apply(this, arguments);
        refreshSlots();
      };
    }
    node._stoiqoRefreshSlots = refreshSlots;
    refreshSlots();
  }
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
              w.inputEl.style.borderColor = "#a855f7";
              w.inputEl.style.backgroundColor = "rgba(168, 85, 247, 0.08)";
            }
          }
        }
      }
      this.setDirtyCanvas(true, true);
    }
  };
}

// src_js/nodes/proSaverNode.js
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
        ctx.fillText("READY / IN ATTESA DI GENERAZIONE", cardX + cardW / 2, cardY + 50);
        ctx.fillStyle = "#2d3748";
        ctx.font = "10px monospace";
        ctx.fillText("I file salvati e i metadati appariranno qui", cardX + cardW / 2, cardY + 74);
        ctx.restore();
        return;
      }
      const info = this.lastSaveInfo[0];
      const batchCount = this.lastSaveInfo.length;
      const badgeY = cardY + 16;
      ctx.fillStyle = "#10b981";
      ctx.font = "bold 10px system-ui, -apple-system, sans-serif";
      ctx.textAlign = "left";
      ctx.fillText("\u2713 SALVATO", cardX + 12, badgeY);
      const tagText = `${info.format || "IMG"} \u2022 ${info.width}x${info.height} \u2022 ${info.size_str || ""}${batchCount > 1 ? ` (+${batchCount - 1} altri)` : ""}`;
      ctx.fillStyle = "#00e5ff";
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
      const btnGap = 8;
      const btnCount = 3;
      const totalGap = btnGap * (btnCount - 1);
      const btnW = Math.floor((cardW - 24 - totalGap) / btnCount);
      const buttons = [
        {
          id: "copy_path",
          text: this.copiedButton === "copy_path" ? "\u2713 COPIATO" : "\u{1F4CB} COPIA PATH",
          active: this.copiedButton === "copy_path",
          actionText: info.filepath
        },
        {
          id: "copy_name",
          text: this.copiedButton === "copy_name" ? "\u2713 COPIATO" : "\u{1F4C4} COPIA NOME",
          active: this.copiedButton === "copy_name",
          actionText: info.filename
        },
        {
          id: "copy_folder",
          text: this.copiedButton === "copy_folder" ? "\u2713 COPIATO" : "\u{1F4C1} COPIA DIR",
          active: this.copiedButton === "copy_folder",
          actionText: info.filepath ? info.filepath.substring(0, info.filepath.lastIndexOf(info.filename || "") - 1) : info.subfolder
        }
      ];
      buttons.forEach((btn, idx) => {
        const bX = cardX + 12 + idx * (btnW + btnGap);
        this.buttonRects[btn.id] = { x: bX, y: btnY, w: btnW, h: btnH, data: btn.actionText };
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
  nodeType.prototype.onNodeCreated = function() {
    if (onNodeCreated) onNodeCreated.apply(this, arguments);
    this.hideOutputImages = true;
    this.imgs = null;
    this.images = null;
    const hudWidget = new StoiqoSaverStatusWidget(this);
    this.addCustomWidget(hudWidget);
    this._stoiqo_saver_hud = hudWidget;
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
import { app as app8 } from "../../../scripts/app.js";
import { ComfyWidgets as ComfyWidgets6 } from "../../../scripts/widgets.js";
function setupMusicPromptNode(nodeType, nodeData, app11) {
  const musicTargetNames = [
    "StoiqoMusicPromptEngineNode",
    "[STOIQO] Music Prompt & Lyrics Engine (YuE2)",
    "[STOIQO] Music Prompt & Lyrics Engine"
  ];
  if (!musicTargetNames.includes(nodeData.name)) return;
  const MIN_NODE_WIDTH = 480;
  const SECTIONS = [
    { targetWidget: "idea", num: "1", title: "CONCEPT & CORE THEME", color: "#f43f5e" },
    { targetWidget: "system_prompt", num: "2", title: "PRODUCER PERSONA & AI AGENT", color: "#ec4899" },
    { targetWidget: "genre", num: "3", title: "GENRE & ACOUSTICS", color: "#a855f7" },
    { targetWidget: "vocal_type", num: "4", title: "VOCALS & LANGUAGE", color: "#38bdf8" },
    { targetWidget: "structure", num: "5", title: "STRUCTURE & TEMPO", color: "#eab308" },
    { targetWidget: "custom_lyrics", num: "6", title: "CUSTOM LYRICS & DIRECTIVES (OPTIONAL)", color: "#818cf8" },
    { targetWidget: "seed", num: "7", title: "GENERATION & SAMPLING", color: "#10b981" }
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
    for (const sec of SECTIONS) {
      const targetIdx = node.widgets.findIndex((w) => w.name === sec.targetWidget);
      if (targetIdx !== -1) {
        const divider = new StoiqoSectionDividerWidget(sec.num, sec.title, sec.color);
        node.widgets.splice(targetIdx, 0, divider);
      }
    }
    let trackInfoDisplay = node.widgets.find((w) => w.name === "preview_track_info");
    if (!trackInfoDisplay) {
      const trackDivider = new StoiqoSectionDividerWidget("8", "YUE2 OUTPUT: TRACK TELEMETRY & STYLE", "#06b6d4");
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
        trackInfoDisplay.options = trackInfoDisplay.options || {};
        trackInfoDisplay.options.serialize = false;
        trackInfoDisplay.computeSize = function(width) {
          return [width, 24];
        };
      }
    }
    let styleDisplay = node.widgets.find((w) => w.name === "preview_style");
    if (!styleDisplay) {
      if (typeof ComfyWidgets6 !== "undefined" && ComfyWidgets6["STRING"]) {
        styleDisplay = ComfyWidgets6["STRING"](
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
          el.style.color = "#38bdf8";
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
      const lyricsDivider = new StoiqoSectionDividerWidget("9", "YUE2 OUTPUT: STRUCTURED LYRICS", "#ec4899");
      node.widgets.push(lyricsDivider);
      if (typeof ComfyWidgets6 !== "undefined" && ComfyWidgets6["STRING"]) {
        lyricsDisplay = ComfyWidgets6["STRING"](
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
        "\u{1F4CB} Copia Style (YuE2 Descriptor)",
        null,
        function() {
          const sw = node.widgets?.find((w) => w.name === "preview_style");
          const val = sw ? sw.value || sw.inputEl && sw.inputEl.value || "" : "";
          if (val && navigator.clipboard) {
            navigator.clipboard.writeText(String(val));
            const orig = this.name;
            this.name = "\u2713 Style Copiato!";
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
      copyStyleBtn.options = { serialize: false };
    }
    let copyLyricsBtn = node.widgets.find((w) => w._isMusicCopyLyrics);
    if (!copyLyricsBtn) {
      copyLyricsBtn = node.addWidget(
        "button",
        "\u{1F4CB} Copia Lyrics (YuE2 Stanza)",
        null,
        function() {
          const lw = node.widgets?.find((w) => w.name === "preview_lyrics");
          const val = lw ? lw.value || lw.inputEl && lw.inputEl.value || "" : "";
          if (val && navigator.clipboard) {
            navigator.clipboard.writeText(String(val));
            const orig = this.name;
            this.name = "\u2713 Lyrics Copiate!";
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
      copyLyricsBtn.options = { serialize: false };
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
      const tw = this.widgets?.find((w) => w.name === "preview_track_info");
      const sw = this.widgets?.find((w) => w.name === "preview_style");
      const lw = this.widgets?.find((w) => w.name === "preview_lyrics");
      if (tw) {
        const durSec = Math.round(info.max_duration || 0);
        const durMin = Math.floor(durSec / 60);
        const durRemSec = String(durSec % 60).padStart(2, "0");
        const durStr = durSec > 0 ? `${durSec}s (~${durMin}:${durRemSec}m)` : "Dynamic";
        const modeStr = info.mode === "full" ? "Full Song" : info.mode === "melody" ? "Melody Lead" : "Vocal";
        const summaryText = `\u{1F3B5} ${info.title || "Untitled"} | \u23F1\uFE0F ${durStr} | \u{1F941} ${info.bpm || 120} BPM | \u{1F3B9} ${info.musical_key || "N/A"} | \u{1F39A}\uFE0F ${modeStr}`;
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
      positive_prompt: 72,
      negative_prompt: 48
    }
  },
  // 3. Tri-Model Loader Hub
  StoiqoTriLoaderHubNode: {
    minWidth: 380
  },
  // 4. Smart Seed & Variance Controller
  StoiqoSeedControllerNode: {
    minWidth: 340
  },
  // 5. Inpaint Stitcher & Composite
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
  // 8. Modular Prompt Synthesizer Engine
  StoiqoPromptSynthesizerNode: {
    minWidth: 420,
    multilineHeights: {
      user_directives: 68
    }
  },
  // 9. AI Persona & Style Directives
  StoiqoStyleDirectivesNode: {
    minWidth: 380,
    multilineHeights: {
      custom_system_prompt: 52
    }
  },
  // 10. LLM Sampling & Precision
  StoiqoSamplingOptionsNode: {
    minWidth: 360
  },
  // 11. Multi-Image Context Hub
  StoiqoMultiImageContextNode: {
    minWidth: 380
  },
  // 12. Character Consistency Memory Bank (Lorebook & DNA)
  StoiqoCharacterMemoryNode: {
    minWidth: 420,
    multilineHeights: {
      face_and_skin: 52,
      signature_outfit: 52,
      negative_constraints: 48,
      user_prompt: 48
    }
  },
  // 13. Universal Context Pipe (In / Bus)
  StoiqoUniversalPipeInNode: {
    minWidth: 320
  },
  // 14. Universal Context Pipe (Out / Unpack)
  StoiqoUniversalPipeOutNode: {
    minWidth: 320
  },
  // 15. Webhook Notifier & Pipeline Exporter
  StoiqoWebhookNotifierNode: {
    minWidth: 400,
    multilineHeights: {
      message: 56
    }
  }
};
function setupPipelineNodes(nodeType, nodeData, appInstance) {
  const nodeName = nodeData.name;
  const config = CONFIGURATIONS[nodeName];
  if (!config) return;
  const origOnNodeCreated = nodeType.prototype.onNodeCreated;
  nodeType.prototype.onNodeCreated = function() {
    if (origOnNodeCreated) origOnNodeCreated.apply(this, arguments);
    const node = this;
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
    if (nodeName === "StoiqoPromptSynthesizerNode") {
      let tw = node.widgets.find((w) => w.name === "synthesized_prompt");
      if (!tw) {
        tw = node.addWidget(
          "customtext",
          "synthesized_prompt",
          "",
          function() {
          },
          { multiline: true }
        );
        tw.options = { serialize: false };
        tw.computeSize = function(width) {
          return [width, 100];
        };
        const styleTw = (el) => {
          if (!el) return;
          el.readOnly = true;
          el.placeholder = "Prompt stream output...";
          el.style.boxSizing = "border-box";
          el.style.fontSize = "11.5px";
          el.style.lineHeight = "1.45";
          el.style.fontFamily = "monospace, -apple-system, sans-serif";
          el.style.opacity = "0.92";
        };
        if (tw.inputEl) {
          styleTw(tw.inputEl);
        } else {
          let rawEl = null;
          Object.defineProperty(tw, "inputEl", {
            configurable: true,
            enumerable: true,
            get() {
              return rawEl;
            },
            set(v) {
              rawEl = v;
              styleTw(v);
            }
          });
        }
      }
    }
    if (nodeName === "StoiqoStyleDirectivesNode") {
      const updateCustomPromptVisibility = () => {
        const sys = node.widgets.find((w) => w.name === "system_prompt");
        const custom = node.widgets.find((w) => w.name === "custom_system_prompt");
        if (!custom) return;
        if (!custom._stoiqoOrig) {
          custom._stoiqoOrig = { computeSize: custom.computeSize, draw: custom.draw };
        }
        const show = !!sys && String(sys.value || "").includes("Custom");
        custom.hidden = !show;
        custom.computeSize = show ? custom._stoiqoOrig.computeSize : () => [0, -4];
        custom.draw = show ? custom._stoiqoOrig.draw : () => {
        };
        if (custom.inputEl) {
          custom.inputEl.hidden = !show;
          custom.inputEl.style.display = show ? "" : "none";
        }
        if (typeof node.computeSize === "function") {
          const computed = node.computeSize();
          node.size[1] = Math.max(Math.ceil(computed[1]), 60);
        }
        node.setDirtyCanvas?.(true, true);
      };
      const sysWidget = node.widgets.find((w) => w.name === "system_prompt");
      if (sysWidget && !sysWidget._stoiqoHooked) {
        sysWidget._stoiqoHooked = true;
        const origCb = sysWidget.callback;
        sysWidget.callback = function() {
          if (origCb) origCb.apply(this, arguments);
          updateCustomPromptVisibility();
        };
      }
      node._stoiqoUpdateCustomPrompt = updateCustomPromptVisibility;
      setTimeout(updateCustomPromptVisibility, 50);
    }
    if (nodeName === "StoiqoAudioSaverNode") {
      createAudioPlayerWidget(node, null);
    }
    if (nodeName === "StoiqoVideoSaverNode") {
      createVideoPlayerWidget(node, null);
    }
    if (node.setDirtyCanvas) {
      node.setDirtyCanvas(true, true);
    }
  };
  if (nodeName === "StoiqoStyleDirectivesNode") {
    const origOnConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function() {
      if (origOnConfigure) origOnConfigure.apply(this, arguments);
      if (this._stoiqoUpdateCustomPrompt) setTimeout(this._stoiqoUpdateCustomPrompt, 50);
    };
  }
  if (nodeName === "StoiqoPromptSynthesizerNode") {
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
    container.style.border = "1px solid rgba(0, 229, 255, 0.25)";
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
    header.style.color = "#00e5ff";
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
    playBtn.style.background = "linear-gradient(135deg, #00e5ff, #7928ca)";
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
    progress.style.accentColor = "#00e5ff";
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
    container.style.border = "1px solid rgba(0, 229, 255, 0.3)";
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
    header.style.color = "#00e5ff";
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
    progress.style.accentColor = "#00e5ff";
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
      btn.onmouseenter = () => btn.style.background = "rgba(0, 229, 255, 0.15)";
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
    playBtn.style.background = "linear-gradient(135deg, #00e5ff, #7928ca)";
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
    loopBtn.style.background = "rgba(0, 229, 255, 0.2)";
    loopBtn.style.borderColor = "rgba(0, 229, 255, 0.5)";
    loopBtn.style.color = "#00e5ff";
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
        loopBtn.style.background = "rgba(0, 229, 255, 0.2)";
        loopBtn.style.borderColor = "rgba(0, 229, 255, 0.5)";
        loopBtn.style.color = "#00e5ff";
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
import { app as app9 } from "../../../scripts/app.js";
import { api as api8 } from "../../../scripts/api.js";
var LORA_NODE_NAMES = ["StoiqoLoraStackNode", "[STOIQO] LoRA Stack"];
var MIN_WIDTH = 400;
var PAD = 6;
var HEAD_H = 24;
var ROW_H = 28;
var BTN_H = 30;
var STEP = 0.05;
var _loraListCache = null;
async function fetchLoraList(force = false) {
  if (_loraListCache && !force) return _loraListCache;
  try {
    const resp = await api8.fetchApi("/stoiqo/loras");
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
    this.loras = parsed.filter((it) => it && typeof it.name === "string" && it.name).map((it) => ({
      name: it.name,
      strength: Number.isFinite(Number(it.strength)) ? Number(it.strength) : 1,
      enabled: it.enabled !== false
    }));
  }
  sync() {
    if (this.store) {
      this.store.value = JSON.stringify(
        this.loras.map((l) => ({
          name: l.name,
          strength: l.strength,
          strength_clip: l.strength,
          enabled: l.enabled
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
    const activeCount = this.loras.filter((l) => l.enabled).length;
    ctx.font = "bold 11px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
    ctx.textAlign = "left";
    ctx.fillStyle = "#94a3b8";
    ctx.fillText(`LoRA Stack \xB7 ${activeCount}/${this.loras.length} attivi`, x0 + 2, y + HEAD_H / 2);
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
        x: allX,
        y: y + 3,
        w: allW,
        h: HEAD_H - 6,
        action: () => {
          const target = activeCount === 0;
          this.loras.forEach((l) => {
            l.enabled = target;
          });
          this.sync();
        }
      });
    }
    y += HEAD_H;
    if (this.loras.length === 0) {
      ctx.font = "italic 11px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
      ctx.fillStyle = "#64748b";
      ctx.textAlign = "center";
      ctx.fillText("Nessun LoRA \u2014 premi \u201C+ Aggiungi LoRA\u201D", x0 + w / 2, y + ROW_H / 2);
      y += ROW_H;
    } else {
      this.loras.forEach((lora, idx) => {
        const rY = y + 2;
        const rH = ROW_H - 4;
        const on = lora.enabled;
        ctx.fillStyle = on ? "rgba(45, 212, 191, 0.08)" : "rgba(255, 255, 255, 0.04)";
        roundRect(ctx, x0, rY, w, rH, 5);
        ctx.fill();
        ctx.strokeStyle = on ? "rgba(45, 212, 191, 0.35)" : "rgba(255, 255, 255, 0.08)";
        ctx.lineWidth = 1;
        ctx.stroke();
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
          x: tX - 2,
          y: rY,
          w: tW + 4,
          h: rH,
          action: () => {
            lora.enabled = !lora.enabled;
            this.sync();
          }
        });
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
        drawBtn(cX, btnW, "\u2212", "#e2e8f0");
        this.hits.push({
          x: cX,
          y: cY,
          w: btnW,
          h: cH,
          action: () => {
            lora.strength = Math.round((lora.strength - STEP) * 100) / 100;
            this.sync();
          }
        });
        const vX = cX + btnW;
        ctx.fillStyle = "rgba(0,0,0,0.25)";
        ctx.fillRect(vX, cY, valW, cH);
        ctx.fillStyle = on ? "#f1f5f9" : "#64748b";
        ctx.font = "11px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(lora.strength.toFixed(2), vX + valW / 2, cY + cH / 2 + 0.5);
        this.hits.push({
          x: vX,
          y: cY,
          w: valW,
          h: cH,
          action: (ev) => {
            app9.canvas.prompt("Strength", lora.strength, (v) => {
              const num = parseFloat(v);
              if (Number.isFinite(num)) {
                lora.strength = Math.round(Math.max(-10, Math.min(10, num)) * 100) / 100;
                this.sync();
              }
            }, ev);
          }
        });
        drawBtn(vX + valW, btnW, "+", "#e2e8f0");
        this.hits.push({
          x: vX + valW,
          y: cY,
          w: btnW,
          h: cH,
          action: () => {
            lora.strength = Math.round((lora.strength + STEP) * 100) / 100;
            this.sync();
          }
        });
        const xX = vX + valW + btnW + gap;
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
        const nX = tX + tW + 10;
        const nW = cX - nX - 8;
        ctx.font = "12px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
        ctx.textAlign = "left";
        ctx.fillStyle = on ? "#e2e8f0" : "#64748b";
        ctx.fillText(fitText(ctx, baseName(lora.name), nW), nX, rY + rH / 2 + 0.5);
        this.hits.push({
          x: nX,
          y: rY,
          w: nW,
          h: rH,
          action: (ev) => this.pickLora(ev, (picked) => {
            lora.name = picked;
            this.sync();
          })
        });
        y += ROW_H;
      });
    }
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
      x: x0,
      y,
      w,
      h: BTN_H - 4,
      action: (ev) => this.pickLora(ev, (picked) => {
        this.loras.push({ name: picked, strength: 1, enabled: true });
        this.sync();
      })
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
    const hasFolders = list.some((n) => /[\\/]/.test(n));
    if (!hasFolders) {
      new LG.ContextMenu(
        list.map((n) => ({ content: baseName(n), value: n })),
        { event, title: "LoRA", callback: choose }
      );
      return;
    }
    const groups = /* @__PURE__ */ new Map();
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
        content: `\u{1F4C1} ${folder}`,
        has_submenu: true,
        callback: (_value, _options, e, menu) => {
          new LG.ContextMenu(
            files.map((n) => ({ content: baseName(n), value: n })),
            { event: e, parentMenu: menu, callback: choose }
          );
          return true;
        }
      });
    }
    rootFiles.forEach((n) => items.push({ content: baseName(n), value: n }));
    new LG.ContextMenu(items, { event, title: "LoRA", callback: choose });
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
  if (node.size && node.size[0] < MIN_WIDTH) node.size[0] = MIN_WIDTH;
  let loraWidget = node.widgets ? node.widgets.find((w) => w instanceof StoiqoLoraStackWidget) : null;
  if (!loraWidget) {
    const store = node.widgets ? node.widgets.find((w) => w.name === "lora_stack") : null;
    if (store) {
      store.hidden = true;
      store.computeSize = () => [0, -4];
      store.draw = () => {
      };
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

// src_js/utils/telemetry.js
import { api as api9 } from "../../scripts/api.js";
var listenerAttached = false;
function initGlobalTelemetryListener(appInstance) {
  if (listenerAttached) return;
  listenerAttached = true;
  if (api9 && api9.addEventListener) {
    api9.addEventListener("stoiqo_node_telemetry", (event) => {
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
  ctx.fillStyle = "#06b6d4";
  ctx.fillText("\u26A1", posX + paddingX, posY + 12);
  ctx.fillStyle = "#cbd5e1";
  ctx.fillText(badgeText, posX + paddingX + iconWidth, posY + 12);
  ctx.restore();
}

// src_js/index.js
app10.registerExtension({
  name: "Stoiqo.PromptGeneratorEngine.Dividers",
  async beforeRegisterNodeDef(nodeType, nodeData, app11) {
    if (nodeData.category === "STOIQO" || nodeData.name && nodeData.name.startsWith("Stoiqo")) {
      setupTelemetryBadge(nodeType, nodeData, app11);
    }
    setupShowPromptNode(nodeType, nodeData, app11);
    setupModelLoaderNode(nodeType, nodeData, app11);
    setupVisualDiffNode(nodeType, nodeData, app11);
    setupImageCompareNode(nodeType, nodeData, app11);
    setupDatasetNode(nodeType, nodeData, app11);
    setupIteratorNode(nodeType, nodeData, app11);
    setupTrioLoaderNode(nodeType, nodeData, app11);
    setupConcatNode(nodeType, nodeData, app11);
    setupProSaverNode(nodeType, nodeData, app11);
    setupMusicPromptNode(nodeType, nodeData, app11);
    setupPipelineNodes(nodeType, nodeData, app11);
    setupLoraStackNode(nodeType, nodeData, app11);
  }
});
