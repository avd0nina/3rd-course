from database import get_db, Student, Group, ScheduleEntry, HomeworkTask, QueueEntry, DeadlinesNotificationSettings, QueueNotificationSettings

class GroupStorage:
    @staticmethod
    def create_group_if_not_exists(group_number: str) -> Group:
        db = get_db()
        try:
            group = db.query(Group).filter(Group.number == group_number).first()
            if not group:
                group = Group(number=group_number)
                db.add(group)
                db.commit()
                db.refresh(group)
            group_id = group.id
            group_number_result = group.number
        finally:
            db.close()
        
        # Return a fresh instance with the group data
        db2 = get_db()
        result = db2.query(Group).filter(Group.id == group_id).first()
        db2.close()
        return result

    @staticmethod
    def add_student_to_group(user_id: int, group_id: int) -> bool:
        db = get_db()
        try:
            student = db.query(Student).filter(Student.user_id == user_id).first()
            if not student:
                student = Student(user_id=user_id, group_id=group_id)
                db.add(student)
            else:
                student.group_id = group_id
            db.commit()
            return True
        finally:
            db.close()

    @staticmethod
    def is_student_in_any_group(user_id: int) -> bool:
        db = get_db()
        try:
            student = db.query(Student).filter(Student.user_id == user_id).first()
            result = student is not None and student.group_id is not None
            return result
        finally:
            db.close()

    @staticmethod
    def get_student_group(user_id: int) -> Group:
        db = get_db()
        try:
            student = db.query(Student).filter(Student.user_id == user_id).first()
            if student and student.group_id:
                group = db.query(Group).filter(Group.id == student.group_id).first()
                return group
            return None
        finally:
            db.close()

class ScheduleStorage:
    @staticmethod
    def save_schedule_entry(user_id: int, group_id: int, day: str, subject: str, start_time: str, end_time: str) -> ScheduleEntry:
        db = get_db()
        entry = ScheduleEntry(user_id=user_id, group_id=group_id, day_of_week=day, subject=subject, start_time=start_time, end_time=end_time)
        db.add(entry)
        db.commit()
        db.refresh(entry)
        db.close()
        return entry

    @staticmethod
    def get_schedule_entries(user_id: int, day: str = None) -> list:
        db = get_db()
        query = db.query(ScheduleEntry).filter(ScheduleEntry.user_id == user_id)
        if day:
            query = query.filter(ScheduleEntry.day_of_week == day)
        entries = query.all()
        db.close()
        return entries

    @staticmethod
    def has_time_conflict(user_id: int, exclude_entry_id: int, day: str, start_time: str, end_time: str) -> bool:
        db = get_db()
        entries = db.query(ScheduleEntry).filter(
            ScheduleEntry.user_id == user_id,
            ScheduleEntry.day_of_week == day,
            ScheduleEntry.id != exclude_entry_id
        ).all()
        
        def time_overlap(s1, e1, s2, e2):
            return s1 < e2 and s2 < e1
        
        for entry in entries:
            if time_overlap(start_time, end_time, entry.start_time, entry.end_time):
                db.close()
                return True
        db.close()
        return False

    @staticmethod
    def update_entry_in_database(entry_id: int, updates: dict) -> bool:
        db = get_db()
        entry = db.query(ScheduleEntry).filter(ScheduleEntry.id == entry_id).first()
        if entry:
            for key, value in updates.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
            db.commit()
            db.close()
            return True
        db.close()
        return False

    @staticmethod
    def delete_entry_from_database(entry_id: int) -> bool:
        db = get_db()
        entry = db.query(ScheduleEntry).filter(ScheduleEntry.id == entry_id).first()
        if entry:
            db.delete(entry)
            db.commit()
            db.close()
            return True
        db.close()
        return False

class HomeworkStorage:
    @staticmethod
    def create_homework_task(user_id: int, group_id: int, subject: str, description: str, deadline: str) -> HomeworkTask:
        db = get_db()
        task = HomeworkTask(user_id=user_id, group_id=group_id, subject=subject, description=description, deadline=deadline)
        db.add(task)
        db.commit()
        db.refresh(task)
        db.close()
        return task

    @staticmethod
    def get_active_tasks(user_id: int, subject: str = None) -> list:
        db = get_db()
        query = db.query(HomeworkTask).filter(HomeworkTask.user_id == user_id, HomeworkTask.is_done == False)
        if subject:
            query = query.filter(HomeworkTask.subject == subject)
        tasks = query.all()
        db.close()
        return tasks

    @staticmethod
    def get_active_subjects(user_id: int) -> list:
        db = get_db()
        subjects = db.query(HomeworkTask.subject).filter(HomeworkTask.user_id == user_id, HomeworkTask.is_done == False).distinct().all()
        result = [s[0] for s in subjects]
        db.close()
        return result

    @staticmethod
    def get_completed_tasks(user_id: int) -> list:
        db = get_db()
        tasks = db.query(HomeworkTask).filter(HomeworkTask.user_id == user_id, HomeworkTask.is_done == True).all()
        db.close()
        return tasks

    @staticmethod
    def update_task(task_id: int, updates: dict) -> bool:
        db = get_db()
        task = db.query(HomeworkTask).filter(HomeworkTask.id == task_id).first()
        if task:
            for key, value in updates.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            db.commit()
            db.close()
            return True
        db.close()
        return False

    @staticmethod
    def delete_task(task_id: int) -> bool:
        db = get_db()
        task = db.query(HomeworkTask).filter(HomeworkTask.id == task_id).first()
        if task:
            db.delete(task)
            db.commit()
            db.close()
            return True
        db.close()
        return False

    @staticmethod
    def mark_as_completed(task_id: int) -> bool:
        return HomeworkStorage.update_task(task_id, {'is_done': True})

