//-----------------------------------------------------------------------------------------------
// UI Base Case Initialisieren
//-----------------------------------------------------------------------------------------------
const canvas = document.getElementById('structureCanvas');
const ctx = canvas.getContext('2d');
const toolSelect = document.getElementById('tool-select');
const sliderW = document.getElementById('slider-width');
const sliderH = document.getElementById('slider-height');
const sliderMass = document.getElementById('slider-mass');
const sliderForce = document.getElementById('slider-force');

let gridState = {
    supports: {},
    forces: {},
    nodesX: 40,
    nodesY: 10
};

let isShowingResult = false;

sliderW.addEventListener('input', (e) => {
    document.getElementById('val-width').innerText = e.target.value;
    setBaseCase();
});
sliderH.addEventListener('input', (e) => {
    document.getElementById('val-height').innerText = e.target.value;
    setBaseCase();
});
sliderMass.addEventListener('input', (e) => { document.getElementById('val-mass').innerText = e.target.value; });
sliderForce.addEventListener('input', (e) => { document.getElementById('val-force').innerText = e.target.value; });

canvas.addEventListener('mousedown', (e) => {
    if (isShowingResult) {
        setBaseCase();
        return;
    }
    handleCanvasClick(e);
});

function setBaseCase() {
    isShowingResult = false;
    const term = document.getElementById('terminal-content');
    const statusDot = document.getElementById('status-dot');
    term.innerHTML = "System reset. Base case applied.";
    statusDot.classList.remove('active');
    gridState.nodesX = parseInt(sliderW.value);
    gridState.nodesY = parseInt(sliderH.value);
    gridState.supports = {};
    gridState.forces = {};
    const leftBottom = `0,${gridState.nodesY - 1}`;
    gridState.supports[leftBottom] = "roller";
    const rightBottom = `${gridState.nodesX - 1},${gridState.nodesY - 1}`;
    gridState.supports[rightBottom] = "fixed";
    const topMiddleX = Math.floor(gridState.nodesX / 2);
    const topMiddle = `${topMiddleX},0`;
    gridState.forces[topMiddle] = { fy: 1000 };
    updateCanvas();
}

function handleCanvasClick(e) {
    const rect = canvas.getBoundingClientRect();
    const { spacing, offsetX, offsetY } = calculateGridMetrics();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const xIdx = Math.round((mouseX - offsetX) / spacing);
    const yIdx = Math.round((mouseY - offsetY) / spacing);
    if (xIdx >= 0 && xIdx < gridState.nodesX && yIdx >= 0 && yIdx < gridState.nodesY) {
        applyTool(xIdx, yIdx);
        updateCanvas();
    }
}

function applyTool(x, y) {
    const key = `${x},${y}`;
    const tool = toolSelect.value;
    if (tool === 'fixed' || tool === 'roller') {
        gridState.supports[key] = tool;
        delete gridState.forces[key];
    } else if (tool === 'force') {
        gridState.forces[key] = { fy: 1000 };
        delete gridState.supports[key];
    } else if (tool === 'eraser') {
        delete gridState.supports[key];
        delete gridState.forces[key];
    }
}

function calculateGridMetrics() {
    const padding = 40;
    const availWidth = canvas.width - (padding * 2);
    const availHeight = canvas.height - (padding * 2);
    const spacing = Math.min(
        availWidth / (gridState.nodesX - 1),
        availHeight / (gridState.nodesY - 1)
    );
    const offsetX = (canvas.width - (gridState.nodesX - 1) * spacing) / 2;
    const offsetY = (canvas.height - (gridState.nodesY - 1) * spacing) / 2;
    return { spacing, offsetX, offsetY };
}

