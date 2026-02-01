from flask import Flask, jsonify, request, render_template
import sys
import io
import time

# Importiere deine Struktur-Klasse
from src.model.structure import Structure

# Falls du die echte Optimierung schon fertig hast, entkommentiere diese Zeile:
# from src.analysis.optimizer import run_optimization

app = Flask(__name__)


# --- Log Capture System ---
class LogCapture(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = io.StringIO()
        return self

    def __exit__(self, *args):
        sys.stdout = self._stdout

    def get_logs(self):
        return self._stringio.getvalue()


global_logs = ""


@app.route('/')
def index():
    """Lädt die Hauptseite (Dashboard)"""
    return render_template('index.html')


@app.route('/api/logs')
def get_logs():
    """Gibt die Logs an das Frontend zurück und leert den Puffer"""
    global global_logs
    logs_to_send = global_logs
    global_logs = ""
    return jsonify({"logs": logs_to_send})


def append_log(text):
    """Hilfsfunktion um Text in den globalen Log-Speicher zu schreiben"""
    global global_logs
    global_logs += text + "\n"
    # Optional: Auch im echten Terminal anzeigen
    print(text)


@app.route('/api/optimize', methods=['POST'])
def optimize():
    data = request.json

    # 1. Parameter auslesen
    width = data.get('width', 20)
    height = data.get('height', 10)
    mass_ratio = data.get('mass_ratio', 0.5)
    supports = data.get('supports', {})
    forces = data.get('forces', {})

    append_log(f"Setup Structure {width}x{height}...")

    # Struktur erstellen
    s = Structure.create_grid(width, height)

    # 2. Lager (Supports) setzen
    for key, type in supports.items():
        x, z = map(int, key.split(','))
        node_id = z * width + x
        if node_id < len(s.nodes):
            if type == 'fixed':
                s.nodes[node_id].fix_dofs([0, 1])
                append_log(f" -> Fixed support at ({x}, {z})")
            elif type == 'roller':
                s.nodes[node_id].fix_dofs([1])
                append_log(f" -> Roller support at ({x}, {z})")

    # 3. Kräfte (Forces) setzen
    for key, val in forces.items():
        x, z = map(int, key.split(','))
        node_id = z * width + x
        fy = val.get('fy', 1000)
        # Richtung beachten: Positive Kraft ist hier oft nach unten definiert (je nach deinem Solver)
        s.last_aufbringen(node_id, 0, fy)
        append_log(f" -> Force {fy}N at ({x}, {z})")

    append_log("Starting Topology Optimization...")

    try:
        # --- HIER DIE ECHTE LOGIK EINFÜGEN ---
        # Aktuell simulieren wir die Berechnung, damit du siehst, dass das Terminal geht.
        # Wenn dein 'run_optimization' funktioniert, ersetze die Schleife unten.

        # run_optimization(s, target_mass_ratio=mass_ratio, removal_rate=0.02)

        # Simulation für das Web-Terminal Feedback:
        for i in range(1, 11):
            time.sleep(0.3)  # Simuliert Rechenzeit
            # Hier würde normalerweise der echte Solver Fehlerwert stehen
            append_log(f"Iteration {i}: Mass reduced to {100 - (i * 5)}%")

        append_log("Optimization finished successfully.")

    except Exception as e:
        append_log(f"ERROR: {str(e)}")
        return jsonify({"status": "error"}), 500

    return jsonify({
        "status": "done",
        "final_mass": round(s.current_mass, 2) if hasattr(s, 'current_mass') else 0
    })


if __name__ == '__main__':
    print("Starting Flask Server...")
    app.run(debug=True, port=5000)