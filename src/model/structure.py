import numpy as np
from typing import List
from .node import Node
from .element import Element, Spring2D


class Structure:
    def __init__(self):
        self.nodes: List[Node] = []
        self.elements: List[Element] = []

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

    def erstelle_globale_steifigkeitsmatrix(self) -> np.ndarray:
        """
        K_{g_{i,j}} = K_{g_{i,j}} + K_o^{(i,j)}
        """
        n_dof = len(self.nodes) * 2
        k_global = np.zeros((n_dof, n_dof))

        for element in self.elements:
            k_element = element.berechne_transformierte_steifigkeitsmatrix()
            # Indizes für die Positionierung in der globalen Matrix
            indizes = element.node_a.global_dof_indices + element.node_b.global_dof_indices

            for local_row, global_row in enumerate(indizes):
                for local_col, global_col in enumerate(indizes):
                    k_global[global_row, global_col] += k_element[local_row, local_col]

        return k_global

    def erstelle_kraftvektor(self) -> np.ndarray:
        """
        vec{F}
        """
        n_dof = len(self.nodes) * 2
        f_global = np.zeros(n_dof)

        for node in self.nodes:
            for local_i, global_i in enumerate(node.global_dof_indices):
                f_global[global_i] = node.forces[local_i]

        return f_global

    def hole_feste_dof_indizes(self) -> List[int]:
        feste_indizes = []
        for node in self.nodes:
            for local_i, is_fixed in enumerate(node.fixed):
                if is_fixed:
                    global_index = node.global_dof_indices[local_i]
                    feste_indizes.append(global_index)
        return feste_indizes

    def speichere_verschiebungen(self, u: np.ndarray):
        if u is None:
            return
        for node in self.nodes:
            ux = u[node.global_dof_indices[0]]
            uz = u[node.global_dof_indices[1]]
            node.displacements = np.array([ux, uz])

    @classmethod
    def create_grid(cls, width: int, height: int):
        """
        Erstellt einen Balken mit X-Verstrebung und Auflagern unten.
        """
        struct = cls()

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