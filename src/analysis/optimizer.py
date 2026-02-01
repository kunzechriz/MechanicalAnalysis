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

        u = structure.loese_system()
        if u is None:
            print("Abbruch: Instabil.")
            break

        raw_energies = structure.berechne_knoten_energien(u)

        current_energies = {}
        for nid, val in raw_energies.items():
            if nid in history_energies:
                current_energies[nid] = 0.6 * val + 0.4 * history_energies[nid]
            else:
                current_energies[nid] = val
        history_energies = current_energies.copy()

        if hasattr(structure, 'width'):
            current_energies = symmetrize_energies(structure, current_energies, structure.width)

        current_energies = filter_energies(structure, current_energies)


        candidate_pairs = []
        visited = set()

        width = getattr(structure, 'width', 0)

        for n in current_active:
            if n.id in visited: continue

            pair = [n.id]
            if width > 0:
                z = n.id // width
                x = n.id % width
                x_mirror = width - 1 - x
                id_mirror = z * width + x_mirror

                if id_mirror != n.id:
                    pair.append(id_mirror)

            for pid in pair: visited.add(pid)

            is_valid = True
            for pid in pair:
                if pid >= len(structure.nodes) or not structure.nodes[pid].active:
                    continue

                node_obj = structure.nodes[pid]
                if any(node_obj.fixed) or (pid in structure.forces):
                    is_valid = False
                    break

            if is_valid:
                e = current_energies.get(n.id, 0.0)
                candidate_pairs.append((pair, e))

        candidate_pairs.sort(key=lambda x: x[1])

        step_size = max(1, int(current_count * removal_rate))
        dist_to_target = current_count - target_count
        step_size = min(step_size, dist_to_target)
        if step_size < 1: step_size = 1

        removed_nodes_count = 0

        for pair_ids, _ in candidate_pairs:
            if removed_nodes_count >= step_size:
                break

            for pid in pair_ids:
                structure.nodes[pid].active = False

            if structure.check_stability():
                removed_nodes_count += len(pair_ids)
            else:
                for pid in pair_ids:
                    structure.nodes[pid].active = True

        structure.entferne_tote_aeste()

        final_count_in_step = len([n for n in structure.nodes if n.active])
        delta = last_count - final_count_in_step
        print(f"{iteration:<5} | {final_count_in_step:<8} | {target_count:<8} | Delta: {delta:+d}")

    print("Post-Processing: Struktur bereinigen...")
    structure.fuelle_loecher()
    structure.entferne_tote_aeste()

    final = len([n for n in structure.nodes if n.active])
    print(f"Fertig. Endgültige Knotenanzahl: {final}")

    return structure