"""
Gateway API для фильтрации и доставки расписания (A6),
управления заметками (B3) и OAuth-привязки Gmail (C2)

Эндпоинты:
- GET /integration/schedule - получить расписание с фильтрами
- POST /notes/discipline - создать общую заметку
- GET /notes/discipline - получить общие заметки
- PUT /notes/discipline/<id> - обновить заметку
- DELETE /notes/discipline/<id> - удалить заметку
- GET /oauth/gmail/start - получить ссылку для привязки Gmail
- GET /oauth/gmail/callback - колбэк от Google после авторизации пользователя
"""

import urllib.parse
import urllib.request
import json
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from controllers import ScheduleController, NoteController, GroupController, GmailController
from analytics import AnalyticsTracker
from storage import ScheduleStorage, GroupStorage
from database import get_db, ScheduleEntry
from config import GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REDIRECT_URI

app = Flask(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_date(date_str: str) -> datetime:
    """Парсит дату из строки (формат: YYYY-MM-DD)"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Некорректный формат даты: {date_str}. Используйте YYYY-MM-DD")

def day_name_to_number(day_name: str) -> int:
    """Преобразует название дня в номер (0=Пн, 6=Вс)"""
    day_mapping = {
        "Monday": 0, "Понедельник": 0,
        "Tuesday": 1, "Вторник": 1,
        "Wednesday": 2, "Среда": 2,
        "Thursday": 3, "Четверг": 3,
        "Friday": 4, "Пятница": 4,
        "Saturday": 5, "Суббота": 5,
        "Sunday": 6, "Воскресенье": 6,
    }
    return day_mapping.get(day_name, -1)

def get_day_of_week_for_date(date_obj) -> str:
    """Получить день недели для даты (возвращает на английском: Monday, Tuesday, ...)"""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days[date_obj.weekday()]

# ============================================================================
# FILTER FUNCTIONS
# ============================================================================

def apply_schedule_filters(entries: list, filters: dict) -> list:
    """
    Применяет фильтры к расписанию

    Параметры фильтров:
    - group_id: int - фильтр по ID группы
    - date: str (YYYY-MM-DD) - фильтр по конкретной дате
    - date_from: str (YYYY-MM-DD) - начало периода
    - date_to: str (YYYY-MM-DD) - конец периода
    - subject: str - фильтр по названию дисциплины (содержит)
    """
    if not entries:
        return []

    filtered = entries

    # Фильтр по group_id
    if filters.get("group_id"):
        group_id = int(filters["group_id"])
        filtered = [e for e in filtered if e.group_id == group_id]

    # Фильтр по дате или периоду дат
    if filters.get("date"):
        date_obj = parse_date(filters["date"])
        target_day = get_day_of_week_for_date(date_obj)
        filtered = [e for e in filtered if e.day_of_week == target_day]
    elif filters.get("date_from") or filters.get("date_to"):
        date_from = parse_date(filters.get("date_from")) if filters.get("date_from") else None
        date_to = parse_date(filters.get("date_to")) if filters.get("date_to") else None

        # Если только date_from - берем 7 дней
        if date_from and not date_to:
            date_to = date_from + timedelta(days=7)
        # Если только date_to - возвращаем ошибку
        elif date_to and not date_from:
            raise ValueError("date_from обязателен при использовании date_to")

        # Собрать дни недели в диапазоне
        valid_days = set()
        current = date_from
        while current <= date_to:
            day_name = get_day_of_week_for_date(current)
            valid_days.add(day_name)
            current += timedelta(days=1)

        filtered = [e for e in filtered if e.day_of_week in valid_days]

    # Фильтр по дисциплине (содержит подстроку, case-insensitive)
    if filters.get("subject"):
        subject_filter = filters["subject"].lower()
        filtered = [e for e in filtered if subject_filter in e.subject.lower()]

    return filtered

# ============================================================================
# REST ENDPOINTS - SCHEDULE
# ============================================================================

@app.route("/integration/schedule", methods=["GET"])
def get_schedule():
    """
    GET /integration/schedule

    Возвращает расписание с поддержкой фильтров

    Query параметры:
    - user_id: int (ОБЯЗАТЕЛЬНО) - ID пользователя
    - group_id: int (опционально) - фильтр по группе
    - date: str (опционально) - конкретная дата (YYYY-MM-DD)
    - date_from: str (опционально) - начало периода (YYYY-MM-DD)
    - date_to: str (опционально) - конец периода (YYYY-MM-DD)
    - subject: str (опционально) - фильтр по дисциплине (содержит)
    """
    try:
        # Проверка обязательного параметра
        user_id_str = request.args.get("user_id")
        if not user_id_str:
            return jsonify({
                "status": "error",
                "message": "user_id обязателен",
                "code": "MISSING_PARAMETER"
            }), 400

        try:
            user_id = int(user_id_str)
        except ValueError:
            return jsonify({
                "status": "error",
                "message": "user_id должен быть целым числом",
                "code": "INVALID_PARAMETER"
            }), 400

        # Получить расписание для пользователя
        all_entries = ScheduleController.get_schedule_entries(user_id)
        if not all_entries:
            return jsonify({
                "status": "success",
                "data": {
                    "schedule": [],
                    "filter_summary": {},
                    "total": 0
                }
            }), 200

        # Подготовить фильтры
        filters = {}
        if request.args.get("group_id"):
            filters["group_id"] = request.args.get("group_id")
        if request.args.get("date"):
            filters["date"] = request.args.get("date")
        if request.args.get("date_from"):
            filters["date_from"] = request.args.get("date_from")
        if request.args.get("date_to"):
            filters["date_to"] = request.args.get("date_to")
        if request.args.get("subject"):
            filters["subject"] = request.args.get("subject")

        # Применить фильтры
        filtered_entries = apply_schedule_filters(all_entries, filters)

        # Форматировать результат
        schedule_data = []
        for entry in filtered_entries:
            schedule_data.append({
                "id": entry.id,
                "day_of_week": entry.day_of_week,
                "subject": entry.subject,
                "start_time": entry.start_time,
                "end_time": entry.end_time,
                "group_id": entry.group_id
            })

        # Сформировать summary фильтров
        filter_summary = {
            "group_id": filters.get("group_id"),
            "date": filters.get("date"),
            "date_from": filters.get("date_from"),
            "date_to": filters.get("date_to"),
            "subject": filters.get("subject"),
            "applied_filters": list(filters.keys())
        }

        return jsonify({
            "status": "success",
            "data": {
                "schedule": schedule_data,
                "filter_summary": filter_summary,
                "total": len(filtered_entries)
            }
        }), 200

    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "code": "INVALID_FILTER"
        }), 400

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Внутренняя ошибка: {str(e)}",
            "code": "INTERNAL_ERROR"
        }), 500

@app.route("/integration/schedule/filters-info", methods=["GET"])
def get_filters_info():
    """
    GET /integration/schedule/filters-info

    Возвращает информацию о доступных фильтрах и их описание
    """
    return jsonify({
        "status": "success",
        "data": {
            "available_filters": {
                "user_id": {
                    "type": "integer",
                    "required": True,
                    "description": "ID пользователя"
                },
                "group_id": {
                    "type": "integer",
                    "required": False,
                    "description": "Фильтр по ID группы"
                },
                "date": {
                    "type": "string (YYYY-MM-DD)",
                    "required": False,
                    "description": "Фильтр по конкретной дате"
                },
                "date_from": {
                    "type": "string (YYYY-MM-DD)",
                    "required": False,
                    "description": "Начало диапазона дат (если не указан date_to, то +7 дней)"
                },
                "date_to": {
                    "type": "string (YYYY-MM-DD)",
                    "required": False,
                    "description": "Конец диапазона дат (требует date_from)"
                },
                "subject": {
                    "type": "string",
                    "required": False,
                    "description": "Фильтр по названию дисциплины (partial match, case-insensitive)"
                }
            },
            "examples": {
                "get_all": "/integration/schedule?user_id=12345",
                "by_group": "/integration/schedule?user_id=12345&group_id=1",
                "by_date": "/integration/schedule?user_id=12345&date=2026-05-15",
                "by_date_range": "/integration/schedule?user_id=12345&date_from=2026-05-15&date_to=2026-05-21",
                "by_subject": "/integration/schedule?user_id=12345&subject=Математика",
                "combined": "/integration/schedule?user_id=12345&group_id=1&date=2026-05-15&subject=Математика"
            }
        }
    }), 200

# ============================================================================
# REST ENDPOINTS - NOTES (B3)
# ============================================================================

@app.route("/notes/discipline", methods=["POST"])
def create_discipline_note():
    """
    POST /notes/discipline

    Создает общую заметку по дисциплине

    Headers:
    - user-id: int - ID пользователя

    Body:
    {
        "discipline_id": int,
        "group_id": int,
        "title": str,
        "content": str
    }
    """
    data = request.json
    user_id = request.headers.get("user-id")

    if not user_id:
        return jsonify({"status": "error", "message": "user-id header required"}), 400

    if not data.get("discipline_id"):
        return jsonify({"status": "error", "message": "discipline_id required"}), 400

    if not data.get("group_id"):
        return jsonify({"status": "error", "message": "group_id required"}), 400

    if not data.get("title"):
        return jsonify({"status": "error", "message": "title required"}), 400

    if not data.get("content"):
        return jsonify({"status": "error", "message": "content required"}), 400

    result = NoteController.create_discipline_note(
        user_id=int(user_id),
        discipline_id=data.get("discipline_id"),
        group_id=data.get("group_id"),
        title=data.get("title"),
        content=data.get("content")
    )

    status = 200 if result["status"] == "success" else 400
    return jsonify(result), status

@app.route("/notes/discipline", methods=["GET"])
def get_discipline_notes():
    """
    GET /notes/discipline

    Получает все общие заметки по дисциплине

    Headers:
    - user-id: int - ID пользователя

    Query params:
    - group_id: int (обязательно)
    - discipline_id: int (опционально)
    """
    user_id = request.headers.get("user-id")
    group_id = request.args.get("group_id", type=int)
    discipline_id = request.args.get("discipline_id", type=int)

    if not user_id:
        return jsonify({"status": "error", "message": "user-id header required"}), 400

    if not group_id:
        return jsonify({"status": "error", "message": "group_id required"}), 400

    result = NoteController.get_discipline_notes(int(user_id), group_id, discipline_id)
    return jsonify(result), 200

@app.route("/notes/discipline/<int:note_id>", methods=["PUT"])
def update_discipline_note(note_id):
    """
    PUT /notes/discipline/<note_id>

    Обновляет общую заметку

    Headers:
    - user-id: int - ID пользователя

    Body:
    {
        "title": str (опционально),
        "content": str (опционально)
    }
    """
    user_id = request.headers.get("user-id")
    data = request.json

    if not user_id:
        return jsonify({"status": "error", "message": "user-id header required"}), 400

    result = NoteController.update_discipline_note(int(user_id), note_id, data)
    status = 200 if result["status"] == "success" else 400
    return jsonify(result), status

@app.route("/notes/discipline/<int:note_id>", methods=["DELETE"])
def delete_discipline_note(note_id):
    """
    DELETE /notes/discipline/<note_id>

    Удаляет общую заметку

    Headers:
    - user-id: int - ID пользователя
    """
    user_id = request.headers.get("user-id")

    if not user_id:
        return jsonify({"status": "error", "message": "user-id header required"}), 400

    result = NoteController.delete_discipline_note(int(user_id), note_id)
    status = 200 if result["status"] == "success" else 400
    return jsonify(result), status

# ============================================================================
# REST ENDPOINTS - GMAIL OAUTH (C2)
# ============================================================================

_GMAIL_TOKEN_URL = "https://oauth2.googleapis.com/token"


@app.route("/oauth/gmail/start", methods=["GET"])
def gmail_oauth_start():
    """
    GET /oauth/gmail/start?user_id=<int>

    Генерирует Google OAuth URL через GmailController.
    Возвращает: {"status": "success", "auth_url": "..."}
    """
    user_id_str = request.args.get("user_id")
    if not user_id_str:
        return jsonify({"status": "error", "message": "user_id обязателен"}), 400
    try:
        user_id = int(user_id_str)
    except ValueError:
        return jsonify({"status": "error", "message": "user_id должен быть числом"}), 400

    auth_url = GmailController.generate_oauth_url(user_id)
    return jsonify({"status": "success", "auth_url": auth_url}), 200


@app.route("/oauth/gmail/callback", methods=["GET"])
def gmail_oauth_callback():
    """
    GET /oauth/gmail/callback?code=<str>&state=<str>

    Принимает код от Google, обменивает на токены, сохраняет через GmailController.
    Возвращает HTML-страницу для пользователя (открыта в браузере).
    """
    error = request.args.get("error")
    if error:
        return f"<h3>Ошибка авторизации: {error}</h3><p>Закройте это окно и попробуйте снова.</p>", 400

    code = request.args.get("code")
    state = request.args.get("state")
    if not code or not state:
        return "<h3>Ошибка: отсутствует code или state.</h3>", 400

    user_id = GmailController.validate_and_consume_state(state)
    if user_id is None:
        return "<h3>Ошибка: недействительный или просроченный state. Попробуйте привязать Gmail заново.</h3>", 400

    # Обмен кода на токены — HTTP к Google, остаётся на границе интеграции
    token_body = urllib.parse.urlencode({
        "code": code,
        "client_id": GMAIL_CLIENT_ID,
        "client_secret": GMAIL_CLIENT_SECRET,
        "redirect_uri": GMAIL_REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()
    req = urllib.request.Request(
        _GMAIL_TOKEN_URL,
        data=token_body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            token_resp = json.loads(resp.read().decode())
    except Exception as exc:
        return f"<h3>Ошибка обмена кода на токен: {exc}</h3>", 500

    access_token = token_resp.get("access_token")
    if not access_token:
        return "<h3>Ошибка: Google не вернул access_token.</h3>", 500

    token_expiry = datetime.utcnow() + timedelta(seconds=token_resp.get("expires_in", 3600))
    GmailController.save_tokens(
        user_id=user_id,
        access_token=access_token,
        refresh_token=token_resp.get("refresh_token"),
        token_expiry=token_expiry,
        scope=token_resp.get("scope", ""),
    )

    return "<h3>✅ Gmail успешно привязан!</h3><p>Вернитесь в Telegram.</p>", 200
  
# ============================================================================
# REST ENDPOINTS - GROUP BROADCAST (D1 / NSU-030)
# ============================================================================

@app.route("/groups/<int:group_id>/broadcast", methods=["POST"])
def create_group_broadcast(group_id):
    """
    POST /groups/<group_id>/broadcast

    Создает общий сбор для выбранной группы.

    Headers:
    - user-id: int - ID пользователя, который запускает общий сбор

    Body:
    {
        "message": str
    }
    """
    user_id = request.headers.get("user-id")
    data = request.json or {}

    if not user_id:
        return jsonify({
            "status": "error",
            "message": "user-id header required"
        }), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({
            "status": "error",
            "message": "user-id должен быть целым числом"
        }), 400

    message = data.get("message")
    if not message:
        return jsonify({
            "status": "error",
            "message": "message required"
        }), 400

    result = GroupController.create_group_broadcast(
        user_id=user_id,
        group_id=group_id,
        message=message
    )

    status_code = 200 if result["status"] == "success" else 400
    return jsonify(result), status_code

@app.route("/groups/<int:group_id>/send_broadcast", methods=["POST"])
def send_group_broadcast(group_id):
    user_id = request.headers.get("user-id")
    data = request.json or {}

    if not user_id:
        return jsonify({"status":"error","message":"user-id header required"}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"status":"error","message":"user-id должен быть целым числом"}), 400

    message = data.get("message")
    if not message:
        return jsonify({"status":"error","message":"message required"}), 400

    result = GroupController.send_group_broadcast(
        user_id=user_id,
        group_id=group_id,
        message=message
    )
    status_code = 200 if result["status"] == "success" else 400
    return jsonify(result), status_code

@app.route("/groups/<int:group_id>/broadcast/history", methods=["GET"])
def broadcast_history(group_id):
    # Пока проверка админа опциональна, можно добавить в будущем
    result = GroupController.get_broadcast_history(group_id)
    status_code = 200 if result["status"] == "success" else 400
    return jsonify(result), status_code

@app.route("/feed/aggregated", methods=["GET"])
def get_aggregated_feed():
    """
    NSU-052 / F7
    Возвращает агрегированную ленту для пользователя
    Параметры GET:
        user-id (header)
        event_type (query string, optional, default "all")
        limit (query string, optional, default 50)
    """
    user_id = request.headers.get("user-id")
    if not user_id:
        return jsonify({"status":"error","message":"user-id header required"}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"status":"error","message":"user-id должен быть числом"}), 400

    event_type_filter = request.args.get("event_type", "all")
    limit = int(request.args.get("limit", 50))

    result = GroupController.get_aggregated_feed(
        user_id=user_id,
        limit=limit,
        event_type_filter=event_type_filter
    )

    status_code = 200 if result["status"] == "success" else 400
    return jsonify(result), status_code

# ============================================================================
# REST ENDPOINTS - NOTIFICATION ANALYTICS (F8 / NSU-053)
# ============================================================================

@app.route("/analytics/notification/open", methods=["POST"])
def track_notification_open():
    """
    NSU-053 / F8
    Записать открытие уведомления.

    Headers:
    - user-id: int

    Body:
    {
        "notification_id": int,
        "event_type": str,
        "target": str,
        "metadata": dict
    }
    """
    user_id = request.headers.get("user-id")
    data = request.json or {}

    if not user_id:
        return jsonify({"status": "error", "message": "user-id header required"}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"status": "error", "message": "user-id должен быть числом"}), 400

    result = AnalyticsTracker.track_notification_metric(
        user_id=user_id,
        metric_type="open",
        notification_id=data.get("notification_id"),
        event_type=data.get("event_type"),
        target=data.get("target"),
        metadata=data.get("metadata")
    )

    status_code = 200 if result["status"] == "success" else 400
    return jsonify(result), status_code


@app.route("/analytics/notification/click", methods=["POST"])
def track_notification_click():
    """
    NSU-053 / F8
    Записать клик по уведомлению.

    Headers:
    - user-id: int

    Body:
    {
        "notification_id": int,
        "event_type": str,
        "target": str,
        "metadata": dict
    }
    """
    user_id = request.headers.get("user-id")
    data = request.json or {}

    if not user_id:
        return jsonify({"status": "error", "message": "user-id header required"}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"status": "error", "message": "user-id должен быть числом"}), 400

    result = AnalyticsTracker.track_notification_metric(
        user_id=user_id,
        metric_type="click",
        notification_id=data.get("notification_id"),
        event_type=data.get("event_type"),
        target=data.get("target"),
        metadata=data.get("metadata")
    )

    status_code = 200 if result["status"] == "success" else 400
    return jsonify(result), status_code


@app.route("/analytics/notification/metrics", methods=["GET"])
def get_notification_metrics():
    """
    NSU-053 / F8
    Получить метрики открытий/кликов.

    Query params:
    - user_id: int, optional
    - metric_type: open/click, optional
    - limit: int, optional
    """
    user_id = request.args.get("user_id", default=None, type=int)
    metric_type = request.args.get("metric_type", default=None)
    limit = request.args.get("limit", default=100, type=int)

    result = AnalyticsTracker.get_notification_metrics(
        user_id=user_id,
        metric_type=metric_type,
        limit=limit
    )

    status_code = 200 if result["status"] == "success" else 400
    return jsonify(result), status_code


@app.route("/analytics/notification/metrics/summary", methods=["GET"])
def get_notification_metrics_summary():
    """
    NSU-053 / F8
    Получить сводку по открытиям и кликам.
    """
    user_id = request.args.get("user_id", default=None, type=int)

    result = AnalyticsTracker.get_notification_metrics_summary(user_id=user_id)

    status_code = 200 if result["status"] == "success" else 400
    return jsonify(result), status_code

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route("/health", methods=["GET"])
def health_check():
    """Проверка здоровья сервиса"""
    return jsonify({
        "status": "ok",
        "service": "gateway-api",
        "version": "1.0.0"
    }), 200

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Обработчик 404"""
    return jsonify({
        "status": "error",
        "message": "Эндпоинт не найден",
        "code": "NOT_FOUND"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Обработчик 500"""
    return jsonify({
        "status": "error",
        "message": "Внутренняя ошибка сервера",
        "code": "INTERNAL_ERROR"
    }), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Запуск на localhost:5000
    # В продакшене использовать gunicorn: gunicorn -w 4 gateway_api:app
    app.run(host="127.0.0.1", port=5000, debug=True)