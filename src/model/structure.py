import numpy as np
from .node import Node
from .element import Element


class Structure:
    """
    Verwaltet das gesamte FE-Modell (Knoten, Elemente, Randbedingungen).
    """

    def __init__(self):
        self.nodes: list[Node] = []
        self.elements: list[Element] = []

    def add_node(self, x: float, z: float, fixed_dofs: list[bool] = None) -> Node:
        """Erstellt einen Knoten und fügt ihn hinzu."""
        pass

    def add_element(self, node_id_a: int, node_id_b: int, stiffness: float = 1.0):
        """Erstellt eine Feder zwischen zwei Knoten."""
        pass

    def assemble_global_stiffness_matrix(self) -> np.ndarray:
        """
        Baut die große Matrix K (Größe: n_dof x n_dof) aus allen Elementen zusammen.
        """
        pass

    def assemble_force_vector(self) -> np.ndarray:
        """Erstellt den Lastvektor F."""
        pass

    def get_fixed_dof_indices(self) -> list[int]:
        """Gibt eine Liste aller Indizes zurück, die fest sind (für den Solver)."""
        pass

    def apply_displacements(self, u: np.ndarray):
        """Speichert die berechneten Verschiebungen zurück in die Knoten."""
        pass