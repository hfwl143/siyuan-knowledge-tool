# vector_db.py
import chromadb
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

embed_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="knowledge",
    metadata={"hnsw:space": "cosine"}
)

def clear_vector_store():
    """清空所有向量数据（删除并重建集合）"""
    global collection
    try:
        # 删除集合
        client.delete_collection("knowledge")
        # 重新创建
        collection = client.get_or_create_collection(
            name="knowledge",
            metadata={"hnsw:space": "cosine"}
        )
        # 同步更新 vector_db.py 中的 collection
        import vector_db
        vector_db.collection = collection
        logger.info("向量库已清空并重建")
    except Exception as e:
        logger.error(f"清空向量库失败: {e}")

def init_vector_store_from_siyuan(siyuan_client, notebook_id):
    """从思源重建向量库（全量）"""
    # 先尝试连接思源，如果连接失败则直接返回，不清空向量库
    try:
        # 简单测试连接，比如获取笔记本列表
        siyuan_client.list_notebooks()
    except Exception as e:
        logger.error(f"无法连接思源，请确保思源笔记已打开且API服务正常。错误: {e}")
        print("⚠️ 思源连接失败，跳过向量库重建，请先启动思源笔记。")
        return

    # 连接正常，执行清空和重建
    clear_vector_store()
    docs = siyuan_client.list_all_docs(notebook_id)
    for doc in docs:
        doc_id = doc["id"]
        title = doc["name"]
        content = siyuan_client.get_doc_content(doc_id)
        if content:
            summary = content[:150].strip()
            metadata = {"title": title, "summary": summary, "tags": []}
            add_document(doc_id, metadata)
            logger.info(f"已索引: {title} ({doc_id})")