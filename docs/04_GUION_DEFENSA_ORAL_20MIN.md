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
* **El Problema:** "En Chile, más del 98% de las empresas son PYMEs. Sin embargo, cuando acuden al banco en busca de capital o leasing, la pre-evaluación crediticia tarda entre **7 y 10 días hábiles**. ¿Por qué? Porque un ejecutivo debe contrastar manualmente un manual de riesgo de más de 150 páginas (antigüedad, DICOM, leverage y garantías FOGAPE), mientras calcula a mano balances en Unidades de Fomento (UF) que cambian día a día con la inflación."
* **Por qué no un LLM genérico:** "Un LLM puro o estándar no conoce las políticas internas de BancoEstado, sufre de alucinaciones en cálculos patrimoniales y padece desfase temporal: no conoce la UF de hoy ni las normativas actualizadas de la CMF. Por ello, diseñamos una arquitectura **Agéntica RAG Aumentada con Herramientas en Tiempo Real**."
* **Objetivos de Impacto:** "Redujimos la latencia de pre-dictamen de 7 días a **0,002 segundos**, con un **100% de consistencia matemática** y **cero alucinaciones**, citando explícitamente el artículo normativo correspondiente."

#### Minuto 3:20 a 6:40 | Bárbara Bustamante: Arquitectura de la Solución y Flujo RAG Híbrido (IE3, IE4, IE7)
* *(Mostrar el Diagrama de Arquitectura Mermaid / Dashboard Web)*
* **Estructura por Capas:** "Nuestra arquitectura desacopla cuatro capas clave para cumplir con los estándares de la industria financiera:
  1. **Capa de Ingesta y Segmentación Interna:** No usamos un chunking ciego por caracteres. Diseñamos un **Semantic & Hierarchical Chunker** que respeta la estructura legal de los textos (`Art. 3`, `Art. 6 FOGAPE`, etc.), evitando cortar excepciones normativas. Indexamos 26 fragmentos con un Vector Store semántico de alta velocidad basado en TF-IDF con n-gramas (1 a 3) y similitud coseno.
  2. **Capa de Herramientas Externas en Vivo (Tool Calling):** Desarrollamos la herramienta `EconomicIndicatorsTool`, conectada a la API oficial de `mindicador.cl` y Banco Central de Chile. Cada vez que una PYME solicita un monto en UF, el agente consulta la API en tiempo real —hoy a **$41.008 CLP**— y calcula la conversión con exactitud al peso, contando con una capa de caché y contingencia local ante caídas de red.
  3. **Base de Datos de Clientes:** Vinculamos la verificación del RUT para cruzar automáticamente balances, antigüedad en el SII y morosidades comerciales en DICOM."

#### Minuto 6:40 a 10:00 | Nelson Carrasco: Prompt Engineering, Demostración y Métricas de Coherencia (IE2, IE5, IE6, IE9)
* **Prompt Engineering y Guardrails:** "El núcleo de razonamiento aplica **Prompt Engineering Avanzado**:
  * **Role-Based Framing:** 'Agente Consultor de Riesgo Crediticio de BancoEstado', fijando un registro prudente y técnico.
  * **Strict Negative Guardrails:** El agente tiene vetado legalmente otorgar 'aprobaciones definitivas', catalogando todo veredicto como pre-admisibilidad técnica. Además, tiene prohibido inventar condiciones: si una situación no está tipificada, debe derivar obligatoriamente al Comité de Crédito según el **Artículo 11**.
  * **Trazabilidad:** Ningún dictamen es válido si no cita el artículo del manual (`[Manual de Crédito, Art. X]`)."
* **Demostración Práctica:**
  * "Veamos el **Caso 1: Transportes Biobío (RUT 76.123.456-K)**, solicitando 1.500 UF para un camión: El agente detecta el RUT, recupera su antigüedad y apalancamiento; calcula que 1.500 UF equivalen a **$61.512.150 CLP** según la UF de hoy; recupera el Art. 6 otorgándole hasta un **85% de garantía estatal FOGAPE** y recomienda **Leasing de Activos Fijos** por su beneficio tributario."
  * "En contraste, en el **Caso 2: Panadería El Trigal**, que registra morosidad en DICOM: El agente emite de inmediato un dictamen de **NO ADMISIBLE** citando el **Art. 4**, impidiendo una colocación fuera de política."
