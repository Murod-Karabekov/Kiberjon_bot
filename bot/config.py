import os
from dotenv import load_dotenv

load_dotenv()

# Bot settings
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Database settings
POSTGRES_USER = os.getenv("POSTGRES_USER", "botuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "botpassword")
POSTGRES_DB = os.getenv("POSTGRES_DB", "telegram_bot")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
