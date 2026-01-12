from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from app.data_shops import *
import json
import os

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='📝 Добавить запись'),
         KeyboardButton(text='📜 История за сутки')],
        [KeyboardButton(text='✏️ Изменить запись'),
         KeyboardButton(text='🔍 Поиск записи')],
        [KeyboardButton(text='🛠️ Редактор'),          
         KeyboardButton(text='👑 Админ меню')],        
        # [KeyboardButton(text='🧹 Очистить чат')]
        [KeyboardButton(text='📚 Руководства')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите пункт'
)

# Создаем клавиатуру с кнопками "Подтвердить" и "Назад"
markup = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_calendar"),
    InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_date")]])


clear_chat = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='✅ Да'), KeyboardButton(
    text='❌ Нет')]], resize_keyboard=True, input_field_placeholder='Выберите пункт')


del_machines = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_delete"),
    InlineKeyboardButton(text='❌ Отмена', callback_data="cancel_delete")]])


del_users = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="✅ Подтвердить",
                         callback_data="confirm_delete_users"),
    InlineKeyboardButton(text='❌ Отмена', callback_data="cancel_delete_users")]])


del_admins = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="✅ Подтвердить",
                         callback_data="confirm_deletes_admins"),
    InlineKeyboardButton(text='❌ Отмена', callback_data="cancel_deletes_admins")]])

del_contact = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="✅ Подтвердить",
                         callback_data="confirm_delet_contact"),
    InlineKeyboardButton(text='❌ Отмена', callback_data="cancel_delet_contacts")]])


edit_mashines = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='✅ Добавить станок'),
         KeyboardButton(text='❌ Удалить станок')],
        [KeyboardButton(text='✅ Добавить контакт'),
         KeyboardButton(text='❌ Удалить контакт')],
        [KeyboardButton(text='✅ Доб.пользователя'),
         KeyboardButton(text='❌ Удал. пользователя')],
        [KeyboardButton(text='↩️ В главное меню')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите действие'
)


admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='✅ Добавить админа'),
         KeyboardButton(text='❌ Удалить админа')],
        [KeyboardButton(text='👥 Пользователи'),
         KeyboardButton(text='📢 Рассылка')],
        [KeyboardButton(text='📄 Посмотреть логи'),
         KeyboardButton(text='💾 Резервная копия БД')],
        [KeyboardButton(text='🕒 Автокопирование БД')],
        [KeyboardButton(text='🔄 Восстановить БД из копии')],
        [KeyboardButton(text='↩️ В главное меню')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите действие'
)




auto_backup_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='🔁 Раз в день')],
        [KeyboardButton(text='📅 Раз в неделю')],
        [KeyboardButton(text='🗓 Раз в месяц')],
        [KeyboardButton(text='❌ Отключить автокопирование')],
        [KeyboardButton(text='↩️ В админ меню')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите интервал'
)




confirm_edit_mashines = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_yes"),
    InlineKeyboardButton(text='❌ Отмена', callback_data="confirm_no")]])


confirm_edit_users = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="✅ Подтвердить",
                         callback_data="confirm_yes_users"),
    InlineKeyboardButton(text='❌ Отмена', callback_data="confirm_no_users")]])

confirm_edit_admins = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="✅ Подтвердить",
                         callback_data="confirm_yes_admins"),
    InlineKeyboardButton(text='❌ Отмена', callback_data="confirm_no_admins")]])


add_contact = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="✅ Подтвердить",
                         callback_data="confirm_yes_contact"),
    InlineKeyboardButton(text='❌ Отмена', callback_data="confirm_no_contact")]])


personal_main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⚡ Электрики', callback_data='electric')],
    [InlineKeyboardButton(text='🔧 Механики', callback_data='mechanic')],
    [InlineKeyboardButton(text='💻 Электроники', callback_data='electron')],
    [InlineKeyboardButton(text="↩️ Назад", callback_data="back_category")]
])


# Кнопки цеха
workshops = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔧 1 цех', callback_data='1-shop'),
     InlineKeyboardButton(text='⚙️ 2 цех', callback_data='2-shop'),
     InlineKeyboardButton(text='🏭 3 цех', callback_data='3-shop')],
    [InlineKeyboardButton(text='📦 11 цех', callback_data='11-shop'),
     InlineKeyboardButton(text='🔬 15 цех', callback_data='15-shop'),
     InlineKeyboardButton(text='🔥 17 цех', callback_data='17-shop')],
    [InlineKeyboardButton(text='💡 20 цех', callback_data='20-shop'),
     InlineKeyboardButton(text='🛠️ 26 цех', callback_data='26-shop'),
     InlineKeyboardButton(text='⚙️ КМТ', callback_data='kmt-shop')]])


def create_keyboard(machine_list):
    buttons = []
    for i in range(0, len(machine_list), 2):
        row = []
        # Добавляем первую кнопку в ряд
        row.append(InlineKeyboardButton(
            text=machine_list[i]['name'], callback_data=machine_list[i]['name']))
        # Проверяем, есть ли следующая кнопка
        if i + 1 < len(machine_list):
            row.append(InlineKeyboardButton(
                text=machine_list[i + 1]['name'], callback_data=machine_list[i + 1]['name']))
        else:
            # Если следующей кнопки нет, добавляем пустую кнопку
            row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
        buttons.append(row)
    # Добавляем кнопку "Назад" на всю ширину
    buttons.append([InlineKeyboardButton(
        text=" ↩️ Назад", callback_data='back_2')])
    # Создаем и возвращаем InlineKeyboardMarkup с кнопками
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Загрузите данные из файла JSON
FILE_PATH = "json/machines_data.json"  # Путь к вашему JSON файлу


def load_machines():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
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


# Загружаем данные о станках из JSON файла
machines_data = load_machines()
# Создаем клавиатуры для каждого цеха
shops_1 = create_keyboard(load_machines()['maschines_1'])
shops_2 = create_keyboard(load_machines()['maschines_2'])
shops_3 = create_keyboard(load_machines()['maschines_3'])
shops_11 = create_keyboard(load_machines()['maschines_11'])
shops_15 = create_keyboard(load_machines()['maschines_15'])
shops_17 = create_keyboard(load_machines()['maschines_17'])
shops_20 = create_keyboard(load_machines()['maschines_20'])
shops_26 = create_keyboard(load_machines()['maschines_26'])
shops_kmt = create_keyboard(load_machines()['maschines_kmt'])