function updateCanvas() {
    const { spacing, offsetX, offsetY } = calculateGridMetrics();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let y = 0; y < gridState.nodesY; y++) {
        for (let x = 0; x < gridState.nodesX; x++) {
            const posX = offsetX + x * spacing;
            const posY = offsetY + y * spacing;
            if (x < gridState.nodesX - 1) {
                ctx.moveTo(posX, posY);
                ctx.lineTo(posX + spacing, posY);
            }
            if (y < gridState.nodesY - 1) {
                ctx.moveTo(posX, posY);
                ctx.lineTo(posX, posY + spacing);
            }
            if (x < gridState.nodesX - 1 && y < gridState.nodesY - 1) {
                ctx.moveTo(posX, posY);
                ctx.lineTo(posX + spacing, posY + spacing);
                ctx.moveTo(posX + spacing, posY);
                ctx.lineTo(posX, posY + spacing);
            }
        }
    }
    ctx.stroke();
    for (let x = 0; x < gridState.nodesX; x++) {
        for (let y = 0; y < gridState.nodesY; y++) {
            const key = `${x},${y}`;
            const posX = offsetX + x * spacing;
            const posY = offsetY + y * spacing;
            ctx.beginPath();
            ctx.arc(posX, posY, 3, 0, 2 * Math.PI);
            ctx.fillStyle = '#3b82f6';
            ctx.fill();
            if (gridState.supports[key]) drawSymbol(posX, posY, gridState.supports[key]);
            if (gridState.forces[key]) drawArrow(posX, posY);
        }
    }
}
//-----------------------------------------------------------------------------------------------
// Verbinde Frontend Struktur mit Backend Optimierung
//-----------------------------------------------------------------------------------------------
function renderOptimizedStructure(nodes) {
    const { spacing, offsetX, offsetY } = calculateGridMetrics();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const activeMap = new Set();
    nodes.forEach(n => {
        if(n.active) activeMap.add(`${n.x},${n.z}`);
    });
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let y = 0; y < gridState.nodesY; y++) {
        for (let x = 0; x < gridState.nodesX; x++) {
            const posX = offsetX + x * spacing;
            const posY = offsetY + y * spacing;
            if (x < gridState.nodesX - 1) {
                if (activeMap.has(`${x},${y}`) && activeMap.has(`${x+1},${y}`)) {
                    ctx.moveTo(posX, posY);
                    ctx.lineTo(posX + spacing, posY);
                }
            }
            if (y < gridState.nodesY - 1) {
                if (activeMap.has(`${x},${y}`) && activeMap.has(`${x},${y+1}`)) {
                    ctx.moveTo(posX, posY);
                    ctx.lineTo(posX, posY + spacing);
                }
            }
            if (x < gridState.nodesX - 1 && y < gridState.nodesY - 1) {
                if (activeMap.has(`${x},${y}`) && activeMap.has(`${x+1},${y+1}`)) {
                    ctx.moveTo(posX, posY);
                    ctx.lineTo(posX + spacing, posY + spacing);
                }
                if (activeMap.has(`${x+1},${y}`) && activeMap.has(`${x},${y+1}`)) {
                    ctx.moveTo(posX + spacing, posY);
                    ctx.lineTo(posX, posY + spacing);
                }
            }
        }
    }
    ctx.stroke();
    nodes.forEach(n => {
        if (!n.active) return;
        const posX = offsetX + n.x * spacing;
        const posY = offsetY + n.z * spacing;
        ctx.beginPath();
        ctx.arc(posX, posY, 3, 0, 2 * Math.PI);
        ctx.fillStyle = '#3b82f6';
        ctx.fill();
        const key = `${n.x},${n.z}`;
        if (gridState.supports[key]) drawSymbol(posX, posY, gridState.supports[key]);
        if (gridState.forces[key]) drawArrow(posX, posY);
    });
}

function drawSymbol(x, y, type) {
    ctx.fillStyle = '#ef4444';
    ctx.beginPath();
    if (type === 'fixed') {
        ctx.moveTo(x, y);
        ctx.lineTo(x - 8, y + 12);
        ctx.lineTo(x + 8, y + 12);
    } else {
        ctx.arc(x, y + 6, 6, 0, 2*Math.PI);
    }
    ctx.fill();
}

function drawArrow(x, y) {
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(x, y - 25);
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x - 5, y - 8);
    ctx.lineTo(x, y);
    ctx.lineTo(x + 5, y - 8);
    ctx.stroke();
}

function resetAnalysis() {
    setBaseCase();
}

function switchView(viewName) {
    const dashboard = document.getElementById('dashboard-view');
    const staticView = document.getElementById('static-analysis-view');
    if (viewName === 'static-analysis') {
        dashboard.style.display = 'none';
        staticView.style.display = 'block';
        setBaseCase();
    } else {
        dashboard.style.display = 'grid';
        staticView.style.display = 'none';
    }
}

