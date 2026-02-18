import numpy as np
from abc import ABC, abstractmethod
from .node import Node

########################################################################################################
#       Abstrakte Klasse um 3D Struktur später zu ermöglichen
########################################################################################################
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
########################################################################################################
#       Federn für 2D Struktur
########################################################################################################
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

########################################################################################################
#       Federn für 3D Struktur
########################################################################################################
class Spring3D:
    def __init__(self, node_a, node_b, stiffness=1.0):
        self.node_a = node_a
        self.node_b = node_b
        self.stiffness = stiffness
        self.id = -1

    def berechne_transformierte_steifigkeitsmatrix(self):
        dx = self.node_b.x - self.node_a.x
        dy = self.node_b.z - self.node_a.z
        dz = getattr(self.node_b, 'y', 0) - getattr(self.node_a, 'y', 0)

        length = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
        if length == 0: return np.zeros((6, 6))

        l = dx / length
        m = dy / length
        n = dz / length

        k = self.stiffness

        T_sub = np.array([
            [l * l, l * m, l * n],
            [m * l, m * m, m * n],
            [n * l, n * m, n * n]
        ])

        k_matrix = np.block([
            [T_sub, -T_sub],
            [-T_sub, T_sub]
        ]) * k

        return k_matrix

    def berechne_verformungsenergie(self, u_global):
        idx_a = self.node_a.global_dof_indices
        idx_b = self.node_b.global_dof_indices

        u_elem = np.concatenate([u_global[idx_a], u_global[idx_b]])
        k_elem = self.berechne_transformierte_steifigkeitsmatrix()

        return 0.5 * np.dot(u_elem.T, np.dot(k_elem, u_elem))