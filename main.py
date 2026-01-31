import matplotlib.pyplot as plt
from src.model.structure import Structure
from src.visualization import plot_structure
from src.analysis.optimizer import run_optimization


def main():
    width = 41
    height = 10

    s = Structure.create_grid(width, height)

    target_x = width // 2
    target_z = 0
    force_node_id = target_z * width + target_x

    if force_node_id >= len(s.nodes):
        force_node_id = 0

    s.last_aufbringen(force_node_id, 0, 1000)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))

    plot_structure(s, ax=ax1)
    ax1.set_title("Vorher")

    run_optimization(s, target_mass_ratio=0.5, removal_rate=0.02)

    plot_structure(s, ax=ax2)
    ax2.set_title("Nachher")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()