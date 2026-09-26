# ARQUITECTURA DE LA SOLUCIÓN TÉCNICA (IE4, IE7)
## Sistema Agéntico RAG: "PYME-Advisor" para BancoEstado Microempresas
**Asignatura:** ISY0101 - Ingeniería de Soluciones con IA | Duoc UC  
**Integrantes:** Juan Serna, Bárbara Bustamante, Nelson Carrasco  
**Fecha:** Septiembre 2026  

---

### 1. Descripción General de la Arquitectura

La arquitectura de la solución **PYME-Advisor** ha sido concebida bajo el paradigma de **Agente Aumentado con Herramientas y Recuperación (ReAct / Tool-Augmented RAG)**. El sistema desacopla eficientemente cuatro capas funcionales:
1. **Capa de Ingesta y Recuperación Interna (Internal RAG):** Almacenamiento vectorial e indexación semántica jerárquica de la normativa bancaria interna.
2. **Capa de Integración Externa en Tiempo Real (External Tools):** Consumo dinámico de la API oficial de indicadores económicos de Chile (mindicador.cl / CMF) y la base de clientes.
3. **Capa de Orquestación y Procesamiento Agéntico (Agent Core):** Extracción de entidades, control de memoria de sesión, enrutamiento semántico y aplicación de guardrails.
4. **Capa de Generación y Explicabilidad (Generation & Guardrails):** Formulación de dictámenes financieros trazables, con citación obligatoria y consistencia matemática.

---

### 2. Diagrama de Arquitectura Global del Sistema (IE7)

```mermaid
flowchart TD
    subgraph UI ["CAPA DE INTERFAZ DE USUARIO"]
        User["Ejecutivo / Cliente PYME"]
        CLI["Consola Interactiva (CLI)\n[app.py]"]
        WebUI["Dashboard Web FastAPI\n[web_server.py]"]
    end

    subgraph AgentCore ["CAPA DE ORQUESTACIÓN AGÉNTICA (Agent Core)"]
        Router["Orquestador Agéntico\n[agent_core.py]"]
        EntityExt["Extractor de Entidades\n(RUT, Monto en UF/CLP, Producto)"]
        ContextMgr["Gestor de Memoria y Contexto\n[context_manager.py]"]
        PromptEng["Módulo de Prompt Engineering\n(System Prompt + Few-Shot + Guardrails)\n[prompts.py]"]
    end

    subgraph ExternalSources ["CAPA DE HERRAMIENTAS Y DATOS EXTERNOS"]
        ExtAPI["API Oficial Indicadores\n(mindicador.cl / CMF)\n[economic_indicators.py]"]
        CacheDisc["Caché Local de Resiliencia\n[indicators_cache.json]"]
        ClientDB["Base de Datos Clientes PYME\n(RUT, Balance, Dicom, FOGAPE)\n[client_lookup.py]"]
    end

    subgraph InternalRAG ["CAPA DE RECUPERACIÓN INTERNA (RAG Pipeline)"]
        RawDocs["Documentación Normativa Interna\n(Manual de Crédito 2026, Catálogo Productos)"]
        SemanticChunk["Segmentador Jerárquico\n(Chunking por Artículos)\n[chunker.py]"]
        VectorStore["Almacén Vectorial Semántico\n(TF-IDF N-Grams + Cosine Similarity)\n[vector_store.py]"]
    end

    subgraph OutputLayer ["CAPA DE GENERACIÓN Y EVALUACIÓN"]
        LLMEngine["Motor de Inferencia\n(LLM gpt-4o-mini / Grounded Engine)"]
        Auditor["Evaluador de Coherencia RAG\n(RAG Triad, Fidelidad, Citas, Math)\n[evaluate_coherence.py]"]
        ReportOut["Dictamen Estructurado de 5 Puntos\n(Trazabilidad APA / CMF)"]
    end

    %% Flujos de Información
    User -->|Consulta en Lenguaje Natural| CLI
    User -->|Consulta en Lenguaje Natural| WebUI
    CLI --> Router
    WebUI --> Router

    Router --> EntityExt
    EntityExt --> ContextMgr
    
    Router -->|Invocación de Herramientas| ExtAPI
    ExtAPI -.-> CacheDisc
    Router -->|Búsqueda de Cliente por RUT| ClientDB

    Router -->|Búsqueda Semántica Vectorial| VectorStore
    RawDocs --> SemanticChunk --> VectorStore

    ContextMgr --> PromptEng
    VectorStore -->|Contexto Normativo Top-K| PromptEng
    ExtAPI -->|UF / Dólar del Día| PromptEng
    ClientDB -->|Perfil de Riesgo| PromptEng

    PromptEng --> LLMEngine
    LLMEngine --> ReportOut
    ReportOut --> Auditor
    ReportOut -->|Visualización Inmediata| CLI
    ReportOut -->|Visualización Inmediata| WebUI
```

