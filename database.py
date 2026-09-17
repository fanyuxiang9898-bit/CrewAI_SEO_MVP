"""
数据库模块
========
使用 sqlite3 构建本地数据存储层，实现：
1. 文章表 (articles) - 存储生成的 SEO 文章
2. 迭代日志表 (iteration_logs) - 存储每次评批的反思建议
3. 关键词表 (keywords) - 存储历史关键词提取

为什么要封装数据库操作？
- 单一职责原则：与数据库相关的逻辑集中在一个模块
- 便于测试：可以轻松 mock 数据库接口
- 代码复用：其他模块通过接口调用数据库，不需要重复 SQL 代码
- 安全性：统一处理 SQL 注入防护（使用参数化查询）
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
from config import Config


class SEODatabase:
    """
    SEO 内容数据库类
    
    核心职责：
    - 初始化表结构
    - 执行 CRUD 操作
    - 管理数据库连接（使用上下文管理器确保连接正确关闭）
    """

    def __init__(self, db_path: str = None):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径。如果为 None，使用配置文件中的路径
        
        为什么要支持自定义路径？
        - 便于单元测试使用临时数据库
        - 支持不同环境使用不同数据库
        """
        self.db_path = db_path or str(Config.DATABASE_PATH)
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """确保数据库文件存在"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接
        
        返回值：sqlite3.Connection 对象
        
        为什么返回连接而不是在类中保存？
        - 避免长连接导致的资源泄漏
        - 每次操作创建新连接，确保线程安全
        - 在异步场景中，每个任务可以独立获取连接
        """
        conn = sqlite3.connect(self.db_path)
        # 设置 row_factory 使得查询结果可以用字典方式访问
        conn.row_factory = sqlite3.Row
        return conn

    def init_tables(self):
        """
        初始化数据库表结构
        
        创建三个核心表：
        1. articles - SEO 文章存储
        2. iteration_logs - 迭代评批日志
        3. keywords - 历史关键词记录
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # ==================== 文章表 ====================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    keyword TEXT NOT NULL,
                    mock_ctr REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    topic_theme TEXT,
                    notes TEXT
                )
            ''')

            # ==================== 迭代日志表 ====================
            # 这是闭环的关键：存储每次评批的反思建议
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS iteration_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    round_number INTEGER NOT NULL,
                    previous_ctr REAL,
                    reflection TEXT NOT NULL,
                    suggestions TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(article_id) REFERENCES articles(id)
                )
            ''')

            # ==================== 关键词表 ====================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    search_volume INTEGER DEFAULT 0,
                    competition_level TEXT,
                    last_used TIMESTAMP,
                    success_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            print("✅ 数据库表初始化成功")
        except sqlite3.Error as e:
            print(f"❌ 数据库初始化失败: {e}")
            raise
        finally:
            conn.close()

    # ===================== 文章操作 =====================

    def insert_article(
        self,
        title: str,
        content: str,
        keyword: str,
        topic_theme: str = None,
        notes: str = None,
        mock_ctr: float = 0.0
    ) -> int:
        """
        插入新文章记录
        
        Args:
            title: 文章标题
            content: 文章内容
            keyword: SEO 关键词
            topic_theme: 主题分类（如 "电商", "教育" 等）
            notes: 备注说明
            mock_ctr: 模拟点击率（0.0-1.0）
        
        Returns:
            插入的文章 ID
        
        为什么使用参数化查询？
        - 防止 SQL 注入攻击
        - 自动转义特殊字符
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO articles (title, content, keyword, topic_theme, notes, mock_ctr)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title, content, keyword, topic_theme, notes, mock_ctr))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"❌ 插入文章失败: {e}")
            raise
        finally:
            conn.close()

    def get_article_by_id(self, article_id: int) -> Optional[Dict]:
        """获取指定 ID 的文章"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM articles WHERE id = ?', (article_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_articles_by_topic(self, topic_theme: str) -> List[Dict]:
        """获取指定主题的所有文章"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM articles WHERE topic_theme = ? ORDER BY created_at DESC',
                (topic_theme,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_all_articles(self, limit: int = 100) -> List[Dict]:
        """获取最近的文章（分页）"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM articles ORDER BY created_at DESC LIMIT ?',
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def update_article_ctr(self, article_id: int, new_ctr: float):
        """更新文章的 CTR 值"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE articles SET mock_ctr = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (new_ctr, article_id)
            )
            conn.commit()
        finally:
            conn.close()

    # ===================== 迭代日志操作 =====================

    def insert_iteration_log(
        self,
        article_id: int,
        round_number: int,
        reflection: str,
        suggestions: str,
        previous_ctr: float = None
    ) -> int:
        """
        插入迭代评批日志
        
        这是闭环系统的核心：
        - 记录每一轮的评批结果
        - 存储改进建议，供下一轮 Writer 参考
        
        Args:
            article_id: 被评批的文章 ID
            round_number: 迭代轮次
            reflection: 评批反思（为什么 CTR 低）
            suggestions: 改进建议（怎么改）
            previous_ctr: 前一轮的 CTR
        
        Returns:
            日志记录 ID
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO iteration_logs 
                (article_id, round_number, reflection, suggestions, previous_ctr)
                VALUES (?, ?, ?, ?, ?)
            ''', (article_id, round_number, reflection, suggestions, previous_ctr))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_iteration_logs_for_article(self, article_id: int) -> List[Dict]:
        """获取一篇文章的所有迭代日志"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT * FROM iteration_logs 
                   WHERE article_id = ? 
                   ORDER BY round_number DESC''',
                (article_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_latest_reflection(self, topic_theme: str = None) -> Optional[Dict]:
        """
        获取最新的反思建议
        
        这个方法用于 Writer 在生成新文章前，
        参考前一轮的评批反思，实现自迭代
        
        Args:
            topic_theme: 如果指定，获取该主题的最新反思；否则全局获取
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if topic_theme:
                cursor.execute('''
                    SELECT il.* FROM iteration_logs il
                    JOIN articles a ON il.article_id = a.id
                    WHERE a.topic_theme = ?
                    ORDER BY il.created_at DESC LIMIT 1
                ''', (topic_theme,))
            else:
                cursor.execute(
                    'SELECT * FROM iteration_logs ORDER BY created_at DESC LIMIT 1'
                )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # ===================== 关键词操作 =====================

    def insert_keyword(
        self,
        keyword: str,
        search_volume: int = 0,
        competition_level: str = None
    ):
        """插入关键词记录"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO keywords (keyword, search_volume, competition_level)
                VALUES (?, ?, ?)
            ''', (keyword, search_volume, competition_level))
            conn.commit()
        finally:
            conn.close()

    def get_popular_keywords(self, limit: int = 10) -> List[Dict]:
        """获取最常用的关键词（按成功次数排序）"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM keywords 
                ORDER BY success_count DESC, search_volume DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    # ===================== 统计与分析 =====================

    def get_statistics(self) -> Dict:
        """
        获取系统的统计数据
        
        返回值示例：
        {
            'total_articles': 10,
            'avg_ctr': 0.35,
            'total_iterations': 5,
            'top_keyword': 'Python教程'
        }
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # 总文章数
            cursor.execute('SELECT COUNT(*) as count FROM articles')
            total_articles = cursor.fetchone()['count']
            
            # 平均 CTR
            cursor.execute('SELECT AVG(mock_ctr) as avg_ctr FROM articles')
            avg_ctr = cursor.fetchone()['avg_ctr'] or 0.0
            
            # 总迭代次数
            cursor.execute('SELECT COUNT(*) as count FROM iteration_logs')
            total_iterations = cursor.fetchone()['count']
            
            # 最常用关键词
            cursor.execute('''
                SELECT keyword FROM articles 
                GROUP BY keyword 
                ORDER BY COUNT(*) DESC 
                LIMIT 1
            ''')
            top_keyword_row = cursor.fetchone()
            top_keyword = top_keyword_row['keyword'] if top_keyword_row else 'N/A'
            
            return {
                'total_articles': total_articles,
                'avg_ctr': round(avg_ctr, 4),
                'total_iterations': total_iterations,
                'top_keyword': top_keyword
            }
        finally:
            conn.close()


# ===================== 单例模式的数据库管理器 =====================

_db_instance: Optional[SEODatabase] = None


def get_db() -> SEODatabase:
    """
    获取全局数据库实例
    
    为什么使用单例模式？
    - 确保整个应用中只有一个数据库连接管理器
    - 避免多个模块各自创建连接，造成资源浪费
    - 但注意：每次操作仍然创建独立的连接，避免并发问题
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = SEODatabase()
    return _db_instance


if __name__ == '__main__':
    # 测试数据库操作
    db = SEODatabase('./test.db')
    db.init_tables()
    
    # 插入测试文章
    article_id = db.insert_article(
        title="Python 教程",
        content="这是一篇 Python 教程...",
        keyword="Python",
        topic_theme="技术",
        mock_ctr=0.25
    )
    print(f"✅ 插入文章 ID: {article_id}")
    
    # 查询统计
    stats = db.get_statistics()
    print(f"📊 统计数据: {stats}")
