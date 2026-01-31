import matplotlib.pyplot as plt
import numpy as np


def plot_structure(structure, ax=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))

    for el in structure.elements:
        if el.node_a.active and el.node_b.active:
            n1 = el.node_a
            n2 = el.node_b
            ax.plot([n1.x, n2.x], [n1.z, n2.z], color='black', linewidth=1, zorder=1, alpha=0.5)

    x_free, z_free = [], []
    x_fixed, z_fixed = [], []
    x_loose, z_loose = [], []
    x_solid, z_solid = [], []

    for node in structure.nodes:
        if not node.active: continue

        if all(node.fixed):
            x_solid.append(node.x)
            z_solid.append(node.z)
        elif any(node.fixed):
            x_loose.append(node.x)
            z_loose.append(node.z)
        else:
            x_free.append(node.x)
            z_free.append(node.z)

    if x_free:
        ax.scatter(x_free, z_free, c='cornflowerblue', s=50, zorder=2, label='Masse')
    if x_solid:
        ax.scatter(x_solid, z_solid, c='firebrick', marker='s', s=80, zorder=2, label='Festlager')
    if x_loose:
        ax.scatter(x_loose, z_loose, c='firebrick', marker='^', s=80, zorder=2, label='Loslager')

    max_force = 1.0
    if structure.forces:
        all_forces = np.array(list(structure.forces.values()))
        if len(all_forces) > 0:
            max_force = np.max(np.linalg.norm(all_forces, axis=1))
            if max_force == 0: max_force = 1.0

    scale_factor = 1.0

    for node_id, force in structure.forces.items():
        if node_id >= len(structure.nodes):
            continue

        node = structure.nodes[node_id]
        if not node.active: continue

        fx, fz = force

        dx = (fx / max_force) * scale_factor
        dz = (fz / max_force) * scale_factor

        ax.arrow(node.x, node.z, dx, dz,
                 head_width=0.2, head_length=0.3, fc='orange', ec='darkorange',
                 width=0.05, zorder=10)

        ax.text(node.x + dx, node.z + dz, "F", color='darkorange', fontweight='bold')

    ax.set_aspect('equal')
    ax.invert_yaxis()
    ax.grid(True, linestyle=':', alpha=0.3)
    ax.set_xlabel('x [m]')
    ax.set_ylabel('z [m]')

    return ax