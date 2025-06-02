from logging.config import fileConfig
import os
import sys
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Thêm thư mục gốc của dự án (chứa thư mục 'src') vào sys.path
# __file__ là migrations/env.py
# os.path.dirname(__file__) là migrations/
# os.path.dirname(os.path.dirname(__file__)) là thư mục gốc của dự án
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)  # Để có thể import từ src.models

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from src.models.base import Base  # Import Base từ src.models.base

# Import tất cả các model của bạn để Base.metadata biết về chúng
# và Alembic có thể tự động phát hiện thay đổi.
# Đảm bảo rằng các file model này đã import Base và định nghĩa các table.
import src.models.user
import src.models.project
import src.models.task
import src.models.team
import src.models.calendar
import src.models.event

# Bảng association_tables cũng cần được import nếu chúng định nghĩa Table objects
# trực tiếp với Base.metadata
import src.models.association_tables

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    from dotenv import load_dotenv

    # Đường dẫn đến file .env ở thư mục gốc của dự án
    dotenv_path = os.path.join(project_root, ".env")
    load_dotenv(dotenv_path=dotenv_path)
    db_url = os.getenv("SQLALCHEMY_DATABASE_URL")
    if not db_url:
        raise ValueError("SQLALCHEMY_DATABASE_URL is not set in .env file for Alembic.")
    return db_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Thay thế phần cấu hình engine mặc định bằng cách lấy URL từ get_url()
    from sqlalchemy import create_engine

    connectable = create_engine(get_url())

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
