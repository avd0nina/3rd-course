from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Table, Text, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, date
import json

Base = declarative_base()

student_group = Table(
    'student_group',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('student.user_id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('group.id'), primary_key=True)
)


class Student(Base):
    __tablename__ = 'student'
    user_id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('group.id'), nullable=True)
    group = relationship("Group", back_populates="students")

class Group(Base):
    __tablename__ = 'group'
    id = Column(Integer, primary_key=True)
    number = Column(String(50), unique=True, nullable=False)
    group_type = Column(String(20), default='academic', nullable=False)
    telegram_chat_id = Column(String(50), nullable=True)
    creator_user_id = Column(Integer, nullable=True)
    status = Column(String(20), default='active', nullable=False)
    students = relationship("Student", back_populates="group")

class ScheduleEntry(Base):
    __tablename__ = 'schedule_entry'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('student.user_id'), nullable=False)
    group_id = Column(Integer, ForeignKey('group.id'), nullable=False)
    day_of_week = Column(String(20), nullable=False)
    subject = Column(String(100), nullable=False)
    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=False)
    snapshot_version = Column(String(20), default='current', nullable=False)

class HomeworkTask(Base):
    __tablename__ = 'homework_task'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('student.user_id'), nullable=False)
    group_id = Column(Integer, ForeignKey('group.id'), nullable=False)
    subject = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=False)
    deadline = Column(String(20), nullable=False)
    is_done = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class QueueEntry(Base):
    __tablename__ = 'queue_entry'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('student.user_id'), nullable=False)
    date = Column(String(20), nullable=False)
    subject = Column(String(100), nullable=False)
    position = Column(Integer, nullable=False)
    is_open = Column(Boolean, default=True)

class DeadlinesNotificationSettings(Base):
    __tablename__ = 'deadlines_notification_settings'
    user_id = Column(Integer, ForeignKey('student.user_id'), primary_key=True)
    enabled = Column(Boolean, default=False)
    reminder_hours_before = Column(Integer, default=24)

class QueueNotificationSettings(Base):
    __tablename__ = 'queue_notification_settings'
    user_id = Column(Integer, ForeignKey('student.user_id'), primary_key=True)
    enabled = Column(Boolean, default=False)

class ScheduleDiff(Base):
    __tablename__ = 'schedule_diff'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('student.user_id'), nullable=False)
    group_id = Column(Integer, ForeignKey('group.id'), nullable=False)
    change_type = Column(String(20), nullable=False)
    lesson_subject = Column(String(100), nullable=False)
    lesson_day = Column(String(20), nullable=False)
    lesson_time = Column(String(20), nullable=False)
    change_details = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ScheduleUpdatedEvent(Base):
    __tablename__ = 'schedule_updated_event'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('student.user_id'), nullable=False)
    group_id = Column(Integer, ForeignKey('group.id'), nullable=False)
    event_type = Column(String(50), default='schedule_updated', nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    changes_json = Column(Text, nullable=True)
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class EventLog(Base):
    __tablename__ = 'event_log'
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey('student.user_id'), nullable=True)
    group_id = Column(Integer, ForeignKey('group.id'), nullable=True)
    event_data = Column(Text, nullable=True)
    status = Column(String(20), default='logged', nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class GroupChatMembership(Base):
    """E4: Track which users have been invited to which chat groups"""
    __tablename__ = 'group_chat_membership'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('student.user_id'), nullable=False)
    chat_group_id = Column(Integer, ForeignKey('group.id'), nullable=False)
    status = Column(String(20), default='invited', nullable=False)
    invited_at = Column(DateTime, default=datetime.utcnow)

class Note(Base):
    __tablename__ = 'note'
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('student.user_id'), nullable=False)
    visibility = Column(String(20), nullable=False, default='personal')
    discipline_id = Column(Integer, nullable=True)
    group_id = Column(Integer, ForeignKey('group.id'), nullable=True)
    subject_name = Column(String(200), nullable=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GmailOAuthState(Base):
    """C2: временное хранилище CSRF state-токенов OAuth"""
    __tablename__ = 'gmail_oauth_state'
    state      = Column(String(100), primary_key=True)
    user_id    = Column(Integer, ForeignKey('student.user_id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class GmailToken(Base):
    """C1: хранение OAuth-токенов Gmail (зашифрованно)"""
    __tablename__ = 'gmail_token'
    user_id       = Column(Integer, ForeignKey('student.user_id'), primary_key=True)
    access_token  = Column(Text, nullable=True)   # зашифровано через crypto.encrypt()
    refresh_token = Column(Text, nullable=True)   # зашифровано через crypto.encrypt()
    token_expiry  = Column(DateTime, nullable=True)
    gmail_address = Column(String(200), nullable=True)
    is_linked     = Column(Boolean, default=False, nullable=False)
    linked_at     = Column(DateTime, nullable=True)
    scope         = Column(Text, nullable=True)


# Database initialization
ENGINE = create_engine('sqlite:///student_planner.db', echo=False)
Base.metadata.create_all(ENGINE)

def _ensure_schedule_entry_snapshot_version_column():
    inspector = inspect(ENGINE)
    columns = {column["name"] for column in inspector.get_columns("schedule_entry")}
    if "snapshot_version" not in columns:
        with ENGINE.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE schedule_entry "
                    "ADD COLUMN snapshot_version VARCHAR(20) NOT NULL DEFAULT 'current'"
                )
            )


def _ensure_group_type_column():
    inspector = inspect(ENGINE)
    columns = {column["name"] for column in inspector.get_columns("group")}
    if "group_type" not in columns:
        with ENGINE.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE \"group\" "
                    "ADD COLUMN group_type VARCHAR(20) NOT NULL DEFAULT 'academic'"
                )
            )


def _ensure_group_telegram_chat_id_column():
    inspector = inspect(ENGINE)
    columns = {column["name"] for column in inspector.get_columns("group")}
    if "telegram_chat_id" not in columns:
        with ENGINE.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE \"group\" "
                    "ADD COLUMN telegram_chat_id VARCHAR(50) NULL"
                )
            )


def _ensure_group_creator_user_id_column():
    inspector = inspect(ENGINE)
    columns = {column["name"] for column in inspector.get_columns("group")}
    if "creator_user_id" not in columns:
        with ENGINE.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE \"group\" "
                    "ADD COLUMN creator_user_id INTEGER NULL"
                )
            )


def _ensure_group_status_column():
    inspector = inspect(ENGINE)
    columns = {column["name"] for column in inspector.get_columns("group")}
    if "status" not in columns:
        with ENGINE.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE \"group\" "
                    "ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'active'"
                )
            )


_ensure_schedule_entry_snapshot_version_column()
_ensure_group_type_column()
_ensure_group_telegram_chat_id_column()
_ensure_group_creator_user_id_column()
_ensure_group_status_column()
SessionLocal = sessionmaker(bind=ENGINE)

def get_db():
    return SessionLocal()
