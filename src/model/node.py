import numpy as np
from typing import List


class Node:
    def __init__(self, node_id: int, koords: List[float], masse: float = 1.0):
        self.id = node_id
        self.coords = np.array(koords, dtype=np.float64)
        self.mass = masse
        self.dim = len(koords)
        self.active = True
        self.forces = np.zeros(self.dim, dtype=np.float64)
        self.displacements = np.zeros(self.dim, dtype=np.float64)
        self.fixed = [False] * self.dim
        self.global_dof_indices: List[int] = []

    def setze_kraft(self, kraftvektor: List[float]):
        if len(kraftvektor) != self.dim:
            raise ValueError(f"Kraftvektor muss Länge {self.dim} haben.")
        self.forces = np.array(kraftvektor, dtype=np.float64)

    def setze_randbedingung(self, fixierte_dofs: List[bool]):
        if len(fixierte_dofs) != self.dim:
            raise ValueError(f"Randbedingungen müssen Länge {self.dim} haben.")
        self.fixed = fixierte_dofs

    @property
    def x(self) -> float:
        return self.coords[0]

    @property
    def z(self) -> float:
        return self.coords[1]

    @property
    def y(self) -> float:
        """Gibt Tiefe zurück (für 3D wichtig!)"""
        return self.coords[2] if self.dim > 2 else 0.0

    def __repr__(self):
        status = "aktiv" if self.active else "inaktiv"
        return f"Node(id={self.id}, pos={self.coords}, status={status})"