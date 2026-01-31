import matplotlib.pyplot as plt
from src.model import Structure
from src.visualization import plot_structure


def run_console_test():
    print("--- Topologieoptimierung: Konsolen-Test ---")

    try:
        width = int(input("Bitte Breite eingeben (Anzahl Knoten x): "))
        height = int(input("Bitte Höhe eingeben (Anzahl Knoten z): "))
    except ValueError:
        print("Fehler: Bitte gib nur ganze Zahlen ein!")
        return

    print(f"\nErstelle Gitter mit {width}x{height} Knoten...")
    system = Structure.create_grid(width, height)

    print(f"Erfolg! Das System hat:")
    print(f"- {len(system.nodes)} Knoten (Massenpunkte)")
    print(f"- {len(system.elements)} Elemente (Federn)")

    print("\nÖffne Plot-Fenster...")

    fig, ax = plt.subplots(figsize=(8, 6))

    plot_structure(system, ax=ax)

    ax.set_title(f"Vorschau: {width}x{height} Gitter")

    plt.show()


if __name__ == "__main__":
    run_console_test()