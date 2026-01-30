import numpy as np
from typing import List, Optional


class Node:
    """
    Repräsentiert einen Massenpunkt im System.

    Attribute:
        id (int): Eindeutige Identifikationsnummer.
        coords (np.ndarray): Koordinatenvektor [x, z] (2D) oder [x, y, z] (3D).
        active (bool): Status für Topologieoptimierung. False bedeutet 'entfernt'.
        mass (float): Masse des Knotens (Standard: 1.0 kg laut Aufgabenstellung).
    """

    def __init__(self, node_id: int, coords: List[float], mass: float = 1.0):
        """
        Initialisiert einen Knoten.

        Args:
            node_id: ID des Knotens.
            coords: Liste der Koordinaten, z.B. [0.0, 1.0].
            mass: Masse in kg.
        """
        self.id = node_id
        self.coords = np.array(coords, dtype=np.float64)
        self.mass = mass

        # Automatische Erkennung der Dimension (2 für 2D, 3 für 3D)
        self.dim = len(coords)

        # Status: Ist der Knoten noch Teil der Struktur?
        self.active = True

        # Kräfte: Vektor der externen Lasten (initially zero)
        # [Fx, Fz] in 2D
        self.forces = np.zeros(self.dim, dtype=np.float64)

        # Randbedingungen: True = fest, False = frei
        # [FestX, FestZ] in 2D
        self.fixed = [False] * self.dim

        # Solver-Mapping: Wo sitzen meine Freiheitsgrade in der globalen Matrix?
        # Wird später von der Structure-Klasse befüllt (z.B. [0, 1] für Knoten 0)
        self.global_dof_indices: List[int] = []

    def set_force(self, force_vector: List[float]):
        """Setzt eine externe Kraft am Knoten."""
        if len(force_vector) != self.dim:
            raise ValueError(f"Kraftvektor muss Länge {self.dim} haben.")
        self.forces = np.array(force_vector, dtype=np.float64)

    def set_fixed(self, fixed_dofs: List[bool]):
        """Setzt Randbedingungen (Lager)."""
        if len(fixed_dofs) != self.dim:
            raise ValueError(f"Randbedingungen müssen Länge {self.dim} haben.")
        self.fixed = fixed_dofs

    @property
    def x(self) -> float:
        """Helper für Zugriff auf X-Koordinate."""
        return self.coords[0]

    @property
    def z(self) -> float:
        """Helper für Zugriff auf Z-Koordinate (in 2D oft y genannt, hier z laut Folien)."""
        # Annahme: In 2D ist coords=[x, z].
        return self.coords[1]

    @property
    def y(self) -> float:
        """Helper für Zugriff auf Y-Koordinate (nur relevant für 3D)."""
        if self.dim < 3:
            raise AttributeError("Y-Koordinate existiert nur in 3D.")
        return self.coords[1]  # In 3D üblicherweise [x, y, z]

    def __repr__(self):
        status = "active" if self.active else "inactive"
        return f"Node(id={self.id}, pos={self.coords}, state={status})"