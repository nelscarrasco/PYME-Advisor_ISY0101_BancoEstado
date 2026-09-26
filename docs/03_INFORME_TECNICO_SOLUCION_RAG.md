> Versión Markdown del informe técnico. El documento oficial entregado es `docs/INFORME_TECNICO_SOLUCION_RAG.docx` (se genera con `python generate_report_docx.py`).

ISY0101 - INGENIERÍA DE SOLUCIONES CON IA | DUOC UC
EVALUACIÓN PARCIAL N°1 - ENCARGO

**PYME-Advisor: Agente con LLM y RAG para la Pre-Evaluación Crediticia de PYMEs en BancoEstado Microempresas**

Integrantes: Juan Serna, Bárbara Bustamante, Nelson Carrasco | Fecha: 25 de septiembre de 2026 | Repositorio: https://github.com/nelscarrasco/PYME-Advisor_ISY0101_BancoEstado


## 1. Análisis del Caso Organizacional y Requerimientos (IE1)
**Organización.** BancoEstado Microempresas es la filial de BancoEstado orientada al financiamiento de micro y pequeñas empresas en todo Chile, con productos de capital de trabajo, leasing y factoring y acceso a garantías estatales como FOGAPE. Las MiPymes superan 1,2 millones de empresas, representan el 98,5% de las empresas formales del país y concentran el 48% del empleo (Ministerio de Economía, Fomento y Turismo, 2026), por lo que la velocidad y consistencia con que se evalúa su acceso al crédito tiene impacto directo.

**Problema.** La pre-evaluación inicial de una solicitud exige que el ejecutivo cruce manualmente tres fuentes: (a) el manual interno de políticas de riesgo (antigüedad, morosidad, endeudamiento, garantías y atribuciones), (b) los antecedentes del cliente y (c) indicadores que cambian a diario, como la UF, en la que se expresan montos y tramos. Esto produce demoras, criterios dispares entre ejecutivos y errores de conversión UF–CLP. Un LLM genérico no resuelve el problema: desconoce las políticas internas, no conoce la UF del día y puede inventar requisitos.

**Alcance.** La organización es real, pero el Manual de Políticas de Crédito (11 artículos), el Catálogo de Productos (4 secciones) y la base de 5 clientes son documentos simulados construidos por el equipo; no son normativa oficial de BancoEstado.

**Requerimientos y objetivos medibles:**

- **R1 Dictamen preliminar trazable:** estado PRE-ADMISIBLE / NO ADMISIBLE / COMITÉ en menos de 2 s, sin emitir aprobaciones definitivas.
- **R2 Fidelidad normativa:** 100% de las citas del dictamen respaldadas por un fragmento recuperado del manual (meta mínima 95%).
- **R3 Datos externos vigentes:** conversión UF→CLP exacta con el valor del día obtenido por API, con continuidad si la API falla.
- **R4 Control de riesgo:** derivación automática al Comité en los supuestos del Art. 11 y respeto al secreto bancario y a la Ley 19.628 (sólo se envían al modelo los campos necesarios del cliente).

## 2. Formulación de Prompts (IE2)
El prompt se ensambla en src/agent/prompts.py en bloques ordenados: (1) system prompt con rol y reglas, (2) ejemplo few-shot de un dictamen completo, (3) memoria de sesión, (4) indicadores de la API, (5) perfil del cliente, (6) fragmentos RAG con fuente y relevancia, (7) resultado del motor de reglas y (8) la consulta. Extracto del system prompt:

```text
Eres "PYME-Advisor", Agente Consultor de Riesgo Crediticio de BancoEstado Microempresas.
1. FIDELIDAD: basa tus conclusiones EXCLUSIVAMENTE en el contexto provisto; PROHIBIDO inventar requisitos, plazos o montos.
   Si el caso no está en el manual: "debe elevarse a evaluación especial".
2. TRAZABILIDAD: toda afirmación normativa cita [Manual de Crédito, Art. X] o [Catálogo de Productos, Sección N].
3. DATOS EXTERNOS: convierte todo monto UF a CLP con el valor de la API y cita la fuente.
4. ESTADO: debe coincidir con el MOTOR DE REGLAS; explícalo, no lo recalcules. Nunca emitas aprobación definitiva.
5. FORMATO: 1) Dictamen 2) Fundamentación 3) Garantías/FOGAPE 4) Producto 5) Documentación.
```

**Justificación.** El rol fija el registro y el umbral de prudencia bancaria. Las restricciones negativas y la cláusula de escape ("elevar a evaluación especial") reducen el espacio de respuesta a lo que el contexto respalda. La cita obligatoria con formato fijo permite verificar automáticamente cada afirmación (sección 5). Entregar al modelo el resultado del motor de reglas evita que el LLM decida el estado crediticio, que es la parte con mayor riesgo regulatorio. El few-shot y la temperatura 0,1 estabilizan el formato de 5 secciones.


