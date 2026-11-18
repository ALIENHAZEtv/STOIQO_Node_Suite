/**
 * [STOIQO] Searchable Picker Modal
 * 
 * High-performance, minimalist dark modal with live search, folder filters,
 * and keyboard navigation (↑/↓/Enter/Esc) for selecting Models and LoRAs.
 */

let modalBackdrop = null;
let currentItems = [];
let filteredItems = [];
let highlightedIndex = 0;
let activeFolderFilter = "ALL";
let onPickCallback = null;
let onRefreshCallback = null;
let activeItemIcon = "📦";
let currentSelectedValue = "";

function ensureStyles() {
    if (document.getElementById("stoiqo-searchable-picker-styles")) return;

    const styleEl = document.createElement("style");
    styleEl.id = "stoiqo-searchable-picker-styles";
    styleEl.textContent = `
        .stoiqo-picker-backdrop {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(3, 5, 8, 0.80);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            z-index: 10005;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.18s cubic-bezier(0.16, 1, 0.3, 1);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #f1f5f9;
        }
        .stoiqo-picker-backdrop.open {
            opacity: 1;
            pointer-events: auto;
        }
        .stoiqo-picker-box {
            background: #090b10;
            border: 1px solid rgba(255, 255, 255, 0.11);
            border-radius: 12px;
            width: 700px;
            max-width: 94vw;
            height: 580px;
            max-height: 86vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 30px 90px rgba(0, 0, 0, 0.88), 0 0 1px 1px rgba(255, 255, 255, 0.06);
            overflow: hidden;
            transform: scale(0.96);
            transition: transform 0.18s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .stoiqo-picker-backdrop.open .stoiqo-picker-box {
            transform: scale(1);
        }
        .stoiqo-picker-header {
            padding: 14px 18px 12px;
            background: rgba(16, 20, 30, 0.75);
            border-bottom: 1px solid rgba(255, 255, 255, 0.07);
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .stoiqo-picker-topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .stoiqo-picker-title {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -0.2px;
        }
        .stoiqo-picker-count {
            font-size: 10px;
            font-weight: 700;
            padding: 2px 7px;
            border-radius: 4px;
            background: rgba(41, 151, 255, 0.15);
            border: 1px solid rgba(41, 151, 255, 0.38);
            color: #58b0ff;
        }
        .stoiqo-picker-top-actions {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .stoiqo-picker-btn-icon {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #94a3b8;
            font-size: 12.5px;
            cursor: pointer;
            padding: 5px 9px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            gap: 5px;
            transition: background 0.15s, color 0.15s;
        }
        .stoiqo-picker-btn-icon:hover {
            background: rgba(255, 255, 255, 0.12);
            color: #ffffff;
        }
        .stoiqo-picker-search-wrap {
            position: relative;
            display: flex;
            align-items: center;
        }
        .stoiqo-picker-search-icon {
            position: absolute;
            left: 12px;
            font-size: 14px;
            color: #64748b;
            pointer-events: none;
        }
        .stoiqo-picker-input {
            width: 100%;
            background: #11141e;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 8px;
            color: #ffffff;
            padding: 10px 36px 10px 36px;
            font-size: 13.5px;
            outline: none;
            transition: border-color 0.15s, background 0.15s;
            box-sizing: border-box;
        }
        .stoiqo-picker-input:focus {
            border-color: #2997ff;
            background: #141824;
            box-shadow: 0 0 0 1px #2997ff;
        }
        .stoiqo-picker-clear-btn {
            position: absolute;
            right: 10px;
            background: transparent;
            border: none;
            color: #64748b;
            font-size: 14px;
            cursor: pointer;
            padding: 4px;
            border-radius: 4px;
            display: none;
        }
        .stoiqo-picker-clear-btn:hover {
            color: #ffffff;
        }
        .stoiqo-picker-chips-bar {
            display: flex;
            gap: 6px;
            overflow-x: auto;
            padding: 2px 0 2px;
            max-width: 100%;
            scrollbar-width: none;
        }
        .stoiqo-picker-chips-bar::-webkit-scrollbar {
            display: none;
        }
        .stoiqo-picker-chip {
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #94a3b8;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.15s;
        }
        .stoiqo-picker-chip:hover {
            background: rgba(255, 255, 255, 0.10);
            color: #f1f5f9;
        }
        .stoiqo-picker-chip.active {
            background: rgba(41, 151, 255, 0.18);
            border-color: rgba(41, 151, 255, 0.50);
            color: #58b0ff;
        }
        .stoiqo-picker-list {
            flex: 1;
            overflow-y: auto;
            padding: 8px 10px;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        .stoiqo-picker-list::-webkit-scrollbar {
            width: 6px;
        }
        .stoiqo-picker-list::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.14);
            border-radius: 3px;
        }
        .stoiqo-picker-item {
            padding: 8px 12px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            cursor: pointer;
            background: transparent;
            border: 1px solid transparent;
            transition: background 0.1s, border-color 0.1s;
        }
        .stoiqo-picker-item:hover, .stoiqo-picker-item.highlighted {
            background: rgba(41, 151, 255, 0.14);
            border-color: rgba(41, 151, 255, 0.40);
        }
        .stoiqo-picker-item.active-selected {
            background: rgba(48, 209, 88, 0.10);
            border-color: rgba(48, 209, 88, 0.35);
        }
        .stoiqo-picker-item-left {
            display: flex;
            align-items: center;
            gap: 10px;
            overflow: hidden;
            flex: 1;
        }
        .stoiqo-picker-item-icon {
            font-size: 14px;
            flex-shrink: 0;
        }
        .stoiqo-picker-item-info {
            display: flex;
            flex-direction: column;
            overflow: hidden;
            gap: 2px;
        }
        .stoiqo-picker-item-name {
            font-size: 13px;
            font-weight: 600;
            color: #f1f5f9;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .stoiqo-picker-item-path {
            font-size: 10.5px;
            color: #64748b;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-family: 'JetBrains Mono', SFMono-Regular, Consolas, monospace;
        }
        .stoiqo-picker-item-right {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-shrink: 0;
        }
        .stoiqo-picker-item-ext {
            font-size: 9.5px;
            font-weight: 700;
            text-transform: uppercase;
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #94a3b8;
            font-family: 'JetBrains Mono', monospace;
        }
        .stoiqo-picker-item-active-tag {
            font-size: 10px;
            font-weight: 700;
            color: #30d158;
            background: rgba(48, 209, 88, 0.15);
            border: 1px solid rgba(48, 209, 88, 0.35);
            border-radius: 4px;
            padding: 1px 5px;
        }
        .stoiqo-picker-empty {
            padding: 40px 20px;
            text-align: center;
            color: #64748b;
            font-size: 13px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }
        .stoiqo-picker-footer {
            padding: 10px 18px;
            background: rgba(14, 18, 28, 0.85);
            border-top: 1px solid rgba(255, 255, 255, 0.07);
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 11.5px;
            color: #64748b;
        }
        .stoiqo-picker-kbd-hints {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .stoiqo-picker-kbd {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 4px;
            padding: 1px 5px;
            font-size: 10px;
            color: #cbd5e1;
            font-family: monospace;
        }
    `;
    document.head.appendChild(styleEl);
}

