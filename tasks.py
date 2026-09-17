"""
Tasks 模块
==========
为每个 Agent 定义具体的任务。

Task 与 Agent 的关系：
- Agent 是"人"（具有角色和能力）
- Task 是"工作"（具体的目标和执行流程）
- 一个 Agent 可以执行多个 Task

Task 的三个核心属性：
1. description: 任务描述（告诉 Agent 要做什么）
2. expected_output: 期望输出（告诉 Agent 输出应该是什么样的）
3. agent: 执行该任务的 Agent

为什么需要工具集成？
- Task 可以调用外部工具（数据库查询、API 调用等）
- 这样 Agent 就不仅能生成文本，还能与现实世界交互
"""

from crewai import Task
from agents import (
    SEOResearcherAgent,
    ContentWriterAgent,
    CriticEvaluatorAgent
)
from database import get_db
from rag import get_rag_system
from typing import List, Optional
import json


class SEOResearchTask:
    """
    SEO 研究任务
    
    流程：
    1. 接收目标关键词
    2. 从 ChromaDB 检索相关爆款文案
    3. 分析成功特征
    4. 生成写作建议
    """

    @staticmethod
    def create(keyword: str, topic: str = None) -> Task:
        """
        创建 SEO 研究任务
        
        Args:
            keyword: 目标 SEO 关键词（如 "Python 教程"）
            topic: 主题分类（如 "技术"、"创业"）
        
        为什么需要 prompt 工程？
        - LLM 不会自动调用外部工具（数据库、RAG）
        - 需要在 description 中明确告诉 Agent：
          * 使用什么工具（RAG 检索）
          * 如何使用工具
          * 最终输出什么内容
        """
        
        # 第一步：执行 RAG 检索
        rag = get_rag_system("seo_content")
        retrieval_results = rag.search_by_keyword(keyword, n_results=5)
        
        # 将检索结果转化为可读的文本
        retrieval_context = "## 历史爆款文案库检索结果\n\n"
        for i, result in enumerate(retrieval_results, 1):
            retrieval_context += f"""
### 相似文案 {i}
- **原标题**: {result['metadata']['original_title']}
- **关键词**: {result['metadata']['keyword']}
- **CTR**: {result['metadata']['ctr']}
- **启发点**: {result['metadata']['insights']}
- **相似度**: {1 - result['distance']:.3f}
"""
        
        return Task(
            description=f"""
            分析关键词 '{keyword}' 的内容创作策略。
            
            你需要：
            1. 参考以下历史爆款文案库的检索结果：
            {retrieval_context}
            
            2. 总结出 3-5 个成功的内容特征（如标题策略、内容结构、数据表达等）
            
            3. 针对关键词 '{keyword}'，生成具体的写作建议：
               - 建议的标题（至少 2 个选项）
               - 推荐的内容结构（标题 → 问题引入 → 解决方案 → 总结）
               - 关键的数据点和数字表达
               - 如何设计 CTA（行动号召）来吸引点击
            
            4. 输出一份详细的"SEO 内容策略报告"
            """,
            expected_output="""
            一份结构化的 SEO 内容策略报告，包含：
            - 关键词分析
            - 竞品文案分析（基于历史爆款）
            - 3 个关键的成功因素
            - 2 个备选标题
            - 推荐的内容结构
            - 具体的数据表达建议
            """,
            agent=SEOResearcherAgent.create(),
            # 给 LLM 更多时间完成复杂任务
            # max_retries=2 表示如果失败可以重试 2 次
        )


class ContentWriteTask:
    """
    内容创作任务
    
    流程：
    1. 接收 SEO 研究报告
    2. 查询数据库中的迭代建议（闭环迭代）
    3. 生成高质量的 SEO 文章
    4. 保存到数据库
    """

    @staticmethod
    def create(
        keyword: str,
        research_report: str,
        topic: str = None
    ) -> Task:
        """
        创建内容创作任务
        
        Args:
            keyword: 目标关键词
            research_report: SEO 研究员生成的报告
            topic: 主题分类
        
        为什么要在 Task 中查询数据库？
        - 实现闭环迭代的关键步骤
        - Writer 不是凭空创作，而是基于：
          * 历史爆款范式（RAG 提供）
          * 前一轮的失败教训（数据库提供）
        """
        
        # 第一步：从数据库查询最新的迭代建议
        db = get_db()
        latest_reflection = db.get_latest_reflection(topic_theme=topic)
        
        reflection_context = ""
        if latest_reflection:
            reflection_context = f"""
## 前一轮的改进建议（来自评批专家）

**评批反思**: {latest_reflection['reflection']}

**改进建议**: {latest_reflection['suggestions']}

请在这次创作中充分考虑这些建议，避免重复犯错。
"""
        
        return Task(
            description=f"""
            根据 SEO 研究员的建议，创作一篇高质量的 SEO 文章。
            
            **目标关键词**: {keyword}
            **主题分类**: {topic}
            
            **SEO 研究报告**:
            {research_report}
            
            {reflection_context}
            
            你需要：
            1. 选择一个有吸引力的标题（最好从研究报告的建议中选择或优化）
            2. 创作文章内容，包含：
               - 开头：用问题或数据吸引读者
               - 中间：提供 3-5 个核心要点或解决方案
               - 结尾：总结和 CTA（如订阅、评论、分享）
            3. 文章长度：800-1200 字
            4. 确保文章可读性强，使用清晰的标题和要点列表
            5. 融入关键词但不过度堆砌（自然融入）
            
            输出格式：
            # 标题
            内容...
            """,
            expected_output="""
            一篇完整的 SEO 文章，包含：
            - 吸引人的标题
            - 800-1200 字的优质内容
            - 清晰的结构和要点
            - 自然融入的关键词
            - 有力的 CTA（行动号召）
            """,
            agent=ContentWriterAgent.create(),
        )


