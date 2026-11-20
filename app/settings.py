import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = ROOT / 'sample_data'
DB = Path(os.getenv('WORKBENCH_DB', str(ROOT/'state/ledger.sqlite3')))
TITLE = '补植验收册'
SLUG = 'tree-warranty'
KEY = '街段验收单'
FIELDS = ('验收日', '观察期天数', '单株款元', '逐株事件')
ROLE = '园林养护验收员'
UNIT = '元'
RULE_VERSION = 'tree-warranty-1.0'
SIGNATURE = '单株验收明细'
TABS = {'intake': '巡检底单', 'contract': '物候字段', 'quality': '异常巡检', 'domain': '保活核款', 'reconcile': '养护台账', 'runs': '验收批次', 'review': '签收底稿'}
