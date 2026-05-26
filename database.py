import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///financas.db"
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        _migrar_colunas(engine)
    except Exception as e:
        raise RuntimeError(f"Erro ao inicializar banco de dados: {e}") from e


def _migrar_colunas(engine):
    from sqlalchemy import text
    migrations = [
        "ALTER TABLE transacoes ADD COLUMN forma_pagamento VARCHAR(20)",
        "ALTER TABLE transacoes ADD COLUMN cartao_credito_id VARCHAR(36)",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                conn.rollback()


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
