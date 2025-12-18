from storage import GroupStorage, ScheduleStorage, HomeworkStorage, QueueStorage, NotificationStorage

class GroupController:
    @staticmethod
    def connect_student_to_group(user_id: int, group_number: str) -> bool:
        group = GroupStorage.create_group_if_not_exists(group_number)
        return GroupStorage.add_student_to_group(user_id, group.id)

class ScheduleController:
    @staticmethod
    def create_schedule_entry(user_id: int, day: str, subject: str, time_range: str) -> dict:
        try:
            start_time, end_time = time_range.split('-')
            start_time = start_time.strip()
            end_time = end_time.strip()
            
            # Проверка что время конца больше времени начала
            try:
                start_h, start_m = map(int, start_time.split(':'))
                end_h, end_m = map(int, end_time.split(':'))
                start_total = start_h * 60 + start_m
                end_total = end_h * 60 + end_m
                if end_total <= start_total:
                    return {'status': 'error', 'message': 'Время окончания должно быть больше времени начала'}
            except ValueError:
                return {'status': 'error', 'message': 'Неверный формат времени. Используйте ЧЧ:ММ'}
            
            if not ScheduleStorage.has_time_conflict(user_id, -1, day, start_time, end_time):
                group = GroupStorage.get_student_group(user_id)
                if group:
                    entry = ScheduleStorage.save_schedule_entry(user_id, group.id, day, subject, start_time, end_time)
                    return {'status': 'success', 'entry': entry}
            return {'status': 'error', 'message': 'Конфликт времени'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_schedule_entries(user_id: int, day: str = None) -> list:
        return ScheduleStorage.get_schedule_entries(user_id, day)

    @staticmethod
    def update_schedule_entry(user_id: int, entry_id: int, updates: dict) -> bool:
        if 'start_time' in updates or 'end_time' in updates:
            entry = ScheduleStorage.get_schedule_entries(user_id)
            entry_obj = next((e for e in entry if e.id == entry_id), None)
            if entry_obj:
                start = updates.get('start_time', entry_obj.start_time)
                end = updates.get('end_time', entry_obj.end_time)
                if ScheduleStorage.has_time_conflict(user_id, entry_id, entry_obj.day_of_week, start, end):
                    return False
        return ScheduleStorage.update_entry_in_database(entry_id, updates)

    @staticmethod
    def delete_schedule_entry(user_id: int, entry_id: int) -> bool:
        return ScheduleStorage.delete_entry_from_database(entry_id)

    @staticmethod
    def display_schedule(user_id: int, day: str = None) -> str:
        entries = ScheduleController.get_schedule_entries(user_id, day)
        if not entries:
            return "❌ Расписание не найдено"
        result = "📚 Ваше расписание\n\n"
        for entry in entries:
            result += f"📅 {entry.day_of_week}\n"
            result += f"📖 {entry.subject}\n"
            result += f"⏰ {entry.start_time} - {entry.end_time}\n\n"
        return result

class NotificationController:
    @staticmethod
    def get_notification_settings(user_id: int) -> dict:
        settings = NotificationStorage.get_notification_settings(user_id)
        return {
            'enabled': settings.enabled,
            'reminder_hours': settings.reminder_hours_before
        }

    @staticmethod
    def update_notification_settings(user_id: int, enabled: bool, reminder_hours: int = 24) -> bool:
        return NotificationStorage.save_notification_settings(user_id, enabled, reminder_hours)

    @staticmethod
    def get_queue_notification_settings(user_id: int) -> dict:
        settings = NotificationStorage.get_queue_notification_settings(user_id)
        return {'enabled': settings.enabled}

    @staticmethod
    def save_queue_notification_settings(user_id: int, enabled: bool) -> bool:
        return NotificationStorage.save_queue_notification_settings(user_id, enabled)

class HomeworkController:
    @staticmethod
    def write_down_homework(user_id: int, subject: str, description: str, deadline: str) -> dict:
        try:
            group = GroupStorage.get_student_group(user_id)
            if not group:
                return {'status': 'error', 'message': 'Вы не подключены к группе'}
            task = HomeworkStorage.create_homework_task(user_id, group.id, subject, description, deadline)
            return {'status': 'success', 'task': task}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_active_tasks(user_id: int, subject: str = None) -> list:
        return HomeworkStorage.get_active_tasks(user_id, subject)

    @staticmethod
    def get_active_subjects(user_id: int) -> list:
        return HomeworkStorage.get_active_subjects(user_id)

    @staticmethod
    def display_active_homework(user_id: int, filter_type: str = "all", subject: str = None) -> str:
        tasks = HomeworkController.get_active_tasks(user_id, subject if filter_type == "subject" else None)
        if not tasks:
            return "❌ Активное домашнее задание не найдено" if filter_type == "all" else f"❌ Домашнее задание для {subject} не найдено"
        result = "📝 Активное домашнее задание\n\n"
        for task in tasks:
            result += f"📌 {task.subject}\n"
            result += f"📄 {task.description}\n"
            result += f"⏳ Срок: {task.deadline}\n\n"
        return result

    @staticmethod
    def get_completed_tasks(user_id: int) -> list:
        return HomeworkStorage.get_completed_tasks(user_id)

    @staticmethod
    def display_completed_homework(user_id: int) -> str:
        tasks = HomeworkController.get_completed_tasks(user_id)
        if not tasks:
            return "❌ Выполненное домашнее задание не найдено"
        result = "✅ Выполненное домашнее задание\n\n"
        for task in tasks:
            result += f"✓ {task.subject}\n"
            result += f"  {task.description}\n\n"
        return result

    @staticmethod
    def mark_homework_as_completed(user_id: int, task_id: int) -> bool:
        return HomeworkStorage.mark_as_completed(task_id)

    @staticmethod
    def update_homework_entry(user_id: int, task_id: int, updates: dict) -> bool:
        return HomeworkStorage.update_task(task_id, updates)

    @staticmethod
    def delete_homework_entry(user_id: int, task_id: int) -> bool:
        return HomeworkStorage.delete_task(task_id)

    @staticmethod
    def get_active_tasks_for_marking(user_id: int) -> list:
        return HomeworkController.get_active_tasks(user_id)

class QueueController:
    @staticmethod
    def take_place_in_queue(user_id: int, date: str, subject: str) -> dict:
        try:
            if not QueueStorage.is_queue_open(date, subject):
                return {'status': 'error', 'message': 'Очередь закрыта'}
            if QueueStorage.is_user_in_queue(user_id, date, subject):
                return {'status': 'error', 'message': 'Вы уже в очереди'}
            position = QueueStorage.find_free_position(date, subject)
            entry = QueueStorage.add_entry_to_database(user_id, date, subject, position)
            return {'status': 'success', 'entry': entry}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_queue_entries(date: str, subject: str) -> list:
        return QueueStorage.get_queue_entries(date, subject)

    @staticmethod
    def display_queue(user_id: int, date: str, subject: str) -> str:
        entries = QueueController.get_queue_entries(date, subject)
        if not entries:
            return f"❌ Очередь для {subject} на {date} не найдена"
        result = f"📋 Очередь для {subject} на {date}\n\n"
        for entry in entries:
            user_marker = "👤 Это вы" if entry.user_id == user_id else ""
            result += f"{entry.position}. Пользователь {user_marker}\n"
        return result

    @staticmethod
    def get_available_subjects(date: str) -> list:
        return QueueStorage.get_available_subjects(date)

    @staticmethod
    def get_user_queue_entry(user_id: int) -> dict:
        entry = QueueStorage.get_user_queue_entry(user_id)
        if entry:
            return {
                'date': entry.date,
                'subject': entry.subject,
                'position': entry.position
            }
        return None

    @staticmethod
    def update_queue_entry(user_id: int, field: str, new_value: str) -> bool:
        return QueueStorage.update_queue_entry(user_id, field, new_value)
