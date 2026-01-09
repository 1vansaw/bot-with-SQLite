from aiogram import F, Router
import json
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import app.keyboards as kb
import re
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.states import Register

router_contact = Router()

# Функция для загрузки контактов из файла


def load_contacts():
    try:
        with open('json/contact.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "name": [],
            "phone": [],
            "email": [],
            "position": []
        }

# Функция для сохранения контактов в файл


def save_contacts(contacts):
    with open('json/contact.json', 'w', encoding='utf-8') as file:
        json.dump(contacts, file, ensure_ascii=False, indent=4)


@router_contact.message(F.text == '✅ Добавить контакт')
async def add_contact(message: Message, state: FSMContext):
    await message.answer(
        "Введите контакт в формате: ФИО, Телефон, Email, должность. Например: Иванов Иван Иванович, +1234567890, example@example.com, директор")
    await state.set_state(Register.add_contact)


# Обработчик для получения контактной информации
@router_contact.message(Register.add_contact)
async def receive_contact(message: Message, state: FSMContext):
    # Регулярные выражения для проверки формата
    name_pattern = r'^[A-Za-zА-Яа-яЁё\s-]+$'  # ФИО: буквы, пробелы и дефисы
    # Телефон: +, цифры, пробелы, скобки и дефисы
    phone_pattern = r'^\+?[0-9\s()-]{7,15}$'
    # Email: стандартный формат email
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    # Должность: буквы, пробелы и дефисы
    position_pattern = r'^[A-Za-zА-Яа-яЁё\s-]+$'
    contact_info = message.text.split(", ")
    # Загрузка существующих контактов
    contacts = load_contacts()

    if len(contact_info) == 4:
        name, phone, email, position = contact_info
        # Проверка формата ФИО
        if not re.match(name_pattern, name):
            await message.answer("Неправильный формат ФИО. Используйте только буквы и пробелы.")
            return

        # Проверка формата телефона
        if not re.match(phone_pattern, phone):
            await message.answer("Неправильный формат телефона. Пример: +1234567890.")
            return

        # Проверка формата email
        if not re.match(email_pattern, email):
            await message.answer("Неправильный формат email. Пример: example@example.com.")
            return

        # Проверка формата должности
        if not re.match(position_pattern, position):
            await message.answer("Неправильный формат должности. Используйте только буквы и пробелы.")
            return
        # Проверка на дубликаты
        for contact in contacts:
            if contact['phone'] == phone or contact['email'] == email:
                await message.answer("Контакт с таким номером телефона или email уже существует.")
                return
        await state.update_data(contact_info=contact_info)
        await message.answer("Вы уверены, что хотите добавить этот контакт?", reply_markup=kb.add_contact)
    else:
        await message.answer("Неправильный формат. Пожалуйста, используйте формат: ФИО, Телефон, Email, Должность.")


@router_contact.callback_query(F.data == "confirm_yes_contact")
async def confirm_add_contact(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    contact = data.get('contact_info')
    name, phone, email, position = contact
    # Загрузка существующих контактов
    contacts = load_contacts()
    # Добавляем контакт в список
    contacts.append({
        "name": name,
        "phone": phone,
        "email": email,
        "position": position
    })
    # Сохраняем обновленный список контактов в файл
    save_contacts(contacts)
    await state.clear()
    await callback_query.message.edit_text("Контакт успешно добавлен!")
    await state.set_state(Register.main_menu)
    await callback_query.message.answer("Возврат в главное меню", reply_markup=kb.main)


@router_contact.callback_query(F.data == "confirm_no_contact")
async def cancel_add_contact(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text("Добавление контакта отменено.")
    await callback_query.message.answer("Выберите действие (только для администраторов)", reply_markup=kb.edit_mashines)
    await state.clear()


def create_keyboard_contact(machine_list):
    buttons = []
    for i in range(0, len(machine_list), 2):
        row = []
        # Добавляем первую кнопку в ряд
        row.append(InlineKeyboardButton(
            text=machine_list[i]['name'], callback_data=f"contact_{machine_list[i]['phone']}"))
        # Проверяем, есть ли следующая кнопка
        if i + 1 < len(machine_list):
            row.append(InlineKeyboardButton(
                text=machine_list[i + 1]['name'], callback_data=f"contact_{machine_list[i + 1]['phone']}"))
        else:
            # Если следующей кнопки нет, добавляем пустую кнопку
            row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router_contact.message(F.text == '❌ Удалить контакт')
async def delete_contact(message: Message, state: FSMContext):
    await state.set_state(Register.delete_contact)
    contacts = load_contacts()
    keyboard = create_keyboard_contact(contacts)
    await message.answer("Выберите контакт для удаления:", reply_markup=keyboard)


@router_contact.callback_query(F.data.startswith("contact_"))
async def confirm_delete_contact(callback_query: CallbackQuery, state: FSMContext):
    contact_id = callback_query.data.split('_')[1]
    await state.update_data(contacts_id=contact_id)
    contacts = load_contacts()
    for i in contacts:
        if i['phone'] == contact_id:
            await callback_query.message.edit_text(f"Вы действительно хотите удалить {i['name']}?", reply_markup=kb.del_contact)
    #         contacts.remove(contacts.index(i))
    # save_contacts(contacts)


@router_contact.callback_query(F.data == "confirm_delet_contact")
async def confirm_deletes_contact(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    contact = data.get('contacts_id')
    contacts = load_contacts()
    for i in contacts:
        if i['phone'] == contact:
            del contacts[contacts.index(i)]
    save_contacts(contacts)
    await callback_query.message.edit_text(f"Пользователь {contact} удален")
    await callback_query.message.answer("Выберите действие (только для администраторов)", reply_markup=kb.edit_mashines)
    await state.clear()


@router_contact.callback_query(F.data == "cancel_delet_contacts")
async def cancel_delete(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text("Удаление отменено.")
    await callback_query.message.answer("Выберите действие (только для администраторов)", reply_markup=kb.edit_mashines)
    await state.clear()


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


# Обработка нажатия кнопки "Контакты"
@router_contact.message(F.text == '/contacts')
async def show_contacts(message: Message):
    data = load_access_data()  # Загружаем данные о пользователях
    user_id = message.from_user.id  # Получаем ID пользователя
    # Определяем роль пользователя
    role = get_users_role(user_id, data)
    if role in ["👑 Главный администратор!", "🛠 Администратор!", "👥 Пользователь"]:
        contacts_info = "Вот наши контакты:\n"
        contacts = load_contacts()
        for contact in contacts:
            # Форматируем строку для вывода
            contacts_info += f"👤 {contact['name']}\n💼 Должность: {contact['position']}\n📞 Телефон: {contact['phone']}\n✉️ Email: {contact['email']}\n"
            contacts_info += "--------------------------------------\n"  # Добавляем разделитель
        # Удаляем последний разделитель
        contacts_info = contacts_info.rstrip("---------\n")
        await message.answer(contacts_info)
    else:
        await message.answer("⛔ У вас нет доступа.")
