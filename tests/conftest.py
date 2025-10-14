import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # faz pytest achar app.py

import pytest
from app import app as flask_app

@pytest.fixture
def client():
    return flask_app.test_client()