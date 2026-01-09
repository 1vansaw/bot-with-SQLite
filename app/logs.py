import os
import logging
from collections import deque
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from app.handlers import get_user_role, load_access_data

# Создаём роутер для логов
router_logs = Router()

# Список ротируемых файлов (в порядке от нового к старому)
LOG_FILES = ['logs/bot.log', 'logs/bot.log.1', 'logs/bot.log.2']


@router_logs.message(F.text == '📄 Посмотреть логи')
async def view_logs_menu(message: Message):
    """
    Показывает меню для выбора файла логов.
    """
    data = load_access_data()
    user_id = message.from_user.id  # Получаем ID пользователя
    role = get_user_role(user_id, data)
    if role in ["👑 Главный администратор!", "🛠 Администратор!"]:
        try:
            # Проверяем, какие файлы существуют
            available_files = [f for f in LOG_FILES if os.path.exists(f)]
            if not available_files:
                await message.answer("Файлы логов не найдены. Проверьте настройки логирования.")
                logging.warning(
                    f"Админ {message.from_user.id} попытался просмотреть логи, но файлы отсутствуют.")
                return

            # Создаём клавиатуру с кнопками для каждого файла
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"{'Текущие' if i == 0 else f'Архив {i}'} ({os.path.basename(f)})",
                                      callback_data=f"logs:{f}")]
                for i, f in enumerate(available_files)
            ])

            await message.answer("Выберите файл логов для просмотра:", reply_markup=keyboard)
            logging.info(f"Админ {message.from_user.id} открыл меню логов.")
        except Exception as e:
            logging.error(
                f"Ошибка при показе меню логов админу {message.from_user.id}: {e}")
            await message.answer("Произошла ошибка. Попробуйте позже.")



@router_logs.callback_query(F.data.startswith("logs:"))
async def view_selected_logs(callback: CallbackQuery):
    """
    Обрабатывает выбор файла и отправляет логи.
    """
    # Проверка доступа
    data = load_access_data()
    user_id = callback.from_user.id
    role = get_user_role(user_id, data)
    if role not in ["👑 Главный администратор!", "🛠 Администратор!"]:
        await callback.answer("⛔ У вас нет доступа.", show_alert=True)
        return

    try:
        # Извлекаем путь к файлу из callback_data
        log_file = callback.data.split(":", 1)[1]
        if not os.path.exists(log_file):
            await callback.answer("❌ Файл больше не существует.", show_alert=True)
            return

        # Проверяем размер файла (только для информационного сообщения)
        file_size = os.path.getsize(log_file)
        
        # ВСЕГДА отправляем файл как документ (как в send_full_log_file)
        document = FSInputFile(
            log_file, 
            filename=f'{os.path.basename(log_file)}.txt'
        )
        
        caption = f"📋 Логи из {os.path.basename(log_file)}"
        if file_size > 1024 * 1024:  # > 1 MB
            caption += " (файл большой, рекомендуется скачать)"
        
        await callback.message.answer_document(document, caption=caption)
        logging.info(f"Админ {user_id} скачал файл логов {log_file}.")
        
        await callback.answer()  # Закрываем уведомление о нажатии
        
    except Exception as e:
        logging.error(f"Ошибка при отправке логов из {log_file} админу {user_id}: {e}")
        await callback.message.answer("⚠️ Произошла ошибка при загрузке логов. Попробуйте позже.")
        await callback.answer()





def get_last_lines(log_file: str, num_lines: int) -> str:
    """
    Эффективно читает последние num_lines строк из файла.
    """
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = deque(f, maxlen=num_lines)
        return ''.join(lines)
    except Exception as e:
        logging.error(f"Ошибка чтения последних строк из {log_file}: {e}")
        return "Ошибка чтения файла."


async def send_last_lines(message: Message, log_file: str, num_lines: int):
    """
    Отправляет последние строки как файл.
    """
    try:
        last_lines = get_last_lines(log_file, num_lines)
        temp_file = 'temp_last_logs.txt'
        with open(temp_file, 'w', encoding='utf-8') as temp:
            temp.write(last_lines)

        document = FSInputFile(
            temp_file, filename=f'last_{num_lines}_lines_{os.path.basename(log_file)}')
        await message.answer_document(document, caption=f"Последние {num_lines} строк из {os.path.basename(log_file)} (файл большой, отправлен только конец).")
        logging.info(
            f"Админ {message.from_user.id} скачал последние {num_lines} строк из {log_file}.")

        os.remove(temp_file)
    except Exception as e:
        logging.error(
            f"Ошибка отправки последних строк из {log_file} админу {message.from_user.id}: {e}")
        await message.answer("Не удалось отправить последние строки логов.")


async def send_full_log_file(message: Message, log_file: str):
    """
    Отправляет полный файл логов.
    """
    try:
        document = FSInputFile(
            log_file, filename=f'{os.path.basename(log_file)}_full.txt')
        await message.answer_document(document, caption=f"Полные логи из {os.path.basename(log_file)} (файл маленький, отправлен целиком).")
        logging.info(
            f"Админ {message.from_user.id} скачал полный файл {log_file}.")
    except Exception as e:
        logging.error(
            f"Ошибка отправки полного файла {log_file} админу {message.from_user.id}: {e}")
        await message.answer("Не удалось отправить файл логов.")


