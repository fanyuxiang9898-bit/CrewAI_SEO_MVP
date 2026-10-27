"""Local, read-only content workbench. No CrewAI imports or environment changes."""
import argparse
import json
import sqlite3
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
ASSETS = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"),
          "/styles.css": ("styles.css", "text/css")}


def handler_for(database):
    class Handler(BaseHTTPRequestHandler):
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
            # A local dashboard must not answer requests through arbitrary DNS names.
            if self.headers.get("Host", "").split(":")[0] not in {"127.0.0.1", "localhost"}:
                return self.respond(403, {"error": "仅允许本机地址访问"})
            path = urlsplit(self.path).path
            if path in ASSETS:
                filename, mime = ASSETS[path]
                return self.respond(200, (ROOT / "web" / filename).read_bytes(), mime)
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

    return Handler


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--database", type=Path, default=ROOT / "data" / "seo_content.db")
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(args.database))
    print(f"Content workbench: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
