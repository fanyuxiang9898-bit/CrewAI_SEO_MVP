"""
RAG 模块 - 彻底修复版本
修复 ChromaDB 1.5.5 的元数据问题
"""

import chromadb
from typing import List, Dict, Optional
from pathlib import Path
from config import Config


class RAGSystem:
    """RAG 系统类 - 完全兼容 ChromaDB 1.5.5"""

    def __init__(self, db_path: str = None, collection_name: str = "seo_content"):
        """初始化 RAG 系统"""
        self.db_path = db_path or Config.CHROMA_DB_PATH
        self.collection_name = collection_name
        
        # ChromaDB 1.5.5 的新 API
        self.client = chromadb.PersistentClient(path=str(self.db_path))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": f"SEO 爆款文案库 - {collection_name}"}
        )

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict] = None,
        ids: List[str] = None
    ):
        """添加文档到向量库"""
        if not documents:
            return
        
        # 生成 ID
        if ids is None:
            ids = [f"doc_{i}_{hash(doc) % 10000}" for i, doc in enumerate(documents)]
        
        # 确保元数据不为空 - 这是关键！
        if metadatas is None:
            metadatas = [{"source": "default"} for _ in documents]
        else:
            # 确保每个元数据都不为空
            metadatas = [
                meta if meta else {"source": "default"} 
                for meta in metadatas
            ]
        
        try:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            print(f"✅ 成功添加 {len(documents)} 篇文档到 ChromaDB")
        except Exception as e:
            print(f"❌ 添加文档失败: {e}")
            raise

    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_dict: Dict = None
    ) -> List[Dict]:
        """检索文档"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_dict
            )
            
            formatted_results = []
            if results['ids'] and len(results['ids']) > 0:
                for i, doc_id in enumerate(results['ids'][0]):
                    formatted_results.append({
                        'id': doc_id,
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i]
                    })
            
            return formatted_results
        except Exception as e:
            print(f"❌ 检索失败: {e}")
            return []

    def search_by_keyword(self, keyword: str, n_results: int = 5) -> List[Dict]:
        """按关键词检索"""
        return self.search(query=keyword, n_results=n_results)

    def search_with_filter(self, query: str, category: str = None, n_results: int = 5) -> List[Dict]:
        """带过滤条件的检索"""
        filter_dict = None
        if category:
            filter_dict = {"category": {"$eq": category}}
        return self.search(query=query, n_results=n_results, filter_dict=filter_dict)

    def get_collection_stats(self) -> Dict:
        """获取统计信息"""
        try:
            count = self.collection.count()
            return {
                'collection_name': self.collection_name,
                'document_count': count,
                'embedding_model': Config.EMBEDDING_MODEL
            }
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return {}

    def clear_collection(self):
        """清空集合"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name
            )
            print(f"✅ 已清空集合: {self.collection_name}")
        except Exception as e:
            print(f"❌ 清空集合失败: {e}")


# 全局实例管理
_rag_instances: Dict[str, RAGSystem] = {}


def get_rag_system(collection_name: str = "seo_content") -> RAGSystem:
    """获取 RAG 系统实例"""
    if collection_name not in _rag_instances:
        _rag_instances[collection_name] = RAGSystem(collection_name=collection_name)
    return _rag_instances[collection_name]


if __name__ == '__main__':
    # 测试
    print("\n测试 RAG 系统...\n")
    rag = RAGSystem(collection_name="test_collection")
    
    test_docs = [
        "Python 是一种强大的编程语言",
        "JavaScript 用于前端开发",
        "Java 用于企业级应用",
    ]
    
    print("✓ 添加测试文档...\n")
    rag.add_documents(documents=test_docs)
    
    print("\n✓ 执行向量检索...\n")
    results = rag.search("编程语言", n_results=2)
    
    print(f"🔍 检索结果:")
    for i, result in enumerate(results, 1):
        print(f"   {i}. {result['document'][:50]}...")
        print(f"      距离: {result['distance']:.3f}")
    
    stats = rag.get_collection_stats()
    print(f"\n📊 统计: {stats}")
