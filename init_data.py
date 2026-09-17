"""
初始化数据模块
==============
为 ChromaDB 和 SQLite 填充 Mock 数据，使系统可以直接运行。

为什么需要 Mock 数据？
- 开发和测试时，不需要真实的爆款文案
- 演示系统功能时，需要有实际的数据来展示检索和评批效果
- 本地开发环境通常没有生产数据库
"""

from database import SEODatabase
from rag import get_rag_system
from typing import List, Dict
import random


# ===================== Mock 爆款文案库 =====================

MOCK_VIRAL_ARTICLES = [
    {
        "title": "2024 年最全面的 Python 进阶教程：从基础到机器学习",
        "content": "本教程涵盖 Python 基础、OOP、函数式编程、异步 IO 和机器学习框架。通过 15 个真实项目案例，带你从初级开发者升级到高级工程师。特别关注性能优化和最佳实践。",
        "keyword": "Python 教程",
        "category": "技术",
        "ctr": 0.42,
        "insights": "详细的代码示例和项目驱动的学习路径"
    },
    {
        "title": "如何 30 天从零开始学会 Web 开发？一份完整的学习路线图",
        "content": "这份路线图涵盖 HTML/CSS/JavaScript 三个月的自学计划。从搭建第一个网站，到使用 React 框架，再到部署到云服务器。每个阶段都有具体的项目目标。",
        "keyword": "Web 开发入门",
        "category": "技术",
        "ctr": 0.38,
        "insights": "清晰的学习阶段划分和实战项目"
    },
    {
        "title": "数据分析工程师高薪秘诀：SQL + Python + BI 工具完全掌握",
        "content": "掌握数据分析必备的三大技能：SQL 数据查询优化、Python 数据处理、Tableau/Power BI 可视化。通过真实案例分析，展示如何从原始数据挖掘商业价值。",
        "keyword": "数据分析",
        "category": "技术",
        "ctr": 0.51,
        "insights": "强调职业发展和薪资增长"
    },
    {
        "title": "2024 年最火的副业项目：如何月入 5000 元的自媒体运营指南",
        "content": "分享 5 个月入 5000+ 的副业项目：短视频带货、自媒体运营、虚拟课程销售、内容写作、联盟营销。每个项目都包含完整的执行步骤和工具推荐。",
        "keyword": "副业赚钱",
        "category": "创业",
        "ctr": 0.65,
        "insights": "具体的金额承诺和可执行的步骤"
    },
    {
        "title": "揭秘电商 CEO 们都在用的 5 个数据驱动增长秘诀",
        "content": "电商运营的核心数据指标：GMV、转化率、客单价、复购率。通过这 5 个秘诀，打造高效的销售漏斗，实现 200% 的增长。",
        "keyword": "电商运营",
        "category": "商业",
        "ctr": 0.48,
        "insights": "数据驱动和具体的增长倍数"
    },
    {
        "title": "独家：这份 AI 提示词库帮我们提升 10 倍效率",
        "content": "收集了 100+ 个实用的 ChatGPT/Claude 提示词模板，覆盖内容创作、数据分析、代码生成、营销文案等领域。每个提示词都经过优化和实际测试。",
        "keyword": "AI 提示词",
        "category": "工具",
        "ctr": 0.44,
        "insights": "具体的数字和覆盖面广的应用"
    },
    {
        "title": "为什么这个创业团队用 1 年时间从 0 做到 100 万用户？内部分享",
        "content": "一家 SaaS 公司的增长复盘：市场调研、产品定位、初期 MVP、用户获取策略、数据运营。包含真实的关键数据和决策过程。",
        "keyword": "创业增长",
        "category": "创业",
        "ctr": 0.56,
        "insights": "具体的用户增长数据和内部流程"
    },
    {
        "title": "新手小白学股票投资：用 500 块钱学会理财的 7 步法则",
        "content": "从零基础开始学习股票：如何开户、选股思路、基本面分析、技术面指标、风险管理。通过虚拟交易和真实案例，让你快速入门。",
        "keyword": "股票投资",
        "category": "金融",
        "ctr": 0.40,
        "insights": "低门槛的学习成本和循序渐进"
    }
]


