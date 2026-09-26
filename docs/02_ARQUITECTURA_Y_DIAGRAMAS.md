# Arquitectura de la solución (IE4, IE7)
## PYME-Advisor – Agente con LLM y RAG para BancoEstado Microempresas
**Asignatura:** ISY0101 – Ingeniería de Soluciones con IA | Duoc UC
**Integrantes:** Juan Serna, Bárbara Bustamante, Nelson Carrasco
**Fecha:** septiembre de 2026

---

### 1. Visión general

La solución sigue el patrón de **agente aumentado con herramientas y recuperación** (ReAct / tool-augmented RAG; Yao et al., 2023; Lewis et al., 2020) y se organiza en cuatro capas:

1. **Interfaz:** CLI (`app.py`) y dashboard web FastAPI (`web_server.py`) con panel de auditoría.
2. **Orquestación agéntica:** `agent_core.py` coordina extracción de entidades, herramientas, motor de reglas (`policy_engine.py`), recuperación, generación y verificación; `context_manager.py` mantiene la memoria de sesión.
3. **Recuperación y herramientas:** índice TF-IDF sobre el Manual de Crédito y el Catálogo (27 fragmentos por artículo/sección), base interna de clientes por RUT y API pública mindicador.cl (UF, dólar, UTM) con caché y respaldo.
4. **Generación y evaluación:** gpt-4o-mini (si existe `OPENAI_API_KEY`) o motor de síntesis local; guardrail de salida que verifica citas y estado; evaluador de coherencia (`evaluate_coherence.py`).

---

### 2. Diagrama de arquitectura

![Arquitectura](diagramas/arquitectura.png)

```mermaid
flowchart TB
    U(["Ejecutivo / Cliente PYME"])
    subgraph L1["1 · Capa de interfaz"]
        direction LR
        CLI["CLI · app.py"]
        WEB["Dashboard FastAPI · web_server.py"]
    end
    subgraph L2["2 · Capa de orquestación agéntica"]
        direction LR
        ENT["Extracción de entidades<br/>RUT · monto UF/CLP"]
        AG["PymeAdvisorAgent<br/>agent_core.py"]
        CTX["Memoria de sesión<br/>context_manager.py (5 turnos)"]
        POL["Motor de reglas del manual<br/>policy_engine.py<br/>(Art. 1, 3, 4, 5, 11)"]
    end
    subgraph L3["3 · Capa de recuperación y herramientas"]
        direction LR
        subgraph RAG["RAG interno"]
            direction TB
            DOCS[("Manual de Crédito + Catálogo<br/>(documentos simulados)")] --> CH["Chunker por artículo<br/>27 fragmentos"] --> VS["Índice TF-IDF 1-3 gramas + coseno<br/>búsqueda multi-consulta"]
        end
        subgraph EXT["Herramientas (tool calling)"]
            direction TB
            API["EconomicIndicatorsTool<br/>API mindicador.cl (UF · USD · UTM)"] -.-> CACHE[("Caché TTL 1 h<br/>+ contingencia")]
            CLDB[("ClientLookupTool<br/>base clientes por RUT")]
        end
    end
    subgraph L4["4 · Capa de generación y evaluación"]
        direction LR
        PR["Prompt ensamblado<br/>System + Few-shot + Guardrails<br/>+ contexto RAG + perfil + UF"]
        LLM["LLM gpt-4o-mini (temp 0.1)<br/>si hay OPENAI_API_KEY"]
        LOC["Motor de síntesis local<br/>por reglas (fallback)"]
        GR["Guardrail de salida<br/>verificación de citas<br/>+ estado vs motor de reglas"]
        OUT["Dictamen de 5 secciones<br/>con citas [Manual, Art. X]"]
        EVAL["Evaluador de coherencia<br/>evaluate_coherence.py"]
        PR --> LLM --> GR
        PR --> LOC --> GR
        GR --> OUT --> EVAL
    end
    U --> CLI & WEB
    CLI & WEB --> AG
    AG --- ENT
    AG --- CTX
    AG --- POL
    POL --> PR
    AG --> VS
    AG --> API
    AG --> CLDB
    VS --> PR
    API --> PR
    CLDB --> PR
```

---

### 3. Flujo de una consulta (secuencia)

![Flujo RAG](diagramas/flujo_rag.png)

