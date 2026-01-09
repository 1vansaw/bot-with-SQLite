import asyncio
from aiogram import Bot, Dispatcher
from app.handlers import router  
from app.timing import router_time
from app.get_users_id import router_users_id
from app.records import router_records
from app.contact import router_contact
from app.database import router_database
from app.logs import router_logs
from app.send_mess import router_broadcast
from app.records import cleanup_old_files
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
import os
from dotenv import load_dotenv
from aiogram.client.session.aiohttp import AiohttpSession
import logging
from logging.handlers import RotatingFileHandler
from app.database import init_db

# Загружаем переменные окружения из .env файла
load_dotenv('/home/ivansaw/bot/token.env')
BOT_TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(
    level=logging.INFO,  # Уровень: DEBUG для подробностей, INFO для основного, ERROR для ошибок
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[RotatingFileHandler('logs/bot.log', encoding='utf-8', maxBytes=5 * 1024*1024, backupCount=3), logging.StreamHandler()])

logger = logging.getLogger(__name__)

async def set_main_menu(bot: Bot):
    # Создаем список с командами и их описанием для кнопки menu
    main_menu_commands = [
        BotCommand(command='/start',
                   description='🏡 Главное меню'),
        BotCommand(command='/url',
                   description='🔗 Ссылка на файл'),
        BotCommand(command='/id',
                   description='🆔 Ваш ID'),
        BotCommand(command='/check_access',
                   description='🔒 Проверка уровня доступа'),
        BotCommand(command='/contacts',
                   description='📞 Контакты'),
        BotCommand(command='/help',
                   description='🆘 Помощь')
    ]

    await bot.set_my_commands(main_menu_commands)

storage = MemoryStorage()
session = AiohttpSession()  # proxy="http://proxy.server:3128"
bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher(storage=storage)
dp.include_router(router)
dp.include_router(router_time)
dp.include_router(router_users_id)
dp.include_router(router_contact)
dp.include_router(router_records)
dp.include_router(router_logs)
dp.include_router(router_broadcast)
dp.include_router(router_database)

# функция удаления файлов истории
async def periodic_cleanup():
    while True:
        logging.info("Запуск периодической очистки...")
        cleanup_old_files()
        await asyncio.sleep(3600)  # 60 минут проверка

async def main():
    await init_db()  # Инициализация базы данных SQLite
    dp.startup.register(set_main_menu)
    asyncio.create_task(periodic_cleanup())
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")