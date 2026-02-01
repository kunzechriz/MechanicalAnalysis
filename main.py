from flask import Flask, jsonify, request, render_template
import sys
import io
import time

from src.model.structure import Structure
from src.analysis.optimizer import run_optimization

app = Flask(__name__)


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
    return render_template('index.html')


@app.route('/api/logs')
def get_logs():
    global global_logs
    logs_to_send = global_logs
    global_logs = ""
    return jsonify({"logs": logs_to_send})


def append_log(text):
    global global_logs
    global_logs += text + "\n"
    print(text)


@app.route('/api/optimize', methods=['POST'])
def optimize():
    try:
        data = request.json
        width = data.get('width', 20)
        height = data.get('height', 10)
        mass_ratio = data.get('mass_ratio', 0.5)
        supports = data.get('supports', {})
        forces = data.get('forces', {})

        append_log(f"Setup Structure {width}x{height}...")

        s = Structure.create_grid(width, height)

        custom_fixed_dofs = []
        for key, type in supports.items():
            x_coord, z_coord = map(int, key.split(','))
            node_id = z_coord * width + x_coord

            if node_id < len(s.nodes):
                if type == 'fixed':
                    custom_fixed_dofs.append(2 * node_id)
                    custom_fixed_dofs.append(2 * node_id + 1)
                    append_log(f" -> Fixed support at Node {node_id}")
                elif type == 'roller':
                    custom_fixed_dofs.append(2 * node_id + 1)
                    append_log(f" -> Roller support at Node {node_id}")

        s.fixed_dofs = custom_fixed_dofs

        for key, val in forces.items():
            x_coord, z_coord = map(int, key.split(','))
            node_id = z_coord * width + x_coord
            fy = float(val.get('fy', 1000))

            if node_id < len(s.nodes):
                if hasattr(s, 'last_aufbringen'):
                    s.last_aufbringen(node_id, 0, fy)
                    append_log(f" -> Force {fy}N at Node {node_id}")

        append_log("Starting Topology Optimization...")


        final_structure = run_optimization(s, target_mass_ratio=mass_ratio)

        append_log("Optimization finished successfully.")


        nodes_data = []
        for n in final_structure.nodes:
            nodes_data.append({
                "x": n.x,
                "z": n.z,
                "active": n.active,
                "u_x": getattr(n, 'u_x', 0.0),
                "u_z": getattr(n, 'u_z', 0.0)
            })

        return jsonify({
            "status": "done",
            "final_mass": round(final_structure.current_mass, 2) if hasattr(final_structure, 'current_mass') else 0,
            "nodes": nodes_data
        })

    except Exception as e:
        error_msg = f"INTERNAL ERROR: {str(e)}"
        print(error_msg)
        append_log(error_msg)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)