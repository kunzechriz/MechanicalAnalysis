import io
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import send_file, Blueprint, request

from src.model.structure import Structure2D

report_bp = Blueprint('report', __name__)


@report_bp.route('/api/report', methods=['POST'])
def generate_report():
    data = request.json
    width = data.get('width', 20)
    height = data.get('height', 10)
    active_indices = data.get('active_nodes', None)
    initial_count = data.get('initial_count', width * height)
    supports = data.get('supports', {})
    forces = data.get('forces', {})

    s = Structure2D.create_grid(width, height)

    if active_indices is not None:
        active_set = set(active_indices)
        for n in s.nodes:
            if n.id not in active_set:
                n.active = False
    else:
        active_indices = [n.id for n in s.nodes if n.active]

    for key, stype in supports.items():
        parts = list(map(int, key.split(',')))
        x, z = parts[0], parts[1]
        node_id = z * width + x
        if node_id < len(s.nodes) and s.nodes[node_id].active:
            if stype == 'fixed':
                s.nodes[node_id].fixed = [True, True]
            elif stype == 'roller':
                s.nodes[node_id].fixed = [False, True]

    for key, val in forces.items():
        parts = list(map(int, key.split(',')))
        x, z = parts[0], parts[1]
        fy = float(val.get('fy', 1000))
        node_id = z * width + x
        if node_id < len(s.nodes) and s.nodes[node_id].active:
            s.last_aufbringen(node_id, 0, fy)

    u = s.loese_system()
    stabkraefte = s.berechne_stabkraefte(u) if u is not None else []


    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        f"Topologieoptimierung - Report\nGrid: {width}x{height} | Reduktion: {100 * (1 - len(active_indices) / initial_count):.1f}%",
        fontsize=16)

    def draw_structure(ax, active_list, title, use_displacements=False, element_forces=None, heatmap_nodes=False):
        ax.set_title(title)
        ax.invert_yaxis()
        ax.set_aspect('equal')
        ax.axis('off')
        ax.margins(x=0.1, y=0.2)

        active_set = set(active_list)

        scale = 0
        if use_displacements and u is not None:
            scale =  0.0001
        def get_pos(node_id):
            n = s.nodes[node_id]
            dx = n.displacements[0] * scale if use_displacements else 0.0
            dz = n.displacements[1] * scale if use_displacements else 0.0
            return n.x + dx, n.z + dz

        if element_forces:
            max_force = max([abs(el['force']) for el in element_forces]) if element_forces else 1
            if max_force == 0: max_force = 1
            for el in element_forces:
                xa, za = get_pos(el['a'])
                xb, zb = get_pos(el['b'])
                force = el['force']
                color = '#3b82f6' if force >= 0 else '#ef4444'
                intensity = abs(force) / max_force
                thickness = 1 + 4 * intensity
                alpha = 0.3 + 0.7 * intensity
                ax.plot([xa, xb], [za, zb], color=color, linewidth=thickness, alpha=alpha, zorder=1)
        else:
            for el in s.elements:
                if el.node_a.id in active_set and el.node_b.id in active_set:
                    xa, za = get_pos(el.node_a.id)
                    xb, zb = get_pos(el.node_b.id)
                    ax.plot([xa, xb], [za, zb], color='#cbd5e1', linewidth=1.2, zorder=1)

        xs, zs, heat_vals = [], [], []
        for nid in active_set:
            x, z = get_pos(nid)
            xs.append(x)
            zs.append(z)
            if heatmap_nodes and u is not None:
                n = s.nodes[nid]
                disp = (n.displacements[0] ** 2 + n.displacements[1] ** 2) ** 0.5
                heat_vals.append(disp)

        if xs:
            if heatmap_nodes and u is not None:
                ABSOLUTE_MAX_DISP = 30000.0

                sc = ax.scatter(xs, zs, c=heat_vals, cmap='jet', vmin=0.0, vmax=ABSOLUTE_MAX_DISP, s=25, zorder=2)
            else:
                ax.scatter(xs, zs, c='#3b82f6', s=25, zorder=2)

        for key, stype in supports.items():
            parts = list(map(int, key.split(',')))
            nid = parts[1] * width + parts[0]
            if nid in active_set:
                x, z = get_pos(nid)
                if stype == 'fixed':
                    ax.plot(x, z + 0.5, '^', color='#ef4444', markersize=10, zorder=3)
                elif stype == 'roller':
                    ax.plot(x, z + 0.5, 'o', color='#ef4444', markersize=8, zorder=3)

        for key, val in forces.items():
            parts = list(map(int, key.split(',')))
            nid = parts[1] * width + parts[0]
            if nid in active_set:
                x, z = get_pos(nid)
                ax.annotate('', xy=(x, z - 0.2), xytext=(x, z - 2.0),
                            arrowprops=dict(facecolor='#f59e0b', edgecolor='#f59e0b', width=2, headwidth=8,
                                            headlength=8),
                            zorder=4)


    draw_structure(axs[0, 0], range(initial_count), "1. Ausgangsstruktur")

    draw_structure(axs[0, 1], active_indices, "2. Optimierte Topologie")

    if u is not None:
        draw_structure(axs[1, 0], active_indices, "3. Verformung", use_displacements=True,
                       heatmap_nodes=True)
    else:
        axs[1, 0].set_title("3. Verformung")
        axs[1, 0].text(0.5, 0.5, 'Struktur instabil', ha='center', va='center', color='red')
        axs[1, 0].axis('off')

    if u is not None and stabkraefte:
        draw_structure(axs[1, 1], active_indices, "4. Kraftfluss (Rot=Druck, Blau=Zug)", element_forces=stabkraefte)
    else:
        axs[1, 1].set_title("4. Kraftfluss (Rot=Druck, Blau=Zug)")
        axs[1, 1].text(0.5, 0.5, 'Struktur instabil', ha='center', va='center', color='red')
        axs[1, 1].axis('off')

    plt.tight_layout()
    plt.subplots_adjust(top=0.9)

    buf = io.BytesIO()
    plt.savefig(buf, format='pdf')
    plt.close(fig)
    buf.seek(0)

    return send_file(buf, download_name='Report_Mechanische_Analyse.pdf', as_attachment=True,
                     mimetype='application/pdf')