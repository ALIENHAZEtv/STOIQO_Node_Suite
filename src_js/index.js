import { app } from "../../scripts/app.js";
import { setupShowPromptNode } from "./nodes/showPromptNode.js";
import { setupModelLoaderNode } from "./nodes/modelLoaderNode.js";
import { setupImageCompareNode } from "./nodes/imageCompareNode.js";
import { setupDatasetNode } from "./nodes/datasetNode.js";
import { setupIteratorNode } from "./nodes/iteratorNode.js";
import { setupTrioLoaderNode } from "./nodes/trioLoaderNode.js";
import { setupConcatNode } from "./nodes/textConcatNode.js";
import { setupProSaverNode } from "./nodes/proSaverNode.js";
import { setupMusicPromptNode } from "./nodes/musicPromptNode.js";
import { setupPipelineNodes } from "./nodes/pipelineNodes.js";
import { setupLoraStackNode } from "./nodes/loraStackNode.js";
import { setupPromptGeneratorNode } from "./nodes/promptGeneratorNode.js";
import { setupSeedNode } from "./nodes/seedNode.js";
import { setupTelemetryBadge } from "./utils/telemetry.js";
import { setupSettingsDrawers, sanitizeNodeWidgetValues } from "./utils/settingsDrawer.js";

app.registerExtension({
    name: "Stoiqo.PromptGeneratorEngine.Dividers",
    async beforeQueue() {
        if (app.graph && Array.isArray(app.graph._nodes)) {
            for (const n of app.graph._nodes) {
                if (n && (n.type?.startsWith("Stoiqo") || n.category === "STOIQO")) {
                    sanitizeNodeWidgetValues(n);
                }
            }
        }
    },
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.category === "STOIQO" || (nodeData.name && nodeData.name.startsWith("Stoiqo"))) {
            setupTelemetryBadge(nodeType, nodeData, app);

            const origConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function (info) {
                if (origConfigure) origConfigure.apply(this, arguments);
                sanitizeNodeWidgetValues(this, info);
            };

            const origSerialize = nodeType.prototype.serialize;
            nodeType.prototype.serialize = function () {
                sanitizeNodeWidgetValues(this);
                return origSerialize ? origSerialize.apply(this, arguments) : {};
            };
        }

        setupShowPromptNode(nodeType, nodeData, app);
        setupModelLoaderNode(nodeType, nodeData, app);
        setupImageCompareNode(nodeType, nodeData, app);
        setupDatasetNode(nodeType, nodeData, app);
        setupIteratorNode(nodeType, nodeData, app);
        setupTrioLoaderNode(nodeType, nodeData, app);
        setupConcatNode(nodeType, nodeData, app);
        setupProSaverNode(nodeType, nodeData, app);
        setupMusicPromptNode(nodeType, nodeData, app);
        setupPipelineNodes(nodeType, nodeData, app);
        setupLoraStackNode(nodeType, nodeData, app);
        setupPromptGeneratorNode(nodeType, nodeData, app);
        setupSeedNode(nodeType, nodeData, app);
        setupSettingsDrawers(nodeType, nodeData);
    }
});