async function triggerPythonSolver() {
    const term = document.getElementById('terminal-content');
    const statusDot = document.getElementById('status-dot');
    term.innerHTML = "<div style='opacity:0.6'>System initialized. Stream started...</div><br>";
    statusDot.classList.add('active');

    const currentForce = parseFloat(sliderForce.value);
    const qualityRate = parseFloat(document.getElementById('select-quality').value);
    const payload = {
        width: gridState.nodesX,
        height: gridState.nodesY,
        mass_ratio: parseInt(sliderMass.value) / 100,
        supports: gridState.supports,
        removal_rate: qualityRate,
        forces: Object.keys(gridState.forces).reduce((acc, key) => {
            acc[key] = { fy: currentForce };
            return acc;
        }, {})
    };

    try {
        const response = await fetch('/api/optimize', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error("Server Error");

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;
            let parts = buffer.split("\n");
            buffer = parts.pop();

            for (let part of parts) {
                if (!part.trim()) continue;
                try {
                    const result = JSON.parse(part);

                    if (result.nodes) {
                        isShowingResult = true;
                        lastOptimizedNodes = result.nodes;
                        renderOptimizedStructure(result.nodes);
                    }
                    if (result.status === "finished") {
                        term.innerHTML += `<div style='color:#007aff;'>✓ ${result.message}</div>`;
                        term.scrollTop = term.scrollHeight;
                        statusDot.classList.remove('active');
                    }
                } catch (e) {}
            }
        }
    } catch (err) {
        term.innerHTML += `<br><div style='color:#ef4444;'>⚠ ERROR: ${err.message}</div>`;
        statusDot.classList.remove('active');
    }
}

//-----------------------------------------------------------------------------------------------
// Verbinde Verformungsanalyse mit Backend
//-----------------------------------------------------------------------------------------------
let lastOptimizedNodes = null;
let isShowingDeformation = false;

async function triggerKinematicAnalysis() {
    const term = document.getElementById('terminal-content');
    if (isShowingDeformation) {
        isShowingDeformation = false;
        if (isShowingResult && lastOptimizedNodes) {
            renderOptimizedStructure(lastOptimizedNodes);
        } else {
            updateCanvas();
        }
        return;
    }
    isShowingDeformation = true;
    term.innerHTML = "<div style='opacity:0.6'>Calculating Deformation...</div>";
    const currentForce = parseFloat(document.getElementById('slider-force').value);
    let activeIndices = [];
    if (isShowingResult && lastOptimizedNodes) {
        lastOptimizedNodes.forEach((n, index) => {
            if (n.active) activeIndices.push(index);
        });
    } else {
        activeIndices = null;
    }

    const payload = {
        width: gridState.nodesX,
        height: gridState.nodesY,
        supports: gridState.supports,
        active_nodes: activeIndices,
        forces: Object.keys(gridState.forces).reduce((acc, key) => {
            acc[key] = { fy: currentForce };
            return acc;
        }, {})
    };

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (result.status === 'done') {
            term.innerHTML += `<br><div style='color:#007aff;'>Fertig.</div>`;
            renderDeformation(result.nodes, result.max_disp);
        } else {
            isShowingDeformation = false;
        }
    } catch (e) {
        isShowingDeformation = false;
    }
}

