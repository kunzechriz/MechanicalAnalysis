import numpy as np
from typing import List
from tinydb import TinyDB, Query
import os
from scipy.sparse import lil_matrix, coo_matrix #lösung für performance auf 3D
from scipy.sparse.linalg import spsolve
from numba import njit

from .node import Node
from .spring import Element, Spring2D, Spring3D
from ..analysis.graph_utils import check_connectivity


########################################################################################################
#       NUMBA JIT OPTIMIERUNGEN (Übersetzt Python in C-Maschinencode)
########################################################################################################
@njit
def build_K_dense_2d(coords, elements, k_vals, active_nodes, n_dofs):
    K = np.zeros((n_dofs, n_dofs), dtype=np.float64)
    for i in range(len(elements)):
        n1 = elements[i, 0]
        n2 = elements[i, 1]

        if not (active_nodes[n1] and active_nodes[n2]):
            continue

        dx = coords[n2, 0] - coords[n1, 0]
        dz = coords[n2, 1] - coords[n1, 1]
        L2 = dx * dx + dz * dz
        if L2 == 0: continue

        L = np.sqrt(L2)
        c = dx / L
        s = dz / L
        k = k_vals[i]

        cc, ss, cs = c * c * k, s * s * k, c * s * k

        # Lokale Steifigkeitsmatrix direkt aufbauen
        Ke = np.array([
            [cc, cs, -cc, -cs],
            [cs, ss, -cs, -ss],
            [-cc, -cs, cc, cs],
            [-cs, -ss, cs, ss]
        ])

        dofs = np.array([n1 * 2, n1 * 2 + 1, n2 * 2, n2 * 2 + 1])
        for r in range(4):
            for c_idx in range(4):
                K[dofs[r], dofs[c_idx]] += Ke[r, c_idx]
    return K


@njit
def calc_energies_2d(coords, elements, k_vals, active_nodes, u_global, num_nodes):
    energies = np.zeros(num_nodes, dtype=np.float64)
    for i in range(len(elements)):
        n1 = elements[i, 0]
        n2 = elements[i, 1]
        if not (active_nodes[n1] and active_nodes[n2]): continue

        dx = coords[n2, 0] - coords[n1, 0]
        dz = coords[n2, 1] - coords[n1, 1]
        L2 = dx * dx + dz * dz
        if L2 == 0: continue

        L = np.sqrt(L2)
        dl = (u_global[n2 * 2] - u_global[n1 * 2]) * (dx / L) + (u_global[n2 * 2 + 1] - u_global[n1 * 2 + 1]) * (dz / L)
        e_val = 0.5 * k_vals[i] * dl * dl

        energies[n1] += e_val / 2.0
        energies[n2] += e_val / 2.0
    return energies


@njit
def build_K_sparse_data_3d(coords, elements, k_vals, active_nodes):
    num_elements = len(elements)
    rows = np.zeros(num_elements * 36, dtype=np.int32)
    cols = np.zeros(num_elements * 36, dtype=np.int32)
    data = np.zeros(num_elements * 36, dtype=np.float64)

    idx = 0
    for i in range(num_elements):
        n1 = elements[i, 0]
        n2 = elements[i, 1]
        if not (active_nodes[n1] and active_nodes[n2]): continue

        dx = coords[n2, 0] - coords[n1, 0]
        dy = coords[n2, 1] - coords[n1, 1]
        dz = coords[n2, 2] - coords[n1, 2]
        L2 = dx * dx + dy * dy + dz * dz
        if L2 == 0: continue

        L = np.sqrt(L2)
        l, m, n = dx / L, dy / L, dz / L
        k = k_vals[i]

        T = np.array([[l * l, l * m, l * n], [m * l, m * m, m * n], [n * l, n * m, n * n]]) * k
        Ke = np.zeros((6, 6), dtype=np.float64)
        Ke[0:3, 0:3] = T
        Ke[3:6, 3:6] = T
        Ke[0:3, 3:6] = -T
        Ke[3:6, 0:3] = -T

        dofs = np.array([n1 * 3, n1 * 3 + 1, n1 * 3 + 2, n2 * 3, n2 * 3 + 1, n2 * 3 + 2])
        for r in range(6):
            for c_idx in range(6):
                rows[idx], cols[idx], data[idx] = dofs[r], dofs[c_idx], Ke[r, c_idx]
                idx += 1
    return rows[:idx], cols[:idx], data[:idx]


