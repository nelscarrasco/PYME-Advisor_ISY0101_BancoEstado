"""
Módulo Principal: Orquestador Agéntico (Agent Core).

Flujo por consulta (patrón herramienta → recuperación → generación → verificación):
  1. Extrae entidades (RUT, monto) de la consulta.
  2. Invoca herramientas: ClientLookupTool (base interna) y EconomicIndicatorsTool (API externa).
  3. Aplica el motor de reglas del manual (policy_engine) para determinar el estado preliminar.
  4. Recupera del índice vectorial los fragmentos normativos mediante descomposición de la
     consulta en sub-consultas por dimensión de riesgo (multi-query retrieval).
  5. Genera el dictamen con el LLM (si hay OPENAI_API_KEY) o con el motor de síntesis local.
  6. Verifica que cada cita del dictamen esté respaldada por un fragmento recuperado
     y que el estado declarado coincida con el motor de reglas (guardrail de salida).
"""

import os
import re
import time
from typing import Dict, Any, Optional, List, Set

from src.rag.vector_store import VectorStore
from src.tools.economic_indicators import EconomicIndicatorsTool
from src.tools.client_lookup import ClientLookupTool
from src.agent.prompts import SYSTEM_PROMPT_PYME_ADVISOR, build_agent_prompt
from src.agent.context_manager import ConversationContextManager
from src.agent.policy_engine import (
    evaluate_policies, detect_product, format_checks_for_prompt,
    PRE_ADMISIBLE, NO_ADMISIBLE, COMITE, INFORMATIVA, fmt_num,
)

# Sub-consultas por dimensión de riesgo (descomposición de la consulta para el retrieval)
DIMENSION_QUERIES = {
    "segmento": "definición segmento PYME ventas anuales netas sujeto de crédito",
    "antiguedad": "antigüedad operacional iniciación de actividades primera categoría meses declaraciones IVA",
    "morosidad": "morosidad protestos boletín comercial DICOM comportamiento comercial",
    "leverage": "ratio de endeudamiento leverage deuda total patrimonio cobertura servicio de la deuda DSCR",
    "fogape": "garantía estatal FOGAPE cobertura capital insoluto ventas",
    "garantias": "garantías reales hipotecaria prendaria prenda sin desplazamiento",
    "comite": "derivación comité especial de riesgo crediticio solicitudes montos",
    "documentos": "requisitos documentales carpeta tributaria certificado de vigencia de poderes",
    "producto_LEASING": "leasing operativo financiero activos fijos maquinaria vehículos camiones opción de compra",
    "producto_CAPITAL_TRABAJO": "crédito capital de trabajo PYME monto mínimo plazo período de gracia",
    "producto_FACTORING": "factoring cesión de facturas anticipo DTE",
}

PRODUCT_INFO = {
    "LEASING": ("Leasing Operativo y Financiero de Activos Fijos", 2, 9),
    "CAPITAL_TRABAJO": ("Crédito Comercial para Capital de Trabajo PYME", 1, 8),
    "FACTORING": ("Factoring Comercial con Cesión Electrónica de Facturas", 4, 10),
}

CITE_MANUAL_RE = re.compile(r"\[Manual de Crédito, Art\. (\d+)\]")
CITE_CATALOG_RE = re.compile(r"\[Catálogo de Productos, Sección (\d+)\]")


def _num(ref: str) -> str:
    m = re.search(r"\d+", ref or "")
    return m.group(0) if m else ""


