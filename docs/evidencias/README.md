# Evidencia de pruebas de software

Evidencia generada el 25-09-2026 ejecutando los comandos del README principal.

| Archivo | Comando | Qué demuestra |
|---|---|---|
| `01_pruebas_unitarias.txt` | `python -m unittest discover tests -v` | 11 pruebas unitarias y de integración (RAG, herramientas, reglas del agente): **OK** |
| `02_benchmark_coherencia_IE6.txt` | `python -m src.evaluation.evaluate_coherence` | Benchmark de 5 casos: precisión de dictamen, groundedness, recall de citas y consistencia UF→CLP |
| `03_demo_agente_3_consultas.txt` | `python -m src.agent.agent_core` | Salida completa del agente para 3 consultas (pre-admisible, no admisible, consulta general) |
| `04_dashboard_inicio.png` | `python web_server.py` | Dashboard web al iniciar (indicadores UF/Dólar/UTM) |
| `05_dashboard_caso1_preadmisible.png` | Botón "Caso 1" | Dictamen pre-admisible + panel de auditoría (herramientas ejecutadas y fragmentos RAG recuperados) |
| `06_dashboard_caso2_no_admisible.png` | Botón "Caso 2" | Rechazo por morosidad DICOM citando Art. 4 |
| `07_dashboard_benchmark.png` | Botón "Re-ejecutar batería" | Métricas IE6 desde la interfaz |

**Nota de trazabilidad:** estas ejecuciones se hicieron en un entorno sin acceso de red a `mindicador.cl`, por lo que la herramienta usó los **valores de contingencia** (UF $41.008,10 del 24-09-2026) y lo informó con el aviso `[Aviso] No se pudo conectar a la API en vivo`. Con conexión a internet la herramienta consulta la API en vivo y guarda el resultado en `src/tools/indicators_cache.json` (ejemplo real guardado: UF $41.016,28 del 25-09-2026).

Las pruebas se ejecutaron sin `OPENAI_API_KEY`, es decir, con el motor de síntesis local.
