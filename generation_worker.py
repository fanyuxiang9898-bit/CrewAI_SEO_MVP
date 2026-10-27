"""CrewAI worker. Progress changes only on actual stage execution/completion."""
import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.request import Request, urlopen
from generation import JobStore, load_settings


def historical_context(database, keyword, topic):
    if not Path(database).is_file():
        return "没有可用的历史文章。不要虚构检索结果或数据。"
    with closing(sqlite3.connect(Path(database).resolve().as_uri()+"?mode=ro", uri=True)) as conn:
        rows = conn.execute("SELECT title,substr(content,1,600),keyword FROM articles WHERE keyword LIKE ? OR topic_theme=? ORDER BY id DESC LIMIT 3", ('%'+keyword+'%', topic)).fetchall()
        reviews = conn.execute("SELECT substr(reflection,1,500),substr(suggestions,1,500) FROM iteration_logs JOIN articles ON articles.id=article_id WHERE topic_theme=? ORDER BY iteration_logs.id DESC LIMIT 1", (topic,)).fetchall()
    return json.dumps({"historical_articles": rows, "previous_review": reviews}, ensure_ascii=False)


def run_job(store, identifier, settings, database):
    from crewai import Agent, BaseLLM, Crew, Process, Task

    class EndpointLLM(BaseLLM):
        def __init__(self):
            super().__init__(model=settings['model'], temperature=.5)

        def call(self, messages, tools=None, callbacks=None, available_functions=None, **kwargs):
            if isinstance(messages, str):
                messages = [{"role": "user", "content": messages}]
            headers = {"Content-Type": "application/json"}
            if settings.get('api_key_file'):
                headers['Authorization'] = 'Bearer '+Path(settings['api_key_file']).read_text(encoding='utf-8').strip()
            body = {"model": settings['model'], "messages": messages, "temperature": .5,
                    "max_tokens": settings['max_tokens'], "stream": False}
            if self.stop:
                body['stop'] = self.stop
            request = Request(settings['endpoint'], data=json.dumps(body).encode(), headers=headers)
            with urlopen(request, timeout=settings['request_timeout']) as response:
                data = json.load(response)
            if data['choices'][0].get('finish_reason') == 'length':
                raise ValueError('model output reached token limit')
            text = data['choices'][0]['message']['content']
            if not isinstance(text, str) or not text.strip():
                raise ValueError('empty model output')
            return text

        def supports_function_calling(self):
            return False

        def get_context_window_size(self):
            return 8192

    brief = store.get(identifier)['brief']
    context = historical_context(database, brief['keyword'], brief['topic'])
    llm = EndpointLLM()
    roles = [('research', 'SEO 内容研究员', '给出有依据、可执行的写作策略'),
             ('writing', '内容主笔', '根据研究报告完成中文文章'),
             ('review', '内容评批专家', '核查文章质量并提供具体改进建议')]
    tasks, agents = [], []
    instructions = [
        f"分析创作需求：{json.dumps(brief, ensure_ascii=False)}。参考本地检索内容：{context}。历史数据仅供写作参考，不是真实市场成效。输出读者定位、搜索意图、2个标题及写作提纲。不要虚构事实或统计；不需要联网或使用工具。",
        f"需求：{json.dumps(brief, ensure_ascii=False)}。根据上一个任务的研究报告写一篇约600至900字的完整中文文章。以 Markdown 一级标题开头，包含清晰的小标题、实用建议和结尾。未知事实明确表述，不编造案例或效果数据。只输出文章正文，不输出思考过程。",
        "根据前面的研究报告和文章逐项检查标题、结构、关键词自然度、事实依据和行动建议。输出简短质量评估与3至5条具体改进建议。没有真实投放数据，不得声称实际CTR、阅读量或预测数值。"
    ]
    for index, (stage, role, goal) in enumerate(roles):
        agent = Agent(role=role, goal=goal, backstory='你是一位严谨的中文内容编辑。以用户需求和给定资料为准，不编造数据。', llm=llm, allow_delegation=False, verbose=False, max_iter=2, max_retry_limit=0)
        agents.append(agent)

        def completed(output, stage=stage, index=index):
            store.stage(identifier, stage, output.raw)
            if index < 2:
                store.stage(identifier, roles[index+1][0])

        task = Task(description=instructions[index], expected_output=['中文研究报告与提纲', '完整中文 Markdown 文章', '中文质量评估与可执行修改建议'][index], agent=agent, context=tasks.copy(), callback=completed)
        tasks.append(task)
    crew = Crew(agents=agents, tasks=tasks, process=Process.sequential, verbose=False,
                memory=False, planning=False, tracing=False, share_crew=False)
    crew.kickoff()
    store.finish(identifier, 'completed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ['jobs', 'settings', 'database', 'job']:
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args()
    store = JobStore(args.jobs)
    try:
        run_job(store, args.job, load_settings(args.settings), args.database)
    except Exception:
        # Provider exceptions can contain credentials or request text. Never persist them.
        store.finish(args.job, 'failed', '模型调用失败或输出不完整。请检查模型服务是否在线、额度与认证配置后重试。已完成的阶段结果已保留。')
        raise SystemExit(1)
