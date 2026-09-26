"""
Pruebas Unitarias: Herramientas Externas y Cálculo Matemático de Indicadores Económicos.
"""

import unittest
from src.tools.economic_indicators import EconomicIndicatorsTool
from src.tools.client_lookup import ClientLookupTool

class TestExternalTools(unittest.TestCase):
    def setUp(self):
        self.econ_tool = EconomicIndicatorsTool()
        self.client_tool = ClientLookupTool()

    def test_economic_indicators_structure(self):
        """Verifica que la API o caché entregue valores numéricos positivos de UF, Dólar y UTM."""
        data = self.econ_tool.get_indicators()
        self.assertIn("uf", data)
        self.assertIn("dolar", data)
        self.assertIn("utm", data)
        self.assertGreater(data["uf"]["valor"], 30000.0)
        self.assertGreater(data["dolar"]["valor"], 700.0)

    def test_uf_to_clp_conversion_consistency(self):
        """Verifica que la conversión matemática de 1.000 UF a CLP sea exacta."""
        res = self.econ_tool.convert_uf_to_clp(1000.0)
        expected = round(1000.0 * res["valor_uf_utilizado"])
        self.assertEqual(res["monto_clp"], expected)

    def test_client_lookup_by_rut(self):
        """Verifica la correcta identificación y limpieza de RUT."""
        client = self.client_tool.find_by_rut("76123456-k")
        self.assertIsNotNone(client)
        self.assertEqual(client["razon_social"], "Transportes y Logistica Biobio SpA")

    def test_client_eligibility_rules(self):
        """Verifica el cálculo de reglas duras sobre clientes problemáticos."""
        client_moroso = self.client_tool.find_by_rut("76.999.888-4")
        eval_moroso = self.client_tool.evaluate_initial_eligibility(client_moroso)
        self.assertIn("NO ADMISIBLE", eval_moroso["status_preliminar"])

if __name__ == "__main__":
    unittest.main()
