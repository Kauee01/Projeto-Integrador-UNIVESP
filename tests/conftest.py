import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # faz pytest achar app.py
from sqlalchemy.orm import sessionmaker, scoped_session


import pytest
from app import app as flask_app

@pytest.fixture
def client():
    return flask_app.test_client()

# -------------------------
# AMBIENTE ISOLADO P/ MODELS
# -------------------------
from flask import Flask
from sqlalchemy import event, exc as sa_exc
from sqlalchemy.engine import Engine

# ativa FK no SQLite
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    try:
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON;")
        cur.close()
    except Exception:
        pass

@pytest.fixture(scope="session")
def models_app():
    """
    App só para testes de MODELS: SQLite em memória,
    não usa nem toca seu database.db real.
    """
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # importa db e modelos do seu projeto
    from models import db  # mesmo db do seu models.py

    with app.app_context():
        db.init_app(app)
        db.create_all()
    return app

@pytest.fixture(scope="session")
def _db(models_app):
    from models import db
    return db

@pytest.fixture
def session(models_app, _db):
    with models_app.app_context():
        connection = _db.engine.connect()
        trans = connection.begin()

        SessionFactory = sessionmaker(bind=connection, autoflush=False, expire_on_commit=False)
        sess = scoped_session(SessionFactory)

        old_session = _db.session
        _db.session = sess
        try:
            yield sess
        finally:
            # 1) tenta reverter a transação da sessão (se existir)
            try:
                sess.rollback()
            except Exception:
                pass

            # 2) apenas faz rollback do "trans" se ele estiver ativo
            try:
                if trans.is_active:
                    trans.rollback()
            except sa_exc.InvalidRequestError:
                pass

            # 3) desmonta sessão e fecha conexão
            sess.remove()
            connection.close()
            _db.session = old_session