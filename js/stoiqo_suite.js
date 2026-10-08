var __getOwnPropNames = Object.getOwnPropertyNames;
var __esm = (fn, res, err) => function __init() {
  if (err) throw err[0];
  try {
    return fn && (res = (0, fn[__getOwnPropNames(fn)[0]])(fn = 0)), res;
  } catch (e) {
    throw err = [e], e;
  }
};
var __commonJS = (cb, mod) => function __require() {
  try {
    return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
  } catch (e) {
    throw mod = 0, e;
  }
};

// src_js/utils/core.js
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";
import { ComfyWidgets } from "../../scripts/widgets.js";
var currentDownloadProgress, downloadClearTimer, comfyApi, StoiqoSectionDividerWidget;
var init_core = __esm({
  "src_js/utils/core.js"() {
    currentDownloadProgress = null;
    downloadClearTimer = null;
    comfyApi = api || typeof app !== "undefined" && app.api;
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
    StoiqoSectionDividerWidget = class {
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
  }
});

// src_js/nodes/engineNode.js
import { app as app2 } from "../../../scripts/app.js";
import { api as api2 } from "../../../scripts/api.js";
import { ComfyWidgets as ComfyWidgets2 } from "../../../scripts/widgets.js";
function setupEngineNode(nodeType, nodeData, app11) {
  const engineTargetNames = [
    "StoiqoPromptGeneratorEngineNode",
    "QwenVLCaptionerNode",
    "[STOIQO] Prompt Generator Engine",
    "[STOIQO] Prompt Generator Engine (Legacy)"
  ];
  if (engineTargetNames.includes(nodeData.name)) {
    let setupEngineNode2 = function(node) {
      if (!node || !node.widgets) return;
      if (node.bgcolor === "#0e1218" || node.bgcolor === "#0b1411") {
        delete node.bgcolor;
      }
      if (node.color === "#18202c" || node.color === "#14251f") {
        delete node.color;
      }
      if (node.size && node.size[0] < MIN_NODE_WIDTH) {
        node.size[0] = MIN_NODE_WIDTH;
      }
      const legacyModelMode = node.widgets.find((w) => w.name === "model_mode");
      if (legacyModelMode) {
        legacyModelMode.hidden = true;
        legacyModelMode.computeSize = function() {
          return [0, -4];
        };
        legacyModelMode.draw = function() {
        };
        if (legacyModelMode.inputEl) {
          legacyModelMode.inputEl.hidden = true;
          legacyModelMode.inputEl.style.display = "none";
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
          };
          if (w.inputEl) {
            applyInputStyles(w.inputEl);
            if (w.hidden) {
              w.inputEl.hidden = true;
              w.inputEl.style.display = "none";
            }
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
                applyInputStyles(val);
                if (w.hidden && val) {
                  val.hidden = true;
                  val.style.display = "none";
                }
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
          node.size[1] = Math.max(Math.ceil(computed[1]), 100);
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
      node.widgets = node.widgets.filter((w) => !w.isStoiqoDivider);
      for (const sec of SECTIONS) {
        let targetIdx = node.widgets.findIndex((w) => w.name === sec.targetWidget);
        if (targetIdx === -1 && sec.fallbackWidget) {
          targetIdx = node.widgets.findIndex((w) => w.name === sec.fallbackWidget);
        }
        if (targetIdx !== -1) {
          const dividerWidget = new StoiqoSectionDividerWidget(sec.num, sec.title, sec.color);
          node.widgets.splice(targetIdx, 0, dividerWidget);
        }
      }
      updateSystemPromptVisibility();
      node.updatePipeVisibility = function() {
        if (!this.inputs) return;
        const pipeInput = this.inputs.find((inp) => inp.name === "stoiqo_model");
        const isConnected = pipeInput ? !!pipeInput.link : false;
        const wNamesToHide = ["model_preset", "local_model_path", "quantization", "attention_mode", "unload_model_after"];
        this.widgets.forEach((w) => {
          if (wNamesToHide.includes(w.name) || w.isStoiqoDivider && w.sectionNum === "1") {
            if (!w._stoiqoOrigComputeSizePipe) {
              w._stoiqoOrigComputeSizePipe = w.computeSize;
              w._stoiqoOrigDrawPipe = w.draw;
            }
            if (isConnected) {
              w.hidden = true;
              w.computeSize = function() {
                return [0, -4];
              };
              w.draw = function() {
              };
              if (w.inputEl) {
                w.inputEl.hidden = true;
                w.inputEl.style.display = "none";
              }
            } else {
              w.hidden = false;
              if (w._stoiqoOrigComputeSizePipe) {
                w.computeSize = w._stoiqoOrigComputeSizePipe;
              } else {
                delete w.computeSize;
              }
              if (w._stoiqoOrigDrawPipe) {
                w.draw = w._stoiqoOrigDrawPipe;
              } else {
                delete w.draw;
              }
              if (w.inputEl) {
                w.inputEl.hidden = false;
                w.inputEl.style.display = "";
              }
            }
          }
        });
        if (isConnected) {
          const browseWidget = this.widgets.find((w) => w._isStoiqoBrowse);
          if (browseWidget) {
            if (!browseWidget._stoiqoOrigComputeSizePipe) {
              browseWidget._stoiqoOrigComputeSizePipe = browseWidget.computeSize;
              browseWidget._stoiqoOrigDrawPipe = browseWidget.draw;
            }
            browseWidget.hidden = true;
            browseWidget.computeSize = function() {
              return [0, -4];
            };
            browseWidget.draw = function() {
            };
          }
        }
        if (typeof this.computeSize === "function") {
          const computed = this.computeSize();
          this.size[0] = Math.max(this.size[0] || 0, MIN_NODE_WIDTH);
          this.size[1] = Math.max(Math.ceil(computed[1]), 100);
        }
        this.setDirtyCanvas(true, true);
      };
      setTimeout(() => node.updatePipeVisibility(), 50);
      if (typeof node.computeSize === "function") {
        const computed = node.computeSize();
        node.size[0] = Math.max(node.size[0] || 0, MIN_NODE_WIDTH);
        node.size[1] = Math.max(node.size[1] || 0, Math.ceil(computed[1]));
      }
      node.setDirtyCanvas(true, true);
    };
    const MIN_NODE_WIDTH = 460;
    const SECTIONS = [
      { targetWidget: "model_preset", num: "1", title: "MODEL & HARDWARE ENGINE", color: "#60a5fa" },
      { targetWidget: "batch_mode", num: "2", title: "TASK & DIRECTIVES", color: "#c084fc" },
      { targetWidget: "seed", num: "3", title: "SAMPLING & GENERATION", color: "#facc15" },
      { targetWidget: "enable_dual_prompt", num: "4", title: "DUAL PROMPT & ARTIFACT AUDIT", color: "#2dd4bf" }
    ];
    const MULTILINE_HEIGHTS = {
      "user_directives": 88,
      "custom_system_prompt": 68
    };
    const origOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function() {
      if (origOnNodeCreated) {
        origOnNodeCreated.apply(this, arguments);
      }
      setupEngineNode2(this);
    };
    const origOnConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function() {
      if (origOnConfigure) {
        origOnConfigure.apply(this, arguments);
      }
      setupEngineNode2(this);
    };
    const origOnConnectionsChange = nodeType.prototype.onConnectionsChange;
    nodeType.prototype.onConnectionsChange = function(type, index, connected, link_info) {
      if (origOnConnectionsChange) {
        origOnConnectionsChange.apply(this, arguments);
      }
      if (type === 1 && this.inputs && this.inputs[index] && this.inputs[index].name === "stoiqo_model") {
        if (typeof this.updatePipeVisibility === "function") {
          this.updatePipeVisibility();
        }
      }
    };
  }
}
var init_engineNode = __esm({
  "src_js/nodes/engineNode.js"() {
    init_core();
  }
});

// src_js/nodes/showPromptNode.js
import { app as app3 } from "../../../scripts/app.js";
import { api as api3 } from "../../../scripts/api.js";
import { ComfyWidgets as ComfyWidgets3 } from "../../../scripts/widgets.js";
function setupShowPromptNode(nodeType, nodeData, app11) {
  const showPromptTargetNames = [
    "StoiqoShowPromptNode",
    "QwenVLTextDisplayNode",
    "[STOIQO] Show Prompt",
    "[STOIQO] Show Prompt (Legacy)"
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
        if (typeof ComfyWidgets3 !== "undefined" && ComfyWidgets3["STRING"]) {
          textWidget = ComfyWidgets3["STRING"](
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
var init_showPromptNode = __esm({
  "src_js/nodes/showPromptNode.js"() {
    init_core();
  }
});

// src_js/nodes/modelLoaderNode.js
import { app as app4 } from "../../../scripts/app.js";
import { api as api4 } from "../../../scripts/api.js";
import { ComfyWidgets as ComfyWidgets4 } from "../../../scripts/widgets.js";
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
var init_modelLoaderNode = __esm({
  "src_js/nodes/modelLoaderNode.js"() {
    init_core();
  }
});

// src_js/nodes/visualDiffNode.js
import { app as app5 } from "../../../scripts/app.js";
import { api as api5 } from "../../../scripts/api.js";
import { ComfyWidgets as ComfyWidgets5 } from "../../../scripts/widgets.js";
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
              const resp = await api5.fetchApi("/stoiqo/browse_folder", {
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
var init_visualDiffNode = __esm({
  "src_js/nodes/visualDiffNode.js"() {
    init_core();
  }
});

// src_js/nodes/imageCompareNode.js
import { app as app6 } from "../../../scripts/app.js";
import { api as api6 } from "../../../scripts/api.js";
import { ComfyWidgets as ComfyWidgets6 } from "../../../scripts/widgets.js";
function setupImageCompareNode(nodeType, nodeData, app11) {
  const compareTargetNames = [
    "StoiqoImageCompareNode",
    "[STOIQO] Visual Compare Slider & Zoom"
  ];
  if (compareTargetNames.includes(nodeData.name)) {
    let imageDataToUrl = function(data) {
      if (!data) return "";
      const sub = data.subfolder ? `&subfolder=${encodeURIComponent(data.subfolder)}` : "";
      const typ = data.type ? `&type=${encodeURIComponent(data.type)}` : "&type=temp";
      const fmt = app11.getPreviewFormatParam ? app11.getPreviewFormatParam() : "";
      const rnd = app11.getRandParam ? app11.getRandParam() : "";
      return api6.apiURL(`/view?filename=${encodeURIComponent(data.filename)}${typ}${sub}${fmt}${rnd}`);
    }, setupImageCompareNodeUI = function(node) {
      if (!node) return;
      node.hideOutputImages = true;
      node.imgs = null;
      node.images = null;
      if (!node.size || node.size[0] < MIN_WIDTH) node.size = [MIN_WIDTH, MIN_HEIGHT];
      let cmpWidget = node.widgets ? node.widgets.find((w) => w instanceof StoiqoCompareCanvasWidget) : null;
      if (!cmpWidget) {
        cmpWidget = new StoiqoCompareCanvasWidget(node);
        node.addCustomWidget(cmpWidget);
        node.cmpWidget = cmpWidget;
      }
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
    const MIN_WIDTH = 520;
    const MIN_HEIGHT = 560;
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
      }
      serializeValue() {
        return void 0;
      }
      computeSize(width) {
        return [width, 440];
      }
      setImages(dataList) {
        if (!dataList || dataList.length < 2) return;
        this.imgA = new Image();
        this.imgB = new Image();
        this.imgA.onload = () => {
          if (this.node) this.node.setDirtyCanvas(true, true);
        };
        this.imgB.onload = () => {
          if (this.node) this.node.setDirtyCanvas(true, true);
        };
        this.imgA.src = imageDataToUrl(dataList[0]);
        this.imgB.src = imageDataToUrl(dataList[1]);
        this.labelA = dataList[0].label || "Original";
        this.labelB = dataList[1].label || "Upscaled";
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
          { key: "side", label: "\u25EB Side-by-Side", activeColor: "#2dd4bf" }
        ];
        let btnX = vX + 6;
        ctx.font = "bold 9px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif";
        modes.forEach((m) => {
          const active = this.mode === m.key;
          const textW = ctx.measureText(m.label).width;
          const bW = textW + 14;
          const bH = 18;
          const bY = barY + 4;
          const col = m.activeColor || "#2dd4bf";
          ctx.fillStyle = active ? m.key === "only_a" ? "rgba(56, 189, 248, 0.22)" : m.key === "only_b" ? "rgba(192, 132, 252, 0.22)" : "rgba(45, 212, 191, 0.22)" : "rgba(255, 255, 255, 0.06)";
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
            x: btnX,
            y: bY,
            w: bW,
            h: bH,
            action: () => {
              this.mode = m.key;
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
        ctx.fillText(resetLabel, rX + 7, rY + 12);
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
        ctx.fillText(zoomLabel, zX, rY + 12);
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
        if (!this.imgA || !this.imgB || !this.imgA.complete || !this.imgB.complete) {
          ctx.fillStyle = "#64748b";
          ctx.font = "12px sans-serif";
          ctx.textAlign = "center";
          ctx.fillText("Connect image_a and image_b and click Queue Prompt to compare", vp.x + vp.w / 2, vp.y + vp.h / 2);
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
        const natWA = this.imgA.naturalWidth || 1024;
        const natHA = this.imgA.naturalHeight || 1024;
        const natWB = this.imgB.naturalWidth || 1024;
        const natHB = this.imgB.naturalHeight || 1024;
        const centerX = vp.x + vp.w / 2;
        const centerY = vp.y + vp.h / 2;
        const fitA = computeFit(natWA, natHA, vp.w, vp.h);
        const fitB = computeFit(natWB, natHB, vp.w, vp.h);
        const halfWA = fitA.w / 2;
        const halfHA = fitA.h / 2;
        const halfWB = fitB.w / 2;
        const halfHB = fitB.h / 2;
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
        if (this.mode === "only_a" || this.mode === "split" || this.mode === "side") {
          const labelAText = `\u25C4 A: ${this.labelA.slice(0, 8)} (${natWA}\xD7${natHA})`;
          const lAW = ctx.measureText(labelAText).width + 12;
          ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
          ctx.fillRect(vp.x + 8, vp.y + 8, lAW, 18);
          ctx.fillStyle = "#38bdf8";
          ctx.fillText(labelAText, vp.x + 14, vp.y + 20);
        }
        if (this.mode === "only_b" || this.mode === "split" || this.mode === "side") {
          const labelBText = `B: ${this.labelB.slice(0, 8)} (${natWB}\xD7${natHB}) \u25BA`;
          const lBW = ctx.measureText(labelBText).width + 12;
          ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
          ctx.fillRect(vp.x + vp.w - lBW - 8, vp.y + 8, lBW, 18);
          ctx.fillStyle = "#c084fc";
          ctx.fillText(labelBText, vp.x + vp.w - lBW - 2, vp.y + 20);
        }
        if (this.zoom > 1.05) {
          const hint = "\u{1F50D} Drag to Pan \u2022 Scroll to Zoom";
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
          if (this.mode === "split") {
            const splitPixelX = vp.x + this.splitX * vp.w;
            if (this.zoom <= 1.05 || Math.abs(mx - splitPixelX) < 40) {
              const relX = (mx - vp.x) / vp.w;
              this.splitX = Math.max(0.01, Math.min(0.99, relX));
              this.isDraggingSplit = true;
              if (this.node) this.node.setDirtyCanvas(true, true);
              if (e && e.stopPropagation) e.stopPropagation();
              return true;
            }
          }
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
    nodeType.prototype.onDrawBackground = function(ctx) {
      this.hideOutputImages = true;
      this.imgs = null;
      this.images = null;
    };
    nodeType.prototype.onExecuted = function(message) {
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
          if (message.images) {
            w.setImages(message.images);
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
var init_imageCompareNode = __esm({
  "src_js/nodes/imageCompareNode.js"() {
    init_core();
  }
});

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
var init_datasetNode = __esm({
  "src_js/nodes/datasetNode.js"() {
  }
});

// src_js/nodes/iteratorNode.js
import { api as api7 } from "../../../scripts/api.js";
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
              const resp = await api7.fetchApi("/stoiqo/browse_folder", {
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
var init_iteratorNode = __esm({
  "src_js/nodes/iteratorNode.js"() {
  }
});

// src_js/nodes/trioLoaderNode.js
import { app as app7 } from "../../../scripts/app.js";
import { api as api8 } from "../../../scripts/api.js";
function setupTrioLoaderNode(nodeType, nodeData, appInstance) {
  const targetNames = [
    "StoiqoTripleImageLoaderNode",
    "[STOIQO] Trio Image Loader (Hero & Thumbs)"
  ];
  if (!targetNames.includes(nodeData.name)) return;
  const MIN_WIDTH = 460;
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
    return api8.apiURL(`/view?${params.toString()}`);
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
    this.size = this.size || [MIN_WIDTH, MIN_HEIGHT];
    if (this.size[0] < MIN_WIDTH) this.size[0] = MIN_WIDTH;
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
var init_trioLoaderNode = __esm({
  "src_js/nodes/trioLoaderNode.js"() {
    init_core();
  }
});

// src_js/nodes/textConcatNode.js
import { app as app8 } from "../../../scripts/app.js";
function setupConcatNode(nodeType, nodeData, appInstance) {
  const concatTargetNames = [
    "StoiqoTextConcatenateNode",
    "[STOIQO] Text Concatenate & Clean"
  ];
  if (!concatTargetNames.includes(nodeData.name)) return;
  const MIN_WIDTH = 420;
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
    node.size = node.size || [MIN_WIDTH, 360];
    if (node.size[0] < MIN_WIDTH) node.size[0] = MIN_WIDTH;
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
        node.setSize([Math.max(node.size[0] || 0, MIN_WIDTH), Math.max(Math.ceil(sz[1]), 220)]);
      }
      node.setDirtyCanvas(true, true);
      if (app8.graph && app8.graph.setDirtyCanvas) {
        app8.graph.setDirtyCanvas(true, true);
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
var init_textConcatNode = __esm({
  "src_js/nodes/textConcatNode.js"() {
  }
});

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
      this.images = null;
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
    this.images = null;
    if (origDrawBackground) {
      origDrawBackground.apply(this, arguments);
    }
  };
}
var init_proSaverNode = __esm({
  "src_js/nodes/proSaverNode.js"() {
  }
});

// src_js/nodes/musicPromptNode.js
import { app as app9 } from "../../../scripts/app.js";
import { ComfyWidgets as ComfyWidgets7 } from "../../../scripts/widgets.js";
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
    { targetWidget: "genre", num: "2", title: "GENRE & ACOUSTICS", color: "#a855f7" },
    { targetWidget: "vocal_type", num: "3", title: "VOCALS & LANGUAGE", color: "#38bdf8" },
    { targetWidget: "structure", num: "4", title: "STRUCTURE & TEMPO", color: "#eab308" },
    { targetWidget: "seed", num: "5", title: "GENERATION & SAMPLING", color: "#10b981" }
  ];
  const MULTILINE_HEIGHTS = {
    "idea": 76,
    "custom_directives": 54
  };
  function setupNodeInstance(node) {
    if (!node || !node.widgets) return;
    if (node.bgcolor === "#0e1218" || node.bgcolor === "#0b1411") delete node.bgcolor;
    if (node.color === "#18202c" || node.color === "#14251f") delete node.color;
    if (node.size && node.size[0] < MIN_NODE_WIDTH) {
      node.size[0] = MIN_NODE_WIDTH;
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
    node.widgets = node.widgets.filter((w) => !w.isStoiqoDivider);
    for (const sec of SECTIONS) {
      const targetIdx = node.widgets.findIndex((w) => w.name === sec.targetWidget);
      if (targetIdx !== -1) {
        const divider = new StoiqoSectionDividerWidget(sec.num, sec.title, sec.color);
        node.widgets.splice(targetIdx, 0, divider);
      }
    }
    let styleDisplay = node.widgets.find((w) => w.name === "preview_style");
    if (!styleDisplay) {
      const styleDivider = new StoiqoSectionDividerWidget("6", "YUE2 OUTPUT: STYLE DESCRIPTOR", "#06b6d4");
      node.widgets.push(styleDivider);
      if (typeof ComfyWidgets7 !== "undefined" && ComfyWidgets7["STRING"]) {
        styleDisplay = ComfyWidgets7["STRING"](
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
      const lyricsDivider = new StoiqoSectionDividerWidget("7", "YUE2 OUTPUT: STRUCTURED LYRICS", "#ec4899");
      node.widgets.push(lyricsDivider);
      if (typeof ComfyWidgets7 !== "undefined" && ComfyWidgets7["STRING"]) {
        lyricsDisplay = ComfyWidgets7["STRING"](
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
      const sw = this.widgets?.find((w) => w.name === "preview_style");
      const lw = this.widgets?.find((w) => w.name === "preview_lyrics");
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
var init_musicPromptNode = __esm({
  "src_js/nodes/musicPromptNode.js"() {
    init_core();
  }
});

// src_js/index.js
import { app as app10 } from "../../scripts/app.js";
var require_index = __commonJS({
  "src_js/index.js"() {
    init_engineNode();
    init_showPromptNode();
    init_modelLoaderNode();
    init_visualDiffNode();
    init_imageCompareNode();
    init_datasetNode();
    init_iteratorNode();
    init_trioLoaderNode();
    init_textConcatNode();
    init_proSaverNode();
    init_musicPromptNode();
    app10.registerExtension({
      name: "Stoiqo.PromptGeneratorEngine.Dividers",
      async beforeRegisterNodeDef(nodeType, nodeData, app11) {
        setupEngineNode(nodeType, nodeData, app11);
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
      }
    });
  }
});
export default require_index();