@njit
def calc_energies_3d(coords, elements, k_vals, active_nodes, u_global, num_nodes):
    energies = np.zeros(num_nodes, dtype=np.float64)
    for i in range(len(elements)):
        n1 = elements[i, 0]
        n2 = elements[i, 1]
        if not (active_nodes[n1] and active_nodes[n2]): continue

        dx, dy, dz = coords[n2, 0] - coords[n1, 0], coords[n2, 1] - coords[n1, 1], coords[n2, 2] - coords[n1, 2]
        L2 = dx * dx + dy * dy + dz * dz
        if L2 == 0: continue

        L = np.sqrt(L2)
        dl = (u_global[n2 * 3] - u_global[n1 * 3]) * (dx / L) + (u_global[n2 * 3 + 1] - u_global[n1 * 3 + 1]) * (
                    dy / L) + (u_global[n2 * 3 + 2] - u_global[n1 * 3 + 2]) * (dz / L)
        e_val = 0.5 * k_vals[i] * dl * dl

        energies[n1] += e_val / 2.0
        energies[n2] += e_val / 2.0
    return energies
########################################################################################################
#       Baue Struktur aus Knoten und Federn auf
########################################################################################################
class Structure2D:
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
        element.id = len(self.elements)
        self.elements.append(element)

    def last_aufbringen(self, node_id: int, fx: float, fz: float):
        self.forces[node_id] = np.array([fx, fz])

    def erstelle_globale_steifigkeitsmatrix(self) -> np.ndarray:
        n_dof = len(self.nodes) * 2
        # Daten aus Objekten entnehmen
        coords = np.array([[n.x, n.z] for n in self.nodes], dtype=np.float64)
        active_nodes = np.array([n.active for n in self.nodes], dtype=np.bool_)
        elements = np.array([[el.node_a.id, el.node_b.id] for el in self.elements], dtype=np.int32)
        k_vals = np.array([el.k for el in self.elements], dtype=np.float64)

        # Die kompilierte C-Funktion aufrufen
        return build_K_dense_2d(coords, elements, k_vals, active_nodes, n_dof)

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
        coords = np.array([[n.x, n.z] for n in self.nodes], dtype=np.float64)
        active_nodes = np.array([n.active for n in self.nodes], dtype=np.bool_)
        elements = np.array([[el.node_a.id, el.node_b.id] for el in self.elements], dtype=np.int32)
        k_vals = np.array([el.k for el in self.elements], dtype=np.float64)

        energies_arr = calc_energies_2d(coords, elements, k_vals, active_nodes, u_global, len(self.nodes))
        return {n.id: energies_arr[n.id] for n in self.nodes}

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

        return check_connectivity(active_nodes, fixed_nodes, adj)

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
        while True:
            nodes_removed_in_pass = 0

            neighbor_counts = {n.id: 0 for n in self.nodes}
            for el in self.elements:
                if el.node_a.active and el.node_b.active:
                    neighbor_counts[el.node_a.id] += 1
                    neighbor_counts[el.node_b.id] += 1

            for node in self.nodes:
                if not node.active: continue
                if any(node.fixed) or (node.id in self.forces): continue

                if neighbor_counts[node.id] < 2:
                    node.active = False
                    nodes_removed_in_pass += 1

            if nodes_removed_in_pass == 0:
                break

    def fuelle_loecher(self):
        for node in self.nodes:
            if node.active: continue
            if any(node.fixed) or (node.id in self.forces): continue

            alle_nachbarn = self.hole_alle_nachbar_indizes(node.id)
            if not alle_nachbarn: continue

            aktive_nachbarn_count = sum(1 for nid in alle_nachbarn if self.nodes[nid].active)

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

    def berechne_stabkraefte(self, u_global):
        results = []

        for el in self.elements:
            if not (el.node_a.active and el.node_b.active):
                continue
            idx_a = el.node_a.global_dof_indices
            idx_b = el.node_b.global_dof_indices

            ua = u_global[idx_a]  # [ux, uz]
            ub = u_global[idx_b]  # [ux, uz]

            pos_a = np.array([el.node_a.x, el.node_a.z])
            pos_b = np.array([el.node_b.x, el.node_b.z])

            diff = pos_b - pos_a
            length = np.linalg.norm(diff)
            if length == 0: continue
            n = diff / length

            delta_u = ub - ua
            dl = np.dot(delta_u, n)

            if hasattr(el, 'steifigkeit'):
                k = el.steifigkeit
            elif hasattr(el, 'stiffness'):
                k = el.stiffness
            else:
                k = 1.0

            force = k * dl

            results.append({
                'id': el.id,
                'a': el.node_a.id,
                'b': el.node_b.id,
                'force': force
            })

        return results

    @staticmethod
    def save_setup_to_db(name, width, height, supports, forces, active_nodes=None, mode='2d', depth=1, db_filename='projects.json'):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(base_dir, db_filename)

        db = TinyDB(db_path)
        Project = Query()

        entry = {
            'name': name,
            'width': width,
            'height': height,
            'supports': supports,
            'forces': forces,
            'depth': depth,
            'mode': mode,
            'active_nodes': active_nodes,
            'timestamp': str(np.datetime64('now'))
        }

        db.upsert(entry, Project.name == name)

        return f"Projekt '{name}' gespeichert."

    @staticmethod
    def delete_project_from_db(name, db_filename='projects.json'):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(base_dir, db_filename)

        if not os.path.exists(db_path):
            return False

        db = TinyDB(db_path)
        Project = Query()

        deleted_ids = db.remove(Project.name == name)

        return len(deleted_ids) > 0

    @staticmethod
    def get_all_projects(db_filename='projects.json'):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(base_dir, db_filename)

        if not os.path.exists(db_path):
            return []

        db = TinyDB(db_path)
        return db.all()

