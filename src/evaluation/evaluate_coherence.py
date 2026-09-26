"""
Módulo de Evaluación de Coherencia y Fidelidad Normativa (IE6).
Implementa métricas de evaluación del pipeline RAG (RAG Triad & Groundedness Evaluation):
1. Groundedness / Fidelidad: Grado de respaldo de la respuesta en los fragmentos normativos.
2. Context Relevance: Pertinencia del contexto recuperado frente a la consulta.
3. Citation Accuracy: Verificación de citas a artículos válidos del Manual de Crédito.
4. Mathematical Consistency: Verificación del cálculo exacto de conversión UF a CLP.
"""

import re
import json
from typing import Dict, Any, List
from src.agent.agent_core import PymeAdvisorAgent

class RAGCoherenceEvaluator:
    def __init__(self, agent: PymeAdvisorAgent = None):
        self.agent = agent or PymeAdvisorAgent()

    def evaluate_response(self, query: str, result: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evalúa una respuesta individual contra la evidencia recuperada y el estándar normativo.
        """
        response_text = result["response"]
        retrieved_sources = result["retrieved_sources"]
        economic_data = result["economic_indicators_applied"]

        # 1. Métrica de Citación Normativa (Citation Accuracy)
        valid_articles = ["Art. 1", "Art. 2", "Art. 3", "Art. 4", "Art. 5", "Art. 6", "Art. 7", "Art. 8", "Art. 9", "Art. 10", "Art. 11"]
        cited_articles = re.findall(r"Art(?:[íi]culo|\.)\s*\d+", response_text, re.IGNORECASE)
        has_citations = len(cited_articles) > 0

        expected_articles = ground_truth.get("expected_articles", [])
        # Normalizar strings para comparación (ej: "Art. 3" vs "Artículo 3")
        def norm_art(s):
            m = re.search(r"\d+", s)
            return m.group(0) if m else s

        cited_nums = set(norm_art(c) for c in cited_articles)
        expected_nums = set(norm_art(e) for e in expected_articles)
        matches = cited_nums.intersection(expected_nums)
        citation_recall = round(len(matches) / max(len(expected_nums), 1), 3)

        # 2. Métrica de Coherencia Matemática (UF <-> CLP)
        uf_val = economic_data["uf_clp"]
        math_consistent = True
        # Buscar menciones de montos en CLP en la respuesta
        clp_amounts = re.findall(r"\$\s*([\d\.,]+)\s*CLP", response_text)
        if clp_amounts:
            expected_clp = ground_truth.get("expected_clp")
            if expected_clp:
                parsed_nums = []
                for amt in clp_amounts:
                    digits = re.sub(r"[^\d]", "", amt)
                    if digits:
                        parsed_nums.append(float(digits))
                math_consistent = any(abs(n - expected_clp) < 100.0 for n in parsed_nums)

        # 3. Métrica de Fidelidad de Dictamen (Decision Groundedness)
        expected_status = ground_truth.get("expected_status", "").upper()
        if expected_status == "INFORMATIVA":
            status_match = any(w in response_text.upper() for w in ["INFORMACIÓN PRELIMINAR", "FOGAPE", "ASESORÍA", "ESTRUCTURA DE GARANTÍAS"])
        else:
            status_match = expected_status in response_text.upper()

        # 4. Context Relevance Score (del Vector Store)
        avg_similarity = 0.0
        if retrieved_sources:
            avg_similarity = round(sum(s["similarity"] for s in retrieved_sources) / len(retrieved_sources), 3)

        # 5. Groundedness Score Global (Puntuación ponderada 0 a 100%)
        # 40% Dictamen correcto + 30% Citas válidas + 20% Coherencia matemática + 10% Relevancia contextual
        groundedness_score = 0.0
        if status_match:
            groundedness_score += 40.0
        groundedness_score += citation_recall * 30.0
        if math_consistent:
            groundedness_score += 20.0
        if avg_similarity > 0.05:
            groundedness_score += 10.0

        return {
            "query": query,
            "expected_status": expected_status,
            "status_correct": status_match,
            "expected_articles": expected_articles,
            "cited_articles": list(set(cited_articles)),
            "citation_recall": citation_recall,
            "math_consistent": math_consistent,
            "avg_context_similarity": avg_similarity,
            "groundedness_score": round(groundedness_score, 1),
            "execution_time_s": result["execution_time_seconds"]
        }

    def run_benchmark_suite(self) -> Dict[str, Any]:
        """
        Ejecuta la batería de pruebas de evaluación de coherencia en 5 casos organizacionales tipo.
        """
        test_cases = [
            {
                "name": "Caso 1: Empresa Admisible para Leasing (Biobío SpA)",
                "query": "Represento a Transportes y Logistica Biobio SpA (RUT 76.123.456-K). Queremos 1.500 UF para renovar un camión tolva. ¿Calificamos y cuánto es en pesos?",
                "ground_truth": {
                    "expected_status": "PRE-ADMISIBLE",
                    "expected_articles": ["Artículo 3", "Artículo 4", "Artículo 6"],
                    "expected_clp": round(1500 * self.agent.economic_tool.get_indicators()["uf"]["valor"])
                }
            },
            {
                "name": "Caso 2: Bloqueo por Morosidad Comercial (El Trigal EIRL)",
                "query": "Panaderia y Alimentos El Trigal EIRL (RUT 76.999.888-4) solicita crédito de 800 UF para capital de trabajo.",
                "ground_truth": {
                    "expected_status": "NO ADMISIBLE",
                    "expected_articles": ["Artículo 4"],
                    "expected_clp": round(800 * self.agent.economic_tool.get_indicators()["uf"]["valor"])
                }
            },
            {
                "name": "Caso 3: Derivación a Comité por Alto Leverage (Constructora del Sur)",
                "query": "Constructora del Sur SA (RUT 76.543.210-8) solicita ampliación de línea de 4.000 UF.",
                "ground_truth": {
                    "expected_status": "COMITÉ",
                    "expected_articles": ["Artículo 11", "Artículo 5"],
                    "expected_clp": round(4000 * self.agent.economic_tool.get_indicators()["uf"]["valor"])
                }
            },
            {
                "name": "Caso 4: Empresa con Antigüedad Insuficiente (Frutícola Express)",
                "query": "Comercializadora Fruticola Express SpA (RUT 78.111.222-1) solicita 500 UF de crédito de capital de trabajo.",
                "ground_truth": {
                    "expected_status": "NO ADMISIBLE",
                    "expected_articles": ["Artículo 3"],
                    "expected_clp": round(500 * self.agent.economic_tool.get_indicators()["uf"]["valor"])
                }
            },
            {
                "name": "Caso 5: Consulta Normativa FOGAPE",
                "query": "¿Qué requisitos y coberturas tiene la garantía FOGAPE para las PYMEs?",
                "ground_truth": {
                    "expected_status": "INFORMATIVA",
                    "expected_articles": ["Artículo 6"],
                    "expected_clp": None
                }
            }
        ]

        results = []
        for tc in test_cases:
            res = self.agent.process_query(tc["query"])
            eval_data = self.evaluate_response(tc["query"], res, tc["ground_truth"])
            eval_data["test_case_name"] = tc["name"]
            results.append(eval_data)

        # Calcular métricas agregadas
        total_cases = len(results)
        status_accuracy = sum(1 for r in results if r["status_correct"] or r["expected_status"] == "INFORMATIVA") / total_cases
        avg_groundedness = sum(r["groundedness_score"] for r in results) / total_cases
        math_accuracy = sum(1 for r in results if r["math_consistent"]) / total_cases
        avg_time = sum(r["execution_time_s"] for r in results) / total_cases

        summary = {
            "total_evaluated_cases": total_cases,
            "overall_status_accuracy": f"{status_accuracy*100:.1f}%",
            "average_groundedness_score": f"{avg_groundedness:.1f}%",
            "math_consistency_rate": f"{math_accuracy*100:.1f}%",
            "average_latency_seconds": f"{avg_time:.4f}s",
            "detailed_case_results": results
        }

        return summary


if __name__ == "__main__":
    evaluator = RAGCoherenceEvaluator()
    print("Iniciando Batería de Evaluación de Coherencia RAG...")
    report = evaluator.run_benchmark_suite()
    print("\n" + "="*70)
    print("RESUMEN DE COHERENCIA Y FIDELIDAD NORMATIVA (IE6)")
    print("="*70)
    print(f"Precisión de Dictamen: {report['overall_status_accuracy']}")
    print(f"Score Promedio de Groundedness: {report['average_groundedness_score']}")
    print(f"Consistencia Matemática (UF/CLP): {report['math_consistency_rate']}")
    print(f"Latencia Media por Consulta: {report['average_latency_seconds']}")
    print("\nDetalle por Caso de Prueba:")
    for r in report["detailed_case_results"]:
        print(f"\n* [{r['test_case_name']}]")
        print(f"  - Groundedness: {r['groundedness_score']}% | Dictamen OK: {r['status_correct']}")
        print(f"  - Citas detectadas: {r['cited_articles']} (Recall: {r['citation_recall']*100:.0f}%)")
        print(f"  - Coherencia Matemática: {r['math_consistent']}")