function renderDeformation(nodes, maxDisp) {
    const { spacing, offsetX, offsetY } = calculateGridMetrics();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const visualScale = (maxDisp > 0) ? (canvas.height * 0.15) / maxDisp : 0;
    function getHeatmapColor(value, max) {
        if (max === 0) return 'hsl(240, 100%, 50%)';
        let percent = value / max;
        let hue = 240 * (1 - percent);
        return `hsl(${hue}, 100%, 50%)`;
    }
    const nodeMap = new Map();
    nodes.forEach(n => nodeMap.set(n.id, n));
    const width = gridState.nodesX;
    ctx.strokeStyle = '#cbd5e1';
    ctx.lineWidth = 1;
    ctx.beginPath();
    nodes.forEach(n => {
        const drawX = offsetX + n.x * spacing + (n.ux * visualScale);
        const drawY = offsetY + n.z * spacing + (n.uz * visualScale);
        if (n.x < width - 1) {
            const rightId = n.id + 1;
            if (nodeMap.has(rightId)) {
                const right = nodeMap.get(rightId);
                const rX = offsetX + right.x * spacing + (right.ux * visualScale);
                const rY = offsetY + right.z * spacing + (right.uz * visualScale);
                ctx.moveTo(drawX, drawY);
                ctx.lineTo(rX, rY);
            }
        }
        const downId = n.id + width;
        if (nodeMap.has(downId)) {
            const down = nodeMap.get(downId);
            const dX = offsetX + down.x * spacing + (down.ux * visualScale);
            const dY = offsetY + down.z * spacing + (down.uz * visualScale);
            ctx.moveTo(drawX, drawY);
            ctx.lineTo(dX, dY);
        }
        if (n.x < width - 1) {
            const diagDRId = n.id + width + 1;
            if (nodeMap.has(diagDRId)) {
                const dDR = nodeMap.get(diagDRId);
                const dDRX = offsetX + dDR.x * spacing + (dDR.ux * visualScale);
                const dDRY = offsetY + dDR.z * spacing + (dDR.uz * visualScale);
                ctx.moveTo(drawX, drawY);
                ctx.lineTo(dDRX, dDRY);
            }
        }
        if (n.x > 0) {
            const diagDLId = n.id + width - 1;
            if (nodeMap.has(diagDLId)) {
                const dDL = nodeMap.get(diagDLId);
                const dDLX = offsetX + dDL.x * spacing + (dDL.ux * visualScale);
                const dDLY = offsetY + dDL.z * spacing + (dDL.uz * visualScale);
                ctx.moveTo(drawX, drawY);
                ctx.lineTo(dDLX, dDLY);
            }
        }
    });
    ctx.stroke();
    nodes.forEach(n => {
        const drawX = offsetX + n.x * spacing + (n.ux * visualScale);
        const drawY = offsetY + n.z * spacing + (n.uz * visualScale);
        ctx.beginPath();
        const radius = 3.5;
        ctx.arc(drawX, drawY, radius, 0, 2 * Math.PI);
        ctx.fillStyle = getHeatmapColor(n.disp, maxDisp);
        ctx.fill();
        const key = `${n.x},${n.z}`;
        if (gridState.supports[key]) drawSymbol(drawX, drawY, gridState.supports[key]);
        if (gridState.forces[key]) drawArrow(drawX, drawY);
    });
}

//-----------------------------------------------------------------------------------------------
// Verbinde Kraftanalyse mit Backend
//-----------------------------------------------------------------------------------------------
let isShowingForces = false;
async function triggerForceAnalysis() {
    const term = document.getElementById('terminal-content');
    if (isShowingForces) {
        isShowingForces = false;
        term.innerHTML += "<div style='opacity:0.6'>Kraftanalyse ausgeblendet.</div>";
        if (isShowingResult && lastOptimizedNodes) {
            renderOptimizedStructure(lastOptimizedNodes);
        } else {
            updateCanvas();
        }
        return;
    }
    isShowingForces = true;
    if (isShowingDeformation) isShowingDeformation = false;
    term.innerHTML = "<div style='opacity:0.6'>Calculating Forces...</div>";
    const currentForce = parseFloat(document.getElementById('slider-force').value);
    let activeIndices = [];
    if (isShowingResult && lastOptimizedNodes) {
        lastOptimizedNodes.forEach((n, index) => {
            if (n.active) activeIndices.push(index);
        });
    } else {
        activeIndices = null;
    }
    const payload = {
        width: gridState.nodesX,
        height: gridState.nodesY,
        supports: gridState.supports,
        active_nodes: activeIndices,
        forces: Object.keys(gridState.forces).reduce((acc, key) => {
            acc[key] = { fy: currentForce };
            return acc;
        }, {})
    };
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (result.status === 'done') {
            term.innerHTML += `<br><div style='color:#f59e0b;'>Kraftanalyse berechnet.</div>`;
            renderForceHeatmap(result.nodes, result.elements);
        } else {
            isShowingForces = false;
        }
    } catch (e) {
        isShowingForces = false;
    }
}

