from typing import Protocol

from .dense_retriever import DenseRetriever
from .operations_index import KeyWordSearch


class RAG(Protocol):
    def get_suggestions(self, query: str, **kwargs) -> dict[str, list[dict]]: ...


class KnowledgeBase:
    def __init__(self):
        self.rag: RAG | None = None

    def trim_text(self, text: str, max_length: int) -> str:
        return f'{text[:max_length]}...' if len(text) > max_length else text

    def setup(self, rag_type: str, **kwargs):
        if rag_type == 'KEYWORD_SEARCH':
            self.rag = KeyWordSearch()
        elif rag_type == 'DENSE_RETRIEVER':
            self.rag = DenseRetriever(**kwargs)
        else:
            raise ValueError(f'No such rag type found: {rag_type}')

    def get_suggestions(self, query: str, **kwargs):
        if self.rag is None:
            raise RuntimeError('RAG is not initialized. Call setup first.')

        results = self.rag.get_suggestions(query, **kwargs)

        for result in results['suggestions']:
            result['description'] = self.trim_text(result['description'], 1000)
            for key, value in result['parameters'].items():
                if isinstance(value, str):
                    result['parameters'][key] = self.trim_text(value, 500)
        return results


knowledge_base = KnowledgeBase()
