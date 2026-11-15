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
                this.setDirtyCanvas(true, true);
            }
        };

        // Render progress telemetry pill on foreground
        const origDrawFg = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function(ctx) {
            if (origDrawFg) origDrawFg.apply(this, arguments);

            const prog = this.properties?._stoiqo_progress;
            const fname = this.properties?._stoiqo_filename;
            if (prog && !this.flags?.collapsed) {
                ctx.save();
                const badgeH = 20;
                const badgeY = this.size[1] - badgeH - 6;
                const badgeX = 10;
                const badgeW = this.size[0] - 20;

                ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
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

                // Progress tag (Teal)
                ctx.fillStyle = "#2dd4bf";
                const pText = `📁 ${prog}`;
                ctx.fillText(pText, badgeX + 8, badgeY + badgeH / 2);
                const pW = ctx.measureText(pText).width;

                // File name tag (Slate)
                if (fname) {
                    ctx.fillStyle = "#94a3b8";
                    const maxChars = Math.max(15, Math.floor((badgeW - pW - 30) / 6.5));
                    const truncFname = fname.length > maxChars ? "…" + fname.slice(-maxChars) : fname;
                    ctx.fillText(`• ${truncFname}`, badgeX + pW + 16, badgeY + badgeH / 2);
                }

                ctx.restore();
            }
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
                browseBtn.serialize = false;
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

            // Setup Refresh Cache Button
            let refreshBtn = node.widgets.find(w => w._isStoiqoRefresh);
            if (!refreshBtn) {
                refreshBtn = node.addWidget(
                    "button",
                    "⟲ Rescan / Invalidate Cache",
                    null,
                    function() {
                        const origLabel = this.name;
                        this.name = "✓ Cache Re-indexed!";
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
        }
    }
}
