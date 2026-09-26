"""
Módulo de Integración Interna: Búsqueda y Validación de Clientes PYME.
Consulta la base de datos interna para extraer antecedentes financieros del cliente según su RUT.
"""

import json
import os
import re
from typing import Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "database", "clientes_pyme_simulados.json")

class ClientLookupTool:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = os.path.abspath(db_path)
        self.clients = self._load_clients()

    def _load_clients(self):
        if not os.path.exists(self.db_path):
            return []
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Error] No se pudo cargar base de clientes: {e}")
            return []

    def _clean_rut(self, rut: str) -> str:
        """Limpia puntos y espacios, manteniendo guión y mayúscula en dígito verificador."""
        cleaned = re.sub(r"[^0-9kK]", "", rut.strip()).upper()
        if len(cleaned) > 1:
            return f"{cleaned[:-1]}-{cleaned[-1]}"
        return cleaned

    def find_by_rut(self, rut: str) -> Optional[Dict[str, Any]]:
        """Busca un cliente por RUT en la base de datos institucional."""
        clean_target = self._clean_rut(rut)
        for client in self.clients:
            if self._clean_rut(client.get("rut", "")) == clean_target:
                return client
        return None

    def search_by_name(self, name_query: str) -> Optional[Dict[str, Any]]:
        """Busca un cliente por coincidencia aproximada de razón social."""
        query_norm = name_query.lower().strip()
        for client in self.clients:
            if query_norm in client.get("razon_social", "").lower():
                return client
        return None

    def evaluate_initial_eligibility(self, client: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verificación preliminar de reglas duras según las políticas bancarias:
        - Antigüedad mínima: 12 meses
        - Morosidad DICOM: <= $500.000 CLP
        - Ratio de Endeudamiento: <= 2.5 (o <= 3.2 en transporte)
        """
        issues = []
        is_hard_reject = False
        requires_committee = False

        # 1. Antigüedad
        antiguedad = client.get("antiguedad_meses", 0)
        if antiguedad < 12:
            issues.append(f"Antigüedad de {antiguedad} meses es inferior a los 12 meses exigidos por el Art. 3 del Manual.")
            if antiguedad < 6:
                is_hard_reject = True

        # 2. Morosidad comercial
        dicom = client.get("morosidad_dicom_clp", 0)
        if dicom > 500000:
            issues.append(f"Registra morosidad en DICOM por ${dicom:,} CLP (Límite máximo permitido: $500.000 CLP según Art. 4).")
            is_hard_reject = True
        elif dicom > 100000:
            issues.append(f"Registra morosidad menor por ${dicom:,} CLP que requiere carta de regularización (Art. 4).")

        # 3. Ratio de apalancamiento
        leverage = client.get("ratio_endeudamiento_leverage", 0.0)
        rubro = client.get("giro", "").lower()
        max_leverage = 3.2 if "transporte" in rubro or "manufactura" in rubro else 2.5

        if leverage > max_leverage:
            requires_committee = True
            issues.append(f"Ratio de endeudamiento (Leverage) de {leverage:.2f} supera el límite normativo de {max_leverage:.1f}x. Requiere elevación a Comité de Crédito (Art. 11).")

        # Estado global preliminar
        if is_hard_reject:
            status = "NO ADMISIBLE (POLÍTICA DE RIESGO)"
        elif requires_committee:
            status = "DERIVACIÓN REQUERIDA (COMITÉ ESPECIAL ART. 11)"
        else:
            status = "PRE-ADMISIBLE (CUMPLE POLÍTICAS GENERALES)"

        return {
            "cliente": client.get("razon_social"),
            "rut": client.get("rut"),
            "status_preliminar": status,
            "observaciones": issues,
            "tramo_fogape": client.get("tramo_ventas_fogape", "No evaluado"),
            "ventas_anuales_uf": client.get("ventas_anuales_uf", 0)
        }


if __name__ == "__main__":
    tool = ClientLookupTool()
    c = tool.find_by_rut("76.123.456-k")
    print("Cliente encontrado:", c.get("razon_social") if c else "No encontrado")
    if c:
        eval_res = tool.evaluate_initial_eligibility(c)
        print("Evaluación preliminar:", json.dumps(eval_res, indent=2, ensure_ascii=False))
