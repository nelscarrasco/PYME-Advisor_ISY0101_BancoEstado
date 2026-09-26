"""
Aplicación Principal / Interfaz Interactiva de Consola (CLI).
Permite interactuar con el agente PYME-Advisor, ejecutar casos de prueba preconfigurados
o realizar consultas en lenguaje natural en tiempo real.
"""

import sys
import os
import json
from src.agent.agent_core import PymeAdvisorAgent
from src.tools.economic_indicators import EconomicIndicatorsTool

def print_banner():
    print("""
================================================================================
   BANCOESTADO MICROEMPRESAS & PYME - SISTEMA AGÉNTICO RAG INTELIGENTE
               "PYME-Advisor: Asesor de Crédito y Garantías"
   ISY0101 Ingeniería de Soluciones con IA | Duoc UC
   Integrantes: Juan Serna, Bárbara Bustamante, Nelson Carrasco
================================================================================
  * RAG Interno: Manual de Crédito 2026 + Catálogo de Productos
  * Integración Externa: API pública mindicador.cl (UF, Dólar, UTM)
  * Control de Contexto: Historial de sesión y verificación de reglas duras
================================================================================
""")

def print_menu():
    print("""
Seleccione una opción:
  [1] Consulta Rápida: Transportes Biobío (Leasing 1.500 UF - Caso Admisible)
  [2] Consulta Rápida: Panadería El Trigal (Capital de Trabajo - Rechazo DICOM)
  [3] Consulta Rápida: Constructora del Sur (4.000 UF - Derivación a Comité Art. 11)
  [4] Consulta Rápida: Consulta Normativa abierta sobre subsidios FOGAPE
  [5] Escribir una consulta personalizada en lenguaje natural
  [6] Ejecutar Batería de Pruebas de Coherencia RAG (7 casos, Métricas IE6)
  [7] Salir
""")

def run_cli():
    print_banner()
    agent = PymeAdvisorAgent()
    econ_tool = EconomicIndicatorsTool()
    ind = econ_tool.get_indicators()

    print(f"-> Indicadores económicos ({ind.get('fuente', 'mindicador.cl')}):")
    print(f"   UF: ${ind['uf']['valor']:,.2f} CLP | Dólar: ${ind['dolar']['valor']:,.2f} CLP | UTM: ${ind['utm']['valor']:,.2f} CLP\n")

    while True:
        print_menu()
        choice = input("Ingrese número de opción (1-7): ").strip()

        if choice == "1":
            q = "Hola, represento a Transportes y Logistica Biobio SpA (RUT 76.123.456-K). Queremos solicitar 1.500 UF para renovar un camión tolva. ¿Calificamos y cuánto es en pesos?"
        elif choice == "2":
            q = "Hola, soy de Panaderia y Alimentos El Trigal EIRL (RUT 76.999.888-4) y necesitamos 800 UF para capital de trabajo."
        elif choice == "3":
            q = "Constructora del Sur SA (RUT 76.543.210-8) solicita ampliación de línea de crédito de 4.000 UF para compra de terreno."
        elif choice == "4":
            q = "¿Cuáles son las condiciones y porcentajes de cobertura del fondo de garantía estatal FOGAPE para las PYMEs?"
        elif choice == "5":
            q = input("\nEscriba su consulta para el agente: ").strip()
            if not q:
                continue
        elif choice == "6":
            from src.evaluation.evaluate_coherence import RAGCoherenceEvaluator
            evaluator = RAGCoherenceEvaluator(agent)
            print("\nEjecutando evaluación cuantitativa de coherencia...")
            summary = evaluator.run_benchmark_suite()
            print("\n" + "="*60)
            print("RESULTADOS DE EVALUACIÓN DE COHERENCIA Y FIDELIDAD (IE6)")
            print("="*60)
            print(f"Precisión de Dictamen:            {summary['overall_status_accuracy']}")
            print(f"Recall de Recuperación:            {summary['context_recall']} (línea base {summary['baseline_context_recall']})")
            print(f"Recall de Citas Esperadas:         {summary['citation_recall']}")
            print(f"Groundedness de Citas:             {summary['average_groundedness_score']}")
            print(f"Consistencia Matemática (UF/CLP): {summary['math_consistency_rate']}")
            print(f"Latencia Media de Inferencia:      {summary['average_latency_seconds']}")
            continue
        elif choice == "7":
            print("\nFinalizando sesión. ¡Hasta pronto!")
            break
        else:
            print("Opción no válida. Intente nuevamente.")
            continue

        print("\n" + "-"*70)
        print(f"PROCESANDO CONSULTA: '{q}'")
        print("-"*70)

        result = agent.process_query(q)

        print("\n" + result["response"])
        print("\n" + "."*70)
        print(f"[METADATOS DEL AGENTE]")
        print(f"-> Cliente Detectado: {result.get('client_identified')} (RUT: {result.get('client_rut')})")
        print(f"-> UF Utilizada: ${result['economic_indicators_applied']['uf_clp']:,.2f} CLP")
        print(f"-> Fuentes RAG Recuperadas:")
        for s in result["retrieved_sources"]:
            print(f"   * [{s['article']}] {s['heading']} (Relevancia: {s['similarity']*100:.1f}%)")
        print(f"-> Herramientas Ejecutadas: {', '.join(t['tool'] for t in result['tools_executed'])}")
        print(f"-> Modo de Generación: {result['generation_mode']}")
        v = result["citation_validation"]
        print(f"-> Guardrail de Citas: {len(v['supported'])}/{len(v['cited'])} citas respaldadas por fragmentos recuperados")
        print(f"-> Tiempo de Ejecución: {result['execution_time_seconds']}s")
        print("."*70 + "\n")

if __name__ == "__main__":
    run_cli()