## 3. Diseño e Implementación del Pipeline RAG (IE3)
- **Fuentes internas:** Manual de Crédito y Catálogo (Markdown) segmentados por encabezado y artículo (chunker.py), generando 27 fragmentos con metadatos de fuente, título y artículo/sección; base de clientes JSON consultada por RUT (ClientLookupTool).
- **Fuente externa:** API pública mindicador.cl (valores del Banco Central de Chile) para UF, dólar y UTM (EconomicIndicatorsTool), con caché de 1 hora; si la API falla usa el último valor real guardado y, en último caso, valores de contingencia, informando siempre la fuente usada.
- **Índice y búsqueda:** TF-IDF con n-gramas 1–3 y similitud coseno (vector_store.py). La consulta se descompone en sub-consultas por dimensión de riesgo (segmento, antigüedad, morosidad, endeudamiento, FOGAPE, garantías, producto, documentos y comité), se recupera el top-1/2 de cada una y se unen sin duplicados.
![Figura 1](diagramas/flujo_rag.png)

*Figura 1. Flujo de información por consulta: herramientas internas y externas, motor de reglas, recuperación multi-consulta, generación y verificación.*


## 4. Arquitectura de la Solución (IE4)
![Figura 2](diagramas/arquitectura.png)

*Figura 2. Arquitectura por capas de PYME-Advisor (fuente editable: docs/diagramas/arquitectura.mmd).*

| Módulo | Archivo | Función en la arquitectura |
|---|---|---|
| Interfaz | app.py, web_server.py | CLI y dashboard FastAPI con panel de auditoría (herramientas, fragmentos, guardrail). |
| Orquestador | agent_core.py | Extrae RUT/monto, invoca herramientas, recupera, genera y verifica la salida. |
| Motor de reglas | policy_engine.py | Aplica los Art. 1, 3, 4, 5 y 11 y fija el estado preliminar de forma determinista. |
| Recuperación | chunker.py, vector_store.py | Segmentación por artículo e índice TF-IDF con búsqueda multi-consulta. |
| Herramientas | client_lookup.py, economic_indicators.py | Base interna de clientes y API de indicadores con caché y respaldo. |
| Contexto | context_manager.py | Memoria de sesión (5 turnos) y cliente activo para preguntas de seguimiento. |
| Generación | prompts.py + gpt-4o-mini | LLM si existe OPENAI_API_KEY; si no, motor de síntesis local que redacta sólo con artículos recuperados. |
| Guardrail de salida | agent_core.validate_citations | Marca toda cita sin fragmento de respaldo y corrige un estado que contradiga al motor de reglas. |


## 5. Evaluación, Decisiones de Diseño y Resultados (IE5)
La batería src/evaluation/evaluate_coherence.py ejecuta 7 casos con resultado esperado conocido y mide la coherencia entre los datos recuperados y la respuesta:

| Caso | Esperado = Obtenido | Artículos requeridos (recuperados) | Citas respaldadas |
|---|---|---|---|
| 1. Transportes Biobío, leasing 1.500 UF | PRE-ADMISIBLE | 3, 4, 5, 6, 9 (100%) | 100% |
| 2. Panadería El Trigal, 800 UF, DICOM $1,25 M | NO ADMISIBLE | 4 (100%) | 100% |
| 3. Constructora del Sur, leverage 3,4x, DSCR 1,1 | COMITÉ | 5, 11 (100%) | 100% |
| 4. Frutícola Express, 5 meses | NO ADMISIBLE | 3 (100%) | 100% |
| 5. TecnoAgro, capital de trabajo 600 UF | PRE-ADMISIBLE | 3, 4, 5, 6, 8 (100%) | 100% |
| 6. TecnoAgro, 12.000 UF | COMITÉ | 11 (100%) | 100% |
| 7. Consulta general FOGAPE | INFORMACIÓN GENERAL | 6 (100%) | 100% |

**Resultados:** precisión de dictamen 100%; recall de recuperación 100% frente a 17,1% de la línea base que busca sólo con la consulta original (top-3); groundedness de citas 100%; consistencia UF→CLP 100%; latencia bajo 0,3 s por consulta. Además, 17 pruebas unitarias (unittest) aprobadas. Logs y capturas en docs/evidencias.

