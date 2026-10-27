"""Isolated fixture: intentionally never imported by the production worker."""
import argparse
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from generation import JobStore

parser = argparse.ArgumentParser()
for name in ['jobs', 'settings', 'database', 'job']:
    parser.add_argument('--'+name)
args = parser.parse_args()
store = JobStore(args.jobs)
keyword = store.get(args.job)['brief']['keyword']
store.stage(args.job, 'research', '测试研究报告')
store.stage(args.job, 'writing')
if keyword == 'cancel':
    time.sleep(60)
if keyword == 'fail':
    raise SystemExit(1)
store.stage(args.job, 'writing', '# 测试文章\n这是确定性的测试正文，不是 AI 结果。')
store.stage(args.job, 'review', '测试评批建议')
store.finish(args.job, 'completed')
