"""
main.py - SEO 内容营销自迭代 Agent 系统主入口
"""

import os
import sys
import asyncio
import logging

# ==================== 导入配置（会自动设置环境变量）====================
from config import Config  # 大模型配置在这里，不要在其他地方配置！

from crewai import Crew
from database import get_db
from rag import get_rag_system
from agents import create_seo_team
from tasks import create_seo_task_sequence
from init_data import init_all

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SEOContentCreationSystem:
    """SEO 内容创作系统"""

    def __init__(self, initialize_data: bool = True):
        logger.info("🚀 启动 SEO 内容营销自迭代系统...\n")

        try:
            Config.validate()
        except ValueError as e:
            logger.error(f"❌ 配置验证失败: {e}")
            raise

        if initialize_data:
            logger.info("📦 初始化 Mock 数据...\n")
            try:
                init_all()
            except Exception as e:
                logger.error(f"❌ 数据初始化失败: {e}")
                raise

        self.db = get_db()
        self.rag = get_rag_system("seo_content")

        logger.info("👥 创建 Agent 团队...")
        try:
            self.researcher_agent, self.writer_agent, self.evaluator_agent = create_seo_team()
            logger.info("✅ Agent 团队创建成功\n")
        except Exception as e:
            logger.error(f"❌ Agent 创建失败: {e}")
            raise

    def process_topic(self, keyword: str, topic_theme: str) -> dict:
        logger.info(f"\n🔍 正在启动 Agent 团队处理主题: {keyword}")

        research_task, write_task, eval_task = create_seo_task_sequence(
            keyword=keyword,
            topic=topic_theme,
            expected_ctr=0.40
        )

        seo_crew = Crew(
            agents=[self.researcher_agent, self.writer_agent, self.evaluator_agent],
            tasks=[research_task, write_task, eval_task],
            verbose=True
        )

        result = seo_crew.kickoff()

        print("\n" + "✨" * 30)
        print(f"🎯 最终生成结果 (关键词: {keyword}):")
        print("-" * 60)
        print(result)
        print("-" * 60)
        print("✨" * 30 + "\n")

        return {
            'keyword': keyword,
            'topic': topic_theme,
            'status': 'completed',
            'message': f'✅ 成功处理主题: {keyword}'
        }


async def main():
    try:
        system = SEOContentCreationSystem(initialize_data=True)

        topics_to_process = [
            {'keyword': 'Python 教程', 'topic': '技术'},
            {'keyword': '副业赚钱', 'topic': '创业'},
        ]

        logger.info("⏳ 开始处理主题...\n")

        results = []
        for topic in topics_to_process:
            result = system.process_topic(
                keyword=topic['keyword'],
                topic_theme=topic['topic']
            )
            results.append(result)

        logger.info("\n" + "=" * 60)
        logger.info("✅ 所有主题处理完成！")
        logger.info("=" * 60)

        for result in results:
            logger.info(f"\n{result['message']}")

        stats = system.db.get_statistics()
        logger.info("\n" + "=" * 60)
        logger.info("📊 系统统计信息")
        logger.info("=" * 60)
        logger.info(f"  - 总文章数: {stats['total_articles']}")
        logger.info(f"  - 平均 CTR: {stats['avg_ctr']:.4f}")

        logger.info("\n✅ 系统运行成功！")
        return True

    except Exception as e:
        logger.error(f"\n❌ 系统错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n\n⏸️ 用户中断了系统")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ 发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
