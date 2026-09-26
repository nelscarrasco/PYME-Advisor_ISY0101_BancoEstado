# Evidencia de pruebas de software

Evidencia generada el 25-09-2026 ejecutando los comandos del README principal.

| Archivo | Comando | Qué demuestra |
|---|---|---|
| `01_pruebas_unitarias.txt` | `python -m unittest discover tests -v` | 17 pruebas unitarias y de integración (RAG, herramientas, motor de reglas, guardrails de citas): **OK** |
| `02_benchmark_coherencia_IE6.txt` | `python -m src.evaluation.evaluate_coherence` | Batería de 7 casos: precisión de dictamen, recall de recuperación (vs. línea base), recall de citas, groundedness de citas y consistencia UF→CLP |
| `03_demo_agente_3_consultas.txt` | `python -m src.agent.agent_core` | Salida completa del agente para 3 consultas (pre-admisible, no admisible, consulta general) |
| `04_dashboard_inicio.png` | `python web_server.py` | Dashboard web al iniciar (indicadores UF/Dólar/UTM) |
| `05_dashboard_caso1_preadmisible.png` | Botón "Caso 1" | Dictamen pre-admisible + panel de auditoría (herramientas, modo de generación, guardrail de citas y fragmentos recuperados por sub-consulta) |
| `06_dashboard_caso2_no_admisible.png` | Botón "Caso 2" | Rechazo por morosidad DICOM citando Art. 4 |
| `07_dashboard_benchmark.png` | Botón "Ejecutar Batería" | Métricas IE6 desde la interfaz |

**Nota de trazabilidad:** estas ejecuciones se hicieron en un entorno sin acceso de red a `mindicador.cl`. Por eso la herramienta usó el **último valor real guardado en caché** (UF $41.016,28 del 25-09-2026, obtenido previamente de la API) y lo informó como fuente: `mindicador.cl (último valor en caché, 2026-09-25; API sin conexión)`. Con conexión a internet, la herramienta consulta la API en vivo y actualiza `src/tools/indicators_cache.json`.

Las pruebas se ejecutaron sin `OPENAI_API_KEY`, es decir, con el motor de síntesis local.
