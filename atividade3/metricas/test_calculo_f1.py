#!/usr/bin/env python3
"""Testes unitarios do calculo de F1 (rodar: python -m unittest -v test_calculo_f1.py)."""
import unittest
from calculo_f1 import tokenizar, f1_lexical, para_texto


class TestTokenizacao(unittest.TestCase):
    def test_casefold_e_nfc(self):
        self.assertEqual(tokenizar("Página"), tokenizar("PA\u0301GINA".replace("A\u0301", "Á")))

    def test_hora_nao_separa(self):
        self.assertEqual(tokenizar("das 8h às 17h"), ["das", "8h", "às", "17h"])

    def test_decimal_um_token(self):
        self.assertEqual(tokenizar("R$ 18,90."), ["r", "18,90"])

    def test_data_barra(self):
        self.assertEqual(tokenizar("10/11"), ["10", "11"])

    def test_url(self):
        self.assertEqual(tokenizar("http://localhost:8000/ct01.html"),
                         ["http", "localhost", "8000", "ct01", "html"])


class TestF1(unittest.TestCase):
    def test_identico(self):
        self.assertAlmostEqual(f1_lexical("a b c", "a b c")["F1"], 1.0)

    def test_resposta_vazia(self):
        self.assertEqual(f1_lexical("", "a b c")["F1"], 0.0)

    def test_sem_sobreposicao(self):
        self.assertEqual(f1_lexical("x y", "a b")["F1"], 0.0)

    def test_multiconjunto(self):
        # ref tem 'a' 2x, resposta 1x -> comuns = 1 (nao 2)
        m = f1_lexical("a", "a a")
        self.assertEqual(m["comuns"], 1)
        self.assertAlmostEqual(m["R"], 0.5)

    def test_referencia_vazia_gera_erro(self):
        with self.assertRaises(ValueError):
            f1_lexical("a", "")

    def test_ordem_nao_importa(self):
        self.assertAlmostEqual(f1_lexical("c b a", "a b c")["F1"], 1.0)

    def test_exemplo_limite_do_f1(self):
        # trocar um numero mantem F1 alto, apesar de a resposta ficar errada
        m = f1_lexical("o prazo de entrega é 11/11", "o prazo de entrega é 10/11")
        self.assertGreater(m["F1"], 0.8)

    def test_ct05_versao_b_conferido_a_mao(self):
        resp = para_texto({"titulo": None, "url": "http://localhost:8000/ct05.html",
                           "conteudo": "Estamos atualizando esta página. Volte em breve.", "links": []},
                          ["titulo", "url", "conteudo", "links"])
        ref = para_texto({"titulo": "Página em manutenção", "url": "http://localhost:8000/ct05.html",
                          "conteudo": "Informação insuficiente: a página informa apenas que está em manutenção.",
                          "links": []}, ["titulo", "url", "conteudo", "links"])
        m = f1_lexical(resp, ref)
        self.assertEqual((m["n_resp"], m["n_ref"], m["comuns"]), (12, 18, 7))
        self.assertAlmostEqual(m["F1"], 0.4667, places=3)


if __name__ == "__main__":
    unittest.main()
