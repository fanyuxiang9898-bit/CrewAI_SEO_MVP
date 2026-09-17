#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
一键修复脚本 - 创建正确编码的 requirements.txt
================================================

使用方法：
  python fix_requirements.py

这个脚本会：
1. 删除原来的 requirements.txt（如果有问题的话）
2. 创建新的 requirements.txt（UTF-8 编码）
3. 自动安装所有依赖
"""

import os
import sys
import subprocess


def create_requirements():
    """创建正确编码的 requirements.txt"""
    
    requirements_content = """crewai==0.28.0
openai==1.3.0
chromadb==0.4.0
sentence-transformers==2.2.2
python-dotenv==1.0.0
pydantic==2.4.0
pytz==2024.1
python-json-logger==2.0.7
"""
    
    try:
        # 写入文件，确保使用 UTF-8 编码
        with open('requirements.txt', 'w', encoding='utf-8') as f:
            f.write(requirements_content)
        
        print("✅ requirements.txt 已创建（UTF-8 编码）")
        return True
    except Exception as e:
        print(f"❌ 创建 requirements.txt 失败: {e}")
        return False


def install_requirements():
    """安装依赖"""
    
    print("\n📦 开始安装依赖（可能需要 3-5 分钟）...")
    print("=" * 60)
    
    try:
        # 运行 pip install
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            capture_output=False
        )
        
        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("✅ 所有依赖安装成功！")
            print("=" * 60)
            return True
        else:
            print("\n❌ 依赖安装失败")
            return False
            
    except Exception as e:
        print(f"\n❌ 安装过程出错: {e}")
        return False


def verify_installation():
    """验证安装是否成功"""
    
    print("\n🔍 验证依赖安装...")
    
    try:
        import crewai
        print("✓ crewai 已安装")
        
        import openai
        print("✓ openai 已安装")
        
        import chromadb
        print("✓ chromadb 已安装")
        
        import sentence_transformers
        print("✓ sentence_transformers 已安装")
        
        from dotenv import load_dotenv
        print("✓ python-dotenv 已安装")
        
        import pydantic
        print("✓ pydantic 已安装")
        
        print("\n✅ 所有依赖验证成功！")
        return True
        
    except ImportError as e:
        print(f"❌ 验证失败: {e}")
        return False


def main():
    """主函数"""
    
    print("\n" + "🔧" * 30)
    print("一键修复脚本 - 修复编码错误")
    print("🔧" * 30)
    
    print("\n📋 操作步骤:")
    print("1. 创建正确编码的 requirements.txt")
    print("2. 安装所有依赖")
    print("3. 验证安装结果")
    
    # 第 1 步
    print("\n" + "=" * 60)
    print("第 1 步：创建 requirements.txt")
    print("=" * 60)
    
    if not create_requirements():
        print("❌ 创建失败，退出")
        return 1
    
    # 第 2 步
    print("\n" + "=" * 60)
    print("第 2 步：安装依赖")
    print("=" * 60)
    
    if not install_requirements():
        print("❌ 安装失败")
        return 1
    
    # 第 3 步
    print("\n" + "=" * 60)
    print("第 3 步：验证安装")
    print("=" * 60)
    
    if not verify_installation():
        print("❌ 验证失败")
        return 1
    
    # 成功
    print("\n" + "🎉" * 30)
    print("✅ 所有步骤完成！系统已准备就绪！")
    print("🎉" * 30)
    
    print("\n📝 后续步骤:")
    print("1. python config.py                      # 验证配置")
    print("2. python test_siliconflow_ready_to_use.py  # 测试 API")
    print("3. python init_data.py                   # 初始化数据")
    print("4. python main.py                        # 运行系统")
    
    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
