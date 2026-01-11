import asyncio
import logging
from aiogram import Router, Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from app.keyboards import create_keyboard
from aiogram.filters.callback_data import CallbackData
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, get_user_locale
from aiogram.exceptions import TelegramBadRequest
from app.states import Register
from app.timing import start_cmd
from app.data_shops import *
from typing import List, Callable, Awaitable
import logging
from functools import wraps
import shutil
import os
from dotenv import load_dotenv
import json
import app.keyboards as kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from datetime import datetime, timedelta
from app.database import init_db, add_data, get_today_history 

load_dotenv('token.env')  # Загружаем переменные окружения из .env файла

PHOTO_SECRET = os.getenv('PHOTO_URL')
HELP = os.getenv('HELP')
MD = os.getenv('PARAMETERS_MD')
PLC_ALARM = os.getenv('PLC_ALARM_840D')
H_COMMAND = os.getenv('H_COMMAND')

router = Router()
logger = logging.getLogger(__name__)

# Путь к файлу БД SQLite (замена Google Sheets)
DB_FILE = 'bot_data.db'

# Путь к файлу, где будут храниться данные (JSON для пользователей и станков остаётся)
FILE_PATH = 'json/machines_data.json'
FILE_PATH_ACCESS = 'json/access_user.json'

# Функция проверки правильности введенного ID
def validate_user_id(user_id: str) -> tuple[bool, str]:
    """Валидирует ID пользователя и возвращает (валидно ли, сообщение)."""
    user_id = user_id.strip()
    if not user_id:
        return False, "Поле не может быть пустым. Пожалуйста, введите корректное название."
    if not user_id.isdigit():
        return False, "ID пользователя может состоять только из цифр. Пожалуйста, введите корректное название."
    if len(user_id) < 9 or len(user_id) > 11:
        return False, "ID пользователя должен содержать от 9 до 11 цифр. Пожалуйста, введите корректный ID."
    if user_id.startswith("0"):
        return False, "ID пользователя не может начинаться с нуля. Введите корректный ID."
    return True, ""

# Функция для загрузки данных из JSON файла
def load_access_data():
    """Загружает данные пользователей из JSON-файла или создает структуру, если файл пуст/не существует."""
    try:
        with open(FILE_PATH_ACCESS, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(
            f"Файл {FILE_PATH_ACCESS} не найден или поврежден, создаем новый: {e}")
        return {
            "main_admins": [],
            "admins": [],
            "users": []
        }

# Функция для сохранения данных в JSON файл
def save_access_data(data):
    try:
        with open(FILE_PATH_ACCESS, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        logger.info("Данные о пользователях успешно сохранены.")
    except (IOError, OSError) as e:
        logger.error(f"Ошибка при записи в файл {FILE_PATH_ACCESS}: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка при сериализации данных в JSON: {e}")
    except Exception as e:
        logger.error(
            f"Произошла непредвиденная ошибка при сохранении данных: {e}")

# Функция для загрузки данных из файла
def load_machines_data():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        logger.warning(f"Файл {FILE_PATH} не найден, создаем новый.")
        return {
            "maschines_1": [],
            "maschines_2": [],
            "maschines_3": [],
            "maschines_11": [],
            "maschines_15": [],
            "maschines_17": [],
            "maschines_20": [],
            "maschines_26": [],
            "maschines_kmt": [],
        }

# Функция для сохранения данных в файл
def save_machines_data(data):
    try:
        with open(FILE_PATH, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        logger.info("Данные о станках успешно сохранены.")
    except (IOError, OSError) as e:
        logger.error(f"Ошибка при записи в файл {FILE_PATH}: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка при сериализации данных в JSON: {e}")
    except Exception as e:
        logger.error(
            f"Произошла непредвиденная ошибка при сохранении данных: {e}")

# функция определения уровня доступа
def get_user_role(user_id, data):
    if user_id in data['main_admins']:
        return "👑 Главный администратор!"
    elif user_id in data['admins']:
        return "🛠 Администратор!"
    elif user_id in data['users']:
        return "👥 Пользователь"
    return None

# Загружаем данные при старте
machines_data = load_machines_data()



# В app.timing.start_cmd добавьте в конце (после сбора данных):
# collected_data = {...}  # Соберите данные в dict
# result = await add_data(collected_data, message.from_user.id)
# await message.answer(result)  # Или лог

# В main.py добавьте init_db() перед запуском бота:
# init_db()



# обработка команды start
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(Register.main_menu)
    # keyboards = create_keyboards()
    # await state.update_data(keyboards=keyboards)
    data = load_access_data()
    user_id = message.from_user.id  # Получаем ID пользователя
    role = get_user_role(user_id, data)
    # Проверяем, какой роль у пользователя
    if role is None:
        role = """⛔ У вас нет доступа. 
➖ Большинство функций вам будет недоступно ❗
➖ Пожалуйста, свяжитесь с администратором для получения прав доступа ❗"""
    # Отправляем сообщение с ролью пользователя
    await message.answer(f"Привет, {message.from_user.full_name}!\nУровень доступа: {role}",
                         reply_markup=kb.main)
    await message.answer("Перед использованием рекомендуем прочитать описание работы бота в разделе помощь")
    logger.info(
        f"Пользователь {user_id} ({message.from_user.full_name}) запустил бота.")

# обработка команды help


@router.message(Command('check_access'))
async def get_access(message: Message):
    data = load_access_data()
    user_id = message.from_user.id  # Получаем ID пользователя
    role = get_user_role(user_id, data)
    if role is None:
        role = '⛔ У вас нет доступа'
    await message.answer(f"Ваш уровень доступа: {role}")


@router.message(Command('help'))
async def cmd_help(message: Message):
    text = """В данном боте существует 3 уровня доступа:
- 🧑‍💻 <strong>Пользователь</strong>: Имеет доступ к добавлению записей, просмотру контактов и просмотру истории.
- 🛠️ <strong>Администратор</strong>: Пользователь + доступ к меню 'Редактор' (за исключением добавления/удаления админа и данных о пользователях), просмотр файла.
- 👑 <strong>Главный администратор</strong>: Имеет доступ ко всем функциям."""

    await message.answer(text, parse_mode='HTML')
    await message.answer(f'Прочитайте [руководство]({HELP}), там ответы на большую часть ваших вопросов.',
                         disable_web_page_preview=True, parse_mode='Markdown')


@router.message(Command('secret'))
async def send_photo(message: Message):
    await message.reply_photo(photo=PHOTO_SECRET, caption="Это невозмутимый воин")


@router.message(Command('id'))
async def send_user_id(message: Message):
    user_id = message.from_user.id
    await message.reply(f'Ваш ID: {user_id}')


@router.message(Command("url"))
async def send_url(message: Message):
    data = load_access_data()
    user_id = message.from_user.id  # Получаем ID пользователя
    role = get_user_role(user_id, data)
    if role in ["👑 Главный администратор!", "🛠 Администратор!"]:
        # Логика для авторизованных пользователей
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(
                text="Перейти по ссылке", url=LIST_URL)]])
        await message.answer("Нажмите на кнопку ниже, чтобы перейти по ссылке:", reply_markup=keyboard)
    else:
        await message.answer('⛔ У вас нет доступа')


