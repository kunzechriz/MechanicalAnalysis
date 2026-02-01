const canvas = document.getElementById('structureCanvas');
const ctx = canvas.getContext('2d');
const toolSelect = document.getElementById('tool-select');

// Slider Elemente
const sliderW = document.getElementById('slider-width');
const sliderH = document.getElementById('slider-height');
const sliderMass = document.getElementById('slider-mass');

// Status-Objekt für die Zeichnung
let gridState = {
    supports: {}, // Speichert Lager: "x,y": "fixed"
    forces: {},   // Speichert Kräfte: "x,y": {fy: 1000}
    nodesX: 20,
    nodesY: 10
};

// --- Event Listeners ---

// 1. Navigation Slider (Breite/Höhe) -> Aktualisieren Canvas sofort
sliderW.addEventListener('input', (e) => {
    document.getElementById('val-width').innerText = e.target.value;
    updateCanvas();
});

sliderH.addEventListener('input', (e) => {
    document.getElementById('val-height').innerText = e.target.value;
    updateCanvas();
});

// 2. Masse Slider -> Nur Text Update (wird erst beim Senden relevant)
sliderMass.addEventListener('input', (e) => {
    document.getElementById('val-mass').innerText = e.target.value;
});

// 3. Canvas Interaktion (Klick für Lager/Kräfte)
canvas.addEventListener('mousedown', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    // Grid Geometrie berechnen (muss identisch zu updateCanvas sein)
    const padding = 40;
    const availWidth = canvas.width - (padding * 2);
    const availHeight = canvas.height - (padding * 2);
    
    // Aktuelle Grid-Größe aus den Slidern/State
    const spacingX = availWidth / (gridState.nodesX - 1);
    const spacingY = availHeight / (gridState.nodesY - 1);
    const spacing = Math.min(spacingX, spacingY);
    
    const offsetX = (canvas.width - (gridState.nodesX - 1) * spacing) / 2;
    const offsetY = (canvas.height - (gridState.nodesY - 1) * spacing) / 2;

    // Klick auf den nächsten Knoten mappen
    const xIdx = Math.round((mouseX - offsetX) / spacing);
    const yIdx = Math.round((mouseY - offsetY) / spacing);

    // Prüfen ob Klick gültig ist
    if (xIdx >= 0 && xIdx < gridState.nodesX && yIdx >= 0 && yIdx < gridState.nodesY) {
        applyTool(xIdx, yIdx);
        updateCanvas();
    }
});

// --- Core Funktionen ---

function applyTool(x, y) {
    const key = `${x},${y}`;
    const tool = toolSelect.value;

    if (tool === 'fixed' || tool === 'roller') {
        gridState.supports[key] = tool;
        delete gridState.forces[key]; // Lager ersetzt Kraft
    } else if (tool === 'force') {
        gridState.forces[key] = { fy: 1000 };
        delete gridState.supports[key]; // Kraft ersetzt Lager
    } else if (tool === 'eraser') {
        delete gridState.supports[key];
        delete gridState.forces[key];
    }
}

function updateCanvas() {
    // 1. Aktuelle Werte aus den Slidern holen
    gridState.nodesX = parseInt(sliderW.value);
    gridState.nodesY = parseInt(sliderH.value);

    // 2. Canvas löschen
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 3. Geometrie berechnen
    const padding = 40;
    const availWidth = canvas.width - (padding * 2);
    const availHeight = canvas.height - (padding * 2);
    const spacing = Math.min(
        availWidth / (gridState.nodesX - 1),
        availHeight / (gridState.nodesY - 1)
    );
    const offsetX = (canvas.width - (gridState.nodesX - 1) * spacing) / 2;
    const offsetY = (canvas.height - (gridState.nodesY - 1) * spacing) / 2;

    // 4. Federn (Gitterlinien) zeichnen
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
            // Diagonale
            if (x < gridState.nodesX - 1 && y < gridState.nodesY - 1) {
                ctx.moveTo(posX, posY);
                ctx.lineTo(posX + spacing, posY + spacing);
                ctx.moveTo(posX + spacing, posY);
                ctx.lineTo(posX, posY + spacing);
            }
        }
    }
    ctx.stroke();

    // 5. Knoten und Objekte zeichnen
    for (let x = 0; x < gridState.nodesX; x++) {
        for (let y = 0; y < gridState.nodesY; y++) {
            const posX = offsetX + x * spacing;
            const posY = offsetY + y * spacing;
            const key = `${x},${y}`;

            // Blauer Knoten
            ctx.beginPath();
            ctx.arc(posX, posY, 3, 0, 2 * Math.PI);
            ctx.fillStyle = '#3b82f6';
            ctx.fill();

            // Lager zeichnen (falls vorhanden)
            if (gridState.supports[key]) {
                drawSymbol(posX, posY, gridState.supports[key]);
            }
            // Kraft zeichnen (falls vorhanden)
            if (gridState.forces[key]) {
                drawArrow(posX, posY);
            }
        }
    }
}

