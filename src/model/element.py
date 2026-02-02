import numpy as np
from abc import ABC, abstractmethod
from .node import Node

class Element(ABC):
    def __init__(self, node_a: Node, node_b: Node, steifigkeit: float):
        self.node_a = node_a
        self.node_b = node_b
        self.k = steifigkeit

    @abstractmethod
    def berechne_lokale_steifigkeitsmatrix(self) -> np.ndarray:
        pass

    @abstractmethod
    def berechne_transformationsmatrix(self) -> np.ndarray:
        pass

    @abstractmethod
    def berechne_transformierte_steifigkeitsmatrix(self) -> np.ndarray:
        pass

    @abstractmethod
    def berechne_verformungsenergie(self, u_global: np.ndarray) -> float:
        pass

class Spring2D(Element):
    def _berechne_richtungsvektor(self) -> np.ndarray:
        """
        vec{n} = [[x_j - x_i], [z_j - z_i]] -> vec{e}_n = vec{n} / ||vec{n}||
        """
        diff = self.node_b.coords - self.node_a.coords
        laenge = np.linalg.norm(diff)
        if laenge == 0:
            raise ValueError("Elementlänge ist Null.")
        return diff / laenge

    def berechne_lokale_steifigkeitsmatrix(self) -> np.ndarray:
        """
        K = [[k, -k], [-k, k]]
        """
        return self.k * np.array([[1.0, -1.0],
                                  [-1.0, 1.0]])

    def berechne_transformationsmatrix(self) -> np.ndarray:
        """
        O = vec{e}_n (outer) vec{e}_n
        """
        e_n = self._berechne_richtungsvektor()
        return np.outer(e_n, e_n)

    def berechne_transformierte_steifigkeitsmatrix(self) -> np.ndarray:
        """
        K_o = K (kron) O
        """
        K_lokal = self.berechne_lokale_steifigkeitsmatrix()
        O = self.berechne_transformationsmatrix()
        return np.kron(K_lokal, O)

    def berechne_verformungsenergie(self, u_global: np.ndarray) -> float:
        """
        c^{(i,j)} = 1/2 * vec{u}^{(i,j)T} * K_o^{(i,j)} * vec{u}^{(i,j)}
        """
        indizes = self.node_a.global_dof_indices + self.node_b.global_dof_indices
        u_element = u_global[indizes]
        K_o = self.berechne_transformierte_steifigkeitsmatrix()
        return 0.5 * np.dot(u_element.T, np.dot(K_o, u_element))