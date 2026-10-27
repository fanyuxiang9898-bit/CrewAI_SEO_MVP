"""Persistent task lifecycle; model execution is isolated from the web process."""
import hashlib
import json
import secrets
import sqlite3
import subprocess
import threading
import time
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

STAGES = ["research", "writing", "review"]
ACTIVE = ("queued", "running")


def now():
    return datetime.now(timezone.utc).isoformat()


def load_settings(path):
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    endpoint = urlsplit(value.get("endpoint", ""))
    local = endpoint.hostname in {"localhost", "127.0.0.1", "::1"}
    if endpoint.username or endpoint.password or endpoint.query or endpoint.fragment:
        raise ValueError("模型地址不能包含凭据、查询参数或片段")
    if endpoint.scheme not in {"http", "https"} or not endpoint.hostname:
        raise ValueError("请配置有效的模型 API 地址")
    if not local and (not value.get("allow_remote_model") or endpoint.scheme != "https"):
        raise ValueError("远程模型需明确启用并使用 HTTPS；请先确认费用")
    if not isinstance(value.get("model"), str) or not value["model"].strip():
        raise ValueError("尚未配置模型名称")
    value["request_timeout"] = min(180, max(5, int(value.get("request_timeout", 150))))
    value["job_timeout"] = min(1200, max(30, int(value.get("job_timeout", 900))))
    value["max_tokens"] = min(3000, max(200, int(value.get("max_tokens", 1600))))
    value["local_model"] = local
    return value


def validate_brief(value):
    if not isinstance(value, dict):
        raise ValueError("请提交有效的创作需求")
    result = {}
    for key, limit, required in [("keyword", 80, True), ("topic", 40, True), ("notes", 2000, False)]:
        raw = value.get(key, "")
        if not isinstance(raw, str) or len(raw) > limit or (required and not raw.strip()):
            raise ValueError(f"{ {'keyword':'关键词','topic':'主题','notes':'创作要求'}[key]}格式无效或超出长度限制")
        result[key] = raw.strip()
    return result


class JobStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS web_jobs (
                id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL, fingerprint TEXT NOT NULL,
                brief TEXT NOT NULL, status TEXT NOT NULL, stage TEXT,
                outputs TEXT NOT NULL DEFAULT '{}', error TEXT,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
            conn.commit()

    def connect(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def serialize(row):
        if not row:
            return None
        data = dict(row)
        data["brief"] = json.loads(data["brief"])
        data["outputs"] = json.loads(data["outputs"])
        data.pop("fingerprint", None)
        data.pop("request_key", None)
        data["completed_stages"] = sum(stage in data["outputs"] for stage in STAGES)
        return data

    def create(self, brief, request_key):
        if not isinstance(request_key, str) or not 16 <= len(request_key) <= 100:
            raise ValueError("缺少有效的请求标识，请刷新页面后重试")
        payload = json.dumps(validate_brief(brief), ensure_ascii=False, sort_keys=True)
        fingerprint = hashlib.sha256(payload.encode()).hexdigest()
        with closing(self.connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute("SELECT * FROM web_jobs WHERE request_key=?", (request_key,)).fetchone()
            if existing:
                if existing["fingerprint"] != fingerprint:
                    raise ValueError("请求标识已被另一份需求使用")
                return self.serialize(existing)
            count = conn.execute("SELECT count(*) FROM web_jobs WHERE status IN ('queued','running')").fetchone()[0]
            if count >= 5:
                raise ValueError("当前最多同时保留 5 个待完成任务，请等待或取消后再提交")
            identifier = secrets.token_hex(12)
            stamp = now()
            conn.execute("INSERT INTO web_jobs(id,request_key,fingerprint,brief,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)", (identifier, request_key, fingerprint, payload, "queued", stamp, stamp))
            conn.commit()
        return self.get(identifier)

    def get(self, identifier):
        with closing(self.connect()) as conn:
            return self.serialize(conn.execute("SELECT * FROM web_jobs WHERE id=?", (identifier,)).fetchone())

    def list(self):
        with closing(self.connect()) as conn:
            return [self.serialize(r) for r in conn.execute("SELECT * FROM web_jobs ORDER BY created_at DESC LIMIT 100")]

    def recover(self):
        with closing(self.connect()) as conn:
            conn.execute("UPDATE web_jobs SET status='interrupted',error=?,updated_at=? WHERE status IN ('queued','running')", ("服务重启导致任务中断。已保留阶段结果，可手动重新创建任务。", now()))
            conn.commit()

    def claim(self):
        with closing(self.connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT id FROM web_jobs WHERE status='queued' ORDER BY created_at LIMIT 1").fetchone()
            if not row:
                return None
            conn.execute("UPDATE web_jobs SET status='running',stage='research',updated_at=? WHERE id=?", (now(), row[0]))
            conn.commit()
            return row[0]

    def stage(self, identifier, stage, output=None):
        with closing(self.connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT outputs,status FROM web_jobs WHERE id=?", (identifier,)).fetchone()
            if not row or row["status"] != "running":
                raise RuntimeError("任务已停止")
            outputs = json.loads(row["outputs"])
            if output is not None:
                if not isinstance(output, str) or not output.strip():
                    raise ValueError("模型返回了空结果")
                outputs[stage] = output.strip()
            conn.execute("UPDATE web_jobs SET stage=?,outputs=?,updated_at=? WHERE id=?", (stage, json.dumps(outputs, ensure_ascii=False), now(), identifier))
            conn.commit()

    def finish(self, identifier, status, error=None):
        if status not in {"completed", "failed", "cancelled", "interrupted"}:
            raise ValueError("无效任务状态")
        with closing(self.connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT outputs FROM web_jobs WHERE id=? AND status IN ('queued','running')", (identifier,)).fetchone()
            if row and status == "completed" and not all(s in json.loads(row[0]) for s in STAGES):
                raise ValueError("任务结果尚不完整")
            conn.execute("UPDATE web_jobs SET status=?,error=?,updated_at=? WHERE id=? AND status IN ('queued','running')", (status, error, now(), identifier))
            conn.commit()
        return self.get(identifier)


class JobManager:
    def __init__(self, store, settings_path, database, python, worker_env=None, worker_script=None):
        self.store, self.settings_path, self.database = store, Path(settings_path), Path(database)
        self.python, self.worker_env = str(python), worker_env
        self.worker_script = Path(worker_script) if worker_script else Path(__file__).with_name('generation_worker.py')
        try:
            checked = subprocess.run([self.python, '-c', "import importlib.metadata; print(importlib.metadata.version('crewai'))"], capture_output=True, timeout=15)
            self.runtime_ok = checked.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            self.runtime_ok = False
        self.stopping = threading.Event()
        self.store.recover()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def availability(self):
        try:
            settings = load_settings(self.settings_path)
            if not Path(self.python).is_file() or not self.runtime_ok:
                raise ValueError("未找到任务执行环境，请安装 requirements-web.txt")
            key = settings.get("api_key_file")
            if key and not Path(key).is_file():
                raise ValueError("模型认证文件不可用，请检查服务配置")
            return {"available": True, "model": settings["model"], "local_model": settings["local_model"]}
        except (OSError, ValueError, TypeError):
            return {"available": False, "message": "生成服务尚未配置，请检查服务端模型配置与任务运行环境。"}

    def run(self):
        while not self.stopping.wait(.3):
            identifier = self.store.claim()
            if not identifier:
                continue
            process = None
            try:
                settings = load_settings(self.settings_path)
                command = [self.python, "-X", "utf8", str(self.worker_script), "--jobs", str(self.store.path.resolve()), "--settings", str(self.settings_path.resolve()), "--database", str(self.database.resolve()), "--job", identifier]
                process = subprocess.Popen(command, cwd=Path(__file__).parent, env=self.worker_env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                deadline = time.monotonic() + settings["job_timeout"]
                while process.poll() is None:
                    if self.stopping.wait(.3) or self.store.get(identifier)["status"] == "cancelled":
                        process.terminate()
                        process.wait(timeout=10)
                        self.store.finish(identifier, "interrupted", "服务停止，任务已中断，可手动重试。")
                        break
                    if time.monotonic() > deadline:
                        process.kill()
                        process.wait(timeout=10)
                        self.store.finish(identifier, "failed", "生成超时，已停止本次任务。请缩短需求后重试。")
                        break
                if self.store.get(identifier)["status"] == "running":
                    self.store.finish(identifier, "failed", "任务执行进程提前结束，请检查模型服务及 CrewAI 安装。")
            except Exception:
                if process and process.poll() is None:
                    process.kill()
                    process.wait(timeout=10)
                self.store.finish(identifier, "failed", "无法启动生成任务，请检查模型配置和执行环境。")

    def close(self):
        self.stopping.set()
        self.thread.join(timeout=15)