function parseItemMeta(rawPath) {
    const norm = String(rawPath || "").replace(/\\/g, "/");
    const parts = norm.split("/");
    const filename = parts[parts.length - 1];
    const folder = parts.length > 1 ? parts.slice(0, -1).join("/") : "";
    const dotIdx = filename.lastIndexOf(".");
    const baseName = dotIdx !== -1 ? filename.slice(0, dotIdx) : filename;
    const ext = dotIdx !== -1 ? filename.slice(dotIdx + 1) : "";

    return {
        raw: rawPath,
        norm,
        filename,
        baseName,
        folder: folder || "Root",
        ext,
    };
}

function buildPickerDOM() {
    modalBackdrop = document.createElement("div");
    modalBackdrop.className = "stoiqo-picker-backdrop";

    modalBackdrop.innerHTML = `
        <div class="stoiqo-picker-box">
            <div class="stoiqo-picker-header">
                <div class="stoiqo-picker-topbar">
                    <div class="stoiqo-picker-title">
                        <span id="stoiqo-picker-icon">📦</span>
                        <span id="stoiqo-picker-heading">Seleziona File</span>
                        <span class="stoiqo-picker-count" id="stoiqo-picker-total">0</span>
                    </div>
                    <div class="stoiqo-picker-top-actions">
                        <button class="stoiqo-picker-btn-icon" id="stoiqo-picker-refresh-btn" title="Ricarica lista da disco">
                            <span>🔄</span> Ricarica
                        </button>
                        <button class="stoiqo-picker-btn-icon" id="stoiqo-picker-close-btn" style="padding: 4px 7px;">
                            ✕
                        </button>
                    </div>
                </div>

                <div class="stoiqo-picker-search-wrap">
                    <span class="stoiqo-picker-search-icon">🔍</span>
                    <input class="stoiqo-picker-input" id="stoiqo-picker-search-input" placeholder="Cerca file o cartella... (es. sdxl, flux, anime, v2)" autocomplete="off" spellcheck="false" />
                    <button class="stoiqo-picker-clear-btn" id="stoiqo-picker-clear-search">✕</button>
                </div>

                <div class="stoiqo-picker-chips-bar" id="stoiqo-picker-chips"></div>
            </div>

            <div class="stoiqo-picker-list" id="stoiqo-picker-items-list"></div>

            <div class="stoiqo-picker-footer">
                <div class="stoiqo-picker-kbd-hints">
                    <span><span class="stoiqo-picker-kbd">↑</span> <span class="stoiqo-picker-kbd">↓</span> Naviga</span>
                    <span><span class="stoiqo-picker-kbd">↵</span> Seleziona</span>
                    <span><span class="stoiqo-picker-kbd">Esc</span> Chiudi</span>
                </div>
                <div id="stoiqo-picker-status-info">STOIQO Universal Picker</div>
            </div>
        </div>
    `;

    document.body.appendChild(modalBackdrop);

    // Event listeners
    const searchInput = modalBackdrop.querySelector("#stoiqo-picker-search-input");
    const clearBtn = modalBackdrop.querySelector("#stoiqo-picker-clear-search");
    const closeBtn = modalBackdrop.querySelector("#stoiqo-picker-close-btn");
    const refreshBtn = modalBackdrop.querySelector("#stoiqo-picker-refresh-btn");

    modalBackdrop.addEventListener("click", (e) => {
        if (e.target === modalBackdrop) closeSearchablePicker();
    });

    closeBtn.addEventListener("click", closeSearchablePicker);

    clearBtn.addEventListener("click", () => {
        searchInput.value = "";
        clearBtn.style.display = "none";
        filterList();
        searchInput.focus();
    });

    searchInput.addEventListener("input", () => {
        clearBtn.style.display = searchInput.value ? "block" : "none";
        filterList();
    });

    refreshBtn.addEventListener("click", async () => {
        if (onRefreshCallback) {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = `<span>⏳</span> Scansione...`;
            try {
                const newList = await onRefreshCallback();
                if (Array.isArray(newList)) {
                    currentItems = newList;
                    renderFolderChips();
                    filterList();
                }
            } catch (err) {
                console.error("[STOIQO Picker] Refresh error:", err);
            } finally {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = `<span>🔄</span> Ricarica`;
            }
        }
    });

    // Keyboard navigation
    modalBackdrop.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeSearchablePicker();
            e.preventDefault();
            return;
        }

        if (e.key === "ArrowDown") {
            if (filteredItems.length > 0) {
                highlightedIndex = (highlightedIndex + 1) % filteredItems.length;
                updateHighlightedRow();
            }
            e.preventDefault();
            return;
        }

        if (e.key === "ArrowUp") {
            if (filteredItems.length > 0) {
                highlightedIndex = (highlightedIndex - 1 + filteredItems.length) % filteredItems.length;
                updateHighlightedRow();
            }
            e.preventDefault();
            return;
        }

        if (e.key === "Enter") {
            if (filteredItems.length > 0 && filteredItems[highlightedIndex]) {
                const chosen = filteredItems[highlightedIndex].raw;
                if (onPickCallback) onPickCallback(chosen);
                closeSearchablePicker();
            }
            e.preventDefault();
            return;
        }
    });
}

