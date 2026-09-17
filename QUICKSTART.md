# 🚀 5分钟快速开始指南

## 1️⃣ 安装依赖（2分钟）

```bash
# 进入项目目录
cd seo-agent-system

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

## 2️⃣ 配置 API Key（1分钟）

编辑 `.env` 文件：

```bash
# 修改这一行，换成你的实际 API Key
OPENAI_API_KEY=sk-...your-actual-key...
```

如果没有 OpenAI API Key，你可以：
- 使用其他 LLM（如 Claude、Ollama）
- 或先用 Mock 模式演示系统架构

## 3️⃣ 运行系统（2分钟）

### 方式 A：运行完整流程（推荐新手）

```bash
python main.py
```

这会：
- ✅ 初始化 Mock 数据
- ✅ 创建三个 Agent（研究员、作者、评批专家）
- ✅ 并发处理 2 个 SEO 主题
- ✅ 显示迭代反思建议
- ✅ 保存数据到本地数据库

### 方式 B：运行测试（验证环境）

```bash
python test_system.py
```

这会验证：
- ✅ 数据库正常工作
- ✅ RAG 向量检索正常
- ✅ 配置文件正确加载

## 📊 预期输出

```
🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯
准备并发处理 2 个主题
🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯
  • 关键词: Python 教程 | 分类: 技术
  • 关键词: 副业赚钱 | 分类: 创业

⏳ 开始异步处理主题: 技术 | 关键词: Python 教程
⏳ 开始异步处理主题: 创业 | 关键词: 副业赚钱

[LLM 调用进行中...]

✅ 任务完成: 技术 | 关键词: Python 教程
✅ 任务完成: 创业 | 关键词: 副业赚钱

============================================================
📋 执行结果汇总
============================================================

✅ 技术 | Python 教程
   状态: success
   时间戳: 2024-01-15T10:30:45.123456

✅ 创业 | 副业赚钱
   状态: success
   时间戳: 2024-01-15T10:30:52.987654

────────────────────────────────────────────────────────────
成功: 2/2 | 总耗时: 12.5 秒
============================================================

📊 系统统计信息
============================================================
  total_articles: 10
  avg_ctr: 0.3821
  total_iterations: 3
  top_keyword: Python 教程
============================================================

📝 最新的迭代反思建议:
  反思: 关键词 'Python 教程' 的内容需要优化。主要问题：标题吸引力不足...
  建议: 建议：1) 在标题中加入数字和数量词...
```

## 🎓 接下来做什么？

### 1. 理解系统架构

阅读 README.md 中的系统架构部分，理解三个 Agent 的职责。

### 2. 查看数据库

```bash
# 查看生成的数据库
ls -la data/

# 导出 SQLite 数据（可用 DB Browser for SQLite 打开）
sqlite3 data/seo_content.db "SELECT * FROM articles LIMIT 3;"
```

### 3. 自定义运行

编辑 `main.py` 的 `topics_to_process` 列表：

```python
topics_to_process = [
    {'keyword': 'AI 与未来', 'topic': '技术'},
    {'keyword': '创业融资', 'topic': '商业'},
    {'keyword': '财务自由', 'topic': '金融'},
]
```

### 4. 集成真实 LLM

目前系统已支持 OpenAI/Claude/Ollama，只需在 `.env` 配置 API Key。

## 🔍 查看详细文档

- **README.md** - 完整的架构和使用说明
- **agents.py** - Agent 定义和详细注释
- **database.py** - 数据库操作的详细注释
- **rag.py** - RAG 原理的详细解释
- **main.py** - 异步并发的详细实现

## ⚠️ 常见问题

### Q: 没有 OpenAI API Key 怎么办？

A: 系统会以 Mock 模式运行，展示架构但不实际调用 LLM。你可以：
1. 申请 OpenAI 免费额度
2. 使用其他 LLM（Anthropic Claude、Ollama 等）
3. 先研究代码理解原理

### Q: 遇到 "OPENAI_API_KEY 未配置" 错误？

A: 检查 `.env` 文件中是否正确设置了 API Key：

```bash
# ❌ 错误（保留了默认值）
OPENAI_API_KEY=your_openai_api_key_here

# ✅ 正确
OPENAI_API_KEY=sk-proj-abc123xyz...
```

### Q: 数据库文件在哪？

A: 默认在 `./data/seo_content.db`，使用 DB Browser for SQLite 可以图形化查看。

### Q: 如何只运行某个部分（如只测试 RAG）？

A: 修改 `init_data.py` 和 `test_system.py` 中的代码：

```python
# 只初始化数据库
from init_data import init_sqlite_with_mock_data
db = init_sqlite_with_mock_data()

# 只初始化 RAG
from init_data import init_chroma_with_mock_data
rag = init_chroma_with_mock_data()
```

## 📚 学习路线图

```
Day 1: 快速上手
├─ ✅ 安装依赖
├─ ✅ 配置 API Key
├─ ✅ 运行 main.py
└─ ✅ 查看输出结果

Day 2: 理解架构
├─ 学习 README.md 的架构部分
├─ 理解三个 Agent 的职责
├─ 学习 RAG 的原理
└─ 理解异步并发的优势

Day 3: 深入代码
├─ 阅读 agents.py（Agent 定义）
├─ 阅读 tasks.py（Task 定义）
├─ 阅读 database.py（数据库操作）
└─ 阅读 main.py（异步协调）

Day 4: 动手实验
├─ 修改 init_data.py 的 Mock 数据
├─ 在 main.py 中添加新的主题
├─ 观察数据库的变化
└─ 运行 test_system.py 验证

Day 5: 扩展功能
├─ 添加新的 Agent
├─ 集成其他 LLM 模型
├─ 优化 RAG 的检索策略
└─ 部署到实际环境
```

## 🎯 目标

通过这个项目，你将学会：

1. ✅ **多智能体系统设计** - 如何设计和协调多个 AI Agent
2. ✅ **RAG 原理与实践** - 如何用向量检索增强 LLM 生成
3. ✅ **异步并发编程** - 如何用 asyncio 提高系统吞吐量
4. ✅ **数据库设计** - 如何设计数据模型支持闭环迭代
5. ✅ **工程最佳实践** - 如何组织和文档化复杂系统

## 💡 进阶挑战

完成基础后，尝试：

- [ ] 集成 Pinecone 云向量数据库替代本地 ChromaDB
- [ ] 添加 Web UI（使用 Streamlit 或 FastAPI）
- [ ] 实现持久化学习（Agent 的改进能力）
- [ ] 集成实时搜索引擎获取真实 CTR 数据
- [ ] 部署到云平台（AWS Lambda、Google Cloud Functions）

---

**祝你学习愉快！如有问题，欢迎查阅 README.md 或代码中的详细注释。** 🎉
