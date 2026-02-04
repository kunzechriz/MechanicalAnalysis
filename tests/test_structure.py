import unittest
from src.model.structure import Structure2D, Structure3D


class TestMechanicalStructure(unittest.TestCase):

    def setUp(self):
        """Wird vor jedem Test ausgeführt."""
        self.struct = Structure2D()

    def test_grid_creation_2d(self):
        """Testet, ob das 2D Gitter die richtige Anzahl an Knoten erzeugt."""
        width, height = 5, 2
        s = Structure2D.create_grid(width, height)

        expected_nodes = width * height
        self.assertEqual(len(s.nodes), expected_nodes, "Falsche Knotenanzahl im 2D Gitter")

        # Teste, ob Knoten 0 bei (0,0) ist
        self.assertEqual(s.nodes[0].x, 0)
        self.assertEqual(s.nodes[0].z, 0)

    def test_single_spring_calculation(self):
        """
        Testet ein einfaches 1-Feder-System (Hookesches Gesetz).
        Knoten A (fest) --[Feder k=1]-- Knoten B (Kraft F=10)
        Erwartete Verschiebung u = F / k = 10 / 1 = 10.
        """
        # 1. Knoten
        n1 = self.struct.knoten_hinzufuegen(0, 0, [True, True])  # Festlager
        n2 = self.struct.knoten_hinzufuegen(10, 0, [False, False])  # Frei

        # 2. Element (Steifigkeit 1.0)
        self.struct.element_hinzufuegen(n1.id, n2.id, steifigkeit=1.0)

        # 3. Kraft auf Knoten 2 in X-Richtung
        self.struct.last_aufbringen(n2.id, 10.0, 0.0)

        # 4. Lösen
        u = self.struct.loese_system()

        # Verschiebung von Knoten 2 prüfen (Index in u: n2.id * 2 für x)
        u_x_node2 = u[n2.id * 2]

        # Wir tolerieren kleine numerische Abweichungen (assertAlmostEqual)
        self.assertAlmostEqual(u_x_node2, 10.0, places=5, msg="Federberechnung fehlerhaft")

    def test_stability_check_connected(self):
        """Testet, ob check_stability True zurückgibt, wenn alles verbunden ist."""
        # Dreieck aufbauen (stabil)
        n1 = self.struct.knoten_hinzufuegen(0, 0, [True, True])
        n2 = self.struct.knoten_hinzufuegen(10, 0, [True, True])
        n3 = self.struct.knoten_hinzufuegen(5, 10)  # Spitze

        # Alle aktiv
        for n in self.struct.nodes: n.active = True

        self.struct.element_hinzufuegen(n1.id, n3.id)
        self.struct.element_hinzufuegen(n2.id, n3.id)

        is_stable = self.struct.check_stability()
        self.assertTrue(is_stable, "Struktur sollte stabil/verbunden sein")

    def test_stability_check_disconnected(self):
        """Testet, ob check_stability False zurückgibt, wenn ein Teil abgetrennt ist."""
        # Zwei getrennte Teile
        n1 = self.struct.knoten_hinzufuegen(0, 0, [True, True])  # Fest
        n2 = self.struct.knoten_hinzufuegen(10, 0)  # Verbunden mit n1

        n3 = self.struct.knoten_hinzufuegen(20, 0)  # Isolierter Knoten (schwebt)

        for n in self.struct.nodes: n.active = True

        self.struct.element_hinzufuegen(n1.id, n2.id)
        # n3 hat keine Verbindung

        is_stable = self.struct.check_stability()
        self.assertFalse(is_stable, "Struktur sollte als instabil erkannt werden")

    def test_3d_grid_logic(self):
        """Testet grundlegende 3D Funktionen."""
        s3 = Structure3D.create_grid(2, 2, 2)  # 2x2x2 Würfel

        expected_nodes = 2 * 2 * 2
        self.assertEqual(len(s3.nodes), expected_nodes, "Falsche Knotenanzahl im 3D Gitter")

        # Prüfen ob Koordinaten 3D sind
        first_node = s3.nodes[0]
        self.assertTrue(hasattr(first_node, 'y'), "3D Knoten muss Y-Koordinate haben")


if __name__ == '__main__':
    unittest.main()