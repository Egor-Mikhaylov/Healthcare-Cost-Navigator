from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.db import Base
from app import models  # noqa: F401

config = context.config
fileConfig(config.config_file_name)

def run_migrations_offline():
    url = os.environ.get("DB_URL")
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    url = os.environ.get("DB_URL")
    connectable = engine_from_config({"sqlalchemy.url": url}, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
