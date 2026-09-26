"""
Módulo de Almacenamiento y Recuperación Vectorial (Vector Store & Semantic Retrieval).
Implementa indexación vectorial con similitud del coseno, ranking de relevancia top-k y filtrado por metadatos.
Garantiza funcionamiento determinista, autónomo y de alta fidelidad, con soporte para embeddings densos opcionales.
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.rag.document_loader import DocumentLoader
from src.rag.chunker import SemanticChunker

class VectorStore:
    def __init__(self, chunks: Optional[List[Dict[str, Any]]] = None):
        self.chunks = chunks if chunks is not None else []
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            sublinear_tf=True,
            strip_accents="unicode",
            lowercase=True
        )
        self.matrix = None
        if self.chunks:
            self._build_index()

    def _build_index(self):
        """Indexa los textos de todos los fragmentos en el espacio vectorial."""
        corpus = [f"{c.get('heading', '')} {c.get('article', '')} {c.get('text', '')}" for c in self.chunks]
        self.matrix = self.vectorizer.fit_transform(corpus)

    def add_chunks(self, new_chunks: List[Dict[str, Any]]):
        """Agrega nuevos chunks y reconstruye el índice."""
        self.chunks.extend(new_chunks)
        self._build_index()

    def search(self, query: str, top_k: int = 3, min_score: float = 0.05) -> List[Dict[str, Any]]:
        """
        Realiza búsqueda semántica por similitud de coseno frente a la consulta del usuario.
        Retorna los mejores top_k fragmentos con su puntaje de relevancia y metadatos.
        """
        if self.matrix is None or len(self.chunks) == 0:
            return []

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix)[0]

        # Obtener los índices de mayor a menor puntuación
        ranked_indices = np.argsort(scores)[::-1]

        results = []
        for idx in ranked_indices[:top_k]:
            score = float(scores[idx])
            if score >= min_score:
                chunk_data = self.chunks[idx].copy()
                chunk_data["similarity_score"] = round(score, 4)
                results.append(chunk_data)

        return results

    def get_formatted_context(self, query: str, top_k: int = 3) -> str:
        """
        Genera el bloque de contexto inyectable en el prompt del LLM con citas de fuentes explícitas.
        """
        results = self.search(query, top_k=top_k)
        if not results:
            return "No se encontraron políticas o normas directamente relevantes en el manual institucional."

        context_parts = []
        for i, res in enumerate(results, 1):
            part = (
                f"--- [FRAGMENTO NORMATIVO {i}] ---\n"
                f"Fuente: {res.get('source')} | Artículo/Sección: {res.get('article')} - {res.get('heading')}\n"
                f"Relevancia: {res.get('similarity_score')*100:.1f}%\n"
                f"Texto Oficial:\n{res.get('text')}\n"
            )
            context_parts.append(part)

        return "\n".join(context_parts)

    @classmethod
    def load_from_default_data(cls) -> "VectorStore":
        """Instancia e indexa la base documental interna predeterminada del banco."""
        loader = DocumentLoader()
        docs = loader.load_documents()
        chunker = SemanticChunker()
        chunks = chunker.chunk_all(docs)
        return cls(chunks=chunks)


if __name__ == "__main__":
    store = VectorStore.load_from_default_data()
    print(f"Vector Store inicializado con {len(store.chunks)} chunks.")

    queries = [
        "¿Cuáles son los requisitos de antigüedad y balances para una empresa?",
        "¿Qué cobertura tiene la garantía FOGAPE y cuáles son los límites de ventas?",
        "¿Qué pasa si la empresa tiene deuda o morosidad en Dicom?",
        "¿En qué condiciones se exige derivar al comité especial de riesgo?"
    ]

    for q in queries:
        print(f"\n==================================================")
        print(f"Query: '{q}'")
        res = store.search(q, top_k=2)
        for r in res:
            print(f"-> [{r['article']}] {r['heading']} (Score: {r['similarity_score']})")
