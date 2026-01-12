import aiosqlite
import re
import logging
from datetime import datetime, timedelta
from aiogram import Router
from app.data_shops import shops

router_database = Router()

# Настройка логирования
#logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Путь к БД (можно изменить, например, на 'data/bot_data.db')
DB_PATH = 'bot_data.db'


def normalize(s: str) -> str:
    if s is None:
        return ""
    s = re.sub(r'[^0-9A-Za-zА-Яа-я]', '', s)
    return s.lower()


async def register_normalize_function(db: aiosqlite.Connection):
    await db.create_function("normalize", 1, normalize)


async def search_data(phrase: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await register_normalize_function(db)

        normalized = normalize(phrase)
        like = f"%{normalized}%"

        query = """
        SELECT id, date, workers, work_description, work_solution, fault_status,
               start_time, end_time, duration, shift, machine, inventory_number
        FROM tasks
        WHERE normalize(date)             LIKE ?
           OR normalize(workers)          LIKE ?
           OR normalize(work_description) LIKE ?
           OR normalize(work_solution)    LIKE ?
           OR normalize(fault_status)     LIKE ?
           OR normalize(machine)          LIKE ?
           OR normalize(inventory_number) LIKE ?
           OR normalize(shift)            LIKE ?
        ORDER BY id DESC
        """

        params = (like, like, like, like, like, like, like, like)

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]




async def init_db():
    """Инициализация базы данных и создание таблицы tasks со всеми колонками."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Создание таблицы со всеми колонками
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                workers TEXT NOT NULL,
                machine TEXT NOT NULL,
                shift TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                work_description TEXT,
                work_solution TEXT,
                fault_status TEXT,
                duration TEXT,
                inventory_number TEXT
            )
        ''')
        await db.commit()
    logger.info("База данных инициализирована.")


async def add_data(
    user_id: int,
    date: str,
    workers: str,
    work_description: str,
    work_solution: str,
    fault_status: str,
    start_time: str,
    end_time: str,
    duration: str,
    shift: str,
    machine: str,
    inventory_number: str = None
):
    """Добавление новой задачи в БД с расширенными полями."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO tasks (
                user_id, date, workers, work_description, work_solution, fault_status,
                start_time, end_time, duration, shift, machine, inventory_number
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, date, workers, work_description, work_solution, fault_status,
            start_time, end_time, duration, shift, machine, inventory_number
        ))
        await db.commit()
    logger.info(f"Задача добавлена для пользователя {user_id}.")

# async def get_today_history():
#     """Получение истории задач за последние 24 часа для всех пользователей и форматирование в строку сообщений."""
#     since = datetime.now() - timedelta(hours=24)
#     since_str = since.strftime('%Y-%m-%d %H:%M:%S')
    
#     async with aiosqlite.connect(DB_PATH) as db:
#         cursor = await db.execute('''
#             SELECT id, date, workers, work_description, work_solution, fault_status, start_time, end_time, duration, shift, machine, inventory_number
#             FROM tasks
#             WHERE end_time >= ?
#             ORDER BY date DESC
#         ''', (since_str,))
#         rows = await cursor.fetchall()
    
#     if not rows:
#         return "За последние 24 часа записей не найдено."
    
#     # Список для хранения отформатированных сообщений
#     messages = []
#     for row in rows:
#         # Распаковка данных из row (порядок как в SELECT)
#         id_, date, workers, work_description, work_solution, fault_status, start_time, end_time, duration, shift, machine, inventory_number = row

#         # Форматирование сообщения для одной записи
#         result_message = (
#         f"📅 <b>Дата:</b> {date}\n"
#         f"📌 <b>Исполнители работ:</b> {workers}\n"
#         f"📝 <b>Описание проблемы:</b> {work_description}\n"
#         f"📝 <b>Решение:</b> {work_solution}\n"
#         f"📝 <b>Статус неисправности:</b> {fault_status}\n"
#         f"📅 <b>Дата начала:</b> {start_time}\n"
#         f"📅 <b>Дата окончания:</b> {end_time}\n"
#         f"⏳ <b>Затраченное время:</b> {duration}\n"
#         f"🏭 <b>Цех:</b> {shift}\n"
#         f"🔧 <b>Станок:</b> {machine}\n"
#         f"🔢 <b>Инвентарный номер:</b> {inventory_number}\n"
#     )
#         messages.append(result_message)
    
#     # Соединение сообщений с разделителем
#     separator = "\n---------------------------------------------\n"
#     return separator.join(messages)

async def get_today_history():
    """Получение истории задач за последние 24 часа и форматирование в строку."""

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            SELECT id, date, workers, work_description, work_solution, fault_status, start_time, end_time, duration, shift, machine, inventory_number
            FROM tasks
            WHERE datetime(substr(end_time, 7, 4) || '-' || substr(end_time, 4, 2) || '-' || substr(end_time, 1, 2) || ' ' || substr(end_time, 12, 5)) 
                  >= datetime('now', '-1 day')
            ORDER BY date DESC
        ''')
        rows = await cursor.fetchall()
    
    if not rows:
        return "За последние 24 часа записей не найдено."

    messages = []
    for row in rows:
        id_, date, workers, work_description, work_solution, fault_status, start_time, end_time, duration, shift, machine, inventory_number = row

        result_message = (
            f"📅 <b>Дата:</b> {date}\n"
            f"📌 <b>Исполнители работ:</b> {workers}\n"
            f"📝 <b>Описание проблемы:</b> {work_description}\n"
            f"📝 <b>Решение:</b> {work_solution}\n"
            f"📝 <b>Статус неисправности:</b> {fault_status}\n"
            f"📅 <b>Дата начала:</b> {start_time}\n"
            f"📅 <b>Дата окончания:</b> {end_time}\n"
            f"⏳ <b>Затраченное время:</b> {duration}\n"
            f"🏭 <b>Цех:</b> {shift}\n"
            f"🔧 <b>Станок:</b> {machine}\n"
            f"🔢 <b>Инвентарный номер:</b> {inventory_number}\n"
        )
        messages.append(result_message)

    separator = "\n---------------------------------------------\n"
    return separator.join(messages)




