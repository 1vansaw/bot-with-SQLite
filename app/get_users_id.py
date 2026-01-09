from aiogram import F, Router
import json
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import app.keyboards as kb

router_users_id = Router()

def load_access_data():
    """Загружает данные пользователей из JSON-файла."""
    try:
        with open('json/access_user.json', "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "main_admins": [],
            "admins": [],
            "users": []
        }
        
        
def get_users_role(user_id, data):
    if user_id in data['main_admins']:
        return "👑 Главный администратор!"
    elif user_id in data['admins']:
        return "🛠 Администратор!"
    elif user_id in data['users']:
        return "👥 Пользователь"
    return None


# Функция для получения информации о пользователе
async def get_user_info(bot, user_id):
    try:
        user = await bot.get_chat(user_id)
        return user.first_name, user.last_name, user.id
    except Exception as e:
        print(f"Ошибка при получении информации о пользователе {user_id}: {e}")
        return None, None, user_id  # Возвращаем ID, если не удалось получить информацию

@router_users_id.message(F.text == '👥 Пользователи')
async def send_user_list(message: Message, bot, state: FSMContext):   
    data = load_access_data()
    user_id = message.from_user.id  # Получаем ID пользователя
    role = get_users_role(user_id, data)
    user_list = {
        "👑 Главный администратор": [],
        "🛠 Администраторы": [],
        "👥 Пользователи": []
    }

    if role == "👑 Главный администратор!":
        # Обрабатываем списки пользователей
        for user_id in data['main_admins']:
            first_name, last_name, uid = await get_user_info(bot, user_id)
            name_display = f"{first_name or 'Недоступен'} {last_name or ''}".strip()
            user_role = get_users_role(uid, data)
            user_list["👑 Главный администратор"].append(f"{name_display}, ID: {uid}, Уровень доступа: {user_role}")

        for user_id in data['admins']:
            first_name, last_name, uid = await get_user_info(bot, user_id)
            name_display = f"{first_name or 'Недоступен'} {last_name or ''}".strip()
            user_role = get_users_role(uid, data)
            user_list["🛠 Администраторы"].append(f"{name_display}, ID: {uid}, Уровень доступа: {user_role}")

        for user_id in data['users']:
            first_name, last_name, uid = await get_user_info(bot, user_id)
            name_display = f"{first_name or 'Недоступен'} {last_name or ''}".strip()
            user_role = get_users_role(uid, data)
            user_list["👥 Пользователи"].append(f"{name_display}, ID: {uid}, Уровень доступа: {user_role}")

        # Формируем ответ
        response = []
        for group, members in user_list.items():
            response.append(group + ":")
            if members:
                response.append("\n".join(members))
            else:
                response.append("Список пуст.")
            response.append("-----------------------------------------------")
        await message.answer('Ваш список: ',reply_markup=kb.main)
        await message.answer("\n".join(response))
        await state.clear()
        
    else:
        # Отправляем сообщение, если у пользователя нет доступа
        await message.answer("⛔ У вас нет доступа для выполнения этой команды.")