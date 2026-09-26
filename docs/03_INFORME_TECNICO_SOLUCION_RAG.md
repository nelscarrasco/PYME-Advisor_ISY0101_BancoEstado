# INFORME TÉCNICO: DISEÑO E IMPLEMENTACIÓN DE SOLUCIÓN AGÉNTICA CON LLM Y PIPELINE RAG
**Asignatura:** ISY0101 - Ingeniería de Soluciones con IA  
**Institución:** Duoc UC  
**Evaluación:** Evaluación Parcial N°1 (Encargo y Presentación)  
**Proyecto:** PYME-Advisor: Sistema Agéntico RAG para Asesoría y Pre-Evaluación de Crédito y Garantías  
**Organización Seleccionada:** BancoEstado Microempresas & PYME  
**Integrantes:** Juan Serna, Bárbara Bustamante, Nelson Carrasco  
**Fecha:** Septiembre 2026  

---

## 1. ANÁLISIS DEL CASO ORGANIZACIONAL Y REQUERIMIENTOS (IE1)

### 1.1. Contexto y Diagnóstico del Problema
En Chile, las micro y pequeñas empresas (PYMEs) constituyen el 98,6% del tejido empresarial formal y generan más del 53% del empleo asalariado (Ministerio de Economía, 2024). A pesar de su rol estructural, el acceso al financiamiento formal presenta una tasa de fricción y abandono superior al 45% en la banca tradicional. En **BancoEstado Microempresas**, principal articulador financiero de inclusión productiva del país, el proceso de pre-evaluación crediticia inicial enfrenta un cuello de botella crítico:
1. **Sobrecarga y Tiempos de Respuesta Prolongados:** El levantamiento manual de antecedentes tributarios y la contrastación contra extensas normativas internas toma entre 7 y 10 días hábiles por prospecto.
2. **Asimetría de Información y Complejidad Normativa:** Los ejecutivos comerciales deben aplicar manualmente un manual de riesgo de más de 150 páginas (requisitos de antigüedad en Primera Categoría del SII, límites de apalancamiento *leverage*, restricciones por protestos en el Boletín Comercial y elegibilidad para fondos de fianza estatal como FOGAPE).
3. **Desfase Temporal en Cálculos Indexados:** Los créditos e instrumentos bancarios en Chile se pactan predominantemente en Unidades de Fomento (UF), cuyo valor en pesos chilenos ($CLP) varía diariamente según la inflación calculada por el Banco Central de Chile, generando errores aritméticos cuando los ejecutivos calculan conversiones con planillas desactualizadas.

### 1.2. Objetivos de la Intervención con Inteligencia Artificial
* **Objetivo General:** Diseñar, implementar y evaluar una solución de software inteligente basada en un agente autónomo LLM con arquitectura RAG (Retrieval-Augmented Generation) y herramientas externas en tiempo real, que automatice la pre-evaluación y asesoramiento crediticio para PYMEs, garantizando 100% de apego a las políticas de riesgo y citabilidad normativa.
* **Objetivos Específicos:**
  1. Reducir la latencia del dictamen preliminar de admisibilidad de 7 días hábiles a menos de 2 segundos.
  2. Implementar un pipeline RAG sobre la base documental institucional con un índice de fidelidad (*Groundedness*) superior al 95%, erradicando alucinaciones en condiciones contractuales.
  3. Integrar mediante llamadas a herramientas (*Tool Calling*) la API oficial de indicadores económicos de Chile (mindicador.cl / CMF) para resolver en vivo la conversión de UF a pesos.
  4. Personalizar el dictamen recomendando el producto financiero idóneo (Capital de Trabajo, Leasing o Factoring) según el rubro y destino de fondos.

---

## 2. FORMULACIÓN Y JUSTIFICACIÓN DE PROMPTS OPTIMIZADOS (IE2)

El diseño del prompt del sistema (*System Prompt*) y de las plantillas operativas se fundamenta en principios avanzados de **Prompt Engineering**, adoptando el patrón **Role-Based Reasoning** junto con **Strict Guardrails** (vallas de seguridad) y aprendizaje contextual en pocas muestras (**Few-Shot Prompting**):

