import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, filters
from controllers import (
    GroupController, ScheduleController, NotificationController,
    HomeworkController, QueueController
)
from storage import GroupStorage

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "YOUR_TELEGRAM_API_TOKEN"

# Conversation states
CHOOSE_GROUP, ENTER_GROUP, CHOOSE_DAY, ENTER_SUBJECT, ENTER_TIME, CHOOSE_ENTRY = 1, 2, 3, 4, 5, 6
CHOOSE_ACTION, CHOOSE_FIELD, ENTER_FIELD_VALUE, CONFIRM_DELETE = 7, 8, 9, 10
ENTER_DESCRIPTION, ENTER_DEADLINE, CHOOSE_TASK, CONFIRM_MARK = 11, 12, 13, 14
TOGGLE_NOTIFICATION, ENTER_HOURS, CHOOSE_DATE, CHOOSE_SUBJECT = 15, 16, 17, 18
CONFIRM_QUEUE, EDIT_FIELD, ENTER_NEW_VALUE = 19, 20, 21

class UserState:
    def __init__(self):
        self.user_data = {}
    
    def set_data(self, user_id, key, value):
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id][key] = value
    
    def get_data(self, user_id, key, default=None):
        if user_id in self.user_data:
            return self.user_data[user_id].get(key, default)
        return default
    
    def clear_data(self, user_id):
        if user_id in self.user_data:
            self.user_data[user_id] = {}

