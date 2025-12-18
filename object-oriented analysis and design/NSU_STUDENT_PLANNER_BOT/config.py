"""
Configuration file for NSU Student Planner Bot
Update these values before running the bot
"""

# Telegram Bot Token
# Get your token from BotFather on Telegram
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# Database configuration
DATABASE_URL = "sqlite:///student_planner.db"
DATABASE_ECHO = False  # Set to True for SQL query logging

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Bot settings
BOT_USERNAME = "nsu_student_planner_bot"
POLLING_TIMEOUT = 30

# Default subjects (for new users)
DEFAULT_SUBJECTS = [
    "Math",
    "Physics", 
    "Chemistry",
    "Literature",
    "History",
    "English",
    "Computer Science",
    "Biology"
]

# Default reminder hours before homework deadline
DEFAULT_REMINDER_HOURS = 24

# Queue settings
QUEUE_MAX_SIZE = 30
EXAMPLE_DATES = ["2025-01-15", "2025-01-16", "2025-01-17", "2025-01-20", "2025-01-21"]

# Time format
TIME_FORMAT = "%H:%M"
DATE_FORMAT = "%Y-%m-%d"

# Emoji settings
EMOJI_SUCCESS = "✅"
EMOJI_ERROR = "❌"
EMOJI_SCHEDULE = "📚"
EMOJI_HOMEWORK = "📝"
EMOJI_QUEUE = "📋"
EMOJI_NOTIFICATION = "🔔"
EMOJI_GROUP = "👥"
EMOJI_BOT = "🤖"
