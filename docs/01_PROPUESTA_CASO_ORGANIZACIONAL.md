# PROPUESTA DE CASO ORGANIZACIONAL (ANTEPROYECTO)
## Asignatura: ISY0101 - Ingeniería de Soluciones con IA | Duoc UC
## Evaluación Parcial N°1: Diseño de Solución con LLM y RAG
**Integrantes:** Juan Serna, Bárbara Bustamante, Nelson Carrasco  
**Docente:** Profesor Guía ISY0101  
**Fecha:** Septiembre 2026  

---

### 1. Nombre y Breve Descripción de la Organización

* **Nombre de la Organización:** BancoEstado Microempresas / División de Financiamiento PYME (*Contexto simulado basado en el ecosistema bancario público-privado de Chile*).
* **Rubro:** Banca Comercial, Servicios Financieros y Apoyo al Desarrollo Productivo PYME.
* **Tamaño:** Gran Institución Financiera (alcance nacional en Chile, más de 500 sucursales y más de 800.000 clientes micro y pequeñas empresas).
* **Contexto General:** BancoEstado Microempresas es el principal articulador financiero de inclusión productiva en Chile. Su misión es brindar acceso a financiamiento, capital de trabajo y leasing a micro y pequeñas empresas, operando bajo la supervisión de la Comisión para el Mercado Financiero (CMF) y actuando como entidad canalizadora de fondos de garantía estatal como FOGAPE (Fondo de Garantía para Pequeños Empresarios) y programas CORFO.

---

### 2. Identificación y Descripción del Problema / Desafío

* **Descripción del Desafío:** 
  Actualmente, las PYMEs que solicitan financiamiento experimentan un proceso de pre-evaluación crediticia lento, fragmentado y altamente dependiente de ejecutivos de cuentas en sucursales. Los ejecutivos deben consultar manualmente extensos manuales normativos de políticas de riesgo (más de 150 páginas de condiciones de antigüedad, ratios de endeudamiento DTI, matrices de garantías y exclusiones por morosidad comercial), al mismo tiempo que deben consultar fuentes externas dinámicas (el valor de la Unidad de Fomento - UF al día para la conversión de balances, la tasa de política monetaria y los topes de Tasa Máxima Convencional regulados por la CMF).
* **Impacto en la Organización:**
  1. **Tiempos de Respuesta Prolongados:** El proceso de pre-calificación inicial toma entre 7 y 10 días hábiles por cliente, generando deserción de prospectos hacia entidades informales o fintechs no reguladas.
  2. **Inconsistencias y Errores Humanos:** Ejecutivos novatos aplican criterios de riesgo desactualizados o no identifican la elegibilidad de subsidios estatales de garantía (como FOGAPE Chile Apoya), derivando en rechazos indebidos o aprobaciones fuera de política.
  3. **Sobrecarga Operativa:** Más del 60% de las consultas atendidas en mesón corresponden a preguntas repetitivas sobre requisitos de admisibilidad básica que podrían ser resueltas de forma autónoma con trazabilidad regulatoria.

---

### 3. Objetivos de la Intervención

* **Objetivo General:**
  Diseñar e implementar una solución de software inteligente basada en un agente conversacional LLM con arquitectura RAG (Retrieval-Augmented Generation) y herramientas de consulta externa, que automatice la pre-evaluación y asesoría crediticia para clientes PYME de manera confiable, explicable y alineada a las políticas institucionales.
* **Objetivos Específicos:**
  1. **Reducir el Tiempo de Orientación y Pre-filtro:** Pasar de un tiempo medio de atención de 7 días a menos de 2 minutos para la entrega de un dictamen preliminar fundamentado.
  2. **Garantizar Cero Alucinaciones en Políticas de Riesgo (Groundedness > 95%):** Diseñar un pipeline RAG sobre el Manual de Políticas de Crédito que asegure que cada recomendación cite el artículo o acápite normativo correspondiente.
  3. **Integrar Datos Externos en Tiempo Real:** Incorporar una herramienta agéntica (*Tool Calling*) conectada a la API oficial de indicadores económicos de Chile (mindicador.cl / CMF) para resolver la indexación dinámica en UF, Dólar y UTM con exactitud matemática al milisegundo.
  4. **Personalizar el Asesoramiento:** Integrar la consulta a registros internos de clientes (RUT, facturación histórica, endeudamiento previo) para sugerir el producto más idóneo (Crédito Capital de Trabajo, Leasing Operativo o Factoring).

---

### 4. Datos Disponibles o que se Pueden Obtener