function renderForceHeatmap(nodes, elements) {
    const { spacing, offsetX, offsetY } = calculateGridMetrics();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    let maxForce = 0;
    elements.forEach(el => {
        if (Math.abs(el.force) > maxForce) maxForce = Math.abs(el.force);
    });
    if (maxForce === 0) maxForce = 1;
    const nodeMap = new Map();
    nodes.forEach(n => nodeMap.set(n.id, n));
    elements.forEach(el => {
        const nA = nodeMap.get(el.a);
        const nB = nodeMap.get(el.b);
        if (!nA || !nB) return;
        const x1 = offsetX + nA.x * spacing;
        const y1 = offsetY + nA.z * spacing;
        const x2 = offsetX + nB.x * spacing;
        const y2 = offsetY + nB.z * spacing;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        const force = el.force;
        const intensity = Math.abs(force) / maxForce;
        ctx.lineWidth = 1 + (4 * intensity);
        const alpha = 0.3 + (0.7 * intensity);
        if (force >= 0) {
            ctx.strokeStyle = `rgba(59, 130, 246, ${alpha})`;
        } else {
            ctx.strokeStyle = `rgba(239, 68, 68, ${alpha})`;
        }
        ctx.stroke();
    });
    nodes.forEach(n => {
        const posX = offsetX + n.x * spacing;
        const posY = offsetY + n.z * spacing;
        ctx.beginPath();
        ctx.arc(posX, posY, 3, 0, 2 * Math.PI);
        ctx.fillStyle = '#3b82f6';
        ctx.fill();
        const key = `${n.x},${n.z}`;
        if (gridState.supports[key]) drawSymbol(posX, posY, gridState.supports[key]);
        if (gridState.forces[key]) drawArrow(posX, posY);
    });
}

//-----------------------------------------------------------------------------------------------
// Verbinde Speichern mit Backend
//-----------------------------------------------------------------------------------------------
async function triggerSaveProject() {
    const nameInput = document.getElementById('project-name');
    const name = nameInput.value.trim();
    const term = document.getElementById('terminal-content');

    if (!name) {
        alert("Bitte gib einen Namen ein!");
        return;
    }

    // NEU: Aktive Knoten ermitteln (falls Optimierung lief)
    let activeNodesList = null;
    if (lastOptimizedNodes) {
        activeNodesList = [];
        lastOptimizedNodes.forEach((node, index) => {
            if (node.active) {
                activeNodesList.push(index); // Index entspricht der ID
            }
        });
    }

    const payload = {
        name: name,
        width: gridState.nodesX,
        height: gridState.nodesY,
        supports: gridState.supports,
        forces: gridState.forces,
        active_nodes: activeNodesList // Wird an das Backend gesendet (oder null)
    };

    try {
        const response = await fetch('/api/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (result.status === 'success') {
            term.innerHTML += `<br><div style='color:#10b981;'>💾 ${result.message}</div>`;
            term.scrollTop = term.scrollHeight;
            nameInput.value = "";
            toggleSaveUI(false);
        } else {
            term.innerHTML += `<br><div style='color:#ef4444;'>Fehler: ${result.message}</div>`;
        }

    } catch (e) {
        term.innerHTML += `<br><div style='color:#ef4444;'>Netzwerkfehler</div>`;
    }
}
function toggleSaveUI(showInput) {
    const initialDiv = document.getElementById('save-initial');
    const formDiv = document.getElementById('save-form');

    if (showInput) {
        initialDiv.style.display = 'none';
        formDiv.style.display = 'flex';
        document.getElementById('project-name').focus();
    } else {
        initialDiv.style.display = 'block';
        formDiv.style.display = 'none';
    }
}
async function loadProjectList() {
    const listContainer = document.getElementById('project-list');
    listContainer.innerHTML = "<p>Lade...</p>";

    try {
        const res = await fetch('/api/projects');
        const data = await res.json();

        if (data.status === 'success') {
            listContainer.innerHTML = "";
            if (data.projects.length === 0) {
                listContainer.innerHTML = "<p>Keine gespeicherten Projekte.</p>";
                return;
            }

            data.projects.forEach(proj => {
                const card = document.createElement('div');
                card.className = "glass-card clickable";
                card.style.padding = "10px 15px";
                card.style.minWidth = "150px";
                card.innerHTML = `
                    <strong>${proj.name}</strong><br>
                    <small style='opacity:0.6'>${proj.width}x${proj.height}</small>
                `;
                card.onclick = () => restoreProject(proj);
                listContainer.appendChild(card);
            });
        }
    } catch (e) {
        listContainer.innerHTML = "<p style='color:red'>Fehler beim Laden.</p>";
    }
}

