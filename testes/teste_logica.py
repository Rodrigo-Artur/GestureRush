import random
import unittest
from types import SimpleNamespace

from logica import (Alvo, DetectorPunho, DetectorGestoMantido,
                    criar_alvo, pontuacao, classificar_gesto,
                    mapear_mira)


class Testes(unittest.TestCase):
    def test_punho_um_clique_por_fechamento(self):
        d = DetectorPunho()
        gestos = ['apontando', 'apontando', 'punho', 'punho', 'punho',
                  'apontando', 'apontando', 'punho', 'punho']
        self.assertEqual([d.atualizar(g) for g in gestos],
                         [False, False, False, True, False,
                          False, False, False, True])

    def test_gesto_mantido(self):
        d = DetectorGestoMantido(1.2)
        self.assertFalse(d.atualizar(True, 0.0))
        self.assertFalse(d.atualizar(True, 1.0))
        self.assertTrue(d.atualizar(True, 1.2))
        self.assertFalse(d.atualizar(True, 2.2))
        self.assertFalse(d.atualizar(False, 2.3))
        self.assertFalse(d.atualizar(True, 3.0))
        self.assertTrue(d.atualizar(True, 4.2))

    def test_pontuacao(self):
        self.assertEqual(pontuacao('normal', 0), 10)
        self.assertEqual(pontuacao('bonus', 3), 26)
        self.assertEqual(pontuacao('perigo', 10), -15)

    def test_criar_alvo_valido(self):
        rng = random.Random(5)
        alvo = criar_alvo(1280, 720, [], 1, rng)
        self.assertIsInstance(alvo, Alvo)
        self.assertTrue(0 < alvo.x < 1280)
        self.assertIn(alvo.tipo, {'normal', 'bonus', 'perigo'})

    def test_mapear_mira(self):
        normal = mapear_mira(0.6, 0.4, 1000, 800, 1.0)
        rapido = mapear_mira(0.6, 0.4, 1000, 800, 1.8)
        self.assertGreater(rapido[0], normal[0])
        self.assertLess(rapido[1], normal[1])
        self.assertEqual(mapear_mira(1.0, 0.0, 1000, 800, 3.0), (1000, 0))

    def test_classificar_gestos(self):
        def marcos(indicador, medio, anelar, minimo):
            pts = [SimpleNamespace(x=.5, y=.7) for _ in range(21)]
            pts[0] = SimpleNamespace(x=.5, y=.9)
            for ponta, base, estendido in zip(
                    (8, 12, 16, 20), (6, 10, 14, 18),
                    (indicador, medio, anelar, minimo)):
                pts[base] = SimpleNamespace(x=.5, y=.65)
                pts[ponta] = SimpleNamespace(x=.5, y=.35 if estendido else .75)
            return pts

        self.assertEqual(classificar_gesto(marcos(1, 0, 0, 0))[2], 'apontando')
        self.assertEqual(classificar_gesto(marcos(0, 0, 0, 0))[2], 'punho')
        self.assertEqual(classificar_gesto(marcos(1, 1, 1, 1))[2], 'palma')
        self.assertEqual(classificar_gesto(marcos(1, 1, 0, 0))[2], 'vitoria')
        self.assertEqual(classificar_gesto(marcos(0, 1, 0, 0))[2], 'outro')


if __name__ == '__main__':
    unittest.main()
