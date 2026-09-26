"""
Módulo de Gestión de Contexto y Memoria Conversacional (Context Manager).
Mantiene el historial de interacciones, preserva el estado del cliente consultado
y controla el tamaño de la ventana de contexto para evitar saturación de tokens.
"""

from typing import List, Dict, Any, Optional

class ConversationContextManager:
    def __init__(self, max_history_turns: int = 5):
        self.max_history_turns = max_history_turns
        self.history: List[Dict[str, str]] = []
        self.active_client: Optional[Dict[str, Any]] = None
        self.last_economic_data: Optional[Dict[str, Any]] = None

    def add_turn(self, role: str, content: str):
        """Agrega un turno conversacional al historial."""
        self.history.append({"role": role, "content": content})
        # Mantener solo los últimos N turnos
        if len(self.history) > self.max_history_turns * 2:
            self.history = self.history[-self.max_history_turns * 2:]

    def set_active_client(self, client: Dict[str, Any]):
        """Preserva el cliente actualmente en análisis."""
        self.active_client = client

    def get_active_client(self) -> Optional[Dict[str, Any]]:
        return self.active_client

    def clear(self):
        """Reinicia el estado y memoria de la sesión."""
        self.history.clear()
        self.active_client = None
        self.last_economic_data = None

    def get_history_summary(self) -> str:
        """Retorna un resumen compacto del historial previo para inyectar en prompts."""
        if not self.history:
            return "No hay interacciones previas."
        formatted = []
        for turn in self.history[-4:]:
            formatted.append(f"{turn['role'].capitalize()}: {turn['content'][:150]}...")
        return "\n".join(formatted)
