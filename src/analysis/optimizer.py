import time
########################################################################################################
#       nach Gewichtung symmetrie erzwingen
########################################################################################################
def symmetrize_energies(structure, energies, width):
    height = getattr(structure, 'height', len(structure.nodes) // width)
    limit_x = (width + 1) // 2

    for z in range(height):
        for x in range(limit_x):
            id_left = z * width + x
            id_right = z * width + (width - 1 - x)

            if id_left in energies and id_right in energies:
                avg = (energies[id_left] + energies[id_right]) / 2.0
                energies[id_left] = avg
                energies[id_right] = avg
    return energies


_force_templates_3d = {}
def set_force_templates_3d(structure, force_dict, width, height, depth):
    global _force_templates_3d
    _force_templates_3d = {}

    for key, val in force_dict.items():
        parts = list(map(int, key.split(',')))
        x, z = parts[0], parts[1]
        fy = float(val.get('fy', 1000))
        _force_templates_3d[(x, z)] = fy


def reapply_forces_3d(structure):
    global _force_templates_3d

    structure.forces.clear()

    width = getattr(structure, 'width', 0)
    height = getattr(structure, 'height', 0)
    depth = getattr(structure, 'depth', 1)

    if width == 0 or height == 0:
        return

    for (x, z), fy in _force_templates_3d.items():
        for y in range(depth):
            node_id = (y * height * width) + (z * width) + x
            if node_id < len(structure.nodes) and structure.nodes[node_id].active:
                structure.last_aufbringen(node_id, 0, fy, 0)


########################################################################################################
#       kleines Feder-Energie-Rauschen filtern
########################################################################################################
def filter_energies(structure, energies):
    smoothed_energies = energies.copy()
    neighbor_weight = 0.8

    for node_id, energy in energies.items():
        if not structure.nodes[node_id].active:
            continue

        neighbors = structure.hole_nachbar_indizes(node_id)
        if not neighbors:
            continue

        valid_neighbors = [nid for nid in neighbors if structure.nodes[nid].active]
        if not valid_neighbors:
            continue

        neighbor_sum = sum(energies.get(nid, 0) for nid in valid_neighbors)
        neighbor_count = len(valid_neighbors)

        smoothed_energies[node_id] = (energy + neighbor_weight * neighbor_sum) / (1 + neighbor_weight * neighbor_count)

    return smoothed_energies

########################################################################################################
#       am Ende Struktur verdicken (verschönert und leifert physikalischere Ergebnisse)
########################################################################################################
def verdicke_struktur(structure):
    if getattr(structure, 'depth', 1) > 1:
        return

    width = getattr(structure, 'width', 0)
    if width == 0: return

    height = len(structure.nodes) // width
    active_set = {n.id for n in structure.nodes if n.active}
    nodes_to_activate = set()

    for n in structure.nodes:
        if not n.active: continue

        x, z = n.x, n.z
        idx = n.id

        left = idx - 1
        right = idx + 1
        up = idx - width
        down = idx + width

        has_left = (x > 0) and (left in active_set)
        has_right = (x < width - 1) and (right in active_set)

        if not has_left and not has_right:
            if x < width - 1:
                nodes_to_activate.add(right)

        has_up = (z > 0) and (up in active_set)
        has_down = (z < height - 1) and (down in active_set)

        if not has_up and not has_down:
            if z < height - 1:
                nodes_to_activate.add(down)

    final_activation = set()
    for nid in nodes_to_activate:
        final_activation.add(nid)
        z = nid // width
        x = nid % width
        x_mirror = width - 1 - x
        id_mirror = z * width + x_mirror
        final_activation.add(id_mirror)

    for nid in final_activation:
        if nid < len(structure.nodes):
            structure.nodes[nid].active = True


def run_optimization(structure, target_mass_ratio=0.4, removal_rate=0.01, use_symmetry=True):
    initial_active = [n for n in structure.nodes if n.active]
    start_count = len(initial_active)
    target_count = int(start_count * target_mass_ratio)

    iteration = 0
    last_count = -1
    stagnation_counter = 0

    history_energies = {}
    count_history = []

    while True:
        current_active = [n for n in structure.nodes if n.active]
        current_count = len(current_active)
        total_to_remove = start_count - target_count
        if total_to_remove > 0:
            progress = (start_count - current_count) / total_to_remove
        else:
            progress = 1.0
        progress = max(0.0, min(1.0, progress))

        bar_length = 20
        filled_length = int(round(bar_length * progress))
        bar = 'x' * filled_length + '-' * (bar_length - filled_length)
        status_msg = f"[{bar}] {current_count}/{target_count} Nodes"
        yield structure, False, status_msg
        time.sleep(0.05)

        if current_count <= target_count:
            yield structure, False, f"ZIEL ERREICHT ({current_count}). Starte Nachbearbeitung..."
            break

        if current_count in count_history[-4:]:
            stagnation_counter += 1
        else:
            if current_count < last_count:
                stagnation_counter = 0

        count_history.append(current_count)
        if len(count_history) > 10: count_history.pop(0)

        if stagnation_counter >= 10:
            yield structure, False, "ABBRUCH: Stagnation. Starte Nachbearbeitung..."
            break

        last_count = current_count
        iteration += 1

        structure.entferne_tote_aeste()

        u = structure.loese_system()
        if u is None:
            yield structure, True, "Abbruch: Instabil"
            return

        raw_energies = structure.berechne_knoten_energien(u)

        current_energies = {}
        for nid, val in raw_energies.items():
            if nid in history_energies:
                current_energies[nid] = 0.5 * val + 0.5 * history_energies[nid]
            else:
                current_energies[nid] = val
        history_energies = current_energies.copy()

        if hasattr(structure, 'width') and use_symmetry:
            current_energies = symmetrize_energies(structure, current_energies, structure.width)

        current_energies = filter_energies(structure, current_energies)

        candidate_pairs = []
        visited = set()
        width = getattr(structure, 'width', 0)
        active_nodes_map = {n.id: n for n in structure.nodes if n.active}

        for nid, node in active_nodes_map.items():
            if nid in visited: continue

            pair = [nid]
            if width > 0 and use_symmetry:
                z = nid // width
                x = nid % width
                x_mirror = width - 1 - x
                id_mirror = z * width + x_mirror
                if id_mirror != nid and id_mirror in active_nodes_map:
                    pair.append(id_mirror)

            for pid in pair: visited.add(pid)

            is_valid = True
            for pid in pair:
                n_obj = structure.nodes[pid]
                is_fixed = False
                if hasattr(n_obj, 'fixed') and n_obj.fixed:
                    if any(n_obj.fixed): is_fixed = True
                has_force = False
                if hasattr(structure, 'forces') and pid in structure.forces:
                    has_force = True

                if is_fixed or has_force:
                    is_valid = False
                    break

            if is_valid:
                e = current_energies.get(nid, 0.0)
                candidate_pairs.append((pair, e))

        candidate_pairs.sort(key=lambda x: (x[1], x[0][0]))

        progress = 1.0 - ((current_count - target_count) / (start_count - target_count))
        current_rate = removal_rate if progress < 0.8 else removal_rate * 0.5

        step_size = max(2, int(current_count * current_rate))
        if current_count - step_size < target_count:
            step_size = current_count - target_count
        if step_size < 1: step_size = 1

        removed_count = 0
        to_delete = []
        for pair, _ in candidate_pairs:
            if len(to_delete) < step_size:
                to_delete.append(pair)
            else:
                break

        deleted_history = []
        for pair in to_delete:
            for pid in pair: structure.nodes[pid].active = False
            deleted_history.append(pair)
            removed_count += len(pair)

        if not structure.check_stability():
            for pair in deleted_history:
                for pid in pair: structure.nodes[pid].active = True
            removed_count = 0

            fallback_limit = max(1, step_size // 4)
            for pair, _ in candidate_pairs:
                if removed_count >= fallback_limit: break
                for pid in pair: structure.nodes[pid].active = False

                if structure.check_stability():
                    removed_count += len(pair)
                else:
                    for pid in pair: structure.nodes[pid].active = True

    structure.fuelle_loecher()
    verdicke_struktur(structure)
    structure.fuelle_loecher()
    structure.entferne_tote_aeste()

    final_count = len([n for n in structure.nodes if n.active])
    yield structure, True, f"Fertig"