"""
Pruebas Unitarias y de Integración: Pipeline RAG y Búsqueda Semántica.
Verifica que el cargador, segmentador y vector store recuperen los artículos normativos correctos.
"""

import unittest
from src.rag.document_loader import DocumentLoader
from src.rag.chunker import SemanticChunker
from src.rag.vector_store import VectorStore

class TestRAGPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loader = DocumentLoader()
        cls.docs = cls.loader.load_documents()
        cls.chunker = SemanticChunker()
        cls.chunks = cls.chunker.chunk_all(cls.docs)
        cls.vector_store = VectorStore(cls.chunks)

    def test_document_loader_loads_required_files(self):
        """Verifica que se carguen el manual de crédito y el catálogo de productos."""
        self.assertGreaterEqual(len(self.docs), 2)
        sources = [d["source"] for d in self.docs]
        self.assertIn("manual_politicas_credito_pyme.md", sources)
        self.assertIn("catalogo_productos_financieros.md", sources)

    def test_semantic_chunker_preserves_articles(self):
        """Verifica que los chunks preserven la identificación de artículos y encabezados."""
        self.assertGreater(len(self.chunks), 10)
        articles = [c["article"] for c in self.chunks]
        self.assertTrue(any("Articulo 3" in a or "Artículo 3" in a for a in articles))
        self.assertTrue(any("Articulo 6" in a or "Artículo 6" in a for a in articles))

    def test_vector_search_fogape_retrieves_article_6(self):
        """Verifica que la consulta sobre garantías FOGAPE retorne prioritariamente el Artículo 6."""
        results = self.vector_store.search("cobertura y requisitos garantia FOGAPE subsidio estatal", top_k=2)
        self.assertGreater(len(results), 0)
        top_result = results[0]
        self.assertTrue("6" in top_result["article"] or "FOGAPE" in top_result["heading"])

    def test_vector_search_dicom_retrieves_article_4(self):
        """Verifica que la consulta sobre morosidades retorne el Artículo 4."""
        results = self.vector_store.search("morosidad comercial protestos boletin DICOM", top_k=2)
        self.assertGreater(len(results), 0)
        top_articles = [r["article"] for r in results]
        self.assertTrue(any("4" in a for a in top_articles))

if __name__ == "__main__":
    unittest.main()
