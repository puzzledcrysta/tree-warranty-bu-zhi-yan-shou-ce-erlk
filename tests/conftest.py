import csv
from io import StringIO
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app import settings
from app.main import app

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture
def source():
    return (ROOT/'sample_data/shift.csv').read_bytes()

@pytest.fixture
def book():
    return (ROOT/'sample_data/external.csv').read_bytes()

@pytest.fixture
def cases():
    with (ROOT/'sample_data/cases.csv').open(encoding='utf-8',newline='') as stream:
        return {row['case']: {key: value for key, value in row.items() if key not in {'case', 'expected', 'evidence'}}
                for row in csv.DictReader(stream)}

@pytest.fixture
def client(monkeypatch,tmp_path):
    monkeypatch.setattr(settings,'DB',tmp_path/'runs.sqlite3')
    with TestClient(app) as client:
        yield client

@pytest.fixture
def sample_csv(source):
    def build(modify, legacy=False):
        reader = csv.reader(StringIO(source.decode('utf-8-sig')))
        header, row = next(reader), next(reader)
        for field,value in modify.items():
            row[header.index(field)] = value
        if legacy:
            header[:3] = ['业务编号','版本','更新时刻']
        out = StringIO(newline='')
        csv.writer(out).writerows((header,row))
        return out.getvalue().encode()
    return build
