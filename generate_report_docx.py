"""
Generador del Informe Técnico (Word .docx) de la EP1 ISY0101.
Produce docs/INFORME_TECNICO_SOLUCION_RAG.docx (máximo 5 páginas, referencias APA 7).
Ejecutar desde la raíz del repositorio:  python generate_report_docx.py
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AZUL = RGBColor(0, 51, 153)
GRIS = RGBColor(40, 40, 40)
REPO_URL = "https://github.com/nelscarrasco/PYME-Advisor_ISY0101_BancoEstado"

REFLEXION_JUAN = "Durante el desarrollo del proyecto, mi principal foco técnico fue estructurar la segmentación jerárquica de los documentos normativos de BancoEstado y validar el almacén vectorial. Comprobé empíricamente que en un sistema RAG financiero, la precisión del retrieval depende del respeto a la estructura legal de los textos: fragmentar por párrafos continuos destruye el vínculo entre los artículos y sus excepciones. La automatización de pruebas cuantitativas de coherencia me permitió entender el rigor con que se debe auditar un sistema de recomendación en entornos bancarios regulados."
REFLEXION_BARBARA = "Mi participación se centró en la orquestación agéntica y la integración de la API externa de indicadores económicos en tiempo real. Constatar cómo la llamada a herramientas (Tool Calling) resuelve la obsolescencia temporal de los modelos fue el aprendizaje más valioso: conectar el valor diario de la UF con las reglas de riesgo transforma una consulta estática en una herramienta operativa de alto impacto financiero. Asimismo, la vinculación de clientes por RUT y validación de ratios tributarios permitió asegurar trazabilidad en cada dictamen."
REFLEXION_NELSON = "Mi trabajo se concentró en la ingeniería de prompts, el diseño de guardrails negativos estrictos para evitar alucinaciones y la gestión de memoria conversacional. En banca comercial es crítico restringir el alcance a pre-admisibilidad técnica preliminar sin generar compromisos contractuales involuntarios. Implementar vallas de seguridad que obligan a derivar al Comité de Crédito los casos no tipificados garantizó la solidez del sistema frente a consultas atípicas o de riesgo crediticio."
CONCLUSION = "La implementación de la arquitectura PYME-Advisor demuestra que la combinación de agentes inteligentes, pipelines RAG semánticos y consumo de herramientas en tiempo real resuelve integralmente las deficiencias de los modelos generativos puros en entornos corporativos de alta regulación. El desacoplamiento entre la base de conocimiento interna (políticas de crédito) y las fuentes externas dinámicas (API macroeconómica de la UF) garantiza explicabilidad, auditabilidad ante la CMF y cero alucinaciones en cálculos patrimoniales."


def shade(cell, fill_hex):
    cell._tc.get_or_add_tcPr().append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))


def heading(doc, text, size=12):
    h = doc.add_heading(level=1)
    h.paragraph_format.space_before = Pt(8)
    h.paragraph_format.space_after = Pt(3)
    r = h.add_run(text)
    r.font.size = Pt(size)
    r.bold = True
    r.font.color.rgb = AZUL


def para(doc, parts, after=4, size=None):
    """parts: str o lista de (texto, bold)."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if isinstance(parts, str):
        parts = [(parts, False)]
    for text, bold in parts:
        r = p.add_run(text)
        r.bold = bold
        if size:
            r.font.size = Pt(size)
    return p


def bullet(doc, label, text, after=1):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(after)
    if label:
        p.add_run(label).bold = True
    p.add_run(text)
    return p


def table(doc, headers, rows, widths=None, font=8):
    t = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.cell(0, i)
        shade(c, "003399")
        r = c.paragraphs[0].add_run(h)
        r.bold = True
        r.font.size = Pt(font)
        r.font.color.rgb = RGBColor(255, 255, 255)
    for ri, row in enumerate(rows, start=1):
        for ci, text in enumerate(row):
            c = t.cell(ri, ci)
            shade(c, "F1F5F9" if ri % 2 == 0 else "FFFFFF")
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.add_run(text).font.size = Pt(font)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return t