class QueueStorage:
    @staticmethod
    def find_free_position(date: str, subject: str) -> int:
        db = get_db()
        entries = db.query(QueueEntry).filter(QueueEntry.date == date, QueueEntry.subject == subject).all()
        positions = [e.position for e in entries]
        position = 1
        while position in positions:
            position += 1
        db.close()
        return position

    @staticmethod
    def is_queue_open(date: str, subject: str) -> bool:
        db = get_db()
        entry = db.query(QueueEntry).filter(QueueEntry.date == date, QueueEntry.subject == subject, QueueEntry.is_open == True).first()
        result = entry is not None
        db.close()
        return result

    @staticmethod
    def is_user_in_queue(user_id: int, date: str, subject: str) -> bool:
        db = get_db()
        entry = db.query(QueueEntry).filter(QueueEntry.user_id == user_id, QueueEntry.date == date, QueueEntry.subject == subject).first()
        result = entry is not None
        db.close()
        return result

    @staticmethod
    def add_entry_to_database(user_id: int, date: str, subject: str, position: int) -> QueueEntry:
        db = get_db()
        entry = QueueEntry(user_id=user_id, date=date, subject=subject, position=position)
        db.add(entry)
        db.commit()
        db.refresh(entry)
        db.close()
        return entry

    @staticmethod
    def get_queue_entries(date: str, subject: str) -> list:
        db = get_db()
        entries = db.query(QueueEntry).filter(QueueEntry.date == date, QueueEntry.subject == subject).order_by(QueueEntry.position).all()
        db.close()
        return entries

    @staticmethod
    def get_available_subjects(date: str) -> list:
        db = get_db()
        subjects = db.query(QueueEntry.subject).filter(QueueEntry.date == date, QueueEntry.is_open == True).distinct().all()
        result = [s[0] for s in subjects]
        db.close()
        return result

    @staticmethod
    def get_user_queue_entry(user_id: int) -> QueueEntry:
        db = get_db()
        entry = db.query(QueueEntry).filter(QueueEntry.user_id == user_id).first()
        db.close()
        return entry

    @staticmethod
    def update_queue_entry(user_id: int, field: str, new_value: str) -> bool:
        db = get_db()
        entry = db.query(QueueEntry).filter(QueueEntry.user_id == user_id).first()
        if entry:
            if hasattr(entry, field):
                setattr(entry, field, new_value)
            db.commit()
            db.close()
            return True
        db.close()
        return False

class NotificationStorage:
    @staticmethod
    def get_notification_settings(user_id: int) -> DeadlinesNotificationSettings:
        db = get_db()
        try:
            settings = db.query(DeadlinesNotificationSettings).filter(DeadlinesNotificationSettings.user_id == user_id).first()
            if not settings:
                settings = DeadlinesNotificationSettings(user_id=user_id)
                db.add(settings)
                db.commit()
            enabled = settings.enabled
            reminder_hours = settings.reminder_hours_before
            
            class SettingsResult:
                def __init__(self, enabled, reminder_hours):
                    self.enabled = enabled
                    self.reminder_hours_before = reminder_hours
            
            return SettingsResult(enabled, reminder_hours)
        finally:
            db.close()

    @staticmethod
    def save_notification_settings(user_id: int, enabled: bool, reminder_hours: int = 24) -> bool:
        db = get_db()
        try:
            settings = db.query(DeadlinesNotificationSettings).filter(DeadlinesNotificationSettings.user_id == user_id).first()
            if not settings:
                settings = DeadlinesNotificationSettings(user_id=user_id)
                db.add(settings)
            settings.enabled = enabled
            settings.reminder_hours_before = reminder_hours
            db.commit()
            return True
        finally:
            db.close()

    @staticmethod
    def get_queue_notification_settings(user_id: int) -> QueueNotificationSettings:
        db = get_db()
        try:
            settings = db.query(QueueNotificationSettings).filter(QueueNotificationSettings.user_id == user_id).first()
            if not settings:
                settings = QueueNotificationSettings(user_id=user_id)
                db.add(settings)
                db.commit()
            enabled = settings.enabled
            
            class SettingsResult:
                def __init__(self, enabled):
                    self.enabled = enabled
            
            return SettingsResult(enabled)
        finally:
            db.close()

    @staticmethod
    def save_queue_notification_settings(user_id: int, enabled: bool) -> bool:
        db = get_db()
        try:
            settings = db.query(QueueNotificationSettings).filter(QueueNotificationSettings.user_id == user_id).first()
            if not settings:
                settings = QueueNotificationSettings(user_id=user_id)
                db.add(settings)
            settings.enabled = enabled
            db.commit()
            return True
        finally:
            db.close()
