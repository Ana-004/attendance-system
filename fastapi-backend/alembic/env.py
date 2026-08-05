'''
This file reads alembic settings (alembic.ini), connects
to your database, loads your models, and performs migrations.
'''

from logging.config import fileConfig             #imports Python's logging configuration function
from sqlalchemy import engine_from_config, pool
import os
from dotenv import load_dotenv
from alembic import context                       #context is Alembic's main object 

load_dotenv()

from database import Base
from config import settings 

config = context.config                          #Gets configuration object

DATABASE_URL = os.getenv("DATABASE_URL")

'''
While loading the database URL from .env
the value in alembic.ini simply acts as a placeholder
because env.py replaces it when Alembic starts.
'''
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)          #Loads logging settings from alembic.ini

target_metadata = Base.metadata                  #Contains information about the database tables


def run_migrations_offline():                    #Generates SQL without connecting to the database
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction(): 
        context.run_migrations()                 #processes the migration within a transaction


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,                 #Temporary pooling connection
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()