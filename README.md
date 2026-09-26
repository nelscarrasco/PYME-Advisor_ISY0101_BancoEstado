# BancoEstado PYME-Advisor: Sistema Agéntico RAG para Asesoría y Pre-Evaluación Crediticia
> **Asignatura:** ISY0101 - Ingeniería de Soluciones con IA | **Institución:** Duoc UC  
> **Evaluación Parcial N°1:** Diseño de Solución con LLM y RAG (Encargo y Presentación)  
> **Integrantes:** Juan Serna, Bárbara Bustamante, Nelson Carrasco  

---

## 1. Descripción del Proyecto

**PYME-Advisor** es una solución de inteligencia artificial agéntica diseñada para **BancoEstado Microempresas**, orientada a resolver el cuello de botella en la pre-evaluación y asesoramiento financiero para micro y pequeñas empresas en Chile.

El sistema combina:
1. **Pipeline RAG Semántico Jerárquico:** Sobre el Manual de Políticas de Crédito Comercial 2026 (11 Artículos normativos) y el Catálogo Institucional de Productos Financieros.
2. **Herramientas Externas en Tiempo Real (Tool Calling):** Conexión en vivo a la API oficial de indicadores económicos de Chile (`mindicador.cl` / Banco Central de Chile) para obtener el valor actualizado de la **Unidad de Fomento (UF)**, Dólar y UTM, asegurando conversiones exactas en pesos chilenos ($CLP).
3. **Validación Cruzada de Clientes:** Consulta en tiempo real de registros internos por RUT para analizar antigüedad en Primera Categoría del SII, niveles de apalancamiento (*leverage*) y deudas en el Boletín Comercial (DICOM).
4. **Guardrails y Trazabilidad:** Respuestas estructuradas en 5 secciones que citan explícitamente los artículos de respaldo, erradicando alucinaciones y derivando automáticamente al Comité de Crédito los casos de riesgo según el Artículo 11.

---

## 2. Arquitectura del Sistema

```mermaid
flowchart TD
    User([Ejecutivo / Cliente PYME]) --> UI{Interfaz}
    UI -->|Consola Interactiva| CLI[app.py]
    UI -->|Dashboard Web| Web[web_server.py]

    CLI --> Agent[Agent Core: PymeAdvisorAgent]
    Web --> Agent

    subgraph Orquestación y Contexto
        Agent --> EntityParser[Extracción de RUT, Monto y Giro]
        Agent --> ContextManager[Memoria de Sesión: Ventana Deslizante]
        Agent --> PromptEngine[Prompt Engineering: Rol + Few-Shot + Guardrails]
    end

    subgraph Herramientas Externas (Tools)
        Agent -->|Consumo REST en Vivo| EconTool[EconomicIndicatorsTool: mindicador.cl]
        EconTool -.-> Cache[(Cache Local: indicators_cache.json)]
        Agent -->|Consulta por RUT| ClientDB[(Base Clientes: clientes_pyme.json)]
    end

    subgraph Recuperación RAG Interna
        Docs[(Manual de Crédito 2026 + Catálogo)] --> Chunker[Semantic & Hierarchical Chunker]
        Chunker --> VectorStore[Vector Store: TF-IDF N-Grams + Cosine Similarity]
        Agent -->|Búsqueda Semántica Top-K| VectorStore
    end

    PromptEngine --> Synthesizer[Motor de Inferencia Fiel / LLM]
    Synthesizer --> Output[Dictamen Estructurado en 5 Puntos con Citas APA/CMF]
    Output --> Evaluator[RAG Coherence Evaluator: Benchmark IE6]
```

---

## 3. Estructura del Repositorio