@router.message(F.text == '📜 История за сутки')
async def history(message: Message):
    data = load_access_data()
    user_id = message.from_user.id  # Получаем ID пользователя
    role = get_user_role(user_id, data)
    if role in ["👑 Главный администратор!", "🛠 Администратор!", "👥 Пользователь"]:
        temp_message = await message.answer( "⏳ Получаю историю за сутки...")
        try:
            await asyncio.sleep(1)
            today_history = await get_today_history()
            await temp_message.edit_text(today_history, parse_mode="HTML")
            logger.info(
                f"Пользователь {message.from_user.id} ({message.from_user.full_name}) запросил историю за сутки.")
        except Exception as e:
            logger.error(
                f"Ошибка при получении истории для пользователя {message.from_user.id}: {e}")
            await message.answer("❌ Произошла ошибка при получении истории. Попробуйте позже или обратитесь к администратору.")
    else:
        await message.answer('⛔ У вас нет доступа')


@router.message(F.text == '🛠️ Редактор')
async def to_edit(message: Message):
    data = load_access_data()
    user_id = message.from_user.id  # Получаем ID пользователя
    role = get_user_role(user_id, data)
    if role in ["👑 Главный администратор!", "🛠 Администратор!"]:
        await message.answer("Выберите действие (только для администраторов)", reply_markup=kb.edit_mashines)
    else:
        await message.answer('⛔ У вас нет доступа')


@router.message(F.text == '👑 Админ меню')
async def admin_menu(message: Message):
    data = load_access_data()
    user_id = message.from_user.id  # Получаем ID пользователя
    role = get_user_role(user_id, data)
    if role in ["👑 Главный администратор!"]:
        await message.answer("Выберите действие (только для администраторов)", reply_markup=kb.admin_menu)
    else:
        await message.answer('⛔ У вас нет доступа')


inline_main_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ]
)


# Callback-хендлер для возврата в главное меню (из вашего кода, с небольшим дополнением для сброса FSM)
@router.callback_query(F.data == "main_menu")
async def go_to_main_menu(callback: CallbackQuery, state: FSMContext):
    try:
        # Удаляем сообщение с PDF и кнопкой
        await callback.message.delete()
    except Exception as e:
        # Иногда сообщение может быть уже удалено, тогда просто логируем
        logger.warning(f"Не удалось удалить сообщение: {e}")

    # Сбрасываем FSM состояние, чтобы выйти из режима калькулятора
    await state.clear()

    # Отправляем главное меню
    await callback.message.answer(
        "Главное меню:",
        reply_markup=kb.main
    )

    # Заканчиваем callback
    await callback.answer()

@router.message(F.text == '💾 Резервная копия БД')
async def backup_database_handler(message: Message):
    # Сообщение о начале процесса
    progress_msg = await message.answer("⏳ Создаю резервную копию базы данных...")

    try:
        await asyncio.sleep(1)
        source_db = 'bot_data.db'

        # Проверяем существование исходной базы
        if not os.path.exists(source_db):
            await progress_msg.edit_text("❌ Ошибка: исходная база данных не найдена!")
            logger.error("Резервная копия: исходная база данных не найдена.")
            return

        # Создаем папку backup, если она не существует
        backup_dir = 'backup'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Получаем список всех файлов резервных копий
        backup_files = [
            f for f in os.listdir(backup_dir)
            if f.startswith('Копия_БД_') and f.endswith('.db')
        ]

        # Если уже есть 5 копий, удаляем самую старую
        if len(backup_files) >= 5:
            backup_files.sort(key=lambda x: os.path.getctime(os.path.join(backup_dir, x)))
            oldest_file = backup_files[0]
            os.remove(os.path.join(backup_dir, oldest_file))
            logger.info(f"Удалена старая резервная копия: {oldest_file}")

        # Создаем имя файла с временной меткой
        timestamp = datetime.now().strftime("%d.%m.%Y_%H-%M-%S")
        backup_filename = f"Копия_БД_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)

        # Копируем базу
        shutil.copy2(source_db, backup_path)

        # Получаем текущее количество копий
        current_count = len([
            f for f in os.listdir(backup_dir)
            if f.startswith('Копия_БД_') and f.endswith('.db')
        ])

        # Обновляем сообщение о прогрессе
        await progress_msg.edit_text(
            f"✅ Резервная копия успешно создана!\n"
            f"Файл: {backup_filename}\n"
            f"Всего копий: {current_count}/5"
        )

        logger.info(f"Создана резервная копия: {backup_filename} ({current_count}/5)")

    except Exception as e:
        await progress_msg.edit_text(f"❌ Ошибка при создании резервной копии: {str(e)}")
        logger.error(f"Ошибка резервного копирования: {e}")