function restoreProject(proj) {
    switchView('static-analysis');

    document.getElementById('slider-width').value = proj.width;
    document.getElementById('slider-height').value = proj.height;
    document.getElementById('val-width').innerText = proj.width;
    document.getElementById('val-height').innerText = proj.height;

    gridState.nodesX = proj.width;
    gridState.nodesY = proj.height;
    gridState.supports = proj.supports;
    gridState.forces = proj.forces;

    if (proj.active_nodes && proj.active_nodes.length > 0) {
        isShowingResult = true;
        lastOptimizedNodes = reconstructNodes(proj.width, proj.height, proj.active_nodes);
        renderOptimizedStructure(lastOptimizedNodes);

        document.getElementById('terminal-content').innerHTML = `Projekt '${proj.name}' (Optimiert) geladen.`;
    } else {
        // Nur Setup laden
        isShowingResult = false;
        lastOptimizedNodes = null;
        updateCanvas();
        document.getElementById('terminal-content').innerHTML = `Projekt-Setup '${proj.name}' geladen.`;
    }
}
function reconstructNodes(w, h, activeIndices) {
    const nodes = [];
    const activeSet = new Set(activeIndices);

    for (let z = 0; z < h; z++) {
        for (let x = 0; x < w; x++) {
            const id = z * w + x;
            nodes.push({
                id: id,
                x: x,
                z: z,
                active: activeSet.has(id),
                ux: 0, uz: 0
            });
        }
    }
    return nodes;
}
function startNewProject() {
    setBaseCase();
    switchView('static-analysis');
}
async function loadAndShowProjects() {
    const btnCard = document.getElementById('btn-open-project');
    const wrapper = document.getElementById('saved-projects-wrapper');
    const listContainer = document.getElementById('project-list');

    // Swap
    btnCard.style.display = 'none';
    wrapper.style.display = 'block';

    listContainer.innerHTML = "<p style='font-size:0.9em; opacity:0.6; padding:10px;'>Lade...</p>";

    try {
        const res = await fetch('/api/projects');
        const data = await res.json();
        listContainer.innerHTML = "";

        if (data.status === 'success') {
            if (data.projects.length === 0) {
                listContainer.innerHTML = "<p style='font-size:0.9em; padding:10px;'>Keine Projekte gefunden.</p>";
                return;
            }

            // Liste sortieren (neueste zuerst)
            data.projects.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

            data.projects.forEach(proj => {
                const item = document.createElement('div');

                // --- STYLING WIE IM SCREENSHOT ---
                item.style.padding = "15px";
                item.style.background = "#f8fafc"; // Helles Weiß/Grau wie im Bild
                item.style.borderRadius = "15px";  // Stärker abgerundet
                item.style.cursor = "pointer";
                item.style.display = "flex";
                item.style.flexDirection = "column";
                item.style.gap = "2px";
                item.style.transition = "transform 0.1s, background 0.1s";

                // Hover Effekt
                item.onmouseenter = () => {
                    item.style.background = "#ffffff";
                    item.style.boxShadow = "0 4px 6px rgba(0,0,0,0.05)";
                };
                item.onmouseleave = () => {
                    item.style.background = "#f8fafc";
                    item.style.boxShadow = "none";
                };

                // Datum formatieren
                const dateObj = new Date(proj.timestamp);
                const dateStr = dateObj.toLocaleDateString('de-DE');

                item.innerHTML = `
                    <div style="font-weight: 700; font-size: 1.1em; color: #f59e0b;">${proj.name}</div>
                    <div style="font-size: 0.85em; color: #64748b;">${proj.width}×${proj.height} Grid</div>
                    <div style="font-size: 0.75em; color: #94a3b8;">${dateStr}</div>
                `;

                item.onclick = () => restoreProject(proj);
                listContainer.appendChild(item);
            });
        }
    } catch (e) {
        listContainer.innerHTML = "<p style='color:red; font-size:0.8em; padding:10px;'>Fehler beim Laden.</p>";
        console.error(e);
    }
}

function hideProjectList() {
    const btnCard = document.getElementById('btn-open-project');
    const wrapper = document.getElementById('saved-projects-wrapper');

    wrapper.style.display = 'none';
    btnCard.style.display = 'flex';
}