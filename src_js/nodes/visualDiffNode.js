import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";
import { StoiqoSectionDividerWidget, currentDownloadProgress } from "../utils/core.js";

export function setupVisualDiffNode(nodeType, nodeData, app) {
        // 4. VISUAL DIFF & FORENSIC INSPECTOR ENHANCEMENTS
        // ══════════════════════════════════════════════════════════════════════
        const diffTargetNames = [
            "StoiqoVisualDiffNode",
            "[STOIQO] Visual Diff & Forensic Inspector",
        ];

        if (diffTargetNames.includes(nodeData.name)) {
            const MIN_NODE_WIDTH = 460;
            const SECTIONS = [
                { targetWidget: "analysis_focus", num: "1", title: "FORENSIC DIRECTIVES", color: "#c084fc" },
                { targetWidget: "seed", num: "2", title: "SAMPLING & RESOLUTION", color: "#facc15" },
                { targetWidget: "model_preset", num: "3", title: "STANDALONE ENGINE FALLBACK", color: "#38bdf8" },
            ];

            function setupVisualDiff(node) {
                if (!node || !node.widgets) return;
                if (node.size && node.size[0] < MIN_NODE_WIDTH) node.size[0] = MIN_NODE_WIDTH;

                // Adjust multiline height for custom_directives
                const dirW = node.widgets.find(w => w.name === "custom_directives");
                if (dirW) {
                    dirW.computeSize = function(width) {
                        return [width, 76];
                    };
                }

                // Dividers
                node.widgets = node.widgets.filter(w => !w.isStoiqoDivider);
                SECTIONS.forEach(sec => {
                    const idx = node.widgets.findIndex(w => w.name === sec.targetWidget);
                    if (idx !== -1) {
                        const div = new StoiqoSectionDividerWidget(sec.num, sec.title, sec.color);
                        node.widgets.splice(idx, 0, div);
                    }
                });

                // Browse Button for fallback local path
                let browseBtn = node.widgets.find(w => w._isStoiqoBrowse);
                if (!browseBtn) {
                    browseBtn = node.addWidget(
                        "button",
                        "📁 Browse Model Folder on Disk",
                        null,
                        async function() {
                            const pathWidget = node.widgets.find(w => w.name === "local_model_path");
                            const currentPath = pathWidget ? (pathWidget.value || "") : "";
                            const origLabel = this.name;
                            this.name = "⏳ Selecting folder in Windows...";
                            node.setDirtyCanvas(true);
                            try {
                                const resp = await api.fetchApi("/stoiqo/browse_folder", {
                                    method: "POST",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({ initial_dir: currentPath }),
                                });
                                if (resp.ok) {
                                    const res = await resp.json();
                                    if (res && res.path) {
                                        if (pathWidget) {
                                            pathWidget.value = res.path;
                                            if (pathWidget.inputEl) pathWidget.inputEl.value = res.path;
                                        }
                                        this.name = "✓ Folder Selected!";
                                        setTimeout(() => { this.name = origLabel; node.setDirtyCanvas(true); }, 1800);
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

                    const pathIdx = node.widgets.findIndex(w => w.name === "local_model_path");
                    if (pathIdx !== -1) {
                        const curIdx = node.widgets.indexOf(browseBtn);
                        if (curIdx !== -1) {
                            node.widgets.splice(curIdx, 1);
                            node.widgets.splice(pathIdx + 1, 0, browseBtn);
                        }
                    }
                }

                function updateDiffVisibility() {
                    const presetW = node.widgets.find(w => w.name === "model_preset");
                    const pathW = node.widgets.find(w => w.name === "local_model_path");
                    const btnW = node.widgets.find(w => w._isStoiqoBrowse);
                    const isCustom = presetW && String(presetW.value).includes("Custom Model");

                    if (pathW) {
                        pathW.hidden = !isCustom;
                        if (!isCustom) {
                            pathW.computeSize = () => [0, -4];
                            if (!pathW._origDraw) pathW._origDraw = pathW.draw;
                            pathW.draw = () => {};
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
                            btnW.draw = () => {};
                        } else {
                            delete btnW.computeSize;
                            if (btnW._origDraw) btnW.draw = btnW._origDraw;
                        }
                    }
                    node.setDirtyCanvas(true, true);
                }

                const presetWidget = node.widgets.find(w => w.name === "model_preset");
                if (presetWidget) {
                    const origCallback = presetWidget.callback;
                    presetWidget.callback = function() {
                        if (origCallback) origCallback.apply(this, arguments);
                        updateDiffVisibility();
                    };
                }
                updateDiffVisibility();
                node.setDirtyCanvas(true, true);
            }

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
