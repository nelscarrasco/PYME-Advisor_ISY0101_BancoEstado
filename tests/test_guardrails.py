"""
Pruebas del motor de reglas y de los guardrails de salida (trazabilidad de citas).
"""

import unittest
from src.agent.agent_core import PymeAdvisorAgent
from src.agent.policy_engine import evaluate_policies, NO_ADMISIBLE, COMITE, PRE_ADMISIBLE


BASE_CLIENT = {"giro": "Comercio", "antiguedad_meses": 24, "ventas_anuales_uf": 5000,
               "ratio_endeudamiento_leverage": 1.5, "dscr_cobertura_deuda": 1.4, "morosidad_dicom_clp": 0}


class TestPolicyEngine(unittest.TestCase):
    def test_leasing_exception_between_6_and_12_months(self):
        """Art. 3 N°2: con 8 meses sólo es admisible vía Leasing."""
        client = dict(BASE_CLIENT, antiguedad_meses=8)
        self.assertEqual(evaluate_policies(client, 500, "LEASING")["status"], PRE_ADMISIBLE)
        self.assertEqual(evaluate_policies(client, 500, "CAPITAL_TRABAJO")["status"], NO_ADMISIBLE)

    def test_leverage_ranges(self):
        """Art. 5 / Art. 11: sobre el límite y hasta 3.5x va a Comité; sobre 3.5x no es admisible."""
        self.assertEqual(evaluate_policies(dict(BASE_CLIENT, ratio_endeudamiento_leverage=3.0), 500, "CAPITAL_TRABAJO")["status"], COMITE)
        self.assertEqual(evaluate_policies(dict(BASE_CLIENT, ratio_endeudamiento_leverage=4.0), 500, "CAPITAL_TRABAJO")["status"], NO_ADMISIBLE)
        transporte = dict(BASE_CLIENT, giro="Transporte de carga", ratio_endeudamiento_leverage=3.0)
        self.assertEqual(evaluate_policies(transporte, 500, "LEASING")["status"], PRE_ADMISIBLE)

    def test_amount_over_10000_uf_goes_to_committee(self):
        self.assertEqual(evaluate_policies(BASE_CLIENT, 12000, "CAPITAL_TRABAJO")["status"], COMITE)


class TestOutputGuardrails(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = PymeAdvisorAgent()

    def test_unsupported_citation_is_detected(self):
        """Una cita a un artículo no recuperado debe marcarse como sin respaldo."""
        chunks = [{"article": "Artículo 4"}, {"article": "Sección 1"}]
        text = "Cumple [Manual de Crédito, Art. 4] y [Manual de Crédito, Art. 9] [Catálogo de Productos, Sección 1]"
        v = self.agent.validate_citations(text, chunks)
        self.assertEqual(v["unsupported"], ["Art. 9"])
        self.assertAlmostEqual(v["grounded_ratio"], 2 / 3, places=2)

    def test_all_citations_in_response_are_grounded(self):
        """Toda cita del dictamen generado debe estar respaldada por un fragmento recuperado."""
        res = self.agent.process_query("TecnoAgro Sustentable Ltda (RUT 77.987.654-3) necesita 600 UF de capital de trabajo.")
        self.assertEqual(res["citation_validation"]["unsupported"], [])
        self.assertEqual(res["policy_status"], PRE_ADMISIBLE)

    def test_uf_to_clp_in_response(self):
        """El monto en pesos informado debe ser monto_UF × UF de la herramienta."""
        res = self.agent.process_query("Transportes y Logistica Biobio SpA (RUT 76.123.456-K) pide 1.500 UF para un camión.")
        expected = round(1500 * res["economic_indicators_applied"]["uf_clp"])
        self.assertEqual(res["amount_clp"], expected)
        self.assertIn(f"{expected:,}".replace(",", "."), res["response"])


if __name__ == "__main__":
    unittest.main()