function renderFolderChips() {
    const chipsBar = modalBackdrop.querySelector("#stoiqo-picker-chips");
    chipsBar.innerHTML = "";

    const folderCounts = new Map();
    let totalCount = currentItems.length;

    currentItems.forEach(it => {
        const meta = parseItemMeta(it);
        folderCounts.set(meta.folder, (folderCounts.get(meta.folder) || 0) + 1);
    });

    if (folderCounts.size <= 1) {
        chipsBar.style.display = "none";
        return;
    }
    chipsBar.style.display = "flex";

    // All chip
    const allChip = document.createElement("button");
    allChip.className = `stoiqo-picker-chip ${activeFolderFilter === "ALL" ? "active" : ""}`;
    allChip.textContent = `Tutti (${totalCount})`;
    allChip.addEventListener("click", () => {
        activeFolderFilter = "ALL";
        renderFolderChips();
        filterList();
    });
    chipsBar.appendChild(allChip);

    // Sorted folder chips
    const sortedFolders = [...folderCounts.keys()].sort((a, b) => {
        if (a === "Root") return -1;
        if (b === "Root") return 1;
        return a.localeCompare(b);
    });

    sortedFolders.forEach(folder => {
        const count = folderCounts.get(folder);
        const chip = document.createElement("button");
        chip.className = `stoiqo-picker-chip ${activeFolderFilter === folder ? "active" : ""}`;
        chip.textContent = `${folder === "Root" ? "📁 Root" : folder} (${count})`;
        chip.addEventListener("click", () => {
            activeFolderFilter = folder;
            renderFolderChips();
            filterList();
        });
        chipsBar.appendChild(chip);
    });
}

