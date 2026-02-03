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
const sliderDepth = document.getElementById('slider-depth'); 

let gridState = {
    supports: {},
    forces: {},
    nodesX: 40,
    nodesY: 10,
    nodesZ: 1,
    mode: '2d'
};

let isShowingResult = false;
let draggedElement = null; // Speichert das aktuell gezogene Element { type, data, key }

// Hilfsfunktion: Mausposition in Grid-Indizes umrechnen
function getGridIndices(e) {
    const rect = canvas.getBoundingClientRect();
    const { spacing, offsetX, offsetY } = calculateGridMetrics();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const xIdx = Math.round((mouseX - offsetX) / spacing);
    const yIdx = Math.round((mouseY - offsetY) / spacing);
    return { xIdx, yIdx, mouseX, mouseY };
}

sliderDepth.addEventListener('input', (e) => {
    document.getElementById('val-depth').innerText = e.target.value;
    gridState.nodesZ = parseInt(e.target.value);
    if(gridState.mode === '3d') setBaseCase();
});

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

// --- NEUE DRAG & DROP LOGIK ---
canvas.addEventListener('mousedown', (e) => {
    if (isShowingResult) {
        setBaseCase();
        return;
    }
    
    if (gridState.mode === '3d') return;

    const { xIdx, yIdx } = getGridIndices(e);
    const key = `${xIdx},${yIdx}`;

    // 1. Prüfen, ob wir ein bestehendes Element "greifen"
    if (gridState.supports[key]) {
        draggedElement = { type: 'support', data: gridState.supports[key], key: key };
        delete gridState.supports[key]; 
        updateCanvas();
    } else if (gridState.forces[key]) {
        draggedElement = { type: 'force', data: gridState.forces[key], key: key };
        delete gridState.forces[key];
        updateCanvas();
    } else {
        // 2. Wenn kein Element da ist, normales Tool (Lager/Kraft setzen)
        handleCanvasClick(e);
    }
});

canvas.addEventListener('mousemove', (e) => {
    if (draggedElement) {
        updateCanvas(); // Hintergrund zeichnen
        const { mouseX, mouseY } = getGridIndices(e);
        
        // Temporäre Vorschau an Mausposition
        if (draggedElement.type === 'support') {
            drawSymbol(mouseX, mouseY, draggedElement.data);
        } else {
            drawArrow(mouseX, mouseY);
        }
    }
});

window.addEventListener('mouseup', (e) => {
    if (draggedElement) {
        const { xIdx, yIdx } = getGridIndices(e);
        const newKey = `${xIdx},${yIdx}`;

        // Prüfen, ob innerhalb des Grids losgelassen
        if (xIdx >= 0 && xIdx < gridState.nodesX && yIdx >= 0 && yIdx < gridState.nodesY) {
            if (draggedElement.type === 'support') {
                gridState.supports[newKey] = draggedElement.data;
            } else {
                gridState.forces[newKey] = draggedElement.data;
            }
        } else {
            // Außerhalb losgelassen -> Zurück an Startposition (oder weglassen zum Löschen)
            if (draggedElement.type === 'support') gridState.supports[draggedElement.key] = draggedElement.data;
            else gridState.forces[draggedElement.key] = draggedElement.data;
        }

        draggedElement = null;
        updateCanvas();
    }
});

function setBaseCase() {
    isShowingResult = false;
    lastOptimizedNodes = null;

    const term = document.getElementById('terminal-content');
    const statusDot = document.getElementById('status-dot');

    if(term) term.innerHTML = "System reset. Base case applied.";
    if(statusDot) statusDot.classList.remove('active');

    gridState.nodesX = parseInt(sliderW.value);
    gridState.nodesY = parseInt(sliderH.value);
    gridState.nodesZ = (gridState.mode === '3d') ? parseInt(sliderDepth.value) : 1;

    gridState.supports = {};
    gridState.forces = {};

    const leftBottom = `0,${gridState.nodesY - 1}`;
    gridState.supports[leftBottom] = "roller";
    const rightBottom = `${gridState.nodesX - 1},${gridState.nodesY - 1}`;
    gridState.supports[rightBottom] = "fixed";

    const topMiddleX = Math.floor(gridState.nodesX / 2);
    const topMiddle = `${topMiddleX},0`;
    gridState.forces[topMiddle] = { fy: 1000 };

    if (gridState.mode === '3d') {
        if (!renderer3D) initThreeJS();
        document.getElementById('structureCanvas').style.display = 'none';
        document.getElementById('three-container').style.display = 'block';
        const baseNodes = generateBase3DNodes();
        renderThreeJSScene(baseNodes);
    } else {
        document.getElementById('three-container').style.display = 'none';
        document.getElementById('structureCanvas').style.display = 'block';
        updateCanvas();
    }
}

function generateBase3DNodes() {
    const nodes = [];
    const w = gridState.nodesX;
    const h = gridState.nodesY;
    const d = gridState.nodesZ;

    for(let y = 0; y < d; y++) {
        for(let z = 0; z < h; z++) {
            for(let x = 0; x < w; x++) {
                nodes.push({ x: x, z: z, y: y, active: true });
            }
        }
    }
    return nodes;
}

