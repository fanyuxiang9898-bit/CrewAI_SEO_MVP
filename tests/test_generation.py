import json
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from generation import JobStore, JobManager, load_settings
from web_server import handler_for

HERE = Path(__file__).parent
BRIEF = {'keyword': '阅读习惯', 'topic': '其他', 'notes': '面向初学者'}


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='job-test-', dir=HERE)
        self.path = Path(self.temp.name)
        self.store = JobStore(self.path/'jobs.db')
        self.settings = self.path/'settings.json'
        self.settings.write_text(json.dumps({'endpoint':'http://127.0.0.1:8088/v1/chat/completions','model':'test'}))
        self.manager = None

    def tearDown(self):
        if self.manager:
            self.manager.close()
        self.temp.cleanup()

    def wait_for(self, identifier, predicate):
        until = time.monotonic()+12
        while time.monotonic()<until:
            job = self.store.get(identifier)
            if predicate(job):
                return job
            time.sleep(.05)
        self.fail('Task did not reach expected state')

    def start_worker(self):
        self.manager = JobManager(self.store, self.settings, self.path/'unused.db', sys.executable,
                                  worker_script=HERE/'fake_generation_worker.py')

    def test_duplicate_submissions_are_idempotent_and_conflicting_reuse_rejected(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            jobs = list(pool.map(lambda _:self.store.create(BRIEF, 'same-request-key-1234'), range(4)))
        self.assertEqual(len({j['id'] for j in jobs}),1)
        with self.assertRaises(ValueError):
            self.store.create({**BRIEF,'keyword':'different'},'same-request-key-1234')

    def test_actual_subprocess_completes_and_result_survives_reload(self):
        self.start_worker()
        job = self.store.create(BRIEF, 'complete-request-1234')
        done = self.wait_for(job['id'], lambda j:j['status']=='completed')
        self.assertEqual(done['completed_stages'],3)
        self.assertIn('测试文章',JobStore(self.store.path).get(job['id'])['outputs']['writing'])

    def test_process_failure_retains_partial_results(self):
        self.start_worker()
        job = self.store.create({**BRIEF,'keyword':'fail'}, 'failure-request-1234')
        failed = self.wait_for(job['id'], lambda j:j['status']=='failed')
        self.assertEqual(failed['completed_stages'],1)

    def test_cancellation_prevents_late_success(self):
        self.start_worker()
        job = self.store.create({**BRIEF,'keyword':'cancel'},'cancel-request-1234')
        self.wait_for(job['id'],lambda j:j['stage']=='writing')
        self.store.finish(job['id'],'cancelled')
        self.manager.close()
        self.manager = None
        self.assertEqual(self.store.get(job['id'])['status'],'cancelled')
        with self.assertRaises(RuntimeError):
            self.store.stage(job['id'],'writing','late output')

    def test_restart_marks_unfinished_jobs_without_replaying(self):
        job = self.store.create(BRIEF,'recovery-request-1234')
        self.store.claim()
        self.store.stage(job['id'],'research','saved research')
        self.store.recover()
        restored = self.store.get(job['id'])
        self.assertEqual(restored['status'],'interrupted')
        self.assertEqual(restored['outputs']['research'],'saved research')
        self.assertIsNone(self.store.claim())

    def test_completion_requires_all_three_outputs(self):
        job = self.store.create(BRIEF,'empty-result-request')
        self.store.claim()
        with self.assertRaises(ValueError):
            self.store.finish(job['id'],'completed')

    def test_paid_or_unencrypted_remote_model_requires_explicit_configuration(self):
        self.settings.write_text(json.dumps({'endpoint':'https://example.com/chat','model':'test'}))
        with self.assertRaises(ValueError):
            load_settings(self.settings)

    def test_http_creation_csrf_origin_and_input_validation(self):
        store = self.store
        class AvailableManager:
            def __init__(self): self.store=store
            def availability(self): return {'available':True,'local_model':True,'model':'test'}
        server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(self.path/'unused.db',AvailableManager()))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        try:
            with urlopen(base+'/api/status') as response:token=json.load(response)['csrf_token']
            def post(payload,token=token,origin=base):
                return urlopen(Request(base+'/api/jobs',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','X-Workbench-Token':token,'Origin':origin,'Idempotency-Key':'api-request-key-12345'}))
            for options in [{'token':'bad'},{'origin':'https://untrusted.example'}]:
                with self.assertRaises(HTTPError) as error:post(BRIEF,**options)
                self.assertEqual(error.exception.code,403)
            with self.assertRaises(HTTPError) as error:post({**BRIEF,'keyword':' '})
            self.assertEqual(error.exception.code,400)
            with post(BRIEF) as response:
                self.assertEqual(response.status,202)
                job=json.load(response)['job']
            with post(BRIEF) as response:self.assertEqual(json.load(response)['job']['id'],job['id'])
        finally:
            server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main()
