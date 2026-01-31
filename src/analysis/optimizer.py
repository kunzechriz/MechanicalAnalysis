import numpy as np


def symmetrize_energies(structure, energies, width):
    height = getattr(structure, 'height', len(structure.nodes) // width)

    for z in range(height):
        for x in range(width // 2 + 1):
            id_left = z * width + x
            id_right = z * width + (width - 1 - x)

            if id_left in energies and id_right in energies:
                avg = (energies[id_left] + energies[id_right]) / 2.0
                energies[id_left] = avg
                energies[id_right] = avg
    return energies


def filter_energies(structure, energies):
    smoothed_energies = energies.copy()

    for node_id, energy in energies.items():
        if not structure.nodes[node_id].active:
            continue

        neighbors = structure.hole_nachbar_indizes(node_id)
        if not neighbors:
            continue

        neighbor_sum = sum(energies.get(nid, 0) for nid in neighbors)
        neighbor_count = len(neighbors)

        smoothed_energies[node_id] = (energy + 0.5 * neighbor_sum) / (1 + 0.5 * neighbor_count)

    return smoothed_energies


def run_optimization(structure, target_mass_ratio=0.4, removal_rate=0.015):
    """
    Führt die Topologieoptimierung mit strikter Symmetrie-Kopplung durch.
    """
    initial_active = [n for n in structure.nodes if n.active]
    start_count = len(initial_active)
    target_count = int(start_count * target_mass_ratio)

    print(f"=== OPTIMIERUNG GESTARTET ===")
    print(f"Startknoten: {start_count} | Zielknoten: {target_count}")
    print("-" * 65)
    print(f"{'Iter':<5} | {'Aktuell':<8} | {'Ziel':<8} | {'Status'}")
    print("-" * 65)

    iteration = 0
    last_count = -1
    stagnation_counter = 0

    history_energies = {}

    while True:
        current_active = [n for n in structure.nodes if n.active]
        current_count = len(current_active)

        # Stagnations-Check
        if current_count == last_count:
            stagnation_counter += 1
        else:
            stagnation_counter = 0
        last_count = current_count

        if current_count <= target_count:
            print("-" * 65)
            print(f"ZIEL ERREICHT: {current_count} Knoten verbleiben.")
            break

        if stagnation_counter >= 5:
            print("-" * 65)
            print(f"ABBRUCH: Optimierung stagniert bei {current_count} Knoten.")
            break

        iteration += 1

        # 1. FEM
        u = structure.loese_system()
        if u is None:
            print("Abbruch: Instabil.")
            break

        # 2. Energie
        raw_energies = structure.berechne_knoten_energien(u)

        # 3. Momentum (Historie)
        current_energies = {}
        for nid, val in raw_energies.items():
            if nid in history_energies:
                current_energies[nid] = 0.6 * val + 0.4 * history_energies[nid]  # Etwas mehr Gewicht auf Aktuelles
            else:
                current_energies[nid] = val
        history_energies = current_energies.copy()

        # 4. Symmetrie & Filter
        if hasattr(structure, 'width'):
            current_energies = symmetrize_energies(structure, current_energies, structure.width)

        current_energies = filter_energies(structure, current_energies)

        # 5. Kandidaten-PAARE bilden (Strict Symmetry Coupling)
        # Wir sammeln keine einzelnen Knoten, sondern Listen von [Links, Rechts]
        candidate_pairs = []
        visited = set()

        width = getattr(structure, 'width', 0)

        for n in current_active:
            if n.id in visited: continue

            # Partner finden
            pair = [n.id]
            if width > 0:
                z = n.id // width
                x = n.id % width
                x_mirror = width - 1 - x
                id_mirror = z * width + x_mirror

                # Wenn es ein Partner existiert und nicht derselbe Knoten ist (Mittelachse)
                if id_mirror != n.id:
                    pair.append(id_mirror)

            # Als besucht markieren
            for pid in pair: visited.add(pid)

            # Prüfen ob das Paar gültig ist (Kein Lager/Last)
            is_valid = True
            for pid in pair:
                # Sicherheitshalber prüfen ob Partner überhaupt existiert/aktiv ist
                if pid >= len(structure.nodes) or not structure.nodes[pid].active:
                    # Sollte bei strikter Symmetrie nicht passieren, aber als Fallback:
                    continue

                node_obj = structure.nodes[pid]
                if any(node_obj.fixed) or (pid in structure.forces):
                    is_valid = False
                    break

            if is_valid:
                # Energie des Paares ist die Energie des ersten Knotens (da symmetrisiert)
                e = current_energies.get(n.id, 0.0)
                candidate_pairs.append((pair, e))

        # Sortieren nach Energie
        candidate_pairs.sort(key=lambda x: x[1])

        # Schrittweite (z.B. entferne 1.5% der Knoten)
        step_size = max(1, int(current_count * removal_rate))
        dist_to_target = current_count - target_count
        step_size = min(step_size, dist_to_target)
        if step_size < 1: step_size = 1

        # 6. Löschen (Gekoppelt)
        removed_nodes_count = 0

        for pair_ids, _ in candidate_pairs:
            # Haben wir genug gelöscht? (Achtung: Ein Paar kann 1 oder 2 Knoten haben)
            if removed_nodes_count >= step_size:
                break

            # 1. Versuchen BEIDE zu löschen
            for pid in pair_ids:
                structure.nodes[pid].active = False

            # 2. Stabilität prüfen
            if structure.check_stability():
                # Erfolg! Beide bleiben gelöscht.
                removed_nodes_count += len(pair_ids)
            else:
                # Fehlschlag! BEIDE wiederherstellen.
                # Wir opfern keinen Zwilling für den anderen -> Symmetrie bleibt erhalten.
                for pid in pair_ids:
                    structure.nodes[pid].active = True

        # Cleanup
        structure.entferne_tote_aeste()

        final_count_in_step = len([n for n in structure.nodes if n.active])
        delta = last_count - final_count_in_step
        print(f"{iteration:<5} | {final_count_in_step:<8} | {target_count:<8} | Delta: {delta:+d}")

    # Post-Processing
    print("Post-Processing: Struktur bereinigen...")
    # Erst Löcher stopfen, dann Äste entfernen -> Sauberes Finish
    structure.fuelle_loecher()
    structure.entferne_tote_aeste()

    final = len([n for n in structure.nodes if n.active])
    print(f"Fertig. Endgültige Knotenanzahl: {final}")

    return structure