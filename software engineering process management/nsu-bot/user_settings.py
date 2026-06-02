from notifier import Notifier

class UserSettings:
    """
    Хранение пользовательских настроек уведомлений:
    - приоритет: critical/high/normal/low
    - каналы доставки: telegram, email, etc.
    """
    DEFAULT_NOTIFICATION_SETTINGS = {
        "priority": "normal",
        "channels": ["telegram"]
    }

    def __init__(self, user_id: int):
        self.user_id = user_id
        # создаём копию дефолтных настроек для каждого пользователя
        self.settings = UserSettings.DEFAULT_NOTIFICATION_SETTINGS.copy()

    def set_priority(self, priority: str):
        """Установить уровень приоритета"""
        self.settings["priority"] = Notifier.validate_priority(priority)

    def set_channels(self, channels: list):
        """Установить каналы доставки"""
        self.settings["channels"] = channels

    def get_settings(self) -> dict:
        """Вернуть текущие настройки"""
        return self.settings