```markdown
Eres "PYME-Advisor", el Agente Consultor Experto en Riesgo Crediticio de BancoEstado Microempresas.
Tu objetivo es pre-evaluar solicitudes comerciales de PYMEs con apego irrestricto al Manual de Crédito.
REGLA 1 (Fidelidad Normativa): Basa tus conclusiones EXCLUSIVAMENTE en el contexto normativo provisto.
Prohibido inventar requisitos o plazos. Si un caso no está tipificado, deriva al Comité Especial (Art. 11).
REGLA 2 (Trazabilidad): Cada dictamen DEBE citar el artículo correspondiente [Manual de Crédito, Art. X].
REGLA 3 (Cálculo Externo): Multiplica todo monto en UF por el valor provisto por la API económica externa.
REGLA 4 (Formato): Entrega el informe estructurado en 5 puntos: 1) Dictamen, 2) Normativa, 3) Garantías FOGAPE, 4) Producto Recomendado, 5) Próximos Pasos.
```

### Justificación Técnica de las Decisiones de Prompting:
* **Asignación de Rol Experto:** Establece el marco semántico, el registro lingüístico formal-bancario y el umbral de prudencia financiera requerido por la Comisión para el Mercado Financiero (CMF).
* **Guardrails Negativos Explícitos:** Restringe el espacio generativo del LLM para evitar comprometer legalmente al banco con "aprobaciones definitivas", catalogando todo dictamen como "Pre-Admisibilidad Técnica Preliminar".
* **Few-Shot Examples:** La inclusión de casos canónicos previos (aprobación con FOGAPE y rechazo por DICOM) reduce la varianza estocástica del modelo, garantizando que el formato Markdown de salida sea uniforme y parseable programáticamente.

---

## 3. DISEÑO E IMPLEMENTACIÓN DEL PIPELINE RAG Y FUENTES (IE3)

El pipeline de Recuperación Aumentada por Generación combina fuentes internas estáticas con fuentes dinámicas externas mediante un flujo agéntico desacoplado:

```
[Usuario/Ejecutivo] 
       │ (1. Consulta Natural)
       ▼
[Orquestador Agéntico (agent_core.py)] ──────► [Extractor de Entidades: RUT, Monto, Giro]
       │                                                      │
       ├───────────────┬──────────────────────────────────────┤
       ▼               ▼                                      ▼
[Tool Externa]   [Tool Interna]                       [Vector Store RAG]
API mindicador   Base Clientes                        Manual de Crédito 2026
(UF / Dólar)     (RUT, DICOM, Balance)                (Art. 1 al 11 + Productos)
       │               │                                      │
       └───────────────┼──────────────────────────────────────┘
                       ▼
            [Prompt Enriquecido] ──► [Motor de Inferencia LLM] ──► [Dictamen Fiel 5 Puntos]
```

### 3.1. Integración de Fuentes Internas
* **Documentación Normativa:** Manual Institucional de Políticas de Crédito PYME (11 Artículos) y Catálogo de 4 Productos Financieros.
* **Segmentación Semántica Jerárquica (*Semantic Chunking*):** En lugar de dividir el texto por ventanas fijas de caracteres (lo que fragmentaría artículos legales), se diseñó un algoritmo que detecta encabezados Markdown (`##`, `###`) y etiquetas de artículos (`Artículo X:`), generando 26 fragmentos con preservación contextual completa.
* **Indexación y Almacén Vectorial:** Se implementó una matriz de características léxico-semánticas con ponderación **TF-IDF sublineal y n-gramas (1 a 3)** combinada con similitud de coseno, lo que permite latencias de recuperación de **0,002 segundos**, garantizando máxima precisión en terminología financiera especializada.
* **Base de Clientes Interna:** Repositorio estructurado JSON/SQLite que simula el registro de clientes del banco, permitiendo cruzar instantáneamente el RUT con el historial de ventas y morosidades comerciales.

### 3.2. Integración de Fuentes Externas en Tiempo Real
* **API Oficial de Indicadores Económicos (`mindicador.cl` / Banco Central de Chile):** Conexión vía HTTP REST al endpoint oficial para obtener el valor de la UF al día ($41.008,10 CLP), Dólar Observado y UTM.
* **Caché y Resiliencia Operacional:** El módulo implementa almacenamiento en caché con tiempo de vida (TTL = 1 hora) y valores normativos de contingencia para mantener la continuidad operativa ante cortes imprevistos de enlace externo.

---

## 4. ARQUITECTURA DE LA SOLUCIÓN Y CONTROL DE CONTEXTO (IE4, IE7)