```text
├── data/
│   ├── database/
│   │   └── clientes_pyme_simulados.json    # Base de clientes PYME para pruebas por RUT
│   └── internal/
│       ├── manual_politicas_credito_pyme.md # Manual normativo oficial (Art. 1 al 11)
│       └── catalogo_productos_financieros.md # Fichas técnicas de productos comerciales
├── docs/
│   ├── 01_PROPUESTA_CASO_ORGANIZACIONAL.md  # Documento de Anteproyecto (Semana 3)
│   ├── 02_ARQUITECTURA_Y_DIAGRAMAS.md       # Especificación arquitectónica y Mermaid
│   ├── 03_INFORME_TECNICO_SOLUCION_RAG.md   # Informe técnico de 5 páginas (APA 7)
│   ├── INFORME_TECNICO_SOLUCION_RAG.docx    # Informe técnico entregado (Word, ≤ 5 páginas)
│   ├── diagramas/                           # Diagramas Mermaid (.mmd) y su render (.png)
│   ├── bocetos/                             # Boceto (wireframe) del dashboard
│   └── evidencias/                          # Logs de pruebas, benchmark y capturas del dashboard
│   └── 04_GUION_DEFENSA_ORAL_20MIN.md       # Guion de presentación (10m) y preguntas (10m)
├── src/
│   ├── agent/
│   │   ├── agent_core.py                    # Orquestador principal del agente
│   │   ├── context_manager.py               # Gestor de memoria y estado conversacional
│   │   └── prompts.py                       # System prompt, guardrails y few-shot
│   ├── evaluation/
│   │   └── evaluate_coherence.py            # Batería de métricas cuantitativas RAG (IE6)
│   ├── rag/
│   │   ├── chunker.py                       # Segmentación semántica por artículos
│   │   ├── document_loader.py               # Cargador de documentos normativos
│   │   └── vector_store.py                  # Índice vectorial semántico y búsqueda
│   └── tools/
│       ├── client_lookup.py                 # Consulta y validación de clientes por RUT
│       └── economic_indicators.py           # Cliente API oficial mindicador.cl con caché
├── tests/
│   ├── test_agent_policies.py               # Pruebas de reglas de negocio y guardrails
│   ├── test_external_tools.py               # Pruebas de API externa y cálculo de UF
│   └── test_rag_pipeline.py                 # Pruebas unitarias del pipeline RAG
├── app.py                                   # Aplicación interactiva de consola (CLI)
├── web_server.py                            # Dashboard interactivo web (FastAPI)
├── generate_report_docx.py                  # Script compilador del informe Word
├── requirements.txt                         # Dependencias del proyecto
└── README.md                                # Documentación general del repositorio
```

---

## 4. Requisitos e Instalación

### Prerrequisitos
* Python 3.10 o superior instalado.
* Conexión a internet (para sincronización de la API de UF de mindicador.cl; el sistema cuenta con fallback local en caso de estar offline).

### Pasos de Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/nelscarrasco/PYME-Advisor_ISY0101_BancoEstado.git
   cd PYME-Advisor_ISY0101_BancoEstado
   ```

2. **Crear y activar entorno virtual (Recomendado):**
   ```bash
   # En Windows PowerShell:
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Instalar dependencias requeridas:**
   ```bash
   pip install -r requirements.txt
   ```

4. **(Opcional) Activar el LLM real:** copie `.env.example`, o defina la variable de entorno `OPENAI_API_KEY`. Si está definida, el agente genera la respuesta con `gpt-4o-mini` (temperatura 0.1) usando el prompt de `src/agent/prompts.py`. Si no está definida, usa el **motor de síntesis local basado en reglas**, que produce el mismo formato de 5 secciones de forma determinista (así se ejecutan las pruebas y el benchmark).
   ```powershell
   $env:OPENAI_API_KEY="sk-..."   # Windows PowerShell
   ```

> Todos los comandos se ejecutan desde la carpeta raíz del repositorio (donde está `app.py`).

---

## 5. Instrucciones de Ejecución

### Opción A: Interfaz de Consola Interactiva (CLI)
Para ejecutar el agente en modo interactivo en la terminal:
```bash
python app.py
```
*Permite seleccionar casos de demostración rápidos (1 al 4), escribir consultas libres o ejecutar el benchmark de evaluación de coherencia.*

