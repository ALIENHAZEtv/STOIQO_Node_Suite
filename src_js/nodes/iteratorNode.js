import { api } from "../../../scripts/api.js";

export function setupIteratorNode(nodeType, nodeData, app) {
    const targetNames = [
        "StoiqoSmartFolderImageIterator",
        "[STOIQO] Smart Folder Image Iterator",
    ];
    if (targetNames.includes(nodeData.name)) {
        const MIN_NODE_WIDTH = 460;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function() {
            if (onNodeCreated) {
                onNodeCreated.apply(this, arguments);
            }
            setupIteratorNodeUI(this);
        };

        function setupIteratorNodeUI(node) {
            if (!node || !node.widgets) return;

            if (node.size && node.size[0] < MIN_NODE_WIDTH) {
                node.size[0] = MIN_NODE_WIDTH;
            }

            const folderPathWidget = node.widgets.find(w => w.name === "folder_path");

            // Setup Browse Button
            let browseBtn = node.widgets.find(w => w._isStoiqoBrowse);
            if (!browseBtn) {
                browseBtn = node.addWidget(
                    "button",
                    "📁 Browse Dataset Folder",
                    null,
                    async function() {
                        const currentPath = folderPathWidget ? (folderPathWidget.value || "") : "";
                        const origLabel = this.name;
                        this.name = "⏳ Selecting folder in Windows...";
                        node.setDirtyCanvas(true);

                        try {
                            const resp = await api.fetchApi("/stoiqo/browse_folder", {
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
                                    this.name = "✓ Folder Selected!";
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

                const pathIdx = node.widgets.findIndex(w => w.name === "folder_path");
                if (pathIdx !== -1) {
                    const curIdx = node.widgets.indexOf(browseBtn);
                    if (curIdx !== -1) {
                        node.widgets.splice(curIdx, 1);
                        node.widgets.splice(pathIdx + 1, 0, browseBtn);
                    }
                }
            }
        }
    }
}
