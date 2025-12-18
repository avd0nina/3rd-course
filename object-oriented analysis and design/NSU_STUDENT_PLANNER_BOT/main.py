import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, filters
from datetime import datetime, timedelta
from controllers import (
    GroupController, ScheduleController, NotificationController,
    HomeworkController, QueueController
)
from storage import GroupStorage

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "YOUR_TELEGRAM_API_TOKEN"

# States for conversations
CHOOSE_GROUP = 1
ENTER_GROUP = 2
CHOOSE_DAY = 3
ENTER_SUBJECT = 4
ENTER_TIME = 5
CHOOSE_ENTRY = 6
CHOOSE_ACTION = 7
CHOOSE_FIELD = 8
ENTER_FIELD_VALUE = 9
CONFIRM_DELETE = 10
ENTER_DESCRIPTION = 11
ENTER_DEADLINE = 12
CHOOSE_TASK = 13
CONFIRM_MARK = 14
TOGGLE_NOTIFICATION = 15
ENTER_HOURS = 16
CHOOSE_DATE = 17
CHOOSE_SUBJECT = 18
CONFIRM_QUEUE = 19
EDIT_FIELD = 20
ENTER_NEW_VALUE = 21

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
        [KeyboardButton("👥 Connect to Group")],
        [KeyboardButton("📚 Schedule"), KeyboardButton("📝 Homework")],
        [KeyboardButton("📋 Queue"), KeyboardButton("🔔 Notifications")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Welcome to Student Planner Bot! 🎓\nSelect an action:",
        reply_markup=reply_markup
    )

# ===== GROUP MANAGEMENT =====
async def connect_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if GroupStorage.is_student_in_any_group(user_id):
        await update.message.reply_text("✅ You're already connected to a group!")
        return ConversationHandler.END
    await update.message.reply_text("Enter your group number:")
    return ENTER_GROUP

async def enter_group_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    group_number = update.message.text.strip()
    if GroupController.connect_student_to_group(user_id, group_number):
        await update.message.reply_text(f"✅ Successfully connected to group {group_number}!")
    else:
        await update.message.reply_text("❌ Failed to connect to group. Try again.")
    return ConversationHandler.END