| Decisión | Alternativa descartada | Justificación |
|---|---|---|
| Motor de reglas + LLM | Que el LLM decida el estado | La decisión crediticia debe ser auditable y reproducible; el LLM explica y el motor decide. |
| Descomposición en sub-consultas | Búsqueda única top-k | Una consulta cubre varias reglas; medido: recall 17,1% → 100%. |
| TF-IDF 1–3 gramas | Embeddings densos | Corpus pequeño y terminología exacta (DICOM, FOGAPE, UF); sin costo ni dependencia externa. Se revisará si crece el corpus. |
| Chunking por artículo | Ventanas fijas de caracteres | Una regla y su excepción quedan en el mismo fragmento y la cita al artículo es inequívoca. |
| Verificación de citas | Confiar en el prompt | El prompt no garantiza fidelidad; la verificación la mide y la hace visible al ejecutivo. |
| Caché + último valor real | Consultar la API siempre | Evita la latencia y la caída del servicio sin inventar valores. |

**Limitaciones:** las métricas se midieron con el motor de síntesis local (sin OPENAI_API_KEY); con el LLM activo la redacción no es determinista y debe re-evaluarse con la misma batería. Los puntajes de similitud TF-IDF son moderados (0,2–0,6). Los documentos y clientes son simulados.


## 6. Conclusiones y Reflexiones Individuales
**Conclusiones del proyecto:** La implementación de la arquitectura PYME-Advisor demuestra que la combinación de agentes inteligentes, pipelines RAG semánticos y consumo de herramientas en tiempo real resuelve integralmente las deficiencias de los modelos generativos puros en entornos corporativos de alta regulación. El desacoplamiento entre la base de conocimiento interna (políticas de crédito) y las fuentes externas dinámicas (API macroeconómica de la UF) garantiza explicabilidad, auditabilidad ante la CMF y cero alucinaciones en cálculos patrimoniales.

**Reflexión individual - Juan Serna:** Durante el desarrollo del proyecto, mi principal foco técnico fue estructurar la segmentación jerárquica de los documentos normativos de BancoEstado y validar el almacén vectorial. Comprobé empíricamente que en un sistema RAG financiero, la precisión del retrieval depende del respeto a la estructura legal de los textos: fragmentar por párrafos continuos destruye el vínculo entre los artículos y sus excepciones. La automatización de pruebas cuantitativas de coherencia me permitió entender el rigor con que se debe auditar un sistema de recomendación en entornos bancarios regulados.

**Reflexión individual - Bárbara Bustamante:** Mi participación se centró en la orquestación agéntica y la integración de la API externa de indicadores económicos en tiempo real. Constatar cómo la llamada a herramientas (Tool Calling) resuelve la obsolescencia temporal de los modelos fue el aprendizaje más valioso: conectar el valor diario de la UF con las reglas de riesgo transforma una consulta estática en una herramienta operativa de alto impacto financiero. Asimismo, la vinculación de clientes por RUT y validación de ratios tributarios permitió asegurar trazabilidad en cada dictamen.

**Reflexión individual - Nelson Carrasco:** Mi trabajo se concentró en la ingeniería de prompts, el diseño de guardrails negativos estrictos para evitar alucinaciones y la gestión de memoria conversacional. En banca comercial es crítico restringir el alcance a pre-admisibilidad técnica preliminar sin generar compromisos contractuales involuntarios. Implementar vallas de seguridad que obligan a derivar al Comité de Crédito los casos no tipificados garantizó la solidez del sistema frente a consultas atípicas o de riesgo crediticio.


## 7. Declaración de Uso de IA y Referencias (APA 7)
**Uso de IA:** conforme a las indicaciones de la evaluación, el equipo declara que utilizó Claude (Anthropic, 2026) para revisar la completitud del encargo frente a la pauta, corregir y ampliar el código (motor de reglas, recuperación multi-consulta, verificación de citas y evaluador), redactar y revisar este informe y el README, generar los diagramas y capturar la evidencia de pruebas. **[COMPLETAR: otras herramientas de IA usadas y para qué.]** Todo el contenido generado fue revisado y validado por el equipo. **[CONFIRMAR: las conclusiones y reflexiones individuales fueron redactadas por el equipo sin apoyo de IA.]**

Anthropic. (2026). Claude (versión Opus 5.5) [Modelo de lenguaje de gran tamaño]. https://claude.ai

Comisión para el Mercado Financiero. (s.f.). Recopilación Actualizada de Normas de Bancos (RAN). https://www.cmfchile.cl/portal/principal/613/w3-propertyvalue-29580.html

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. Advances in Neural Information Processing Systems, 33, 9459–9474.

mindicador.cl. (s.f.). API de indicadores económicos diarios en Chile. https://mindicador.cl

Ministerio de Economía, Fomento y Turismo. (2026). MiPymes y emprendimiento. https://www.economia.gob.cl/wp-content/uploads/2026/02/10-03-26-mipymes-y-emprendimiento.pdf

Shuster, K., Poff, S., Chen, M., Kiela, D., & Weston, J. (2021). Retrieval augmentation reduces hallucination in conversation. En Findings of the Association for Computational Linguistics: EMNLP 2021 (pp. 3784–3803).

Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. International Conference on Learning Representations (ICLR 2023).
