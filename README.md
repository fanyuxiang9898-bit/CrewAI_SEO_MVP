# 🚀 SEO 内容营销自迭代 Agent 系统

## Content Studio 网页工作台

使用 Python 3.10+ 启动：

```sh
python web_server.py
```

打开 `http://127.0.0.1:8766`。无需安装额外依赖。支持内容概览、搜索与主题筛选、排序分页、文章阅读、迭代记录、Markdown 导出和可编辑创作草稿，适配桌面与手机。

工作台只读现有 `data/seo_content.db`，不会导入模型配置、修改环境变量或自动调用模型。所有 CTR 均明确标记为模拟指标。创作草稿保存在当前浏览器的 localStorage，可导出；不代表已执行 CrewAI 任务。现有命令行创作流程保持不变。

可使用 `python web_server.py --port 8766 --database path/to/seo_content.db` 指定已有数据库。服务仅监听本机，不能直接用于公网部署。静态文件采用白名单，不提供数据库、配置文件或凭据下载。

验证：`python -m unittest discover -s tests -p test_web.py`。浏览器回归使用已有 Playwright：`node tests/browser.cjs <playwright模块路径> <浏览器可执行文件路径> http://127.0.0.1:8766`。不修改已有数据，也不调用付费模型。

一个基于 **CrewAI** 框架的工业级多智能体系统，实现了 SEO 内容创作的自动化和持续迭代优化。

## 📋 目录结构

```
seo-agent-system/
├── main.py                 # 系统主入口，异步并发控制
├── agents.py              # 三个 Agent 定义（研究员、作者、评批专家）
├── tasks.py               # 三个 Task 定义（研究、创作、评批）
├── database.py            # SQLite 数据库操作封装
├── rag.py                 # RAG（检索增强生成）模块
├── config.py              # 配置管理（从 .env 读取）
├── init_data.py           # Mock 数据初始化
├── .env                   # 环境变量（需要配置 API Key）
├── requirements.txt       # Python 依赖
└── README.md             # 本文件
```

## 🎯 系统架构

### 三个核心 Agent

```
┌─────────────────────────────────────────────────────────┐
│          SEO 内容营销自迭代 Agent 系统                   │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
    ┌────────┐         ┌─────────┐      ┌──────────┐
    │ 研究员  │         │  作者   │      │ 评批专家 │
    │(RAG)  │ ──────> │(生成)  │ ───> │(反思)   │
    └────────┘         └─────────┘      └──────────┘
        ▲                                      │
        │         闭环迭代 (关键!)            │
        └──────────────────────────────────────┘
```

### 工作流程

#### 第一轮：初始创作

```
1. SEO 研究员
   - 从 ChromaDB 检索相关爆款文案
   - 提炼成功的内容特征
   - 输出"SEO 策略报告"

2. 爆款内容主笔
   - 阅读研究报告
   - 生成新的 SEO 文章
   - 保存到 SQLite 数据库

3. 数据迭代评批
   - 读取文章的模拟 CTR
   - 与预期 CTR 对比
   - 生成改进反思和建议
   - 保存到 iteration_logs 表
```

#### 闭环迭代：持续优化

```
下一轮创作时：
- Writer 会读取前一轮的迭代建议
- 基于建议优化内容
- 形成自迭代的循环
```

## 🔑 核心概念解析

### 1. RAG（检索增强生成）

**问题**：LLM 凭空生成文案可能不够优质。
**解决**：使用历史爆款文案作为参考。

**RAG 的三步**：
1. **编码**：历史文案 → 向量（使用 embedding 模型）
2. **检索**：新关键词 → 向量，找出最相似的历史文案
3. **增强**：将检索结果作为上下文，增强 LLM 生成

**本系统的实现**：
```python
rag = get_rag_system("seo_content")
results = rag.search("Python 教程", n_results=5)
# 返回 5 篇最相似的历史文案，供 Writer 参考
```

### 2. 异步并发

**问题**：串行处理多个主题太慢（每个主题可能需要 100+ 秒 LLM 调用）。
**解决**：使用 asyncio 异步执行。

**性能对比**：
- 串行：处理 2 个主题 = 200 秒
- 异步：处理 2 个主题 ≈ 110 秒

**实现**：
```python
# 并发处理 2 个主题
results = await system.process_topics_concurrent([
    {'keyword': 'Python 教程', 'topic': '技术'},
    {'keyword': '副业赚钱', 'topic': '创业'}
])
```

### 3. 闭环迭代

**问题**：一次性创作缺乏反馈，无法持续改进。
**解决**：建立数据反馈循环。

**闭环的三个环节**：

```
第一轮：
  Writer 创作 → Evaluator 评批 → 反思存入 DB

第二轮：
  Reader 读取前轮反思 → Writer 基于建议改进 → Evaluator 再次评批
  
无限循环，直到 CTR 达到目标
```

**SQL 实现**：
```python
# Evaluator 生成反思，存入 iteration_logs 表
db.insert_iteration_log(
    article_id=1,
    reflection="标题吸引力不足",
    suggestions="在标题中加入数字和数量词"
)

# Writer 查询最新反思
latest = db.get_latest_reflection(topic_theme="技术")
# 下次写作时参考这个建议
```

## 🛠️ 安装与配置

### 1. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

编辑 `.env` 文件：

```bash
OPENAI_API_KEY=sk-...your-actual-key...
OPENAI_MODEL=gpt-4-turbo
```

## 🚀 运行系统

### 基础运行

```bash
python main.py
```

系统会：
1. ✅ 验证配置
2. ✅ 初始化 Mock 数据（ChromaDB + SQLite）
3. ✅ 创建 Agent 团队
4. ✅ 并发处理 2 个主题
5. ✅ 显示统计和迭代反思

### 自定义运行