# Глобальное хранилище для отслеживания состояния восстановления
restore_states = {}

@router.message(F.text == '🔄 Восстановить БД из копии')
async def restore_database_handler(message: Message):
    try:
        backup_dir = 'backup'
        
        if not os.path.exists(backup_dir):
            await message.answer("❌ Папка с резервными копиями не найдена!")
            return
        
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith('Копия_БД_') and f.endswith('.db')]
        backup_files.sort(key=lambda x: os.path.getctime(os.path.join(backup_dir, x)), reverse=True)
        
        if not backup_files:
            await message.answer("❌ Резервные копии не найдены!")
            return
        
        # Создаем inline клавиатуру с выбором копий
        keyboard = []
        for i, filename in enumerate(backup_files[:5], 1):
            file_time = datetime.fromtimestamp(os.path.getctime(os.path.join(backup_dir, filename))).strftime("%d.%m.%Y %H:%M")
            button_text = f"{i}. {file_time}"
            callback_data = f"select_restore_{i}"
            keyboard.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="restore_cancel")])
        
        # Сохраняем список файлов для текущего пользователя
        restore_states[message.from_user.id] = {
            'files': backup_files[:5],
            'step': 'select_backup'
        }
        
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await message.answer("📋 Выберите резервную копию для восстановления:", reply_markup=markup)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

# Обработчик выбора резервной копии
@router.callback_query(F.data.startswith('select_restore_'))
async def select_backup_handler(callback: CallbackQuery):
    try:
        user_id = callback.from_user.id
        
        if user_id not in restore_states:
            await callback.answer("❌ Сессия истекла, начните заново", show_alert=True)
            return
        
        # Получаем номер выбранной копии
        backup_index = int(callback.data.split('_')[2]) - 1
        selected_file = restore_states[user_id]['files'][backup_index]
        
        # Обновляем состояние - теперь ждем подтверждения
        restore_states[user_id].update({
            'selected_file': selected_file,
            'step': 'confirm_restore'
        })
        
        file_time = datetime.fromtimestamp(os.path.getctime(os.path.join('backup', selected_file))).strftime("%d.%m.%Y %H:%M")
        
        # Создаем клавиатуру подтверждения
        confirm_keyboard = [
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_restore")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="restore_cancel")]
        ]
        
        markup = InlineKeyboardMarkup(inline_keyboard=confirm_keyboard)
        
        await callback.message.edit_text(
            f"⚠️ ВНИМАНИЕ!\n\n"
            f"Вы собираетесь восстановить базу данных из копии:\n"
            f"📄 {selected_file}\n"
            f"📅 {file_time}\n\n"
            f"Текущие данные будут заменены. Это действие нельзя отменить!\n\n"
            f"Подтвердите восстановление:",
            reply_markup=markup
        )
        await callback.answer()
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

# Обработчик подтверждения восстановления
@router.callback_query(F.data == 'confirm_restore')
async def confirm_restore_handler(callback: CallbackQuery):
    try:
        user_id = callback.from_user.id
        
        if user_id not in restore_states or restore_states[user_id]['step'] != 'confirm_restore':
            await callback.answer("❌ Сессия истекла, начните заново", show_alert=True)
            return
        
        selected_file = restore_states[user_id]['selected_file']
        
        # Выполняем восстановление
        result = await perform_database_restore(selected_file)
        
        if result:
            await callback.message.edit_text("✅ База данных успешно восстановлена из резервной копии!")
            # Перезапуск бота может потребоваться в зависимости от архитектуры
        else:
            await callback.message.edit_text("❌ Ошибка при восстановлении базы данных!")
        
        # Очищаем состояние
        if user_id in restore_states:
            del restore_states[user_id]
            
        await callback.answer()
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

# Обработчик отмены
@router.callback_query(F.data == 'restore_cancel')
async def cancel_restore_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id in restore_states:
        del restore_states[user_id]
    
    await callback.message.edit_text("↩️ Восстановление отменено.")
    await callback.answer()

# Функция выполнения восстановления
async def perform_database_restore(backup_filename: str) -> bool:
    try:
        main_db_path = 'bot_data.db'
        backup_path = f'backup/{backup_filename}'
        
        # Проверяем существование файла резервной копии
        if not os.path.exists(backup_path):
            return False
        
        # Закрываем все соединения с БД (если используется)
        # await close_all_db_connections()  # Реализуйте эту функцию если нужно
        
        # Восстанавливаем из выбранной копии
        shutil.copy2(backup_path, main_db_path)
        
        return True
    except Exception as e:
        logger.error(f"Ошибка восстановления БД: {e}")
        return False


@router.message(F.text == '🕒 Автокопирование БД')
async def auto_backup_settings(message: Message):
    await message.answer(
        "Выберите интервал автоматического резервного копирования:",
        reply_markup=kb.auto_backup_menu
    )




@router.message(F.text == '📚 Руководства')
async def manuals(message: Message):
    data = load_access_data()
    user_id = message.from_user.id
    role = get_user_role(user_id, data)

    if role in ["👑 Главный администратор!", "🛠 Администратор!", "👥 Пользователь"]:
        text = (
            f"Выберите руководство:\n\n"
            f"📄 [Параметры MD]({MD})\n"
            f"🔧 [PLC Alarm]({PLC_ALARM})\n"
            f"⚙️ [H Command]({H_COMMAND})"
        )

        if not text:
            await message.answer("Руководства пока не добавлены.")
            return

        # Создаём inline-клавиатуру с кнопками для калькулятора и возврата в главное меню
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🧮 Калькулятор ошибок", callback_data="error_calculator")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])

        await message.answer(text, parse_mode='Markdown', disable_web_page_preview=True, reply_markup=keyboard)
    else:
        await message.answer('⛔ У вас нет доступа')


