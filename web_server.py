"""
Servidor Web y Dashboard Interactivo (FastAPI + HTML5/CSS3/JavaScript).
Proporciona una interfaz gráfica moderna para interactuar con el agente RAG PYME-Advisor,
visualizar indicadores macroeconómicos en tiempo real, auditar fuentes recuperadas
y presentar la solución en la defensa oral (IE9).
"""

import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from src.agent.policy_engine import fmt_num
from src.agent.agent_core import PymeAdvisorAgent
from src.tools.economic_indicators import EconomicIndicatorsTool
from src.evaluation.evaluate_coherence import RAGCoherenceEvaluator

app = FastAPI(title="BancoEstado PYME-Advisor Agent API", version="1.0.0")

# Instancia global del agente y herramientas
agent = PymeAdvisorAgent()
econ_tool = EconomicIndicatorsTool()
evaluator = RAGCoherenceEvaluator(agent)

class QueryRequest(BaseModel):
    query: str

@app.get("/api/indicators")
async def get_indicators():
    return econ_tool.get_indicators()

@app.post("/api/query")
async def process_query(req: QueryRequest):
    result = agent.process_query(req.query)
    return JSONResponse(content=result)

@app.get("/api/evaluation")
async def run_evaluation():
    summary = evaluator.run_benchmark_suite()
    return JSONResponse(content=summary)

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    indicators = econ_tool.get_indicators()
    uf_val = indicators.get("uf", {}).get("valor", 41000.0)
    dolar_val = indicators.get("dolar", {}).get("valor", 950.0)
    utm_val = indicators.get("utm", {}).get("valor", 71700.0)

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BancoEstado | PYME-Advisor RAG Agent</title>
    <style>
        :root {{
            --primary: #003399;
            --primary-light: #0055cc;
            --accent: #f28b00;
            --bg-page: #f4f6fa;
            --surface: #ffffff;
            --text-main: #1f2937;
            --text-muted: #6b7280;
            --border: #e5e7eb;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
        body {{ background-color: var(--bg-page); color: var(--text-main); line-height: 1.5; }}
        header {{ background: linear-gradient(135deg, var(--primary) 0%, #001f5c 100%); color: white; padding: 1.25rem 2rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
        .header-title h1 {{ font-size: 1.4rem; font-weight: 700; letter-spacing: -0.5px; }}
        .header-title p {{ font-size: 0.85rem; opacity: 0.85; }}
        .indicators-bar {{ display: flex; gap: 1rem; }}
        .indicator-badge {{ background: rgba(255,255,255,0.12); backdrop-filter: blur(4px); padding: 0.4rem 0.8rem; border-radius: 6px; font-size: 0.8rem; border: 1px solid rgba(255,255,255,0.2); }}
        .indicator-badge span {{ font-weight: bold; color: #ffca7a; }}
        
        .main-container {{ display: grid; grid-template-columns: 1.6fr 1fr; gap: 1.5rem; padding: 1.5rem 2rem; max-width: 1400px; margin: 0 auto; height: calc(100vh - 85px); }}
        .card {{ background: var(--surface); border-radius: 12px; border: 1px solid var(--border); box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: flex; flex-direction: column; overflow: hidden; }}
        .card-header {{ padding: 1rem 1.25rem; border-bottom: 1px solid var(--border); background: #fafbfc; display: flex; justify-content: space-between; align-items: center; }}
        .card-header h2 {{ font-size: 1.05rem; font-weight: 600; color: var(--primary); }}
        
        .chat-history {{ flex: 1; padding: 1.25rem; overflow-y: auto; display: flex; flex-direction: column; gap: 1rem; }}
        .chat-bubble {{ padding: 1rem 1.2rem; border-radius: 10px; max-width: 90%; font-size: 0.92rem; line-height: 1.5; }}
        .chat-bubble.user {{ background: #e8f0fe; color: #174ea6; align-self: flex-end; border-bottom-right-radius: 2px; }}
        .chat-bubble.agent {{ background: #ffffff; border: 1px solid var(--border); align-self: flex-start; border-bottom-left-radius: 2px; box-shadow: 0 2px 4px rgba(0,0,0,0.03); }}
        .chat-bubble.agent h3 {{ font-size: 1rem; color: var(--primary); margin: 0.8rem 0 0.4rem 0; padding-bottom: 0.2rem; border-bottom: 1px solid #eef2f6; }}
        .chat-bubble.agent h3:first-child {{ margin-top: 0; }}
        .chat-bubble.agent ul, .chat-bubble.agent ol {{ margin-left: 1.25rem; margin-top: 0.3rem; }}
        .chat-bubble.agent li {{ margin-bottom: 0.25rem; }}
        
        .quick-actions {{ padding: 0.75rem 1.25rem; background: #f8fafc; border-top: 1px solid var(--border); display: flex; gap: 0.5rem; flex-wrap: wrap; }}
        .quick-btn {{ background: white; border: 1px solid #cbd5e1; padding: 0.35rem 0.7rem; border-radius: 6px; font-size: 0.75rem; cursor: pointer; transition: all 0.15s ease; color: #475569; font-weight: 500; }}
        .quick-btn:hover {{ background: #f1f5f9; border-color: var(--primary); color: var(--primary); }}
        
        .chat-input-area {{ padding: 1rem 1.25rem; border-top: 1px solid var(--border); display: flex; gap: 0.75rem; background: white; }}
        .chat-input {{ flex: 1; padding: 0.75rem 1rem; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 0.9rem; outline: none; }}
        .chat-input:focus {{ border-color: var(--primary); box-shadow: 0 0 0 3px rgba(0,51,153,0.1); }}
        .send-btn {{ background: var(--primary); color: white; border: none; padding: 0 1.25rem; border-radius: 8px; font-weight: 600; cursor: pointer; transition: background 0.15s; }}
        .send-btn:hover {{ background: var(--primary-light); }}
        
        .sidebar {{ display: flex; flex-direction: column; gap: 1rem; height: 100%; overflow-y: auto; }}
        .meta-section {{ padding: 1rem; border-bottom: 1px solid var(--border); }}
        .meta-section:last-child {{ border-bottom: none; }}
        .meta-title {{ font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-muted); font-weight: 700; margin-bottom: 0.6rem; }}
        .source-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.6rem; margin-bottom: 0.5rem; font-size: 0.8rem; }}
        .source-header {{ display: flex; justify-content: space-between; font-weight: 600; color: #334155; margin-bottom: 0.2rem; }}
        .badge-score {{ background: #dbeafe; color: #1e40af; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.7rem; }}
        
        .benchmark-box {{ background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 0.8rem; font-size: 0.82rem; }}
        .benchmark-btn {{ width: 100%; margin-top: 0.5rem; background: #059669; color: white; border: none; padding: 0.5rem; border-radius: 6px; cursor: pointer; font-weight: 600; }}
        .benchmark-btn:hover {{ background: #047857; }}
    </style>
</head>
<body>
    <header>
        <div class="header-title">
            <h1>BancoEstado Microempresas | PYME-Advisor</h1>
            <p>ISY0101 Ingeniería de Soluciones con IA | Duoc UC — Equipo: Juan Serna, Bárbara Bustamante, Nelson Carrasco · Prototipo académico con datos simulados; no es un servicio de BancoEstado</p>
        </div>
        <div class="indicators-bar">
            <div class="indicator-badge">UF Hoy: <span id="uf-display">${fmt_num(uf_val, 2)} CLP</span></div>
            <div class="indicator-badge">Dólar: <span id="dolar-display">${fmt_num(dolar_val, 2)} CLP</span></div>
            <div class="indicator-badge">UTM: <span id="utm-display">${fmt_num(utm_val, 2)} CLP</span></div>
        </div>
    </header>

    <div class="main-container">
        <!-- Panel de Conversación -->
        <div class="card">
            <div class="card-header">
                <h2>Asesor Virtual de Riesgo y Financiamiento Comercial</h2>
                <span style="font-size: 0.8rem; color: #059669; font-weight: 600;">● RAG Activo (Grounded)</span>
            </div>
            
            <div class="chat-history" id="chat-history">
                <div class="chat-bubble agent">
                    <h3>Bienvenido a PYME-Advisor</h3>
                    <p>Soy el asistente inteligente de evaluación y riesgo crediticio de <strong>BancoEstado Microempresas</strong>. Puedo asesorarle sobre líneas de financiamiento (Capital de Trabajo, Leasing y Factoring), consultar requisitos normativos, calcular conversiones en tiempo real en UF/CLP y evaluar la pre-admisibilidad de su empresa según el manual de políticas (simulado) del prototipo.</p>
                    <p style="margin-top: 0.5rem; font-size: 0.85rem; color: var(--text-muted);">Puede ingresar el RUT de su empresa o seleccionar uno de los casos de demostración a continuación:</p>
                </div>
            </div>

            <div class="quick-actions">
                <button class="quick-btn" onclick="sendQuick(1)">Caso 1: Transportes Biobío (Leasing 1.500 UF)</button>
                <button class="quick-btn" onclick="sendQuick(2)">Caso 2: Panadería El Trigal (Rechazo DICOM)</button>
                <button class="quick-btn" onclick="sendQuick(3)">Caso 3: Constructora del Sur (Comité Art. 11)</button>
                <button class="quick-btn" onclick="sendQuick(4)">Consulta: Cobertura FOGAPE</button>
            </div>

            <div class="chat-input-area">
                <input type="text" id="user-input" class="chat-input" placeholder="Escriba su consulta o RUT (ej: 'Queremos 1.500 UF para comprar un camión con RUT 76.123.456-K')..." onkeydown="if(event.key==='Enter') sendQuery()">
                <button class="send-btn" id="send-btn" onclick="sendQuery()">Consultar Agente</button>
            </div>
        </div>

        <!-- Panel Lateral de Auditoría y Métricas -->
        <div class="sidebar">
            <div class="card">
                <div class="card-header">
                    <h2>Auditoría RAG y Trazabilidad (IE3, IE6)</h2>
                </div>
                
                <div class="meta-section">
                    <div class="meta-title">Cliente Identificado en Sistema</div>
                    <div id="client-info" style="font-size: 0.85rem; color: #334155; font-weight: 500;">Ninguno seleccionado</div>
                </div>

                <div class="meta-section">
                    <div class="meta-title">Herramientas Externas Ejecutadas (Tools)</div>
                    <div id="tools-executed-list" style="font-size: 0.8rem; color: #475569;">
                        - API mindicador.cl (UF en vivo conectada)
                    </div>
                </div>

                <div class="meta-section">
                    <div class="meta-title">Fuentes Normativas Recuperadas (Vector Store)</div>
                    <div id="sources-list">
                        <div style="font-size: 0.8rem; color: #94a3b8;">Realice una consulta para inspeccionar los fragmentos normativos recuperados.</div>
                    </div>
                </div>

                <div class="meta-section">
                    <div class="meta-title">Evaluación de Coherencia RAG (IE6)</div>
                    <div class="benchmark-box">
                        <div style="font-weight: 600; color: #065f46;">Métricas de Calidad y Fidelidad</div>
                        <div id="benchmark-metrics" style="margin-top: 0.3rem;">
                            Presione el botón para ejecutar la batería de 7 casos.
                        </div>
                        <button class="benchmark-btn" onclick="runBenchmark()">Ejecutar Batería de Pruebas (7 Casos)</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const quickQueries = {{
            1: "Hola, represento a Transportes y Logistica Biobio SpA (RUT 76.123.456-K). Queremos solicitar 1.500 UF para renovar un camión tolva. ¿Calificamos y cuánto es en pesos?",
            2: "Hola, soy de Panaderia y Alimentos El Trigal EIRL (RUT 76.999.888-4) y necesitamos 800 UF para capital de trabajo.",
            3: "Constructora del Sur SA (RUT 76.543.210-8) solicita ampliación de línea de crédito de 4.000 UF para obras menores.",
            4: "¿Cuáles son las condiciones y porcentajes de cobertura del fondo de garantía estatal FOGAPE para las PYMEs?"
        }};

        function sendQuick(idx) {{
            document.getElementById('user-input').value = quickQueries[idx];
            sendQuery();
        }}

        async function sendQuery() {{
            const input = document.getElementById('user-input');
            const q = input.value.trim();
            if (!q) return;

            const chatHistory = document.getElementById('chat-history');
            
            // Mensaje usuario
            const userBubble = document.createElement('div');
            userBubble.className = 'chat-bubble user';
            userBubble.innerText = q;
            chatHistory.appendChild(userBubble);
            input.value = '';

            // Mensaje pensando
            const loadingBubble = document.createElement('div');
            loadingBubble.className = 'chat-bubble agent';
            loadingBubble.id = 'loading-bubble';
            loadingBubble.innerText = 'Consultando RAG, evaluando políticas y calculando UF...';
            chatHistory.appendChild(loadingBubble);
            chatHistory.scrollTop = chatHistory.scrollHeight;

            try {{
                const res = await fetch('/api/query', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ query: q }})
                }});
                const data = await res.json();
                
                chatHistory.removeChild(loadingBubble);

                const agentBubble = document.createElement('div');
                agentBubble.className = 'chat-bubble agent';
                
                // Formatear markdown básico a HTML
                let formatted = data.response
                    .replace(/### (.*?)\\n/g, '<h3>$1</h3>')
                    .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                    .replace(/\\n- /g, '<br>• ')
                    .replace(/\\n1\\. /g, '<br>1. ')
                    .replace(/\\n2\\. /g, '<br>2. ')
                    .replace(/\\n3\\. /g, '<br>3. ')
                    .replace(/\\n/g, '<br>');
                
                agentBubble.innerHTML = formatted;
                chatHistory.appendChild(agentBubble);
                chatHistory.scrollTop = chatHistory.scrollHeight;

                // Actualizar panel lateral
                document.getElementById('client-info').innerHTML = data.client_identified ? 
                    `<strong>${{data.client_identified}}</strong><br><span style="color:#64748b;">RUT: ${{data.client_rut}}</span>` : 
                    'Consulta General (Sin cliente asociado)';

                // Herramientas
                const toolsDiv = document.getElementById('tools-executed-list');
                toolsDiv.innerHTML = data.tools_executed.map(t => `<div>• <strong>${{t.tool}}</strong>: ${{t.data}}</div>`).join('')
                    + `<div>• <strong>Generación</strong>: ${{data.generation_mode}}</div>`
                    + `<div>• <strong>Guardrail de citas</strong>: ${{data.citation_validation.supported.length}}/${{data.citation_validation.cited.length}} citas respaldadas por fragmentos recuperados</div>`;

                // Fuentes
                const sourcesDiv = document.getElementById('sources-list');
                sourcesDiv.innerHTML = data.retrieved_sources.map(s => `
                    <div class="source-card">
                        <div class="source-header">
                            <span>[${{s.article}}] ${{s.heading}}</span>
                            <span class="badge-score">${{(s.similarity*100).toFixed(1)}}%</span>
                        </div>
                        <div style="color: #64748b; font-size: 0.75rem;">Archivo: ${{s.source}} · sub-consulta: ${{s.retrieved_for}}</div>
                    </div>
                `).join('');

            }} catch (err) {{
                if (document.getElementById('loading-bubble')) {{
                    chatHistory.removeChild(loadingBubble);
                }}
                alert('Error al procesar consulta: ' + err);
            }}
        }}

        async function runBenchmark() {{
            const btn = document.querySelector('.benchmark-btn');
            btn.innerText = 'Ejecutando pruebas...';
            btn.disabled = true;
            try {{
                const res = await fetch('/api/evaluation');
                const data = await res.json();
                document.getElementById('benchmark-metrics').innerHTML = `
                    - Precisión de Dictamen: <strong>${{data.overall_status_accuracy}}</strong><br>
                    - Recall de Recuperación: <strong>${{data.context_recall}}</strong> (línea base ${{data.baseline_context_recall}})<br>
                    - Groundedness de Citas: <strong>${{data.average_groundedness_score}}</strong><br>
                    - Consistencia Matemática: <strong>${{data.math_consistency_rate}}</strong><br>
                    - Latencia Promedio: <strong>${{data.average_latency_seconds}}</strong>
                `;
            }} catch (e) {{
                alert('Error al ejecutar evaluación: ' + e);
            }} finally {{
                btn.innerText = 'Re-ejecutar Batería de Pruebas (5 Casos)';
                btn.disabled = false;
            }}
        }}
    </script>
</body>
</html>
"""
    return html_content

if __name__ == "__main__":
    import uvicorn
    print("Iniciando Servidor Web BancoEstado PYME-Advisor en http://localhost:8000 ...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