---

### 3. Diagrama de Secuencia: Flujo de Consulta y Evaluación Crediticia

El siguiente diagrama detalla la interacción paso a paso entre los componentes del sistema ante la solicitud de una PYME:

```mermaid
sequenceDiagram
    autonumber
    actor Ejecutivo as Ejecutivo / Cliente PYME
    participant Web as Dashboard Web (FastAPI)
    participant Agent as Agente PYME-Advisor
    participant Tools as Herramientas Externas (API UF/CMF)
    participant ClientDB as Base de Clientes (RUT)
    participant RAG as Vector Store (Políticas)
    participant Engine as Motor de Generación (Guardrails)

    Ejecutivo->>Web: Envía solicitud ("Queremos 1.500 UF para camión, RUT 76.123.456-K")
    Web->>Agent: process_query(texto)
    
    rect rgb(240, 248, 255)
        Note over Agent,Tools: Paso 1: Ejecución de Herramientas Externas
        Agent->>Tools: get_indicators()
        Tools-->>Agent: UF actual = $41.008,10 CLP (mindicador.cl)
        Agent->>ClientDB: find_by_rut("76.123.456-K")
        ClientDB-->>Agent: Transportes Biobío SpA (Antigüedad: 36 meses, DICOM: $0, Leverage: 1.8)
    end

    rect rgb(245, 255, 245)
        Note over Agent,RAG: Paso 2: Recuperación Aumentada RAG
        Agent->>RAG: search("Transporte camión 1.500 UF leasing garantías FOGAPE")
        RAG-->>Agent: Retorna Art. 3 (Antigüedad), Art. 6 (FOGAPE 85%), Art. 7 (Prenda Leasing)
    end

    rect rgb(255, 250, 240)
        Note over Agent,Engine: Paso 3: Ensamble de Prompt y Razonamiento
        Agent->>Engine: Prompt con Contexto RAG + UF en vivo + Perfil Financiero
        Engine->>Engine: Computa: 1.500 UF * $41.008,10 = $61.512.150 CLP
        Engine->>Engine: Evalúa: Leverage 1.8x < 3.2x -> PRE-ADMISIBLE
        Engine-->>Agent: Dictamen Estructurado de 5 Puntos con Citas Textuales
    end

    Agent->>Web: Retorna respuesta con metadatos de auditoría y tiempo (0.002s)
    Web-->>Ejecutivo: Muestra pre-calificación, producto Leasing y desglose en CLP
```

---

### 4. Justificación Técnica de los Componentes Arquitectónicos (IE4, IE8)

| Componente | Tecnología Seleccionada | Justificación Técnica y Beneficio Organizacional |
| :--- | :--- | :--- |
| **Segmentador Semántico (Chunking)** | Hierarchical & Semantic Heading Splitter | A diferencia de un splitter por número ciego de caracteres (que cortaría cláusulas legales por la mitad), este segmentador agrupa los fragmentos respetando los títulos (`##`) y artículos (`Art. X`), conservando la unidad conceptual de la regla de crédito. |
| **Almacén Vectorial (Vector Store)** | Sparse Vectorizer N-Grams (1-3) & Cosine Distance | Proporciona búsqueda léxico-semántica determinista de latencia ultrabaja (<2 milisegundos), garantizando que términos técnicos exactos (como "FOGAPE", "DICOM", "Leverage") tengan coincidencia perfecta sin falsos positivos semánticos. |
| **Integración Externa (External Tools)** | REST API `mindicador.cl` + Caché TTL | Resuelve la principal limitación de los LLMs: el desfase temporal y la incapacidad de calcular montos actualizados. Permite indexar contratos en UF del día hábil con fallback local ante caídas del enlace. |
| **Control de Contexto (Context Manager)** | Stateful Sliding Window Buffer | Mantiene el perfil de la PYME identificada durante la sesión para consultas sucesivas, descartando turnos antiguos para prevenir saturación de ventana y alucinaciones por ruido contextual. |
| **Guardrails de Inferencia** | Strict Role Prompting + Grounded Synthesizer | Implementa el principio de "defensa en profundidad": el agente tiene vetado emitir aprobaciones finales y rechaza inventar condiciones, citando obligatoriamente el artículo de soporte normativo. |
| **Métricas de Evaluación (Coherencia)** | Framework RAG Triad (Faithfulness, Recall, Math) | Permite auditar cuantitativamente el 100% de los dictámenes emitidos, demostrando solidez técnica y mitigando el riesgo regulatorio ante la CMF. |
