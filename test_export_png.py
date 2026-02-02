import matplotlib.pyplot as plt
import numpy as np
from src.model.structure import Structure
from src.analysis.optimizer import run_optimization

def main():
    # 1. Parameter definieren
    width = 40
    height = 15
    print(f"--- Test-Start: Grid {width}x{height} ---")

    # 2. Struktur erstellen
    s = Structure.create_grid(width, height)

    # 3. Randbedingungen (Lager)
    # Links unten (Festlager)
    idx_fixed = (height - 1) * width
    s.nodes[idx_fixed].fixed = [True, True]
    
    # Rechts unten (Loslager)
    idx_roller = (height - 1) * width + (width - 1)
    s.nodes[idx_roller].fixed = [False, True]

    # 4. Last aufbringen (Mitte oben, nach unten)
    idx_load = width // 2
    load_force = -1000.0
    s.last_aufbringen(idx_load, 0, load_force)

    # 5. Optimierung laufen lassen
    print("Starte Optimierung...")
    # Wir nutzen hier Parameter, die ein gutes Ergebnis liefern sollten
    s = run_optimization(s, target_mass_ratio=0.35, removal_rate=0.02)

    # 6. Analyse für Heatmap (Kräfte berechnen)
    print("Berechne Kräfte für Visualisierung...")
    u = s.loese_system()
    if u is None:
        print("Fehler: System instabil!")
        return

    stabkraefte = s.berechne_stabkraefte(u)
    
    # 7. Plotten mit Matplotlib
    print("Erstelle PNG...")
    plt.figure(figsize=(12, 6))
    
    # Max Kraft für Skalierung der Farben ermitteln
    max_force = 0
    for entry in stabkraefte:
        f_abs = abs(entry['force'])
        if f_abs > max_force: max_force = f_abs
    
    if max_force == 0: max_force = 1.0

    # Mapping ID -> Node Objekt für schnellen Zugriff
    node_map = {n.id: n for n in s.nodes}

    # Elemente zeichnen
    for entry in stabkraefte:
        n_a = node_map[entry['a']]
        n_b = node_map[entry['b']]
        force = entry['force']

        # Koordinaten (Y invertieren, da im Grid z=0 oben ist, im Plot aber y=0 unten sein soll)
        x_vals = [n_a.x, n_b.x]
        y_vals = [-n_a.z, -n_b.z]

        # Farbe: Blau (Zug, >0), Rot (Druck, <0)
        color = 'blue' if force >= 0 else 'red'
        
        # Dicke je nach Last
        linewidth = 0.5 + 2.5 * (abs(force) / max_force)
        # Transparenz damit man Überlagerungen sieht
        alpha = 0.4 + 0.6 * (abs(force) / max_force)

        plt.plot(x_vals, y_vals, color=color, linewidth=linewidth, alpha=alpha)

    # Lager und Last einzeichnen
    plt.plot(s.nodes[idx_fixed].x, -s.nodes[idx_fixed].z, 'ks', markersize=10, label='Festlager')
    plt.plot(s.nodes[idx_roller].x, -s.nodes[idx_roller].z, 'ko', markersize=10, label='Loslager')
    plt.plot(s.nodes[idx_load].x, -s.nodes[idx_load].z, 'mv', markersize=10, label='Last')

    plt.title(f"Optimierungsergebnis (Rot=Zug, Blau=Druck)\nKnoten: {len([n for n in s.nodes if n.active])}")
    plt.axis('equal')
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.3)
    
    filename = "test_ergebnis.png"
    plt.savefig(filename, dpi=150)
    print(f"Fertig! Bild gespeichert unter: {filename}")

if __name__ == "__main__":
    main()