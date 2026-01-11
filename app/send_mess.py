import json
import logging
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from app.handlers import get_user_role, load_access_data
from app.keyboards import edit_mashines, main, admin_menu

# Роутер для рассылки
router_broadcast = Router()

# Состояние для ожидания текста рассылки (расширено для хранения текста)
waiting_for_broadcast = {}  # user_id -> {"waiting": True, "text": str}


def get_all_user_ids():
    """
    Читает access_user.json и возвращает set уникальных telegram_id из всех ролей.
    """
    try:
        with open('json/access_user.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        user_ids = set()
        for role in ['main_admins', 'admins', 'users']:
            user_ids.update(data.get(role, []))
        return user_ids
    except FileNotFoundError:
        logging.error("Файл json/access_user.json не найден.")
        return set()
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка чтения JSON: {e}")
        return set()


@router_broadcast.message(F.text == '📢 Рассылка')
async def start_broadcast(message: Message):
    data = load_access_data()
    user_id = message.from_user.id  # Получаем ID пользователя
    role = get_user_role(user_id, data)
    if role in ["👑 Главный администратор!"]:
        waiting_for_broadcast[user_id] = {
            "waiting": True, "text": None}  # Инициализируем состояние
        await message.answer("Введите текст для рассылки всем пользователям. После ввода вы увидите preview и сможете подтвердить или отменить.",
                             reply_markup=ReplyKeyboardRemove(remove_keyboard=True))
        logging.info(f"Главный админ {user_id} начал процесс рассылки.")
    else:
        await message.answer("Рассылать может только главный администратор")


@router_broadcast.message(F.text)
async def handle_broadcast_text(message: Message):
    data = load_access_data()
    user_id = message.from_user.id  # Получаем ID пользователя
    role = get_user_role(user_id, data)
    if role in ["👑 Главный администратор!"]:
        if not waiting_for_broadcast.get(user_id, {}).get("waiting", False):
            # Тихий возврат, если процесс рассылки не начат
            return

        broadcast_text = message.text
        waiting_for_broadcast[user_id] = {
            "waiting": True, "text": broadcast_text}  # Сохраняем текст

        # Кнопки для подтверждения
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить",
                                  callback_data="broadcast:confirm")],
            [InlineKeyboardButton(
                text="❌ Отмена", callback_data="broadcast:cancel")]
        ])

        # Показываем preview текста с кнопками
        await message.answer(
            f"**Preview рассылки:**\n\n{broadcast_text}\n\nОтправить всем пользователям (кроме вас)?",
            reply_markup=keyboard,
            parse_mode="Markdown"  # Для жирного текста, если нужно
        )
        logging.info(
            f"Главный админ {user_id} ввел текст для рассылки: '{broadcast_text}'.")
    else:
        # Не главный админ — игнорируем
        pass


@router_broadcast.callback_query(F.data.startswith("broadcast:"))
async def handle_broadcast_confirmation(callback):
    user_id = callback.from_user.id
    data = load_access_data()
    role = get_user_role(user_id, data)
    if role not in ["👑 Главный администратор!"]:
        await callback.answer("⛔ У вас нет доступа.", show_alert=True)
        return

    state = waiting_for_broadcast.get(user_id, {})
    if not state.get("waiting", False) or state.get("text") is None:
        await callback.answer("Процесс рассылки не активен.", show_alert=True)
        return

    action = callback.data.split(":", 1)[1]
    broadcast_text = state["text"]

    if action == "confirm":
        # Подтверждение: отправляем рассылку
        waiting_for_broadcast[user_id] = {
            "waiting": False, "text": None}  # Сбрасываем состояние

        # Получаем всех пользователей из JSON
        user_ids = get_all_user_ids()
        total_users = len(user_ids)
        if total_users == 0:
            # Случай без пользователей: отправляем отчет как новое сообщение с клавиатурой
            report_text = "Нет пользователей для рассылки (файл пуст или ошибка чтения)."
            await callback.message.answer(report_text, reply_markup=admin_menu)
            logging.info(
                f"Главный админ {user_id} попытался отправить рассылку, но пользователей нет.")
            await callback.answer("Рассылка не отправлена (нет пользователей).")
            return

        sent_count = 0
        failed_count = 0

        for uid in user_ids:
            if uid == user_id:
                continue  # Исключаем главного админа (отправителя)
            try:
                await callback.bot.send_message(chat_id=uid, text=broadcast_text)
                sent_count += 1
            except Exception as e:
                logging.warning(
                    f"Не удалось отправить рассылку пользователю {uid}: {e}")
                failed_count += 1

        # Отчет о выполнении: отправляем как новое сообщение с клавиатурой (вместо edit_text + пустой answer)
        report_text = f"Рассылка завершена!\nОтправлено: {sent_count}/{total_users - 1}\nНе удалось: {failed_count}\n\nТекст: {broadcast_text}"
        await callback.message.answer(report_text, reply_markup=admin_menu)
        # Опционально: удалить старое сообщение с кнопками для чистоты чата
        await callback.message.delete()

        logging.info(
            f"Главный админ {user_id} подтвердил и отправил рассылку: '{broadcast_text}' ({sent_count} успешно, {failed_count} неудач).")
        await callback.answer("Рассылка отправлена!")

    elif action == "cancel":
        # Отмена: отправляем отчет как новое сообщение с клавиатурой
        waiting_for_broadcast[user_id] = {"waiting": False, "text": None}
        report_text = "Рассылка отменена."
        await callback.message.answer(report_text, reply_markup=admin_menu)

        # Опционально: удалить старое сообщение
        await callback.message.delete()

        logging.info(f"Главный админ {user_id} отменил рассылку.")
        await callback.answer("Отменено.")

