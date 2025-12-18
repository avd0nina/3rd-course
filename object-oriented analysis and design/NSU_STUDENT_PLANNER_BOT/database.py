from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, date

Base = declarative_base()

# Association table for many-to-many relationship
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

# Database initialization
ENGINE = create_engine('sqlite:///student_planner.db', echo=False)
Base.metadata.create_all(ENGINE)
SessionLocal = sessionmaker(bind=ENGINE)

def get_db():
    return SessionLocal()