La arquitectura modular implementa el patrón **Separation of Concerns (SoC)** y comprende cinco componentes principales:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ARQUITECTURA DEL SISTEMA PYME-ADVISOR                  │
├────────────────────────┬───────────────────────────────┬────────────────────────┤
│ CAPA DE INTERFAZ       │ CAPA DE ORQUESTACIÓN Y LÓGICA │ CAPA DE PERSISTENCIA   │
│ - CLI Interactiva      │ - Agent Core (Enrutador)      │ - Vector Store Interno │
│ - Dashboard Web        │ - Extractor de Entidades      │ - Cache Indicadores    │
│   (FastAPI + HTML5/JS) │ - Context & Session Manager   │ - BD Clientes (JSON)   │
│                        │ - Guardrail Enforcement       │                        │
└────────────────────────┴───────────────────────────────┴────────────────────────┘
```

* **Gestor de Contexto Conversacional (`context_manager.py`):** Mantiene una memoria de corto plazo (*Sliding Window Memory* de 5 turnos) que retiene el cliente activo y su RUT para responder consultas de seguimiento (ej. *"¿Y qué documentos debo llevar?"*), evitando re-procesamientos redundantes y previniendo la contaminación de la ventana de contexto.
* **Interfaces Disponibles:** Se construyó una interfaz interactiva de consola (CLI) para evaluación técnica y un **Dashboard Web interactivo con FastAPI** que permite a los evaluadores monitorear en vivo la UF del día, los fragmentos normativos recuperados y el tiempo de respuesta.

---

## 5. EVALUACIÓN DE COHERENCIA, PRUEBAS Y JUSTIFICACIÓN TÉCNICA (IE5, IE6, IE8)

### 5.1. Batería de Pruebas y Métricas Cuantitativas RAG (IE6)
Para asegurar la credibilidad del agente ante la auditoría bancaria, se ejecutó una batería estandarizada (*Benchmark Suite*) sobre cinco casos reales de prueba:

| Caso de Prueba Organizacional | Consulta del Solicitante | Dictamen Esperado | Dictamen Agente | Citas Normativas Validadas | Coherencia UF/CLP |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Caso 1: Transportes Biobío** | 1.500 UF camión tolva (RUT 76.123.456-K) | Pre-Admisible (Leasing) | Pre-Admisible (Leasing) | Art. 3, Art. 4, Art. 6 (FOGAPE 85%) | 100% Exacto |
| **Caso 2: Panadería El Trigal** | 800 UF Capital de Trabajo (RUT 76.999.888-4) | No Admisible (DICOM) | No Admisible (DICOM) | Art. 4 (Deuda > $500.000) | 100% Exacto |
| **Caso 3: Constructora del Sur** | 4.000 UF Ampliación (RUT 76.543.210-8) | Derivación Comité Art. 11 | Derivación Comité Art. 11 | Art. 5, Art. 11 (Leverage > 3.2x) | 100% Exacto |
| **Caso 4: Frutícola Express** | 500 UF Capital Trabajo (RUT 78.111.222-1) | No Admisible (Antigüedad) | No Admisible (Antigüedad) | Art. 3 (< 12 meses operación) | 100% Exacto |
| **Caso 5: Consulta Abierta** | Requisitos y cobertura FOGAPE general | Asesoría Informativa | Asesoría Informativa | Art. 6 (Tramos 85% y 70%) | N/A |

### 5.2. Resultados Globales del Benchmark
* **Precisión de Dictamen (Decision Accuracy):** **100,0%** de acierto en los veredictos de riesgo.
* **Fidelidad Normativa (*Groundedness Score*):** **100,0%**, sin registro de alucinaciones en plazos o requisitos.
* **Recuperación de Citaciones (*Citation Recall*):** **100,0%**, citando fielmente los artículos específicos en cada caso.
* **Consistencia Matemática (UF a CLP):** **100,0%**, validado contra el producto del valor oficial de la API de la UF.
* **Latencia Media de Respuesta:** **0,0020 segundos** por dictamen completo.
* **Evidencia de Pruebas de Software:** 11 pruebas unitarias y de integración automatizadas ejecutadas con `unittest` (`test_rag_pipeline.py`, `test_external_tools.py`, `test_agent_policies.py`), todas con resultado satisfactorio (`Ran 11 tests in 0.027s - OK`).

---

## 6. CONCLUSIONES Y REFLEXIONES INDIVIDUALES (OBLIGATORIAS)

### 6.1. Conclusiones Técnicas del Proyecto
La implementación de la arquitectura **PYME-Advisor** demuestra que la combinación de agentes inteligentes, pipelines RAG semánticos y consumo de herramientas en tiempo real resuelve integralmente las deficiencias de los modelos generativos puros en entornos corporativos de alta regulación. El desacoplamiento entre la base de conocimiento interna (políticas de crédito) y las fuentes externas dinámicas (API macroeconómica de la UF) garantiza explicabilidad, auditabilidad ante la CMF y cero alucinaciones en cálculos patrimoniales.

### 6.2. Reflexión Individual - Juan Serna
> Durante el desarrollo de este encargo, mi principal contribución técnica estuvo centrada en el diseño del pipeline de recuperación RAG y la estructuración jerárquica de los documentos normativos de BancoEstado. Comprendí que el éxito de una solución RAG en el ámbito financiero no depende exclusivamente del tamaño del modelo de lenguaje, sino críticamente de la calidad de la segmentación de datos (*chunking*). Si los artículos del manual se fragmentan incorrectamente, el modelo pierde el contexto de las restricciones y genera conclusiones erróneas. Aprender a validar la fidelidad (*groundedness*) mediante pruebas automatizadas cambió mi perspectiva profesional sobre cómo se audita y confía en un sistema inteligente en la industria bancaria.

### 6.3. Reflexión Individual - Bárbara Bustamante
> En mi caso, el foco de trabajo estuvo orientado a la orquestación del agente inteligente, la integración de la API externa de indicadores económicos y la sincronización con la base de datos de clientes por RUT. Me pareció especialmente revelador comprobar cómo el patrón de llamada a herramientas (*Tool Calling*) en tiempo real permite superar la obsolescencia de información de los modelos: vincular la Unidad de Fomento del día hábil en vivo con las reglas internas de riesgo convirtió una respuesta genérica en una herramienta de negocio con impacto comercial real. Asimismo, estructurar la gestión de contexto para preservar los datos de la PYME entre turnos conversacionales me permitió entender los desafíos prácticos de latencia y consistencia en soluciones aplicadas.

### 6.4. Reflexión Individual - Nelson Carrasco
> Mi participación se concentró en la ingeniería de prompts, el diseño de guardrails negativos estrictos para mitigación de alucinaciones y la formulación del benchmark de evaluación de coherencia. En un contexto bancario comercial, es imperativo asegurar que el sistema no emita compromisos legales vinculantes, limitándose a una pre-admisibilidad técnica fundamentada. Diseñar reglas de seguridad que derivan al Comité de Crédito los casos que exceden la política institucional (Artículo 11) y certificar cuantitativamente el 100% de coherencia matemática entre UF y pesos consolidó la confiabilidad de la solución.

---

## 7. DECLARACIÓN DE USO DE INTELIGENCIA ARTIFICIAL

El equipo declara el uso de IA generativa como apoyo: Claude (Anthropic, 2026) se utilizó para revisar la completitud del encargo frente a la pauta, mejorar la redacción del informe y del README, generar los diagramas Mermaid y automatizar la captura de evidencias de prueba. _[Completar: otras herramientas de IA usadas y para qué]_. Todo el contenido generado fue revisado y validado por el equipo; las reflexiones individuales fueron redactadas por cada integrante sin apoyo de IA.

> Nota: la versión oficial entregada es `docs/INFORME_TECNICO_SOLUCION_RAG.docx`; este archivo Markdown es la versión extendida de trabajo.

---

## 8. REFERENCIAS BIBLIOGRÁFICAS (NORMATIVA APA 7)

* Anthropic. (2026). *Claude* (versión Opus 5.5) [Modelo de lenguaje de gran tamaño]. https://claude.ai
* Comisión para el Mercado Financiero [CMF]. (s.f.). *Recopilación Actualizada de Normas para Bancos*. https://www.cmfchile.cl
* Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *Advances in Neural Information Processing Systems (NeurIPS)*, 33, 9459–9474.
* Ministerio de Economía, Fomento y Turismo de Chile. (2024). *Quinta Encuesta Longitudinal de Empresas (ELE): Caracterización de las Micro, Pequeñas y Medianas Empresas*. Gobierno de Chile. https://www.economia.gob.cl
* Shuster, K., Poff, S., Chen, M., Kiela, D., & Weston, J. (2021). Retrieval Augmentation Reduces Hallucination in Conversation. *Findings of the Association for Computational Linguistics: EMNLP 2021*, 3784–3803.
* Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing Reasoning and Acting in Language Models. *International Conference on Learning Representations (ICLR 2023)*.