class PymeAdvisorAgent:
    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.vector_store = vector_store or VectorStore.load_from_default_data()
        self.economic_tool = EconomicIndicatorsTool()
        self.client_tool = ClientLookupTool()
        self.context_manager = ConversationContextManager()

    # ------------------------------------------------------------------ entidades
    def _extract_rut(self, text: str) -> Optional[str]:
        """Detecta patrones de RUT chileno en el texto del usuario."""
        match = re.search(r"\b(\d{1,2}\.?\d{3}\.?\d{3}-?[\dkK])\b", text)
        return match.group(1) if match else None

    def _extract_amount(self, text: str) -> Dict[str, Any]:
        """Extrae montos solicitados en UF o pesos chilenos."""
        uf_match = re.search(r"(\d{1,3}(?:\.\d{3})+|\d+(?:,\d+)?)\s*(?:uf|unidades de fomento)\b", text, re.IGNORECASE)
        if uf_match:
            val_str = uf_match.group(1).replace(".", "").replace(",", ".")
            try:
                return {"type": "UF", "amount": float(val_str)}
            except ValueError:
                pass
        millones_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:millones|millón|millon)\b", text, re.IGNORECASE)
        if millones_match:
            return {"type": "CLP", "amount": float(millones_match.group(1).replace(",", ".")) * 1_000_000}
        clp_match = re.search(r"\$\s*(\d{1,3}(?:\.\d{3})+)", text)
        if clp_match:
            return {"type": "CLP", "amount": float(clp_match.group(1).replace(".", ""))}
        return {"type": "UNKNOWN", "amount": 0.0}

    # ------------------------------------------------------------------ retrieval
    def _retrieve(self, user_query: str, dimensions: List[str]) -> List[Dict[str, Any]]:
        """Multi-query retrieval: una sub-consulta por dimensión + la consulta original."""
        merged: Dict[str, Dict[str, Any]] = {}

        def merge(results, label):
            for r in results:
                cid = r["chunk_id"]
                if cid not in merged or r["similarity_score"] > merged[cid]["similarity_score"]:
                    r = dict(r)
                    r["retrieved_for"] = label
                    merged[cid] = r

        merge(self.vector_store.search(user_query, top_k=2), "consulta original")
        for dim in dimensions:
            top_k = 2 if dim.startswith("producto_") else 1
            merge(self.vector_store.search(DIMENSION_QUERIES[dim], top_k=top_k), dim)
        return sorted(merged.values(), key=lambda c: c["similarity_score"], reverse=True)

    @staticmethod
    def _format_context(chunks: List[Dict[str, Any]]) -> str:
        if not chunks:
            return "No se encontraron fragmentos normativos relevantes."
        parts = []
        for i, c in enumerate(chunks, 1):
            parts.append(
                f"--- [FRAGMENTO {i}] Fuente: {c.get('source')} | {c.get('article')} - {c.get('heading')} "
                f"| Relevancia: {c.get('similarity_score', 0)*100:.1f}%\n{c.get('text')}\n"
            )
        return "\n".join(parts)

    @staticmethod
    def _supported_refs(chunks: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
        arts, secs = set(), set()
        for c in chunks:
            ref = c.get("article", "")
            if "Art" in ref:
                arts.add(_num(ref))
            elif ref.startswith("Sección"):
                secs.add(_num(ref))
        return {"articles": arts, "sections": secs}

    def validate_citations(self, text: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Guardrail de salida: cada cita debe estar respaldada por un fragmento recuperado."""
        refs = self._supported_refs(chunks)
        cited = [f"Art. {n}" for n in CITE_MANUAL_RE.findall(text)] + [f"Sección {n}" for n in CITE_CATALOG_RE.findall(text)]
        unique = sorted(set(cited), key=lambda x: (x.split()[0], int(_num(x))))
        supported = [c for c in unique if (_num(c) in refs["articles"] if c.startswith("Art") else _num(c) in refs["sections"])]
        unsupported = [c for c in unique if c not in supported]
        ratio = round(len(supported) / len(unique), 3) if unique else 0.0
        return {"cited": unique, "supported": supported, "unsupported": unsupported, "grounded_ratio": ratio}

    # ------------------------------------------------------------------ flujo principal
    def process_query(self, user_query: str) -> Dict[str, Any]:
        start_time = time.time()
        tools_executed = []
        q_lower = user_query.lower()

        # 1. Entidades
        detected_rut = self._extract_rut(user_query)
        amount = self._extract_amount(user_query)

        # 2. Herramienta interna: cliente
        client_profile = None
        is_generic = any(w in q_lower for w in ["consulta general", "en general", "cuáles son los", "cuáles son las",
                                                "qué requisitos", "que requisitos"])
        if detected_rut:
            client_profile = self.client_tool.find_by_rut(detected_rut)
            tools_executed.append({
                "tool": "ClientLookupTool", "action": "find_by_rut", "target": detected_rut,
                "status": "SUCCESS" if client_profile else "NOT_FOUND",
                "data": f"Cliente identificado: {client_profile.get('razon_social')}" if client_profile
                        else "RUT no registrado en la base interna",
            })
        elif not is_generic and any(w in q_lower for w in ["mi empresa", "nosotros", "nuestro", "mi rut", "postular", "calificamos"]):
            client_profile = self.context_manager.get_active_client()
        elif not is_generic:
            for c in self.client_tool.clients:
                if c.get("razon_social", "").lower() in q_lower:
                    client_profile = c
                    tools_executed.append({"tool": "ClientLookupTool", "action": "search_by_name",
                                           "target": c.get("razon_social"), "status": "SUCCESS",
                                           "data": f"Cliente identificado: {c.get('razon_social')}"})
                    break
        if client_profile:
            self.context_manager.set_active_client(client_profile)

        # 2b. Herramienta externa: indicadores económicos
        economic_data = self.economic_tool.get_indicators()
        tools_executed.append({
            "tool": "EconomicIndicatorsTool", "action": "get_indicators", "status": "SUCCESS",
            "data": f"UF: ${fmt_num(economic_data['uf']['valor'], 2)} CLP | Dólar: ${fmt_num(economic_data['dolar']['valor'], 2)} CLP "
                    f"({economic_data.get('fuente', 'mindicador.cl')})",
        })
        uf_val = economic_data["uf"]["valor"]
        if amount["type"] == "UF":
            monto_uf, monto_clp = amount["amount"], round(amount["amount"] * uf_val)
        elif amount["type"] == "CLP":
            monto_clp, monto_uf = round(amount["amount"]), round(amount["amount"] / uf_val, 2)
        else:
            monto_uf = monto_clp = None

        # 3. Motor de reglas
        product = detect_product(user_query)
        policy = evaluate_policies(client_profile, monto_uf, product)

        # 4. Retrieval multi-consulta
        dims = ["antiguedad", "morosidad", "leverage", "fogape", "garantias", f"producto_{product}", "documentos"]
        if client_profile:
            dims.insert(0, "segmento")
        if policy["status"] in (COMITE, NO_ADMISIBLE) or (monto_uf and monto_uf > 10000):
            dims.append("comite")
        chunks = self._retrieve(user_query, dims)
        tools_executed.append({"tool": "VectorStore", "action": "multi_query_search", "status": "SUCCESS",
                               "data": f"{len(dims) + 1} sub-consultas → {len(chunks)} fragmentos únicos recuperados"})

        # 5. Generación
        generation_mode = "Motor de síntesis local (reglas)"
        response = None
        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key:
            try:
                import openai
                client = openai.OpenAI(api_key=openai_key)
                prompt = build_agent_prompt(user_query, self._format_context(chunks), economic_data, client_profile,
                                            policy_checks=format_checks_for_prompt(policy),
                                            history=self.context_manager.get_history_summary())
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": SYSTEM_PROMPT_PYME_ADVISOR},
                              {"role": "user", "content": prompt}],
                    temperature=0.1,
                )
                response = completion.choices[0].message.content
                generation_mode = "LLM gpt-4o-mini"
            except Exception as e:
                print(f"[Aviso] Error al llamar al LLM: {e}. Usando motor de síntesis local.")
        if not response:
            response = self._synthesize_grounded_response(user_query, client_profile, monto_uf, monto_clp,
                                                          economic_data, chunks, policy, product)

        # 6. Guardrails de salida
        validation = self.validate_citations(response, chunks)
        if generation_mode.startswith("LLM") and policy["status"] != INFORMATIVA and policy["status"] not in response.upper():
            response += (f"\n\n> **Nota de control:** el motor de reglas del manual determina el estado "
                         f"**{policy['status']}**; prevalece sobre la redacción del modelo.")
        if validation["unsupported"]:
            response += (f"\n\n> **Advertencia de trazabilidad:** las citas {', '.join(validation['unsupported'])} "
                         f"no están respaldadas por los fragmentos recuperados; requieren revisión del ejecutivo.")

        self.context_manager.add_turn("user", user_query)
        self.context_manager.add_turn("assistant", response)

        return {
            "query": user_query,
            "response": response,
            "generation_mode": generation_mode,
            "policy_status": policy["status"],
            "policy_checks": policy["checks"],
            "citation_validation": validation,
            "client_identified": client_profile.get("razon_social") if client_profile else None,
            "client_rut": client_profile.get("rut") if client_profile else None,
            "tools_executed": tools_executed,
            "retrieved_sources": [
                {"article": c.get("article"), "heading": c.get("heading"), "source": c.get("source"),
                 "similarity": c.get("similarity_score"), "retrieved_for": c.get("retrieved_for")}
                for c in chunks
            ],
            "economic_indicators_applied": {
                "uf_clp": uf_val, "dolar_clp": economic_data["dolar"]["valor"], "fecha": economic_data["uf"].get("fecha"),
            },
            "amount_uf": monto_uf,
            "amount_clp": monto_clp,
            "execution_time_seconds": round(time.time() - start_time, 3),
        }

    # ------------------------------------------------------------------ síntesis local
    def _synthesize_grounded_response(self, user_query, client, monto_uf, monto_clp, economic_data,
                                      chunks, policy, product) -> str:
        """
        Motor de síntesis local fundamentado: redacta el dictamen a partir de los resultados del
        motor de reglas y SÓLO cita artículos/secciones presentes en los fragmentos recuperados.
        """
        refs = self._supported_refs(chunks)
        uf_val = economic_data["uf"]["valor"]
        fuente = economic_data.get("fuente", "API mindicador.cl")

        def art(n: int) -> str:
            return f"[Manual de Crédito, Art. {n}]" if str(n) in refs["articles"] else "(sin respaldo recuperado)"

        def sec(n: int) -> str:
            return f"[Catálogo de Productos, Sección {n}]" if str(n) in refs["sections"] else ""

        def cite_ref(ref: str) -> str:
            return art(int(_num(ref)))

        status = policy["status"]
        empresa = client.get("razon_social") if client else "Consulta sin cliente identificado"
        rut = client.get("rut") if client else "No informado"
        if monto_uf is not None:
            monto_txt = (f"{fmt_num(monto_uf, 2)} UF, equivalente a **${fmt_num(monto_clp)} CLP** con UF de ${fmt_num(uf_val, 2)} "
                         f"[Fuente: {fuente}]")
        else:
            monto_txt = f"No indicado (UF de referencia del día: ${fmt_num(uf_val, 2)} CLP [Fuente: {fuente}])"

        if status == INFORMATIVA:
            dictamen = "Se entrega información general del manual; para una pre-evaluación se requiere el RUT de la empresa."
        elif status == NO_ADMISIBLE:
            fails = [c for c in policy["checks"] if c["result"] == "NO CUMPLE"]
            dictamen = "; ".join(f"{c['detail']} {cite_ref(c['article'])}" for c in fails)
        elif status == COMITE:
            obs = [c for c in policy["checks"] if c["result"] == "COMITÉ"]
            dictamen = ("La solicitud no puede resolverse en el flujo regular y debe derivarse al Comité Regional de Crédito "
                        f"{art(11)}: " + "; ".join(c["detail"] for c in obs))
        else:
            dictamen = "Cumple los requisitos generales de admisibilidad del manual. El resultado es preliminar y no constituye aprobación del crédito."

        # Sección 2: verificaciones
        if client:
            sec2 = "\n".join(f"- **{c['dimension']}** — {c['result']}: {c['detail']} {cite_ref(c['article'])}"
                             for c in policy["checks"])
        else:
            sec2 = "\n".join([
                f"- **Antigüedad:** mínimo 12 meses de actividad en Primera Categoría; entre 6 y 12 meses sólo vía Leasing con pie de 25% {art(3)}.",
                f"- **Morosidad:** sin morosidades vigentes superiores a $500.000 CLP en el Boletín Comercial {art(4)}.",
                f"- **Endeudamiento:** leverage máximo 2.5x (3.2x en transporte o manufactura) y DSCR mínimo 1.25 {art(5)}.",
            ])

        # Sección 3: garantías
        ventas = client.get("ventas_anuales_uf") if client else None
        if status == NO_ADMISIBLE:
            fogape = f"No corresponde evaluar la garantía FOGAPE mientras no se subsanen los incumplimientos indicados {art(6)}."
        elif ventas is None:
            fogape = (f"Ventas hasta 25.000 UF: cobertura de hasta 85% del capital insoluto; entre 25.001 y 100.000 UF: hasta 70%. "
                      f"Sólo para capital de trabajo e inversión productiva {art(6)}.")
        elif ventas <= 25000:
            fogape = f"Ventas de {fmt_num(ventas)} UF (tramo hasta 25.000 UF): cobertura FOGAPE de hasta **85%** del capital insoluto {art(6)}."
        elif ventas <= 100000:
            fogape = f"Ventas de {fmt_num(ventas)} UF (tramo 25.001–100.000 UF): cobertura FOGAPE de hasta **70%** del capital insoluto {art(6)}."
        else:
            fogape = f"Ventas sobre 100.000 UF: fuera de los tramos FOGAPE {art(6)}."
        if product == "LEASING":
            real = f"Se constituye prenda sin desplazamiento sobre el activo adquirido {art(7)}."
        elif monto_uf is not None and monto_uf > 3000:
            real = f"Monto superior a 3.000 UF: se exige garantía hipotecaria con cobertura mínima de 120% (LTV 80%) {art(7)}."
        elif monto_uf is not None:
            real = f"Monto no supera 3.000 UF: no se exige garantía hipotecaria general {art(7)}."
        else:
            real = f"Sobre 3.000 UF en capital de trabajo o inversión se exige garantía hipotecaria (cobertura 120%) {art(7)}."

        # Sección 4: producto
        prod_name, sec_n, art_n = PRODUCT_INFO[product]
        prod_detail = {
            "LEASING": "Monto mínimo 300 UF, plazo de 24 a 60 meses, opción de compra típica de 1% y cuotas deducibles como gasto para el Impuesto de Primera Categoría",
            "CAPITAL_TRABAJO": "Monto mínimo 150 UF, hasta 3 meses de venta promedio (tope 5.000 UF sin garantía hipotecaria o 15.000 UF con garantía real o FOGAPE), plazo de 6 a 36 meses y hasta 6 meses de gracia de capital",
            "FACTORING": "Anticipo de 80% a 90% del valor neto de las facturas cedidas; deudores con clasificación mínima BBB; tasa sujeta a la TMC fijada por la CMF",
        }[product]
        prod_obs = ""
        if product == "CAPITAL_TRABAJO" and monto_uf is not None and monto_uf < 150:
            prod_obs = " El monto solicitado es inferior al mínimo del producto."
        if product == "LEASING" and monto_uf is not None and monto_uf < 300:
            prod_obs = " El monto solicitado es inferior al mínimo del producto."

        # Sección 5: documentos
        docs = [f"Carpeta Tributaria Electrónica para solicitar créditos (últimos 24 F29 y 2 últimos F22) {sec(1)}".strip(),
                f"Certificado de Vigencia de Poderes con antigüedad menor a 60 días {sec(1)}".strip()]
        if product == "LEASING":
            docs.append("Cotización o factura proforma del bien a financiar.")
        if client and client.get("morosidad_dicom_clp", 0) >= 100000:
            docs.append(f"Comprobante de regularización o convenio de pago de las morosidades informadas {art(4)}.")
        if status == COMITE:
            docs.append("Estados financieros firmados por contador para la presentación al Comité de Crédito.")
        docs_md = "\n".join(f"{i}. {d}" for i, d in enumerate(docs, 1))

        return f"""### 1. Resumen de la Solicitud y Dictamen Preliminar
- **Empresa / RUT:** {empresa} ({rut})
- **Monto Solicitado:** {monto_txt}
- **Estado Preliminar:** **{status}**
- **Fundamento:** {dictamen}

### 2. Análisis y Fundamentación Normativa (Políticas RAG)
{sec2}

### 3. Estructura de Garantías y Cobertura Estatal
- **Garantía FOGAPE:** {fogape}
- **Garantías reales:** {real}

### 4. Producto Financiero Recomendado
- **Producto:** **{prod_name}** {sec(sec_n)}
- **Condiciones:** {prod_detail} {art(art_n)}.{prod_obs}

### 5. Próximos Pasos y Documentación Requerida
{docs_md}""".strip()


if __name__ == "__main__":
    agent = PymeAdvisorAgent()
    print("Iniciando Agente PYME-Advisor...")
    test_queries = [
        "Hola, represento a Transportes y Logistica Biobio SpA (RUT 76.123.456-K). Queremos solicitar 1.500 UF para comprar un nuevo camión de carga. ¿Cumplimos con las políticas del banco y cuánto dinero es en pesos?",
        "Hola, soy de Panaderia El Trigal (RUT 76.999.888-4) y necesitamos un crédito de 800 UF para capital de trabajo.",
        "Consulta general: ¿Cuáles son las condiciones para acceder a la garantía FOGAPE y qué porcentaje de cobertura tiene?",
    ]
    for q in test_queries:
        print("\n" + "=" * 70)
        print(f"QUERY: {q}")
        print("=" * 70)
        res = agent.process_query(q)
        print(res["response"])
        print("\n[Modo de generación]:", res["generation_mode"])
        print("[Herramientas ejecutadas]:", [t["tool"] + ":" + t["action"] for t in res["tools_executed"]])
        print("[Fragmentos recuperados]:", [f"{s['article']} ({s['similarity']:.2f})" for s in res["retrieved_sources"]])
        print("[Validación de citas]:", res["citation_validation"])
        print("[Tiempo de ejecución]:", res["execution_time_seconds"], "segundos")
