import json
import os
from typing import List, Dict, Any
import faiss
import numpy as np
from langchain_ollama import OllamaEmbeddings
from config import PROFILE_PATH, EPISODES_PATH, SEMANTIC_PATH, OLLAMA_MODEL, OLLAMA_BASE_URL

class LongTermProfile:
    """Manages user facts and preferences with conflict handling."""
    def __init__(self, file_path: str = PROFILE_PATH):
        self.file_path = file_path
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except:
                    return {}
        return {}

    def save(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def update_fact(self, key: str, value: Any):
        self.data[key] = value
        self.save()

    def get_all(self) -> Dict[str, Any]:
        return self.data

class EpisodicMemory:
    """Saves key interactions and outcomes."""
    def __init__(self, file_path: str = EPISODES_PATH):
        self.file_path = file_path
        self.episodes = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except:
                    return []
        return []

    def save(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.episodes, f, indent=4, ensure_ascii=False)

    def add_episode(self, summary: str, outcome: str):
        self.episodes.append({
            "summary": summary,
            "outcome": outcome
        })
        if len(self.episodes) > 10:
            self.episodes = self.episodes[-10:]
        self.save()

    def get_recent(self) -> List[Dict[str, Any]]:
        return self.episodes

class SemanticMemory:
    """Vector-based memory for knowledge chunks using Ollama."""
    def __init__(self, index_path: str = SEMANTIC_PATH):
        self.index_path = index_path
        self.embeddings = OllamaEmbeddings(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
        self.index = None
        self.texts = []
        self._load_or_init()

    def _load_or_init(self):
        if os.path.exists(self.index_path + ".index"):
            self.index = faiss.read_index(self.index_path + ".index")
            with open(self.index_path + ".texts", 'r', encoding='utf-8') as f:
                self.texts = json.load(f)
        else:
            # We'll determine dimension on first add
            self.index = None
            self.texts = []

    def save(self):
        if self.index:
            faiss.write_index(self.index, self.index_path + ".index")
            with open(self.index_path + ".texts", 'w', encoding='utf-8') as f:
                json.dump(self.texts, f, indent=4, ensure_ascii=False)

    def add_knowledge(self, text: str):
        vector = self.embeddings.embed_query(text)
        if self.index is None:
            dim = len(vector)
            self.index = faiss.IndexFlatL2(dim)
        
        self.index.add(np.array([vector]).astype('float32'))
        self.texts.append(text)
        self.save()

    def search(self, query: str, k: int = 3) -> List[str]:
        if not self.texts or self.index is None:
            return []
        vector = self.embeddings.embed_query(query)
        distances, indices = self.index.search(np.array([vector]).astype('float32'), k)
        results = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.texts):
                results.append(self.texts[idx])
        return results
