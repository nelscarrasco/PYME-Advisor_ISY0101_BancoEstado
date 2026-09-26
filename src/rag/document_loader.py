"""
Módulo de Carga y Preprocesamiento de Documentos Internos.
Lee archivos Markdown de políticas de crédito, garantías y catálogo de productos.
"""

import os
from typing import List, Dict, Any

class DocumentLoader:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            self.data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "internal"))
        else:
            self.data_dir = os.path.abspath(data_dir)

    def load_documents(self) -> List[Dict[str, Any]]:
        """Carga todos los documentos de la carpeta interna con sus metadatos básicos."""
        documents = []
        if not os.path.exists(self.data_dir):
            print(f"[Error] Directorio de datos no encontrado: {self.data_dir}")
            return documents

        for filename in os.listdir(self.data_dir):
            if filename.endswith(".md") or filename.endswith(".txt"):
                file_path = os.path.join(self.data_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        documents.append({
                            "source": filename,
                            "file_path": file_path,
                            "content": content,
                            "size_chars": len(content)
                        })
                except Exception as e:
                    print(f"[Error] No se pudo leer {filename}: {e}")

        return documents


if __name__ == "__main__":
    loader = DocumentLoader()
    docs = loader.load_documents()
    print(f"Documentos cargados: {len(docs)}")
    for d in docs:
        print(f"- {d['source']} ({d['size_chars']} caracteres)")
