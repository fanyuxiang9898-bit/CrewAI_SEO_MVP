"""
配置管理模块 - 硅基流动专属版本
===============================
使用硅基流动的 OpenAI 兼容 API，无需任何额外设置

所有大模型配置都在这里，其他文件不需要再配置！
"""

import os
from pathlib import Path

# ==================== 环境变量设置（必须在导入其他模块之前！）====================
os.environ['CREWAI_TELEMETRY_OPT_OUT'] = 'true'

# ==================== 环境变量读取 ====================
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    """全局配置类 - 所有关键配置都在这里"""

    # ==================== LLM 配置（硅基流动）====================
    # 重要：大模型配置只在这里设置！

    # API Key - 硅基流动 API
    LLM_API_KEY = os.getenv('OPENAI_API_KEY', '')

    # 硅基流动的 API 地址
    LLM_BASE_URL = 'https://api.siliconflow.cn/v1'

    # 选择的模型
    # 可选模型：
    # - Qwen/Qwen2.5-7B-Instruct（快速+便宜，推荐）
    # - Qwen/Qwen2.5-14B-Instruct（更强大）
    LLM_MODEL = 'openai/Qwen/Qwen2.5-7B-Instruct'
    # ==================== 设置环境变量（供其他模块使用）====================
    os.environ['OPENAI_API_KEY'] = LLM_API_KEY
    os.environ['OPENAI_API_BASE'] = LLM_BASE_URL

    # ==================== 数据库配置 ====================
    DATABASE_PATH = Path(os.getenv('DATABASE_PATH', './data/seo_content.db'))
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # ==================== 向量数据库配置 ====================
    CHROMA_DB_PATH = os.getenv('CHROMA_DB_PATH', './data/chroma_db')
    EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
    Path(CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)

    # ==================== 系统配置 ====================
    MAX_CONCURRENT_TASKS = int(os.getenv('MAX_CONCURRENT_TASKS', '2'))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def validate(cls):
        """验证关键配置是否存在"""
        if not cls.LLM_API_KEY:
            raise ValueError(
                "\n" + "=" * 60 + "\n"
                "❌ API Key 未设置！\n"
                "=" * 60 + "\n"
                "请在 .env 或环境变量中设置 OPENAI_API_KEY\n"
                "获取 API Key: https://cloud.siliconflow.cn\n"
                "=" * 60 + "\n"
            )

        print("\n✅ 配置验证通过")
        print("   - API Key: 已配置")
        print(f"   - API 地址: {cls.LLM_BASE_URL}")
        print(f"   - 模型: {cls.LLM_MODEL}")
        print()


# ==================== 初始化时设置环境变量 ====================
Config.validate()


if __name__ == '__main__':
    """测试配置"""
    print("✅ 配置测试通过！")