#### A. Fuentes Internas (Base de Conocimiento y Registros)
1. **Manual Institucional de Políticas de Crédito PYME (Documento semiestructurado):** Define políticas de antigüedad mínima (ej. 12 meses para persona jurídica con facturación continua), límites de endeudamiento (Razón Deuda/Patrimonio < 2.5), exclusión por quiebra o boletín comercial grave (> $500.000 no justificados), y requisitos para garantías FOGAPE.
2. **Catálogo de Productos Financieros Institucionales:** Detalle de plazos, periodos de gracia, comisiones y condiciones de:
   * Crédito Capital de Trabajo PYME (hasta 36 meses).
   * Leasing Inmobiliario y Maquinaria (hasta 60 meses con opción de compra).
   * Línea de Sobregiro Operacional.
   * Factoring con Cesión Electrónica de Facturas.
3. **Base de Datos Simulada de Empresas PYME (`clientes_pyme.json` / SQLite):** Contiene RUT, razón social, giro comercial, facturación anual (en UF), score de comportamiento histórico interno y vigencia de estatutos.

#### B. Fuentes Externas (APIs y Normativa Pública en Vivo)
1. **API Pública de Indicadores Económicos de Chile (mindicador.cl / CMF):**
   * Endpoint REST en tiempo real que proporciona los valores de la UF (Unidad de Fomento), UTM (Unidad Tributaria Mensual) y Dólar Observado.
   * Permite realizar la conversión fidedigna de montos solicitados en pesos chilenos a UF del día hábil respectivo.
2. **Normativa CMF sobre Tasa Máxima Convencional (TMC):**
   * Reglas de tope crediticio por tramos de colocación financiera.

---

### 5. Restricciones o Requerimientos Particulares

* **Normativa Bancaria y Secreto Bancario (Ley General de Bancos de Chile):** La solución no debe exponer datos sensibles ni compartir información financiera con servicios de terceros no autorizados.
* **Ley N° 19.628 sobre Protección de la Vida Privada / Datos Personales:** Anonimización de datos en el prompt y almacenamiento seguro de sesiones.
* **Requisito de Trazabilidad y Explicabilidad (Explainable AI - XAI):** No se permiten respuestas de "caja negra". Cada pre-aprobación o rechazo debe indicar con precisión:
  * El motivo de la decisión.
  * La sección del Manual de Crédito donde se estipula la condición.
  * El cálculo financiero realizado utilizando el valor de la UF recuperado desde la API externa.
* **Guardrails Anti-Alucinación:** En caso de que un requerimiento o excepción no figure explícitamente en el manual recuperado por RAG, el agente tiene prohibido inventar criterios y debe derivar la consulta al Comité de Crédito Especial.

---

### 6. Motivación para el Uso de Agentes de IA, LLMs y RAG

* **¿Por qué no basta un LLM tradicional (Zero-Shot / Vanilla)?**
  Los LLMs genéricos no conocen las políticas de crédito específicas de BancoEstado, sufren desfase temporal (no conocen el valor de la UF del día de hoy) y sufren de alucinaciones en cálculos financieros y restricciones normativas.
* **¿Por qué se requiere un Pipeline RAG?**
  RAG permite alimentar dinámicamente al LLM con los fragmentos exactos del Manual de Riesgo Institucional, garantizando respuestas fundamentadas en evidencia factual (*grounded generation*) y permitiendo actualizar las políticas del banco sin necesidad de costosos re-entrenamientos (*fine-tuning*).
* **¿Por qué se requiere una Arquitectura Agéntica (Agentic Workflow)?**
  Un RAG estándar únicamente recupera texto estático. El desafío del banco requiere razonamiento multi-paso:
  1. Interpretar la necesidad del usuario.
  2. Identificar el cliente en la base interna.
  3. Ejecutar una herramienta (*tool*) para obtener la UF del día vía API REST.
  4. Recuperar las cláusulas pertinentes mediante búsqueda semántica vectorial.
  5. Razonar y computar si los ratios financieros cumplen el umbral.
  6. Sintetizar un informe de recomendación estructurado.

---

### 7. Referencias y Marco Teórico (Normativa APA 7)

* Comisión para el Mercado Financiero [CMF]. (2025). *Compendio de Normas Contables y de Crédito para Instituciones Bancarias*. CMF Chile. https://www.cmfchile.cl
* Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *Advances in Neural Information Processing Systems (NeurIPS 2020)*, 33, 9459–9474.
* Ministerio de Economía, Fomento y Turismo de Chile. (2024). *Reglamento del Fondo de Garantía para Pequeños Empresarios (FOGAPE)*. Biblioteca del Congreso Nacional de Chile. https://www.bcn.cl
* Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing Reasoning and Acting in Language Models. *International Conference on Learning Representations (ICLR 2023)*.