function filterList() {
    const searchInput = modalBackdrop.querySelector("#stoiqo-picker-search-input");
    const query = (searchInput.value || "").trim().toLowerCase();
    const queryTokens = query.split(/\s+/).filter(Boolean);

    filteredItems = currentItems
        .map(it => parseItemMeta(it))
        .filter(meta => {
            // Folder check
            if (activeFolderFilter !== "ALL" && meta.folder !== activeFolderFilter) {
                return false;
            }
            // Multi-token fuzzy match
            if (queryTokens.length > 0) {
                const targetText = `${meta.norm} ${meta.baseName}`.toLowerCase();
                return queryTokens.every(token => targetText.includes(token));
            }
            return true;
        });

    highlightedIndex = 0;
    renderList();
}

function renderList() {
    const listEl = modalBackdrop.querySelector("#stoiqo-picker-items-list");
    const countEl = modalBackdrop.querySelector("#stoiqo-picker-total");
    listEl.innerHTML = "";

    countEl.textContent = `${filteredItems.length} di ${currentItems.length}`;

    if (filteredItems.length === 0) {
        listEl.innerHTML = `
            <div class="stoiqo-picker-empty">
                <span style="font-size: 28px;">🔍</span>
                <span style="font-weight: 600;">Nessun elemento corrispondente alla ricerca.</span>
                <span style="font-size: 11px; opacity: 0.7;">Prova con una parola chiave diversa o premi Ricarica.</span>
            </div>
        `;
        return;
    }

    // Limit rendered items to 200 for lightning performance
    const renderLimit = Math.min(filteredItems.length, 200);

    for (let i = 0; i < renderLimit; i++) {
        const meta = filteredItems[i];
        const isCurrent = Boolean(
            currentSelectedValue &&
            (meta.raw === currentSelectedValue || meta.norm === currentSelectedValue || meta.filename === currentSelectedValue)
        );

        const row = document.createElement("div");
        row.className = `stoiqo-picker-item ${i === highlightedIndex ? "highlighted" : ""} ${isCurrent ? "active-selected" : ""}`;
        row.dataset.index = i;

        row.innerHTML = `
            <div class="stoiqo-picker-item-left">
                <span class="stoiqo-picker-item-icon">${activeItemIcon}</span>
                <div class="stoiqo-picker-item-info">
                    <span class="stoiqo-picker-item-name" title="${meta.filename}">${meta.baseName}</span>
                    <span class="stoiqo-picker-item-path" title="${meta.norm}">${meta.folder !== "Root" ? `📁 ${meta.folder}/` : "Root"}</span>
                </div>
            </div>
            <div class="stoiqo-picker-item-right">
                ${isCurrent ? `<span class="stoiqo-picker-item-active-tag">ATTIVO</span>` : ""}
                ${meta.ext ? `<span class="stoiqo-picker-item-ext">.${meta.ext}</span>` : ""}
            </div>
        `;

        row.addEventListener("mouseenter", () => {
            highlightedIndex = i;
            updateHighlightedRow(false);
        });

        row.addEventListener("click", () => {
            if (onPickCallback) onPickCallback(meta.raw);
            closeSearchablePicker();
        });

        listEl.appendChild(row);
    }

    if (filteredItems.length > renderLimit) {
        const moreNotice = document.createElement("div");
        moreNotice.style.padding = "10px 14px";
        moreNotice.style.fontSize = "11.5px";
        moreNotice.style.color = "#64748b";
        moreNotice.style.textAlign = "center";
        moreNotice.textContent = `... altri ${filteredItems.length - renderLimit} file disponibili. Digita per affinare la ricerca.`;
        listEl.appendChild(moreNotice);
    }
}

