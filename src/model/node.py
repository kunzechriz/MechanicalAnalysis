import numpy as np
from typing import List, Optional


class Node:
    """
    Repräsentiert einen Massenpunkt (Knoten) im System.

    Physikalische Beschreibung:
    Der Knoten wird durch den Ortsvektor vec{x} definiert:
    vec{x} = [x, z]^T (in 2D)

    Attribute:
        id (int): Eindeutige Identifikationsnummer.
        coords (np.ndarray): Koordinatenvektor vec{x}.
        active (bool): Status für Topologieoptimierung. False bedeutet 'entfernt'.
        mass (float): Masse m des Knotens (Standard: 1.0 kg).
        forces (np.ndarray): Kraftvektor vec{F}.
        displacements (np.ndarray): Verschiebungsvektor vec{u}.
    """

    def __init__(self, node_id: int, koords: List[float], masse: float = 1.0):
        """
        Initialisiert einen Knoten.
        """
        self.id = node_id
        self.coords = np.array(koords, dtype=np.float64)
        self.mass = masse

        # Erkennung 2D, 3D struktur für später
        self.dim = len(koords)

        self.active = True

        # vec{F} = [F_x, F_z]^T
        self.forces = np.zeros(self.dim, dtype=np.float64)

        # vec{u} = [u_x, u_z]^T
        self.displacements = np.zeros(self.dim, dtype=np.float64)

        # Randbedingungen: True = fest, False = frei
        # [FestX, FestZ]
        self.fixed = [False] * self.dim

        self.global_dof_indices: List[int] = []

    def setze_kraft(self, kraftvektor: List[float]):
        """
        vec{F} = [F_x, F_z]^T
        """
        if len(kraftvektor) != self.dim:
            raise ValueError(f"Kraftvektor muss Länge {self.dim} haben.")
        self.forces = np.array(kraftvektor, dtype=np.float64)

    def setze_randbedingung(self, fixierte_dofs: List[bool]):
        """
        Setzt Randbedingungen (Lager).
            fixierte_dofs: Liste v. Booleans [Fest_x, Fest_z].
            True bedeutet u_i = 0
        """
        if len(fixierte_dofs) != self.dim:
            raise ValueError(f"Randbedingungen müssen Länge {self.dim} haben.")
        self.fixed = fixierte_dofs

    @property
    def x(self) -> float:
        """Zugriff auf x-Komponente
        """
        return self.coords[0]

    @property
    def z(self) -> float:
        """
        Zugriff auf z-Komponente.
        """
        return self.coords[1]

    def __repr__(self):
        status = "aktiv" if self.active else "inaktiv"
        return f"Node(id={self.id}, pos={self.coords}, status={status})"