# ===== SCHEDULE MANAGEMENT =====
async def schedule_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Create", callback_data="schedule_create"),
         InlineKeyboardButton("View", callback_data="schedule_view"),
         InlineKeyboardButton("Edit", callback_data="schedule_edit")],
        [InlineKeyboardButton("Delete", callback_data="schedule_delete")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📚 Schedule Menu", reply_markup=reply_markup)

async def schedule_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    keyboard = [[InlineKeyboardButton(day, callback_data=f"view_day_{day}")] for day in days]
    keyboard.append([InlineKeyboardButton("All Days", callback_data="view_day_all")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Choose a day:", reply_markup=reply_markup)

async def view_schedule_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    day = query.data.replace("view_day_", "")
    
    if day == "all":
        message = ScheduleController.display_schedule(user_id)
    else:
        message = ScheduleController.display_schedule(user_id, day)
    
    await query.edit_message_text(message)

async def schedule_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    keyboard = [[InlineKeyboardButton(day, callback_data=f"create_day_{day}")] for day in days]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Choose a day:", reply_markup=reply_markup)
    return CHOOSE_DAY

async def choose_day_for_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    day = query.data.replace("create_day_", "")
    user_state.set_data(user_id, 'schedule_day', day)
    await query.edit_message_text(f"Enter subject for {day}:")
    return ENTER_SUBJECT

async def enter_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subject = update.message.text.strip()
    user_state.set_data(user_id, 'schedule_subject', subject)
    await update.message.reply_text("Enter time range (HH:MM-HH:MM):")
    return ENTER_TIME

async def enter_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    time_range = update.message.text.strip()
    day = user_state.get_data(user_id, 'schedule_day')
    subject = user_state.get_data(user_id, 'schedule_subject')
    
    result = ScheduleController.create_schedule_entry(user_id, day, subject, time_range)
    if result['status'] == 'success':
        await update.message.reply_text(f"✅ Schedule created: {day}, {subject}, {time_range}")
    else:
        await update.message.reply_text(f"❌ {result['message']}")
    return ConversationHandler.END

async def schedule_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    entries = ScheduleController.get_schedule_entries(user_id)
    
    if not entries:
        await query.edit_message_text("No schedule entries to edit.")
        return ConversationHandler.END
    
    keyboard = [[InlineKeyboardButton(f"{e.day_of_week} - {e.subject}", callback_data=f"edit_entry_{e.id}")] for e in entries]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Choose an entry:", reply_markup=reply_markup)
    return CHOOSE_ENTRY

async def edit_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    entry_id = int(query.data.replace("edit_entry_", ""))
    user_state.set_data(user_id, 'edit_entry_id', entry_id)
    
    keyboard = [
        [InlineKeyboardButton("Edit", callback_data="action_edit"), InlineKeyboardButton("Delete", callback_data="action_delete")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Choose action:", reply_markup=reply_markup)
    return CHOOSE_ACTION

async def handle_edit_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action = query.data.replace("action_", "")
    
    if action == "delete":
        user_state.set_data(user_id, 'edit_action', 'delete')
        await query.edit_message_text("Confirm delete? (yes/no)")
        return CONFIRM_DELETE
    else:
        keyboard = [[InlineKeyboardButton("Start Time", callback_data="field_start_time"),
                    InlineKeyboardButton("End Time", callback_data="field_end_time"),
                    InlineKeyboardButton("Subject", callback_data="field_subject")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Choose field to edit:", reply_markup=reply_markup)
        return CHOOSE_FIELD

async def choose_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    field = query.data.replace("field_", "")
    user_state.set_data(user_id, 'edit_field', field)
    await query.edit_message_text(f"Enter new value for {field}:")
    return ENTER_FIELD_VALUE

async def enter_field_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    value = update.message.text.strip()
    entry_id = user_state.get_data(user_id, 'edit_entry_id')
    field = user_state.get_data(user_id, 'edit_field')
    
    field_map = {'start_time': 'start_time', 'end_time': 'end_time', 'subject': 'subject'}
    db_field = field_map.get(field, field)
    
    if ScheduleController.update_schedule_entry(user_id, entry_id, {db_field: value}):
        await update.message.reply_text(f"✅ Schedule updated!")
    else:
        await update.message.reply_text("❌ Failed to update.")
    return ConversationHandler.END

async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    response = update.message.text.strip().lower()
    
    if response == 'yes':
        entry_id = user_state.get_data(user_id, 'edit_entry_id')
        if ScheduleController.delete_schedule_entry(user_id, entry_id):
            await update.message.reply_text("✅ Schedule deleted!")
        else:
            await update.message.reply_text("❌ Failed to delete.")
    else:
        await update.message.reply_text("❌ Delete cancelled.")
    
    return ConversationHandler.END

async def schedule_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await schedule_edit(update, context)

# ===== HOMEWORK MANAGEMENT =====
async def homework_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Write", callback_data="hw_write"),
         InlineKeyboardButton("View", callback_data="hw_view"),
         InlineKeyboardButton("Mark Complete", callback_data="hw_mark")],
        [InlineKeyboardButton("Edit", callback_data="hw_edit"),
         InlineKeyboardButton("Delete", callback_data="hw_delete"),
         InlineKeyboardButton("Completed", callback_data="hw_completed")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📝 Homework Menu", reply_markup=reply_markup)

async def hw_write(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    subjects = HomeworkController.get_active_subjects(user_id)
    if not subjects:
        subjects = ["Math", "Physics", "Chemistry", "Literature", "History"]
    
    keyboard = [[InlineKeyboardButton(s, callback_data=f"hw_subject_{s}")] for s in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Choose subject:", reply_markup=reply_markup)
    return ENTER_SUBJECT

async def hw_subject_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    subject = query.data.replace("hw_subject_", "")
    user_state.set_data(user_id, 'hw_subject', subject)
    await query.edit_message_text("Enter homework description:")
    return ENTER_DESCRIPTION

async def hw_enter_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    description = update.message.text.strip()
    user_state.set_data(user_id, 'hw_description', description)
    await update.message.reply_text("Enter deadline (YYYY-MM-DD):")
    return ENTER_DEADLINE

async def hw_enter_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    deadline = update.message.text.strip()
    subject = user_state.get_data(user_id, 'hw_subject')
    description = user_state.get_data(user_id, 'hw_description')
    
    result = HomeworkController.write_down_homework(user_id, subject, description, deadline)
    if result['status'] == 'success':
        await update.message.reply_text(f"✅ Homework saved!\nSubject: {subject}\nDeadline: {deadline}")
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
        await query.edit_message_text("No active homework to mark.")
        return ConversationHandler.END
    
    keyboard = [[InlineKeyboardButton(f"{t.subject}", callback_data=f"mark_task_{t.id}")] for t in tasks]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Choose task:", reply_markup=reply_markup)
    return CHOOSE_TASK

async def mark_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    task_id = int(query.data.replace("mark_task_", ""))
    user_state.set_data(user_id, 'mark_task_id', task_id)
    
    keyboard = [[InlineKeyboardButton("Yes", callback_data="confirm_mark_yes"),
                InlineKeyboardButton("No", callback_data="confirm_mark_no")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Mark as completed?", reply_markup=reply_markup)
    return CONFIRM_MARK

async def confirm_mark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    confirmed = query.data.replace("confirm_mark_", "") == "yes"
    
    if confirmed:
        task_id = user_state.get_data(user_id, 'mark_task_id')
        if HomeworkController.mark_homework_as_completed(user_id, task_id):
            await query.edit_message_text("✅ Homework marked as completed!")
        else:
            await query.edit_message_text("❌ Failed to mark.")
    else:
        await query.edit_message_text("❌ Cancelled.")
    return ConversationHandler.END

async def hw_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    tasks = HomeworkController.get_active_tasks(user_id)
    
    if not tasks:
        await query.edit_message_text("No homework to edit.")
        return ConversationHandler.END
    
    keyboard = [[InlineKeyboardButton(f"{t.subject}", callback_data=f"edit_hw_{t.id}")] for t in tasks]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Choose homework:", reply_markup=reply_markup)
    return CHOOSE_TASK

async def edit_hw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    task_id = int(query.data.replace("edit_hw_", ""))
    user_state.set_data(user_id, 'edit_hw_id', task_id)
    
    keyboard = [[InlineKeyboardButton("Description", callback_data="hw_field_description"),
                InlineKeyboardButton("Deadline", callback_data="hw_field_deadline")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Choose field:", reply_markup=reply_markup)
    return CHOOSE_FIELD

async def hw_choose_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    field = query.data.replace("hw_field_", "")
    user_state.set_data(user_id, 'edit_hw_field', field)
    await query.edit_message_text(f"Enter new {field}:")
    return ENTER_FIELD_VALUE

async def hw_enter_field_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    value = update.message.text.strip()
    task_id = user_state.get_data(user_id, 'edit_hw_id')
    field = user_state.get_data(user_id, 'edit_hw_field')
    
    field_map = {'description': 'description', 'deadline': 'deadline'}
    db_field = field_map.get(field, field)
    
    if HomeworkController.update_homework_entry(user_id, task_id, {db_field: value}):
        await update.message.reply_text(f"✅ Homework updated!")
    else:
        await update.message.reply_text("❌ Failed to update.")
    return ConversationHandler.END

async def hw_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    tasks = HomeworkController.get_active_tasks(user_id)
    
    if not tasks:
        await query.edit_message_text("No homework to delete.")
        return ConversationHandler.END
    
    keyboard = [[InlineKeyboardButton(f"{t.subject}", callback_data=f"delete_hw_{t.id}")] for t in tasks]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Choose homework:", reply_markup=reply_markup)
    return CHOOSE_TASK

async def delete_hw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    task_id = int(query.data.replace("delete_hw_", ""))
    user_state.set_data(user_id, 'delete_hw_id', task_id)
    
    keyboard = [[InlineKeyboardButton("Yes", callback_data="confirm_delete_hw_yes"),
                InlineKeyboardButton("No", callback_data="confirm_delete_hw_no")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Delete homework?", reply_markup=reply_markup)
    return CONFIRM_DELETE

async def confirm_delete_hw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    confirmed = query.data.replace("confirm_delete_hw_", "") == "yes"
    
    if confirmed:
        task_id = user_state.get_data(user_id, 'delete_hw_id')
        if HomeworkController.delete_homework_entry(user_id, task_id):
            await query.edit_message_text("✅ Homework deleted!")
        else:
            await query.edit_message_text("❌ Failed to delete.")
    else:
        await query.edit_message_text("❌ Cancelled.")
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
        [InlineKeyboardButton("View", callback_data="queue_view"),
         InlineKeyboardButton("Join", callback_data="queue_join")],
        [InlineKeyboardButton("My Entry", callback_data="queue_my_entry"),
         InlineKeyboardButton("Edit", callback_data="queue_edit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📋 Queue Menu", reply_markup=reply_markup)

async def queue_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    example_dates = ["2025-01-15", "2025-01-16", "2025-01-17"]
    keyboard = [[InlineKeyboardButton(d, callback_data=f"queue_date_{d}")] for d in example_dates]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Choose date:", reply_markup=reply_markup)
    return CHOOSE_DATE

async def queue_choose_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    date = query.data.replace("queue_date_", "")
    user_state.set_data(user_id, 'queue_date', date)
    
    subjects = QueueController.get_available_subjects(date)
    if not subjects:
        subjects = ["Math", "Physics"]
    
    keyboard = [[InlineKeyboardButton(s, callback_data=f"queue_subj_{s}")] for s in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Choose subject:", reply_markup=reply_markup)
    return CHOOSE_SUBJECT

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
    await query.edit_message_text("Choose date:", reply_markup=reply_markup)
    return CHOOSE_DATE

async def queue_join_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    date = query.data.replace("queue_join_date_", "")
    user_state.set_data(user_id, 'join_queue_date', date)
    
    subjects = QueueController.get_available_subjects(date)
    if not subjects:
        subjects = ["Math", "Physics"]
    
    keyboard = [[InlineKeyboardButton(s, callback_data=f"queue_join_subj_{s}")] for s in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Choose subject:", reply_markup=reply_markup)
    return CHOOSE_SUBJECT

async def queue_join_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    subject = query.data.replace("queue_join_subj_", "")
    date = user_state.get_data(user_id, 'join_queue_date')
    
    result = QueueController.take_place_in_queue(user_id, date, subject)
    if result['status'] == 'success':
        entry = result['entry']
        await query.edit_message_text(f"✅ Joined queue!\nPosition: {entry.position}")
    else:
        await query.edit_message_text(f"❌ {result['message']}")
    return ConversationHandler.END

async def queue_my_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    entry = QueueController.get_user_queue_entry(user_id)
    
    if entry:
        message = f"📋 Your Queue Entry\n"
        message += f"Date: {entry['date']}\n"
        message += f"Subject: {entry['subject']}\n"
        message += f"Position: {entry['position']}"
    else:
        message = "You are not in any queue."
    
    await query.edit_message_text(message)

async def queue_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    entry = QueueController.get_user_queue_entry(user_id)
    if not entry:
        await query.edit_message_text("You are not in any queue.")
        return ConversationHandler.END
    
    keyboard = [[InlineKeyboardButton("Position", callback_data="queue_edit_position"),
                InlineKeyboardButton("Delete", callback_data="queue_edit_delete")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Choose action:", reply_markup=reply_markup)
    return EDIT_FIELD

async def queue_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    action = query.data.replace("queue_edit_", "")
    if action == "delete":
        keyboard = [[InlineKeyboardButton("Yes", callback_data="queue_confirm_delete_yes"),
                    InlineKeyboardButton("No", callback_data="queue_confirm_delete_no")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Delete queue entry?", reply_markup=reply_markup)
    else:
        user_state.set_data(user_id, 'edit_queue_field', action)
        await query.edit_message_text(f"Enter new {action}:")
        return ENTER_NEW_VALUE

async def queue_enter_new_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    value = update.message.text.strip()
    field = user_state.get_data(user_id, 'edit_queue_field')
    
    if QueueController.update_queue_entry(user_id, field, value):
        await update.message.reply_text(f"✅ Queue entry updated!")
    else:
        await update.message.reply_text("❌ Failed to update.")
    return ConversationHandler.END

# ===== NOTIFICATION MANAGEMENT =====
async def notification_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Deadlines", callback_data="notif_deadlines"),
         InlineKeyboardButton("Queue", callback_data="notif_queue")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔔 Notifications Menu", reply_markup=reply_markup)

async def notif_deadlines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    settings = NotificationController.get_notification_settings(user_id)
    
    status = "Enabled ✅" if settings['enabled'] else "Disabled ❌"
    keyboard = [[InlineKeyboardButton("Toggle", callback_data="toggle_notif_deadlines")]]
    if settings['enabled']:
        keyboard.append([InlineKeyboardButton("Change Time", callback_data="notif_change_time")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Deadline Notifications: {status}", reply_markup=reply_markup)
    return TOGGLE_NOTIFICATION

async def toggle_notif_deadlines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    settings = NotificationController.get_notification_settings(user_id)
    
    NotificationController.update_notification_settings(user_id, not settings['enabled'])
    new_status = "Enabled ✅" if not settings['enabled'] else "Disabled ❌"
    await query.edit_message_text(f"Deadline Notifications: {new_status}")
    return ConversationHandler.END

async def notif_change_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter reminder hours before deadline:")
    return ENTER_HOURS

async def notif_enter_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        hours = int(update.message.text.strip())
        NotificationController.update_notification_settings(user_id, True, hours)
        await update.message.reply_text(f"✅ Reminder set to {hours} hours before deadline!")
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number.")
    return ConversationHandler.END

async def notif_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    settings = NotificationController.get_queue_notification_settings(user_id)
    
    status = "Enabled ✅" if settings['enabled'] else "Disabled ❌"
    keyboard = [[InlineKeyboardButton("Toggle", callback_data="toggle_notif_queue")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Queue Notifications: {status}", reply_markup=reply_markup)
    return TOGGLE_NOTIFICATION

async def toggle_notif_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    settings = NotificationController.get_queue_notification_settings(user_id)
    
    NotificationController.save_queue_notification_settings(user_id, not settings['enabled'])
    new_status = "Enabled ✅" if not settings['enabled'] else "Disabled ❌"
    await query.edit_message_text(f"Queue Notifications: {new_status}")
    return ConversationHandler.END

# ===== BUTTON HANDLERS =====
async def handle_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if text == "👥 Connect to Group":
        await connect_to_group(update, context)
    elif text == "📚 Schedule":
        await schedule_menu(update, context)
    elif text == "📝 Homework":
        await homework_menu(update, context)
    elif text == "📋 Queue":
        await queue_menu(update, context)
    elif text == "🔔 Notifications":
        await notification_menu(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    
    # Commands
    app.add_handler(CommandHandler("start", start))
    
    # Main conversation handlers
    group_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex(r"👥 Connect"), connect_to_group)],
        states={ENTER_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_group_number)]},
        fallbacks=[MessageHandler(filters.TEXT, lambda u, c: ConversationHandler.END)],
    )
    
    schedule_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex(r"📚 Schedule"), schedule_menu)],
        states={
            CHOOSE_DAY: [CallbackQueryHandler(choose_day_for_schedule)],
            ENTER_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_subject)],
            ENTER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_time)],
            CHOOSE_ENTRY: [CallbackQueryHandler(edit_entry)],
            CHOOSE_ACTION: [CallbackQueryHandler(handle_edit_action)],
            CHOOSE_FIELD: [CallbackQueryHandler(choose_field)],
            ENTER_FIELD_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_field_value)],
            CONFIRM_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_delete)],
        },
        fallbacks=[CallbackQueryHandler(schedule_menu)],
    )
    
    homework_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex(r"📝 Homework"), homework_menu)],
        states={
            ENTER_SUBJECT: [CallbackQueryHandler(hw_subject_select)],
            ENTER_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, hw_enter_description)],
            ENTER_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, hw_enter_deadline)],
            CHOOSE_TASK: [CallbackQueryHandler(lambda u, c: hw_mark(u, c) if u.callback_query.data.startswith('mark') else (hw_edit(u, c) if u.callback_query.data.startswith('edit_hw') else hw_delete(u, c)))],
            CONFIRM_MARK: [CallbackQueryHandler(confirm_mark)],
            CHOOSE_FIELD: [CallbackQueryHandler(hw_choose_field)],
            ENTER_FIELD_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, hw_enter_field_value)],
            CONFIRM_DELETE: [CallbackQueryHandler(confirm_delete_hw)],
        },
        fallbacks=[CallbackQueryHandler(homework_menu)],
    )
    
    queue_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex(r"📋 Queue"), queue_menu)],
        states={
            CHOOSE_DATE: [CallbackQueryHandler(queue_choose_date)],
            CHOOSE_SUBJECT: [CallbackQueryHandler(queue_choose_subject)],
            EDIT_FIELD: [CallbackQueryHandler(queue_edit_field)],
            ENTER_NEW_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, queue_enter_new_value)],
        },
        fallbacks=[CallbackQueryHandler(queue_menu)],
    )
    
    notif_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex(r"🔔 Notifications"), notification_menu)],
        states={
            TOGGLE_NOTIFICATION: [CallbackQueryHandler(toggle_notif_deadlines)],
            ENTER_HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, notif_enter_hours)],
        },
        fallbacks=[CallbackQueryHandler(notification_menu)],
    )
    
    app.add_handler(group_handler)
    app.add_handler(schedule_handler)
    app.add_handler(homework_handler)
    app.add_handler(queue_handler)
    app.add_handler(notif_handler)
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(schedule_view, pattern="^schedule_view$"))
    app.add_handler(CallbackQueryHandler(view_schedule_day, pattern="^view_day_"))
    app.add_handler(CallbackQueryHandler(schedule_create, pattern="^schedule_create$"))
    app.add_handler(CallbackQueryHandler(schedule_edit, pattern="^schedule_edit$"))
    app.add_handler(CallbackQueryHandler(schedule_delete, pattern="^schedule_delete$"))
    
    app.add_handler(CallbackQueryHandler(hw_write, pattern="^hw_write$"))
    app.add_handler(CallbackQueryHandler(hw_view, pattern="^hw_view$"))
    app.add_handler(CallbackQueryHandler(hw_mark, pattern="^hw_mark$"))
    app.add_handler(CallbackQueryHandler(mark_task, pattern="^mark_task_"))
    app.add_handler(CallbackQueryHandler(hw_edit, pattern="^hw_edit$"))
    app.add_handler(CallbackQueryHandler(hw_delete, pattern="^hw_delete$"))
    app.add_handler(CallbackQueryHandler(hw_completed, pattern="^hw_completed$"))
    app.add_handler(CallbackQueryHandler(delete_hw, pattern="^delete_hw_"))
    app.add_handler(CallbackQueryHandler(edit_hw, pattern="^edit_hw_"))
    
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
    app.add_handler(CallbackQueryHandler(notif_change_time, pattern="^notif_change_time$"))
    
    # Text handler for menu buttons
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button_press))
    
    print("🤖 Bot started!")
    app.run_polling()

if __name__ == '__main__':
    main()
