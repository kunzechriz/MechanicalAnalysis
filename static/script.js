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
    mode: '2d',
    activeMap: null // NEU: Speichert die importierte Form
};

let isShowingResult = false;

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

canvas.addEventListener('mousedown', (e) => {
    // Wenn wir ein Ergebnis anzeigen, resettet ein Klick alles.
    // Falls wir ein Bild importiert haben (isShowingResult=false, aber activeMap!=null), dürfen wir editieren!
    if (isShowingResult) {
        setBaseCase();
        return;
    }
    handleCanvasClick(e);
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
    gridState.activeMap = null; // Reset der Form

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
    if (gridState.mode === '3d') return;

    const rect = canvas.getBoundingClientRect();
    const { spacing, offsetX, offsetY } = calculateGridMetrics();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const xIdx = Math.round((mouseX - offsetX) / spacing);
    const yIdx = Math.round((mouseY - offsetY) / spacing);

    if (xIdx >= 0 && xIdx < gridState.nodesX && yIdx >= 0 && yIdx < gridState.nodesY) {
        // NEU: Nur klicken erlauben, wenn Knoten existiert (bei Import)
        if (gridState.activeMap && !gridState.activeMap.has(`${xIdx},${yIdx}`)) {
            return;
        }
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

// NEU: updateCanvas respektiert jetzt activeMap
function updateCanvas() {
    const { spacing, offsetX, offsetY } = calculateGridMetrics();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 1;
    ctx.beginPath();

    for (let y = 0; y < gridState.nodesY; y++) {
        for (let x = 0; x < gridState.nodesX; x++) {
            // Nur zeichnen, wenn Knoten aktiv (oder kein Import aktiv ist)
            const exists = !gridState.activeMap || gridState.activeMap.has(`${x},${y}`);
            if (!exists) continue;

            const posX = offsetX + x * spacing;
            const posY = offsetY + y * spacing;

            // Linie rechts
            if (x < gridState.nodesX - 1) {
                const rightExists = !gridState.activeMap || gridState.activeMap.has(`${x+1},${y}`);
                if (rightExists) {
                    ctx.moveTo(posX, posY);
                    ctx.lineTo(posX + spacing, posY);
                }
            }
            // Linie unten
            if (y < gridState.nodesY - 1) {
                const downExists = !gridState.activeMap || gridState.activeMap.has(`${x},${y+1}`);
                if (downExists) {
                    ctx.moveTo(posX, posY);
                    ctx.lineTo(posX, posY + spacing);
                }
            }
            // Diagonalen (optional)
            if (x < gridState.nodesX - 1 && y < gridState.nodesY - 1) {
                const rExists = !gridState.activeMap || gridState.activeMap.has(`${x+1},${y}`);
                const dExists = !gridState.activeMap || gridState.activeMap.has(`${x},${y+1}`);
                const diagExists = !gridState.activeMap || gridState.activeMap.has(`${x+1},${y+1}`);

                if (rExists && dExists && diagExists) {
                    ctx.moveTo(posX, posY);
                    ctx.lineTo(posX + spacing, posY + spacing);
                    ctx.moveTo(posX + spacing, posY);
                    ctx.lineTo(posX, posY + spacing);
                }
            }
        }
    }
    ctx.stroke();

    // Knotenpunkte
    for (let x = 0; x < gridState.nodesX; x++) {
        for (let y = 0; y < gridState.nodesY; y++) {
            const exists = !gridState.activeMap || gridState.activeMap.has(`${x},${y}`);
            if (!exists) continue;

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

// NEU: Hilfsfunktion für ALLE Trigger (Speichern, Optimieren, Analyse)
function getActiveIndices() {
    // Fall 1: Ergebnis wird angezeigt
    if (isShowingResult && lastOptimizedNodes) {
        return lastOptimizedNodes.filter(n => n.active).map(n => n.id);
    }
    // Fall 2: Bild importiert (activeMap vorhanden)
    if (gridState.activeMap) {
        const indices = [];
        const w = gridState.nodesX;
        gridState.activeMap.forEach(key => {
            const [x, y] = key.split(',').map(Number);
            indices.push(y * w + x); // ID Berechnung
        });
        return indices;
    }
    // Fall 3: Standard Rechteck
    return null;
}

//-----------------------------------------------------------------------------------------------
// Verbinde Frontend Struktur mit Backend Optimierung
//-----------------------------------------------------------------------------------------------
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

    term.innerHTML = "<div style='opacity:0.6'>System initialized. Stream started...</div>";
    statusDot.classList.add('active');
    const logInterval = setInterval(async () => {
        try {
            const res = await fetch('/api/logs');
            if(res.ok) {
                const data = await res.json();
                if (data.logs && data.logs.trim() !== "") {
                    const lines = data.logs.split('\n');
                    lines.forEach(line => {
                        if(line) term.innerHTML += `<div>${line}</div>`;
                    });
                    term.scrollTop = term.scrollHeight;
                }
            }
        } catch(e) { }
    }, 500);

    const currentForce = parseFloat(sliderForce.value);
    const qualityRate = parseFloat(document.getElementById('select-quality').value);

    // NEU: Nutze Helper Funktion
    const activeIndices = getActiveIndices();
    if(activeIndices && activeIndices.length > 0) {
        term.innerHTML += `<div style='color:#007aff'>Starte Optimierung auf bestehender Struktur (${activeIndices.length} Knoten)...</div>`;
    }

    const payload = {
        width: gridState.nodesX,
        height: gridState.nodesY,
        depth: gridState.nodesZ,
        mode: gridState.mode,
        mass_ratio: parseInt(sliderMass.value) / 100,
        supports: gridState.supports,
        removal_rate: qualityRate,
        active_nodes: activeIndices, // Sende Import-Daten oder Ergebnis
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
                    if (result.message) {
                        term.innerHTML += `<div>${result.message}</div>`;
                        term.scrollTop = term.scrollHeight;
                    }
                    if (result.nodes) {
                        isShowingResult = true;
                        lastOptimizedNodes = result.nodes;
                        renderOptimizedStructure(result.nodes);
                    }
                    if (result.status === "finished") {
                        statusDot.classList.remove('active');
                    }
                } catch (e) {}
            }
        }
    } catch (err) {
        term.innerHTML += `<br><div style='color:#ef4444;'>⚠ ERROR: ${err.message}</div>`;
        statusDot.classList.remove('active');
    } finally {
        clearInterval(logInterval);
    }
}

function toggleModeUI() {
    const selectMode = document.getElementById('select-mode');
    const mode = selectMode.value;
    const qualitySelect = document.getElementById('select-quality');
    const depthGroup = document.getElementById('group-depth');
    const analysisWrapper = document.getElementById('analysis-buttons-wrapper');
    const canvas2D = document.getElementById('structureCanvas');
    const container3D = document.getElementById('three-container');
    const btnExportSTL = document.getElementById('btn-export-stl');

    if (mode === '3d') {
        gridState.mode = '3d';
        gridState.nodesZ = parseInt(document.getElementById('slider-depth').value);

        depthGroup.style.display = 'block';
        if(analysisWrapper) analysisWrapper.style.display = 'none';
        qualitySelect.value = "0.02";
        canvas2D.style.display = 'none';
        container3D.style.display = 'block';
        if(btnExportSTL) btnExportSTL.style.display = 'block';

        document.getElementById('terminal-content').innerHTML =
            "<div style='color:#007aff'>3D Modus. (Nur Topologieoptimierung möglich)</div>";

    } else {
        gridState.mode = '2d';
        gridState.nodesZ = 1;
        qualitySelect.value = "0.01";
        depthGroup.style.display = 'none';
        if(analysisWrapper) analysisWrapper.style.display = 'block';
        if(btnExportSTL) btnExportSTL.style.display = 'none';

        canvas2D.style.display = 'block';
        container3D.style.display = 'none';
    }
    setBaseCase();
}

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
        const ambientLight = new THREE.AmbientLight(0x404040, 1.5);
        scene3D.add(ambientLight);
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
    threeObjects.supports = [];
    threeObjects.forces = [];

    const activeNodes = nodes.filter(n => n.active !== false);
    if (activeNodes.length === 0) return;

    const offsetX = gridState.nodesX / 2;
    const offsetZ = gridState.nodesY / 2;
    const depth = gridState.nodesZ;
    const offsetY_Depth = depth / 2;

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

    const linePoints = [];
    function checkAndAddLine(n, dx, dz, dy) {
        const nx = n.x + dx;
        const nz = n.z + dz;
        const ny = (n.y || 0) + dy;
        if (activeCoords.has(`${nx},${nz},${ny}`)) {
            linePoints.push(n.x - offsetX, -(n.z - offsetZ), (n.y || 0) - offsetY_Depth);
            linePoints.push(nx - offsetX, -(nz - offsetZ), ny - offsetY_Depth);
        }
    }
    activeNodes.forEach(n => {
        checkAndAddLine(n, 1, 0, 0);
        checkAndAddLine(n, 0, 1, 0);
        checkAndAddLine(n, 0, 0, 1);
        checkAndAddLine(n, 1, 1, 0);
        checkAndAddLine(n, 1, -1, 0);
    });

    if (linePoints.length > 0) {
        const lineGeo = new THREE.BufferGeometry();
        lineGeo.setAttribute('position', new THREE.Float32BufferAttribute(linePoints, 3));
        const lineMat = new THREE.LineBasicMaterial({ color: 0x94a3b8, transparent: true, opacity: 0.4 });
        const lineSegments = new THREE.LineSegments(lineGeo, lineMat);
        scene3D.add(lineSegments);
        threeObjects.lines = lineSegments;
    }

    for (const [key, type] of Object.entries(gridState.supports)) {
        const [gx, gz] = key.split(',').map(Number);
        for (let y = 0; y < depth; y++) {
            const px = gx - offsetX;
            const py = -(gz - offsetZ);
            const pz = y - offsetY_Depth;
            const boxGeo = new THREE.BoxGeometry(0.8, 0.8, 0.8);
            const boxMat = new THREE.MeshLambertMaterial({ color: 0xef4444 });
            const supportMesh = new THREE.Mesh(boxGeo, boxMat);
            supportMesh.position.set(px, py - 0.5, pz);
            scene3D.add(supportMesh);
            threeObjects.supports.push(supportMesh);
        }
    }
    for (const [key, val] of Object.entries(gridState.forces)) {
        const [gx, gz] = key.split(',').map(Number);
        for (let y = 0; y < depth; y++) {
            const px = gx - offsetX;
            const py = -(gz - offsetZ);
            const pz = y - offsetY_Depth;
            const dir = new THREE.Vector3(0, -1, 0);
            const origin = new THREE.Vector3(px, py + 2, pz);
            const length = 2;
            const hex = 0xf59e0b;
            const arrowHelper = new THREE.ArrowHelper(dir, origin, length, hex, 0.5, 0.3);
            scene3D.add(arrowHelper);
            threeObjects.forces.push(arrowHelper);
        }
    }
    if (!renderer3D.loopStarted) {
        renderer3D.loopStarted = true;
        animate3D();
    }
}

function animate3D() {
    requestAnimationFrame(animate3D);
    if(controls3D) controls3D.update();
    if(renderer3D && scene3D && camera3D) renderer3D.render(scene3D, camera3D);
}

//-----------------------------------------------------------------------------------------------
// Analyse
//-----------------------------------------------------------------------------------------------
let isShowingDeformation = false;

async function triggerKinematicAnalysis() {
    const term = document.getElementById('terminal-content');
    if (gridState.mode === '3d') {
        term.innerHTML += "<div style='color:orange'>Verformungsanalyse nur in 2D verfügbar.</div>";
        return;
    }
    if (isShowingDeformation) {
        isShowingDeformation = false;
        if (isShowingResult && lastOptimizedNodes) renderOptimizedStructure(lastOptimizedNodes);
        else updateCanvas();
        return;
    }
    isShowingDeformation = true;
    term.innerHTML = "<div style='opacity:0.6'>Berechne Verformung (2D)...</div>";
    const currentForce = parseFloat(document.getElementById('slider-force').value);

    // NEU: Nutze Helper
    const activeIndices = getActiveIndices();

    const payload = {
        width: gridState.nodesX,
        height: gridState.nodesY,
        mode: '2d',
        depth: 1,
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
            term.innerHTML += `<br><div style='color:#007aff;'>Max. Verformung: ${result.max_disp.toFixed(4)}</div>`;
            term.scrollTop = term.scrollHeight;
            renderDeformation(result.nodes, result.max_disp);
        } else {
            term.innerHTML += `<br><div style='color:#ef4444;'>Fehler: ${result.message}</div>`;
            isShowingDeformation = false;
        }
    } catch (e) {
        console.error(e);
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
    const width = gridState.nodesX;
    const nodeMap = new Map();
    nodes.forEach(n => nodeMap.set(n.id, n));
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

let isShowingForces = false;
async function triggerForceAnalysis() {
    const term = document.getElementById('terminal-content');
    if (gridState.mode === '3d') {
        term.innerHTML += "<div style='color:orange'>Kraftanalyse nur in 2D verfügbar.</div>";
        return;
    }
    if (isShowingForces) {
        isShowingForces = false;
        term.innerHTML += "<div>Kraftanalyse beendet.</div>";
        if (isShowingResult && lastOptimizedNodes) renderOptimizedStructure(lastOptimizedNodes);
        else updateCanvas();
        return;
    }
    isShowingForces = true;
    isShowingDeformation = false;
    term.innerHTML = "<div style='opacity:0.6'>Berechne Kräfte...</div>";
    const currentForce = parseFloat(document.getElementById('slider-force').value);

    // NEU: Nutze Helper
    const activeIndices = getActiveIndices();

    const payload = {
        width: gridState.nodesX,
        height: gridState.nodesY,
        mode: '2d',
        depth: 1,
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
            term.innerHTML += `<br><div style='color:#f59e0b;'>Kraftanalyse berechnet. Rot Druck & Blau Zug</div>`;
            renderForceHeatmap(result.nodes, result.elements);
        } else {
            isShowingForces = false;
        }
    } catch (e) {
        console.error(e);
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
        if (force >= 0) ctx.strokeStyle = `rgba(59, 130, 246, ${alpha})`;
        else ctx.strokeStyle = `rgba(239, 68, 68, ${alpha})`;
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
// Saving & Export
//-----------------------------------------------------------------------------------------------
async function triggerSaveProject() {
    const nameInput = document.getElementById('project-name');
    const name = nameInput.value.trim();
    const term = document.getElementById('terminal-content');

    if (!name) {
        alert("Bitte gib einen Namen ein!");
        return;
    }

    // NEU: Speicher-Logik fixen mit Helper
    const activeNodesList = getActiveIndices();

    const payload = {
        name: name,
        width: gridState.nodesX,
        height: gridState.nodesY,
        mode: gridState.mode,
        depth: gridState.nodesZ,
        supports: gridState.supports,
        forces: gridState.forces,
        active_nodes: activeNodesList
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

function exportCanvasAsPNG() {
    const originalCanvas = document.getElementById('structureCanvas');
    const term = document.getElementById('terminal-content');
    if(gridState.mode === '3d') {
        if(!renderer3D) return;
        const link = document.createElement('a');
        link.download = 'Struktur3D.png';
        renderer3D.render(scene3D, camera3D);
        link.href = renderer3D.domElement.toDataURL("image/png");
        link.click();
        return;
    }
    try {
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = originalCanvas.width;
        tempCanvas.height = originalCanvas.height;
        const tCtx = tempCanvas.getContext('2d');
        tCtx.fillStyle = "#ffffff";
        tCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
        tCtx.drawImage(originalCanvas, 0, 0);
        const nameInput = document.getElementById('project-name');
        let filename = "Struktur";
        if (nameInput && nameInput.value.trim() !== "") filename = nameInput.value.trim();
        else {
            const now = new Date();
            filename = `Struktur_${now.getHours()}-${now.getMinutes()}-${now.getSeconds()}`;
        }
        const link = document.createElement('a');
        link.download = `${filename}.png`;
        link.href = tempCanvas.toDataURL("image/png");
        link.click();
        if (term) {
            term.innerHTML += `<div style='color:#10b981; opacity:0.8;'>Bild gespeichert.</div>`;
            term.scrollTop = term.scrollHeight;
        }
    } catch (e) {
        alert("Fehler beim Speichern.");
    }
}

function exportStructureAsSTL() {
    if (gridState.mode !== '3d') {
        alert("STL Export ist nur im 3D Modus verfügbar.");
        return;
    }
    let nodesToExport = [];
    if (isShowingResult && lastOptimizedNodes) {
        nodesToExport = lastOptimizedNodes.filter(n => n.active);
    } else {
        nodesToExport = generateBase3DNodes();
    }
    if (nodesToExport.length === 0) {
        alert("Keine Struktur zum Exportieren vorhanden.");
        return;
    }
    const exportScene = new THREE.Scene();
    const geometry = new THREE.BoxGeometry(1, 1, 1);
    const material = new THREE.MeshBasicMaterial({ color: 0xffffff });
    const offsetX = gridState.nodesX / 2;
    const offsetZ = gridState.nodesY / 2;
    const depth = gridState.nodesZ;
    const offsetY_Depth = depth / 2;
    nodesToExport.forEach(n => {
        const mesh = new THREE.Mesh(geometry, material);
        const posX = n.x - offsetX;
        const posY = -(n.z - offsetZ);
        const posZ = (n.y || 0) - offsetY_Depth;
        mesh.position.set(posX, posY, posZ);
        mesh.updateMatrixWorld();
        exportScene.add(mesh);
    });
    const exporter = new THREE.STLExporter();
    const result = exporter.parse(exportScene, { binary: true });
    const blob = new Blob([result], { type: 'application/octet-stream' });
    const link = document.createElement('a');
    link.style.display = 'none';
    document.body.appendChild(link);
    const nameInput = document.getElementById('project-name');
    let filename = "Struktur_3D";
    if (nameInput && nameInput.value.trim() !== "") filename = nameInput.value.trim();
    link.href = URL.createObjectURL(blob);
    link.download = `${filename}.stl`;
    link.click();
    document.body.removeChild(link);
}

//-----------------------------------------------------------------------------------------------
// Projekt laden
//-----------------------------------------------------------------------------------------------
async function loadAndShowProjects() {
    const btnCard = document.getElementById('btn-open-project');
    const wrapper = document.getElementById('saved-projects-wrapper');
    const listContainer = document.getElementById('project-list');
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
            data.projects.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            data.projects.forEach(proj => {
                const item = document.createElement('div');
                item.style.padding = "15px";
                item.style.background = "#f8fafc";
                item.style.borderRadius = "15px";
                item.style.cursor = "pointer";
                item.style.display = "flex";
                item.style.flexDirection = "column";
                item.style.gap = "2px";
                item.style.transition = "transform 0.1s, background 0.1s";
                item.onmouseenter = () => { item.style.background = "#ffffff"; item.style.boxShadow = "0 4px 6px rgba(0,0,0,0.05)"; };
                item.onmouseleave = () => { item.style.background = "#f8fafc"; item.style.boxShadow = "none"; };
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
    }
}

function hideProjectList() {
    const btnCard = document.getElementById('btn-open-project');
    const wrapper = document.getElementById('saved-projects-wrapper');
    wrapper.style.display = 'none';
    btnCard.style.display = 'flex';
}

function restoreProject(proj) {
    switchView('static-analysis');
    document.getElementById('slider-width').value = proj.width;
    document.getElementById('slider-height').value = proj.height;
    document.getElementById('val-width').innerText = proj.width;
    document.getElementById('val-height').innerText = proj.height;
    const savedMode = proj.mode || '2d';
    const savedDepth = proj.depth || 1;
    document.getElementById('select-mode').value = savedMode;
    document.getElementById('slider-depth').value = savedDepth;
    document.getElementById('val-depth').innerText = savedDepth;
    gridState.nodesX = proj.width;
    gridState.nodesY = proj.height;
    gridState.nodesZ = savedDepth;
    gridState.mode = savedMode;
    gridState.supports = proj.supports;
    gridState.forces = proj.forces;
    toggleModeUI();
    if (proj.active_nodes && proj.active_nodes.length > 0) {
        isShowingResult = true;
        if (savedMode === '3d') {
             const allNodes = generateBase3DNodes();
             const activeSet = new Set(proj.active_nodes);
             const w = proj.width;
             const h = proj.height;
             allNodes.forEach(n => {
                 const id = (n.y * h * w) + (n.z * w) + n.x;
                 n.id = id;
                 n.active = activeSet.has(id);
             });
             lastOptimizedNodes = allNodes;
             renderOptimizedStructure(allNodes);
        } else {
            lastOptimizedNodes = reconstructNodes(proj.width, proj.height, proj.active_nodes);
            renderOptimizedStructure(lastOptimizedNodes);
        }
        document.getElementById('terminal-content').innerHTML = `Projekt '${proj.name}' (Optimiert) geladen.`;
    } else {
        isShowingResult = false;
        lastOptimizedNodes = null;
        document.getElementById('terminal-content').innerHTML = `Projekt-Setup '${proj.name}' geladen.`;
    }
}

function reconstructNodes(w, h, activeIndices) {
    const nodes = [];
    const activeSet = new Set(activeIndices);
    for (let z = 0; z < h; z++) {
        for (let x = 0; x < w; x++) {
            const currentId = z * w + x;
            nodes.push({
                id: currentId, x: x, z: z, active: activeSet.has(currentId), ux: 0, uz: 0
            });
        }
    }
    return nodes;
}

function startNewProject() {
    setBaseCase();
    switchView('static-analysis');
}

//-----------------------------------------------------------------------------------------------
// Image Upload
//-----------------------------------------------------------------------------------------------
const fileInput = document.getElementById('file-input');
let tempImportData = null;

if (fileInput) {
    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        fileInput.value = '';
        const term = document.getElementById('terminal-content');
        term.innerHTML = "<div style='opacity:0.6'>Analysiere Bild...</div>";
        const formData = new FormData();
        formData.append('image', file);
        try {
            const response = await fetch('/api/upload_image', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            if (result.status === 'success') {
                term.innerHTML += `<div style='color:#10b981;'>${result.message}</div>`;
                tempImportData = { nodes: result.nodes, width: result.width, height: result.height };
                const sizeLabel = document.getElementById('preview-grid-size');
                if(sizeLabel) sizeLabel.innerText = `${result.width}x${result.height}`;
                document.getElementById('preview-modal-overlay').style.display = 'flex';
                drawPreviewCanvas(result.nodes, result.width, result.height);
            } else {
                term.innerHTML += `<div style='color:#ef4444;'>Fehler: ${result.message}</div>`;
                alert("Fehler: " + result.message);
            }
        } catch (err) {
            console.error(err);
            term.innerHTML += `<div style='color:#ef4444;'>Netzwerkfehler.</div>`;
        }
    });
}

function drawPreviewCanvas(nodes, w, h) {
    const pCanvas = document.getElementById('previewCanvas');
    const pCtx = pCanvas.getContext('2d');
    pCanvas.width = 460;
    pCanvas.height = 200;
    pCtx.clearRect(0, 0, pCanvas.width, pCanvas.height);
    const padding = 10;
    const availW = pCanvas.width - padding*2;
    const availH = pCanvas.height - padding*2;
    const spacing = Math.min(availW / w, availH / h);
    const offsetX = (pCanvas.width - (w * spacing)) / 2;
    const offsetY = (pCanvas.height - (h * spacing)) / 2;
    pCtx.beginPath();
    nodes.forEach(n => {
        const posX = offsetX + n.x * spacing;
        const posY = offsetY + n.z * spacing;
        if (n.active) {
            pCtx.moveTo(posX, posY);
            pCtx.arc(posX, posY, Math.max(1.5, spacing * 0.3), 0, 2 * Math.PI);
        }
    });
    pCtx.fillStyle = '#3b82f6';
    pCtx.fill();
}

function cancelUpload() {
    document.getElementById('preview-modal-overlay').style.display = 'none';
    tempImportData = null;
    document.getElementById('terminal-content').innerHTML += "<div>Import abgebrochen.</div>";
}

function confirmUpload() {
    if (!tempImportData) return;
    document.getElementById('preview-modal-overlay').style.display = 'none';

    switchView('static-analysis'); // Reset

    gridState.nodesX = tempImportData.width;
    gridState.nodesY = tempImportData.height;

    // NEU: activeMap setzen für Editor
    gridState.activeMap = new Set();
    tempImportData.nodes.forEach(n => {
        if(n.active) gridState.activeMap.add(`${n.x},${n.z}`);
    });

    const sW = document.getElementById('slider-width');
    const sH = document.getElementById('slider-height');
    if(sW) { sW.value = tempImportData.width; document.getElementById('val-width').innerText = tempImportData.width; }
    if(sH) { sH.value = tempImportData.height; document.getElementById('val-height').innerText = tempImportData.height; }

    isShowingResult = false; // Wir sind im Editier-Modus
    lastOptimizedNodes = tempImportData.nodes;

    updateCanvas(); // Nutzt activeMap
    document.getElementById('terminal-content').innerHTML += `<div style='color:#10b981;'>Geometrie (${gridState.nodesX}x${gridState.nodesY}) übernommen.</div>`;
    tempImportData = null;
}