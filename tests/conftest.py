import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("SECRET_KEY", "test-secret")

from app import app as flask_app  # noqa: E402
from connection import get_connection  # noqa: E402


@pytest.fixture()
def client():
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as c:
        yield c


def token(client, path="/login"):
    html = client.get(path).get_data(as_text=True)
    m = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert m, f"sin token CSRF en {path}"
    return m.group(1)


@pytest.fixture()
def db():
    conn = get_connection()
    yield conn
    conn.close()
