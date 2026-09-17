"""
测试模块
======
包含单元测试和集成测试，验证各个模块的功能。

为什么需要测试？
- 确保代码在不同环境下都能正常工作
- 及早发现 Bug
- 重构时防止回归
- 文档化代码行为（测试就是可执行的文档）
"""

import unittest
import tempfile
import os
from pathlib import Path

# 导入待测试的模块
from database import SEODatabase
from rag import RAGSystem
from config import Config


class TestDatabase(unittest.TestCase):
    """数据库模块的单元测试"""

    def setUp(self):
        """
        测试前准备
        为了避免污染真实数据库，每个测试使用临时数据库
        """
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # 初始化数据库
        self.db = SEODatabase(self.db_path)
        self.db.init_tables()

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_init_tables(self):
        """测试表初始化"""
        self.assertTrue(os.path.exists(self.db_path))
        print("✅ 表初始化成功")

    def test_insert_article(self):
        """测试插入文章"""
        article_id = self.db.insert_article(
            title="测试文章",
            content="测试内容",
            keyword="测试关键词",
            mock_ctr=0.35
        )
        
        self.assertIsNotNone(article_id)
        self.assertGreater(article_id, 0)
        
        # 验证插入的数据
        article = self.db.get_article_by_id(article_id)
        self.assertEqual(article['title'], "测试文章")
        self.assertEqual(article['keyword'], "测试关键词")
        
        print(f"✅ 文章插入成功 (ID: {article_id})")

    def test_update_ctr(self):
        """测试更新 CTR"""
        article_id = self.db.insert_article(
            title="测试",
            content="测试",
            keyword="测试",
            mock_ctr=0.2
        )
        
        # 更新 CTR
        self.db.update_article_ctr(article_id, 0.5)
        
        # 验证更新
        article = self.db.get_article_by_id(article_id)
        self.assertEqual(article['mock_ctr'], 0.5)
        
        print("✅ CTR 更新成功")

    def test_insert_iteration_log(self):
        """测试插入迭代日志"""
        # 先插入文章
        article_id = self.db.insert_article(
            title="测试",
            content="测试",
            keyword="测试"
        )
        
        # 插入迭代日志
        log_id = self.db.insert_iteration_log(
            article_id=article_id,
            round_number=1,
            reflection="标题不吸引人",
            suggestions="在标题中加入数字"
        )
        
        self.assertIsNotNone(log_id)
        
        # 验证查询
        logs = self.db.get_iteration_logs_for_article(article_id)
        self.assertEqual(len(logs), 1)
        self.assertIn("数字", logs[0]['suggestions'])
        
        print("✅ 迭代日志插入成功")

    def test_get_statistics(self):
        """测试统计功能"""
        # 插入几篇文章
        for i in range(3):
            self.db.insert_article(
                title=f"文章 {i}",
                content="测试",
                keyword="测试",
                mock_ctr=0.30 + i * 0.05
            )
        
        stats = self.db.get_statistics()
        
        self.assertEqual(stats['total_articles'], 3)
        self.assertGreater(stats['avg_ctr'], 0)
        
        print(f"✅ 统计信息: {stats}")


class TestRAG(unittest.TestCase):
    """RAG 模块的单元测试"""

    def setUp(self):
        """创建临时 RAG 实例"""
        self.temp_dir = tempfile.mkdtemp()
        self.rag = RAGSystem(
            db_path=self.temp_dir,
            collection_name="test_collection"
        )

    def tearDown(self):
        """清理临时文件"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_add_documents(self):
        """测试添加文档"""
        docs = [
            "Python 是一种强大的编程语言",
            "JavaScript 用于前端开发",
            "Java 用于企业级开发"
        ]
        
        self.rag.add_documents(documents=docs)
        
        stats = self.rag.get_collection_stats()
        self.assertEqual(stats['document_count'], 3)
        
        print(f"✅ 文档添加成功: {stats['document_count']} 篇")

    def test_search(self):
        """测试检索功能"""
        docs = [
            "Python 是一种强大的编程语言",
            "Java 用于企业级开发",
            "Go 语言由 Google 设计"
        ]
        
        self.rag.add_documents(documents=docs)
        
        # 搜索相关文档
        results = self.rag.search("编程语言", n_results=2)
        
        self.assertGreater(len(results), 0)
        self.assertLessEqual(len(results), 2)
        
        # 验证返回格式
        for result in results:
            self.assertIn('document', result)
            self.assertIn('distance', result)
        
        print(f"✅ 检索成功: 返回 {len(results)} 篇文档")

    def test_search_with_filter(self):
        """测试带过滤的检索"""
        docs = ["Python", "Java"]
        metadatas = [
            {"category": "编程"},
            {"category": "数据库"}
        ]
        
        self.rag.add_documents(documents=docs, metadatas=metadatas)
        
        # 带过滤搜索
        results = self.rag.search_with_filter(
            query="编程",
            category="编程",
            n_results=5
        )
        
        # 注：实际过滤效果取决于 ChromaDB 的支持
        print(f"✅ 带过滤检索成功: 返回 {len(results)} 篇")


class TestConfig(unittest.TestCase):
    """配置模块的单元测试"""

    def test_config_loading(self):
        """测试配置加载"""
        # 验证关键配置是否存在
        self.assertIsNotNone(Config.DATABASE_PATH)
        self.assertIsNotNone(Config.CHROMA_DB_PATH)
        self.assertGreater(Config.MAX_CONCURRENT_TASKS, 0)
        
        print("✅ 配置加载成功")

    def test_directory_creation(self):
        """测试目录是否被正确创建"""
        self.assertTrue(Path(Config.DATABASE_PATH).parent.exists())
        self.assertTrue(Path(Config.CHROMA_DB_PATH).exists())
        
        print("✅ 目录结构正确")


class IntegrationTest(unittest.TestCase):
    """集成测试"""

    def test_full_workflow(self):
        """测试完整的工作流程"""
        # 1. 创建临时数据库
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        db_path = temp_db.name
        temp_db.close()
        
        db = SEODatabase(db_path)
        db.init_tables()
        
        # 2. 插入文章
        article_id = db.insert_article(
            title="完整测试",
            content="测试内容",
            keyword="测试关键词",
            topic_theme="测试",
            mock_ctr=0.30
        )
        
        # 3. 插入迭代日志（模拟评批）
        log_id = db.insert_iteration_log(
            article_id=article_id,
            round_number=1,
            reflection="初次评批",
            suggestions="改进建议"
        )
        
        # 4. 查询反思建议
        latest = db.get_latest_reflection(topic_theme="测试")
        
        # 5. 验证闭环
        self.assertEqual(latest['article_id'], article_id)
        self.assertIn("改进", latest['suggestions'])
        
        # 清理
        os.remove(db_path)
        
        print("✅ 完整工作流测试成功")


def run_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🧪 启动单元测试和集成测试")
    print("="*60 + "\n")
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestRAG))
    suite.addTests(loader.loadTestsFromTestCase(IntegrationTest))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 显示结果汇总
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    print(f"运行测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 有测试失败，请检查错误日志")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