function updateHighlightedRow(scrollIntoView = true) {
    const listEl = modalBackdrop.querySelector("#stoiqo-picker-items-list");
    const rows = listEl.querySelectorAll(".stoiqo-picker-item");

    rows.forEach((r, idx) => {
        const isCurrent = idx === highlightedIndex;
        r.classList.toggle("highlighted", isCurrent);
        if (isCurrent && scrollIntoView) {
            r.scrollIntoView({ block: "nearest", behavior: "smooth" });
        }
    });
}

/**
 * Opens the searchable picker modal.
 * @param {Object} options
 * @param {string} options.title - Modal title (e.g. "Scegli Modello")
 * @param {string} options.icon - Emoji icon (e.g. "📦" or "⚡")
 * @param {string[]} options.items - Array of relative file paths
 * @param {string} [options.current] - Currently selected item name
 * @param {Function} options.onPick - Callback(chosenString)
 * @param {Function} [options.onRefresh] - Async callback returning fresh string[]
 */
export function openSearchablePicker(options = {}) {
    ensureStyles();

    if (!modalBackdrop) {
        buildPickerDOM();
    }

    const {
        title = "Seleziona File",
        icon = "📦",
        items = [],
        current = "",
        onPick = null,
        onRefresh = null,
    } = options;

    activeItemIcon = icon;
    currentItems = Array.isArray(items) ? [...items] : [];
    currentSelectedValue = current || "";
    activeFolderFilter = "ALL";
    onPickCallback = onPick;
    onRefreshCallback = onRefresh;

    modalBackdrop.querySelector("#stoiqo-picker-heading").textContent = title;
    modalBackdrop.querySelector("#stoiqo-picker-icon").textContent = icon;

    const searchInput = modalBackdrop.querySelector("#stoiqo-picker-search-input");
    searchInput.value = "";
    modalBackdrop.querySelector("#stoiqo-picker-clear-search").style.display = "none";

    renderFolderChips();
    filterList();

    modalBackdrop.classList.add("open");

    // Instant autofocus on search bar
    setTimeout(() => {
        searchInput.focus();
        searchInput.select();
    }, 40);
}

export function closeSearchablePicker() {
    if (modalBackdrop) {
        modalBackdrop.classList.remove("open");
    }
}
