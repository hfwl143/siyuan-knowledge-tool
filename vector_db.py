import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional

# 全局初始化
embed_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="knowledge",
    metadata={"hnsw:space": "cosine"}
)

def add_document(doc_id: str, metadata: Dict):
    """新增或更新文档向量。metadata 应包含 title, summary, tags 等"""
    text = f"{metadata['title']} {metadata['summary']}"
    vector = embed_model.encode(text).tolist()
    # 只保留必要的元数据，并添加 doc_id 用于检索
    full_meta = {**metadata, "doc_id": doc_id}
    collection.upsert(
        ids=[doc_id],
        embeddings=[vector],
        metadatas=[full_meta]
    )

def delete_document(file_name: str):
    collection.delete(ids=[file_name])

def update_document(file_name: str, new_metadata: Dict):
    """覆盖更新（调用 add_document 即可）"""
    add_document(file_name, new_metadata)

def search_similar(query_text: str, top_k: int = 5, threshold: float = 0.7) -> List[Dict]:
    query_vector = embed_model.encode(query_text).tolist()
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["metadatas", "distances"]
    )
    similar = []
    if results['distances'][0]:
        for i in range(len(results['ids'][0])):
            similarity = 1 - results['distances'][0][i]
            if similarity >= threshold:
                meta = results['metadatas'][0][i]
                similar.append({
                    "doc_id": results['ids'][0][i],
                    "title": meta.get('title', ''),
                    "summary": meta.get('summary', ''),
                    "tags": meta.get('tags', []),
                    "similarity": similarity
                })
    return similar 