```mermaid
sequenceDiagram
    autonumber
    actor E as Ejecutivo
    participant A as Agente (agent_core)
    participant C as ClientLookupTool
    participant I as EconomicIndicatorsTool
    participant R as Motor de reglas
    participant V as Vector Store (RAG)
    participant G as LLM / Motor local
    E->>A: Consulta en lenguaje natural (RUT, monto, destino)
    A->>A: Extrae RUT y monto (regex)
    A->>C: find_by_rut(RUT)
    C-->>A: Perfil (antigüedad, DICOM, leverage, DSCR, ventas UF)
    A->>I: get_indicators()
    I-->>A: UF, Dólar, UTM (API en vivo, caché o respaldo)
    A->>R: evaluate_policies(perfil, monto UF, producto)
    R-->>A: Estado preliminar + verificación por artículo
    A->>V: 9 sub-consultas por dimensión + consulta original
    V-->>A: Fragmentos del Manual/Catálogo (sin duplicados, con score)
    A->>G: Prompt: reglas + contexto RAG + perfil + UF + memoria
    G-->>A: Dictamen de 5 secciones con citas
    A->>A: Guardrail: cada cita respaldada por un fragmento recuperado
    A-->>E: Respuesta + fuentes + herramientas + validación
```

**Ejemplo (Caso 1, Transportes Biobío, 1.500 UF para un camión):**
1. Se extraen el RUT 76.123.456-K y el monto de 1.500 UF.
2. `ClientLookupTool` entrega: 36 meses, DICOM $0, leverage 1,8x, DSCR 1,45 y ventas de 8.500 UF.
3. `EconomicIndicatorsTool` entrega la UF del día y el monto se convierte a CLP (1.500 × UF).
4. El motor de reglas verifica los Art. 1, 3, 4 y 5 (límite de leverage de 3,2x para transporte) → **PRE-ADMISIBLE**; el producto detectado es **Leasing**.
5. La búsqueda multi-consulta recupera, entre otros, los Art. 3, 4, 5, 6, 7 y 9 y las Secciones 1 y 2 del catálogo.
6. El dictamen cita sólo esos artículos; el guardrail confirma que las 9 citas tienen respaldo.

---

### 4. Componentes y decisiones de diseño (IE4, IE8)

| Componente | Implementación | Justificación |
| :--- | :--- | :--- |
| Segmentación | Por encabezado Markdown y artículo (`chunker.py`) | Una regla y su excepción quedan en el mismo fragmento y la cita al artículo es inequívoca. |
| Índice vectorial | TF-IDF sublineal, n-gramas 1–3, coseno (`vector_store.py`) | Corpus pequeño con terminología exacta (DICOM, FOGAPE, UF); determinista, sin costo ni dependencias externas. Con un corpus mayor se migraría a embeddings densos. |
| Recuperación multi-consulta | Sub-consultas por dimensión de riesgo (`agent_core._retrieve`) | Una solicitud involucra varias reglas; medido en la batería: recall de recuperación de 17,1% (sólo la consulta original, top-3) a 100%. |
| Motor de reglas | `policy_engine.py` (Art. 1, 3, 4, 5 y 11) | La decisión crediticia debe ser reproducible y auditable; el LLM explica, no decide. |
| Herramienta externa | API mindicador.cl + caché de 1 h + último valor real + contingencia | Resuelve el desfase temporal del LLM sin inventar valores si la API falla, e informa siempre la fuente usada. |
| Memoria | Ventana de 5 turnos y cliente activo (`context_manager.py`) | Permite preguntas de seguimiento ("¿y qué documentos necesito?") sin saturar el prompt. |
| Prompt | Rol, reglas negativas, citas obligatorias, few-shot, estado impuesto por el motor, temperatura 0,1 (`prompts.py`) | Reduce el espacio de respuesta a lo que el contexto respalda y estabiliza el formato de 5 secciones. |
| Guardrail de salida | `validate_citations` y control de estado | Toda cita sin fragmento de respaldo se marca y se advierte al ejecutivo; si el LLM contradice al motor de reglas, prevalece el motor. |
| Evaluación | `evaluate_coherence.py` (7 casos) | Mide precisión de dictamen, recall de recuperación y de citas, groundedness de citas y consistencia UF→CLP. |

---

### 5. Referencias

- Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems, 33*, 9459–9474.
- Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. *International Conference on Learning Representations (ICLR 2023)*.