// Hilfsfunktion: Lager Symbole
function drawSymbol(x, y, type) {
    ctx.fillStyle = '#ef4444'; // Rot
    ctx.beginPath();
    if (type === 'fixed') {
        // Dreieck
        ctx.moveTo(x, y);
        ctx.lineTo(x - 8, y + 12);
        ctx.lineTo(x + 8, y + 12);
    } else {
        // Kreis (Loslager)
        ctx.arc(x, y + 6, 6, 0, 2*Math.PI);
    }
    ctx.fill();
}

// Hilfsfunktion: Kraft Pfeil
function drawArrow(x, y) {
    ctx.strokeStyle = '#f59e0b'; // Orange
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(x, y - 25);
    ctx.lineTo(x, y);
    ctx.stroke();
    // Spitze
    ctx.beginPath();
    ctx.moveTo(x - 5, y - 8);
    ctx.lineTo(x, y);
    ctx.lineTo(x + 5, y - 8);
    ctx.stroke();
}

// --- View Navigation ---
function switchView(viewName) {
    const dashboard = document.getElementById('dashboard-view');
    const staticView = document.getElementById('static-analysis-view');

    if (viewName === 'static-analysis') {
        dashboard.style.display = 'none';
        staticView.style.display = 'block';
        // Wichtig: Einmal zeichnen, damit man was sieht
        updateCanvas();
    } else {
        dashboard.style.display = 'grid';
        staticView.style.display = 'none';
    }
}
async function triggerPythonSolver() {
    const term = document.getElementById('terminal-content');
    const statusDot = document.getElementById('status-dot');

    // UI Reset
    term.innerHTML = "<div style='opacity:0.6'>System initialized. Waiting for calculation...</div><br>";
    statusDot.classList.add('active');

    // 1. Log Polling starten (alle 500ms)
    const logInterval = setInterval(async () => {
        try {
            const res = await fetch('/api/logs');
            if(res.ok) {
                const data = await res.json();
                if (data.logs && data.logs.trim() !== "") {
                    // Wir formatieren die Logs etwas schöner (jede Zeile ein div)
                    const lines = data.logs.split('\n');
                    lines.forEach(line => {
                        if(line) term.innerHTML += `<div>${line}</div>`;
                    });
                    term.scrollTop = term.scrollHeight;
                }
            }
        } catch(e) { console.log("Log poll error", e); }
    }, 500);

    // 2. Datenpaket senden
    const payload = {
        width: gridState.nodesX,
        height: gridState.nodesY,
        mass_ratio: parseInt(sliderMass.value) / 100,
        supports: gridState.supports,
        forces: gridState.forces
    };

    try {
        const response = await fetch('/api/optimize', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });

        // HIER WAR DER FEHLER: Erst prüfen, ob Server OK sagt (Status 200-299)
        if (!response.ok) {
            // Wenn 500er Fehler, lesen wir den Text, nicht JSON
            throw new Error(`Server Error (${response.status})`);
        }

        const result = await response.json();

        if (result.status === 'done') {
            term.innerHTML += `<br><div style='color:#007aff; font-weight:bold;'>✓ Optimization FINISHED.</div>
                               <div>Final Mass: ${result.final_mass} kg</div>`;
        } else {
            term.innerHTML += `<br><div style='color:#ef4444;'>⚠ Server reported logical failure.</div>`;
        }

    } catch (err) {
        // Fehler wird nun sauber im cleanen Design angezeigt
        term.innerHTML += `<br><div style='color:#ef4444; font-weight:bold;'>⚠ ERROR: ${err.message}</div>`;
        console.error(err);
    } finally {
        clearInterval(logInterval);
        statusDot.classList.remove('active');
    }
}

