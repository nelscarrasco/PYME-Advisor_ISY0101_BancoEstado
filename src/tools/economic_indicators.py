"""
Módulo de Integración Externa: Indicadores Económicos Oficiales de Chile.
Recupera valores en tiempo real de UF, UTM y Dólar Observado desde la API pública de mindicador.cl.
Incluye mecanismo de caché local y resiliencia ante caídas de red.
"""

import requests
import json
import os
import time
from typing import Dict, Any, Optional

CACHE_FILE = os.path.join(os.path.dirname(__file__), "indicators_cache.json")
CACHE_EXPIRY_SECONDS = 3600  # 1 hora de vigencia de caché

class EconomicIndicatorsTool:
    def __init__(self, api_url: str = "https://mindicador.cl/api"):
        self.api_url = api_url
        self._cached_data = None

    def get_indicators(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Obtiene los indicadores económicos actuales (UF, UTM, Dólar).
        Utiliza caché local en disco para evitar sobrecargar la API y garantizar disponibilidad offline.
        """
        # 1. Intentar leer desde caché si es válida
        if not force_refresh and os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    cache_content = json.load(f)
                    cache_time = cache_content.get("_timestamp", 0)
                    if time.time() - cache_time < CACHE_EXPIRY_SECONDS:
                        return cache_content.get("data", {})
            except Exception:
                pass  # Si falla la lectura de caché, intentar llamada en vivo

        # Si la API falló hace poco en esta sesión, no se reintenta (evita esperar el timeout en cada consulta)
        if not force_refresh and self._cached_data and time.time() - self._cached_data["_ts"] < 300:
            return self._cached_data["data"]

        # 2. Consultar API en vivo
        try:
            response = requests.get(self.api_url, timeout=6)
            if response.status_code == 200:
                raw_data = response.json()
                processed = {
                    "uf": {
                        "nombre": "Unidad de Fomento",
                        "valor": float(raw_data.get("uf", {}).get("valor", 41000.0)),
                        "fecha": raw_data.get("uf", {}).get("fecha", ""),
                        "unidad": "Pesos Chilenos (CLP)"
                    },
                    "dolar": {
                        "nombre": "Dólar Observado",
                        "valor": float(raw_data.get("dolar", {}).get("valor", 950.0)),
                        "fecha": raw_data.get("dolar", {}).get("fecha", ""),
                        "unidad": "Pesos Chilenos (CLP)"
                    },
                    "utm": {
                        "nombre": "Unidad Tributaria Mensual",
                        "valor": float(raw_data.get("utm", {}).get("valor", 71700.0)),
                        "fecha": raw_data.get("utm", {}).get("fecha", ""),
                        "unidad": "Pesos Chilenos (CLP)"
                    },
                    "fuente": "mindicador.cl / Banco Central de Chile"
                }

                # Guardar en caché
                try:
                    with open(CACHE_FILE, "w", encoding="utf-8") as f:
                        json.dump({"_timestamp": time.time(), "data": processed}, f, indent=2, ensure_ascii=False)
                except Exception:
                    pass

                return processed
        except Exception as e:
            # Fallback en caso de que la red falle o esté sin conexión
            print(f"[Aviso] No se pudo conectar a la API en vivo ({e.__class__.__name__}). Usando último valor disponible.")

        # 3a. Fallback: último valor real guardado en caché (aunque esté vencido)
        fallback = None
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    fallback = json.load(f).get("data")
                fecha = str(fallback["uf"].get("fecha", ""))[:10]
                fallback["fuente"] = f"mindicador.cl (último valor en caché, {fecha}; API sin conexión)"
            except Exception:
                fallback = None

        # 3b. Fallback final: valores de contingencia fijos
        if not fallback:
            fallback = {
                "uf": {"nombre": "Unidad de Fomento", "valor": 41008.10, "fecha": "2026-09-24", "unidad": "Pesos Chilenos (CLP)"},
                "dolar": {"nombre": "Dólar Observado", "valor": 959.39, "fecha": "2026-09-24", "unidad": "Pesos Chilenos (CLP)"},
                "utm": {"nombre": "Unidad Tributaria Mensual", "valor": 71721.00, "fecha": "2026-09-24", "unidad": "Pesos Chilenos (CLP)"},
                "fuente": "Valores de contingencia locales (API sin conexión)"
            }
        self._cached_data = {"_ts": time.time(), "data": fallback}
        return fallback

    def convert_uf_to_clp(self, monto_uf: float) -> Dict[str, Any]:
        """Convierte un monto en UF a pesos chilenos según la UF del día."""
        data = self.get_indicators()
        valor_uf = data["uf"]["valor"]
        monto_clp = round(monto_uf * valor_uf)
        return {
            "monto_uf": monto_uf,
            "valor_uf_utilizado": valor_uf,
            "monto_clp": monto_clp,
            "fecha_uf": data["uf"].get("fecha", "Hoy"),
            "fuente": data["fuente"]
        }

    def convert_clp_to_uf(self, monto_clp: float) -> Dict[str, Any]:
        """Convierte un monto en pesos chilenos a UF según la UF del día."""
        data = self.get_indicators()
        valor_uf = data["uf"]["valor"]
        monto_uf = round(monto_clp / valor_uf, 2)
        return {
            "monto_clp": monto_clp,
            "valor_uf_utilizado": valor_uf,
            "monto_uf": monto_uf,
            "fecha_uf": data["uf"].get("fecha", "Hoy"),
            "fuente": data["fuente"]
        }


if __name__ == "__main__":
    tool = EconomicIndicatorsTool()
    ind = tool.get_indicators()
    print("Indicadores obtenidos:")
    print(f"UF: ${ind['uf']['valor']:,.2f} CLP ({ind['uf']['fecha']})")
    print(f"Dólar: ${ind['dolar']['valor']:,.2f} CLP")
    calc = tool.convert_uf_to_clp(1000)
    print(f"1.000 UF equivalen a: ${calc['monto_clp']:,} CLP")
