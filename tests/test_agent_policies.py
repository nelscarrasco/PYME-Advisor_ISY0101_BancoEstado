"""
Pruebas de Integración y Reglas de Negocio: Agente PYME-Advisor.
Verifica que las respuestas del agente respeten los guardrails y dictámenes obligatorios.
"""

import unittest
from src.agent.agent_core import PymeAdvisorAgent

class TestAgentPolicies(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = PymeAdvisorAgent()

    def test_admissible_case_leasing(self):
        """Verifica que una empresa solvente solicitando camión reciba dictamen PRE-ADMISIBLE y Leasing."""
        query = "Represento a Transportes y Logistica Biobio SpA (RUT 76.123.456-K). Queremos 1.500 UF para renovar camión."
        res = self.agent.process_query(query)
        self.assertIn("PRE-ADMISIBLE", res["response"])
        self.assertIn("Leasing", res["response"])
        self.assertIn("Art. 3", res["response"])
        self.assertIn("Art. 6", res["response"])

    def test_rejected_case_dicom(self):
        """Verifica que empresa con morosidad > $500.000 sea clasificada NO ADMISIBLE."""
        query = "Panaderia y Alimentos El Trigal EIRL (RUT 76.999.888-4) solicita crédito de 800 UF."
        res = self.agent.process_query(query)
        self.assertIn("NO ADMISIBLE", res["response"])
        self.assertIn("Art. 4", res["response"])

    def test_derivation_case_high_leverage(self):
        """Verifica que empresa con leverage > 3.2 sea derivada a Comité según Art. 11."""
        query = "Constructora del Sur SA (RUT 76.543.210-8) solicita ampliación de línea de 4.000 UF."
        res = self.agent.process_query(query)
        self.assertIn("COMITÉ", res["response"])
        self.assertIn("Art. 11", res["response"])

if __name__ == "__main__":
    unittest.main()