编辑 `main.py` 中的 `topics_to_process`：

```python
topics_to_process = [
    {'keyword': 'AI 与未来', 'topic': '技术'},
    {'keyword': '创业融资', 'topic': '商业'},
    {'keyword': '财务自由', 'topic': '金融'},
]
```

## 📊 数据库结构

### articles 表（文章存储）

```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    title TEXT,           -- 文章标题
    content TEXT,         -- 文章内容
    keyword TEXT,         -- SEO 关键词
    mock_ctr REAL,        -- 模拟点击率
    topic_theme TEXT,     -- 主题分类
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### iteration_logs 表（迭代日志）

```sql
CREATE TABLE iteration_logs (
    id INTEGER PRIMARY KEY,
    article_id INTEGER,    -- 关联文章 ID
    round_number INTEGER,  -- 迭代轮次
    reflection TEXT,       -- 评批反思
    suggestions TEXT,      -- 改进建议 ← Writer 下次会参考这个
    previous_ctr REAL,     -- 前一轮 CTR
    created_at TIMESTAMP
)
```

### keywords 表（关键词库）

```sql
CREATE TABLE keywords (
    id INTEGER PRIMARY KEY,
    keyword TEXT,
    search_volume INTEGER,      -- 搜索量
    competition_level TEXT,     -- 竞争度
    success_count INTEGER,      -- 成功次数
    created_at TIMESTAMP
)
```

## 🔌 API 与工具集成

### 使用数据库

```python
from database import get_db

db = get_db()

# 查询统计
stats = db.get_statistics()
print(f"总文章数: {stats['total_articles']}")
print(f"平均 CTR: {stats['avg_ctr']}")

# 插入新文章
article_id = db.insert_article(
    title="新文章",
    content="内容...",
    keyword="关键词",
    mock_ctr=0.35
)

# 查询迭代日志
logs = db.get_iteration_logs_for_article(article_id)
```

### 使用 RAG

```python
from rag import get_rag_system

rag = get_rag_system("seo_content")

# 添加新文档
rag.add_documents(
    documents=["文档内容"],
    metadatas=[{"keyword": "Python"}]
)

# 检索相似文档
results = rag.search("编程教程", n_results=5)
for result in results:
    print(f"标题: {result['metadata']['original_title']}")
    print(f"相似度: {1 - result['distance']:.3f}")
```

## 📝 代码注释说明

每个文件都包含详细的中文注释，解释：

- **为什么这么写**（设计原理）
- **怎么工作的**（执行流程）
- **什么时候用**（应用场景）

例如在 `main.py` 中：

```python
async def process_topics_concurrent(self, topics):
    """
    并发处理多个 SEO 主题
    
    asyncio.gather 的工作原理：
    - 接收多个 coroutine（异步函数）
    - 并发执行所有 coroutine
    - 等待所有 coroutine 完成后返回结果列表
    """
    tasks = [self.process_topic_async(...) for ...]
    results = await asyncio.gather(*tasks)
    return results
```

## 🎓 学习路径

### 第一阶段：理解架构

1. 阅读 `README.md`（本文件）
2. 浏览 `agents.py` 和 `tasks.py`
3. 理解三个 Agent 的职责

### 第二阶段：了解数据流

1. 研究 `database.py` 的表结构
2. 学习 `rag.py` 的 RAG 原理
3. 跟踪 `main.py` 中的执行流程

### 第三阶段：动手实验

1. 修改 `init_data.py` 中的 Mock 数据
2. 在 `main.py` 中添加新的主题
3. 观察数据库的变化

### 第四阶段：扩展功能

1. 添加新的 Agent（如 SEO 优化专家）
2. 集成真实的 LLM（目前用 Mock）
3. 部署到生产环境

## 🔧 常见问题

### Q: 为什么需要 RAG？

A: RAG 不是可选的，是提高内容质量的关键。LLM 的生成质量取决于上下文。有爆款参考比没有参考好得多。

### Q: 异步一定比同步快吗？

A: 不一定。异步适合 I/O 密集型任务（如 LLM 调用）。对于 CPU 密集型任务，异步反而可能更慢。

### Q: 如何扩展到更多主题？

A: 修改 `main.py` 中的 `topics_to_process` 列表。但要注意 `MAX_CONCURRENT_TASKS` 限制（防止 API 限流）。

### Q: 如何集成真实 LLM？

A: 目前系统已经支持 OpenAI API。只需在 `.env` 中配置真实的 API Key。CrewAI 会自动调用。

## 📚 参考资源

- [CrewAI 官方文档](https://docs.crewai.com/)
- [ChromaDB 向量数据库](https://docs.trychroma.com/)
- [OpenAI API 文档](https://platform.openai.com/docs/)
- [Python asyncio 官方文档](https://docs.python.org/3/library/asyncio.html)

## 🤝 贡献指南

欢迎提交 Issue 和 PR！请确保：

1. 代码有清晰的中文注释
2. 遵循 PEP 8 代码风格
3. 添加必要的错误处理

## 📄 许可证

MIT License

## 📞 联系方式

如有问题，欢迎通过以下方式联系：

- 提交 GitHub Issue
- 发送邮件

---

**最后的话**：这个系统展示了如何用现代 AI 技术（多智能体、RAG、异步并发）构建一个真实的工业级应用。希望它能帮助你理解多智能体系统的架构和工程实现！🎉


## GitHub 复制说明

本仓库复制自 https://github.com/fanyuxiang20051076/CrewAI_SEO_MVP ，源提交为 `54deadad42045436156c05a76545418dabd07614`。

复制时移除了硬编码 API 密钥，以新的初始提交保存源码和数据，未复制含密钥的原始 Git 历史。运行前将 `.env.example` 复制为 `.env`，填写自己的 `OPENAI_API_KEY`。
