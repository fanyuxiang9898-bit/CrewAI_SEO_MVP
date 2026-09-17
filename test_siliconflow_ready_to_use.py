"""
硅基流动 API 连接测试脚本
========================
验证 API Key 和网络连接是否正常工作

使用方法：
  python test_siliconflow.py
"""

import sys
from config import Config

try:
    from openai import OpenAI
except ImportError:
    print("❌ 未安装 openai 库")
    print("请先运行：pip install openai")
    sys.exit(1)


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_config():
    """测试配置是否正确"""
    print_header("1️⃣ 验证配置")
    
    try:
        if not Config.LLM_API_KEY:
            print("❌ API Key 未设置！")
            return False
        
        print(f"✓ API Key: {Config.LLM_API_KEY[:15]}...{Config.LLM_API_KEY[-5:]}")
        print(f"✓ API URL: {Config.LLM_BASE_URL}")
        print(f"✓ 模型: {Config.LLM_MODEL}")
        print(f"✓ 数据库: {Config.DATABASE_PATH}")
        
        return True
    except Exception as e:
        print(f"❌ 配置错误: {e}")
        return False


def test_api_connection():
    """测试 API 连接"""
    print_header("2️⃣ 测试 API 连接")
    
    try:
        print(f"📡 正在连接硅基流动 API...")
        print(f"   URL: {Config.LLM_BASE_URL}")
        print(f"   模型: {Config.LLM_MODEL}")
        
        # 创建 OpenAI 兼容客户端
        client = OpenAI(
            api_key=Config.LLM_API_KEY,
            base_url=Config.LLM_BASE_URL,
            timeout=30
        )
        
        print(f"\n📤 发送测试请求...")
        
        # 发送简单的测试消息
        response = client.chat.completions.create(
            model=Config.LLM_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": "你好，请简短地自我介绍（5-10个字）"
                }
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
        
        print(f"\n✅ API 连接成功！\n")
        print(f"🤖 模型回答: {answer}\n")
        
        # 显示 token 使用情况
        print(f"📊 Token 使用统计:")
        print(f"   - 输入 tokens: {response.usage.prompt_tokens}")
        print(f"   - 输出 tokens: {response.usage.completion_tokens}")
        print(f"   - 总 tokens: {response.usage.total_tokens}")
        
        # 计算成本
        total_tokens = response.usage.total_tokens
        # 硅基流动: ¥0.5 / 100万 tokens
        cost_yuan = total_tokens * 0.5 / 1_000_000
        
        print(f"\n💰 成本估算:")
        print(f"   - 这次请求成本: ¥{cost_yuan:.6f} (<1分钱)")
        print(f"   - 处理 1 个 SEO 主题: 约 ¥0.015")
        print(f"   - ¥100 额度可处理: 6000+ 个主题")
        
        return True
        
    except Exception as e:
        print(f"\n❌ API 连接失败!\n")
        print(f"错误信息: {str(e)}\n")
        
        print(f"💡 可能的原因:")
        print(f"   1. API Key 错误或未设置")
        print(f"   2. 网络连接问题")
        print(f"   3. API 地址不可用")
        print(f"   4. 模型名称错误\n")
        
        print(f"✅ 解决方案:")
        print(f"   1. 检查 API Key: https://cloud.siliconflow.cn")
        print(f"   2. 检查网络连接")
        print(f"   3. 确认模型: https://docs.siliconflow.cn/docs/model-list")
        
        return False


def test_database():
    """测试数据库初始化"""
    print_header("3️⃣ 测试数据库")
    
    try:
        print("初始化数据库...")
        from database import get_db
        
        db = get_db()
        db.init_tables()
        
        # 插入测试数据
        print("✓ 创建测试数据...")
        article_id = db.insert_article(
            title="测试文章",
            content="这是一个测试",
            keyword="测试",
            mock_ctr=0.35
        )
        
        # 查询测试数据
        article = db.get_article_by_id(article_id)
        print(f"✓ 数据库读写正常")
        print(f"✓ 测试数据 ID: {article['id']}")
        
        # 获取统计
        stats = db.get_statistics()
        print(f"\n✅ 数据库初始化成功\n")
        print(f"📊 数据库统计:")
        print(f"   - 总文章数: {stats['total_articles']}")
        print(f"   - 平均 CTR: {stats['avg_ctr']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False


def test_rag():
    """测试 RAG 系统"""
    print_header("4️⃣ 测试 RAG 系统")
    
    try:
        print("初始化 RAG 系统...")
        from rag import get_rag_system
        
        rag = get_rag_system("test")
        
        # 添加测试文档
        print("✓ 添加测试文档...")
        test_docs = [
            "Python 是一种强大的编程语言",
            "JavaScript 用于前端开发",
            "Java 用于企业级应用"
        ]
        
        rag.add_documents(documents=test_docs)
        
        # 执行检索
        print("✓ 执行向量检索...")
        results = rag.search("编程语言", n_results=2)
        
        print(f"\n✅ RAG 系统初始化成功\n")
        print(f"🔍 检索结果 (关键词: '编程语言'):")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result['document'][:50]}...")
            print(f"      相似度: {1 - result['distance']:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG 测试失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🧪" * 30)
    print("硅基流动系统完整测试套件")
    print("🧪" * 30)
    
    results = {
        "配置验证": test_config(),
        "API 连接": test_api_connection(),
        "数据库": test_database(),
        "RAG 系统": test_rag(),
    }
    
    # 显示总结
    print_header("📊 测试结果总结")
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n" + "🎉" * 30)
        print("✅ 所有测试通过！系统已准备就绪！")
        print("🎉" * 30)
        print("\n📝 后续步骤:")
        print("   1. python init_data.py     # 初始化 Mock 数据")
        print("   2. python main.py          # 运行主程序")
        return 0
    else:
        print("\n⚠️ 有测试失败，请检查错误信息")
        return 1


if __name__ == '__main__':
    try:
        exit_code = run_all_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏸️ 用户中断了测试")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
