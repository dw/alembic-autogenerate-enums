import os

from sqlalchemy import create_engine


def get_url():
    user = os.environ.get("POSTGRES_USER", "alembic-autogenerate")
    password = os.environ.get("POSTGRES_PASSWORD", "")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "alembic-autogenerate_db")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"
