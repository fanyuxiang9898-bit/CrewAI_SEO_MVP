"""
直接使用 litellm 测试 API
"""
import os
from litellm import completion

from dotenv import load_dotenv
load_dotenv()
if not os.getenv('OPENAI_API_KEY'):
    raise RuntimeError('Set OPENAI_API_KEY in .env or environment before running this test')
os.environ['OPENAI_API_BASE'] = 'https://api.siliconflow.cn/v1'

try:
    response = completion(
        model="Qwen/Qwen2.5-7B-Instruct",
        messages=[{"role": "user", "content": "你好"}],
        api_base="https://api.siliconflow.cn/v1"
    )
    print("✅ 成功!")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"❌ 失败: {e}")