* **Resultados Cuantitativos del Benchmark (IE6):**
  * "Sometimos al sistema a una batería de 5 casos canónicos de prueba:
    * **Precisión de Dictamen:** 100%
    * **Groundedness Score (Fidelidad RAG):** 100%
    * **Consistencia Matemática UF/CLP:** 100%
    * **Latencia Promedio:** 0,0020 segundos.
    * **Pruebas de Software:** 11 pruebas unitarias automáticas con `unittest`, todas exitosas."
* **Cierre:** "Con esto demostramos una solución viable, escalable y éticamente responsable. Quedamos a disposición de la comisión para sus preguntas."

---

### BLOQUE 2: BANCO DE PREGUNTAS Y RESPUESTAS TÉCNICAS (10 MINUTOS)

A continuación se preparan las preguntas técnicas más probables que formulará el docente o comisión evaluadora, asignadas a cada integrante:

#### Pregunta 1: "¿Por qué decidieron implementar un Vector Store con TF-IDF n-grams y similitud coseno en lugar de usar embeddings densos externos?"
* **Integrante a Cargo:** Juan Serna.
* **Respuesta Técnica:**
  "Fue una decisión de ingeniería deliberada basada en tres factores críticos:
  1. **Determinismo y Fidelidad Terminológica:** En el dominio bancario chileno existen siglas y términos unívocos como 'FOGAPE', 'DICOM', 'Leverage', 'SII F29'. Los embeddings densos generales a veces sufren de falsos positivos semánticos (por ejemplo, confundir FOGAPE con cualquier subsidio estatal genérico). Los n-gramas sparse (1 a 3) capturan la frase exacta con peso TF-IDF sublineal, garantizando que cuando se busca 'cobertura FOGAPE', el Artículo 6 obtenga el score más alto.
  2. **Latencia y Autonomía Operativa:** El cálculo toma 0,002 segundos y no depende de llamadas de red a servidores en el extranjero ni de cuotas de tokens, asegurando 100% de disponibilidad.
  3. **Modularidad:** Nuestra arquitectura está desacoplada mediante una interfaz abstracta; si el banco decidiera conectar un modelo de embeddings como *text-embedding-3-small*, basta con instanciar el cliente sin alterar el resto del pipeline."

#### Pregunta 2: "¿Qué sucede si la API externa de mindicador.cl se cae o no responde?"
* **Integrante a Cargo:** Bárbara Bustamante.
* **Respuesta Técnica:**
  "Diseñamos el componente `EconomicIndicatorsTool` bajo el principio de **Resiliencia y Fallback Degradado**:
  1. Primero, mantiene un archivo de caché local en disco (`indicators_cache.json`) con un TTL (Time To Live) de 1 hora. Si la API falla, el sistema recupera el último valor de la UF registrado válidamente.
  2. En caso de una falla total de red en un arranque frío, el sistema recurre a valores de contingencia normativos predefinidos y emite una advertencia en los metadatos de auditoría, impidiendo que el agente se detenga o lance una excepción no controlada."

#### Pregunta 3: "¿Cómo garantiza su solución que el modelo no sufra de alucinaciones en un entorno tan regulado como el bancario?"
* **Integrante a Cargo:** Nelson Carrasco.
* **Respuesta Técnica:**
  "Implementamos una estrategia de **Defensa en Profundidad** con cuatro barreras:
  1. **Recuperación Estricta (Grounded RAG):** El prompt solo suministra al modelo los fragmentos normativos recuperados y prohíbe explícitamente asumir o interpolar reglas.
  2. **Guardrails Negativos en el System Prompt:** Se instruye al modelo que si una condición o excepción no aparece textualmente en el fragmento, está obligado a declarar que no está tipificada y derivar al Comité Especial según el Art. 11.
  3. **Trazabilidad Mandatoria:** Cada afirmación debe estar anclada a una cita `[Manual de Crédito, Art. X]`.
  4. **Auditoría Cuantitativa:** Desarrollamos el módulo `evaluate_coherence.py`, que valida con expresiones regulares y pruebas automatizadas que el 100% de los dictámenes mantengan correspondencia exacta con las políticas institucionales."

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
  1. **Anonimización en Tránsito:** En el contexto de producción, los datos de los socios y personería son anonimizados o tokenizados antes de cualquier inferencia.
  2. **Aislamiento de Sesión:** El `context_manager.py` opera en memoria local volátil y solo mantiene un buffer acotado de 5 turnos para la interacción en curso, sin persistir datos crediticios sensibles en servidores externos no autorizados por la CMF.
  3. **Principio de Mínimo Privilegio:** El agente sólo tiene acceso a los campos tributarios y comerciales estrictamente necesarios para determinar la pre-admisibilidad de la solicitud."
