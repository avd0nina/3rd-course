import logging
import hashlib
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, \
    ConversationHandler, filters
from token_config import get_telegram_bot_token
from controllers import (
    GroupController, ScheduleController, NotificationController,
    HomeworkController, QueueController, NoteController, GmailController
)
from notifier import Notifier
from storage import GroupStorage

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = get_telegram_bot_token()

# Conversation states
CHOOSE_GROUP, ENTER_GROUP, CHOOSE_DAY, ENTER_SUBJECT, ENTER_TIME, CHOOSE_ENTRY = 1, 2, 3, 4, 5, 6
CHOOSE_ACTION, CHOOSE_FIELD, ENTER_FIELD_VALUE, CONFIRM_DELETE = 7, 8, 9, 10
ENTER_DESCRIPTION, ENTER_DEADLINE, CHOOSE_TASK, CONFIRM_MARK = 11, 12, 13, 14
TOGGLE_NOTIFICATION, ENTER_HOURS, CHOOSE_DATE, CHOOSE_SUBJECT = 15, 16, 17, 18
CONFIRM_QUEUE, EDIT_FIELD, ENTER_NEW_VALUE = 19, 20, 21
NOTE_ENTER_TITLE, NOTE_ENTER_CONTENT, NOTE_CHOOSE, NOTE_EDIT_FIELD, NOTE_ENTER_NEW_VALUE = 30, 31, 32, 33, 34
BROADCAST_ENTER_MESSAGE, BROADCAST_CONFIRM = 70, 71
FEED_MENU = 80
# После существующих констант добавить:
DISCIPLINE_NOTE_CHOOSE_DISCIPLINE, DISCIPLINE_NOTE_ENTER_TITLE, DISCIPLINE_NOTE_ENTER_CONTENT, DISCIPLINE_NOTE_EDIT_PICK, DISCIPLINE_NOTE_EDIT_FIELD, DISCIPLINE_NOTE_ENTER_VALUE = 40, 41, 42, 43, 44, 45
DISCIPLINE_CHOOSE, DISCIPLINE_NOTE_VIEW = 50, 51
# После существующих констант
DISCIPLINE_NOTE_ENTER_TITLE, DISCIPLINE_NOTE_ENTER_CONTENT, DISCIPLINE_NOTE_EDIT_CHOOSE, DISCIPLINE_NOTE_EDIT_FIELD, DISCIPLINE_NOTE_EDIT_VALUE, DISCIPLINE_NOTE_DELETE_CHOOSE = 60, 61, 62, 63, 64, 65


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
        [KeyboardButton("👥 Подключиться к группе"), KeyboardButton("👥 Моя группа")],
        [KeyboardButton("📚 Расписание"), KeyboardButton("📝 Домашнее задание")],
        [KeyboardButton("📋 Очередь"), KeyboardButton("🔔 Уведомления")],
        [KeyboardButton("📒 Заметки"), KeyboardButton("💬 Предметные чаты")],
        [KeyboardButton("📧 Привязать Gmail")],
        [KeyboardButton("📰 Лента событий")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать в бота для планирования студента! 🎓\nВыберите действие:",
                                    reply_markup=reply_markup)


# ===== GMAIL OAUTH — C2 =====

async def link_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /link_gmail и кнопка — запускает OAuth-привязку Gmail."""
    user_id = update.effective_user.id
    if GmailController.get_link_status(user_id):
        await update.message.reply_text("📧 Gmail уже привязан к вашему аккаунту.")
        return
    auth_url = GmailController.generate_oauth_url(user_id)
    await update.message.reply_text(
        "📧 Для привязки Gmail перейдите по ссылке:\n\n"
        + auth_url
        + "\n\nПосле авторизации в браузере вернитесь сюда."
    )


# ===== GROUP MANAGEMENT =====
async def connect_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введите номер группы.\n"
        "Если вы уже были подключены, группа и расписание будут обновлены."
    )
    return ENTER_GROUP


async def enter_group_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    group_number = update.message.text.strip()
    result = GroupController.connect_student_to_group_with_details(user_id, group_number)
    if result["status"] == "success":
        await update.message.reply_text(result["message"])
    else:
        await update.message.reply_text(f"❌ {result['message']}")
    return ConversationHandler.END

async def group_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_group = GroupStorage.get_student_group(user_id)

    if not user_group:
        await update.message.reply_text("❌ Вы пока не подключены к группе.")
        return

    keyboard = [
        [InlineKeyboardButton("📣 Общий сбор", callback_data="group_broadcast")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👥 Ваша группа\n\n"
        f"Номер: {user_group.number}\n"
        f"ID: {user_group.id}\n\n"
        f"Выберите действие:",
        reply_markup=reply_markup
    )


async def group_broadcast_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_group = GroupStorage.get_student_group(user_id)

    if not user_group:
        await query.edit_message_text("❌ Вы пока не подключены к группе.")
        return ConversationHandler.END

    user_state.set_data(user_id, "broadcast_group_id", user_group.id)

    await query.edit_message_text(
        f"📣 Общий сбор для группы {user_group.number}\n\n"
        f"Введите текст сообщения, которое нужно отправить группе:"
    )

    return BROADCAST_ENTER_MESSAGE

async def show_feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    NSU-050 / F5 + NSU-051 / F6:
    экран 'Лента событий' с фильтрами по типу события.
    """
    user_id = update.effective_user.id

    events = Notifier.get_queued_digest_events(user_id=user_id, limit=20)

    keyboard = [
        [
            InlineKeyboardButton("Все", callback_data="feed_filter_all"),
            InlineKeyboardButton("📚 Расписание", callback_data="feed_filter_schedule")
        ],
        [
            InlineKeyboardButton("📝 Домашка", callback_data="feed_filter_homework"),
            InlineKeyboardButton("📒 Заметки", callback_data="feed_filter_notes")
        ],
        [
            InlineKeyboardButton("📣 Сборы", callback_data="feed_filter_broadcast"),
            InlineKeyboardButton("📋 Очередь", callback_data="feed_filter_queue")
        ]
    ]

    text = build_feed_text(events, selected_filter="all")

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def build_feed_text(events: list, selected_filter: str = "all") -> str:
    """
    NSU-051 / F6:
    формирует текст ленты с учётом выбранного фильтра.
    """
    filter_titles = {
        "all": "Все события",
        "schedule": "Расписание",
        "homework": "Домашнее задание",
        "notes": "Заметки",
        "broadcast": "Общие сборы",
        "queue": "Очередь"
    }

    filtered_events = filter_feed_events(events, selected_filter)

    title = filter_titles.get(selected_filter, "Все события")

    if not filtered_events:
        return f"📰 Лента событий\nФильтр: {title}\n\n📭 Нет событий по выбранному фильтру."

    text = f"📰 Лента событий\nФильтр: {title}\n\n"

    for event in filtered_events:
        priority = event.get("priority", "normal")
        event_type = event.get("event_type", "unknown")
        message = event.get("message", "")
        queued_at = event.get("queued_at") or event.get("created_at") or ""

        text += (
            f"• [{priority.upper()}] {event_type}\n"
            f"  {message}\n"
            f"  {queued_at}\n\n"
        )

    return text


