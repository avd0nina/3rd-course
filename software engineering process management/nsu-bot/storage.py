from database import get_db, Student, Group, ScheduleEntry, HomeworkTask, QueueEntry, DeadlinesNotificationSettings, QueueNotificationSettings, ScheduleDiff, ScheduleUpdatedEvent, EventLog, GroupChatMembership, Note

class GroupStorage:
    @staticmethod
    def create_group_if_not_exists(group_number: str, group_type: str = 'academic') -> Group:
        db = get_db()
        try:
            group = db.query(Group).filter(Group.number == group_number).first()
            if not group:
                group = Group(number=group_number, group_type=group_type)
                db.add(group)
                db.commit()
                db.refresh(group)
            group_id = group.id
            group_number_result = group.number
        finally:
            db.close()
        
        db2 = get_db()
        result = db2.query(Group).filter(Group.id == group_id).first()
        db2.close()
        return result

    @staticmethod
    def get_groups_by_type(group_type: str) -> list:
        db = get_db()
        try:
            groups = db.query(Group).filter(Group.group_type == group_type).all()
            return groups
        finally:
            db.close()

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

    @staticmethod
    def get_group_by_id(group_id: int) -> Group:
        db = get_db()
        try:
            group = db.query(Group).filter(Group.id == group_id).first()
            return group
        finally:
            db.close()

    @staticmethod
    def save_telegram_chat_id(group_id: int, telegram_chat_id: str) -> bool:
        """E3: Save Telegram chat ID for a group"""
        db = get_db()
        try:
            group = db.query(Group).filter(Group.id == group_id).first()
            if group:
                group.telegram_chat_id = telegram_chat_id
                db.commit()
                return True
            return False
        finally:
            db.close()

    @staticmethod
    def get_group_by_telegram_chat_id(telegram_chat_id: str) -> Group:
        """E3: Get group by Telegram chat ID"""
        db = get_db()
        try:
            group = db.query(Group).filter(Group.telegram_chat_id == telegram_chat_id).first()
            return group
        finally:
            db.close()

    @staticmethod
    def get_group_members(group_id: int) -> list:
        """E4: Get all members of a group"""
        db = get_db()
        try:
            students = db.query(Student).filter(Student.group_id == group_id).all()
            return students
        finally:
            db.close()

    @staticmethod
    def save_chat_membership(user_id: int, chat_group_id: int, status: str = 'invited') -> bool:
        """E4: Record that user has been invited to chat"""
        db = get_db()
        try:
            # Check if already exists
            existing = db.query(GroupChatMembership).filter(
                GroupChatMembership.user_id == user_id,
                GroupChatMembership.chat_group_id == chat_group_id
            ).first()
            
            if existing:
                existing.status = status
                db.commit()
                return True
            
            # Create new membership
            membership = GroupChatMembership(user_id=user_id, chat_group_id=chat_group_id, status=status)
            db.add(membership)
            db.commit()
            return True
        except Exception:
            return False
        finally:
            db.close()

    @staticmethod
    def get_chat_members(chat_group_id: int) -> list:
        """E4: Get all users already invited to a chat"""
        db = get_db()
        try:
            memberships = db.query(GroupChatMembership).filter(
                GroupChatMembership.chat_group_id == chat_group_id,
                GroupChatMembership.status == 'invited'
            ).all()
            return [m.user_id for m in memberships]
        finally:
            db.close()

    @staticmethod
    def save_group_creator(group_id: int, user_id: int) -> bool:
        """E5: Record the user who created a subject chat"""
        db = get_db()
        try:
            group = db.query(Group).filter(Group.id == group_id).first()
            if group:
                group.creator_user_id = user_id
                db.commit()
                return True
            return False
        except Exception:
            return False
        finally:
            db.close()

    @staticmethod
    def get_group_creator(group_id: int) -> int:
        """E5: Get the user ID of who created this group"""
        db = get_db()
        try:
            group = db.query(Group).filter(Group.id == group_id).first()
            if group:
                return group.creator_user_id
            return None
        finally:
            db.close()

    @staticmethod
    def archive_group(group_id: int) -> bool:
        """E5: Archive a subject chat group"""
        db = get_db()
        try:
            group = db.query(Group).filter(Group.id == group_id).first()
            if group:
                group.status = 'archived'
                db.commit()
                return True
            return False
        except Exception:
            return False
        finally:
            db.close()

    @staticmethod
    def unarchive_group(group_id: int) -> bool:
        """E5: Restore an archived subject chat group"""
        db = get_db()
        try:
            group = db.query(Group).filter(Group.id == group_id).first()
            if group:
                group.status = 'active'
                db.commit()
                return True
            return False
        except Exception:
            return False
        finally:
            db.close()

    @staticmethod
    def get_group_status(group_id: int) -> str:
        """E5: Get the status of a group (active or archived)"""
        db = get_db()
        try:
            group = db.query(Group).filter(Group.id == group_id).first()
            if group:
                return group.status
            return None
        finally:
            db.close()