########################################################################################################
#       Baue Struktur aus Knoten und Federn auf
########################################################################################################
class Structure3D(Structure2D):
    def __init__(self):
        super().__init__()
        self.depth = 1

    def knoten_hinzufuegen(self, x: float, z: float, y: float = 0.0, fixierte_dofs: List[bool] = None) -> Node:
        node_id = len(self.nodes)
        if fixierte_dofs is None:
            fixierte_dofs = [False, False, False]

        neuer_knoten = Node(node_id, [x, z, y])
        neuer_knoten.setze_randbedingung(fixierte_dofs)

        n_dim = 3
        start_index = node_id * n_dim
        neuer_knoten.global_dof_indices = [start_index, start_index + 1, start_index + 2]

        self.nodes.append(neuer_knoten)
        return neuer_knoten

    def element_hinzufuegen(self, node_id_a: int, node_id_b: int, steifigkeit: float = 1.0):
        if not (0 <= node_id_a < len(self.nodes)) or not (0 <= node_id_b < len(self.nodes)):
            raise ValueError("Ungültige Knoten-ID.")

        node_a = self.nodes[node_id_a]
        node_b = self.nodes[node_id_b]

        element = Spring3D(node_a, node_b, steifigkeit)
        element.id = len(self.elements)
        self.elements.append(element)

    def last_aufbringen(self, node_id: int, fx: float, fz: float, fy: float = 0.0):
        self.forces[node_id] = np.array([fx, fz, fy])

    def erstelle_globale_steifigkeitsmatrix(self) -> lil_matrix:
        n_dof = len(self.nodes) * 3
        coords = np.array([[n.x, n.z, getattr(n, 'y', 0.0)] for n in self.nodes], dtype=np.float64)
        active_nodes = np.array([n.active for n in self.nodes], dtype=np.bool_)
        elements = np.array([[el.node_a.id, el.node_b.id] for el in self.elements], dtype=np.int32)
        k_vals = np.array([el.stiffness if hasattr(el, 'stiffness') else 1.0 for el in self.elements], dtype=np.float64)

        rows, cols, data = build_K_sparse_data_3d(coords, elements, k_vals, active_nodes)

        # Matrix sehr schnell über den COO-Format Umweg (SciPy) aufbauen
        k_global = coo_matrix((data, (rows, cols)), shape=(n_dof, n_dof)).tolil()
        return k_global

    def erstelle_kraftvektor(self) -> np.ndarray:
        n_dof = len(self.nodes) * 3
        f_global = np.zeros(n_dof)

        for node_id, force in self.forces.items():
            if self.nodes[node_id].active:
                dofs = self.nodes[node_id].global_dof_indices
                f_global[dofs[0]] += force[0]
                f_global[dofs[1]] += force[1]
                f_global[dofs[2]] += force[2]

        return f_global


    def loese_system(self) -> np.ndarray:
        K = self.erstelle_globale_steifigkeitsmatrix()
        F = self.erstelle_kraftvektor()

        penalty_factor = 1e10

        for node in self.nodes:
            dofs = node.global_dof_indices

            if not node.active:
                for idx in dofs:
                    K[idx, idx] += penalty_factor
                    F[idx] = 0.0
            else:
                for i, is_fixed in enumerate(node.fixed):
                    if is_fixed:
                        idx = dofs[i]
                        K[idx, idx] += penalty_factor
                        F[idx] = 0.0

        try:
            u = spsolve(K, F)
            self.speichere_verschiebungen(u)
            return u
        except Exception:
            return None

    def speichere_verschiebungen(self, u: np.ndarray):
        if u is None:
            return
        for node in self.nodes:
            ux = u[node.global_dof_indices[0]]
            uz = u[node.global_dof_indices[1]]
            uy = u[node.global_dof_indices[2]]
            node.displacements = np.array([ux, uz, uy])
            node.u_x = ux
            node.u_z = uz
            node.u_y = uy

    def berechne_knoten_energien(self, u_global: np.ndarray):
        coords = np.array([[n.x, n.z, getattr(n, 'y', 0.0)] for n in self.nodes], dtype=np.float64)
        active_nodes = np.array([n.active for n in self.nodes], dtype=np.bool_)
        elements = np.array([[el.node_a.id, el.node_b.id] for el in self.elements], dtype=np.int32)
        k_vals = np.array([el.stiffness if hasattr(el, 'stiffness') else 1.0 for el in self.elements], dtype=np.float64)

        energies_arr = calc_energies_3d(coords, elements, k_vals, active_nodes, u_global, len(self.nodes))
        return {n.id: energies_arr[n.id] for n in self.nodes}

    def check_stability(self) -> bool:
        return super().check_stability()

    def hole_nachbar_indizes(self, node_id: int) -> List[int]:
        return super().hole_nachbar_indizes(node_id)

    def hole_alle_nachbar_indizes(self, node_id: int) -> List[int]:
        return super().hole_alle_nachbar_indizes(node_id)

    def entferne_tote_aeste(self):
        super().entferne_tote_aeste()

    def fuelle_loecher(self):
        pass

    @classmethod
    def create_grid(cls, width: int, height: int, depth: int):
        struct = cls()
        struct.width = width
        struct.height = height
        struct.depth = depth

        for y in range(depth):
            for z in range(height):
                for x in range(width):
                    fix = [False, False, False]
                    if z == height - 1:
                        if x == 0:
                            fix = [False, True, False]
                        elif x == width - 1:
                            fix = [True, True, True]

                    struct.knoten_hinzufuegen(float(x), float(z), float(y), fix)

        k_diag = 1.0 / np.sqrt(2)
        k_space = 1.0 / np.sqrt(3)

        for y in range(depth):
            for z in range(height):
                for x in range(width):
                    current_id = (y * height * width) + (z * width) + x

                    if x < width - 1:
                        neighbor_id = current_id + 1
                        struct.element_hinzufuegen(current_id, neighbor_id, 1.0)

                    if z < height - 1:
                        neighbor_id = current_id + width
                        struct.element_hinzufuegen(current_id, neighbor_id, 1.0)

                    if y < depth - 1:
                        neighbor_id = current_id + (width * height)
                        struct.element_hinzufuegen(current_id, neighbor_id, 1.0)

                    if x < width - 1 and z < height - 1:
                        n_br = current_id + width + 1
                        struct.element_hinzufuegen(current_id, n_br, k_diag)
                        n_tr = current_id + 1
                        n_bl = current_id + width
                        struct.element_hinzufuegen(n_tr, n_bl, k_diag)

                    if x < width - 1 and y < depth - 1:
                        n_next_right = current_id + (width * height) + 1
                        struct.element_hinzufuegen(current_id, n_next_right, k_diag)
                        n_curr_right = current_id + 1
                        n_next_curr = current_id + (width * height)
                        struct.element_hinzufuegen(n_curr_right, n_next_curr, k_diag)

                    if z < height - 1 and y < depth - 1:
                        n_next_down = current_id + (width * height) + width
                        struct.element_hinzufuegen(current_id, n_next_down, k_diag)
                        n_curr_down = current_id + width
                        n_next_curr = current_id + (width * height)
                        struct.element_hinzufuegen(n_curr_down, n_next_curr, k_diag)

        return struct