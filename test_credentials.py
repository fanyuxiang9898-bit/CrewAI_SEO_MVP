"""Offline regression checks for environment-based credentials."""
import ast
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent


class CredentialTests(unittest.TestCase):
    def run_config(self, key):
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env.pop('OPENAI_API_KEY', None)
        if key is not None:
            env['OPENAI_API_KEY'] = key
        with tempfile.TemporaryDirectory() as work:
            env['DATABASE_PATH'] = str(Path(work) / 'data.db')
            env['CHROMA_DB_PATH'] = str(Path(work) / 'chroma')
            command = ('import runpy; c = runpy.run_path(' + repr(str(ROOT / 'config.py')) +
                       ')["Config"]; assert c.LLM_API_KEY == ' + repr(key))
            return subprocess.run([sys.executable, '-S', '-c', command], cwd=work,
                                  env=env, text=True, encoding='utf-8', capture_output=True)

    def test_environment_key_is_used_without_printing_it(self):
        key = 'regression-only-not-a-real-credential'
        result = self.run_config(key)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(key, result.stdout + result.stderr)

    def test_missing_key_fails_clearly(self):
        result = self.run_config(None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('OPENAI_API_KEY', result.stderr)

    def test_source_has_no_embedded_provider_keys(self):
        for file in list(ROOT.glob('*.py')) + [ROOT / 'env', ROOT / '.env.example']:
            source = file.read_text(encoding='utf-8')
            self.assertIsNone(re.search(r'sk-[A-Za-z0-9_-]{20,}', source), file.name)
            if file.suffix == '.py':
                ast.parse(source, filename=str(file))


if __name__ == '__main__':
    unittest.main()
