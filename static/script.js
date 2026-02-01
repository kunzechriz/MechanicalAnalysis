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
    nodesX: 20,
    nodesY: 10
};

let isShowingResult = false;


sliderW.addEventListener('input', (e) => { document.getElementById('val-width').innerText = e.target.value; resetAnalysis(); });
sliderH.addEventListener('input', (e) => { document.getElementById('val-height').innerText = e.target.value; resetAnalysis(); });
sliderMass.addEventListener('input', (e) => { document.getElementById('val-mass').innerText = e.target.value; });
sliderForce.addEventListener('input', (e) => { document.getElementById('val-force').innerText = e.target.value; });

canvas.addEventListener('mousedown', (e) => {
    if (isShowingResult) {
        resetAnalysis(); 
        return;
    }
    handleCanvasClick(e);
});


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
    gridState.nodesX = parseInt(sliderW.value);
    gridState.nodesY = parseInt(sliderH.value);
    
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
            ctx.fillStyle = '#3b82f6'; // Blau
            ctx.fill();

            if (gridState.supports[key]) drawSymbol(posX, posY, gridState.supports[key]);
            if (gridState.forces[key]) drawArrow(posX, posY);
        }
    }
}

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
    isShowingResult = false;
    const term = document.getElementById('terminal-content');
    const statusDot = document.getElementById('status-dot');
    
    term.innerHTML = "System reset. Ready for new input...";
    statusDot.classList.remove('active');
    
    updateCanvas();
}

function switchView(viewName) {
    const dashboard = document.getElementById('dashboard-view');
    const staticView = document.getElementById('static-analysis-view');

    if (viewName === 'static-analysis') {
        dashboard.style.display = 'none';
        staticView.style.display = 'block';
        updateCanvas();
    } else {
        dashboard.style.display = 'grid';
        staticView.style.display = 'none';
    }
}

async function triggerPythonSolver() {
    const term = document.getElementById('terminal-content');
    const statusDot = document.getElementById('status-dot');
    
    term.innerHTML = "<div style='opacity:0.6'>System initialized. Calculation started...</div><br>";
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

    const payload = {
        width: gridState.nodesX,
        height: gridState.nodesY,
        mass_ratio: parseInt(sliderMass.value) / 100,
        supports: gridState.supports,
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

        if (!response.ok) {
            throw new Error(`Server Error (${response.status})`);
        }

        const result = await response.json();
        
        if (result.status === 'done') {
            term.innerHTML += `<br><div style='color:#007aff; font-weight:bold;'>✓ Optimization FINISHED.</div>
                               <div>Final Mass: ${result.final_mass} kg</div>`;
            
            if (result.nodes) {
                isShowingResult = true;
                renderOptimizedStructure(result.nodes);
            }
        } else {
            term.innerHTML += `<br><div style='color:#ef4444;'>⚠ Server reported logical failure.</div>`;
        }
        
    } catch (err) {
        term.innerHTML += `<br><div style='color:#ef4444; font-weight:bold;'>⚠ ERROR: ${err.message}</div>`;
    } finally {
        clearInterval(logInterval);
        statusDot.classList.remove('active');
    }
}

updateCanvas();