class ScheduleStorage:
    @staticmethod
    def save_schedule_entry(user_id: int, group_id: int, day: str, subject: str, start_time: str, end_time: str, snapshot_version: str = 'current') -> ScheduleEntry:
        db = get_db()
        entry = ScheduleEntry(user_id=user_id, group_id=group_id, day_of_week=day, subject=subject, start_time=start_time, end_time=end_time, snapshot_version=snapshot_version)
        db.add(entry)
        db.commit()
        db.refresh(entry)
        db.close()
        return entry

    @staticmethod
    def get_schedule_entries(user_id: int, day: str = None) -> list:
        db = get_db()
        query = db.query(ScheduleEntry).filter(
            ScheduleEntry.user_id == user_id,
            ScheduleEntry.snapshot_version.in_(["current", "manual"])
        )
        if day:
            query = query.filter(ScheduleEntry.day_of_week == day)
        entries = query.all()
        db.close()
        return entries

    @staticmethod
    def get_schedule_entry(user_id: int, entry_id: int) -> ScheduleEntry:
        db = get_db()
        try:
            entry = db.query(ScheduleEntry).filter(
                ScheduleEntry.id == entry_id,
                ScheduleEntry.user_id == user_id,
                ScheduleEntry.snapshot_version.in_(["current", "manual"]),
            ).first()
            return entry
        finally:
            db.close()

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
    def update_entry_in_database(entry_id: int, updates: dict, user_id: int = None) -> bool:
        db = get_db()
        query = db.query(ScheduleEntry).filter(ScheduleEntry.id == entry_id)
        if user_id is not None:
            query = query.filter(ScheduleEntry.user_id == user_id)
        entry = query.first()
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
    def delete_entry_from_database(entry_id: int, user_id: int = None) -> bool:
        db = get_db()
        query = db.query(ScheduleEntry).filter(ScheduleEntry.id == entry_id)
        if user_id is not None:
            query = query.filter(ScheduleEntry.user_id == user_id)
        entry = query.first()
        if entry:
            db.delete(entry)
            db.commit()
            db.close()
            return True
        db.close()
        return False

    @staticmethod
    def replace_schedule_entries_for_user(user_id: int, group_id: int, entries: list[dict]) -> int:
        db = get_db()
        try:
            # Only delete current snapshot entries, keep previous for diff
            db.query(ScheduleEntry).filter(
                ScheduleEntry.user_id == user_id,
                ScheduleEntry.snapshot_version == "current"
            ).delete()
            new_entries = [
                ScheduleEntry(
                    user_id=user_id,
                    group_id=group_id,
                    day_of_week=entry["day_of_week"],
                    subject=entry["subject"],
                    start_time=entry["start_time"],
                    end_time=entry["end_time"],
                    snapshot_version="current",
                )
                for entry in entries
            ]
            db.add_all(new_entries)
            db.commit()
            return len(new_entries)
        finally:
            db.close()

    @staticmethod
    def promote_current_to_previous_for_user(user_id: int) -> int:
        """Move current snapshot entries to previous before syncing new data."""
        db = get_db()
        try:
            current_entries = db.query(ScheduleEntry).filter(
                ScheduleEntry.user_id == user_id,
                ScheduleEntry.snapshot_version == "current"
            ).all()
            
            promoted_count = 0
            for entry in current_entries:
                entry.snapshot_version = "previous"
                promoted_count += 1
            
            if promoted_count > 0:
                db.commit()
            
            return promoted_count
        finally:
            db.close()

    @staticmethod
    def get_schedule_entries_by_snapshot(user_id: int, snapshot_version: str = "current", day: str = None) -> list:
        """Get schedule entries filtered by snapshot version."""
        db = get_db()
        query = db.query(ScheduleEntry).filter(
            ScheduleEntry.user_id == user_id,
            ScheduleEntry.snapshot_version == snapshot_version
        )
        if day:
            query = query.filter(ScheduleEntry.day_of_week == day)
        entries = query.all()
        db.close()
        return entries

    @staticmethod
    def get_previous_snapshot_for_user(user_id: int) -> list:
        """Get previous snapshot for diff calculation."""
        return ScheduleStorage.get_schedule_entries_by_snapshot(user_id, snapshot_version="previous")

class DiffStorage:
    @staticmethod
    def save_schedule_diff(user_id: int, group_id: int, change_type: str, lesson_subject: str, 
                          lesson_day: str, lesson_time: str, change_details: str = None) -> dict:
        """Save a schedule change to the database."""
        db = get_db()
        try:
            diff = ScheduleDiff(
                user_id=user_id,
                group_id=group_id,
                change_type=change_type,
                lesson_subject=lesson_subject,
                lesson_day=lesson_day,
                lesson_time=lesson_time,
                change_details=change_details
            )
            db.add(diff)
            db.commit()
            db.refresh(diff)
            return {
                'id': diff.id,
                'change_type': diff.change_type,
                'lesson_subject': diff.lesson_subject,
                'change_details': diff.change_details
            }
        finally:
            db.close()

    @staticmethod
    def get_schedule_diffs_for_user(user_id: int, limit: int = 50) -> list:
        """Get recent schedule changes for a user."""
        db = get_db()
        try:
            diffs = db.query(ScheduleDiff).filter(
                ScheduleDiff.user_id == user_id
            ).order_by(ScheduleDiff.created_at.desc()).limit(limit).all()
            return diffs
        finally:
            db.close()

    @staticmethod
    def clear_diffs_for_user(user_id: int) -> int:
        """Clear all diffs for a user (after displaying or archiving)."""
        db = get_db()
        try:
            count = db.query(ScheduleDiff).filter(ScheduleDiff.user_id == user_id).delete()
            db.commit()
            return count
        finally:
            db.close()

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

