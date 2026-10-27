"""Content workbench with isolated, persistent AI generation tasks."""
import argparse
import base64
import json
import os
import secrets
import sqlite3
import sys
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from generation import JobManager, JobStore, validate_brief

ROOT = Path(__file__).resolve().parent
ASSETS = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"),
          "/styles.css": ("styles.css", "text/css"), "/jobs.js": ("jobs.js", "text/javascript"),
          "/jobs.css": ("jobs.css", "text/css")}


def worker_environment():
    """Return an isolated child environment without changing this process."""
    return dict(os.environ, CREWAI_TELEMETRY_OPT_OUT='true', OTEL_SDK_DISABLED='true', CREWAI_TRACING_ENABLED='false')


def handler_for(database, manager=None, public_origin=None, access_token=None):
    csrf_token = secrets.token_urlsafe(32)
    origin = urlsplit(public_origin) if public_origin else None
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(15)

        def allowed(self, api=True):
            host = self.headers.get("Host", "")
            if host.split(":")[0] not in {"127.0.0.1", "localhost"} and (not origin or host != origin.netloc):
                self.respond(403, {"error": "访问地址未被允许"})
                return False
            if access_token and api:
                try:
                    scheme, encoded = self.headers.get('Authorization', '').split(' ', 1)
                    password = base64.b64decode(encoded, validate=True).decode().split(':', 1)[1]
                    valid = scheme.lower() == 'basic' and secrets.compare_digest(password, access_token)
                except (ValueError, UnicodeError, IndexError, TypeError):
                    valid = False
                if not valid:
                    self.send_response(401)
                    self.send_header('WWW-Authenticate', 'Basic realm="Content Studio", charset="UTF-8"')
                    self.send_header('Content-Length', '0')
                    self.end_headers()
                    return False
            return True

        def respond(self, status, value, content_type="application/json"):
            body = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = urlsplit(self.path).path
            if not self.allowed():
                return
            if path in ASSETS:
                filename, mime = ASSETS[path]
                return self.respond(200, (ROOT / "web" / filename).read_bytes(), mime)
            if path == '/api/status':
                availability = manager.availability() if manager else {"available": False, "message": "任务执行尚未启用。"}
                return self.respond(200, {"generation": availability, "csrf_token": csrf_token})
            if path == '/api/jobs':
                return self.respond(200, {"jobs": manager.store.list() if manager else []})
            if path.startswith('/api/jobs/'):
                job = manager.store.get(path.removeprefix('/api/jobs/')) if manager else None
                return self.respond(200, {"job": job}) if job else self.respond(404, {"error": "任务不存在"})
            if path != "/api/articles" and not path.startswith("/api/articles/"):
                return self.respond(404, {"error": "页面不存在"})
            if not database.is_file():
                return self.respond(503, {"error": "未找到文章数据库。请通过 --database 指定已有的 seo_content.db。"})
            try:
                with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as conn:
                    conn.row_factory = sqlite3.Row
                    if path == "/api/articles":
                        articles = conn.execute("SELECT id,title,keyword,topic_theme,mock_ctr,created_at,length(content) AS word_count, (SELECT count(*) FROM iteration_logs WHERE article_id=articles.id) AS iterations FROM articles ORDER BY id DESC").fetchall()
                        return self.respond(200, {"articles": [dict(a) for a in articles], "metric_type": "simulated"})
                    identifier = path.removeprefix("/api/articles/")
                    if not identifier.isdecimal() or len(identifier) > 12:
                        return self.respond(404, {"error": "文章不存在"})
                    article = conn.execute("SELECT * FROM articles WHERE id=?", (int(identifier),)).fetchone()
                    if not article:
                        return self.respond(404, {"error": "文章不存在"})
                    logs = conn.execute("SELECT round_number,previous_ctr,reflection,suggestions,created_at FROM iteration_logs WHERE article_id=? ORDER BY round_number DESC,id DESC", (int(identifier),)).fetchall()
                    return self.respond(200, {"article": dict(article), "logs": [dict(r) for r in logs]})
            except sqlite3.Error:
                self.respond(503, {"error": "暂时无法读取数据库，请确认文件包含 articles 和 iteration_logs 表后重试。"})

        def do_POST(self):
            if not self.allowed():
                return
            host = self.headers.get('Host', '')
            expected_origin = public_origin or 'http://' + host
            supplied_origin = self.headers.get('Origin')
            if supplied_origin and supplied_origin != expected_origin:
                return self.respond(403, {"error": "请从当前工作台提交任务"})
            if not secrets.compare_digest(self.headers.get('X-Workbench-Token', ''), csrf_token):
                return self.respond(403, {"error": "页面已过期，请刷新后重试"})
            if not manager:
                return self.respond(503, {"error": "任务执行尚未启用"})
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 12000 or self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                    return self.respond(400, {"error": "请求格式无效或内容过长"})
                payload = json.loads(self.rfile.read(size))
                path = urlsplit(self.path).path
                if path == '/api/jobs':
                    if not manager.availability()['available']:
                        return self.respond(503, {"error": "生成服务不可用，请检查模型配置。"})
                    job = manager.store.create(validate_brief(payload), self.headers.get('Idempotency-Key'))
                    return self.respond(202, {"job": job})
                if path.startswith('/api/jobs/') and path.endswith('/cancel'):
                    identifier = path[len('/api/jobs/'):-len('/cancel')]
                    if not manager.store.get(identifier):
                        return self.respond(404, {"error": "任务不存在"})
                    return self.respond(200, {"job": manager.store.finish(identifier, 'cancelled')})
                return self.respond(404, {"error": "操作不存在"})
            except (ValueError, TypeError):
                return self.respond(400, {"error": "请检查关键词、主题和创作要求；任务队列最多容纳5项。"})
            except sqlite3.Error:
                return self.respond(503, {"error": "暂时无法保存任务，请稍后重试。"})

    return Handler


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--database", type=Path, default=ROOT / "data" / "seo_content.db")
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--generation-config', type=Path)
    parser.add_argument('--worker-python', type=Path, default=Path(sys.executable))
    parser.add_argument('--jobs-database', type=Path, default=ROOT / 'data' / 'workbench-jobs.sqlite3')
    parser.add_argument('--public-origin')
    parser.add_argument('--access-token-file', type=Path)
    args = parser.parse_args()
    if args.host not in {'127.0.0.1', 'localhost'} and (not args.public_origin or not args.public_origin.startswith('https://') or not args.access_token_file):
        parser.error('公网监听必须提供 HTTPS public-origin 与 access-token-file。')
    token = args.access_token_file.read_text(encoding='utf-8').strip() if args.access_token_file else None
    if token is not None and len(token) < 24:
        parser.error('访问密码至少24个字符。')
    # Bind before recovering jobs: a second server must not interrupt a live worker.
    server = ThreadingHTTPServer((args.host, args.port), handler_for(args.database))
    worker_env = worker_environment()
    manager = JobManager(JobStore(args.jobs_database), args.generation_config, args.database, args.worker_python, worker_env=worker_env) if args.generation_config else None
    server.RequestHandlerClass = handler_for(args.database, manager, args.public_origin, token)
    print(f"Content workbench: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if manager:
            manager.close()
        server.server_close()
