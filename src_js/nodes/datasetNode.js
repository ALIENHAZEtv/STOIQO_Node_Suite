import { api } from "../../../scripts/api.js";

export function setupDatasetNode(nodeType, nodeData, app) {
    const targetNames = [
        "StoiqoDatasetWriterNode",
        "[STOIQO] Dataset & LoRA Toolkit",
    ];
    if (targetNames.includes(nodeData.name)) {
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

        function configureDatasetNode(node) {
            if (!node || !node.widgets) return;

            if (node.size && node.size[0] < MIN_NODE_WIDTH) {
                node.size[0] = MIN_NODE_WIDTH;
            }

            // 1. Add Native OS Folder Picker Button right below output_dir
            const outputDirWidget = node.widgets.find(w => w.name === "output_dir");
            const hasBrowseBtn = node.widgets.some(w => w._isStoiqoBrowse);
            if (outputDirWidget && !hasBrowseBtn) {
                const browseBtn = node.addWidget("button", "📁 Browse Output Folder", null, async () => {
                    try {
                        const resp = await api.fetchApi("/stoiqo/browse_folder", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                        });
                        const data = await resp.json();
                        if (data && data.status === "ok" && data.folder_path) {
                            outputDirWidget.value = data.folder_path;
                            if (outputDirWidget.callback) {
                                outputDirWidget.callback(data.folder_path);
                            }
                            node.setDirtyCanvas(true, true);
                        }
                    } catch (err) {
                        console.error("[STOIQO Dataset Toolkit] Folder selection error:", err);
                    }
                });
                browseBtn.serialize = false;
                browseBtn._isStoiqoBrowse = true;

                // Place right after output_dir
                const btnIdx = node.widgets.indexOf(browseBtn);
                const dirIdx = node.widgets.indexOf(outputDirWidget);
                if (btnIdx > -1 && dirIdx > -1 && btnIdx !== dirIdx + 1) {
                    node.widgets.splice(btnIdx, 1);
                    node.widgets.splice(dirIdx + 1, 0, browseBtn);
                }
            }

            // 2. Style blacklist_tags multiline box
            const blacklistWidget = node.widgets.find(w => w.name === "blacklist_tags");
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
                        get() { return rawInputEl; },
                        set(val) {
                            rawInputEl = val;
                            applyInputStyles(val);
                        }
                    });
                }
            }
        }
    }
}
