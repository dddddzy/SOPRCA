"""
vector_store.py - 向量库统一封装
"""

import chromadb
from typing import List, Dict, Any


class VectorStore:
    """向量库封装"""

    def __init__(self, persist_directory: str, collection_name: str):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection_name = collection_name

    def get_collection(self):
        return self.client.get_collection(name=self.collection_name)

    def query(self, query_texts: List[str], n_results: int = 3) -> Dict[str, Any]:
        collection = self.get_collection()
        return collection.query(query_texts=query_texts, n_results=n_results)

    def upsert(self, ids: List[str], documents: List[str], metadatas: List[Dict]):
        collection = self.get_collection()
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