@router.callback_query(F.data == 'error_calculator')
async def start_error_calculator(callback: CallbackQuery, state: FSMContext):
    data = load_access_data()
    user_id = callback.from_user.id
    role = get_user_role(user_id, data)

    if role in ["👑 Главный администратор!", "🛠 Администратор!", "👥 Пользователь"]:
        await callback.answer()

        # Пытаемся удалить сообщение с кнопками руководств
        try:
            await callback.message.delete()
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение с руководствами: {e}")

        # Отправляем запрос на ввод ошибки
        await callback.message.answer("Введите номер ошибки:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Register.error_code)
    else:
        await callback.answer()
        await callback.message.answer('⛔ У вас нет доступа')


# Хендлер для обработки введенного номера ошибки (обновлено: возвращает полный бит, добавляет кнопку "🔙 Главное меню", не сбрасывает состояние для повторных запросов)
@router.message(Register.error_code)
async def process_error_code(message: Message, state: FSMContext):
    error_code = message.text.strip()  # Получаем введенный текст и убираем лишние пробелы

    try:
        # Загружаем JSON файл (замените 'json/alarm_840D.json' на правильный путь, если нужно)
        with open('json/alarm_840D.json', 'r', encoding='utf-8') as f:
            errors = json.load(f)

        if error_code in errors:
            # Возвращаем полный бит (весь errors[error_code], например, "DB2.DBX 0.0")
            bit = errors[error_code]
            await message.answer(f"Бит для ошибки {error_code}: {bit}\n\nВведите следующий номер ошибки или нажмите '🔙 Главное меню'.", reply_markup=inline_main_menu)
        else:
           await message.answer("❌ Ошибка не найдена. Проверьте номер и попробуйте ввести еще раз.", reply_markup=inline_main_menu)
    except FileNotFoundError:
        await message.answer("Файл с ошибками не найден.", reply_markup=inline_main_menu)
    except json.JSONDecodeError:
        await message.answer("Ошибка чтения файла с ошибками.", reply_markup=inline_main_menu)


# обработка кнопки очистить чат
@router.message(F.text == '🧹 Очистить чат')
async def cmd_clear_1(message: Message):
    await message.answer('Вы уверены?', reply_markup=kb.clear_chat)


# обработка кнопки да
@router.message(F.text == '✅ Да')
async def cmd_clear(message: Message, bot):
    try:
        # Все сообщения, начиная с текущего и до первого (message_id = 0)
        for i in range(message.message_id, 0, -1):
            await bot.delete_message(message.from_user.id, i)
    except TelegramBadRequest as ex:
        if ex.message == "Bad Request: message to delete not found":
            print("Все сообщения удалены")


@router.message((F.text == '❌ Нет') | (F.text == '↩️ Назад'))
async def cmd_clear_no(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(f"Привет, {message.from_user.full_name}!",
                         reply_markup=kb.main)


@router.message(F.text == '📝 Добавить запись')
async def add_record(message: Message, state: FSMContext):
    data = load_access_data()
    user_id = message.from_user.id  # Получаем ID пользователя
    role = get_user_role(user_id, data)
    if role in ["👑 Главный администратор!", "🛠 Администратор!", "👥 Пользователь"]:
        await state.set_state(Register.shop_selection)
        await message.answer('Выберите цех', reply_markup=kb.workshops)
    else:
        await message.answer('⛔ У вас нет доступа')


# привязка к 2 кнопке назад
@router.callback_query(F.data == 'back_2')
async def shops_back_2(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Выберите цех', reply_markup=kb.workshops)
    await state.set_state(Register.shop_selection)


@router.message(F.text == '✅ Добавить станок')
async def add_maschine_name(message: Message, state: FSMContext):
    await state.set_state(Register.awaiting_machine_name)
    await message.answer('Выберите цех', reply_markup=kb.workshops)


@router.message(F.text == '❌ Удалить станок')
async def remove_maschine_name(message: Message, state: FSMContext):
    await state.set_state(Register.delete_machine)
    await message.answer('Выберите цех', reply_markup=kb.workshops)


@router.message(F.text == '✅ Доб.пользователя')
async def add_users(message: Message, state: FSMContext):
    await state.set_state(Register.add_user)
    await message.answer("Введите ID пользователя")


@router.message(Register.add_user)
async def get_machine_name(message: Message, state: FSMContext):
    user_id = message.text.strip()  # Убираем пробелы по краям
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        await message.answer(error_msg)
        return

    # Загружаем текущие данные из JSON
    access_data = load_access_data()
    user_id_int = int(user_id)  # Преобразуем ID к числу
    # Приводим все ID к int
    # Проверяем, есть ли ID в администраторах
    existing_main_admins = set(map(int, access_data.get("main_admins", [])))
    existing_admins = set(map(int, access_data.get("admins", [])))
    existing_users = set(map(int, access_data.get("users", [])))

    if user_id_int in existing_main_admins or user_id_int in existing_admins:
        await message.answer(f"Этот пользователь уже является администратором и не требует добавления в список пользователей.")
        return
    if user_id_int in existing_users:
        await message.answer(f"Пользователь с ID {user_id} уже существует в списке пользователей.")
        return

    await message.answer(f"Вы хотите сохранить пользователя с ID: {user_id}", reply_markup=kb.confirm_edit_users)
    await state.update_data(users_id=user_id)


@router.callback_query(F.data == "confirm_yes_users")
async def confirm_yes_users(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    user_id = user_data.get('users_id')
    # Загружаем текущие данные из JSON
    access_data = load_access_data()
    # Добавляем новый ID в список пользователей
    # Приводим к int, если это необходимо
    access_data['users'].append(int(user_id))
    # Сохраняем обновленные данные обратно в файл
    save_access_data(access_data)
    logger.info(
        f"Пользователь {user_id} добавлен в список пользователей администратором {callback.from_user.id}.")
    await callback.message.edit_text(f"Пользователь с ID {user_id} успешно добавлен в список пользователей!")
    await state.clear()  # Завершение состояния после успешного добавления
    await state.set_state(Register.main_menu)
    await callback.message.answer('Возврат в начальное меню', reply_markup=kb.main)


@router.callback_query(F.data == "confirm_no_users")
async def confirm_no_users(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Вы отменили добавление пользователя")
    await callback.message.answer("Выберите действие", reply_markup=kb.edit_mashines)


@router.message(F.text == '✅ Добавить админа')
async def add_admins(message: Message, state: FSMContext):
    data = load_access_data()
    user_id = message.from_user.id  # Получаем ID пользователя
    role = get_user_role(user_id, data)
    if role in ["👑 Главный администратор!"]:
        await state.set_state(Register.add_admins)
        await message.answer("Введите ID администратора")
    else:
        await message.answer('⛔ У вас нет доступа')


@router.message(Register.add_admins)
async def add_admins_id(message: Message, state: FSMContext):
    user_id = message.text.strip()  # Убираем пробелы по краям
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        await message.answer(error_msg)
        return

    # Загружаем текущие данные из JSON
    access_data = load_access_data()
    user_id_int = int(user_id)  # Преобразуем ID к числу
    # Приводим все ID к int
    # Проверяем, есть ли ID в администраторах
    existing_main_admins = set(map(int, access_data.get("main_admins", [])))
    existing_admins = set(map(int, access_data.get("admins", [])))
    existing_users = set(map(int, access_data.get("users", [])))
    if user_id_int in existing_main_admins:
        await message.answer(f"Этот пользователь уже является главным администратором и не требует добавления в список администраторов.")
        return
    if user_id_int in existing_admins:
        await message.answer(f"Пользователь с ID {user_id} уже существует в списке администраторов.")
        return

    await message.answer(f"Вы хотите сохранить администратора с ID: {user_id}", reply_markup=kb.confirm_edit_admins)
    await state.update_data(admins_id=user_id)


@router.callback_query(F.data == "confirm_yes_admins")
async def confirm_yes_users(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    user_id = user_data.get('admins_id')
    access_data = load_access_data()
    access_data['admins'].append(int(user_id))
    if int(user_id) in access_data['users']:
        access_data['users'].remove(int(user_id))
    logger.info(
        f"Пользователь {callback.from_user.id} успешно добавил {user_id}.")
    save_access_data(access_data)
    await callback.message.edit_text(f"Пользователь с ID {user_id} успешно добавлен в список администраторов!")
    await state.clear()  # Завершение состояния после успешного добавления
    await state.set_state(Register.main_menu)
    await callback.message.answer('Возврат в начальное меню', reply_markup=kb.main)


@router.callback_query(F.data == "confirm_no_admins")
async def confirm_no_users(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Вы отменили добавление пользователя")
    await callback.message.answer("Выберите действие", reply_markup=kb.edit_mashines)


def delete_user_from_access(user_id):
    """Удаляет пользователя по ID, если он есть в списке, и обновляет JSON-файл."""
    access_data = load_access_data()
    if user_id in access_data["users"]:
        access_data["users"].remove(user_id)
        try:
            save_access_data(access_data)
            logger.info(
                f"Пользователь {user_id} удален из списка пользователей")
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления пользователя {user_id}: {e}")
            return False
    logger.warning(f"Попытка удалить несуществующего пользователя {user_id}.")
    return False


def generate_users_keyboard():
    """Создает клавиатуру с ID пользователей."""
    access_data = load_access_data()
    users = access_data.get("users", [])
    if not users:
        logger.info("Список пользователей пуст; клавиатура не создана.")
        return None  # Если список пуст, клавиатуру не создаем
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    row = []
    for user in users:
        row.append(InlineKeyboardButton(
            text=str(user), callback_data=f"deletes_{user}"))
        if len(row) == 3:  # 3 кнопки в ряд
            keyboard.inline_keyboard.append(row)
            row = []
    if row:  # Добавляем оставшиеся кнопки, если их меньше 3
        keyboard.inline_keyboard.append(row)
    return keyboard


def delete_admins_from_access(user_id):
    """Удаляет пользователя по ID, если он есть в списке, и обновляет JSON-файл."""
    access_data = load_access_data()
    if user_id in access_data["admins"]:
        access_data["admins"].remove(user_id)  # Удаляем ID
        try:
            save_access_data(access_data)  # Сохраняем обновленный файл
            logger.info(
                f"Администратор {user_id} удален из списка администраторов.")
            return True  # Успешное удаление
        except Exception as e:
            logger.error(f"Ошибка при удалении администратора {user_id}: {e}")
            return False
    logger.warning(
        f"Попытка удалить несуществующего администратора {user_id}.")
    return False


def generate_admins_keyboard():
    """Создает клавиатуру с ID пользователей."""
    access_data = load_access_data()
    admins = access_data.get("admins", [])

    if not admins:
        logger.info("Список администраторов пуст; клавиатура не создана.")
        return None  # Если список пуст, клавиатуру не создаем

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    row = []
    for admin in admins:
        row.append(InlineKeyboardButton(
            text=str(admin), callback_data=f"deletes_{admin}"))
        if len(row) == 3:  # 3 кнопки в ряд
            keyboard.inline_keyboard.append(row)
            row = []
    if row:  # Добавляем оставшиеся
        keyboard.inline_keyboard.append(row)
    return keyboard


@router.message(F.text == '❌ Удалить админа')
async def show_admins_to_delete(message: Message, state: FSMContext):
    data = load_access_data()
    user_id = message.from_user.id  # Получаем ID пользователя
    role = get_user_role(user_id, data)
    if role in ["👑 Главный администратор!"]:
        keyboard = generate_admins_keyboard()
        if keyboard:
            await message.answer("Выберите пользователя для удаления:", reply_markup=keyboard)
        else:
            await message.answer("Список пользователей пуст, удалять некого!")
    else:
        await message.answer('⛔ У вас нет доступа')


@router.callback_query(F.data.startswith("deletes_"))
async def confirm_delete_admins(callback: CallbackQuery, state: FSMContext):
    """Удаляет выбранного пользователя."""
    user_id = int(callback.data.split("_")[1])  # Получаем ID из callback_data
    await state.update_data(admins_id_access=user_id)
    await callback.message.edit_text(f'Вы уверены что хотите удалить администратора {user_id}?', reply_markup=kb.del_admins)


@router.callback_query(F.data.startswith("confirm_deletes_"))
async def confirm_delete_admins_1(callback: CallbackQuery, state: FSMContext):
    """Удаляет пользователя после подтверждения."""
    user_data = await state.get_data()
    user_id = user_data.get('admins_id_access')
    if delete_admins_from_access(user_id):
        logger.info(
            f"Пользователь {callback.from_user.id} подтвердил удаление администратора {user_id}.")
        await callback.message.edit_text(f"✅ Пользователь с ID {user_id} удален!")
    else:
        logger.warning(
            f"Пользователь {callback.from_user.id} не смог удалить администратора {user_id}.")
        await callback.message.edit_text(f"❌ Ошибка: пользователь с ID {user_id} не найден.")


@router.callback_query(F.data == "cancel_deletes_admins")
async def cancel_delete_admins(callback: CallbackQuery):
    """Отмена удаления пользователя."""
    logger.info(
        f"Пользователь {callback.from_user.id} отменил удаление администратора.")
    await callback.message.edit_text("❌ Удаление отменено.")


@router.message(F.text == '❌ Удал. пользователя')
async def show_users_to_delete(message: Message):
    """Показывает список пользователей для удаления."""
    logger.info(
        f"Пользователь {message.from_user.id} запросил просмотр списка пользователей для удаления.")
    keyboard = generate_users_keyboard()
    if keyboard:
        await message.answer("Выберите пользователя для удаления:", reply_markup=keyboard)
    else:
        await message.answer("Список пользователей пуст, удалять некого!")


@router.callback_query(F.data.startswith("delete_"))
async def confirm_delete_user(callback: CallbackQuery, state: FSMContext):
    """Удаляет выбранного пользователя."""
    user_id = int(callback.data.split("_")[1])  # Получаем ID из callback_data
    logger.info(
        f"Пользователь {callback.from_user.id} выбрал пользователя {user_id} для удаления.")
    await state.update_data(user_id_access=user_id)
    await callback.message.edit_text(f'Вы уверены что хотите удалить пользователя {user_id}?', reply_markup=kb.del_users)


@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete_user_1(callback: CallbackQuery, state: FSMContext):
    """Удаляет пользователя после подтверждения."""
    user_data = await state.get_data()
    user_id = user_data.get('user_id_access')
    if delete_user_from_access(user_id):
        logger.info(
            f"Пользователь {callback.from_user.id} подтвердил удаление пользователя {user_id}.")
        await callback.message.edit_text(f"✅ Пользователь с ID {user_id} удален!")
    else:
        logger.warning(
            f"Пользователь {callback.from_user.id} не смог удалить пользователя {user_id}.")
        await callback.message.edit_text(f"❌ Ошибка: пользователь с ID {user_id} не найден.")


@router.callback_query(F.data == "cancel_delete_users")
async def cancel_delete_users(callback: CallbackQuery):
    """Отмена удаления пользователя."""
    logger.info(
        f"Пользователь {callback.from_user.id} отменил удаление пользователя.")
    await callback.message.edit_text("❌ Удаление отменено.")


# функция формирования кнопок из файла json в зависимости от состояния
@router.callback_query(F.data.regexp(r'(.+?)-shop'))
async def shops(callback: CallbackQuery, state: FSMContext):
    # Извлекаем номер цеха из данных колбэка
    # Получаем номер или название цеха
    shop_number = callback.data.split('-')[0]
    machines_data = load_machines_data()
    machines = machines_data.get(f'maschines_{shop_number}', [])
    # Обновляем состояние пользователя
    await state.update_data(selected_shop=callback.data)
    logger.info(
        f"Пользователь {callback.from_user.id} выбрал цех {shop_number}.")
    if await state.get_state() == Register.shop_selection.state:
        # Устанавливаем состояние в зависимости от номера цеха
        await state.set_state(getattr(Register, f'machine_selection_{shop_number}'))
        # Генерируем клавиатуру с станками
        keyboard = create_keyboard(machines)
        await callback.message.edit_text('Выберите станок', reply_markup=keyboard)
    elif await state.get_state() == Register.awaiting_machine_name.state:
        await callback.message.edit_text("Введите название станка")
        await state.set_state(Register.awaiting_machine_name)
    elif await state.get_state() == Register.delete_machine.state:
        # Устанавливаем состояние в зависимости от номера цеха
        await state.set_state(getattr(Register, f'machine_selection_{shop_number}'))
        keyboard = create_keyboard(machines)
        await callback.message.edit_text('Выберите станок для удаления', reply_markup=keyboard)
        await state.set_state(Register.delete_machine_1)


# функция обработки имени станка из сообщения пользователя
@router.message(Register.awaiting_machine_name)
async def get_machine_name(message: Message, state: FSMContext):
    machine_name = message.text.strip()  # Убираем пробелы по краям

    # Проверка, что название станка не пустое
    if not machine_name:
        logger.warning(
            f"Пользователь {message.from_user.id} ввел пустое название станка.")
        await message.answer("Название станка не может быть пустым. Пожалуйста, введите корректное название.")
        return
    # Получаем данные из состояния
    user_data = await state.get_data()
    shop = user_data.get('selected_shop')
    shop_number = shop.split('-')[0]
    # Загружаем данные о станках из файла
    machines_data = load_machines_data()
    # Проверка, есть ли уже станок с таким именем в выбранном цехе
    existing_machines = machines_data.get(f'maschines_{shop_number}', [])
    if any(machine['name'].lower() == machine_name.lower() for machine in existing_machines):
        logger.warning(
            f"Пользователь {message.from_user.id} ввел дублирующее название станка '{machine_name}' в цехе {shop_number}.")
        await message.answer(f"Станок с таким названием уже существует в цехе {shop_number}. Пожалуйста, введите другое название.")
        return
    # Сохраняем имя станка в данных пользователя
    await state.update_data(machine_name=machine_name)
    # Переходим к следующему шагу для ввода инвентарного номера
    await message.answer("Введите инвентарный номер станка:")
    await state.set_state(Register.awaiting_machine_inventory)

# функция обработки инвентарного номера станка из сообщения пользователя


@router.message(Register.awaiting_machine_inventory)
async def add_machine_inventory(message: Message, state: FSMContext):
    inventory_number = message.text  # Получаем инвентарный номер из сообщения
    # Получаем данные из состояния
    user_data = await state.get_data()
    machine_name = user_data.get("machine_name")
    shop = user_data.get('selected_shop')
    shop_number = shop.split('-')[0]
    # Загружаем данные о станках из файла
    machines_data = load_machines_data()
    # Проверка, есть ли уже станок с таким инвентарным номером в выбранном цехе
    existing_machines = machines_data.get(f'maschines_{shop_number}', [])
    if any(machine['inventory_number'] == inventory_number for machine in existing_machines):
        logger.warning(
            f"Пользователь {message.from_user.id} ввел дублирующий инвентарный номер '{inventory_number}' в цехе {shop_number}.")
        await message.answer(f"Станок с таким инвентарным номером уже существует в цехе {shop_number}. Пожалуйста, введите другой номер.")
        return
    # Создаем новый объект станка
    new_machine = {"name": machine_name, "inventory_number": inventory_number}
    # Получаем выбранный цех
    shop = user_data.get('selected_shop')
    shop_number = shop.split('-')[0]
    # Сформируем сообщение для подтверждения
    confirmation_text = f"Вы хотите сохранить станок: {machine_name}, инвентарный номер: {inventory_number}?"
    # Отправляем сообщение с кнопками для подтверждения
    await message.answer(confirmation_text, reply_markup=kb.confirm_edit_mashines)
    # Сохраняем данные в состоянии, чтобы потом их использовать
    await state.update_data(new_machine=new_machine, shop_number=shop_number)


# Обработчик для кнопки "ДА" добавления станка
@router.callback_query(F.data == "confirm_yes")
async def confirm_yes(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    new_machine = user_data.get("new_machine")
    shop_number = user_data.get("shop_number")
    machines_data = load_machines_data()
    # Проверка, существует ли уже станок с таким именем или инвентарным номером
    existing_machines = machines_data.get(f'maschines_{shop_number}', [])
    if any(machine['name'].lower() == new_machine['name'].lower() or
           machine['inventory_number'] == new_machine['inventory_number']
           for machine in existing_machines):
        logger.warning(
            f"Пользователь {callback.from_user.id} подтвердил добавление дублирующего станка в цехе {shop_number}.")
        await callback.message.answer(f"Станок с таким названием или инвентарным номером уже существует в цехе {shop_number}.")
        return

    # Добавляем станок в соответствующий цех
    machines_data[f'maschines_{shop_number}'].append(new_machine)
    # Сохраняем обновленные данные в файл
    try:
        save_machines_data(machines_data)
        logger.info(
            f"Пользователь {callback.from_user.id} добавил станок '{new_machine['name']}' в цех {shop_number}.")
        # Подтверждение добавления станка
        await callback.message.edit_text(f"Станок {new_machine['name']} с инвентарным номером {new_machine['inventory_number']} добавлен!")
    except Exception as e:
        logger.error(
            f"Ошибка при добавлении станка пользователем {callback.from_user.id}: {e}")
        await callback.message.edit_text("Произошла ошибка при сохранении данных.")
        return
    await state.clear()
    await state.set_state(Register.main_menu)
    await callback.message.answer('Возврат в начальное меню', reply_markup=kb.main)


# кнопка отмены добавления станка
@router.callback_query(F.data == "confirm_no")
async def confirm_no(callback: CallbackQuery, state: FSMContext):
    logger.info(
        f"Пользователь {callback.from_user.id} отменил добавление станка.")
    await callback.message.answer("Вы отменили добавление станка")
    await callback.message.answer("Выберите действие", reply_markup=kb.edit_mashines)


# функция для работы после выбора станка в зависимости от состояния
@router.callback_query(lambda callback: any(machine['name'] in callback.data for machines in load_machines_data().values() for machine in machines))
async def reg(callback: CallbackQuery, state: FSMContext):
    await state.update_data(selected_machine=callback.data)
    if await state.get_state() == Register.delete_machine_1.state:
        user_data = await state.get_data()
        shop_number = user_data.get('selected_shop').split('-')[0]
        machine_name = user_data.get('selected_machine')  # Получаем имя станка
        machines_data = load_machines_data()
        machines = machines_data.get(f'maschines_{shop_number}', [])
        machine_to_remove = next(
            (machine for machine in machines if machine['name'] == machine_name), None)
        if machine_to_remove:
            # Показываем пользователю кнопки подтверждения
            await callback.message.edit_text(
                f"Вы уверены, что хотите удалить станок {machine_name}?",
                reply_markup=kb.del_machines)
            # Сохраняем станок для удаления в состояние
            await state.update_data(machine_to_remove=machine_to_remove)
        else:
            logger.warning(
                f"Пользователь {callback.from_user.id} выбрал несуществующий станок '{machine_name}' в цехе {shop_number}.")
            await callback.answer("Станок не найден.")
    else:
        # Сохраняем текущее состояние перед переходом к новому
        await state.update_data(previous_state=await state.get_state())
        await state.set_state(Register.date_start)
        await callback.message.edit_text(
            "Пожалуйста выберите дату начала работ: ",
            reply_markup=await SimpleCalendar(
                locale=await get_user_locale(callback.from_user)).start_calendar())


# кнопка подтверждения удаления станка
@router.callback_query(lambda callback: callback.data == "confirm_delete")
async def confirm_delete(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    machine_to_remove = user_data.get(
        'machine_to_remove')  # Получаем станок для удаления

    if machine_to_remove:
        shop_number = user_data.get('selected_shop').split(
            '-')[0]  # Получаем номер цеха
        machines_data = load_machines_data()  # Загружаем данные станков
        # Получаем список станков для выбранного цеха
        machines = machines_data.get(f'maschines_{shop_number}', [])

        machines.remove(machine_to_remove)  # Удаляем станок из списка
        try:
            save_machines_data(machines_data)  # Сохраняем обновленные данные
            logger.info(
                f"Пользователь {callback.from_user.id} удалил станок '{machine_to_remove['name']}' из цеха {shop_number}.")
            await callback.message.edit_text(f'✅ Станок {machine_to_remove["name"]} удален.', parse_mode="HTML")
        except Exception as e:
            logger.error(
                f"Ошибка при удалении станка пользователем {callback.from_user.id}: {e}")
            await callback.message.edit_text("❌ Ошибка при удалении станка.")
        await state.clear()  # Очищаем состояние
        await state.set_state(Register.main_menu)
        await callback.message.answer('Возврат в начальное меню', reply_markup=kb.main)
    else:
        logger.warning(
            f"Пользователь {callback.from_user.id} подтвердил удаление несуществующего станка.")
        await callback.message.edit_text("❌ Станок не найден для удаления.")


# кнопка отмены удаления станка
@router.callback_query(lambda callback: callback.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery, state: FSMContext):
    logger.info(
        f"Пользователь {callback.from_user.id} отменил удаление станка.")
    await callback.message.edit_text('Операция удаления станка отменена.')
    await state.clear()  # Очищаем состояние
    await callback.message.answer("Выберите действие", reply_markup=kb.edit_mashines)


# simple calendar usage - filtering callbacks of calendar format
@router.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(callback_query: CallbackQuery, callback_data: CallbackData, state: FSMContext):
    logger.info(
        f"Пользователь {callback_query.from_user.id} взаимодействует с календарем.")
    calendar = SimpleCalendar(
        locale=await get_user_locale(callback_query.from_user),
        show_alerts=True)
    calendar.set_dates_range(datetime(2022, 1, 1), datetime(
        datetime.now().year + 1, 12, 31))
    result = await calendar.process_selection(callback_query, callback_data, state)
    if result is not None:
        selected, date = result
        if date is None:
            date = datetime.now()
        if selected:
            if await state.get_state() == Register.date_start.state:
                await state.update_data(selected_date_start=date)
                user_data = await state.get_data()
                selected_date_start = user_data.get("selected_date_start")
                await callback_query.message.edit_text(f'Выбрать дату {selected_date_start.strftime("%d.%m.%Y")}?', reply_markup=kb.markup)
                await state.set_state(Register.date_end)
                logger.info(
                    f"Пользователь {callback_query.from_user.id} выбрал дату начала: {selected_date_start.strftime('%d.%m.%Y')}.")
            elif await state.get_state() == Register.confirm_dates.state:
                await state.update_data(selected_date_end=date)
                await callback_query.message.edit_text(
                    f'Вы выбрали дату завершения: {date.strftime("%d.%m.%Y")}. Подтвердите выбор?',
                    reply_markup=kb.markup)
                logger.info(
                    f"Пользователь {callback_query.from_user.id} выбрал дату окончания: {date.strftime('%d.%m.%Y')}.")


# привязка к кнопке назад
@router.callback_query(F.data == "back_to_calendar")
async def back_to_calendar(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Пользователь {callback.from_user.id} вернулся к календарю.")
    current_state = await state.get_state()
    user_data = await state.get_data()
    if current_state == Register.today_date.state or current_state == Register.date_end.state:
        await callback.message.edit_text(
            "Выберите дату начала работ: ",
            reply_markup=await SimpleCalendar(
                locale=await get_user_locale(callback.from_user)).start_calendar())
        # Возвращаемся к выбору даты начала
        await state.set_state(Register.date_start)
    elif current_state == Register.confirm_dates.state:
        await callback.message.edit_text(
            f'Вы выбрали дату начала: {user_data.get("selected_date_start").strftime("%d.%m.%Y")}. Пожалуйста, выберите дату завершения.',
            reply_markup=await SimpleCalendar(locale=await get_user_locale(callback.from_user)).start_calendar())


# привязка к кнопке подтвердить
@router.callback_query(F.data == "confirm_date")
async def confirm_date(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state == Register.date_end.state or current_state == Register.today_date.state:
        data = await state.get_data()
        await callback.message.edit_text(
            f'Вы выбрали дату начала: {data.get("selected_date_start").strftime("%d.%m.%Y")}. Пожалуйста, выберите дату завершения.',
            reply_markup=await SimpleCalendar(locale=await get_user_locale(callback.from_user)).start_calendar())
        # Устанавливаем состояние на выбор даты окончания
        await state.set_state(Register.confirm_dates)
        logger.info(
            f"Пользователь {callback.from_user.id} подтвердил дату начала и перешел к выбору даты окончания.")
    elif current_state == Register.confirm_dates.state:
        data = await state.get_data()
        if data.get("selected_date_end").date() < data.get("selected_date_start").date():
            logger.warning(
                f"Пользователь {callback.from_user.id} выбрал некорректную дату окончания (раньше начала).")
            await callback.message.edit_text(
                f'Дата завершения должна быть больше или равна дате начала. Пожалуйста, выберите другую дату (дата начала: {data.get("selected_date_start").strftime("%d.%m.%Y")}).',
                reply_markup=await SimpleCalendar(locale=await get_user_locale(callback.from_user)).start_calendar())
        else:
            # Устанавливаем состояние
            await state.set_state(Register.date_to_time)
            logger.info(
                f"Пользователь {callback.from_user.id} подтвердил даты: начало {data.get('selected_date_start').strftime('%d.%m.%Y')}, окончание {data.get('selected_date_end').strftime('%d.%m.%Y')}.")
            # ✅ Отправляем сообщение сразу, чтобы вызвать `start_cmd`
            await start_cmd(callback.message, state)



