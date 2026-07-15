import os
from dotenv import load_dotenv
from alembic import context

load_dotenv()

config = context.config

database_url = os.getenv("DATABASE_URL")

'''
While loading the database URL from .env
the value iin alembic.ini simply acts as a placeholder
because env.py replaces it when Alembic starts.
'''
config.set_main_option("sqlalchemy.url", database_url)