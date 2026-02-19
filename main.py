from flask import Flask, jsonify, request, render_template, Response, stream_with_context
import sys
import json
import cv2
import numpy as np

from src.model.structure import Structure2D, Structure3D
from src.analysis.optimizer import run_optimization
########################################################################################################
#       Initialisiere Flask Server
########################################################################################################
app = Flask(__name__)
@app.route('/')
def index():
    return render_template('index.html')
########################################################################################################
#       Logging to UI
########################################################################################################
class OutputTee(object):
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout

    def write(self, message):
        self.original_stdout.write(message)
        global global_logs
        if "GET /api/logs" not in message:
            global_logs += message

    def flush(self):
        self.original_stdout.flush()


global_logs = ""
if not isinstance(sys.stdout, OutputTee):
    sys.stdout = OutputTee(sys.stdout)


@app.route('/api/logs')
def get_logs():
    global global_logs
    logs_to_send = global_logs
    global_logs = ""
    return jsonify({"logs": logs_to_send})


########################################################################################################
#       Verbinde Optimierung mit UI
########################################################################################################
@app.route('/api/optimize', methods=['POST'])
def optimize():
    try:
        data = request.json
        use_symmetry = data.get('symmetry_enabled', True)
        width = data.get('width', 20)
        height = data.get('height', 10)
        mode = data.get('mode', '2d')
        depth = int(data.get('depth', 1))

        mass_ratio = data.get('mass_ratio', 0.5)
        supports = data.get('supports', {})
        forces = data.get('forces', {})
        removal_rate = data.get('removal_rate', 0.01)

        active_indices = data.get('active_nodes', None)

        if mode == '3d':
            print(f"--> Starte 3D Modus: {width}x{height}x{depth}")
            s = Structure3D.create_grid(width, height, depth)
        else:
            print(f"--> Starte 2D Modus: {width}x{height}")
            s = Structure2D.create_grid(width, height)

        if active_indices is not None:
            print(f"--> Übernehme existierende Topologie ({len(active_indices)} Knoten)")
            active_set = set(active_indices)
            for n in s.nodes:
                if n.id not in active_set:
                    n.active = False

        for key, type in supports.items():
            parts = list(map(int, key.split(',')))
            x, z = parts[0], parts[1]

            if mode == '3d':
                for y in range(depth):
                    node_id = (y * height * width) + (z * width) + x
                    if node_id < len(s.nodes):
                        if type == 'fixed':
                            s.nodes[node_id].fixed = [True, True, True]
                        elif type == 'roller':
                            s.nodes[node_id].fixed = [False, True, False]
            else:
                node_id = z * width + x
                if node_id < len(s.nodes):
                    if type == 'fixed':
                        s.nodes[node_id].fixed = [True, True]
                    elif type == 'roller':
                        s.nodes[node_id].fixed = [False, True]

        for key, val in forces.items():
            parts = list(map(int, key.split(',')))
            x, z = parts[0], parts[1]
            fy = float(val.get('fy', 1000))

            if mode == '3d':
                for y in range(depth):
                    node_id = (y * height * width) + (z * width) + x
                    if node_id < len(s.nodes):
                        s.last_aufbringen(node_id, 0, fy, 0)
            else:
                node_id = z * width + x
                if node_id < len(s.nodes):
                    s.last_aufbringen(node_id, 0, fy)
        def generate():
            gen = run_optimization(s, target_mass_ratio=mass_ratio, removal_rate=removal_rate, use_symmetry=use_symmetry)
            for step_struct, is_done, msg in gen:
                nodes_data = []
                for n in step_struct.nodes:
                    if n.active:
                        nd = {"id": n.id, "x": n.x, "z": n.z, "active": True}
                        if hasattr(n, 'y'): nd['y'] = n.y
                        nodes_data.append(nd)

                resp = {
                    "status": "finished" if is_done else "running",
                    "message": msg,
                    "nodes": nodes_data
                }
                yield json.dumps(resp) + "\n"

        return Response(stream_with_context(generate()), mimetype='application/x-ndjson')

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
########################################################################################################
#       Verformungsanalyse verbinden mit UI
########################################################################################################
@app.route('/api/analyze', methods=['POST'])
def analyze_kinematics():
    try:
        data = request.json
        width = data.get('width', 20)
        height = data.get('height', 10)
        mode = data.get('mode', '2d')
        depth = int(data.get('depth', 1))
        active_indices = data.get('active_nodes', None)

        if mode == '3d':
            s = Structure3D.create_grid(width, height, depth)
        else:
            s = Structure2D.create_grid(width, height)

        if active_indices is not None:
            active_set = set(active_indices)
            for n in s.nodes:
                if n.id not in active_set:
                    n.active = False

        supports = data.get('supports', {})
        forces = data.get('forces', {})

        for key, type in supports.items():
            parts = list(map(int, key.split(',')))
            x, z = parts[0], parts[1]
            if mode == '3d':
                for y in range(depth):
                    node_id = (y * height * width) + (z * width) + x
                    if node_id < len(s.nodes) and s.nodes[node_id].active:
                        if type == 'fixed': s.nodes[node_id].fixed = [True, True, True]
                        elif type == 'roller': s.nodes[node_id].fixed = [False, True, False]
            else:
                node_id = z * width + x
                if node_id < len(s.nodes) and s.nodes[node_id].active:
                    if type == 'fixed': s.nodes[node_id].fixed = [True, True]
                    elif type == 'roller': s.nodes[node_id].fixed = [False, True]

        for key, val in forces.items():
            parts = list(map(int, key.split(',')))
            x, z = parts[0], parts[1]
            fy = float(val.get('fy', 1000))
            if mode == '3d':
                for y in range(depth):
                    node_id = (y * height * width) + (z * width) + x
                    if node_id < len(s.nodes) and s.nodes[node_id].active:
                        s.last_aufbringen(node_id, 0, fy, 0)
            else:
                node_id = z * width + x
                if node_id < len(s.nodes) and s.nodes[node_id].active:
                    s.last_aufbringen(node_id, 0, fy)

        u = s.loese_system()
        if u is None: return jsonify({"status": "error", "message": "Struktur instabil"})
        stabkraefte = s.berechne_stabkraefte(u)
        nodes_data = []
        max_disp = 0.0
        for i, node in enumerate(s.nodes):
            if not node.active: continue
            if mode == '3d':
                ux = u[3 * i]; uz = u[3 * i + 1]; uy = u[3 * i + 2]
                total_disp = (ux**2 + uz**2 + uy**2)**0.5
                nodes_data.append({"id": node.id, "x": node.x, "z": node.z, "y": node.y, "ux": ux, "uz": uz, "uy": uy, "disp": total_disp})
            else:
                ux = u[2 * i]; uz = u[2 * i + 1]
                total_disp = (ux**2 + uz**2)**0.5
                nodes_data.append({"id": node.id, "x": node.x, "z": node.z, "ux": ux, "uz": uz, "disp": total_disp})
            if total_disp > max_disp: max_disp = total_disp

        return jsonify({"status": "done", "max_disp": max_disp, "nodes": nodes_data, "elements": stabkraefte})

    except Exception as e:
        print(f"ANALYZE ERROR: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
########################################################################################################
#       Speicher- und Ladelogik für UI
########################################################################################################
@app.route('/api/save', methods=['POST'])
def save_project():
    try:
        data = request.json
        name = data.get('name')
        if not name:
            return jsonify({"status": "error", "message": "Kein Name angegeben"}), 400

        Structure2D.save_setup_to_db(
            name=name,
            width=data.get('width'),
            height=data.get('height'),
            mode=data.get('mode', '2d'),
            depth=data.get('depth', 1),
            supports=data.get('supports'),
            forces=data.get('forces'),
            active_nodes=data.get('active_nodes')
        )

        return jsonify({"status": "success", "message": f"Projekt '{name}' gespeichert."})

    except Exception as e:
        print(f"SAVE ERROR: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/projects', methods=['GET'])
def get_projects():
    try:
        projects = Structure2D.get_all_projects()
        return jsonify({"status": "success", "projects": projects})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/delete_project', methods=['POST'])
def delete_project():
    try:
        data = request.json
        name = data.get('name')
        if not name:
            return jsonify({"status": "error", "message": "Kein Name angegeben"}), 400

        success = Structure2D.delete_project_from_db(name)

        if success:
            return jsonify({"status": "success", "message": f"Projekt '{name}' gelöscht."})
        else:
            return jsonify({"status": "error", "message": "Projekt nicht gefunden."}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
########################################################################################################
#       Upload Image to UI
########################################################################################################
@app.route('/api/upload_image', methods=['POST'])
def upload_image():
    try:
        file = request.files['image']

        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)

        if img is None:
            return jsonify({"status": "error", "message": "Konnte Bild nicht lesen"}), 400

        h, w = img.shape

        max_dim = 64
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            img_resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        else:
            img_resized = img
            new_w, new_h = w, h

        _, thresh = cv2.threshold(img_resized, 128, 255, cv2.THRESH_BINARY_INV)

        s = Structure2D.create_grid(new_w, new_h)

        nodes_data = []

        for n in s.nodes:
            px_x = int(n.x)
            px_y = int(n.z)

            if 0 <= px_y < new_h and 0 <= px_x < new_w:
                pixel_val = thresh[px_y, px_x]
                n.active = bool(pixel_val > 0)
            else:
                n.active = False

            nodes_data.append({
                "id": n.id,
                "x": n.x,
                "z": n.z,
                "active": n.active,
                "ux": 0, "uz": 0
            })

        return jsonify({
            "status": "success",
            "nodes": nodes_data,
            "width": new_w,
            "height": new_h,
            "message": f"Importiert: {new_w}x{new_h} Knoten"
        })

    except Exception as e:
        print(f"UPLOAD ERROR: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)