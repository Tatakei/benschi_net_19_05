let selectedImageId = null;

document.addEventListener('DOMContentLoaded', () => {
    const navItems = document.querySelectorAll('nav li');
    const tabs = document.querySelectorAll('.tab-content');
    const pageTitle = document.getElementById('page-title');
    const notesArea = document.getElementById('projectNotes');
    const tpsDisplay = document.getElementById('tps-display');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const target = item.getAttribute('data-target');
            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            tabs.forEach(tab => {
                tab.classList.remove('active');
                if (tab.id === target) tab.classList.add('active');
            });
            pageTitle.innerText = item.innerText.trim();
        });
    });

    notesArea.addEventListener('input', (e) => localStorage.setItem('atm10_notes', e.target.value));
    const savedNotes = localStorage.getItem('atm10_notes');
    if (savedNotes) notesArea.value = savedNotes;

    loadMatrixGrid();
});

const MATRIX_CONFIG = {
    "Import": { class: "import-card", icon: "fa-file-import", title: "Import" },
    "Export": { class: "export-card", icon: "fa-file-export", title: "Export" },
    "Transfer": { class: "transfer-card", icon: "fa-exchange-alt", title: "Transfer" },
    "ME2_Request": { class: "request-card", icon: "fa-shuttle-van", title: "ME2 Request" },
    "Unknown": { class: "unknown-card", icon: "fa-question-circle", title: "Unknown" }
};

const CATEGORY_ASSETS = {
    "Dimensional Chest": "dimensional_chest.png",
    "Dimensional Fluid Tank": "dimensional_fluid_tank.png"
};

function getTypeFromFreq(freq) {
    const f = parseInt(freq);
    if (f >= 1 && f <= 99) return "Import";
    if (f >= 100 && f <= 199) return "Export";
    if (f >= 300 && f <= 399) return "Transfer";
    if (f >= 400 && f <= 499) return "ME2_Request";
    return "Unknown";
}

async function loadMatrixGrid() {
    const content = document.querySelector('#dimstorage');
    const content__header = document.querySelector('#dimstorage__header');
    if (!content) return;

    try {
        const response = await fetch('/data/get');
        const data = await response.json();

        content__header.innerHTML = `
<div class="matrix-card">
    <div class="matrix-setup-container">
        <div class="matrix-type-selector">
            <label class="type-option">
                <input type="radio" name="matrix_type" value="Dimensional Chest" checked>
                <div class="option-content ds_yaml_form_input">
                    <img src="/static/img/blocks/dimensional_chest.png" width="40">
                    <span>Dimensional Chest</span>
                </div>
            </label>
            <label class="type-option">
                <input type="radio" name="matrix_type" value="Dimensional Fluid Tank">
                <div class="option-content ds_yaml_form_input">
                    <img src="/static/img/blocks/dimensional_fluid_tank.png" width="40">
                    <span>Dimensional Fluid Tank</span>
                </div>
            </label>
            <button class="btn-ghost-purple" onclick="validateYAML()"><span class="btn-text">VALIDATE</span></button>
        </div>
        <div class="matrix-config-side">
            <div class="form-group"><label>Description</label><textarea id="input-desc" placeholder="Enter link description..." rows="2" class="ds_yaml_form_input"></textarea></div>
            <div class="form-row">
                <div class="form-group"><label>Frequency</label><input type="number" id="input-freq" min="0" max="999" placeholder="000" class="matrix-input ds_yaml_form_input"></div>
                <div class="form-group"><label>UID (System)</label><input type="text" id="input-uid" value="#AUTO_GEN" class="matrix-input blocked" readonly></div>
            </div>
        </div>
    </div>
</div>`;

        const typeOrder = ["Import", "Export", "Transfer", "ME2_Request"];
        const gridItems = document.querySelectorAll('.category-group');
        gridItems.forEach(el => el.remove());

        for (const [categoryName, items] of Object.entries(data)) {
            const fileName = CATEGORY_ASSETS[categoryName] || "unknown.png";
            let html = `<div class="category-group"><div class="category-header-main"><img src="/static/img/blocks/${fileName}" alt="${categoryName}"></div>`;

            const grouped = { "Import": [], "Export": [], "Transfer": [], "ME2_Request": [], "Unknown": [] };
            items.forEach(item => grouped[getTypeFromFreq(item.freq)].push(item));

            typeOrder.forEach(typeName => {
                const typeItems = grouped[typeName];
                if (typeItems.length === 0) return;
                html += `<div class="matrix-grid">`;
                typeItems.forEach(item => {
                    const config = MATRIX_CONFIG[typeName];
                    html += `
                        <div class="matrix-card ${config.class}" data-id="${item.id}">
                            <div class="matrix-card-header"><h3>${config.title}</h3><i class="fas ${config.icon}"></i></div>
                            <div class="matrix-dim-row"><span>${item.label}</span><span class="matrix-dim-freq">#${item.freq}</span></div>
                            <div class="matrix-actions">
                                <div class="matrix-user-info"><span>${item.user}</span></div>
                                <div class="matrix-btn-group">
                                    <button class="matrix-btn-pixel matrix-btn-edit" onclick="openEditModal(${item.id}, '${item.label}', ${item.freq})">Edit</button>
                                    <button class="matrix-btn-pixel matrix-btn-delete" onclick="deleteItem(${item.id})">Delete</button>
                                </div>
                            </div>
                        </div>`;
                });
                const remainder = typeItems.length % 3;
                if (remainder !== 0) for (let i = 0; i < (3 - remainder); i++) html += `<div class="matrix-card" style="visibility: hidden; pointer-events: none;"></div>`;
                html += `</div>`;
            });
            html += `</div>`;
            content.insertAdjacentHTML('beforeend', html);
        }

        const radioGroup = document.querySelectorAll('input[name="matrix_type"]');
        radioGroup.forEach(radio => radio.addEventListener('change', (e) => { if (e.target.checked) selectedImageId = e.target.value; }));
        selectedImageId = document.querySelector('input[name="matrix_type"]:checked').value;
    } catch (error) { console.error(error); }
}

