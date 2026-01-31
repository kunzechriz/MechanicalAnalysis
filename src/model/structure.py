import numpy as np
from typing import List
from .node import Node
from .element import Element, Spring2D


class Structure:
    def __init__(self):
        self.nodes: List[Node] = []
        self.elements: List[Element] = []
        self.forces = {}

    def knoten_hinzufuegen(self, x: float, z: float, fixierte_dofs: List[bool] = None) -> Node:
        node_id = len(self.nodes)
        if fixierte_dofs is None:
            fixierte_dofs = [False, False]

        neuer_knoten = Node(node_id, [x, z])
        neuer_knoten.setze_randbedingung(fixierte_dofs)

        n_dim = 2
        start_index = node_id * n_dim
        neuer_knoten.global_dof_indices = [start_index, start_index + 1]

        self.nodes.append(neuer_knoten)
        return neuer_knoten

    def element_hinzufuegen(self, node_id_a: int, node_id_b: int, steifigkeit: float = 1.0):
        if not (0 <= node_id_a < len(self.nodes)) or not (0 <= node_id_b < len(self.nodes)):
            raise ValueError("Ungültige Knoten-ID.")

        node_a = self.nodes[node_id_a]
        node_b = self.nodes[node_id_b]

        element = Spring2D(node_a, node_b, steifigkeit)
        self.elements.append(element)

    def last_aufbringen(self, node_id: int, fx: float, fz: float):
        self.forces[node_id] = np.array([fx, fz])

    def erstelle_globale_steifigkeitsmatrix(self) -> np.ndarray:
        n_dof = len(self.nodes) * 2
        k_global = np.zeros((n_dof, n_dof))

        for element in self.elements:
            if element.node_a.active and element.node_b.active:
                k_element = element.berechne_transformierte_steifigkeitsmatrix()
                indizes = element.node_a.global_dof_indices + element.node_b.global_dof_indices

                for local_row, global_row in enumerate(indizes):
                    for local_col, global_col in enumerate(indizes):
                        k_global[global_row, global_col] += k_element[local_row, local_col]

        return k_global

    def erstelle_kraftvektor(self) -> np.ndarray:
        n_dof = len(self.nodes) * 2
        f_global = np.zeros(n_dof)

        for node_id, force in self.forces.items():
            if self.nodes[node_id].active:
                dofs = self.nodes[node_id].global_dof_indices
                f_global[dofs[0]] += force[0]
                f_global[dofs[1]] += force[1]

        return f_global

    def loese_system(self) -> np.ndarray:
        K = self.erstelle_globale_steifigkeitsmatrix()
        F = self.erstelle_kraftvektor()

        for node in self.nodes:
            dofs = node.global_dof_indices

            if not node.active:
                for idx in dofs:
                    K[idx, :] = 0.0
                    K[:, idx] = 0.0
                    K[idx, idx] = 1.0
                    F[idx] = 0.0
                continue

            for i, is_fixed in enumerate(node.fixed):
                if is_fixed:
                    idx = dofs[i]
                    K[idx, :] = 0.0
                    K[:, idx] = 0.0
                    K[idx, idx] = 1.0
                    F[idx] = 0.0

        try:
            u = np.linalg.solve(K, F)
        except np.linalg.LinAlgError:
            u, _, _, _ = np.linalg.lstsq(K, F, rcond=None)

        self.speichere_verschiebungen(u)
        return u

    def berechne_knoten_energien(self, u_global: np.ndarray):
        energien = {n.id: 0.0 for n in self.nodes}

        for element in self.elements:
            if element.node_a.active and element.node_b.active:
                e_val = element.berechne_verformungsenergie(u_global)
                energien[element.node_a.id] += e_val / 2.0
                energien[element.node_b.id] += e_val / 2.0
        return energien

    def check_stability(self) -> bool:
        active_nodes = [n for n in self.nodes if n.active]
        if not active_nodes:
            return False

        fixed_nodes = [n for n in active_nodes if any(n.fixed)]
        if not fixed_nodes:
            return False

        adj = {n.id: [] for n in active_nodes}
        for el in self.elements:
            if el.node_a.active and el.node_b.active:
                adj[el.node_a.id].append(el.node_b.id)
                adj[el.node_b.id].append(el.node_a.id)

        visited = set()
        queue = [n.id for n in fixed_nodes]
        for start in queue:
            visited.add(start)

        idx = 0
        while idx < len(queue):
            curr = queue[idx]
            idx += 1
            for neighbor in adj[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return len(visited) == len(active_nodes)

    def speichere_verschiebungen(self, u: np.ndarray):
        if u is None:
            return
        for node in self.nodes:
            ux = u[node.global_dof_indices[0]]
            uz = u[node.global_dof_indices[1]]
            node.displacements = np.array([ux, uz])

    def hole_nachbar_indizes(self, node_id: int) -> List[int]:
        nachbarn = []
        for el in self.elements:
            if not (el.node_a.active and el.node_b.active):
                continue

            if el.node_a.id == node_id:
                nachbarn.append(el.node_b.id)
            elif el.node_b.id == node_id:
                nachbarn.append(el.node_a.id)
        return nachbarn

    def hole_alle_nachbar_indizes(self, node_id: int) -> List[int]:
        nachbarn = []
        for el in self.elements:
            if el.node_a.id == node_id:
                nachbarn.append(el.node_b.id)
            elif el.node_b.id == node_id:
                nachbarn.append(el.node_a.id)
        return nachbarn

    def entferne_tote_aeste(self):
        """
        Löscht REKURSIV alle Knoten, die weniger als 2 Nachbarn haben.
        Macht solange weiter, bis das Gitter 'sauber' ist.
        """
        while True:
            nodes_removed_in_pass = 0

            # 1. Nachbarn zählen (frisch für diesen Durchlauf)
            neighbor_counts = {n.id: 0 for n in self.nodes}
            for el in self.elements:
                if el.node_a.active and el.node_b.active:
                    neighbor_counts[el.node_a.id] += 1
                    neighbor_counts[el.node_b.id] += 1

            # 2. Löschen
            for node in self.nodes:
                if not node.active: continue
                # Lager und Lasten schützen
                if any(node.fixed) or (node.id in self.forces): continue

                # Wenn < 2 Nachbarn -> Weg damit
                if neighbor_counts[node.id] < 2:
                    node.active = False
                    nodes_removed_in_pass += 1

            # Wenn in diesem Durchlauf nichts gelöscht wurde, sind wir fertig
            if nodes_removed_in_pass == 0:
                break

    def fuelle_loecher(self):
        """Reaktiviert Knoten, die von aktiven Knoten umzingelt sind."""
        # Dies ist eine rein geometrische Operation
        for node in self.nodes:
            if node.active: continue
            if any(node.fixed) or (node.id in self.forces): continue

            alle_nachbarn = self.hole_alle_nachbar_indizes(node.id)
            if not alle_nachbarn: continue

            aktive_nachbarn_count = sum(1 for nid in alle_nachbarn if self.nodes[nid].active)

            # Gitter mit Diagonalen hat max 8 Nachbarn.
            # Wenn >= 5 aktiv sind, ist es sehr wahrscheinlich ein ungewolltes Loch.
            if aktive_nachbarn_count >= 5:
                node.active = True

    @classmethod
    def create_grid(cls, width: int, height: int):
        struct = cls()
        struct.width = width
        struct.height = height

        for z in range(height):
            for x in range(width):
                fix = [False, False]

                if z == height - 1:
                    if x == 0:
                        fix = [False, True]
                    elif x == width - 1:
                        fix = [True, True]

                struct.knoten_hinzufuegen(float(x), float(z), fix)

        k_diag = 1.0 / np.sqrt(2)

        for z in range(height):
            for x in range(width):
                current_id = z * width + x

                if x < width - 1:
                    right_id = z * width + (x + 1)
                    struct.element_hinzufuegen(current_id, right_id, steifigkeit=1.0)

                if z < height - 1:
                    down_id = (z + 1) * width + x
                    struct.element_hinzufuegen(current_id, down_id, steifigkeit=1.0)

                if x < width - 1 and z < height - 1:
                    bottom_right_id = (z + 1) * width + (x + 1)
                    struct.element_hinzufuegen(current_id, bottom_right_id, steifigkeit=k_diag)

                    top_right_id = z * width + (x + 1)
                    bottom_left_id = (z + 1) * width + x
                    struct.element_hinzufuegen(top_right_id, bottom_left_id, steifigkeit=k_diag)

        return struct