def filter_feed_events(events: list, selected_filter: str) -> list:
    """
    NSU-051 / F6:
    фильтрация событий ленты по типу.
    """
    if selected_filter == "all":
        return events

    filter_keywords = {
        "schedule": ["schedule", "lesson", "пара", "распис"],
        "homework": ["homework", "deadline", "hw", "домаш"],
        "notes": ["note", "notes", "замет"],
        "broadcast": ["broadcast", "group_broadcast", "сбор"],
        "queue": ["queue", "очеред"]
    }

    keywords = filter_keywords.get(selected_filter, [])

    result = []
    for event in events:
        event_type = str(event.get("event_type", "")).lower()
        message = str(event.get("message", "")).lower()

        if any(keyword in event_type or keyword in message for keyword in keywords):
            result.append(event)

    return result


async def show_feed_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    NSU-051 / F6:
    обработчик кнопок фильтра ленты.
    """
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    selected_filter = query.data.replace("feed_filter_", "")

    events = Notifier.get_queued_digest_events(user_id=user_id, limit=20)

    keyboard = [
        [
            InlineKeyboardButton("Все", callback_data="feed_filter_all"),
            InlineKeyboardButton("📚 Расписание", callback_data="feed_filter_schedule")
        ],
        [
            InlineKeyboardButton("📝 Домашка", callback_data="feed_filter_homework"),
            InlineKeyboardButton("📒 Заметки", callback_data="feed_filter_notes")
        ],
        [
            InlineKeyboardButton("📣 Сборы", callback_data="feed_filter_broadcast"),
            InlineKeyboardButton("📋 Очередь", callback_data="feed_filter_queue")
        ]
    ]

    text = build_feed_text(events, selected_filter=selected_filter)

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def broadcast_enter_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text.strip()

    if not message:
        await update.message.reply_text("❌ Сообщение не может быть пустым. Введите текст общего сбора:")
        return BROADCAST_ENTER_MESSAGE

    user_state.set_data(user_id, "broadcast_message", message)

    keyboard = [
        [
            InlineKeyboardButton("✅ Отправить", callback_data="broadcast_confirm_yes"),
            InlineKeyboardButton("❌ Отмена", callback_data="broadcast_confirm_no")
        ]
    ]

    await update.message.reply_text(
        f"📣 Подтвердите общий сбор\n\n"
        f"Сообщение:\n"
        f"{message}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return BROADCAST_CONFIRM

async def send_telegram_group_broadcast(context: ContextTypes.DEFAULT_TYPE, group_id: int, message: str) -> dict:
    """
    Реальная Telegram-рассылка общего сбора участникам группы.
    Важно: бот может написать пользователю только если пользователь уже запускал бота.
    """
    members = GroupStorage.get_group_members(group_id)

    sent = []
    failed = []

    for member in members:
        try:
            await context.bot.send_message(
                chat_id=member.user_id,
                text=f"📣 Общий сбор\n\n{message}"
            )
            sent.append(member.user_id)
        except Exception as e:
            failed.append({
                "user_id": member.user_id,
                "error": str(e)
            })

    return {
        "sent_count": len(sent),
        "failed_count": len(failed),
        "sent": sent,
        "failed": failed
    }

async def broadcast_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "broadcast_confirm_no":
        user_state.set_data(user_id, "broadcast_group_id", None)
        user_state.set_data(user_id, "broadcast_message", None)
        await query.edit_message_text("❌ Общий сбор отменён.")
        return ConversationHandler.END

    group_id = user_state.get_data(user_id, "broadcast_group_id")
    message = user_state.get_data(user_id, "broadcast_message")

    if not group_id or not message:
        await query.edit_message_text("❌ Не удалось найти данные общего сбора. Попробуйте заново.")
        return ConversationHandler.END

    result = GroupController.send_group_broadcast(
        user_id=user_id,
        group_id=group_id,
        message=message
    )

    user_state.set_data(user_id, "broadcast_group_id", None)
    user_state.set_data(user_id, "broadcast_message", None)

    if result["status"] == "success":
        telegram_result = await send_telegram_group_broadcast(
            context=context,
            group_id=group_id,
            message=message
        )

        await query.edit_message_text(
            f"✅ Общий сбор отправлен.\n\n"
            f"Отправлено в Telegram: {telegram_result['sent_count']}\n"
            f"Ошибок отправки: {telegram_result['failed_count']}"
        )
    else:
        await query.edit_message_text(f"❌ {result['message']}")

    return ConversationHandler.END

# ===== SCHEDULE MANAGEMENT =====
async def schedule_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Создать", callback_data="schedule_create"),
         InlineKeyboardButton("Просмотр", callback_data="schedule_view"),
         InlineKeyboardButton("Что изменилось", callback_data="schedule_changes"),
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
    message = ScheduleController.display_nsu_schedule(
        user_id) if day == "all" else ScheduleController.display_nsu_schedule(user_id, day)
    await query.edit_message_text(message)


async def schedule_changes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    message = ScheduleController.display_schedule_changes(user_id)
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
    await query.edit_message_text(
        "Введите пару в формате:\n"
        "Предмет | ЧЧ:ММ-ЧЧ:ММ\n"
        "Например: Математика | 09:00-10:35"
    )
    return ENTER_SUBJECT


async def enter_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lesson_text = update.message.text.strip()
    day = user_state.get_data(user_id, 'schedule_day')
    try:
        lesson = ScheduleController.parse_lesson_input(lesson_text)
    except ValueError as error:
        await update.message.reply_text(f"❌ {error}\nПопробуйте ещё раз:")
        return ENTER_SUBJECT

    result = ScheduleController.create_schedule_entry(
        user_id,
        day,
        lesson["subject"],
        f'{lesson["start_time"]}-{lesson["end_time"]}',
    )
    if result['status'] == 'success':
        await update.message.reply_text(f"✅ Пара добавлена в {day}.")
    else:
        await update.message.reply_text(f"❌ {result['message']}")
    return ConversationHandler.END


async def schedule_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    entries = ScheduleController.get_schedule_entries(user_id)
    if not entries:
        await query.edit_message_text("Нет пар для редактирования.")
        return ConversationHandler.END
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    keyboard = [[InlineKeyboardButton(day, callback_data=f"edit_day_{day}")] for day in days]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Выберите день недели, в котором находится пара для изменения:",
        reply_markup=reply_markup,
    )
    return CHOOSE_DAY


async def schedule_edit_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    day = query.data.replace("edit_day_", "")
    user_state.set_data(user_id, 'schedule_day', day)
    entries = ScheduleController.get_schedule_entries(user_id, day)
    if not entries:
        await query.edit_message_text(f"На {day} нет пар для редактирования.")
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(f"{e.start_time}-{e.end_time} — {e.subject}", callback_data=f"edit_entry_{e.id}")]
                for e in entries]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Выберите пару на {day}:", reply_markup=reply_markup)
    return CHOOSE_ENTRY


async def edit_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    entry_id = int(query.data.replace("edit_entry_", ""))
    user_state.set_data(user_id, 'edit_entry_id', entry_id)
    await query.edit_message_text(
        "Введите новые данные пары в формате:\n"
        "Предмет | ЧЧ:ММ-ЧЧ:ММ\n"
        "Например: Физика | 12:40-14:15"
    )
    return ENTER_FIELD_VALUE


async def enter_field_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lesson_text = update.message.text.strip()
    entry_id = user_state.get_data(user_id, 'edit_entry_id')
    try:
        lesson = ScheduleController.parse_lesson_input(lesson_text)
    except ValueError as error:
        await update.message.reply_text(f"❌ {error}\nПопробуйте ещё раз:")
        return ENTER_FIELD_VALUE
    updates = {
        "subject": lesson["subject"],
        "start_time": lesson["start_time"],
        "end_time": lesson["end_time"],
    }
    if ScheduleController.update_schedule_entry(user_id, entry_id, updates):
        await update.message.reply_text("✅ Пара обновлена!")
        return ConversationHandler.END
    await update.message.reply_text("❌ Не удалось обновить.")
    return ConversationHandler.END


async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if query.data == "confirm_schedule_delete_yes":
        entry_id = user_state.get_data(user_id, 'edit_entry_id')
        if ScheduleController.delete_schedule_entry(user_id, entry_id):
            await query.edit_message_text("✅ Пара удалена из расписания!")
        else:
            await query.edit_message_text("❌ Не удалось удалить.")
    else:
        await query.edit_message_text("❌ Удаление отменено.")
    return ConversationHandler.END


async def schedule_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    keyboard = [[InlineKeyboardButton(day, callback_data=f"delete_day_{day}")] for day in days]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Выберите день недели, в котором находится пара для удаления:",
        reply_markup=reply_markup,
    )
    return CHOOSE_DAY


async def schedule_delete_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    day = query.data.replace("delete_day_", "")
    user_state.set_data(user_id, 'schedule_day', day)
    entries = ScheduleController.get_schedule_entries(user_id, day)
    if not entries:
        await query.edit_message_text(f"На {day} нет пар для удаления.")
        return ConversationHandler.END
    keyboard = [
        [InlineKeyboardButton(f"{e.start_time}-{e.end_time} — {e.subject}", callback_data=f"delete_entry_{e.id}")] for e
        in entries]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Выберите пару на {day} для удаления:", reply_markup=reply_markup)
    return CHOOSE_ENTRY


async def delete_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    entry_id = int(query.data.replace("delete_entry_", ""))
    user_state.set_data(user_id, 'edit_entry_id', entry_id)
    keyboard = [[InlineKeyboardButton("Да", callback_data="confirm_schedule_delete_yes"),
                 InlineKeyboardButton("Нет", callback_data="confirm_schedule_delete_no")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Удалить выбранную пару?", reply_markup=reply_markup)
    return CONFIRM_DELETE


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


async def discipline_note_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    safe_key = query.data.replace("disc_note_subj_back_", "")
    subject_name = user_state.get_data(user_id, f'subject_back_{safe_key}', "Unknown")

    user_state.set_data(user_id, 'disc_note_subject_name', subject_name)

    keyboard = [
        [InlineKeyboardButton("➕ Создать", callback_data="disc_note_create")],
        [InlineKeyboardButton("📖 Просмотреть", callback_data="disc_note_view")],
        [InlineKeyboardButton("✏️ Редактировать", callback_data="disc_note_edit")],
        [InlineKeyboardButton("🗑️ Удалить", callback_data="disc_note_delete")],
        [InlineKeyboardButton("🔙 Назад", callback_data="subject_notes")]
    ]
    await query.edit_message_text(
        f"📚 *{subject_name}*\n\nВыберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


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
    elif text == "👥 Моя группа":
        await group_card(update, context)
    elif text == "📚 Расписание":
        await schedule_menu(update, context)
    elif text == "📝 Домашнее задание":
        await homework_menu(update, context)
    elif text == "📋 Очередь":
        await queue_menu(update, context)
    elif text == "🔔 Уведомления":
        await notification_menu(update, context)
    elif text == "📒 Заметки":
        await notes_menu(update, context)
    elif text == "💬 Предметные чаты":
        await subject_chats_menu(update, context)
    elif text == "📧 Привязать Gmail":
        await link_gmail(update, context)
    elif text == "📰 Лента событий":
        await show_feed(update, context)


async def notes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 Мои заметки", callback_data="my_notes")],
        [InlineKeyboardButton("📚 Заметки по предмету", callback_data="subject_notes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📒 Заметки\n\nВыберите тип заметок:", reply_markup=reply_markup)


async def note_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Введите заголовок заметки:")
    return NOTE_ENTER_TITLE


async def note_enter_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state.set_data(user_id, 'note_title', update.message.text.strip())
    await update.message.reply_text("Введите текст заметки:")
    return NOTE_ENTER_CONTENT


async def note_enter_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    title = user_state.get_data(user_id, 'note_title')
    content = update.message.text.strip()
    result = NoteController.create_personal_note(user_id, title, content)
    if result['status'] == 'success':
        await update.message.reply_text(f"✅ Заметка «{title}» сохранена!")
    else:
        await update.message.reply_text(f"❌ {result['message']}")
    return ConversationHandler.END


async def note_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    await query.edit_message_text(NoteController.display_personal_notes(user_id))


async def note_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    notes = NoteController.get_personal_notes(user_id)
    if not notes:
        await query.edit_message_text("❌ Нет заметок для редактирования.")
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(n.title, callback_data=f"note_edit_pick_{n.id}")] for n in notes]
    await query.edit_message_text("Выберите заметку:", reply_markup=InlineKeyboardMarkup(keyboard))
    return NOTE_CHOOSE


async def note_edit_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    note_id = int(query.data.replace("note_edit_pick_", ""))
    user_state.set_data(user_id, 'edit_note_id', note_id)
    keyboard = [[InlineKeyboardButton("Заголовок", callback_data="note_field_title"),
                 InlineKeyboardButton("Текст", callback_data="note_field_content")]]
    await query.edit_message_text("Что редактировать?", reply_markup=InlineKeyboardMarkup(keyboard))
    return NOTE_EDIT_FIELD


async def note_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    field = query.data.replace("note_field_", "")
    user_state.set_data(user_id, 'edit_note_field', field)
    label = "заголовок" if field == "title" else "текст"
    await query.edit_message_text(f"Введите новый {label}:")
    return NOTE_ENTER_NEW_VALUE


async def note_enter_new_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    note_id = user_state.get_data(user_id, 'edit_note_id')
    field = user_state.get_data(user_id, 'edit_note_field')
    result = NoteController.update_personal_note(user_id, note_id, {field: update.message.text.strip()})
    if result['status'] == 'success':
        await update.message.reply_text("✅ Заметка обновлена!")
    else:
        await update.message.reply_text(f"❌ {result['message']}")
    return ConversationHandler.END


async def note_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    notes = NoteController.get_personal_notes(user_id)
    if not notes:
        await query.edit_message_text("❌ Нет заметок для удаления.")
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(n.title, callback_data=f"note_delete_pick_{n.id}")] for n in notes]
    await query.edit_message_text("Выберите заметку для удаления:", reply_markup=InlineKeyboardMarkup(keyboard))
    return NOTE_CHOOSE


async def note_delete_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    note_id = int(query.data.replace("note_delete_pick_", ""))
    user_state.set_data(user_id, 'delete_note_id', note_id)
    keyboard = [[InlineKeyboardButton("Да", callback_data="note_delete_confirm_yes"),
                 InlineKeyboardButton("Нет", callback_data="note_delete_confirm_no")]]
    await query.edit_message_text("Удалить заметку?", reply_markup=InlineKeyboardMarkup(keyboard))
    return NOTE_CHOOSE


async def back_to_notes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("📝 Мои заметки", callback_data="my_notes")],
        [InlineKeyboardButton("📚 Заметки по предмету", callback_data="subject_notes")]
    ]
    await query.edit_message_text("📒 Заметки\n\nВыберите тип заметок:", reply_markup=InlineKeyboardMarkup(keyboard))


async def note_delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if query.data == "note_delete_confirm_yes":
        note_id = user_state.get_data(user_id, 'delete_note_id')
        result = NoteController.delete_personal_note(user_id, note_id)
        await query.edit_message_text(
            "✅ Заметка удалена!" if result['status'] == 'success' else f"❌ {result['message']}")
    else:
        await query.edit_message_text("❌ Отменено.")
    return ConversationHandler.END


async def discipline_note_choose_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    subject = query.data.replace("disc_note_subj_", "")
    user_state.set_data(user_id, 'disc_note_subject', subject)
    user_state.set_data(user_id, 'disc_note_subject_name', subject)

    keyboard = [
        [InlineKeyboardButton("➕ Создать", callback_data="disc_note_create")],
        [InlineKeyboardButton("📖 Просмотреть", callback_data="disc_note_view")],
        [InlineKeyboardButton("✏️ Редактировать", callback_data="disc_note_edit")],
        [InlineKeyboardButton("🗑️ Удалить", callback_data="disc_note_delete")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_notes")]
    ]
    await query.edit_message_text(f"📚 *{subject}*\n\nВыберите действие:", reply_markup=InlineKeyboardMarkup(keyboard),
                                  parse_mode="Markdown")


async def discipline_note_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    subject_name = user_state.get_data(user_id, 'disc_note_subject_name')

    user_group = GroupStorage.get_student_group(user_id)
    if not user_group:
        await query.edit_message_text("❌ Вы не подключены к группе")
        return

    result = NoteController.get_discipline_notes(user_id, user_group.id, subject_name)

    if result['status'] != 'success' or not result['notes']:
        await query.edit_message_text(f"❌ Нет общих заметок по предмету *{subject_name}*", parse_mode="Markdown")
        return

    text = f"📚 *Общие заметки по {subject_name}*\n\n"
    for i, note in enumerate(result['notes'], 1):
        text += f"{i}. *{note.title}*\n"
        text += f"   📄 {note.content[:100]}...\n"
        text += f"   👤 Автор: {note.owner_id} | 🔄 v{note.version}\n\n"

    safe_back = hashlib.md5(subject_name.encode()).hexdigest()[:8]
    user_state.set_data(user_id, f'subject_back_{safe_back}', subject_name)
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=f"disc_note_subj_back_{safe_back}")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def discipline_note_edit_choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    subject_name = user_state.get_data(user_id, 'disc_note_subject_name')

    user_group = GroupStorage.get_student_group(user_id)
    if not user_group:
        await query.edit_message_text("❌ Вы не подключены к группе")
        return

    result = NoteController.get_discipline_notes(user_id, user_group.id, user_group.id)

    if result['status'] != 'success' or not result['notes']:
        await query.edit_message_text(f"❌ Нет заметок для редактирования по предмету *{subject_name}*",
                                      parse_mode="Markdown")
        return

    keyboard = []
    for note in result['notes']:
        keyboard.append([InlineKeyboardButton(f"✏️ {note.title}", callback_data=f"disc_note_edit_pick_{note.id}")])
    safe_back = hashlib.md5(subject_name.encode()).hexdigest()[:8]
    user_state.set_data(user_id, f'subject_back_{safe_back}', subject_name)
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=f"disc_note_subj_back_{safe_back}")]]
    await query.edit_message_text(
        f"📚 *{subject_name}*\n\nВыберите заметку для редактирования:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def discipline_note_edit_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    note_id = int(query.data.replace("disc_note_edit_pick_", ""))
    user_state.set_data(user_id, 'disc_note_edit_id', note_id)

    keyboard = [
        [InlineKeyboardButton("📝 Заголовок", callback_data="disc_note_edit_title")],
        [InlineKeyboardButton("📄 Текст", callback_data="disc_note_edit_content")],
        [InlineKeyboardButton("🔙 Назад", callback_data="disc_note_edit")]
    ]
    await query.edit_message_text("Что вы хотите изменить?", reply_markup=InlineKeyboardMarkup(keyboard))


async def discipline_note_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    field = query.data.replace("disc_note_edit_", "")
    user_state.set_data(user_id, 'disc_note_edit_field', field)

    field_name = "заголовок" if field == "title" else "текст"
    await query.edit_message_text(f"Введите новый {field_name}:")
    return DISCIPLINE_NOTE_EDIT_VALUE


async def discipline_note_edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    note_id = user_state.get_data(user_id, 'disc_note_edit_id')
    field = user_state.get_data(user_id, 'disc_note_edit_field')
    new_value = update.message.text.strip()

    result = NoteController.update_discipline_note(user_id, note_id, {field: new_value})

    if result['status'] == 'success':
        await update.message.reply_text(f"✅ {field} успешно обновлен!")
    else:
        await update.message.reply_text(f"❌ {result['message']}")

    return ConversationHandler.END


async def discipline_note_delete_choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    subject_name = user_state.get_data(user_id, 'disc_note_subject_name')

    user_group = GroupStorage.get_student_group(user_id)
    if not user_group:
        await query.edit_message_text("❌ Вы не подключены к группе")
        return

    result = NoteController.get_discipline_notes(user_id, user_group.id, user_group.id)

    if result['status'] != 'success' or not result['notes']:
        await query.edit_message_text(f"❌ Нет заметок для удаления по предмету *{subject_name}*", parse_mode="Markdown")
        return

    keyboard = []
    for note in result['notes']:
        keyboard.append([InlineKeyboardButton(f"🗑️ {note.title}", callback_data=f"disc_note_delete_pick_{note.id}")])
    safe_back = hashlib.md5(subject_name.encode()).hexdigest()[:8]
    user_state.set_data(user_id, f'subject_back_{safe_back}', subject_name)
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=f"disc_note_subj_back_{safe_back}")]]
    await query.edit_message_text(
        f"📚 *{subject_name}*\n\nВыберите заметку для удаления:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def discipline_note_delete_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    subject_name = user_state.get_data(user_id, 'disc_note_subject_name')

    keyboard = [
        [InlineKeyboardButton("➕ Создать", callback_data="disc_note_create")],
        [InlineKeyboardButton("📖 Просмотреть", callback_data="disc_note_view")],
        [InlineKeyboardButton("✏️ Редактировать", callback_data="disc_note_edit")],
        [InlineKeyboardButton("🗑️ Удалить", callback_data="disc_note_delete")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_notes")]
    ]
    await query.edit_message_text(f"📚 *{subject_name}*\n\nВыберите действие:",
                                  reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def discipline_note_delete_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    note_id = int(query.data.replace("disc_note_delete_pick_", ""))
    user_state.set_data(user_id, 'disc_note_delete_id', note_id)

    keyboard = [
        [InlineKeyboardButton("✅ Да, удалить", callback_data="disc_note_delete_confirm")],
        [InlineKeyboardButton("❌ Нет, отменить", callback_data="disc_note_delete_cancel")]
    ]
    await query.edit_message_text("Вы уверены, что хотите удалить эту заметку?",
                                  reply_markup=InlineKeyboardMarkup(keyboard))


async def discipline_note_delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    note_id = user_state.get_data(user_id, 'disc_note_delete_id')
    subject_name = user_state.get_data(user_id, 'disc_note_subject_name')

    result = NoteController.delete_discipline_note(user_id, note_id)

    if result['status'] == 'success':
        await query.edit_message_text(f"✅ Заметка успешно удалена!")
    else:
        await query.edit_message_text(f"❌ {result['message']}")

    # Показать меню предмета
    keyboard = [
        [InlineKeyboardButton("➕ Создать", callback_data="disc_note_create")],
        [InlineKeyboardButton("📖 Просмотреть", callback_data="disc_note_view")],
        [InlineKeyboardButton("✏️ Редактировать", callback_data="disc_note_edit")],
        [InlineKeyboardButton("🗑️ Удалить", callback_data="disc_note_delete")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_notes")]
    ]
    await query.edit_message_text(f"📚 *{subject_name}*\n\nВыберите действие:",
                                  reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def subject_chats_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Мои чаты", callback_data="chats_list")],
        [InlineKeyboardButton("➕ Создать чат", callback_data="chats_create")],
        [InlineKeyboardButton("🔗 Привязать Telegram чат", callback_data="chats_link")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("💬 *Управление предметными чатами*\n\nВыберите действие:",
                                    reply_markup=reply_markup, parse_mode="Markdown")


async def chats_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    user_group = GroupStorage.get_student_group(user_id)
    if not user_group:
        await query.edit_message_text("❌ Вы не подключены к академической группе")
        return

    result = GroupController.get_user_subject_chats(user_id)

    if result['status'] != 'success' or not result['chats']:
        await query.edit_message_text("❌ Нет предметных чатов для вашей группы")
        return

    text = f"📋 *Предметные чаты для группы {user_group.number}*\n\n"
    for chat in result['chats']:
        tg_status = "✅ привязан" if chat['has_telegram'] else "❌ не привязан"
        text += f"📌 *{chat['name']}*\n"
        text += f"   ID: {chat['id']}\n"
        text += f"   Telegram: {tg_status}\n\n"

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="chats_back")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def chats_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    user_group = GroupStorage.get_student_group(user_id)
    if not user_group:
        await query.edit_message_text("❌ Вы не подключены к академической группе")
        return

    entries = ScheduleController.get_schedule_entries(user_id)
    subjects = set()
    for entry in entries:
        subject_name = entry.subject.split('(')[0].strip()
        subjects.add(subject_name)

    if not subjects:
        await query.edit_message_text("❌ Нет предметов в расписании. Сначала синхронизируйте расписание.")
        return

    keyboard = []
    for subject in sorted(subjects):
        # Кодируем название предмета для callback_data
        safe_subject = hashlib.md5(subject.encode()).hexdigest()[:8]
        user_state.set_data(user_id, f'create_chat_subject_{safe_subject}', subject)
        keyboard.append([InlineKeyboardButton(subject, callback_data=f"create_chat_{safe_subject}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="chats_back")])

    await query.edit_message_text(
        "📚 Выберите предмет для создания чата:\n\nЧат будет создан в формате [Номер_группы] Название_предмета",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def create_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    safe_subject = query.data.replace("create_chat_", "")
    subject = user_state.get_data(user_id, f'create_chat_subject_{safe_subject}', "Unknown")

    user_group = GroupStorage.get_student_group(user_id)
    if not user_group:
        await query.edit_message_text("❌ Вы не подключены к академической группе")
        return

    result = GroupController.create_subject_chat(user_id, subject, user_group.id)

    if result['status'] == 'success':
        await query.edit_message_text(
            f"✅ Чат создан!\n\n"
            f"📌 Название: {result['chat']['name']}\n"
            f"🆔 ID: {result['chat']['id']}\n\n"
            f"Теперь вы можете привязать к нему Telegram-чат"
        )
    else:
        await query.edit_message_text(f"❌ {result['message']}")


async def chats_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    user_group = GroupStorage.get_student_group(user_id)
    if not user_group:
        await query.edit_message_text("❌ Вы не подключены к академической группе")
        return

    result = GroupController.get_user_subject_chats(user_id)

    if result['status'] != 'success' or not result['chats']:
        await query.edit_message_text("❌ Нет предметных чатов для привязки. Сначала создайте чат.")
        return

    keyboard = []
    for chat in result['chats']:
        if not chat['has_telegram']:
            keyboard.append([InlineKeyboardButton(chat['name'], callback_data=f"link_chat_{chat['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="chats_back")])

    if len(keyboard) == 1:
        await query.edit_message_text("❌ Нет непривязанных чатов. Все чаты уже имеют Telegram-чат.")
        return

    await query.edit_message_text(
        "🔗 *Выберите чат для привязки Telegram-чата:*\n\n"
        "После выбора отправьте ID Telegram-чата\n"
        "(например: -1001234567890)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return "awaiting_chat_id"


async def link_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    chat_group_id = int(query.data.replace("link_chat_", ""))

    user_state.set_data(user_id, 'linking_chat_id', chat_group_id)
    await query.edit_message_text(
        "📨 *Введите ID Telegram-чата*\n\n"
        "Как получить ID:\n"
        "1. Добавьте бота в чат\n"
        "2. Отправьте любое сообщение\n"
        "3. Перейдите на https://api.telegram.org/bot<TOKEN>/getUpdates\n"
        "4. Найдите 'chat':{'id': ...}\n\n"
        "Отправьте ID в ответном сообщении:",
        parse_mode="Markdown"
    )
    return "awaiting_chat_id"


async def receive_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id_input = update.message.text.strip()
    linking_id = user_state.get_data(user_id, 'linking_chat_id')

    try:
        tg_chat_id = int(chat_id_input)
    except ValueError:
        await update.message.reply_text("❌ Неверный формат. Введите числовой ID (например: -1001234567890)")
        return "awaiting_chat_id"

    result = GroupController.link_telegram_chat_to_subject_group(linking_id, str(tg_chat_id))

    if result['status'] == 'success':
        await update.message.reply_text(f"✅ {result['message']}")
    else:
        await update.message.reply_text(f"❌ {result['message']}")

    user_state.set_data(user_id, 'linking_chat_id', None)
    return ConversationHandler.END


async def chats_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("📋 Мои чаты", callback_data="chats_list")],
        [InlineKeyboardButton("➕ Создать чат", callback_data="chats_create")],
        [InlineKeyboardButton("🔗 Привязать Telegram чат", callback_data="chats_link")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    await query.edit_message_text("💬 *Управление предметными чатами*\n\nВыберите действие:",
                                  reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [KeyboardButton("👥 Подключиться к группе")],
        [KeyboardButton("📚 Расписание"), KeyboardButton("📝 Домашнее задание")],
        [KeyboardButton("📋 Очередь"), KeyboardButton("🔔 Уведомления")],
        [KeyboardButton("📒 Заметки"), KeyboardButton("💬 Предметные чаты")],
        [KeyboardButton("📧 Привязать Gmail")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await query.edit_message_text("Добро пожаловать в бота для планирования студента! 🎓\nВыберите действие:",
                                  reply_markup=reply_markup)


async def notes_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "my_notes":
        keyboard = [
            [InlineKeyboardButton("➕ Создать", callback_data="note_create")],
            [InlineKeyboardButton("📖 Просмотреть", callback_data="note_view")],
            [InlineKeyboardButton("✏️ Редактировать", callback_data="note_edit")],
            [InlineKeyboardButton("🗑️ Удалить", callback_data="note_delete")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_notes")]
        ]
        await query.edit_message_text(
            "📝 *Личные заметки*\n\nВыберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data == "subject_notes":
        user_group = GroupStorage.get_student_group(user_id)
        if not user_group:
            await query.edit_message_text("❌ Вы не подключены к группе")
            return

        entries = ScheduleController.get_schedule_entries(user_id)
        subjects = {}
        for entry in entries:
            subject_name = entry.subject.split('(')[0].strip()
            subjects[subject_name] = subject_name

        if not subjects:
            await query.edit_message_text("❌ Нет предметов в расписании")
            return

        keyboard = []
        for subject_name in sorted(subjects.keys()):
            safe_subject = hashlib.md5(subject_name.encode()).hexdigest()[:8]
            user_state.set_data(user_id, f'subject_{safe_subject}', subject_name)
            keyboard.append([InlineKeyboardButton(subject_name, callback_data=f"subject_note_{safe_subject}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_notes")])

        await query.edit_message_text(
            "📚 *Заметки по предмету*\n\nВыберите предмет:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


async def subject_notes_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    subject_key = query.data.replace("subject_note_", "")
    subject = user_state.get_data(user_id, f'subject_{subject_key}', "Unknown")

    user_group = GroupStorage.get_student_group(user_id)
    if not user_group:
        await query.edit_message_text("❌ Вы не подключены к группе")
        return

    result = NoteController.get_discipline_notes(user_id, user_group.id, user_group.id)

    if result['status'] != 'success' or not result['notes']:
        await query.edit_message_text(f"❌ Нет общих заметок по предмету *{subject}*", parse_mode="Markdown")
        return

    text = f"📚 *Заметки по предмету: {subject}*\n\n"
    for note in result['notes']:
        text += f"▪️ *{note.title}*\n"
        text += f"   {note.content[:100]}...\n"
        text += f"   👤 Автор: {note.owner_id} | 🔄 v{note.version}\n\n"

    keyboard = [[InlineKeyboardButton("🔙 Назад к предметам", callback_data="subject_notes")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def discipline_note_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    subject_key = query.data.replace("subject_note_", "")
    subject = user_state.get_data(user_id, f'subject_{subject_key}', "Unknown")

    user_state.set_data(user_id, 'disc_note_subject', subject)
    user_state.set_data(user_id, 'disc_note_subject_name', subject)

    keyboard = [
        [InlineKeyboardButton("➕ Создать", callback_data="disc_note_create")],
        [InlineKeyboardButton("📖 Просмотреть", callback_data="disc_note_view")],
        [InlineKeyboardButton("✏️ Редактировать", callback_data="disc_note_edit")],
        [InlineKeyboardButton("🗑️ Удалить", callback_data="disc_note_delete")],
        [InlineKeyboardButton("🔙 Назад", callback_data="subject_notes")]
    ]
    await query.edit_message_text(
        f"📚 *{subject}*\n\nВыберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def discipline_note_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Введите заголовок заметки:")
    return DISCIPLINE_NOTE_ENTER_TITLE


async def discipline_note_enter_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state.set_data(user_id, 'disc_note_title', update.message.text.strip())
    await update.message.reply_text("Введите текст заметки:")
    return DISCIPLINE_NOTE_ENTER_CONTENT


async def discipline_note_enter_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    title = user_state.get_data(user_id, 'disc_note_title')
    content = update.message.text.strip()
    subject = user_state.get_data(user_id, 'disc_note_subject')

    user_group = GroupStorage.get_student_group(user_id)

    result = NoteController.create_discipline_note(
        user_id=user_id,
        group_id=user_group.id,
        title=title,
        content=content,
        subject_name=subject
    )

    if result['status'] == 'success':
        await update.message.reply_text(f"✅ Общая заметка «{title}» сохранена для дисциплины {subject}!")
    else:
        await update.message.reply_text(f"❌ {result['message']}")
    return ConversationHandler.END


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link_gmail", link_gmail))

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
        },
        fallbacks=[],
    )

    schedule_edit_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(schedule_edit, pattern="^schedule_edit$")],
        states={
            CHOOSE_DAY: [CallbackQueryHandler(schedule_edit_day, pattern="^edit_day_")],
            CHOOSE_ENTRY: [CallbackQueryHandler(edit_entry, pattern="^edit_entry_")],
            ENTER_FIELD_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_field_value)],
        },
        fallbacks=[],
    )

    schedule_delete_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(schedule_delete, pattern="^schedule_delete$")],
        states={
            CHOOSE_DAY: [CallbackQueryHandler(schedule_delete_day, pattern="^delete_day_")],
            CHOOSE_ENTRY: [CallbackQueryHandler(delete_entry, pattern="^delete_entry_")],
            CONFIRM_DELETE: [CallbackQueryHandler(confirm_delete, pattern="^confirm_schedule_delete_")],
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

    note_create_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(note_create, pattern="^note_create$")],
        states={
            NOTE_ENTER_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, note_enter_title)],
            NOTE_ENTER_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, note_enter_content)],
        },
        fallbacks=[],
    )

    note_edit_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(note_edit, pattern="^note_edit$")],
        states={
            NOTE_CHOOSE: [CallbackQueryHandler(note_edit_pick, pattern="^note_edit_pick_")],
            NOTE_EDIT_FIELD: [CallbackQueryHandler(note_edit_field, pattern="^note_field_")],
            NOTE_ENTER_NEW_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, note_enter_new_value)],
        },
        fallbacks=[],
    )

    note_delete_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(note_delete, pattern="^note_delete$")],
        states={
            NOTE_CHOOSE: [
                CallbackQueryHandler(note_delete_pick, pattern="^note_delete_pick_"),
                CallbackQueryHandler(note_delete_confirm, pattern="^note_delete_confirm_"),
            ],
        },
        fallbacks=[],
    )

    discipline_note_create_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(discipline_note_create, pattern="^disc_note_create$")],
        states={
            DISCIPLINE_NOTE_ENTER_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, discipline_note_enter_title)],
            DISCIPLINE_NOTE_ENTER_CONTENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, discipline_note_enter_content)],
        },
        fallbacks=[],
    )

    discipline_note_edit_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(discipline_note_edit_field,
                                           pattern="^disc_note_edit_title$|^disc_note_edit_content$")],
        states={
            DISCIPLINE_NOTE_EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, discipline_note_edit_value)],
        },
        fallbacks=[],
    )

    link_chat_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(link_chat_handler, pattern="^link_chat_")],
        states={
            "awaiting_chat_id": [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_chat_id)],
        },
        fallbacks=[],
    )

    group_broadcast_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(group_broadcast_button, pattern="^group_broadcast$")],
        states={
            BROADCAST_ENTER_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_enter_message)
            ],
            BROADCAST_CONFIRM: [
                CallbackQueryHandler(broadcast_confirm, pattern="^broadcast_confirm_")
            ],
        },
        fallbacks=[],
    )

    app.add_handler(group_broadcast_handler)

    app.add_handler(link_chat_conv_handler)

    app.add_handler(discipline_note_create_handler)
    app.add_handler(discipline_note_edit_handler)
    app.add_handler(CallbackQueryHandler(discipline_note_choose_subject, pattern="^disc_note_subj_"))

    app.add_handler(note_create_handler)
    app.add_handler(note_edit_handler)
    app.add_handler(note_delete_handler)
    app.add_handler(CallbackQueryHandler(note_view, pattern="^note_view$"))
    app.add_handler(group_handler)
    app.add_handler(schedule_handler)
    app.add_handler(schedule_edit_handler)
    app.add_handler(schedule_delete_handler)
    app.add_handler(homework_handler)
    app.add_handler(homework_edit_handler)
    app.add_handler(notification_handler)

    app.add_handler(CallbackQueryHandler(discipline_note_back, pattern="^disc_note_subj_back_"))
    app.add_handler(CallbackQueryHandler(notes_choice_handler, pattern="^(my_notes|subject_notes)$"))
    app.add_handler(CallbackQueryHandler(discipline_note_menu, pattern="^subject_note_"))
    app.add_handler(CallbackQueryHandler(back_to_notes_menu, pattern="^back_to_notes$"))

    app.add_handler(CallbackQueryHandler(schedule_view, pattern="^schedule_view$"))
    app.add_handler(CallbackQueryHandler(view_schedule_day, pattern="^view_day_"))
    app.add_handler(CallbackQueryHandler(schedule_changes, pattern="^schedule_changes$"))

    app.add_handler(CallbackQueryHandler(hw_view, pattern="^hw_view$"))
    app.add_handler(CallbackQueryHandler(hw_mark, pattern="^hw_mark$"))
    app.add_handler(CallbackQueryHandler(mark_task, pattern="^mark_task_"))
    app.add_handler(CallbackQueryHandler(confirm_mark, pattern="^confirm_mark_"))
    app.add_handler(CallbackQueryHandler(hw_delete, pattern="^hw_delete$"))
    app.add_handler(CallbackQueryHandler(delete_hw, pattern="^delete_hw_"))
    app.add_handler(CallbackQueryHandler(confirm_delete_hw, pattern="^confirm_delete_hw_"))
    app.add_handler(CallbackQueryHandler(hw_completed, pattern="^hw_completed$"))

    app.add_handler(CallbackQueryHandler(discipline_note_menu, pattern="^subject_note_"))
    app.add_handler(CallbackQueryHandler(discipline_note_view, pattern="^disc_note_view$"))
    app.add_handler(CallbackQueryHandler(discipline_note_edit_choose, pattern="^disc_note_edit$"))
    app.add_handler(CallbackQueryHandler(discipline_note_edit_pick, pattern="^disc_note_edit_pick_"))
    app.add_handler(CallbackQueryHandler(discipline_note_delete_choose, pattern="^disc_note_delete$"))
    app.add_handler(CallbackQueryHandler(discipline_note_delete_pick, pattern="^disc_note_delete_pick_"))
    app.add_handler(CallbackQueryHandler(discipline_note_delete_confirm, pattern="^disc_note_delete_confirm$"))
    app.add_handler(CallbackQueryHandler(discipline_note_delete_cancel, pattern="^disc_note_delete_cancel$"))
    app.add_handler(CallbackQueryHandler(chats_list, pattern="^chats_list$"))
    app.add_handler(CallbackQueryHandler(chats_create, pattern="^chats_create$"))
    app.add_handler(CallbackQueryHandler(chats_link, pattern="^chats_link$"))
    app.add_handler(CallbackQueryHandler(create_chat_handler, pattern="^create_chat_"))
    app.add_handler(CallbackQueryHandler(chats_back, pattern="^chats_back$"))
    app.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))
    app.add_handler(CallbackQueryHandler(subject_chats_menu, pattern="^subject_chats$"))
    app.add_handler(CallbackQueryHandler(show_feed_filter, pattern="^feed_filter_"))
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
