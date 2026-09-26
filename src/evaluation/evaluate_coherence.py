"""
Módulo de Evaluación de Coherencia entre Datos Recuperados y Respuestas (IE6).

Métricas calculadas por caso (y promediadas en la batería):
1. Precisión de dictamen: el estado preliminar coincide con el resultado esperado del caso.
2. Recall de recuperación (context recall): los artículos que el caso necesita aparecen
   entre los fragmentos recuperados del índice vectorial.
3. Recall de citas: la respuesta cita los artículos esperados.
4. Groundedness de citas: proporción de citas de la respuesta que están respaldadas por un
   fragmento efectivamente recuperado (una cita sin respaldo cuenta como posible alucinación).
5. Consistencia matemática: el monto en CLP informado es igual a monto_UF × UF de la herramienta.
6. Latencia media por consulta.
Además se compara el recall de recuperación contra una línea base que busca sólo con la
consulta original (top-3), para medir el aporte de la descomposición en sub-consultas.
"""

import re
from typing import Dict, Any, List
from src.agent.agent_core import PymeAdvisorAgent


def _num(s: str) -> str:
    m = re.search(r"\d+", s)
    return m.group(0) if m else s


class RAGCoherenceEvaluator:
    def __init__(self, agent: PymeAdvisorAgent = None):
        self.agent = agent or PymeAdvisorAgent()

    TEST_CASES: List[Dict[str, Any]] = [
        {"name": "Caso 1: Leasing de camión, cliente solvente (Transportes Biobío)",
         "query": "Represento a Transportes y Logistica Biobio SpA (RUT 76.123.456-K). Queremos 1.500 UF para renovar un camión tolva. ¿Calificamos y cuánto es en pesos?",
         "expected_status": "PRE-ADMISIBLE", "expected_articles": ["3", "4", "5", "6", "9"], "monto_uf": 1500},
        {"name": "Caso 2: Morosidad DICOM sobre $500.000 (Panadería El Trigal)",
         "query": "Panaderia y Alimentos El Trigal EIRL (RUT 76.999.888-4) solicita crédito de 800 UF para capital de trabajo.",
         "expected_status": "NO ADMISIBLE", "expected_articles": ["4"], "monto_uf": 800},
        {"name": "Caso 3: Leverage 3,4x y DSCR 1,1 (Constructora del Sur)",
         "query": "Constructora del Sur SA (RUT 76.543.210-8) solicita ampliación de línea de 4.000 UF.",
         "expected_status": "DERIVACIÓN A COMITÉ ESPECIAL", "expected_articles": ["5", "11"], "monto_uf": 4000},
        {"name": "Caso 4: Antigüedad de 5 meses (Frutícola Express)",
         "query": "Comercializadora Fruticola Express SpA (RUT 78.111.222-1) solicita 500 UF de crédito de capital de trabajo.",
         "expected_status": "NO ADMISIBLE", "expected_articles": ["3"], "monto_uf": 500},
        {"name": "Caso 5: Capital de trabajo, cliente que cumple (TecnoAgro)",
         "query": "TecnoAgro Sustentable Ltda (RUT 77.987.654-3) necesita 600 UF de capital de trabajo para comprar insumos.",
         "expected_status": "PRE-ADMISIBLE", "expected_articles": ["3", "4", "5", "6", "8"], "monto_uf": 600},
        {"name": "Caso 6: Monto sobre 10.000 UF (TecnoAgro)",
         "query": "TecnoAgro Sustentable Ltda (RUT 77.987.654-3) solicita 12.000 UF de capital de trabajo.",
         "expected_status": "DERIVACIÓN A COMITÉ ESPECIAL", "expected_articles": ["11"], "monto_uf": 12000},
        {"name": "Caso 7: Consulta general sobre FOGAPE (sin cliente)",
         "query": "¿Qué requisitos y coberturas tiene la garantía FOGAPE para las PYMEs?",
         "expected_status": "INFORMACIÓN GENERAL", "expected_articles": ["6"], "monto_uf": None},
    ]

    def evaluate_response(self, case: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        text = result["response"]
        expected = set(case["expected_articles"])

        retrieved = {_num(s["article"]) for s in result["retrieved_sources"] if "Art" in (s["article"] or "")}
        validation = result["citation_validation"]
        cited = {_num(c) for c in validation["cited"] if c.startswith("Art")}

        context_recall = len(expected & retrieved) / len(expected)
        citation_recall = len(expected & cited) / len(expected)

        math_ok = True
        if case["monto_uf"] is not None:
            uf = result["economic_indicators_applied"]["uf_clp"]
            expected_clp = round(case["monto_uf"] * uf)
            found = [int(x.replace(".", "")) for x in re.findall(r"\$([\d\.]+) CLP", text)]
            math_ok = any(abs(v - expected_clp) <= 1 for v in found)

        return {
            "test_case_name": case["name"],
            "expected_status": case["expected_status"],
            "obtained_status": result["policy_status"],
            "status_correct": result["policy_status"] == case["expected_status"] and case["expected_status"] in text,
            "expected_articles": sorted(expected, key=int),
            "retrieved_articles": sorted(retrieved, key=int),
            "cited_citations": validation["cited"],
            "unsupported_citations": validation["unsupported"],
            "context_recall": round(context_recall, 3),
            "citation_recall": round(citation_recall, 3),
            "groundedness": validation["grounded_ratio"],
            "math_consistent": math_ok,
            "baseline_context_recall": round(len(expected & {_num(c["article"]) for c in self.agent.vector_store.search(case["query"], top_k=3) if "Art" in c["article"]}) / len(expected), 3),
            "top_similarity": max((s["similarity"] for s in result["retrieved_sources"]), default=0.0),
            "execution_time_s": result["execution_time_seconds"],
            "generation_mode": result["generation_mode"],
        }

    def run_benchmark_suite(self) -> Dict[str, Any]:
        results = []
        for case in self.TEST_CASES:
            self.agent.context_manager.clear()
            results.append(self.evaluate_response(case, self.agent.process_query(case["query"])))

        n = len(results)
        avg = lambda k: sum(r[k] for r in results) / n
        return {
            "total_evaluated_cases": n,
            "generation_mode": results[0]["generation_mode"],
            "overall_status_accuracy": f"{avg('status_correct')*100:.1f}%",
            "context_recall": f"{avg('context_recall')*100:.1f}%",
            "baseline_context_recall": f"{avg('baseline_context_recall')*100:.1f}%",
            "citation_recall": f"{avg('citation_recall')*100:.1f}%",
            "average_groundedness_score": f"{avg('groundedness')*100:.1f}%",
            "math_consistency_rate": f"{avg('math_consistent')*100:.1f}%",
            "average_latency_seconds": f"{avg('execution_time_s'):.3f}s",
            "detailed_case_results": results,
        }


if __name__ == "__main__":
    evaluator = RAGCoherenceEvaluator()
    print("Iniciando batería de evaluación de coherencia RAG (IE6)...")
    report = evaluator.run_benchmark_suite()
    print("\n" + "=" * 72)
    print("RESUMEN DE COHERENCIA ENTRE DATOS RECUPERADOS Y RESPUESTAS (IE6)")
    print("=" * 72)
    print(f"Casos evaluados:                    {report['total_evaluated_cases']}")
    print(f"Modo de generación:                 {report['generation_mode']}")
    print(f"Precisión de dictamen:              {report['overall_status_accuracy']}")
    print(f"Recall de recuperación (contexto):  {report['context_recall']}")
    print(f"  (línea base: sólo consulta original, top-3: {report['baseline_context_recall']})")
    print(f"Recall de citas esperadas:          {report['citation_recall']}")
    print(f"Groundedness de citas:              {report['average_groundedness_score']}")
    print(f"Consistencia matemática UF→CLP:     {report['math_consistency_rate']}")
    print(f"Latencia media por consulta:        {report['average_latency_seconds']}")
    print("\nDetalle por caso:")
    for r in report["detailed_case_results"]:
        print(f"\n* {r['test_case_name']}")
        print(f"  - Estado esperado/obtenido: {r['expected_status']} / {r['obtained_status']} -> {'OK' if r['status_correct'] else 'ERROR'}")
        print(f"  - Artículos esperados: {r['expected_articles']} | recuperados: {r['retrieved_articles']}")
        print(f"  - Recall recuperación: {r['context_recall']*100:.0f}% | Recall citas: {r['citation_recall']*100:.0f}% | Groundedness: {r['groundedness']*100:.0f}%")
        print(f"  - Citas sin respaldo: {r['unsupported_citations'] or 'ninguna'} | UF→CLP consistente: {r['math_consistent']} | Similitud máx.: {r['top_similarity']:.2f}")
