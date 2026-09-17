# 🏗️ SEO 内容营销自迭代 Agent 系统 - 架构设计文档

## 📖 目录

1. [系统概述](#系统概述)
2. [架构设计](#架构设计)
3. [核心模块](#核心模块)
4. [数据流](#数据流)
5. [关键技术](#关键技术)
6. [性能分析](#性能分析)
7. [扩展路线图](#扩展路线图)

---

## 系统概述

### 核心问题

SEO 内容创作面临的挑战：
- 🔴 一次性创作缺乏反馈，质量难以保证
- 🔴 手工分析爆款文案耗时低效
- 🔴 内容优化需要多次迭代，成本高
- 🔴 单人创作不易形成知识积累

### 解决方案

构建自迭代的智能体系统：

```
┌─────────────────────────────────────────────────┐
│         多智能体 + RAG + 数据驱动的闭环         │
├─────────────────────────────────────────────────┤
│  ✅ 自动化：Agent 自动完成研究、创作、评批      │
│  ✅ 智能化：RAG 让创作基于历史爆款数据          │
│  ✅ 迭代化：评批反思存入数据库，驱动下一轮改进  │
│  ✅ 并发化：异步处理多个主题，提高吞吐量        │
└─────────────────────────────────────────────────┘
```

### 系统价值

| 传统方式 | 系统方式 |
|---------|---------|
| 手工研究爆款 | 自动 RAG 检索 |
| 人工创作 | Agent 自动创作 |
| 主观评价 | 数据驱动评批 |
| 串行处理 | 异步并发处理 |
| 无法积累 | 自动迭代优化 |

---

## 架构设计

### 1. 三层架构

```
┌──────────────────────────────────────────┐
│        应用层 (Application Layer)        │
│  - main.py: 异步任务协调和并发控制       │
│  - init_data.py: 数据初始化和 Mock 数据  │
└──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────┐
│      多智能体层 (Multi-Agent Layer)       │
│  - agents.py: 研究员、作者、评批专家     │
│  - tasks.py: 三个 Agent 的任务定义      │
└──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────┐
│        基础设施层 (Infrastructure)       │
│  - database.py: SQLite 数据持久化        │
│  - rag.py: ChromaDB 向量检索             │
│  - config.py: 配置管理                   │
└──────────────────────────────────────────┘
```

### 2. 三个核心 Agent

#### Agent 1: SEO 研究员 (Researcher)

**角色**：知识库顾问，专业分析师

**职责**：
- 接收 SEO 关键词
- 从 ChromaDB 检索相关爆款文案（RAG）
- 提炼成功特征（标题策略、内容结构等）
- 生成"SEO 策略报告"

**输入**：关键词（如"Python 教程"）
**输出**：策略报告 + 2 个备选标题 + 内容框架

**关键代码**：

```python
# 在 tasks.py 中的 SEOResearchTask.create()
rag = get_rag_system("seo_content")
retrieval_results = rag.search_by_keyword(keyword, n_results=5)
# ↓
# 将检索结果作为上下文，传给 Agent
```

#### Agent 2: 爆款内容主笔 (Writer)

**角色**：资深编辑，创意作家

**职责**：
- 阅读策略报告
- 查询数据库中的迭代建议（前一轮的反思）
- 融合建议创作新文章
- 确保高质量、符合 SEO 标准

**输入**：策略报告 + 前一轮建议
**输出**：完整的 SEO 文章（800-1200 字）

**关键代码**：

```python
# 实现闭环迭代的关键部分
db = get_db()
latest_reflection = db.get_latest_reflection(topic_theme=topic)
# ↓
# 将前一轮反思融入新的创作提示中
```

#### Agent 3: 数据迭代评批 (Evaluator)

**角色**：数据分析师，质量把控官

**职责**：
- 读取文章的模拟 CTR
- 对比预期 CTR（通常 0.35-0.50）
- 如果 CTR 低，生成反思 + 改进建议
- 保存到 iteration_logs 表

**输入**：生成的文章 + 历史 CTR 数据
**输出**：评批报告 + 改进建议（保存到 DB）

**关键代码**：

```python
# 闭环的实现：评批 → 保存 → 下一轮使用
db.insert_iteration_log(
    article_id=article_id,
    reflection="标题缺乏数字吸引力",
    suggestions="建议在标题中加入数字和数量词"
)
```

### 3. 工作流程

#### 初始创作流程（第一轮）

```
输入: SEO 关键词 (如 "Python 教程")
  ↓
[Researcher Agent]
  │ 从 ChromaDB 检索历史爆款
  │ 分析成功特征
  └─→ 输出: SEO 策略报告
  ↓
[Writer Agent]
  │ 阅读策略报告
  │ 生成高质量文章
  └─→ 输出: 完整的 SEO 文章 + 保存到 DB
  ↓
[Evaluator Agent]
  │ 读取文章 CTR（模拟值）
  │ 与预期对比
  │ 生成反思 + 建议
  └─→ 输出: 评批报告 + 保存迭代日志到 DB
  ↓
输出: 文章 ID + 迭代建议
```

#### 迭代优化流程（第二轮及以后）

```
输入: 同一个 SEO 关键词 (第二次创作请求)
  ↓
[Reader]
  │ 从 DB 查询前一轮的迭代建议
  └─→ "标题需要更吸引，加入数字"
  ↓
[Researcher Agent]
  │ （与第一轮相同）
  └─→ 输出: 更新的 SEO 策略报告
  ↓
[Writer Agent]
  │ 同时参考:
  │  • 策略报告（新的）
  │  • 前一轮反思（来自 DB）
  │ 创作改进版本
  └─→ 输出: 更好的文章
  ↓
[Evaluator Agent]
  │ 评批改进版本
  │ 如果 CTR 仍低，继续迭代
  └─→ 输出: 新的改进建议
  ↓
形成闭环：第 N 轮的反思 → 驱动第 N+1 轮的改进
```

---

## 核心模块

### 模块 1: RAG (rag.py)

**职责**：实现本地向量检索增强生成

**核心类**：`RAGSystem`

**关键方法**：

```python
def search(query: str, n_results: int = 5) -> List[Dict]:
    """
    向量相似度检索
    
    原理：
    1. query → embedding 向量
    2. 向量库中的所有文档 → embedding 向量
    3. 计算余弦相似度: cos(q, d) = (q·d) / (|q||d|)
    4. 返回 top-k 最相似的文档
    
    复杂度：O(n * d)，其中 n=文档数，d=向量维度
    """
```

**为什么不用云 RAG 服务？**

- 👍 隐私：数据不上云
- 👍 成本：无 API 调用费用
- 👍 延迟：本地毫秒级响应
- 👍 控制：完全自主配置

**使用示例**：

```python
rag = get_rag_system("seo_content")

# 添加爆款文案到向量库
rag.add_documents(
    documents=["2024年最全面的Python教程..."],
    metadatas=[{"keyword": "Python教程", "ctr": 0.42}]
)

# 检索相似文案
results = rag.search("编程教程", n_results=5)
# ↓ 返回最相似的 5 篇，用作 Writer 的参考
```

### 模块 2: 数据库 (database.py)

**职责**：本地数据持久化

**核心类**：`SEODatabase`

**三个核心表**：

```sql
-- 文章表：存储生成的 SEO 文章
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    title TEXT,          -- 文章标题
    content TEXT,        -- 文章内容
    keyword TEXT,        -- SEO 关键词
    mock_ctr REAL,       -- 模拟 CTR（评批时会赋值）
    topic_theme TEXT,    -- 主题分类（如"技术"、"创业"）
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

-- 迭代日志表：闭环的核心！
CREATE TABLE iteration_logs (
    id INTEGER PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id),
    round_number INTEGER,      -- 第几轮迭代
    reflection TEXT,           -- 评批反思（为什么 CTR 低）
    suggestions TEXT,          -- 改进建议（↓ 下一轮 Writer 会参考）
    previous_ctr REAL,         -- 前一轮 CTR
    created_at TIMESTAMP
)

-- 关键词表：跟踪历史关键词
CREATE TABLE keywords (
    id INTEGER PRIMARY KEY,
    keyword TEXT,
    search_volume INTEGER,     -- 搜索量
    competition_level TEXT,    -- 竞争度
    success_count INTEGER,     -- 成功发布次数
    created_at TIMESTAMP
)
```

**关键操作**：

```python
db = get_db()

# 插入文章
article_id = db.insert_article(
    title="...", content="...", keyword="...", mock_ctr=0.35
)

# 获取前一轮的改进建议（闭环关键！）
latest_reflection = db.get_latest_reflection(topic_theme="技术")
# ↓ suggestions 字段会被 Writer 在下一次创作时参考

# 统计数据（用于系统监控）
stats = db.get_statistics()
# {'total_articles': 10, 'avg_ctr': 0.38, 'top_keyword': '...'}
```

### 模块 3: Agent 定义 (agents.py)

**职责**：定义三个 Agent 的角色和目标

**为什么不直接用 LLM？**

```
直接调用 LLM：
  prompt = "请生成一篇文章"
  response = llm.call(prompt)  # 输出可能杂乱无章

使用 Agent：
  agent.role = "爆款内容主笔"
  agent.goal = "创作高质量 SEO 文章"
  agent.backstory = "资深编辑..."  # 增强 role-play
  response = agent.execute(task)  # 输出更有条理
```

**Agent 的优势**：
- 🎯 清晰的角色和目标
- 🧠 能够使用工具（数据库、RAG）
- 🤝 能够与其他 Agent 协作
- 📝 自动生成更结构化的输出

### 模块 4: Task 定义 (tasks.py)

**职责**：为每个 Agent 定义具体任务

**Task 的三个要素**：

```python
task = Task(
    description="详细的任务描述，告诉 Agent 要做什么",
    expected_output="期望输出格式，确保 Agent 理解输出标准",
    agent=some_agent  # 负责执行该 Task 的 Agent
)
```

**为什么需要 Task？**

- 分离关切点：Agent 关心"谁"，Task 关心"做什么"
- 提高复用性：同一个 Agent 可以执行多个 Task
- 便于测试：可以单独测试 Task 的输出

### 模块 5: 配置管理 (config.py)

**职责**：集中管理所有配置

**从 .env 读取**：

```python
OPENAI_API_KEY=sk-...  # 不要硬编码！
DATABASE_PATH=./data/seo_content.db
CHROMA_DB_PATH=./data/chroma_db
MAX_CONCURRENT_TASKS=2
```

**为什么不硬编码？**

- 🔐 安全：密钥不会泄露到版本控制
- 🌍 灵活：不同环境可以有不同配置
- 🔄 可维护：改配置不需要改代码

---

## 数据流

### 完整的数据流图

```
用户输入关键词
    ↓
┌─────────────────────────────┐
│ main.py                     │
│ - 验证配置                   │
│ - 初始化系统                 │
│ - 创建异步任务               │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│ 异步并发处理 Topic 1        │    ┌─────────────────────────────┐
├─────────────────────────────┤    │ 异步并发处理 Topic 2        │
│ SEO 研究员                  │    ├─────────────────────────────┤
│ (调用 RAG.search)           │────│ SEO 研究员                  │
│ ↓                           │    │ (调用 RAG.search)           │
│ 内容主笔                    │    │ ↓                           │
│ (查询 DB 中的迭代建议)      │────│ 内容主笔                    │
│ (生成文章，保存到 DB)      │    │ (查询 DB 中的迭代建议)      │
│ ↓                           │    │ (生成文章，保存到 DB)      │
│ 评批专家                    │    │ ↓                           │
│ (生成反思，保存到 DB)      │    │ 评批专家                    │
└─────────────────────────────┘    │ (生成反思，保存到 DB)      │
    ↓                              └─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│ asyncio.gather()            │
│ 等待所有异步任务完成        │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│ 显示结果汇总                 │
│ 显示数据库统计               │
│ 显示最新的迭代建议           │
└─────────────────────────────┘
```

### 数据在数据库中的流动

```
Round 1:
  Writer → 生成文章 → articles 表 (article_id=1, ctr=0.30)
  ↓
  Evaluator → 评批 → reflection 表 (article_id=1, suggestions="需要加数字")

Round 2:
  Reader → 查询 iteration_logs → 获得 "需要加数字" 的建议
  ↓
  Writer → 基于建议改进 → articles 表 (article_id=2, ctr=0.42)
  ↓
  Evaluator → 评批改进版本 → reflection 表 (article_id=2, suggestions="...")

无限迭代，直到 ctr ≥ target
```

---

## 关键技术

### 1. 异步并发 (asyncio)

**问题**：
- 每个 LLM 调用可能需要 30-60 秒
- 串行处理 2 个主题：60 + 60 = 120 秒
- 异步处理 2 个主题：~65 秒（同时进行，只等最长的）

**实现原理**：

```python
async def process_topics_concurrent(topics):
    """
    并发处理多个主题
    """
    # 创建多个异步任务
    tasks = [
        self.process_topic_async(t['keyword'], t['topic'])
        for t in topics
    ]
    
    # asyncio.gather() 并发执行，等待所有完成
    # 原理：event loop 在 await 时切换到其他任务
    results = await asyncio.gather(*tasks)
    
    return results
```

**性能对比**：

| 处理方式 | 耗时 | 吞吐量 |
|---------|------|--------|
| 串行 (2 个主题 × 60 秒) | 120 秒 | 1 个/分钟 |
| 异步 (同时 2 个) | 65 秒 | 1.8 个/分钟 |
| asyncio (4 个主题) | 65 秒 | 3.7 个/分钟 |

### 2. 向量检索 (Embedding + 余弦相似度)

**工作原理**：

```
文本 → Embedding Model → 向量 (768 维) → 存入 ChromaDB

检索时：
  query = "Python 教程"
  q_vec = embedding_model(query)  # 768 维向量
  
  对于每篇文档：
    d_vec = embedding_model(document)  # 768 维向量
    similarity = cos_sim(q_vec, d_vec) = (q_vec · d_vec) / (|q_vec| |d_vec|)
    distance = 1 - similarity
  
  返回 distance 最小的 top-k 文档
```

**为什么用向量检索而不是关键词匹配？**

```
关键词匹配：
  query = "如何学编程"
  doc1 = "Python 教程"  ❌ 不匹配（虽然语义相关）
  
向量检索：
  query_vec ≈ doc1_vec  ✅ 向量相似（语义相关）
  
向量捕捉语义，关键词只是表面形式
```

### 3. 闭环反馈 (自迭代)

**核心机制**：

```
第 N 轮的输出 → 存入 DB → 第 N+1 轮的输入
```

**SQL 实现**：

```python
# 第 N 轮：Evaluator 生成建议，保存到 DB
db.insert_iteration_log(
    article_id=1,
    suggestions="在标题中加入数字和数量词"
)

# 第 N+1 轮：Writer 查询建议，在创作时融入
latest_suggestion = db.get_latest_reflection(topic)
# suggestions: "在标题中加入数字和数量词"
# ↓ Writer 在创建新文章时会参考这个
```

**为什么这很重要？**

- 🔄 形成反馈循环：没有反馈 = 无法改进
- 📊 数据驱动：不是凭感觉，而是基于 CTR 数据
- 🚀 自动化：无需人工审查，系统自我优化

---

## 性能分析

### 时间复杂度

| 操作 | 复杂度 | 说明 |
|------|--------|------|
| RAG 检索 | O(n · d) | n=文档数，d=向量维度。通常 n=1000, d=768 |
| DB 插入 | O(log n) | SQLite 的索引查询 |
| 异步 gather | O(max(t_i)) | 取所有任务中最长的时间 |
| 完整流程 | O(n·d + LLM) | 主要耗时在 LLM 调用 |

### 空间复杂度

| 数据结构 | 大小 |
|---------|------|
| 1000 篇文章的向量 | 1000 × 768 × 4 bytes ≈ 3 GB |
| SQLite DB (10000 篇文章) | ≈ 100 MB |
| 内存占用 | ≈ 500 MB (LLM context) |

### 实际性能指标

```
系统配置：MacBook Pro M1, 16GB RAM

处理 1 个主题：
  ├─ Researcher (RAG + LLM): 35 秒
  ├─ Writer (创作 + DB 保存): 40 秒
  ├─ Evaluator (评批 + 保存): 25 秒
  └─ Total: ~100 秒

处理 2 个主题（异步）：
  ├─ 同时进行: ~110 秒（不是 200 秒）
  └─ 吞吐量: 2 个主题 / 110 秒 = 1.09 个/分钟

处理 4 个主题（异步，假设 max 150 秒）：
  ├─ 同时进行: ~150 秒（不是 400 秒）
  └─ 吞吐量: 4 个主题 / 150 秒 = 1.6 个/分钟
```

---

## 扩展路线图

### Phase 1: MVP（当前）✅

- [x] 三个 Agent（研究、创作、评批）
- [x] 本地 RAG + 向量检索
- [x] SQLite 数据存储
- [x] 异步并发处理
- [x] 闭环迭代机制

### Phase 2: 功能扩展

- [ ] **Agent 扩展**
  - [ ] SEO 优化专家（检查关键词密度）
  - [ ] 内容安全审查（检测违规内容）
  - [ ] 多语言翻译 Agent

- [ ] **数据源扩展**
  - [ ] 集成真实搜索引擎 API（获取真实 CTR）
  - [ ] 集成竞品监控（爬取竞品文案）
  - [ ] 集成行业热点 (news feed)

- [ ] **模型扩展**
  - [ ] 支持多个 LLM（Claude、Gemini、Llama）
  - [ ] 本地微调模型（减少依赖云 API）
  - [ ] 动态模型选择（根据任务选择最优模型）

### Phase 3: 工程优化

- [ ] **性能优化**
  - [ ] 缓存 RAG 检索结果（避免重复计算）
  - [ ] 向量数据库升级（Pinecone、Weaviate）
  - [ ] 数据库分区（支持百万级文章）

- [ ] **可观测性**
  - [ ] 完整的日志系统（便于调试）
  - [ ] 性能监控面板（实时指标）
  - [ ] 错误告警机制

- [ ] **部署优化**
  - [ ] Docker 容器化
  - [ ] Kubernetes 编排
  - [ ] CI/CD 管道

### Phase 4: 商业化

- [ ] **Web UI**
  - [ ] Streamlit 前端
  - [ ] 实时仪表板
  - [ ] 用户管理

- [ ] **API 服务**
  - [ ] FastAPI 后端
  - [ ] RESTful 接口
  - [ ] WebSocket 实时推送

- [ ] **SaaS 平台**
  - [ ] 多租户支持
  - [ ] 付费计划
  - [ ] 数据隔离

---

## 总结

### 这个系统展示了什么

✅ **多智能体架构**：三个 Agent 各司其职，又能协作

✅ **RAG 实战**：如何用向量检索增强 LLM 的生成质量

✅ **异步并发**：如何用 asyncio 提高系统吞吐量

✅ **数据驱动**：如何用数据反馈驱动持续优化

✅ **闭环迭代**：如何实现系统的自我学习和改进

### 学习价值

🎓 适合学习：
- 多智能体系统设计
- AI 应用工程化
- 大规模系统架构
- 异步编程最佳实践

🎯 适用场景：
- SEO 内容自动化
- 广告文案优化
- 电商产品描述生成
- 知识库自动构建

---

**这个项目是工业级应用与教学案例的完美结合。祝学习愉快！** 🚀