async function validateYAML() {
    const desc = document.querySelector('#input-desc').value.trim();
    const freq = document.querySelector('#input-freq').value;
    if (!desc || !freq || freq === '0') return showToast('error', 'Missing data!');

    const res = await fetch('/data/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category: selectedImageId, label: desc, freq: freq })
    });
    if (res.ok) { showToast('success', 'Saved!'); setTimeout(() => location.reload(), 1000); }
}

async function deleteItem(id) {
    if (!confirm("Delete this entry?")) return;
    const res = await fetch('/data/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: id })
    });
    if (res.ok) location.reload();
}

async function openEditModal(id, oldLabel, oldFreq) {
    const newLabel = prompt("New Description:", oldLabel);
    const newFreq = prompt("New Frequency:", oldFreq);
    if (!newLabel || !newFreq) return;

    const res = await fetch('/data/edit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: id, label: newLabel, freq: newFreq })
    });
    if (res.ok) location.reload();
}

// Run this BEFORE the DOM even fully loads if possible to catch the scroll
window.scrollTo(0, 0);

document.addEventListener("DOMContentLoaded", () => {
    const navItems = document.querySelectorAll('li[data-target]');
    const sections = document.querySelectorAll('.tab-content');
    const titleElement = document.getElementById('page-title');

    const switchTab = (targetId) => {
        if (!targetId) return;

        const targetLi = document.querySelector(`li[data-target="${targetId}"]`);
        const targetSection = document.getElementById('tab-' + targetId);

        if (targetSection) {
            navItems.forEach(li => li.classList.remove('active'));
            sections.forEach(sec => sec.classList.remove('active'));

            if (targetLi) {
                targetLi.classList.add('active');
                if (titleElement) titleElement.textContent = targetLi.textContent.trim();
            }

            targetSection.classList.add('active');

            // Use replaceState to change URL without triggering a jump
            history.replaceState(null, null, `#${targetId}`);
        }
    };

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            switchTab(item.getAttribute('data-target'));
        });
    });

    // Capture the hash and immediately clear it from the URL temporarily
    // to prevent the browser from finding the ID and jumping
    const initialHash = window.location.hash.replace('#', '');

    if (initialHash) {
        // Force the scroll to the top of the page
        window.scrollTo(0, 0);
        // Execute the tab switch
        switchTab(initialHash);
        // Second safety scroll for stubborn browsers
        setTimeout(() => window.scrollTo(0, 0), 1);
    } else {
        switchTab('dashboard');
    }
});

const textarea = document.querySelector('projectNotes');

textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
        alert("a")
        e.preventDefault();

        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;

        textarea.value = textarea.value.substring(0, start) +
            "  " +
            textarea.value.substring(end);

        textarea.selectionStart = textarea.selectionEnd = start + 2;
    }
});