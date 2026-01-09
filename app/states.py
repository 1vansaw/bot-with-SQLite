from aiogram.fsm.state import State, StatesGroup


class Register(StatesGroup):
    main_menu = State()                 # состояние после нажатия команды старт
    shop_selection = State()            # состояние после нажатия кнопки добавить запись
    machine_selection_1 = State()       # состояние после нажатия кнопки 1 цех
    machine_selection_2 = State()       # состояние после нажатия кнопки 2 цех
    machine_selection_3 = State()       # состояние после нажатия кнопки 3 цех
    machine_selection_11 = State()
    machine_selection_15 = State()
    machine_selection_17 = State()
    machine_selection_20 = State()
    machine_selection_26 = State()
    machine_selection_kmt = State()
    date_start = State()                # состояние после выбора станка любого из цехов
    date_end = State()                  # состояние после нажатия на дату в календаре
    today_date = State()                # состояние после нажатия кнопки сегодня
    confirm_dates = State()             # состояние после подтверждения даты начала работ
    # состояние после подтверждения даты окончания работ
    date_to_time = State()
    time_start = State()                # состояние ввода времени начала работ
    time_end = State()                  # состояние ввода времени окончания работ
    # состояние для перехода к вводу времени окончания работ
    confirm_time = State()
    # состояние для отображения клавиатуры с выбором категории персонала (не используется)
    personal = State()
    working = State()
    working_solution = State()
    fault_status = State()
    awaiting_machine_name = State()
    awaiting_machine_inventory = State()
    delete_machine = State()
    delete_machine_1 = State()
    add_user = State()
    add_admins = State()
    add_contact = State()
    delete_contact = State()
    search_record = State()
    edit_record = State()
    error_code = State()
    waiting_for_search_phrase = State()
    viewing_record = State()
    editing_field = State()
    confirming_edit = State()