def init_chroma_with_mock_data():
    """
    用 Mock 数据初始化 ChromaDB
    
    流程：
    1. 获取 RAG 系统实例
    2. 清空现有集合（防止重复）
    3. 添加 Mock 爆款文案
    4. 验证插入成功
    """
    print("\n" + "="*60)
    print("🚀 初始化 ChromaDB 向量数据库...")
    print("="*60)
    
    rag = get_rag_system("seo_content")
    
    # 准备文档和元数据
    documents = []
    metadatas = []
    ids = []
    
    for i, article in enumerate(MOCK_VIRAL_ARTICLES):
        # 文档内容：标题 + 内容（RAG 会对整个文本进行 embedding）
        doc_content = f"{article['title']}\n{article['content']}"
        documents.append(doc_content)
        
        # 元数据：不参与 embedding，但在搜索时用于过滤和展示
        metadatas.append({
            "keyword": article['keyword'],
            "category": article['category'],
            "ctr": article['ctr'],
            "insights": article['insights'],
            "original_title": article['title']
        })
        
        ids.append(f"article_{i}")
    
    # 添加到向量库
    rag.add_documents(documents=documents, metadatas=metadatas, ids=ids)
    
    # 显示统计信息
    stats = rag.get_collection_stats()
    print(f"✅ ChromaDB 初始化完成")
    print(f"   - 文档数量: {stats['document_count']}")
    print(f"   - Embedding 模型: {stats['embedding_model']}")
    
    return rag


def init_sqlite_with_mock_data():
    """
    用 Mock 数据初始化 SQLite
    
    流程：
    1. 初始化表结构
    2. 插入历史文章（用不同的 CTR 模拟真实数据）
    3. 插入一些迭代日志（模拟评批反思）
    """
    print("\n" + "="*60)
    print("🚀 初始化 SQLite 数据库...")
    print("="*60)
    
    db = SEODatabase()
    db.init_tables()
    
    # 插入历史文章
    article_ids = []
    for i, article in enumerate(MOCK_VIRAL_ARTICLES):
        # 为了展示迭代效果，故意让部分文章 CTR 较低
        mock_ctr = article['ctr']
        if i % 2 == 0:
            # 偶数位置的文章降低 CTR，模拟需要优化的文章
            mock_ctr = article['ctr'] * 0.6
        
        article_id = db.insert_article(
            title=article['title'],
            content=article['content'],
            keyword=article['keyword'],
            topic_theme=article['category'],
            notes=article['insights'],
            mock_ctr=mock_ctr
        )
        article_ids.append(article_id)
        print(f"  ✓ 插入文章: {article['title'][:30]}... (CTR: {mock_ctr:.2f})")
    
    # 为部分文章插入迭代日志（模拟一次评批）
    print("\n📝 插入迭代日志...")
    for i in [0, 2, 4]:  # 为 3 篇文章添加迭代日志
        article_id = article_ids[i]
        article = MOCK_VIRAL_ARTICLES[i]
        
        reflection = f"文章 '{article['keyword']}' 的 CTR 低于预期。主要问题：标题吸引力不足，缺少数字亮点。"
        suggestions = f"建议：1) 在标题中加入数字和数量词（如'5个秘诀'、'30天'); 2) 强调具体的商业价值或个人收益; 3) 使用对比和承诺来吸引点击。"
        
        db.insert_iteration_log(
            article_id=article_id,
            round_number=1,
            reflection=reflection,
            suggestions=suggestions,
            previous_ctr=article['ctr'] * 0.6
        )
        print(f"  ✓ 迭代日志: 文章 ID {article_id}")
    
    # 插入关键词记录
    print("\n🔑 插入关键词记录...")
    keywords_data = [
        ("Python 教程", 50000, "高"),
        ("Web 开发入门", 35000, "高"),
        ("数据分析", 40000, "中"),
        ("副业赚钱", 80000, "高"),
        ("电商运营", 25000, "中"),
        ("AI 提示词", 30000, "中"),
        ("创业增长", 15000, "低"),
        ("股票投资", 70000, "高")
    ]
    
    for keyword, search_volume, competition in keywords_data:
        db.insert_keyword(keyword, search_volume, competition)
    print(f"  ✓ 插入 {len(keywords_data)} 个关键词")
    
    # 显示统计信息
    print("\n📊 数据库统计信息:")
    stats = db.get_statistics()
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    return db


def init_all():
    """
    一键初始化所有 Mock 数据
    """
    print("\n" + "🎯" * 30)
    print("SEO 内容营销自迭代 Agent 系统 - 数据初始化")
    print("🎯" * 30)
    
    try:
        # 初始化 ChromaDB
        rag = init_chroma_with_mock_data()
        
        # 初始化 SQLite
        db = init_sqlite_with_mock_data()
        
        print("\n" + "="*60)
        print("✅ 所有数据初始化成功！")
        print("="*60)
        
        # 测试 RAG 检索
        print("\n🔍 测试 RAG 检索能力...")
        results = rag.search("编程教程", n_results=3)
        print(f"关键词 '编程教程' 的检索结果:")
        for j, result in enumerate(results, 1):
            print(f"  {j}. {result['metadata']['original_title']}")
            print(f"     距离: {result['distance']:.3f} | 关键词: {result['metadata']['keyword']}")
        
        print("\n✅ 系统已就绪，可以开始运行 Agent 了！")
        return rag, db
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        raise


if __name__ == '__main__':
    init_all()
