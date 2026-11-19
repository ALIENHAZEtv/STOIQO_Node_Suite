import { api } from "../../../scripts/api.js";

/**
 * [STOIQO] Prompt Studio Modal
 * 
 * Minimalist dark glassmorphism modal for full Create, Edit, Duplicate,
 * and Delete (CRUD) operations on:
 *   - Layer 1: Cognitive Personas
 *   - Layer 2: Structural Output Formats
 *   - Layer 3: Artistic Styles
 * 
 * Directly reads and writes SSOT Markdown files with YAML frontmatter.
 * Dynamically reloads backend SSOT and syncs ComfyUI canvas node dropdowns in real time.
 */

let modalContainer = null;
let activeNodeRef = null;
let currentKind = "styles"; // "styles" | "personas" | "types"
let currentItemList = [];
let currentItemData = null;
let isNewMode = false;
let originalName = "";

const KIND_METADATA = {
    styles: {
        title: "Artistic Styles",
        icon: "🎨",
        badge: "LAYER 3",
        widgetName: "prompt_style",
        fallbackWidgetName: "artistic_style",
    },
    personas: {
        title: "Cognitive Personas",
        icon: "🧠",
        badge: "LAYER 1",
        widgetName: "system_prompt",
        fallbackWidgetName: "system_prompt",
    },
    types: {
        title: "Output Formats",
        icon: "📐",
        badge: "LAYER 2",
        widgetName: "prompt_type",
        fallbackWidgetName: "prompt_type",
    },
};

function ensureStyles() {
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
    toast.textContent = (isError ? "⚠️ " : "✅ ") + message;
    toast.style.borderColor = isError ? "rgba(255, 69, 58, 0.45)" : "rgba(48, 209, 88, 0.45)";
    toast.style.color = isError ? "#ff453a" : "#30d158";
    toast.classList.add("show");
    setTimeout(() => {
        toast.classList.remove("show");
    }, 3200);
}