def figure(doc, rel_path, width_in, caption):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_picture(os.path.join(BASE_DIR, rel_path), width=Inches(width_in))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(6)
    r = c.add_run(caption)
    r.italic = True
    r.font.size = Pt(8.5)
    r.font.color.rgb = RGBColor(90, 90, 90)


def pending(p, text):
    r = p.add_run(text)
    r.font.highlight_color = WD_COLOR_INDEX.YELLOW


def create_report_docx(output_path=os.path.join(BASE_DIR, "docs", "INFORME_TECNICO_SOLUCION_RAG.docx")):
    doc = docx.Document()
    for s in doc.sections:
        s.top_margin = s.bottom_margin = Inches(0.8)
        s.left_margin = s.right_margin = Inches(0.8)
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10)
    normal.font.color.rgb = GRIS

    # Encabezado
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run("ISY0101 - INGENIERÍA DE SOLUCIONES CON IA | DUOC UC\nEVALUACIÓN PARCIAL N°1 - ENCARGO")
    r.font.size = Pt(8.5)
    r.bold = True
    r.font.color.rgb = RGBColor(120, 120, 120)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("PYME-Advisor: Agente con LLM y RAG para la Pre-Evaluación Crediticia de PYMEs en BancoEstado Microempresas")
    r.font.size = Pt(16)
    r.bold = True
    r.font.color.rgb = AZUL
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(f"Integrantes: Juan Serna, Bárbara Bustamante, Nelson Carrasco | Fecha: 25 de septiembre de 2026 | Repositorio: {REPO_URL}")
    r.font.size = Pt(9)
    r.italic = True
    r.font.color.rgb = RGBColor(100, 100, 100)

    # 1. Caso
    heading(doc, "1. Análisis del Caso Organizacional y Requerimientos (IE1)")
    para(doc, [("Organización. ", True), ("BancoEstado Microempresas es la filial de BancoEstado orientada al financiamiento de micro y pequeñas empresas en todo Chile, con productos de capital de trabajo, leasing y factoring y acceso a garantías estatales como FOGAPE. Las MiPymes superan 1,2 millones de empresas, representan el 98,5% de las empresas formales del país y concentran el 48% del empleo (Ministerio de Economía, Fomento y Turismo, 2026), por lo que la velocidad y consistencia con que se evalúa su acceso al crédito tiene impacto directo.", False)])
    para(doc, [("Problema. ", True), ("La pre-evaluación inicial de una solicitud exige que el ejecutivo cruce manualmente tres fuentes: (a) el manual interno de políticas de riesgo (antigüedad, morosidad, endeudamiento, garantías y atribuciones), (b) los antecedentes del cliente y (c) indicadores que cambian a diario, como la UF, en la que se expresan montos y tramos. Esto produce demoras, criterios dispares entre ejecutivos y errores de conversión UF–CLP. Un LLM genérico no resuelve el problema: desconoce las políticas internas, no conoce la UF del día y puede inventar requisitos.", False)])
    para(doc, [("Alcance. ", True), ("La organización es real, pero el Manual de Políticas de Crédito (11 artículos), el Catálogo de Productos (4 secciones) y la base de 5 clientes son documentos simulados construidos por el equipo; no son normativa oficial de BancoEstado.", False)])
    para(doc, [("Requerimientos y objetivos medibles:", True)], after=1)
    bullet(doc, "R1 Dictamen preliminar trazable: ", "estado PRE-ADMISIBLE / NO ADMISIBLE / COMITÉ en menos de 2 s, sin emitir aprobaciones definitivas.")
    bullet(doc, "R2 Fidelidad normativa: ", "100% de las citas del dictamen respaldadas por un fragmento recuperado del manual (meta mínima 95%).")
    bullet(doc, "R3 Datos externos vigentes: ", "conversión UF→CLP exacta con el valor del día obtenido por API, con continuidad si la API falla.")
    bullet(doc, "R4 Control de riesgo: ", "derivación automática al Comité en los supuestos del Art. 11 y respeto al secreto bancario y a la Ley 19.628 (sólo se envían al modelo los campos necesarios del cliente).", after=4)

    # 2. Prompts
    heading(doc, "2. Formulación de Prompts (IE2)")
    para(doc, "El prompt se ensambla en src/agent/prompts.py en bloques ordenados: (1) system prompt con rol y reglas, (2) ejemplo few-shot de un dictamen completo, (3) memoria de sesión, (4) indicadores de la API, (5) perfil del cliente, (6) fragmentos RAG con fuente y relevancia, (7) resultado del motor de reglas y (8) la consulta. Extracto del system prompt:", after=3)
    t = doc.add_table(rows=1, cols=1)
    c = t.cell(0, 0)
    shade(c, "F1F5F9")
    r = c.paragraphs[0].add_run(
        'Eres "PYME-Advisor", Agente Consultor de Riesgo Crediticio de BancoEstado Microempresas.\n'
        "1. FIDELIDAD: basa tus conclusiones EXCLUSIVAMENTE en el contexto provisto; PROHIBIDO inventar requisitos, plazos o montos.\n"
        '   Si el caso no está en el manual: "debe elevarse a evaluación especial".\n'
        "2. TRAZABILIDAD: toda afirmación normativa cita [Manual de Crédito, Art. X] o [Catálogo de Productos, Sección N].\n"
        "3. DATOS EXTERNOS: convierte todo monto UF a CLP con el valor de la API y cita la fuente.\n"
        "4. ESTADO: debe coincidir con el MOTOR DE REGLAS; explícalo, no lo recalcules. Nunca emitas aprobación definitiva.\n"
        "5. FORMATO: 1) Dictamen 2) Fundamentación 3) Garantías/FOGAPE 4) Producto 5) Documentación.")
    r.font.name = "Consolas"
    r.font.size = Pt(8)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    para(doc, [("Justificación. ", True), ("El rol fija el registro y el umbral de prudencia bancaria. Las restricciones negativas y la cláusula de escape (\"elevar a evaluación especial\") reducen el espacio de respuesta a lo que el contexto respalda. La cita obligatoria con formato fijo permite verificar automáticamente cada afirmación (sección 5). Entregar al modelo el resultado del motor de reglas evita que el LLM decida el estado crediticio, que es la parte con mayor riesgo regulatorio. El few-shot y la temperatura 0,1 estabilizan el formato de 5 secciones.", False)])

    # 3. RAG
    heading(doc, "3. Diseño e Implementación del Pipeline RAG (IE3)")
    bullet(doc, "Fuentes internas: ", "Manual de Crédito y Catálogo (Markdown) segmentados por encabezado y artículo (chunker.py), generando 27 fragmentos con metadatos de fuente, título y artículo/sección; base de clientes JSON consultada por RUT (ClientLookupTool).")
    bullet(doc, "Fuente externa: ", "API pública mindicador.cl (valores del Banco Central de Chile) para UF, dólar y UTM (EconomicIndicatorsTool), con caché de 1 hora; si la API falla usa el último valor real guardado y, en último caso, valores de contingencia, informando siempre la fuente usada.")
    bullet(doc, "Índice y búsqueda: ", "TF-IDF con n-gramas 1–3 y similitud coseno (vector_store.py). La consulta se descompone en sub-consultas por dimensión de riesgo (segmento, antigüedad, morosidad, endeudamiento, FOGAPE, garantías, producto, documentos y comité), se recupera el top-1/2 de cada una y se unen sin duplicados.", after=3)
    figure(doc, "docs/diagramas/flujo_rag.png", 5.0, "Figura 1. Flujo de información por consulta: herramientas internas y externas, motor de reglas, recuperación multi-consulta, generación y verificación.")

    # 4. Arquitectura
    heading(doc, "4. Arquitectura de la Solución (IE4)")
    figure(doc, "docs/diagramas/arquitectura.png", 4.0, "Figura 2. Arquitectura por capas de PYME-Advisor (fuente editable: docs/diagramas/arquitectura.mmd).")
    table(doc, ["Módulo", "Archivo", "Función en la arquitectura"], [
        ("Interfaz", "app.py, web_server.py", "CLI y dashboard FastAPI con panel de auditoría (herramientas, fragmentos, guardrail)."),
        ("Orquestador", "agent_core.py", "Extrae RUT/monto, invoca herramientas, recupera, genera y verifica la salida."),
        ("Motor de reglas", "policy_engine.py", "Aplica los Art. 1, 3, 4, 5 y 11 y fija el estado preliminar de forma determinista."),
        ("Recuperación", "chunker.py, vector_store.py", "Segmentación por artículo e índice TF-IDF con búsqueda multi-consulta."),
        ("Herramientas", "client_lookup.py, economic_indicators.py", "Base interna de clientes y API de indicadores con caché y respaldo."),
        ("Contexto", "context_manager.py", "Memoria de sesión (5 turnos) y cliente activo para preguntas de seguimiento."),
        ("Generación", "prompts.py + gpt-4o-mini", "LLM si existe OPENAI_API_KEY; si no, motor de síntesis local que redacta sólo con artículos recuperados."),
        ("Guardrail de salida", "agent_core.validate_citations", "Marca toda cita sin fragmento de respaldo y corrige un estado que contradiga al motor de reglas."),
    ], widths=[1.3, 1.9, 3.7])

    # 5. Evaluación
    heading(doc, "5. Evaluación, Decisiones de Diseño y Resultados (IE5)")
    para(doc, "La batería src/evaluation/evaluate_coherence.py ejecuta 7 casos con resultado esperado conocido y mide la coherencia entre los datos recuperados y la respuesta:", after=3)
    table(doc, ["Caso", "Esperado = Obtenido", "Artículos requeridos (recuperados)", "Citas respaldadas"], [
        ("1. Transportes Biobío, leasing 1.500 UF", "PRE-ADMISIBLE", "3, 4, 5, 6, 9 (100%)", "100%"),
        ("2. Panadería El Trigal, 800 UF, DICOM $1,25 M", "NO ADMISIBLE", "4 (100%)", "100%"),
        ("3. Constructora del Sur, leverage 3,4x, DSCR 1,1", "COMITÉ", "5, 11 (100%)", "100%"),
        ("4. Frutícola Express, 5 meses", "NO ADMISIBLE", "3 (100%)", "100%"),
        ("5. TecnoAgro, capital de trabajo 600 UF", "PRE-ADMISIBLE", "3, 4, 5, 6, 8 (100%)", "100%"),
        ("6. TecnoAgro, 12.000 UF", "COMITÉ", "11 (100%)", "100%"),
        ("7. Consulta general FOGAPE", "INFORMACIÓN GENERAL", "6 (100%)", "100%"),
    ], widths=[2.6, 1.4, 1.9, 1.0])
    para(doc, [("Resultados: ", True), ("precisión de dictamen 100%; recall de recuperación 100% frente a 17,1% de la línea base que busca sólo con la consulta original (top-3); groundedness de citas 100%; consistencia UF→CLP 100%; latencia bajo 0,3 s por consulta. Además, 17 pruebas unitarias (unittest) aprobadas. Logs y capturas en docs/evidencias.", False)])
    table(doc, ["Decisión", "Alternativa descartada", "Justificación"], [
        ("Motor de reglas + LLM", "Que el LLM decida el estado", "La decisión crediticia debe ser auditable y reproducible; el LLM explica y el motor decide."),
        ("Descomposición en sub-consultas", "Búsqueda única top-k", "Una consulta cubre varias reglas; medido: recall 17,1% → 100%."),
        ("TF-IDF 1–3 gramas", "Embeddings densos", "Corpus pequeño y terminología exacta (DICOM, FOGAPE, UF); sin costo ni dependencia externa. Se revisará si crece el corpus."),
        ("Chunking por artículo", "Ventanas fijas de caracteres", "Una regla y su excepción quedan en el mismo fragmento y la cita al artículo es inequívoca."),
        ("Verificación de citas", "Confiar en el prompt", "El prompt no garantiza fidelidad; la verificación la mide y la hace visible al ejecutivo."),
        ("Caché + último valor real", "Consultar la API siempre", "Evita la latencia y la caída del servicio sin inventar valores."),
    ], widths=[1.6, 1.6, 3.7])
    para(doc, [("Limitaciones: ", True), ("las métricas se midieron con el motor de síntesis local (sin OPENAI_API_KEY); con el LLM activo la redacción no es determinista y debe re-evaluarse con la misma batería. Los puntajes de similitud TF-IDF son moderados (0,2–0,6). Los documentos y clientes son simulados.", False)])

    # 6. Conclusiones y reflexiones
    heading(doc, "6. Conclusiones y Reflexiones Individuales")
    para(doc, [("Conclusiones del proyecto: ", True), (CONCLUSION, False)])
    para(doc, [("Reflexión individual - Juan Serna: ", True), (REFLEXION_JUAN, False)])
    para(doc, [("Reflexión individual - Bárbara Bustamante: ", True), (REFLEXION_BARBARA, False)])
    para(doc, [("Reflexión individual - Nelson Carrasco: ", True), (REFLEXION_NELSON, False)])

    # 7. IA y referencias
    heading(doc, "7. Declaración de Uso de IA y Referencias (APA 7)", size=11)
    p = para(doc, [("Uso de IA: ", True), ("conforme a las indicaciones de la evaluación, el equipo declara que utilizó Claude (Anthropic, 2026) para revisar la completitud del encargo frente a la pauta, corregir y ampliar el código (motor de reglas, recuperación multi-consulta, verificación de citas y evaluador), redactar y revisar este informe y el README, generar los diagramas y capturar la evidencia de pruebas. ", False)])
    pending(p, "[COMPLETAR: otras herramientas de IA usadas y para qué.] ")
    p.add_run("Todo el contenido generado fue revisado y validado por el equipo. ")
    pending(p, "[CONFIRMAR: las conclusiones y reflexiones individuales fueron redactadas por el equipo sin apoyo de IA.]")
    refs = [
        "Anthropic. (2026). Claude (versión Opus 5.5) [Modelo de lenguaje de gran tamaño]. https://claude.ai",
        "Comisión para el Mercado Financiero. (s.f.). Recopilación Actualizada de Normas de Bancos (RAN). https://www.cmfchile.cl/portal/principal/613/w3-propertyvalue-29580.html",
        "Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. Advances in Neural Information Processing Systems, 33, 9459–9474.",
        "mindicador.cl. (s.f.). API de indicadores económicos diarios en Chile. https://mindicador.cl",
        "Ministerio de Economía, Fomento y Turismo. (2026). MiPymes y emprendimiento. https://www.economia.gob.cl/wp-content/uploads/2026/02/10-03-26-mipymes-y-emprendimiento.pdf",
        "Shuster, K., Poff, S., Chen, M., Kiela, D., & Weston, J. (2021). Retrieval augmentation reduces hallucination in conversation. En Findings of the Association for Computational Linguistics: EMNLP 2021 (pp. 3784–3803).",
        "Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. International Conference on Learning Representations (ICLR 2023).",
    ]
    for ref in refs:
        rp = doc.add_paragraph()
        rp.paragraph_format.space_after = Pt(1)
        rp.paragraph_format.left_indent = Inches(0.3)
        rp.paragraph_format.first_line_indent = Inches(-0.3)
        rr = rp.add_run(ref)
        rr.font.size = Pt(8.5)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    doc.save(output_path)
    print(f"Documento Word generado en: {output_path}")


if __name__ == "__main__":
    create_report_docx()
