"""
Motor de Reglas de Política Crediticia (Guardrail determinista).

Traduce los artículos del Manual de Políticas de Crédito PYME a verificaciones
explícitas sobre el perfil del cliente y la solicitud. Se usa para:
  1. Decidir el estado preliminar (PRE-ADMISIBLE / NO ADMISIBLE / COMITÉ) sin depender del LLM.
  2. Entregar al LLM los resultados de cada regla, para que explique y no invente.
  3. Contrastar el dictamen del LLM: si difiere del motor de reglas, prevalece el motor.

Cada verificación indica el artículo que la respalda, lo que permite la trazabilidad.
"""

from typing import Dict, Any, List, Optional

def fmt_num(value, decimals: int = 0) -> str:
    """Formato numérico chileno: punto para miles y coma para decimales (ej: 1.500,00)."""
    s = f"{value:,.{decimals}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


PRE_ADMISIBLE = "PRE-ADMISIBLE"
NO_ADMISIBLE = "NO ADMISIBLE"
COMITE = "DERIVACIÓN A COMITÉ ESPECIAL"
INFORMATIVA = "INFORMACIÓN GENERAL"

LEASING_KEYWORDS = ["camion", "camión", "maquinaria", "tractor", "equipo", "vehiculo", "vehículo", "leasing"]
FACTORING_KEYWORDS = ["factura", "facturas", "dte", "cesion", "cesión", "factoring"]


def detect_product(query: str) -> str:
    q = query.lower()
    if any(w in q for w in LEASING_KEYWORDS):
        return "LEASING"
    if any(w in q for w in FACTORING_KEYWORDS):
        return "FACTORING"
    return "CAPITAL_TRABAJO"


def sector_leverage_limit(giro: str) -> float:
    g = (giro or "").lower()
    return 3.2 if ("transporte" in g or "manufactura" in g) else 2.5


def evaluate_policies(client: Optional[Dict[str, Any]], monto_uf: Optional[float], product: str) -> Dict[str, Any]:
    """Aplica las reglas del manual y retorna el estado y el detalle de cada verificación."""
    checks: List[Dict[str, str]] = []

    def add(dimension, article, result, detail):
        checks.append({"dimension": dimension, "article": article, "result": result, "detail": detail})

    if not client:
        return {"status": INFORMATIVA, "checks": checks, "reasons": []}

    rejects, committee = [], []

    # Art. 1 — Segmento PYME por ventas
    ventas = client.get("ventas_anuales_uf", 0)
    if 800 <= ventas <= 100000:
        add("Segmento PYME", "Art. 1", "CUMPLE", f"Ventas anuales de {fmt_num(ventas)} UF dentro del rango 800–100.000 UF.")
    else:
        add("Segmento PYME", "Art. 1", "NO CUMPLE", f"Ventas anuales de {fmt_num(ventas)} UF fuera del rango 800–100.000 UF.")
        rejects.append("Art. 1")

    # Art. 3 — Antigüedad
    meses = client.get("antiguedad_meses", 0)
    if meses >= 12:
        add("Antigüedad", "Art. 3", "CUMPLE", f"{meses} meses de actividad (mínimo 12).")
    elif meses >= 6 and product == "LEASING":
        add("Antigüedad", "Art. 3", "OBSERVACIÓN", f"{meses} meses: sólo admisible vía Leasing con garantía real y pie mínimo de 25% (excepción Art. 3 N°2).")
    else:
        motivo = "inferior a 6 meses" if meses < 6 else "entre 6 y 12 meses y el producto solicitado no es Leasing"
        add("Antigüedad", "Art. 3", "NO CUMPLE", f"{meses} meses de actividad ({motivo}).")
        rejects.append("Art. 3")

    # Art. 4 — Morosidad comercial
    dicom = client.get("morosidad_dicom_clp", 0)
    if dicom > 500000:
        add("Morosidad DICOM", "Art. 4", "NO CUMPLE", f"Morosidad de ${fmt_num(dicom)} CLP supera el máximo de $500.000.")
        rejects.append("Art. 4")
    elif dicom >= 100000:
        add("Morosidad DICOM", "Art. 4", "OBSERVACIÓN", f"Morosidad de ${fmt_num(dicom)} CLP: requiere carta de justificación y comprobante de regularización.")
    else:
        add("Morosidad DICOM", "Art. 4", "CUMPLE", f"Morosidad de ${fmt_num(dicom)} CLP (máximo $500.000).")

    # Art. 5 / Art. 11 — Leverage
    lev = float(client.get("ratio_endeudamiento_leverage", 0.0))
    lim = sector_leverage_limit(client.get("giro", ""))
    if lev <= lim:
        add("Leverage", "Art. 5", "CUMPLE", f"Leverage {fmt_num(lev, 2)}x dentro del límite de {fmt_num(lim, 1)}x para el rubro.")
    elif lev <= 3.5:
        add("Leverage", "Art. 11", "COMITÉ", f"Leverage {fmt_num(lev, 2)}x supera el límite de {fmt_num(lim, 1)}x (Art. 5) pero no 3,5x: derivación obligatoria.")
        committee.append("Art. 11")
    else:
        add("Leverage", "Art. 11", "NO CUMPLE", f"Leverage {fmt_num(lev, 2)}x supera 3,5x: no admisible.")
        rejects.append("Art. 11")

    # Art. 5 — DSCR
    dscr = client.get("dscr_cobertura_deuda")
    if dscr is not None:
        if dscr >= 1.25:
            add("Cobertura de deuda (DSCR)", "Art. 5", "CUMPLE", f"DSCR {fmt_num(dscr, 2)} (mínimo 1,25).")
        else:
            add("Cobertura de deuda (DSCR)", "Art. 5", "COMITÉ", f"DSCR {fmt_num(dscr, 2)} bajo el mínimo de 1,25: se eleva a Comité (Art. 11 N°5).")
            committee.append("Art. 11")

    # Art. 11 — Monto
    if monto_uf is not None and monto_uf > 10000:
        add("Monto solicitado", "Art. 11", "COMITÉ", f"{fmt_num(monto_uf, 0)} UF supera las 10.000 UF de atribución regular.")
        committee.append("Art. 11")

    if rejects:
        status = NO_ADMISIBLE
    elif committee:
        status = COMITE
    else:
        status = PRE_ADMISIBLE

    return {"status": status, "checks": checks, "reasons": rejects or committee}


def format_checks_for_prompt(policy: Dict[str, Any]) -> str:
    if not policy["checks"]:
        return "Sin cliente identificado: no se aplican reglas individuales. Responder con información general del manual."
    lines = [f"- [{c['article']}] {c['dimension']}: {c['result']} — {c['detail']}" for c in policy["checks"]]
    lines.append(f"ESTADO DETERMINADO POR EL MOTOR DE REGLAS: {policy['status']}")
    return "\n".join(lines)
