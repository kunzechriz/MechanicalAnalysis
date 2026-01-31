import matplotlib.pyplot as plt


def plot_structure(structure, ax=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 4))

    for el in structure.elements:
        n1 = el.node_a
        n2 = el.node_b

        ax.plot([n1.x, n2.x], [n1.z, n2.z], color='black', linewidth=1, zorder=1, alpha=0.7)

    x_free, z_free = [], []
    x_fixed, z_fixed = [], []

    for node in structure.nodes:

        if any(node.fixed):
            x_fixed.append(node.x)
            z_fixed.append(node.z)
        else:
            x_free.append(node.x)
            z_free.append(node.z)

    if x_free:
        ax.scatter(x_free, z_free, c='cornflowerblue', s=80, zorder=2, label='Masse')

    if x_fixed:
        ax.scatter(x_fixed, z_fixed, c='firebrick', marker='s', s=80, zorder=2, label='Lager')

    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.set_xlabel('x [m]')
    ax.set_ylabel('z [m]')

    ax.invert_yaxis()

    if x_fixed:
        ax.legend(loc='upper right')

    return ax