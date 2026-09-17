"""
agents.py - CrewAI Agent 定义
大模型配置在 config.py 中，这里只需要创建 Agent
"""

from crewai import Agent, LLM
from config import Config


class SEOResearcherAgent:
    """SEO 策略研究员 Agent"""

    @staticmethod
    def create() -> Agent:
        llm = LLM(
            model=Config.LLM_MODEL,
            api_key=Config.LLM_API_KEY,
            base_url=Config.LLM_BASE_URL,
            is_litellm=True
        )

        return Agent(
            role="SEO 策略搜索专家",
            goal="从历史爆款文案数据库中检索相关文案，提供 SEO 策略建议",
            backstory="你是一位经验丰富的 SEO 专家，拥有多年的内容优化经验。你擅长从历史数据中挖掘模式，为内容创作提供数据驱动的建议。",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )


class ContentWriterAgent:
    """爆款内容主笔 Agent"""

    @staticmethod
    def create() -> Agent:
        llm = LLM(
            model=Config.LLM_MODEL,
            api_key=Config.LLM_API_KEY,
            base_url=Config.LLM_BASE_URL,
            is_litellm=True
        )

        return Agent(
            role="爆款内容主笔",
            goal="根据 SEO 策略创作高 CTR 的爆款内容",
            backstory="你是一位资深的内容创作者，曾创作过多篇 10 万+ 阅读的爆款文章。你擅长用数据驱动的标题、引人入胜的开篇和有效的 CTA 来提升文章的吸引力。",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )


class CriticEvaluatorAgent:
    """数据迭代评批 Agent"""

    @staticmethod
    def create() -> Agent:
        llm = LLM(
            model=Config.LLM_MODEL,
            api_key=Config.LLM_API_KEY,
            base_url=Config.LLM_BASE_URL,
            is_litellm=True
        )

        return Agent(
            role="数据迭代评批",
            goal="评估内容质量，生成改进建议，驱动自迭代",
            backstory="你是一位数据分析专家，擅长通过对标历史数据来评估内容表现，并提出科学的改进方案。你相信数据驱动的决策能够不断优化内容质量。",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )


class DataEvaluatorAgent:
    """数据迭代评批 Agent（备用）"""

    @staticmethod
    def create() -> Agent:
        return CriticEvaluatorAgent.create()


def create_seo_team():
    """创建完整的 SEO Agent 团队"""
    researcher = SEOResearcherAgent.create()
    writer = ContentWriterAgent.create()
    evaluator = CriticEvaluatorAgent.create()

    return researcher, writer, evaluator
