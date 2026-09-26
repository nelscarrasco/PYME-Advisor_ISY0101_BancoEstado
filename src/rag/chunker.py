"""
Módulo de Segmentación Semántica (Chunking Jerárquico).
Divide los documentos preservando la jerarquía de títulos, artículos y subtítulos
para evitar la fragmentación de reglas operacionales y maximizar la precisión del retrieval.
"""

import re
from typing import List, Dict, Any

class SemanticChunker:
    def __init__(self, max_chunk_chars: int = 700, chunk_overlap_chars: int = 150):
        self.max_chunk_chars = max_chunk_chars
        self.chunk_overlap_chars = chunk_overlap_chars

    def chunk_document(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Segmenta el contenido respetando encabezados Markdown (##, ###) y Artículos.
        """
        content = doc.get("content", "")
        source = doc.get("source", "desconocido")
        chunks = []

        # Expresión regular para detectar títulos y artículos
        section_pattern = re.compile(r"(?=^(?:##|###)\s+)", re.MULTILINE)
        sections = section_pattern.split(content)

        chunk_counter = 0
        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Extraer el encabezado
            first_line = section.split("\n")[0].strip()
            heading = first_line.replace("#", "").strip()

            # Extraer artículo si aplica
            art_match = re.search(r"(Art[íi]culo\s+\d+)", section, re.IGNORECASE)
            article_ref = art_match.group(1).title() if art_match else "General"

            # Si la sección es pequeña o razonable, se guarda como un solo chunk cohesivo
            if len(section) <= self.max_chunk_chars:
                chunk_counter += 1
                chunks.append({
                    "chunk_id": f"{source}_{chunk_counter}",
                    "source": source,
                    "heading": heading,
                    "article": article_ref,
                    "text": section,
                    "char_count": len(section)
                })
            else:
                # Si supera max_chunk_chars, dividir en párrafos con solapamiento
                paragraphs = section.split("\n\n")
                current_text = f"[{heading}] "
                for p in paragraphs:
                    p = p.strip()
                    if not p:
                        continue
                    if len(current_text) + len(p) <= self.max_chunk_chars:
                        current_text += "\n" + p
                    else:
                        chunk_counter += 1
                        chunks.append({
                            "chunk_id": f"{source}_{chunk_counter}",
                            "source": source,
                            "heading": heading,
                            "article": article_ref,
                            "text": current_text.strip(),
                            "char_count": len(current_text.strip())
                        })
                        # Iniciar siguiente chunk con encabezado de contexto
                        current_text = f"[{heading} - cont.] " + p[-self.chunk_overlap_chars:] + "\n" + p

                if current_text.strip():
                    chunk_counter += 1
                    chunks.append({
                        "chunk_id": f"{source}_{chunk_counter}",
                        "source": source,
                        "heading": heading,
                        "article": article_ref,
                        "text": current_text.strip(),
                        "char_count": len(current_text.strip())
                    })

        return chunks

    def chunk_all(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        all_chunks = []
        for doc in documents:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks


if __name__ == "__main__":
    from document_loader import DocumentLoader
    loader = DocumentLoader()
    docs = loader.load_documents()
    chunker = SemanticChunker()
    chunks = chunker.chunk_all(docs)
    print(f"Total de chunks generados: {len(chunks)}")
    for i, c in enumerate(chunks[:5]):
        print(f"\n--- Chunk {i+1} [{c['source']} | {c['article']}] ({c['char_count']} chars) ---")
        print(c['text'][:180] + "...")
