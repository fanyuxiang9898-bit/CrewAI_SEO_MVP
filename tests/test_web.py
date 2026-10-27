"""Read-only API contract, missing-data recovery and static-file boundary tests."""
import json
import base64
import os
import sqlite3
import tempfile
import threading
import unittest
from contextlib import closing
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from web_server import handler_for, worker_environment


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='workbench-test-', dir=Path(__file__).parent)
        self.db = Path(self.temp.name) / 'test.db'
        with closing(sqlite3.connect(self.db)) as conn:
            conn.executescript('CREATE TABLE articles(id INTEGER PRIMARY KEY,title TEXT,content TEXT,keyword TEXT,topic_theme TEXT,mock_ctr REAL,created_at TEXT); CREATE TABLE iteration_logs(id INTEGER PRIMARY KEY,article_id INTEGER,round_number INTEGER,previous_ctr REAL,reflection TEXT,suggestions TEXT,created_at TEXT);')
            conn.execute('INSERT INTO articles VALUES(1,?,?,?,?,?,?)', ('测试文章','<script>alert(1)</script>','测试','技术',.25,'2026-10-27'))
            conn.execute("INSERT INTO iteration_logs VALUES(1,1,1,.2,'反思','建议','2026-10-27')")
            conn.commit()
        self.before = self.db.read_bytes()
        self.server = ThreadingHTTPServer(('127.0.0.1',0), handler_for(self.db))
        self.thread = threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def read(self,path):
        with urlopen(self.base+path) as r:
            return json.load(r)

    def test_list_detail_and_database_unchanged(self):
        result=self.read('/api/articles')
        self.assertEqual(result['metric_type'],'simulated')
        self.assertEqual(result['articles'][0]['iterations'],1)
        self.assertNotIn('content',result['articles'][0])
        self.assertEqual(len(self.read('/api/articles/1')['logs']),1)
        self.assertEqual(self.db.read_bytes(),self.before)

    def test_unknown_and_private_files_not_served(self):
        for path in ['/env','/.env','/config.py','/data/seo_content.db','/../config.py','/api/articles/0','/api/articles/1%20OR%201=1']:
            with self.subTest(path=path),self.assertRaises(HTTPError) as error:
                urlopen(self.base+path)
            self.assertEqual(error.exception.code,404)

    def test_missing_database_has_recoverable_error(self):
        self.db.unlink()
        with self.assertRaises(HTTPError) as error:
            urlopen(self.base+'/api/articles')
        self.assertEqual(error.exception.code,503)
        self.assertIn('--database',json.load(error.exception)['error'])
        self.assertFalse(self.db.exists())

    def test_static_page_has_security_headers(self):
        with urlopen(self.base+'/') as response:
            self.assertIn("default-src 'self'",response.headers['Content-Security-Policy'])
            self.assertIn('Content Studio',response.read().decode())

    def test_untrusted_host_cannot_read_local_database(self):
        request = Request(self.base+'/api/articles',headers={'Host':'untrusted.example'})
        with self.assertRaises(HTTPError) as error:
            urlopen(request)
        self.assertEqual(error.exception.code,403)

    def test_telemetry_settings_are_child_only(self):
        before = dict(os.environ)
        child = worker_environment()
        self.assertEqual(child['CREWAI_TELEMETRY_OPT_OUT'], 'true')
        self.assertEqual(child['OTEL_SDK_DISABLED'], 'true')
        self.assertEqual(child['CREWAI_TRACING_ENABLED'], 'false')
        self.assertEqual(dict(os.environ), before)
        self.assertIsNot(child, os.environ)

    def test_public_origin_requires_authentication_for_page_and_api(self):
        self.server.RequestHandlerClass = handler_for(self.db, public_origin='https://studio.example', access_token='a-test-password-of-24-characters')
        for path in ['/', '/api/status', '/api/articles']:
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(self.base+path, headers={'Host':'studio.example'}))
            self.assertEqual(error.exception.code, 401)
        encoded = base64.b64encode(b'user:a-test-password-of-24-characters').decode()
        with urlopen(Request(self.base+'/api/articles', headers={'Host':'studio.example','Authorization':'Basic '+encoded})) as response:
            self.assertEqual(response.status, 200)


if __name__=='__main__':
    unittest.main()