class EventStorage:
    @staticmethod
    def save_schedule_updated_event(user_id: int, group_id: int, changes_json: str) -> ScheduleUpdatedEvent:
        db = get_db()
        try:
            event = ScheduleUpdatedEvent(
                user_id=user_id,
                group_id=group_id,
                changes_json=changes_json,
                is_processed=False
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            return event
        finally:
            db.close()
    
    @staticmethod
    def get_events_for_user(user_id: int, limit: int = 20) -> list:
        db = get_db()
        try:
            events = db.query(ScheduleUpdatedEvent).filter(
                ScheduleUpdatedEvent.user_id == user_id
            ).order_by(ScheduleUpdatedEvent.created_at.desc()).limit(limit).all()
            return events
        finally:
            db.close()
    
    @staticmethod
    def mark_event_processed(event_id: int) -> bool:
        db = get_db()
        try:
            event = db.query(ScheduleUpdatedEvent).filter(
                ScheduleUpdatedEvent.id == event_id
            ).first()
            if event:
                event.is_processed = True
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    @staticmethod
    def get_unprocessed_events(limit: int = 50) -> list:
        db = get_db()
        try:
            events = db.query(ScheduleUpdatedEvent).filter(
                ScheduleUpdatedEvent.is_processed == False
            ).order_by(ScheduleUpdatedEvent.created_at.asc()).limit(limit).all()
            return events
        finally:
            db.close()


class LogStorage:
    @staticmethod
    def save_event_log(event_type: str, user_id: int = None, group_id: int = None, event_data: str = None) -> EventLog:
        db = get_db()
        try:
            log = EventLog(
                event_type=event_type,
                user_id=user_id,
                group_id=group_id,
                event_data=event_data,
                status='logged'
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            return log
        finally:
            db.close()
    
    @staticmethod
    def get_logs_for_user(user_id: int, limit: int = 50) -> list:
        db = get_db()
        try:
            logs = db.query(EventLog).filter(
                EventLog.user_id == user_id
            ).order_by(EventLog.created_at.desc()).limit(limit).all()
            return logs
        finally:
            db.close()

class NoteStorage:
    @staticmethod
    def create_note(owner_id: int, title: str, content: str,
                    visibility: str = 'personal',
                    discipline_id: int = None,
                    group_id: int = None,
                    subject_name: str = None) -> Note:
        db = get_db()
        try:
            note = Note(
                owner_id=owner_id,
                title=title,
                content=content,
                visibility=visibility,
                discipline_id=discipline_id,
                group_id=group_id,
                subject_name=subject_name,
                version=1,
            )
            db.add(note)
            db.commit()
            db.refresh(note)
            return note
        finally:
            db.close()

    @staticmethod
    def get_note_by_id(note_id: int) -> Note:
        db = get_db()
        try:
            return db.query(Note).filter(Note.id == note_id).first()
        finally:
            db.close()

    @staticmethod
    def get_personal_notes(owner_id: int) -> list:
        db = get_db()
        try:
            return db.query(Note).filter(
                Note.owner_id == owner_id,
                Note.visibility == 'personal'
            ).order_by(Note.updated_at.desc()).all()
        finally:
            db.close()

    @staticmethod
    def get_discipline_notes(group_id: int, subject_name: str = None) -> list:
        db = get_db()
        try:
            query = db.query(Note).filter(
                Note.group_id == group_id,
                Note.visibility == 'discipline'
            )
            if subject_name:
                query = query.filter(Note.subject_name == subject_name)
            return query.order_by(Note.updated_at.desc()).all()
        finally:
            db.close()

    @staticmethod
    def create_discipline_note(owner_id: int, group_id: int, title: str, content: str, subject_name: str) -> Note:
        db = get_db()
        try:
            note = Note(
                owner_id=owner_id,
                title=title,
                content=content,
                visibility='discipline',
                group_id=group_id,
                subject_name=subject_name,
                version=1
            )
            db.add(note)
            db.commit()
            db.refresh(note)
            return note
        finally:
            db.close()

    @staticmethod
    def update_note(note_id: int, updates: dict) -> bool:
        db = get_db()
        try:
            note = db.query(Note).filter(Note.id == note_id).first()
            if not note:
                return False
            for key, value in updates.items():
                if hasattr(note, key):
                    setattr(note, key, value)
            note.version += 1
            db.commit()
            return True
        finally:
            db.close()

    @staticmethod
    def delete_note(note_id: int) -> bool:
        db = get_db()
        try:
            note = db.query(Note).filter(Note.id == note_id).first()
            if not note:
                return False
            db.delete(note)
            db.commit()
            return True
        finally:
            db.close()