export function openPromptStudioModal({ node = null, kind = "styles", activeName = null, isNew = false }) {
    ensureStyles();
    activeNodeRef = node;
    currentKind = kind;

    // Detect target name from active node if not explicitly passed
    if (!activeName && node && node.widgets) {
        const meta = KIND_METADATA[kind];
        const w = node.widgets.find(item => item.name === meta.widgetName || item.name === meta.fallbackWidgetName);
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

export function closePromptStudioModal() {
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
                    <span id="stoiqo-modal-icon">🎨</span>
                    <span id="stoiqo-modal-heading">STOIQO Prompt Studio</span>
                    <span class="stoiqo-modal-badge" id="stoiqo-modal-badge">LAYER 3</span>
                </div>
                <button class="stoiqo-modal-close-btn" id="stoiqo-modal-close">✕</button>
            </div>

            <div class="stoiqo-tabs-bar">
                <button class="stoiqo-tab-btn" data-kind="styles">🎨 Artistic Styles (Layer 3)</button>
                <button class="stoiqo-tab-btn" data-kind="personas">🧠 Cognitive Personas (Layer 1)</button>
                <button class="stoiqo-tab-btn" data-kind="types">📐 Output Formats (Layer 2)</button>
            </div>

            <div class="stoiqo-subnav-toolbar">
                <div class="stoiqo-search-filter-wrap">
                    <input class="stoiqo-input stoiqo-search-input" id="stoiqo-filter-search" placeholder="🔍 Cerca per nome o categoria..." autocomplete="off" />
                </div>
                <div class="stoiqo-selector-group">
                    <select class="stoiqo-item-select" id="stoiqo-item-dropdown"></select>
                    <span class="stoiqo-item-type-tag" id="stoiqo-item-badge">CORE</span>
                </div>
                <div class="stoiqo-toolbar-actions">
                    <button class="stoiqo-btn-sm stoiqo-btn-secondary" id="stoiqo-btn-new">➕ Nuovo</button>
                    <button class="stoiqo-btn-sm stoiqo-btn-secondary" id="stoiqo-btn-dup">📋 Duplica</button>
                    <button class="stoiqo-btn-sm stoiqo-btn-danger" id="stoiqo-btn-del">🗑️ Elimina</button>
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
                    <button class="stoiqo-btn-primary" id="stoiqo-btn-save">💾 Save & Apply to Canvas</button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modalContainer);

    // Event Listeners
    modalContainer.querySelector("#stoiqo-modal-close").addEventListener("click", closePromptStudioModal);
    modalContainer.querySelector("#stoiqo-btn-cancel").addEventListener("click", closePromptStudioModal);

    modalContainer.querySelectorAll(".stoiqo-tab-btn").forEach(btn => {
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

    modalContainer.querySelector("#stoiqo-modal-heading").textContent = `STOIQO Prompt Studio — ${meta.title}`;
    modalContainer.querySelector("#stoiqo-modal-icon").textContent = meta.icon;
    modalContainer.querySelector("#stoiqo-modal-badge").textContent = meta.badge;

    const filterInput = modalContainer.querySelector("#stoiqo-filter-search");
    if (filterInput) filterInput.value = "";

    modalContainer.querySelectorAll(".stoiqo-tab-btn").forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-kind") === kind);
    });

    // Render extra fields for this kind
    renderExtraFields(kind);

    // Fetch item list from server with resilient fallback
    try {
        const resp = await api.fetchApi(`/stoiqo/api/prompt_engine/list?kind=${kind}`);
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

        // Fallback: Read choices from active node widgets so user is never blocked
        let fallbackChoices = [];
        if (activeNodeRef && activeNodeRef.widgets) {
            const w = activeNodeRef.widgets.find(item => item.name === meta.widgetName || item.name === meta.fallbackWidgetName);
            if (w && w.options && Array.isArray(w.options.values)) {
                fallbackChoices = w.options.values;
            }
        }

        if (fallbackChoices.length > 0) {
            currentItemList = fallbackChoices.map((name, idx) => ({
                name,
                category: name.includes("//") ? name.split("//")[0].trim() : (currentKind === "styles" ? "Stili Generali" : "Core Essenziale"),
                order: idx,
                is_core: currentKind === "styles" ? false : idx < 7,
                filename: `${name.toLowerCase().replace(/[^a-z0-9]+/g, "_")}.md`,
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
    const filtered = query
        ? items.filter(it => 
            (it.name && it.name.toLowerCase().includes(query)) ||
            (it.category && it.category.toLowerCase().includes(query)) ||
            (Array.isArray(it.aliases) && it.aliases.some(a => String(a).toLowerCase().includes(query)))
          )
        : items;

    if (filtered.length === 0) {
        const emptyOpt = document.createElement("option");
        emptyOpt.value = "";
        emptyOpt.textContent = `Nessun risultato per "${filterQuery}"`;
        dropdown.appendChild(emptyOpt);
        return;
    }

    // Group items by category (e.g. Photo, Anime, Comics, etc.)
    const groups = {};
    for (const item of filtered) {
        let cat = item.category ? item.category.trim() : (currentKind === "styles" ? "Stili Generali" : (item.is_core ? "Core Essenziale" : "Custom"));
        if (!cat) cat = currentKind === "styles" ? "Stili Generali" : "Custom";
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
            // Layer 1 & 2: lucchetto 🔒 su quelli proprietari essenziali, ✨ su custom
            // Layer 3 (Stili): tutti allo stesso livello, nessun lucchetto!
            if (currentKind === "styles") {
                opt.textContent = item.name;
            } else {
                opt.textContent = `${item.is_core ? "🔒" : "✨"} ${item.name}`;
            }
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
        const resp = await api.fetchApi(`/stoiqo/api/prompt_engine/get?kind=${currentKind}&name=${encodeURIComponent(name)}`);
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

    // Fallback if backend route not reached yet:
    const item = currentItemList.find(x => x.name === name) || { name };
    currentItemData = {
        name: item.name,
        filename: item.filename || `${name}.md`,
        is_core: Boolean(item.is_core),
        frontmatter: {
            name: item.name,
            category: item.category || "",
            order: item.order || 100,
        },
        body: `Direttive per ${name}...\n(Riavvia il server ComfyUI per sincronizzare il file da disco).`,
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
    if (currentKind === "styles") {
        badge.textContent = "🎨 STILE";
        badge.className = "stoiqo-item-type-tag custom";
        modalContainer.querySelector("#stoiqo-btn-del").disabled = false;
    } else {
        badge.textContent = isCore ? "🔒 PROPRIETARIO (BLOCCATO)" : "✨ CUSTOM (MODIFICABILE)";
        badge.className = `stoiqo-item-type-tag ${isCore ? "core" : "custom"}`;
        modalContainer.querySelector("#stoiqo-btn-del").disabled = isCore;
    }

    const kindFolder = currentKind === "styles" ? "style_prompts" : (currentKind === "personas" ? "main_prompts" : "type_prompts");
    modalContainer.querySelector("#stoiqo-footer-info").textContent = 
        `📄 File su disco: core/image/${kindFolder}/${data.filename || "custom.md"}`;

    // Populate extra fields
    if (currentKind === "styles") {
        const medEl = modalContainer.querySelector("#stoiqo-style-medium-type");
        const tagEl = modalContainer.querySelector("#stoiqo-style-tag-injection");
        const negEl = modalContainer.querySelector("#stoiqo-style-negative-injection");
        if (medEl) medEl.value = fm.medium_type || "";
        if (tagEl) tagEl.value = fm.tag_injection || "";
        if (negEl) negEl.value = fm.negative_injection || "";
    } else if (currentKind === "personas") {
        const tempEl = modalContainer.querySelector("#stoiqo-persona-temp");
        const tokEl = modalContainer.querySelector("#stoiqo-persona-tokens");
        const topPEl = modalContainer.querySelector("#stoiqo-persona-top-p");
        const repEl = modalContainer.querySelector("#stoiqo-persona-rep");
        if (tempEl) tempEl.value = fm.temperature ?? 0.65;
        if (tokEl) tokEl.value = fm.max_new_tokens ?? 1024;
        if (topPEl) topPEl.value = fm.top_p ?? 0.90;
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
        const resp = await api.fetchApi("/stoiqo/api/prompt_engine/delete", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ kind: currentKind, name }),
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
        order,
    };

    if (currentKind === "styles") {
        const med = modalContainer.querySelector("#stoiqo-style-medium-type")?.value.trim();
        const tag = modalContainer.querySelector("#stoiqo-style-tag-injection")?.value.trim();
        const neg = modalContainer.querySelector("#stoiqo-style-negative-injection")?.value.trim();
        if (med) frontmatter.medium_type = med;
        if (tag) frontmatter.tag_injection = tag;
        if (neg) frontmatter.negative_injection = neg;
    } else if (currentKind === "personas") {
        frontmatter.temperature = parseFloat(modalContainer.querySelector("#stoiqo-persona-temp")?.value || 0.65);
        frontmatter.max_new_tokens = parseInt(modalContainer.querySelector("#stoiqo-persona-tokens")?.value || 1024, 10);
        frontmatter.top_p = parseFloat(modalContainer.querySelector("#stoiqo-persona-top-p")?.value || 0.90);
        frontmatter.repetition_penalty = parseFloat(modalContainer.querySelector("#stoiqo-persona-rep")?.value || 1.15);
    }

    try {
        const resp = await api.fetchApi("/stoiqo/api/prompt_engine/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                kind: currentKind,
                name,
                body,
                frontmatter,
                original_name: isNewMode ? "" : originalName,
            }),
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

    // Dispatch custom event for any listeners
    try {
        window.dispatchEvent(new CustomEvent("stoiqo-definitions-updated", {
            detail: { kind, choices, newlySelectedName }
        }));
    } catch (_) {}

    // Synchronize active node if connected
    if (activeNodeRef && activeNodeRef.widgets) {
        const meta = KIND_METADATA[kind];
        const w = activeNodeRef.widgets.find(item => item.name === meta.widgetName || item.name === meta.fallbackWidgetName);
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
