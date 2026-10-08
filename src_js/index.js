import { app } from "../../scripts/app.js";
import { setupEngineNode } from "./nodes/engineNode.js";
import { setupShowPromptNode } from "./nodes/showPromptNode.js";
import { setupModelLoaderNode } from "./nodes/modelLoaderNode.js";
import { setupVisualDiffNode } from "./nodes/visualDiffNode.js";
import { setupImageCompareNode } from "./nodes/imageCompareNode.js";
import { setupDatasetNode } from "./nodes/datasetNode.js";
import { setupIteratorNode } from "./nodes/iteratorNode.js";
import { setupTrioLoaderNode } from "./nodes/trioLoaderNode.js";
import { setupConcatNode } from "./nodes/textConcatNode.js";
import { setupProSaverNode } from "./nodes/proSaverNode.js";
import { setupMusicPromptNode } from "./nodes/musicPromptNode.js";

app.registerExtension({
    name: "Stoiqo.PromptGeneratorEngine.Dividers",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        setupEngineNode(nodeType, nodeData, app);
        setupShowPromptNode(nodeType, nodeData, app);
        setupModelLoaderNode(nodeType, nodeData, app);
        setupVisualDiffNode(nodeType, nodeData, app);
        setupImageCompareNode(nodeType, nodeData, app);
        setupDatasetNode(nodeType, nodeData, app);
        setupIteratorNode(nodeType, nodeData, app);
        setupTrioLoaderNode(nodeType, nodeData, app);
        setupConcatNode(nodeType, nodeData, app);
        setupProSaverNode(nodeType, nodeData, app);
        setupMusicPromptNode(nodeType, nodeData, app);
    }
});