user_state = UserState()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("👥 Подключиться к группе")],
        [KeyboardButton("📚 Расписание"), KeyboardButton("📝 Домашнее задание")],
        [KeyboardButton("📋 Очередь"), KeyboardButton("🔔 Уведомления")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать в бота для планирования студента! 🎓\nВыберите действие:", reply_markup=reply_markup)

# ===== GROUP MANAGEMENT =====
async def connect_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if GroupStorage.is_student_in_any_group(user_id):
        await update.message.reply_text("✅ Вы уже подключены к группе!")
        return ConversationHandler.END
    await update.message.reply_text("Введите номер вашей группы:")
    return ENTER_GROUP

async def enter_group_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    group_number = update.message.text.strip()
    if GroupController.connect_student_to_group(user_id, group_number):
        await update.message.reply_text(f"✅ Успешно подключены к группе {group_number}!")
    else:
        await update.message.reply_text("❌ Не удалось подключиться к группе. Попробуйте ещё раз.")
    return ConversationHandler.END

# ===== SCHEDULE MANAGEMENT =====
async def schedule_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Создать", callback_data="schedule_create"),
         InlineKeyboardButton("Просмотр", callback_data="schedule_view"),
         InlineKeyboardButton("Редактировать", callback_data="schedule_edit")],
        [InlineKeyboardButton("Удалить", callback_data="schedule_delete")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📚 Меню расписания", reply_markup=reply_markup)

async def schedule_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    keyboard = [[InlineKeyboardButton(day, callback_data=f"view_day_{day}")] for day in days]
    keyboard.append([InlineKeyboardButton("Все дни", callback_data="view_day_all")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите день:", reply_markup=reply_markup)

async def view_schedule_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    day = query.data.replace("view_day_", "")
    message = ScheduleController.display_schedule(user_id) if day == "all" else ScheduleController.display_schedule(user_id, day)
    await query.edit_message_text(message)

async def schedule_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    keyboard = [[InlineKeyboardButton(day, callback_data=f"create_day_{day}")] for day in days]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите день:", reply_markup=reply_markup)
    return CHOOSE_DAY

async def choose_day_for_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    day = query.data.replace("create_day_", "")
    user_state.set_data(user_id, 'schedule_day', day)
    await query.edit_message_text(f"Введите предмет для {day}:")
    return ENTER_SUBJECT

async def enter_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subject = update.message.text.strip()
    user_state.set_data(user_id, 'schedule_subject', subject)
    await update.message.reply_text("Введите диапазон времени (ЧЧ:ММ-ЧЧ:ММ):")
    return ENTER_TIME

async def enter_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    time_range = update.message.text.strip()
    day = user_state.get_data(user_id, 'schedule_day')
    subject = user_state.get_data(user_id, 'schedule_subject')
    result = ScheduleController.create_schedule_entry(user_id, day, subject, time_range)
    if result['status'] == 'success':
        await update.message.reply_text(f"✅ Расписание создано: {day}, {subject}, {time_range}")
    else:
        await update.message.reply_text(f"❌ {result['message']}")
    return ConversationHandler.END

async def schedule_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    keyboard = [[InlineKeyboardButton(day, callback_data=f"edit_day_{day}")] for day in days]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите день для редактирования:", reply_markup=reply_markup)
    return CHOOSE_DAY

async def schedule_edit_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    day = query.data.replace("edit_day_", "")
    user_state.set_data(user_id, 'edit_schedule_day', day)
    entries = ScheduleController.get_schedule_entries(user_id, day)
    if not entries:
        await query.edit_message_text(f"Нет записей на {day}.")
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(f"{e.subject} ({e.start_time}-{e.end_time})", callback_data=f"edit_entry_{e.id}")] for e in entries]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите запись:", reply_markup=reply_markup)
    return CHOOSE_ENTRY

async def edit_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    entry_id = int(query.data.replace("edit_entry_", ""))
    user_state.set_data(user_id, 'edit_entry_id', entry_id)
    keyboard = [[InlineKeyboardButton("Редактировать", callback_data="action_edit"), InlineKeyboardButton("Удалить", callback_data="action_delete")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите действие:", reply_markup=reply_markup)
    return CHOOSE_ACTION

async def handle_edit_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action = query.data.replace("action_", "")
    if action == "delete":
        user_state.set_data(user_id, 'edit_action', 'delete')
        keyboard = [[InlineKeyboardButton("Да", callback_data="confirm_delete_yes"),
                    InlineKeyboardButton("Нет", callback_data="confirm_delete_no")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Удалить расписание?", reply_markup=reply_markup)
        return CONFIRM_DELETE
    else:
        keyboard = [[InlineKeyboardButton("Время начала", callback_data="field_start_time"),
                    InlineKeyboardButton("Время окончания", callback_data="field_end_time"),
                    InlineKeyboardButton("Предмет", callback_data="field_subject")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите поле для редактирования:", reply_markup=reply_markup)
        return CHOOSE_FIELD

async def choose_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    field = query.data.replace("field_", "")
    user_state.set_data(user_id, 'edit_field', field)
    
    field_labels = {
        'subject': 'название предмета',
        'start_time': 'времени начала (формат ЧЧ:ММ)',
        'end_time': 'времени окончания (формат ЧЧ:ММ)'
    }
    label = field_labels.get(field, field)
    await query.edit_message_text(f"Введите новое значение для {label}:")
    return ENTER_FIELD_VALUE

async def enter_field_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    value = update.message.text.strip()
    entry_id = user_state.get_data(user_id, 'edit_entry_id')
    field = user_state.get_data(user_id, 'edit_field')
    field_map = {'start_time': 'start_time', 'end_time': 'end_time', 'subject': 'subject'}
    db_field = field_map.get(field, field)
    if ScheduleController.update_schedule_entry(user_id, entry_id, {db_field: value}):
        await update.message.reply_text(f"✅ Расписание обновлено!")
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Не удалось обновить.")
        return ConversationHandler.END

async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    confirmed = query.data.replace("confirm_delete_", "") == "yes"
    if confirmed:
        entry_id = user_state.get_data(user_id, 'edit_entry_id')
        if ScheduleController.delete_schedule_entry(user_id, entry_id):
            await query.edit_message_text("✅ Предмет удален!")
        else:
            await query.edit_message_text("❌ Не удалось удалить.")
    else:
        await query.edit_message_text("❌ Удаление отменено.")
    return ConversationHandler.END

async def schedule_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await schedule_edit(update, context)

# ===== HOMEWORK MANAGEMENT =====
async def homework_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Написать", callback_data="hw_write"),
         InlineKeyboardButton("Просмотр", callback_data="hw_view"),
         InlineKeyboardButton("Отметить выполненным", callback_data="hw_mark")],
        [InlineKeyboardButton("Редактировать", callback_data="hw_edit"),
         InlineKeyboardButton("Удалить", callback_data="hw_delete"),
         InlineKeyboardButton("Выполненные", callback_data="hw_completed")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📝 Меню домашнего задания", reply_markup=reply_markup)

async def hw_write(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Введите название предмета:")
    return CHOOSE_SUBJECT

async def hw_subject_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subject = update.message.text.strip()
    user_state.set_data(user_id, 'hw_subject', subject)
    await update.message.reply_text("Введите описание домашнего задания:")
    return ENTER_DESCRIPTION

async def hw_enter_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    description = update.message.text.strip()
    user_state.set_data(user_id, 'hw_description', description)
    await update.message.reply_text("Введите срок выполнения (ГГГГ-ММ-ДД):")
    return ENTER_DEADLINE

async def hw_enter_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    deadline = update.message.text.strip()
    subject = user_state.get_data(user_id, 'hw_subject')
    description = user_state.get_data(user_id, 'hw_description')
    result = HomeworkController.write_down_homework(user_id, subject, description, deadline)
    if result['status'] == 'success':
        await update.message.reply_text(f"✅ Домашнее задание сохранено!\nПредмет: {subject}\nСрок: {deadline}")
    else:
        await update.message.reply_text(f"❌ {result['message']}")
    return ConversationHandler.END

async def hw_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    message = HomeworkController.display_active_homework(user_id)
    await query.edit_message_text(message)

async def hw_mark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    tasks = HomeworkController.get_active_tasks_for_marking(user_id)
    if not tasks:
        await query.edit_message_text("Нет активного домашнего задания для отметки.")
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(f"{t.subject}", callback_data=f"mark_task_{t.id}")] for t in tasks]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите задачу:", reply_markup=reply_markup)

async def mark_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    task_id = int(query.data.replace("mark_task_", ""))
    user_state.set_data(user_id, 'mark_task_id', task_id)
    keyboard = [[InlineKeyboardButton("Да", callback_data="confirm_mark_yes"),
                InlineKeyboardButton("Нет", callback_data="confirm_mark_no")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Отметить как выполненное?", reply_markup=reply_markup)

async def confirm_mark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    confirmed = query.data.replace("confirm_mark_", "") == "yes"
    if confirmed:
        task_id = user_state.get_data(user_id, 'mark_task_id')
        if HomeworkController.mark_homework_as_completed(user_id, task_id):
            await query.edit_message_text("✅ Домашнее задание отмечено как выполненное!")
        else:
            await query.edit_message_text("❌ Не удалось отметить.")
    else:
        await query.edit_message_text("❌ Отменено.")
    return ConversationHandler.END

async def hw_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    tasks = HomeworkController.get_active_tasks(user_id)
    if not tasks:
        await query.edit_message_text("Нет домашнего задания для редактирования.")
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(f"{t.subject}", callback_data=f"edit_hw_{t.id}")] for t in tasks]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите домашнее задание:", reply_markup=reply_markup)

async def edit_hw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    task_id = int(query.data.replace("edit_hw_", ""))
    user_state.set_data(user_id, 'edit_hw_id', task_id)
    keyboard = [[InlineKeyboardButton("Описание", callback_data="hw_field_description"),
                InlineKeyboardButton("Срок", callback_data="hw_field_deadline")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите поле:", reply_markup=reply_markup)

async def hw_choose_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    field = query.data.replace("hw_field_", "")
    user_state.set_data(user_id, 'edit_hw_field', field)
    
    field_labels = {
        'description': 'описание',
        'deadline': 'срок (формат ГГГГ-ММ-ДД)'
    }
    label = field_labels.get(field, field)
    await query.edit_message_text(f"Введите новое {label}:")
    return ENTER_NEW_VALUE

async def hw_enter_field_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    value = update.message.text.strip()
    task_id = user_state.get_data(user_id, 'edit_hw_id')
    field = user_state.get_data(user_id, 'edit_hw_field')
    field_map = {'description': 'description', 'deadline': 'deadline'}
    db_field = field_map.get(field, field)
    if HomeworkController.update_homework_entry(user_id, task_id, {db_field: value}):
        await update.message.reply_text(f"✅ Домашнее задание обновлено!")
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Не удалось обновить.")
        return ConversationHandler.END

async def hw_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    tasks = HomeworkController.get_active_tasks(user_id)
    if not tasks:
        await query.edit_message_text("Нет домашнего задания для удаления.")
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(f"{t.subject}", callback_data=f"delete_hw_{t.id}")] for t in tasks]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите домашнее задание:", reply_markup=reply_markup)

async def delete_hw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    task_id = int(query.data.replace("delete_hw_", ""))
    user_state.set_data(user_id, 'delete_hw_id', task_id)
    keyboard = [[InlineKeyboardButton("Да", callback_data="confirm_delete_hw_yes"),
                InlineKeyboardButton("Нет", callback_data="confirm_delete_hw_no")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Удалить домашнее задание?", reply_markup=reply_markup)

async def confirm_delete_hw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    confirmed = query.data.replace("confirm_delete_hw_", "") == "yes"
    if confirmed:
        task_id = user_state.get_data(user_id, 'delete_hw_id')
        if HomeworkController.delete_homework_entry(user_id, task_id):
            await query.edit_message_text("✅ Домашнее задание удалено!")
        else:
            await query.edit_message_text("❌ Не удалось удалить.")
    else:
        await query.edit_message_text("❌ Отменено.")
    return ConversationHandler.END

async def hw_completed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    message = HomeworkController.display_completed_homework(user_id)
    await query.edit_message_text(message)

# ===== QUEUE MANAGEMENT =====
async def queue_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Просмотр", callback_data="queue_view"),
         InlineKeyboardButton("Присоединиться", callback_data="queue_join")],
        [InlineKeyboardButton("Моя запись", callback_data="queue_my_entry"),
         InlineKeyboardButton("Редактировать", callback_data="queue_edit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📋 Меню очереди", reply_markup=reply_markup)

async def queue_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    example_dates = ["2025-01-15", "2025-01-16", "2025-01-17"]
    keyboard = [[InlineKeyboardButton(d, callback_data=f"queue_date_{d}")] for d in example_dates]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите дату:", reply_markup=reply_markup)

async def queue_choose_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    date = query.data.replace("queue_date_", "")
    user_state.set_data(user_id, 'queue_date', date)
    subjects = QueueController.get_available_subjects(date)
    if not subjects:
        subjects = ["Математика", "Физика"]
    keyboard = [[InlineKeyboardButton(s, callback_data=f"queue_subj_{s}")] for s in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите предмет:", reply_markup=reply_markup)

async def queue_choose_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    subject = query.data.replace("queue_subj_", "")
    date = user_state.get_data(user_id, 'queue_date')
    message = QueueController.display_queue(user_id, date, subject)
    await query.edit_message_text(message)

async def queue_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    example_dates = ["2025-01-15", "2025-01-16", "2025-01-17"]
    keyboard = [[InlineKeyboardButton(d, callback_data=f"queue_join_date_{d}")] for d in example_dates]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите дату:", reply_markup=reply_markup)

async def queue_join_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    date = query.data.replace("queue_join_date_", "")
    user_state.set_data(user_id, 'join_queue_date', date)
    subjects = QueueController.get_available_subjects(date)
    if not subjects:
        subjects = ["Математика", "Физика"]
    keyboard = [[InlineKeyboardButton(s, callback_data=f"queue_join_subj_{s}")] for s in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите предмет:", reply_markup=reply_markup)

async def queue_join_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    subject = query.data.replace("queue_join_subj_", "")
    date = user_state.get_data(user_id, 'join_queue_date')
    result = QueueController.take_place_in_queue(user_id, date, subject)
    if result['status'] == 'success':
        entry = result['entry']
        await query.edit_message_text(f"✅ Вы присоединились к очереди!\nПозиция: {entry.position}")
    else:
        await query.edit_message_text(f"❌ {result['message']}")
    return ConversationHandler.END

async def queue_my_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    entry = QueueController.get_user_queue_entry(user_id)
    if entry:
        message = f"📋 Ваша запись в очереди\nДата: {entry['date']}\nПредмет: {entry['subject']}\nПозиция: {entry['position']}"
    else:
        message = "Вы не в очереди."
    await query.edit_message_text(message)

async def queue_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    entry = QueueController.get_user_queue_entry(user_id)
    if not entry:
        await query.edit_message_text("Вы не в очереди.")
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton("Удалить", callback_data="queue_edit_delete")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите действие:", reply_markup=reply_markup)

async def queue_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action = query.data.replace("queue_edit_", "")
    if action == "delete":
        await query.edit_message_text("Удалить запись в очереди? Это действие невозможно будет отменить.")
        user_state.set_data(user_id, 'queue_delete_confirm', True)

# ===== NOTIFICATION MANAGEMENT =====
async def notification_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Сроки выполнения", callback_data="notif_deadlines"),
         InlineKeyboardButton("Очередь", callback_data="notif_queue")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔔 Меню уведомлений", reply_markup=reply_markup)

async def notif_deadlines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    settings = NotificationController.get_notification_settings(user_id)
    status = "Включено ✅" if settings['enabled'] else "Отключено ❌"
    keyboard = [[InlineKeyboardButton("Переключить", callback_data="toggle_notif_deadlines")]]
    if settings['enabled']:
        keyboard.append([InlineKeyboardButton("Изменить время", callback_data="notif_change_time")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Уведомления о сроках: {status}", reply_markup=reply_markup)

async def toggle_notif_deadlines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    settings = NotificationController.get_notification_settings(user_id)
    NotificationController.update_notification_settings(user_id, not settings['enabled'])
    new_status = "Включено ✅" if not settings['enabled'] else "Отключено ❌"
    await query.edit_message_text(f"Уведомления о сроках: {new_status}")
    return ConversationHandler.END

async def notif_change_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Введите часы напоминания перед сроком выполнения (целое число, например 24):")
    return ENTER_HOURS

async def notif_enter_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        hours = int(update.message.text.strip())
        NotificationController.update_notification_settings(user_id, True, hours)
        await update.message.reply_text(f"✅ Напоминание установлено на {hours} часов перед сроком!")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите допустимое число.")
        return ConversationHandler.END

async def notif_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    settings = NotificationController.get_queue_notification_settings(user_id)
    status = "Включено ✅" if settings['enabled'] else "Отключено ❌"
    keyboard = [[InlineKeyboardButton("Переключить", callback_data="toggle_notif_queue")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Уведомления об очереди: {status}", reply_markup=reply_markup)

async def toggle_notif_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    settings = NotificationController.get_queue_notification_settings(user_id)
    NotificationController.save_queue_notification_settings(user_id, not settings['enabled'])
    new_status = "Включено ✅" if not settings['enabled'] else "Отключено ❌"
    await query.edit_message_text(f"Уведомления об очереди: {new_status}")
    return ConversationHandler.END

async def handle_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "👥 Подключиться к группе":
        await connect_to_group(update, context)
    elif text == "📚 Расписание":
        await schedule_menu(update, context)
    elif text == "📝 Домашнее задание":
        await homework_menu(update, context)
    elif text == "📋 Очередь":
        await queue_menu(update, context)
    elif text == "🔔 Уведомления":
        await notification_menu(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    group_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex(r"👥 Подключиться"), connect_to_group)],
        states={ENTER_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_group_number)]},
        fallbacks=[],
    )
    
    schedule_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(schedule_create, pattern="^schedule_create$")],
        states={
            CHOOSE_DAY: [CallbackQueryHandler(choose_day_for_schedule, pattern="^create_day_")],
            ENTER_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_subject)],
            ENTER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_time)],
        },
        fallbacks=[],
    )
    
    schedule_edit_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(schedule_edit, pattern="^schedule_edit$")],
        states={
            CHOOSE_DAY: [CallbackQueryHandler(schedule_edit_day, pattern="^edit_day_")],
            CHOOSE_ENTRY: [CallbackQueryHandler(edit_entry, pattern="^edit_entry_")],
            CHOOSE_ACTION: [CallbackQueryHandler(handle_edit_action, pattern="^action_")],
            CHOOSE_FIELD: [CallbackQueryHandler(choose_field, pattern="^field_")],
            ENTER_FIELD_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_field_value)],
            CONFIRM_DELETE: [CallbackQueryHandler(confirm_delete, pattern="^confirm_delete_")],
        },
        fallbacks=[],
    )
    
    homework_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(hw_write, pattern="^hw_write$")],
        states={
            CHOOSE_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, hw_subject_select)],
            ENTER_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, hw_enter_description)],
            ENTER_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, hw_enter_deadline)],
        },
        fallbacks=[],
    )
    
    homework_edit_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(hw_edit, pattern="^hw_edit$")],
        states={
            CHOOSE_TASK: [CallbackQueryHandler(edit_hw, pattern="^edit_hw_")],
            CHOOSE_FIELD: [CallbackQueryHandler(hw_choose_field, pattern="^hw_field_")],
            ENTER_NEW_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, hw_enter_field_value)],
        },
        fallbacks=[],
    )
    
    notification_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(notif_change_time, pattern="^notif_change_time$")],
        states={
            ENTER_HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, notif_enter_hours)],
        },
        fallbacks=[],
    )
    
    app.add_handler(group_handler)
    app.add_handler(schedule_handler)
    app.add_handler(schedule_edit_handler)
    app.add_handler(homework_handler)
    app.add_handler(homework_edit_handler)
    app.add_handler(notification_handler)
    
    app.add_handler(CallbackQueryHandler(schedule_edit_day, pattern="^edit_day_"))
    
    app.add_handler(CallbackQueryHandler(schedule_view, pattern="^schedule_view$"))
    app.add_handler(CallbackQueryHandler(view_schedule_day, pattern="^view_day_"))
    app.add_handler(CallbackQueryHandler(schedule_delete, pattern="^schedule_delete$"))
    
    app.add_handler(CallbackQueryHandler(hw_view, pattern="^hw_view$"))
    app.add_handler(CallbackQueryHandler(hw_mark, pattern="^hw_mark$"))
    app.add_handler(CallbackQueryHandler(mark_task, pattern="^mark_task_"))
    app.add_handler(CallbackQueryHandler(confirm_mark, pattern="^confirm_mark_"))
    app.add_handler(CallbackQueryHandler(hw_delete, pattern="^hw_delete$"))
    app.add_handler(CallbackQueryHandler(delete_hw, pattern="^delete_hw_"))
    app.add_handler(CallbackQueryHandler(confirm_delete_hw, pattern="^confirm_delete_hw_"))
    app.add_handler(CallbackQueryHandler(hw_completed, pattern="^hw_completed$"))
    
    app.add_handler(CallbackQueryHandler(queue_view, pattern="^queue_view$"))
    app.add_handler(CallbackQueryHandler(queue_choose_date, pattern="^queue_date_"))
    app.add_handler(CallbackQueryHandler(queue_choose_subject, pattern="^queue_subj_"))
    app.add_handler(CallbackQueryHandler(queue_join, pattern="^queue_join$"))
    app.add_handler(CallbackQueryHandler(queue_join_date, pattern="^queue_join_date_"))
    app.add_handler(CallbackQueryHandler(queue_join_subject, pattern="^queue_join_subj_"))
    app.add_handler(CallbackQueryHandler(queue_my_entry, pattern="^queue_my_entry$"))
    app.add_handler(CallbackQueryHandler(queue_edit, pattern="^queue_edit$"))
    app.add_handler(CallbackQueryHandler(queue_edit_field, pattern="^queue_edit_"))
    
    app.add_handler(CallbackQueryHandler(notif_deadlines, pattern="^notif_deadlines$"))
    app.add_handler(CallbackQueryHandler(notif_queue, pattern="^notif_queue$"))
    app.add_handler(CallbackQueryHandler(toggle_notif_deadlines, pattern="^toggle_notif_deadlines$"))
    app.add_handler(CallbackQueryHandler(toggle_notif_queue, pattern="^toggle_notif_queue$"))
    
    text_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button_press)],
        states={},
        fallbacks=[],
    )
    app.add_handler(text_handler)
    
    print("🤖 Бот запущен! Нажмите Ctrl+C для остановки.")
    app.run_polling()

if __name__ == '__main__':
    main()