### Opción B: Dashboard Web Interactivo (FastAPI) - Ideal para la Presentación Oral
Para lanzar la interfaz gráfica web en el navegador:
```bash
python web_server.py
```
Luego abra su navegador web en: **`http://localhost:8000`**
*Incluye visualización en tiempo real del valor de la UF, panel de conversación con botones de demostración, panel de auditoría de herramientas ejecutadas y trazabilidad de fragmentos normativos recuperados.*

### Opción C: Ejecución de Batería de Pruebas de Coherencia RAG (IE6)
Para auditar cuantitativamente las métricas de fidelidad (*groundedness*), citación de artículos y cálculo matemático de divisas:
```bash
python -m src.evaluation.evaluate_coherence
```

### Opción D: Ejecución de Pruebas Unitarias Automatizadas
Para verificar la integridad del código fuente y pipelines:
```bash
python -m unittest discover tests
```

### Opción E: Regenerar Informe Técnico en Formato Word (.docx)
```bash
python generate_report_docx.py
```
*El archivo generado quedará disponible en `docs/INFORME_TECNICO_SOLUCION_RAG.docx`.*

---

## 6. Evidencia de Pruebas, Diagramas y Bocetos

* **Evidencia de pruebas:** [`docs/evidencias/`](docs/evidencias/) — salida de `unittest`, del benchmark IE6, demo del agente y capturas del dashboard (ver su README).
* **Diagramas:** [`docs/diagramas/arquitectura.png`](docs/diagramas/arquitectura.png) (arquitectura por capas) y [`docs/diagramas/flujo_rag.png`](docs/diagramas/flujo_rag.png) (secuencia del flujo RAG). Las fuentes `.mmd` se pueden editar en https://mermaid.live.
* **Bocetos de diseño:** [`docs/bocetos/wireframe_dashboard.png`](docs/bocetos/wireframe_dashboard.png) — wireframe de baja fidelidad de la interfaz.

![Arquitectura](docs/diagramas/arquitectura.png)

---

## 7. Resultados del Benchmark y Métricas de Calidad (IE6)

Sometido a evaluación sobre un conjunto de 5 casos canónicos de prueba:

| Métrica de Evaluación | Resultado Obtenido | Criterio de Aprobación |
| :--- | :---: | :--- |
| **Precisión de Dictamen (Decision Accuracy)** | **100,0%** | > 95,0% |
| **Score de Fidelidad Normativa (Groundedness)** | **100,0%** | > 90,0% |
| **Recuperación de Citas de Artículos (Citation Recall)** | **100,0%** | > 85,0% |
| **Consistencia Matemática (Conversión UF a CLP)** | **100,0%** | 100% |
| **Latencia Media por Inferencia** | **< 0,3 s** (motor local) | < 2,0 s |
| **Pruebas de Software Unitarias (`unittest`)** | **11 / 11 Aprobadas** | 100% |

---

> Las métricas se midieron con el motor de síntesis local (sin `OPENAI_API_KEY`). Con el LLM activo la salida no es determinista y debe re-evaluarse con la misma batería.

### Limitaciones conocidas
* El Manual de Crédito, el Catálogo y la base de clientes son **datos simulados** creados para el prototipo; no son normativa oficial de BancoEstado.
* El índice vectorial es TF-IDF (léxico): los puntajes de similitud son bajos (~10 %) y a veces recupera fragmentos poco específicos. Mejora propuesta: embeddings densos.
* Sin internet, la herramienta de indicadores usa valores de contingencia y lo informa en consola.

---

## 8. Declaración de Uso de Inteligencia Artificial

Conforme a las indicaciones de la evaluación (https://bibliotecas.duoc.cl/ia), el equipo declara el uso de IA generativa como apoyo:
* **Claude (Anthropic)**: revisión de completitud frente a la pauta, redacción del README e informe, generación de diagramas Mermaid, boceto y captura automatizada de evidencias.
* _[Completar: otras herramientas de IA utilizadas por el equipo y para qué]_

Todo el contenido generado con IA fue revisado y validado por el equipo. Las reflexiones individuales del informe fueron redactadas por cada integrante sin apoyo de IA.

Anthropic. (2026). *Claude* (versión Opus 5.5) [Modelo de lenguaje de gran tamaño]. https://claude.ai
