# GUION Y PLAN DE DEFENSA ORAL: 20 MINUTOS (IE6, IE7, IE8, IE9)
## Asignatura: ISY0101 - Ingeniería de Soluciones con IA | Duoc UC
## Proyecto: "PYME-Advisor" para BancoEstado Microempresas
**Integrantes:** Juan Serna, Bárbara Bustamante, Nelson Carrasco  
**Fecha:** Septiembre 2026  

---

### ESTRUCTURA DE LA DEFENSA ORAL (Ponderación 40% de la EP1)
* **Tiempo Total:** 20 minutos (10 minutos de exposición + 10 minutos de ronda de preguntas).
* **Participación:** Equitativa (~3:20 min cada uno) entre los tres integrantes del equipo.
* **Apoyo Visual:** Dashboard Web en vivo (`python web_server.py`) o diapositivas con diagramas de arquitectura.

---

### BLOQUE 1: EXPOSICIÓN ORAL (10 MINUTOS CRONOMETRADOS)

#### Minuto 0:00 a 3:20 | Juan Serna: Diagnóstico del Problema y Requerimientos Organizacionales (IE1, IE8)
* **Apertura:** "Buenos días profesor/a y comisión evaluadora. Junto a Bárbara Bustamante y Nelson Carrasco, presentamos nuestra solución de ingeniería con IA denominada **PYME-Advisor**, diseñada para **BancoEstado Microempresas**."
* **El Problema:** "En Chile las MiPymes son el 98,5% de las empresas formales y concentran el 48% del empleo, según el Ministerio de Economía (2026). Cuando piden capital o leasing, el ejecutivo debe cruzar a mano tres fuentes: el manual de riesgo (antigüedad, DICOM, endeudamiento, garantías FOGAPE), los antecedentes del cliente y la UF del día. Eso genera demoras, criterios distintos entre ejecutivos y errores de conversión." *(Aclarar: el manual, el catálogo y los clientes son simulados por el equipo.)*
* **Por qué no un LLM genérico:** "Un LLM puro o estándar no conoce las políticas internas de BancoEstado, sufre de alucinaciones en cálculos patrimoniales y padece desfase temporal: no conoce la UF de hoy ni las normativas actualizadas de la CMF. Por ello, diseñamos una arquitectura **Agéntica RAG Aumentada con Herramientas en Tiempo Real**."
* **Objetivos medibles:** "Dictamen preliminar en menos de 2 segundos; 100% de las citas respaldadas por un fragmento recuperado; conversión UF→CLP exacta con la UF del día, y derivación automática al Comité en los casos del Art. 11."

#### Minuto 3:20 a 6:40 | Bárbara Bustamante: Arquitectura de la Solución y Flujo RAG Híbrido (IE3, IE4, IE7)
* *(Mostrar el Diagrama de Arquitectura Mermaid / Dashboard Web)*
* **Estructura por Capas:** "Nuestra arquitectura desacopla cuatro capas clave para cumplir con los estándares de la industria financiera:
  1. **Capa de Ingesta y Segmentación Interna:** No usamos un chunking ciego por caracteres. Diseñamos un **Semantic & Hierarchical Chunker** que respeta la estructura legal de los textos (`Art. 3`, `Art. 6 FOGAPE`, etc.), evitando cortar excepciones normativas. Indexamos 27 fragmentos en un índice TF-IDF con n-gramas (1 a 3) y similitud coseno. Y en vez de buscar una sola vez, **descomponemos la consulta en sub-consultas por dimensión de riesgo** (antigüedad, morosidad, endeudamiento, FOGAPE, garantías, producto, documentos, comité): con sólo la consulta original recuperábamos el 17,1% de los artículos necesarios; con sub-consultas, el 100%.
  2. **Capa de Herramientas Externas en Vivo (Tool Calling):** Desarrollamos la herramienta `EconomicIndicatorsTool`, conectada a la API pública `mindicador.cl`, que publica los valores del Banco Central de Chile. El agente convierte cada monto en UF a pesos con la UF del día; si la API no responde, usa el último valor real guardado en caché y lo informa como fuente.
  3. **Base de Datos de Clientes:** Vinculamos la verificación del RUT para cruzar automáticamente antigüedad, morosidad DICOM, leverage, DSCR y ventas.
  4. **Motor de reglas + guardrail:** `policy_engine.py` aplica los Art. 1, 3, 4, 5 y 11 y fija el estado; el LLM sólo redacta la explicación. Al final, un guardrail verifica que cada cita tenga un fragmento recuperado que la respalde."

