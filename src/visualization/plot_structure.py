import matplotlib.pyplot as plt
import numpy as np

def plot_structure(structure, ax=None, element_forces=None):

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))

    if element_forces is None:
        for el in structure.elements:
            if el.node_a.active and el.node_b.active:
                n1 = el.node_a
                n2 = el.node_b
                ax.plot([n1.x, n2.x], [n1.z, n2.z], color='black', linewidth=1, zorder=1, alpha=0.5)
    else:
        max_force = 0
        for entry in element_forces:
            if abs(entry['force']) > max_force:
                max_force = abs(entry['force'])
        if max_force == 0: max_force = 1.0

        node_map = {n.id: n for n in structure.nodes}

        for entry in element_forces:
            n_a = node_map[entry['a']]
            n_b = node_map[entry['b']]
            force = entry['force']

            x_vals = [n_a.x, n_b.x]
            z_vals = [n_a.z, n_b.z]

            color = 'blue' if force >= 0 else 'red'

            linewidth = 0.5 + 4.0 * (abs(force) / max_force)
            alpha = 0.4 + 0.6 * (abs(force) / max_force)

            ax.plot(x_vals, z_vals, color=color, linewidth=linewidth, alpha=alpha, zorder=1)

    x_free, z_free = [], []
    x_fixed, z_fixed = [], []
    x_loose, z_loose = [], []

    for node in structure.nodes:
        if not node.active: continue

        if all(node.fixed):
            x_fixed.append(node.x)
            z_fixed.append(node.z)
        elif any(node.fixed):
            x_loose.append(node.x)
            z_loose.append(node.z)
        else:
            x_free.append(node.x)
            z_free.append(node.z)

    if x_free:
        ax.scatter(x_free, z_free, c='cornflowerblue', s=40, zorder=2, alpha=0.8)
    if x_fixed:
        ax.scatter(x_fixed, z_fixed, c='firebrick', marker='s', s=80, zorder=2, label='Festlager')
    if x_loose:
        ax.scatter(x_loose, z_loose, c='firebrick', marker='^', s=80, zorder=2, label='Loslager')

    ax.set_aspect('equal')
    ax.invert_yaxis()
    ax.grid(True, linestyle=':', alpha=0.3)
    ax.set_xlabel('x [m]')
    ax.set_ylabel('z [m]')

    if element_forces is not None:
        ax.set_title(f"Kraftanalyse: Blau = Zug, Rot = Druck (Max: {max_force:.1f} N)")

    return ax