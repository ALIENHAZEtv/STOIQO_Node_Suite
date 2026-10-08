
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
            setupDatasetNode(this);
        };

        function setupDatasetNode(node) {
            if (!node || !node.widgets) return;

            if (node.size && node.size[0] < MIN_NODE_WIDTH) {
                node.size[0] = MIN_NODE_WIDTH;
            }

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