#### Minuto 6:40 a 10:00 | Nelson Carrasco: Prompt Engineering, Demostración y Métricas de Coherencia (IE2, IE5, IE6, IE9)
* **Prompt Engineering y Guardrails:** "El núcleo de razonamiento aplica **Prompt Engineering Avanzado**:
  * **Role-Based Framing:** 'Agente Consultor de Riesgo Crediticio de BancoEstado', fijando un registro prudente y técnico.
  * **Strict Negative Guardrails:** El agente tiene vetado legalmente otorgar 'aprobaciones definitivas', catalogando todo veredicto como pre-admisibilidad técnica. Además, tiene prohibido inventar condiciones: si una situación no está tipificada, debe derivar obligatoriamente al Comité de Crédito según el **Artículo 11**.
  * **Trazabilidad:** Ningún dictamen es válido si no cita el artículo del manual (`[Manual de Crédito, Art. X]`)."
* **Demostración Práctica:**
  * "Veamos el **Caso 1: Transportes Biobío (RUT 76.123.456-K)**, solicitando 1.500 UF para un camión: El agente detecta el RUT, recupera su antigüedad y apalancamiento; convierte 1.500 UF a pesos con la UF del día (mostrar el monto en pantalla); recupera el Art. 6 otorgándole hasta un **85% de garantía estatal FOGAPE** y recomienda **Leasing de Activos Fijos** por su beneficio tributario."
  * "En contraste, en el **Caso 2: Panadería El Trigal**, que registra morosidad en DICOM: El agente emite de inmediato un dictamen de **NO ADMISIBLE** citando el **Art. 4**, impidiendo una colocación fuera de política."
* **Resultados Cuantitativos del Benchmark (IE6):**
  * "Sometimos al sistema a una batería de 7 casos con resultado esperado conocido (botón *Ejecutar Batería* del dashboard):
    * **Precisión de dictamen:** 100%
    * **Recall de recuperación:** 100% (vs 17,1% con búsqueda simple)
    * **Groundedness de citas** (citas respaldadas por fragmentos recuperados): 100%
    * **Consistencia UF→CLP:** 100%
    * **Latencia:** bajo 0,3 s por consulta
    * **Pruebas de software:** 17 pruebas `unittest`, todas exitosas.
  * "Ojo: estas métricas son en modo motor local, sin LLM. Con gpt-4o-mini la redacción varía, pero el estado lo fija el motor de reglas y el guardrail marca cualquier cita sin respaldo."
* **Cierre:** "Con esto demostramos una solución viable, escalable y éticamente responsable. Quedamos a disposición de la comisión para sus preguntas."

---

### BLOQUE 2: BANCO DE PREGUNTAS Y RESPUESTAS TÉCNICAS (10 MINUTOS)

A continuación se preparan las preguntas técnicas más probables que formulará el docente o comisión evaluadora, asignadas a cada integrante:

#### Pregunta 1: "¿Por qué decidieron implementar un Vector Store con TF-IDF n-grams y similitud coseno en lugar de usar embeddings densos externos?"
* **Integrante a Cargo:** Juan Serna.
* **Respuesta Técnica:**
  "Fue una decisión de ingeniería deliberada basada en tres factores críticos:
  1. **Determinismo y Fidelidad Terminológica:** En el dominio bancario chileno existen siglas y términos unívocos como 'FOGAPE', 'DICOM', 'Leverage', 'SII F29'. Los embeddings densos generales a veces sufren de falsos positivos semánticos (por ejemplo, confundir FOGAPE con cualquier subsidio estatal genérico). Los n-gramas sparse (1 a 3) capturan la frase exacta con peso TF-IDF sublineal, garantizando que cuando se busca 'cobertura FOGAPE', el Artículo 6 obtenga el score más alto.
  2. **Latencia y Autonomía Operativa:** La búsqueda toma milisegundos y no depende de llamadas de red a servidores en el extranjero ni de cuotas de tokens, asegurando 100% de disponibilidad.
  3. **Modularidad:** La búsqueda está encapsulada en `vector_store.py` (métodos `search` y `get_formatted_context`); cambiar a embeddings densos implica reemplazar ese módulo sin tocar el orquestador. Con un corpus más grande sería la mejora natural."

#### Pregunta 2: "¿Qué sucede si la API externa de mindicador.cl se cae o no responde?"
* **Integrante a Cargo:** Bárbara Bustamante.
* **Respuesta Técnica:**
  "Diseñamos el componente `EconomicIndicatorsTool` bajo el principio de **Resiliencia y Fallback Degradado**:
  1. Mantiene un caché local (`indicators_cache.json`) con vigencia de 1 hora, para no llamar a la API en cada consulta.
  2. Si la API falla, usa el último valor real guardado en caché y lo informa como fuente ("último valor en caché, API sin conexión").
  3. Si tampoco hay caché, usa valores de contingencia fijos, también informados. Además, no reintenta la API en cada consulta durante 5 minutos, para no esperar el timeout cada vez."