function handleCanvasClick(e) {
    const { xIdx, yIdx } = getGridIndices(e);
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

// --- RESTLICHE FUNKTIONEN (RENDER, SOLVER, SAVING) ---

function renderOptimizedStructure(nodes) {
    lastOptimizedNodes = nodes;
    if (gridState.mode === '3d') {
        document.getElementById('structureCanvas').style.display = 'none';
        document.getElementById('three-container').style.display = 'block';
        if (!renderer3D) initThreeJS();
        renderThreeJSScene(nodes);
    } else {
        document.getElementById('three-container').style.display = 'none';
        document.getElementById('structureCanvas').style.display = 'block';
        render2DCanvas(nodes);
    }
}

function render2DCanvas(nodes) {
    const { spacing, offsetX, offsetY } = calculateGridMetrics();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const activeMap = new Set();
    nodes.forEach(n => { if(n.active) activeMap.add(`${n.x},${n.z}`); });
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let y = 0; y < gridState.nodesY; y++) {
        for (let x = 0; x < gridState.nodesX; x++) {
            const posX = offsetX + x * spacing;
            const posY = offsetY + y * spacing;
            if (x < gridState.nodesX - 1) {
                if (activeMap.has(`${x},${y}`) && activeMap.has(`${x+1},${y}`)) {
                    ctx.moveTo(posX, posY); ctx.lineTo(posX + spacing, posY);
                }
            }
            if (y < gridState.nodesY - 1) {
                if (activeMap.has(`${x},${y}`) && activeMap.has(`${x},${y+1}`)) {
                    ctx.moveTo(posX, posY); ctx.lineTo(posX, posY + spacing);
                }
            }
            if (x < gridState.nodesX - 1 && y < gridState.nodesY - 1) {
                 if (activeMap.has(`${x},${y}`) && activeMap.has(`${x+1},${y+1}`)) {
                    ctx.moveTo(posX, posY); ctx.lineTo(posX + spacing, posY + spacing);
                }
                if (activeMap.has(`${x+1},${y}`) && activeMap.has(`${x},${y+1}`)) {
                    ctx.moveTo(posX + spacing, posY); ctx.lineTo(posX, posY + spacing);
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

function resetAnalysis() { setBaseCase(); }

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
    term.innerHTML = "<div style='opacity:0.6'>System initialized. Stream started...</div>";
    statusDot.classList.add('active');

    const logInterval = setInterval(async () => {
        try {
            const res = await fetch('/api/logs');
            if(res.ok) {
                const data = await res.json();
                if (data.logs && data.logs.trim() !== "") {
                    const lines = data.logs.split('\n');
                    lines.forEach(line => { if(line) term.innerHTML += `<div>${line}</div>`; });
                    term.scrollTop = term.scrollHeight;
                }
            }
        } catch(e) { }
    }, 500);

    const currentForce = parseFloat(sliderForce.value);
    const qualityRate = parseFloat(document.getElementById('select-quality').value);

    const payload = {
        width: gridState.nodesX, height: gridState.nodesY, depth: gridState.nodesZ,
        mode: gridState.mode, mass_ratio: parseInt(sliderMass.value) / 100,
        supports: gridState.supports, removal_rate: qualityRate,
        forces: Object.keys(gridState.forces).reduce((acc, key) => {
            acc[key] = { fy: currentForce }; return acc;
        }, {})
    };

    try {
        const response = await fetch('/api/optimize', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
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
                    if (result.message) { term.innerHTML += `<div>${result.message}</div>`; term.scrollTop = term.scrollHeight; }
                    if (result.nodes) { isShowingResult = true; lastOptimizedNodes = result.nodes; renderOptimizedStructure(result.nodes); }
                    if (result.status === "finished") { statusDot.classList.remove('active'); }
                } catch (e) {}
            }
        }
    } catch (err) {
        term.innerHTML += `<br><div style='color:#ef4444;'>⚠ ERROR: ${err.message}</div>`;
        statusDot.classList.remove('active');
    } finally { clearInterval(logInterval); }
}

function toggleModeUI() {
    const selectMode = document.getElementById('select-mode');
    const mode = selectMode.value;
    const qualitySelect = document.getElementById('select-quality');
    const depthGroup = document.getElementById('group-depth');
    const analysisWrapper = document.getElementById('analysis-buttons-wrapper');
    const canvas2D = document.getElementById('structureCanvas');
    const container3D = document.getElementById('three-container');

    if (mode === '3d') {
        gridState.mode = '3d';
        gridState.nodesZ = parseInt(document.getElementById('slider-depth').value);
        depthGroup.style.display = 'block';
        if(analysisWrapper) analysisWrapper.style.display = 'none';
        qualitySelect.value = "0.02";
        canvas2D.style.display = 'none';
        container3D.style.display = 'block';
        document.getElementById('terminal-content').innerHTML = "<div style='color:#007aff'>3D Modus.</div>";
    } else {
        gridState.mode = '2d';
        gridState.nodesZ = 1;
        qualitySelect.value = "0.01";
        depthGroup.style.display = 'none';
        if(analysisWrapper) analysisWrapper.style.display = 'block';
        canvas2D.style.display = 'block';
        container3D.style.display = 'none';
    }
    setBaseCase();
}

// --- THREE.JS LOGIK ---
let renderer3D, scene3D, camera3D, controls3D;
let threeObjects = { nodes: null, lines: null, supports: [], forces: [] };

function initThreeJS() {
    const container = document.getElementById('three-container');
    if (!renderer3D) {
        const width = container.clientWidth || 800;
        const height = container.clientHeight || 400;
        scene3D = new THREE.Scene();
        scene3D.background = new THREE.Color(0xffffff);
        camera3D = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        camera3D.position.set(40, 40, 60);
        renderer3D = new THREE.WebGLRenderer({ antialias: true });
        renderer3D.setSize(width, height);
        renderer3D.setPixelRatio(window.devicePixelRatio);
        container.appendChild(renderer3D.domElement);
        controls3D = new THREE.OrbitControls(camera3D, renderer3D.domElement);
        controls3D.enableDamping = true;
        scene3D.add(new THREE.AmbientLight(0x404040, 1.5));
        const dirLight = new THREE.DirectionalLight(0xffffff, 1);
        dirLight.position.set(10, 20, 10);
        scene3D.add(dirLight);
    }
}

function renderThreeJSScene(nodes) {
    if (!scene3D) return;
    if (threeObjects.nodes) scene3D.remove(threeObjects.nodes);
    if (threeObjects.lines) scene3D.remove(threeObjects.lines);
    threeObjects.supports.forEach(o => scene3D.remove(o));
    threeObjects.forces.forEach(o => scene3D.remove(o));
    threeObjects.supports = []; threeObjects.forces = [];

    const activeNodes = nodes.filter(n => n.active !== false);
    if (activeNodes.length === 0) return;

    const offsetX = gridState.nodesX / 2;
    const offsetZ = gridState.nodesY / 2;
    const offsetY_Depth = gridState.nodesZ / 2;

    const sphereGeo = new THREE.SphereGeometry(0.3, 16, 16);
    const sphereMat = new THREE.MeshPhongMaterial({ color: 0x3b82f6 });
    const nodeMesh = new THREE.InstancedMesh(sphereGeo, sphereMat, activeNodes.length);
    const dummy = new THREE.Object3D();
    const activeCoords = new Set();

    activeNodes.forEach((n, i) => {
        const posX = n.x - offsetX;
        const posY = -(n.z - offsetZ);
        const posZ = (n.y || 0) - offsetY_Depth;
        dummy.position.set(posX, posY, posZ);
        dummy.updateMatrix();
        nodeMesh.setMatrixAt(i, dummy.matrix);
        activeCoords.add(`${n.x},${n.z},${n.y || 0}`);
    });
    nodeMesh.instanceMatrix.needsUpdate = true;
    scene3D.add(nodeMesh);
    threeObjects.nodes = nodeMesh;

    // Linien und Symbole in 3D (vereinfacht)
    if (!renderer3D.loopStarted) { renderer3D.loopStarted = true; animate3D(); }
}

function animate3D() {
    requestAnimationFrame(animate3D);
    if(controls3D) controls3D.update();
    if(renderer3D && scene3D && camera3D) renderer3D.render(scene3D, camera3D);
}

// --- ANALYSE & EXPORT (VERKÜRZT) ---
let lastOptimizedNodes = null;
let isShowingDeformation = false;

async function triggerKinematicAnalysis() {
    /* ... (wie im Original) ... */
}

function renderDeformation(nodes, maxDisp) {
    /* ... (wie im Original) ... */
}

async function triggerForceAnalysis() {
    /* ... (wie im Original) ... */
}

function renderForceHeatmap(nodes, elements) {
    /* ... (wie im Original) ... */
}

async function triggerSaveProject() {
    /* ... (wie im Original) ... */
}

function toggleSaveUI(showInput) {
    const initialDiv = document.getElementById('save-initial');
    const formDiv = document.getElementById('save-form');
    if (showInput) { initialDiv.style.display = 'none'; formDiv.style.display = 'flex'; document.getElementById('project-name').focus(); }
    else { initialDiv.style.display = 'block'; formDiv.style.display = 'none'; }
}

function exportCanvasAsPNG() {
    /* ... (wie im Original) ... */
}

async function loadAndShowProjects() {
    /* ... (wie im Original) ... */
}

function hideProjectList() {
    document.getElementById('saved-projects-wrapper').style.display = 'none';
    document.getElementById('btn-open-project').style.display = 'flex';
}

function restoreProject(proj) {
    /* ... (wie im Original) ... */
}

function startNewProject() { setBaseCase(); switchView('static-analysis'); }