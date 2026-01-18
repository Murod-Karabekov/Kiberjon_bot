import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from bot.config import BOT_TOKEN
from bot.database.database import Database
from bot.handlers import start, groups, admin, broadcast, coins

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to run the bot"""
    # Initialize database
    db = Database()
    
    # Wait for database to be ready and create tables
    max_retries = 30
    for i in range(max_retries):
        try:
            await db.create_tables()
            logger.info("Database tables created successfully")
            break
        except Exception as e:
            if i < max_retries - 1:
                logger.warning(f"Database not ready, retrying in 2 seconds... ({i+1}/{max_retries})")
                await asyncio.sleep(2)
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts: {e}")
                raise

    # Initialize bot and dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Register routers
    dp.include_router(start.router)
    dp.include_router(groups.router)
    dp.include_router(admin.router)
    dp.include_router(broadcast.router)
    dp.include_router(coins.router)

    # Inject database into handlers
    dp["db"] = db

    try:
        logger.info("Bot started successfully!")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}")