class EvaluationTask:
    """
    评批任务
    
    流程：
    1. 读取数据库中的文章 CTR
    2. 对比预期 CTR
    3. 生成改进反思
    4. 保存回数据库，形成闭环
    
    这是自迭代系统的核心！
    """

    @staticmethod
    def create(
        keyword: str,
        generated_article: str,
        topic: str = None,
        expected_ctr: float = 0.40
    ) -> Task:
        """
        创建评批任务
        
        Args:
            keyword: 文章关键词
            generated_article: 生成的文章内容
            topic: 主题
            expected_ctr: 预期 CTR（目标值）
        
        为什么需要这个 Task？
        - 没有反馈的创作是盲目的
        - 通过数据反馈，系统才能学习和改进
        - 闭环的形成：生成 → 评批 → 反思 → 改进 → 生成
        """
        
        # 从数据库获取类似文章的历史 CTR
        db = get_db()
        articles_by_topic = db.get_articles_by_topic(topic_theme=topic) if topic else []
        
        ctr_context = ""
        if articles_by_topic:
            avg_ctr = sum(a['mock_ctr'] for a in articles_by_topic) / len(articles_by_topic)
            ctr_context = f"""
## 历史 CTR 数据参考

- 目标 CTR（预期）: {expected_ctr:.1%}
- 同主题平均 CTR: {avg_ctr:.1%}
- 过去发布文章数: {len(articles_by_topic)}

本文章应至少达到平均水平或以上。
"""
        
        return Task(
            description=f"""
            评批生成的 SEO 文章，并生成改进建议。
            
            **评批对象**:
            关键词: {keyword}
            主题: {topic}
            
            {ctr_context}
            
            **生成的文章内容**:
            {generated_article}
            
            你的任务：
            1. 评估文章的质量，从以下角度分析：
               - 标题吸引力（是否能吸引用户点击？）
               - 内容结构（是否清晰易读？）
               - 关键词融入（自然度如何？）
               - CTA 有效性（是否能驱动用户行动？）
               - 数据使用（是否充分利用了数字和统计？）
            
            2. 假设模拟 CTR 为: {expected_ctr:.1%}（随机 ±10%）
            
            3. 如果 CTR 低于预期，生成：
               - **深入反思**: 为什么 CTR 低？主要问题是什么？
               - **具体建议**: 如何改进？下次应该注意什么？
            
            4. 输出结构化的评批报告
            """,
            expected_output="""
            详细的评批报告，包含：
            - 文章质量评分（1-10）
            - 各维度评价（标题、结构、关键词、CTA）
            - 模拟 CTR 值
            - 如果 CTR 低于预期：
              * 问题分析（为什么低）
              * 改进建议（具体怎么改）
            - 总体建议
            """,
            agent=CriticEvaluatorAgent.create(),
        )


# ===================== Task 工厂函数 =====================

def create_seo_task_sequence(
    keyword: str,
    topic: str = "技术",
    expected_ctr: float = 0.40
) -> tuple:
    """
    创建完整的 SEO 创作流程
    
    流程：研究 → 创作 → 评批 → 改进建议存库（闭环）
    
    返回值：(research_task, write_task, eval_task)
    """
    
    # Task 1: 研究
    research_task = SEOResearchTask.create(keyword, topic)
    
    # Task 2: 创作（依赖研究结果）
    # 注意：这里我们先创建一个占位符，实际执行时会传入 research_task 的输出
    write_task = ContentWriteTask.create(
        keyword=keyword,
        research_report="[研究报告将在运行时传入]",
        topic=topic
    )
    
    # Task 3: 评批（依赖创作结果）
    eval_task = EvaluationTask.create(
        keyword=keyword,
        generated_article="[生成的文章将在运行时传入]",
        topic=topic,
        expected_ctr=expected_ctr
    )
    
    return research_task, write_task, eval_task


if __name__ == '__main__':
    # 测试任务创建
    research_task, write_task, eval_task = create_seo_task_sequence(
        keyword="Python 教程",
        topic="技术",
        expected_ctr=0.40
    )
    print("✅ 任务创建成功")
