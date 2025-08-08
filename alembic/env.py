"""Alembic migration environment."""  # ← keeps linters quiet

from logging.config import fileConfig
import os
import sys
from sqlalchemy import engine_from_config, pool
from alembic import context

# -------------------------------------------------------------------
# Make sure '/code' (the Docker WORKDIR) is on the import path
# -------------------------------------------------------------------
sys.path.append("/code")

from app.db import Base                             # noqa: E402
from app import models                              # noqa: F401,E402

# -------------------------------------------------------------------
# Alembic config & logging
# -------------------------------------------------------------------
config = context.config
fileConfig(config.config_file_name)

# -------------------------------------------------------------------
# Helper: pick a synchronous DB URL for Alembic
# -------------------------------------------------------------------
def _sync_url() -> str:
    """Return a sync SQLAlchemy URL, derived from env or ini."""
    url = os.getenv("DB_URL") or config.get_main_option("sqlalchemy.url")

    # If the app URL uses asyncpg, swap to sync psycopg driver for Alembic.
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url


# -------------------------------------------------------------------
# Offline mode (sql script generation)
# -------------------------------------------------------------------
def run_migrations_offline() -> None:
    url = _sync_url()
    context.configure(
        url=url,
        target_metadata=Base.metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# -------------------------------------------------------------------
# Online mode (apply directly to DB)
# -------------------------------------------------------------------
def run_migrations_online() -> None:
    connectable = engine_from_config(
        {"sqlalchemy.url": _sync_url()},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()


# -------------------------------------------------------------------
# Entrypoint
# -------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
