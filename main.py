from flask import Flask, jsonify, request, render_template, Response, stream_with_context
import sys
import json

from src.model.structure import Structure
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
        width = data.get('width', 20)
        height = data.get('height', 10)
        mass_ratio = data.get('mass_ratio', 0.5)
        supports = data.get('supports', {})
        forces = data.get('forces', {})
        removal_rate = data.get('removal_rate', 0.01)

        s = Structure.create_grid(width, height)

        custom_fixed_dofs = []
        for key, type in supports.items():
            x_coord, z_coord = map(int, key.split(','))
            node_id = z_coord * width + x_coord
            if node_id < len(s.nodes):
                if type == 'fixed':
                    s.nodes[node_id].fixed = [True, True]
                    custom_fixed_dofs.append(2 * node_id)
                    custom_fixed_dofs.append(2 * node_id + 1)
                elif type == 'roller':
                    s.nodes[node_id].fixed = [False, True]
                    custom_fixed_dofs.append(2 * node_id + 1)
        s.fixed_dofs = custom_fixed_dofs

        for key, val in forces.items():
            x_coord, z_coord = map(int, key.split(','))
            node_id = z_coord * width + x_coord
            fy = float(val.get('fy', 1000))
            if node_id < len(s.nodes):
                if hasattr(s, 'last_aufbringen'):
                    s.last_aufbringen(node_id, 0, fy)

        def generate():
            gen = run_optimization(s, target_mass_ratio=mass_ratio, removal_rate=removal_rate)
            for step_struct, is_done, msg in gen:
                nodes_data = []
                for n in step_struct.nodes:
                    nodes_data.append({
                        "x": n.x, "z": n.z, "active": n.active
                    })

                resp = {
                    "status": "finished" if is_done else "running",
                    "message": msg,
                    "nodes": nodes_data
                }
                yield json.dumps(resp) + "\n"

        return Response(stream_with_context(generate()), mimetype='application/x-ndjson')

    except Exception as e:
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
        supports = data.get('supports', {})
        forces = data.get('forces', {})
        active_indices = data.get('active_nodes', None)

        s = Structure.create_grid(width, height)

        if active_indices is not None:
            active_set = set(active_indices)
            for n in s.nodes:
                if n.id not in active_set:
                    n.active = False

        custom_fixed_dofs = []
        for key, type in supports.items():
            x_coord, z_coord = map(int, key.split(','))
            node_id = z_coord * width + x_coord
            if node_id < len(s.nodes) and s.nodes[node_id].active:
                if type == 'fixed':
                    s.nodes[node_id].fixed = [True, True]
                    custom_fixed_dofs.append(2 * node_id)
                    custom_fixed_dofs.append(2 * node_id + 1)
                elif type == 'roller':
                    s.nodes[node_id].fixed = [False, True]
                    custom_fixed_dofs.append(2 * node_id + 1)
        s.fixed_dofs = custom_fixed_dofs

        for key, val in forces.items():
            x_coord, z_coord = map(int, key.split(','))
            node_id = z_coord * width + x_coord
            fy = float(val.get('fy', 1000))
            if node_id < len(s.nodes) and s.nodes[node_id].active:
                s.last_aufbringen(node_id, 0, fy)

        u = s.loese_system()

        if u is None:
            return jsonify({"status": "error", "message": "Struktur instabil (System singulär)"})

        stabkraefte = s.berechne_stabkraefte(u)

        nodes_data = []
        max_disp = 0.0

        for i, node in enumerate(s.nodes):
            if not node.active:
                continue
            ux = u[2 * i]
            uz = u[2 * i + 1]
            total_disp = (ux ** 2 + uz ** 2) ** 0.5
            if total_disp > max_disp:
                max_disp = total_disp

            nodes_data.append({
                "id": node.id,
                "x": node.x,
                "z": node.z,
                "ux": ux,
                "uz": uz,
                "disp": total_disp
            })

        return jsonify({
            "status": "done",
            "max_disp": max_disp,
            "nodes": nodes_data,
            "elements": stabkraefte
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)