#### Pregunta 3: "¿Cómo garantiza su solución que el modelo no sufra de alucinaciones en un entorno tan regulado como el bancario?"
* **Integrante a Cargo:** Nelson Carrasco.
* **Respuesta Técnica:**
  "Implementamos una estrategia de **Defensa en Profundidad** con cuatro barreras:
  1. **Recuperación Estricta (Grounded RAG):** El prompt solo suministra al modelo los fragmentos normativos recuperados y prohíbe explícitamente asumir o interpolar reglas.
  2. **Guardrails Negativos en el System Prompt:** Se instruye al modelo que si una condición o excepción no aparece textualmente en el fragmento, está obligado a declarar que no está tipificada y derivar al Comité Especial según el Art. 11.
  3. **Trazabilidad Mandatoria:** Cada afirmación debe estar anclada a una cita `[Manual de Crédito, Art. X]`.
  4. **Motor de reglas:** el estado (admisible, no admisible, comité) lo calcula `policy_engine.py`, no el LLM; si el LLM escribe otro estado, se agrega una nota de control y prevalece el motor.
  5. **Verificación de citas:** `validate_citations` revisa que cada `[Manual de Crédito, Art. X]` corresponda a un fragmento efectivamente recuperado; si no, se advierte al ejecutivo. `evaluate_coherence.py` mide esto en 7 casos (groundedness de citas 100%)."

#### Pregunta 4: "¿Por qué se requirió un enfoque agéntico y no simplemente un buscador semántico tradicional?"
* **Integrante a Cargo:** Bárbara Bustamante / Juan Serna.
* **Respuesta Técnica:**
  "Un buscador tradicional únicamente devuelve párrafos de texto; no puede razonar, cruzar variables ni ejecutar cálculos. Nuestro agente debe realizar un flujo multi-paso:
  1. Extraer entidades estructuradas (RUT de la empresa, monto en UF).
  2. Consultar la base de datos interna para conocer el apalancamiento y mora en DICOM del cliente.
  3. Llamar a una herramienta externa para obtener el valor financiero de la UF al segundo.
  4. Realizar la multiplicación aritmética para saber el costo real en pesos.
  5. Contrastar los ratios financieros del cliente contra los artículos recuperados por el RAG.
  6. Sintetizar una asesoría explicable en cinco secciones. Ese razonamiento condicional solo es posible mediante una arquitectura agéntica."

#### Pregunta 5: "¿Cómo aseguran el cumplimiento de la Ley de Protección de Datos Personales N° 19.628 y el Secreto Bancario?"
* **Integrante a Cargo:** Nelson Carrasco.
* **Respuesta Técnica:**
  "El diseño contempla tres medidas:
  1. **Minimización de datos (propuesta para producción):** al LLM sólo se envían campos financieros agregados del cliente; en producción se agregaría anonimización o tokenización del RUT antes de llamar a un modelo externo.
  2. **Aislamiento de Sesión:** El `context_manager.py` opera en memoria local volátil y solo mantiene un buffer acotado de 5 turnos para la interacción en curso, sin persistir datos crediticios sensibles en servidores externos no autorizados por la CMF.
  3. **Principio de Mínimo Privilegio:** El agente sólo tiene acceso a los campos tributarios y comerciales estrictamente necesarios para determinar la pre-admisibilidad de la solicitud."

#### Pregunta 6: "Si las métricas son 100%, ¿dónde está realmente el LLM?"
* **Integrante a Cargo:** Nelson Carrasco.
* **Respuesta Técnica:**
  "El sistema tiene dos modos de generación. Con `OPENAI_API_KEY`, el prompt completo (system prompt, few-shot, memoria, UF, perfil, fragmentos RAG y resultado del motor de reglas) se envía a gpt-4o-mini con temperatura 0,1. Sin clave, un motor de síntesis local redacta el mismo formato. Las métricas publicadas son del modo local, porque es determinista y reproducible por cualquier evaluador. En ambos modos el estado lo decide el motor de reglas y el guardrail verifica las citas, así que la parte crítica no depende de la variabilidad del modelo."

#### Pregunta 7: "¿Cómo miden que la respuesta es coherente con los datos recuperados? (IE6)"
* **Integrante a Cargo:** Juan Serna.
* **Respuesta Técnica:**
  "Con cuatro métricas por caso: (1) *recall de recuperación*, si los artículos que el caso necesita están entre los fragmentos recuperados; (2) *recall de citas*, si la respuesta cita esos artículos; (3) *groundedness de citas*, qué proporción de las citas tiene un fragmento recuperado que la respalde; (4) *consistencia UF→CLP*, si el monto en pesos es exactamente monto × UF de la herramienta. En el dashboard se ve, para cada respuesta, qué fragmentos se recuperaron, para qué sub-consulta y cuántas citas quedaron respaldadas."
