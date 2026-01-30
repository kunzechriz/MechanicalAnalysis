from abc import ABC, abstractmethod
from .node import Node

class Element(ABC):
    """
    Abstrakte Basisklasse für alle Strukturelemente (Federn, Balken, etc.).
    Ermöglicht spätere Erweiterung auf 3D ohne den Optimizer ändern zu müssen.
    """
    def __init__(self, node_a: Node, node_b: Node, stiffness: float):
        self.node_a = node_a
        self.node_b = node_b
        self.k = stiffness

    @abstractmethod
    def element_stiffness_matrix(self) -> np.ndarray:
        """Berechnet die lokale Steifigkeitsmatrix (lokale Koordinaten)."""
        pass

    @abstractmethod
    def transformation_matrix(self) -> np.ndarray:
        """Berechnet die Transformationsmatrix ins globale System."""
        pass

    @abstractmethod
    def global_stiffness_matrix(self) -> np.ndarray:
        """Gibt die transformierte Matrix (Kg_element) zurück."""
        pass

    @abstractmethod
    def calculate_strain_energy(self, u_global: np.ndarray) -> float:
        """Berechnet die Verformungsenergie in diesem Element."""
        pass

class Spring2D(Element):
    """Konkrete Implementierung einer 2D-Feder."""
    def element_stiffness_matrix(self) -> np.ndarray:
        # Hier kommt später die 2x2 Matrix rein (k, -k...)
        pass

    def transformation_matrix(self) -> np.ndarray:
        # Hier kommt die Berechnung von cos/sin bzw. Richtungsvektor rein
        pass

    def global_stiffness_matrix(self) -> np.ndarray:
        # Hier kommt Kronecker-Produkt oder Matrizenmultiplikation rein
        pass

    def calculate_strain_energy(self, u_global: np.ndarray) -> float:
        # Berechnung: 0.5 * u.T * K * u
        pass

    @abstractmethod
    def element_stiffness_matrix(self) -> np.ndarray:
        """Berechnet die lokale Steifigkeitsmatrix (lokale Koordinaten)."""
        pass

    @abstractmethod
    def transformation_matrix(self) -> np.ndarray:
        """Berechnet die Transformationsmatrix ins globale System."""
        pass

    @abstractmethod
    def global_stiffness_matrix(self) -> np.ndarray:
        """Gibt die transformierte Matrix (Kg_element) zurück."""
        pass

    @abstractmethod
    def calculate_strain_energy(self, u_global: np.ndarray) -> float:
        """Berechnet die Verformungsenergie in diesem Element."""
        pass


class Spring2D(Element):
    """Konkrete Implementierung einer 2D-Feder."""

    def element_stiffness_matrix(self) -> np.ndarray:
        # Hier kommt später die 2x2 Matrix rein (k, -k...)
        pass

    def transformation_matrix(self) -> np.ndarray:
        # Hier kommt die Berechnung von cos/sin bzw. Richtungsvektor rein
        pass

    def global_stiffness_matrix(self) -> np.ndarray:
        # Hier kommt Kronecker-Produkt oder Matrizenmultiplikation rein
        pass

    def calculate_strain_energy(self, u_global: np.ndarray) -> float:
        # Berechnung: 0.5 * u.T * K * u
        pass