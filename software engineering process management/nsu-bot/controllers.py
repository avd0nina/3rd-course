import re
import secrets
import urllib.parse
from datetime import datetime, timedelta

from datetime import datetime
from storage import GroupStorage, ScheduleStorage, HomeworkStorage, QueueStorage, NotificationStorage, DiffStorage, \
    EventStorage, LogStorage, NoteStorage
from nsu_integration import NSUIntegrationError, NSUIntegrationService, ParsedScheduleEntry
from notifier import EventPublisher, Notifier
from database import get_db, GmailOAuthState, GmailToken
from config import GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REDIRECT_URI
from gmail_integration import GmailService, GmailIntegrationError
import crypto

NSU_INTEGRATION_SERVICE = NSUIntegrationService()
DAY_NAME_EN_TO_RU = {
    "Monday": "Понедельник",
    "Tuesday": "Вторник",
    "Wednesday": "Среда",
    "Thursday": "Четверг",
    "Friday": "Пятница",
    "Saturday": "Суббота",
    "Sunday": "Воскресенье",
}
DAY_NAME_RU_TO_EN = {value: key for key, value in DAY_NAME_EN_TO_RU.items()}
DAY_NAME_ORDER = {
    "Понедельник": 0,
    "Monday": 0,
    "Вторник": 1,
    "Tuesday": 1,
    "Среда": 2,
    "Wednesday": 2,
    "Четверг": 3,
    "Thursday": 3,
    "Пятница": 4,
    "Friday": 4,
    "Суббота": 5,
    "Saturday": 5,
    "Воскресенье": 6,
    "Sunday": 6,
}


class Verificator:
    """E5: Access control verification for subject chat operations"""

    @staticmethod
    def can_create_subject_chat(user_id: int, academic_group_id: int) -> dict:
        """Check if user can create a subject chat for an academic group"""
        try:
            user_group = GroupStorage.get_student_group(user_id)
            if not user_group:
                return {"status": "denied", "message": "Пользователь не состоит в группе"}

            if user_group.id != academic_group_id:
                return {"status": "denied", "message": "Можно создавать чаты только для своей группы"}

            return {"status": "allowed", "message": "Пользователь имеет право создать чат по предмету"}
        except Exception as e:
            return {"status": "error", "message": f"Ошибка проверки: {str(e)}"}

    @staticmethod
    def can_start_group_broadcast(user_id: int, group_id: int) -> dict:
        """
        Проверка прав для запуска общего сбора (NSU-031)
        """
        try:
            group = GroupStorage.get_group_by_id(group_id)
            if not group:
                return {"status": "denied", "message": "Группа не найдена"}


            return {"status": "allowed", "message": "Пользователь может запустить общий сбор"}

        except Exception as e:
            return {"status": "error", "message": f"Ошибка проверки прав: {str(e)}"}

    @staticmethod
    def can_archive_subject_chat(user_id: int, chat_group_id: int) -> dict:
        """Check if user can archive a subject chat"""
        try:
            chat_group = GroupStorage.get_group_by_id(chat_group_id)
            if not chat_group:
                return {"status": "denied", "message": "Чат не найден"}

            if chat_group.group_type != "subject_chat":
                return {"status": "denied", "message": "Это не чат по предмету"}

            creator_id = GroupStorage.get_group_creator(chat_group_id)
            if creator_id != user_id:
                return {"status": "denied", "message": "Только создатель чата может его архивировать"}

            return {"status": "allowed", "message": "Пользователь может архивировать этот чат"}
        except Exception as e:
            return {"status": "error", "message": f"Ошибка проверки: {str(e)}"}

    @staticmethod
    def can_unarchive_subject_chat(user_id: int, chat_group_id: int) -> dict:
        """Check if user can restore an archived subject chat"""
        try:
            chat_group = GroupStorage.get_group_by_id(chat_group_id)
            if not chat_group:
                return {"status": "denied", "message": "Чат не найден"}

            if chat_group.group_type != "subject_chat":
                return {"status": "denied", "message": "Это не чат по предмету"}

            creator_id = GroupStorage.get_group_creator(chat_group_id)
            if creator_id != user_id:
                return {"status": "denied", "message": "Только создатель чата может его восстановить"}

            return {"status": "allowed", "message": "Пользователь может восстановить этот чат"}
        except Exception as e:
            return {"status": "error", "message": f"Ошибка проверки: {str(e)}"}

    @staticmethod
    def can_view_subject_chat(user_id: int, chat_group_id: int) -> dict:
        """Check if user can view a subject chat"""
        try:
            chat_group = GroupStorage.get_group_by_id(chat_group_id)
            if not chat_group:
                return {"status": "denied", "message": "Чат не найден"}

            if chat_group.group_type != "subject_chat":
                return {"status": "denied", "message": "Это не чат по предмету"}

            user_group = GroupStorage.get_student_group(user_id)
            if not user_group:
                return {"status": "denied", "message": "Пользователь не состоит в группе"}

            if not chat_group.number.startswith(f"[{user_group.number}]"):
                return {"status": "denied", "message": "Этот чат не для вашей группы"}

            return {"status": "allowed", "message": "Пользователь может просматривать этот чат"}
        except Exception as e:
            return {"status": "error", "message": f"Ошибка проверки: {str(e)}"}


class GroupController:
    @staticmethod
    def connect_student_to_group(user_id: int, group_number: str) -> bool:
        result = GroupController.connect_student_to_group_with_details(user_id, group_number)
        return result["status"] == "success"

    @staticmethod
    def connect_student_to_group_with_details(
            user_id: int,
            group_number: str,
            integration_service: NSUIntegrationService = None,
    ) -> dict:
        service = integration_service or NSU_INTEGRATION_SERVICE
        group_entity = NSUIntegrationService.normalize_group_entity(group_number)
        normalized_group_number = group_entity.normalized
        if not normalized_group_number:
            return {"status": "error", "message": "Номер группы не может быть пустым."}

        should_sync_nsu_schedule = GroupController._looks_like_nsu_group(normalized_group_number)

        if should_sync_nsu_schedule:
            try:
                available_groups = service.get_fit_groups()
            except NSUIntegrationError as error:
                return {
                    "status": "error",
                    "message": f"Не удалось получить список групп НГУ: {error}",
                }
            if normalized_group_number not in available_groups:
                return {
                    "status": "error",
                    "message": (
                        f"Группа {normalized_group_number} не найдена на сайте НГУ "
                        "(ФИТ, бакалавриат)."
                    ),
                }

        group = GroupStorage.create_group_if_not_exists(normalized_group_number)
        if not GroupStorage.add_student_to_group(user_id, group.id):
            return {"status": "error", "message": "Не удалось подключить к группе."}

        if not should_sync_nsu_schedule:
            return {
                "status": "success",
                "message": f"✅ Успешно подключены к группе {normalized_group_number}!",
            }

        sync_result = ScheduleController.sync_nsu_schedule(
            user_id=user_id,
            group_id=group.id,
            group_number=normalized_group_number,
            integration_service=service,
        )
        if sync_result["status"] != "success":
            return sync_result

        return {
            "status": "success",
            "message": (
                f"✅ Успешно подключены к группе {normalized_group_number}!\n"
                f"📚 Загружено занятий: {sync_result['entries_count']}"
            ),
        }

    @staticmethod
    def get_nsu_fit_groups(integration_service: NSUIntegrationService = None) -> list[str]:
        service = integration_service or NSU_INTEGRATION_SERVICE
        return service.get_fit_groups()

    @staticmethod
    def _looks_like_nsu_group(group_number: str) -> bool:
        return len(group_number) == 5 and group_number.isdigit()

    @staticmethod
    def link_telegram_chat_to_subject_group(group_id: int, telegram_chat_id: str) -> dict:
        """E3: Link a Telegram chat to a subject_chat group"""
        try:
            group = GroupStorage.get_group_by_id(group_id)
            if not group:
                return {"status": "error", "message": "Группа не найдена"}

            if group.group_type != "subject_chat":
                return {"status": "error", "message": "Эта группа не является чатом по предмету"}

            if GroupStorage.save_telegram_chat_id(group_id, telegram_chat_id):
                return {
                    "status": "success",
                    "message": f"✅ Telegram-чат привязан к группе '{group.number}'",
                    "group": {
                        "id": group.id,
                        "name": group.number,
                        "type": group.group_type,
                        "telegram_chat_id": telegram_chat_id
                    }
                }
            return {"status": "error", "message": "Не удалось сохранить Telegram-чат"}
        except Exception as e:
            return {"status": "error", "message": f"Ошибка: {str(e)}"}

    @staticmethod
    def get_user_subject_chats(user_id: int) -> dict:
        """E7 preview: Get subject_chat groups for user's academic group"""
        try:
            user_group = GroupStorage.get_student_group(user_id)
            if not user_group:
                return {"status": "success", "chats": []}

            # Get all subject_chat groups for this academic group
            all_subject_chats = GroupStorage.get_groups_by_type("subject_chat")
            user_chats = []
            for chat_group in all_subject_chats:
                if chat_group.number.startswith(f"[{user_group.number}]"):
                    user_chats.append({
                        "id": chat_group.id,
                        "name": chat_group.number,
                        "telegram_chat_id": chat_group.telegram_chat_id,
                        "has_telegram": bool(chat_group.telegram_chat_id)
                    })

            return {"status": "success", "chats": sorted(user_chats, key=lambda x: x["name"])}
        except Exception as e:
            return {"status": "error", "message": f"Ошибка: {str(e)}"}

    @staticmethod
    def create_group_broadcast(user_id: int, group_id: int, message: str) -> dict:
        """
        D1 / NSU-030 + D2 / NSU-031: создать общий сбор для группы
        с проверкой прав на запуск
        """
        try:
            # Проверка текста
            if not message or not message.strip():
                return {
                    "status": "error",
                    "message": "Текст общего сбора не может быть пустым"
                }

            # Проверка прав NSU-031
            access_check = Verificator.can_start_group_broadcast(user_id, group_id)
            if access_check["status"] != "allowed":
                return {
                    "status": "error",
                    "message": access_check["message"]
                }

            # Проверка существования группы
            group = GroupStorage.get_group_by_id(group_id)
            if not group:
                return {
                    "status": "error",
                    "message": "Группа не найдена"
                }

            # Получаем участников и формируем recipients
            members = GroupStorage.get_group_members(group_id)
            recipients = [{"user_id": m.user_id} for m in members]

            # Логируем событие
            Notifier.log_event(
                event_type="group_broadcast_created",
                user_id=user_id,
                group_id=group_id,
                event_data={
                    "message": message.strip(),
                    "recipients_count": len(recipients),
                    "recipients": recipients
                }
            )

            return {
                "status": "success",
                "message": "Общий сбор создан",
                "broadcast": {
                    "group_id": group_id,
                    "group_number": group.number,
                    "sender_user_id": user_id,
                    "text": message.strip(),
                    "recipients_count": len(recipients),
                    "recipients": recipients
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка при создании общего сбора: {str(e)}"
            }

    @staticmethod
    def send_group_broadcast(user_id: int, group_id: int, message: str) -> dict:
        """
        D3 / NSU-032 + D6 / NSU-035:
        массовая отправка общего сбора с логом доставки.

        Для каждого участника фиксируем:
        - кому отправляли
        - статус delivered / error
        - время попытки
        - текст ошибки, если она была
        """
        try:
            if not message or not message.strip():
                return {
                    "status": "error",
                    "message": "Текст общего сбора не может быть пустым"
                }

            access_check = Verificator.can_start_group_broadcast(user_id, group_id)
            if access_check["status"] != "allowed":
                return {
                    "status": "error",
                    "message": access_check["message"]
                }

            group = GroupStorage.get_group_by_id(group_id)
            if not group:
                return {
                    "status": "error",
                    "message": "Группа не найдена"
                }

            members = GroupStorage.get_group_members(group_id)

            delivered = []
            failed = []

            for member in members:
                delivery_time = datetime.now().isoformat(timespec="seconds")

                try:
                    delivery_info = {
                        "sender_user_id": user_id,
                        "recipient_user_id": member.user_id,
                        "message": message.strip(),
                        "delivery_status": "delivered",
                        "delivered_at": delivery_time
                    }

                    Notifier.log_event(
                        event_type="group_broadcast_delivery",
                        user_id=member.user_id,
                        group_id=group_id,
                        event_data=delivery_info
                    )

                    delivered.append({
                        "user_id": member.user_id,
                        "status": "delivered",
                        "delivered_at": delivery_time
                    })

                except Exception as delivery_error:
                    error_time = datetime.now().isoformat(timespec="seconds")

                    error_info = {
                        "sender_user_id": user_id,
                        "recipient_user_id": member.user_id,
                        "message": message.strip(),
                        "delivery_status": "error",
                        "error": str(delivery_error),
                        "failed_at": error_time
                    }

                    failed.append({
                        "user_id": member.user_id,
                        "status": "error",
                        "error": str(delivery_error),
                        "failed_at": error_time
                    })

                    try:
                        Notifier.log_event(
                            event_type="group_broadcast_delivery_error",
                            user_id=member.user_id,
                            group_id=group_id,
                            event_data=error_info
                        )
                    except Exception:
                        pass

            summary = {
                "sender_user_id": user_id,
                "group_id": group_id,
                "group_number": group.number,
                "message": message.strip(),
                "delivered_count": len(delivered),
                "failed_count": len(failed),
                "created_at": datetime.now().isoformat(timespec="seconds")
            }

            Notifier.log_event(
                event_type="group_broadcast_delivery_summary",
                user_id=user_id,
                group_id=group_id,
                event_data=summary
            )

            return {
                "status": "success",
                "message": f"Общий сбор обработан: доставлено {len(delivered)}, ошибок {len(failed)}",
                "delivery_log": {
                    "group_id": group_id,
                    "group_number": group.number,
                    "delivered": delivered,
                    "failed": failed,
                    "delivered_count": len(delivered),
                    "failed_count": len(failed)
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка отправки общего сбора: {str(e)}"
            }

    @staticmethod
    def get_broadcast_history(group_id: int) -> dict:
        """
        D7 / NSU-036
        Возвращает историю всех запусков общего сбора для группы.
        История берётся из Notifier.log_event.
        """
        try:
            group = GroupStorage.get_group_by_id(group_id)
            if not group:
                return {"status": "error", "message": "Группа не найдена"}

            # Берём все события по этой группе
            history_events = Notifier.get_group_events(group_id, event_type_prefix="group_broadcast")

            # Фильтруем только события общего сбора
            broadcast_events = []
            for event in history_events:
                if event["event_type"].startswith("group_broadcast"):
                    broadcast_events.append({
                        "event_type": event["event_type"],
                        "user_id": event.get("user_id"),
                        "message": event.get("event_data", {}).get("message"),
                        "recipient_user_id": event.get("event_data", {}).get("recipient_user_id"),
                        "delivery_status": event.get("event_data", {}).get("delivery_status"),
                        "timestamp": event.get("event_data", {}).get("delivered_at") or event.get("event_data", {}).get("failed_at") or event.get("event_data", {}).get("created_at")
                    })

            return {
                "status": "success",
                "group_id": group_id,
                "group_number": group.number,
                "history_count": len(broadcast_events),
                "history": broadcast_events
            }

        except Exception as e:
            return {"status": "error", "message": f"Ошибка при получении истории: {str(e)}"}

    @staticmethod
    def auto_invite_group_members_to_chat(academic_group_id: int, chat_group_id: int) -> dict:
        """E4: Auto-invite all members of academic group to a subject chat"""
        try:
            # Get the chat group to verify it's a subject_chat
            chat_group = GroupStorage.get_group_by_id(chat_group_id)
            if not chat_group:
                return {"status": "error", "message": "Чат не найден"}

            if chat_group.group_type != "subject_chat":
                return {"status": "error", "message": "Это не чат по предмету"}

            if not chat_group.telegram_chat_id:
                return {"status": "error", "message": "Telegram-чат не привязан к группе"}

            # Get all members of the academic group
            members = GroupStorage.get_group_members(academic_group_id)
            if not members:
                return {"status": "success", "invited_count": 0, "message": "В группе нет студентов"}

            # Get already invited members
            already_invited = GroupStorage.get_chat_members(chat_group_id)

            # Invite new members
            invited_count = 0
            for member in members:
                if member.user_id not in already_invited:
                    if GroupStorage.save_chat_membership(member.user_id, chat_group_id, 'invited'):
                        invited_count += 1

            return {
                "status": "success",
                "invited_count": invited_count,
                "already_members": len(already_invited),
                "message": f"Приглашено {invited_count} новых участников в {chat_group.number}"
            }
        except Exception as e:
            return {"status": "error", "message": f"Ошибка при приглашении: {str(e)}"}

    @staticmethod
    def auto_invite_all_subject_chats(academic_group_id: int) -> dict:
        """E4: Auto-invite all members to all subject chats of their academic group"""
        try:
            academic_group = GroupStorage.get_group_by_id(academic_group_id)
            if not academic_group:
                return {"status": "error", "message": "Группа не найдена"}

            # Get all subject_chat groups for this academic group
            all_subject_chats = GroupStorage.get_groups_by_type("subject_chat")
            matching_chats = [g for g in all_subject_chats if g.number.startswith(f"[{academic_group.number}]")]

            if not matching_chats:
                return {"status": "success", "message": "Нет чатов по предметам для этой группы", "chats_processed": 0}

            results = []
            total_invited = 0
            for chat in matching_chats:
                result = GroupController.auto_invite_group_members_to_chat(academic_group_id, chat.id)
                if result["status"] == "success":
                    total_invited += result.get("invited_count", 0)
                    results.append({
                        "chat": chat.number,
                        "invited": result.get("invited_count", 0)
                    })

            return {
                "status": "success",
                "message": f"Всего приглашено {total_invited} участников в {len(matching_chats)} чатов",
                "total_invited": total_invited,
                "chats_processed": len(matching_chats),
                "details": results
            }
        except Exception as e:
            return {"status": "error", "message": f"Ошибка: {str(e)}"}

    @staticmethod
    def create_subject_chat(user_id: int, chat_name: str, academic_group_id: int) -> dict:
        """E5: Create a subject chat with access control verification"""
        try:
            # Verify access
            access_check = Verificator.can_create_subject_chat(user_id, academic_group_id)
            if access_check["status"] != "allowed":
                return {"status": "error", "message": access_check["message"]}

            # Get academic group to format chat name correctly
            academic_group = GroupStorage.get_group_by_id(academic_group_id)
            if not academic_group:
                return {"status": "error", "message": "Группа не найдена"}

            # Format chat name: [GROUP_NUMBER] SUBJECT
            formatted_name = f"[{academic_group.number}] {chat_name}"

            # Create subject_chat group
            subject_chat = GroupStorage.create_group_if_not_exists(formatted_name, group_type="subject_chat")

            # Record creator
            if GroupStorage.save_group_creator(subject_chat.id, user_id):
                return {
                    "status": "success",
                    "message": f"✅ Чат по предмету '{formatted_name}' создан",
                    "chat": {
                        "id": subject_chat.id,
                        "name": subject_chat.number,
                        "type": subject_chat.group_type,
                        "creator_id": user_id
                    }
                }
            return {"status": "error", "message": "Не удалось сохранить информацию о создателе"}
        except Exception as e:
            return {"status": "error", "message": f"Ошибка при создании чата: {str(e)}"}

    @staticmethod
    def archive_subject_chat(user_id: int, chat_group_id: int) -> dict:
        """E5: Archive a subject chat with access control verification"""
        try:
            # Verify access
            access_check = Verificator.can_archive_subject_chat(user_id, chat_group_id)
            if access_check["status"] != "allowed":
                return {"status": "error", "message": access_check["message"]}

            # Get group info before archiving
            chat_group = GroupStorage.get_group_by_id(chat_group_id)
            if not chat_group:
                return {"status": "error", "message": "Чат не найден"}

            # Archive
            if GroupStorage.archive_group(chat_group_id):
                return {
                    "status": "success",
                    "message": f"✅ Чат '{chat_group.number}' архивирован",
                    "chat": {
                        "id": chat_group_id,
                        "name": chat_group.number,
                        "status": "archived"
                    }
                }
            return {"status": "error", "message": "Не удалось архивировать чат"}
        except Exception as e:
            return {"status": "error", "message": f"Ошибка при архивировании: {str(e)}"}

    @staticmethod
    def unarchive_subject_chat(user_id: int, chat_group_id: int) -> dict:
        """E5: Restore an archived subject chat with access control verification"""
        try:
            # Verify access
            access_check = Verificator.can_unarchive_subject_chat(user_id, chat_group_id)
            if access_check["status"] != "allowed":
                return {"status": "error", "message": access_check["message"]}

            # Get group info before restoring
            chat_group = GroupStorage.get_group_by_id(chat_group_id)
            if not chat_group:
                return {"status": "error", "message": "Чат не найден"}

            # Restore
            if GroupStorage.unarchive_group(chat_group_id):
                return {
                    "status": "success",
                    "message": f"✅ Чат '{chat_group.number}' восстановлен",
                    "chat": {
                        "id": chat_group_id,
                        "name": chat_group.number,
                        "status": "active"
                    }
                }
            return {"status": "error", "message": "Не удалось восстановить чат"}
        except Exception as e:
            return {"status": "error", "message": f"Ошибка при восстановлении: {str(e)}"}

    @staticmethod
    def verify_subject_chat_access(user_id: int, chat_group_id: int, action: str) -> dict:
        """E5: General verification method for any subject chat action"""
        try:
            if action == "create":
                group_id = chat_group_id
                return Verificator.can_create_subject_chat(user_id, group_id)
            elif action == "archive":
                return Verificator.can_archive_subject_chat(user_id, chat_group_id)
            elif action == "unarchive":
                return Verificator.can_unarchive_subject_chat(user_id, chat_group_id)
            elif action == "view":
                return Verificator.can_view_subject_chat(user_id, chat_group_id)
            else:
                return {"status": "error", "message": f"Неизвестное действие: {action}"}
        except Exception as e:
            return {"status": "error", "message": f"Ошибка проверки доступа: {str(e)}"}

    @staticmethod
    def get_aggregated_feed(user_id: int, limit: int = 50, event_type_filter: str = "all") -> dict:
        """
        NSU-052 / F7
        Возвращает агрегированную ленту уведомлений для пользователя.
        Можно фильтровать по типу события.
        """
        try:
            events = Notifier.get_queued_digest_events(user_id=user_id, limit=limit)

            filtered_events = GroupController.filter_feed_events(
                events=events,
                selected_filter=event_type_filter
            )

            feed_items = []
            for event in filtered_events:
                feed_items.append({
                    "id": event.get("id"),
                    "event_type": event.get("event_type"),
                    "message": event.get("message"),
                    "priority": event.get("priority", "normal"),
                    "channels": event.get("channels", ["telegram"]),
                    "created_at": event.get("queued_at") or event.get("created_at")
                })

            return {
                "status": "success",
                "user_id": user_id,
                "event_type_filter": event_type_filter,
                "events_count": len(feed_items),
                "feed": feed_items
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка получения агрегированной ленты: {str(e)}"
            }
    @staticmethod
    def filter_feed_events(events: list, selected_filter: str) -> list:
        """
        NSU-052 / F7
        Фильтрация событий агрегированной ленты по типу.
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


class ScheduleController:
    @staticmethod
    def parse_lesson_input(text: str) -> dict:
        raw = text.strip()
        if "|" not in raw:
            raise ValueError("Используйте формат: Предмет | ЧЧ:ММ-ЧЧ:ММ")

        subject_part, time_part = [part.strip() for part in raw.split("|", 1)]
        if not subject_part or not time_part:
            raise ValueError("Используйте формат: Предмет | ЧЧ:ММ-ЧЧ:ММ")

        start_time, end_time = ScheduleController._parse_time_range(time_part)
        if not ScheduleController._is_valid_time_order(start_time, end_time):
            raise ValueError("Время окончания должно быть больше времени начала")

        return {
            "subject": subject_part,
            "start_time": start_time,
            "end_time": end_time,
        }

    @staticmethod
    def _parse_time_range(time_range: str) -> tuple[str, str]:
        if "-" not in time_range:
            raise ValueError("Используйте формат: ЧЧ:ММ-ЧЧ:ММ")

        start_time, end_time = [part.strip() for part in time_range.split("-", 1)]
        if not re.fullmatch(r"\d{1,2}:\d{2}", start_time) or not re.fullmatch(r"\d{1,2}:\d{2}", end_time):
            raise ValueError("Используйте формат: ЧЧ:ММ-ЧЧ:ММ")

        return start_time, end_time

    @staticmethod
    def _is_valid_time_order(start_time: str, end_time: str) -> bool:
        try:
            start_h, start_m = map(int, start_time.split(":"))
            end_h, end_m = map(int, end_time.split(":"))
        except ValueError:
            return False
        return (end_h * 60 + end_m) > (start_h * 60 + start_m)

    @staticmethod
    def create_schedule_entry(user_id: int, day: str, subject: str, time_range: str) -> dict:
        try:
            start_time, end_time = ScheduleController._parse_time_range(time_range)
            if not ScheduleController._is_valid_time_order(start_time, end_time):
                return {'status': 'error', 'message': 'Время окончания должно быть больше времени начала'}

            if not ScheduleStorage.has_time_conflict(user_id, -1, day, start_time, end_time):
                group = GroupStorage.get_student_group(user_id)
                if group:
                    entry = ScheduleStorage.save_schedule_entry(
                        user_id,
                        group.id,
                        day,
                        subject,
                        start_time,
                        end_time,
                        snapshot_version="manual",
                    )
                    return {'status': 'success', 'entry': entry}
            return {'status': 'error', 'message': 'Конфликт времени'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_schedule_entries(user_id: int, day: str = None) -> list:
        if day is None:
            entries = ScheduleStorage.get_schedule_entries(user_id, day)
            return sorted(entries, key=ScheduleController._schedule_sort_key)

        day_aliases = ScheduleController._get_day_aliases(day)
        if len(day_aliases) == 1:
            entries = ScheduleStorage.get_schedule_entries(user_id, day)
            return sorted(entries, key=ScheduleController._schedule_sort_key)

        entries = ScheduleStorage.get_schedule_entries(user_id)
        filtered = [entry for entry in entries if entry.day_of_week in day_aliases]
        return sorted(filtered, key=ScheduleController._schedule_sort_key)

    @staticmethod
    def update_schedule_entry(user_id: int, entry_id: int, updates: dict) -> bool:
        entry = ScheduleStorage.get_schedule_entry(user_id, entry_id)
        if not entry:
            return False

        next_day = updates.get('day_of_week', entry.day_of_week)
        next_start = updates.get('start_time', entry.start_time)
        next_end = updates.get('end_time', entry.end_time)

        if ('start_time' in updates) or ('end_time' in updates) or ('day_of_week' in updates):
            if not ScheduleController._is_valid_time_order(next_start, next_end):
                return False
            if ScheduleStorage.has_time_conflict(user_id, entry_id, next_day, next_start, next_end):
                return False

        return ScheduleStorage.update_entry_in_database(entry_id, updates, user_id=user_id)

    @staticmethod
    def delete_schedule_entry(user_id: int, entry_id: int) -> bool:
        return ScheduleStorage.delete_entry_from_database(entry_id, user_id=user_id)

    @staticmethod
    def display_schedule(user_id: int, day: str = None) -> str:
        entries = ScheduleController.get_schedule_entries(user_id, day)
        if not entries:
            return "❌ Расписание не найдено"
        result = "📚 Ваше расписание\n\n"
        for entry in entries:
            result += f"📅 {ScheduleController.to_russian_day(entry.day_of_week)}\n"
            result += f"📖 {entry.subject}\n"
            result += f"⏰ {entry.start_time} - {entry.end_time}\n\n"
        return result

    @staticmethod
    def display_nsu_schedule(user_id: int, day: str = None, integration_service: NSUIntegrationService = None) -> str:
        group = GroupStorage.get_student_group(user_id)
        if not group:
            return "❌ Вы не подключены к группе"

        service = integration_service or NSU_INTEGRATION_SERVICE
        try:
            entries = service.get_group_schedule(group.number)
        except (NSUIntegrationError, ValueError) as error:
            return f"❌ Не удалось загрузить расписание НГУ: {error}"

        if day:
            day_aliases = ScheduleController._get_day_aliases(day)
            entries = [entry for entry in entries if entry.day_of_week in day_aliases]

        manual_entries = ScheduleStorage.get_schedule_entries_by_snapshot(user_id, snapshot_version="manual", day=day)
        entries.extend(manual_entries)

        if not entries:
            return "❌ Расписание не найдено"

        entries = sorted(entries, key=ScheduleController._nsu_schedule_sort_key)
        result = f"📚 Расписание группы {group.number}\n\n"
        current_day = None
        for entry in entries:
            if entry.day_of_week != current_day:
                current_day = entry.day_of_week
                result += f"📅 {current_day}\n"
            result += f"⏰ {entry.start_time} - {entry.end_time}\n"
            result += f"📖 {ScheduleController._format_nsu_lesson(entry)}\n\n"
        return result

    @staticmethod
    def display_schedule_changes(user_id: int) -> str:
        changes = ScheduleController.get_schedule_changes(user_id)
        if not changes:
            return "❌ Изменений в расписании не найдено"

        result = "🗂 Что изменилось в расписании\n\n"
        grouped_changes = {
            "added": [],
            "removed": [],
            "modified": [],
        }
        for change in changes:
            grouped_changes.setdefault(change["change_type"], []).append(change)

        labels = {
            "added": "➕ Добавлено",
            "removed": "➖ Удалено",
            "modified": "✏️ Изменено",
        }
        for change_type in ("added", "removed", "modified"):
            items = grouped_changes.get(change_type, [])
            if not items:
                continue
            result += f"{labels[change_type]}:\n"
            for item in items:
                result += f"• {ScheduleController.to_russian_day(item['day'])} {item['time']} — {item['subject']}\n"
                if item.get("details"):
                    result += f"  {item['details']}\n"
            result += "\n"

        return result

    @staticmethod
    def to_russian_day(day: str) -> str:
        return DAY_NAME_EN_TO_RU.get(day, day)

    @staticmethod
    def _get_day_aliases(day: str) -> set[str]:
        aliases = {day}
        en_day = DAY_NAME_RU_TO_EN.get(day)
        ru_day = DAY_NAME_EN_TO_RU.get(day)
        if en_day:
            aliases.add(en_day)
        if ru_day:
            aliases.add(ru_day)
        return aliases

    @staticmethod
    def _schedule_sort_key(entry) -> tuple[int, str, int]:
        return (
            DAY_NAME_ORDER.get(entry.day_of_week, 99),
            entry.start_time,
            entry.id,
        )

    @staticmethod
    def _nsu_schedule_sort_key(entry) -> tuple[int, str, str, str]:
        return (
            DAY_NAME_ORDER.get(entry.day_of_week, 99),
            entry.start_time,
            entry.subject,
            getattr(entry, "lesson_type", ""),
        )

    @staticmethod
    def _format_nsu_lesson(lesson: ParsedScheduleEntry) -> str:
        if not hasattr(lesson, "lesson_type"):
            return lesson.subject
        details = [value for value in [lesson.lesson_type, lesson.teacher, lesson.room, lesson.week] if value]
        if not details:
            return lesson.subject
        return f"{lesson.subject} ({'; '.join(details)})"

    @staticmethod
    def get_filtered_schedule(user_id: int, filters: dict = None) -> list:
        """
        A6: Получить отфильтрованное расписание

        Параметры фильтров:
        - group_id: int - фильтр по ID группы
        - subject: str - фильтр по названию дисциплины (содержит)
        - day_of_week: str - фильтр по дню недели

        Возвращает список записей ScheduleEntry, соответствующих фильтрам
        """
        if filters is None:
            filters = {}

        entries = ScheduleController.get_schedule_entries(user_id)
        if not entries:
            return []

        filtered = entries

        # Фильтр по group_id
        if filters.get("group_id"):
            group_id = int(filters["group_id"])
            filtered = [e for e in filtered if e.group_id == group_id]

        # Фильтр по дню недели
        if filters.get("day_of_week"):
            day_filter = filters["day_of_week"]
            day_aliases = ScheduleController._get_day_aliases(day_filter)
            filtered = [e for e in filtered if e.day_of_week in day_aliases]

        # Фильтр по дисциплине (partial match, case-insensitive)
        if filters.get("subject"):
            subject_filter = filters["subject"].lower()
            filtered = [e for e in filtered if subject_filter in e.subject.lower()]

        return filtered

    @staticmethod
    def sync_nsu_schedule(
            user_id: int,
            group_id: int,
            group_number: str,
            integration_service: NSUIntegrationService = None,
    ) -> dict:
        service = integration_service or NSU_INTEGRATION_SERVICE
        try:
            parsed_schedule = service.get_group_schedule(group_number)
        except (NSUIntegrationError, ValueError) as error:
            return {"status": "error", "message": f"Не удалось загрузить расписание НГУ: {error}"}

        unique_lessons = {}
        for lesson in parsed_schedule:
            lesson_key = (
                lesson.day_of_week,
                lesson.start_time,
                lesson.end_time,
                lesson.discipline_key,
                lesson.teacher_key,
                lesson.room_key,
                lesson.group_key,
                lesson.lesson_type.casefold(),
                lesson.week.casefold(),
            )
            if lesson_key not in unique_lessons:
                unique_lessons[lesson_key] = lesson

        # A3: Promote current snapshot to previous before saving new data
        ScheduleStorage.promote_current_to_previous_for_user(user_id)

        db_entries = [
            {
                "day_of_week": lesson.day_of_week,
                "subject": ScheduleController._format_nsu_subject(lesson),
                "start_time": lesson.start_time,
                "end_time": lesson.end_time,
            }
            for lesson in unique_lessons.values()
        ]
        entries_count = ScheduleStorage.replace_schedule_entries_for_user(user_id, group_id, db_entries)

        # E2: Auto-generate subject_chat groups from schedule
        ScheduleController.auto_generate_subject_groups_from_schedule(user_id, group_id, group_number)

        # A4: Calculate diff between current and previous snapshots
        ScheduleController.calculate_diff_on_sync(user_id, group_id)

        # A5: Publish schedule_updated event
        changes = ScheduleController.get_schedule_changes(user_id)
        EventPublisher.publish_schedule_updated(user_id, group_id, changes)

        return {"status": "success", "entries_count": entries_count}

    @staticmethod
    def _format_nsu_subject(lesson: ParsedScheduleEntry) -> str:
        details = [value for value in [lesson.lesson_type, lesson.teacher, lesson.room, lesson.week] if value]
        if not details:
            return lesson.subject
        return f"{lesson.subject} ({'; '.join(details)})"

    @staticmethod
    def calculate_diff_on_sync(user_id: int, group_id: int) -> dict:
        """Calculate diff between current and previous snapshots after sync."""
        try:
            current = ScheduleStorage.get_schedule_entries_by_snapshot(user_id, "current")
            previous = ScheduleStorage.get_previous_snapshot_for_user(user_id)

            # Clear old diffs before saving new ones
            DiffStorage.clear_diffs_for_user(user_id)

            # Build maps for comparison
            def entry_key(entry):
                return (entry.day_of_week, entry.start_time, entry.end_time)

            current_map = {entry_key(e): e for e in current}
            previous_map = {entry_key(e): e for e in previous}

            changes = {
                'added': [],
                'removed': [],
                'modified': []
            }

            # Detect added lessons
            for key, curr_entry in current_map.items():
                if key not in previous_map:
                    time_str = f"{curr_entry.start_time}-{curr_entry.end_time}"
                    DiffStorage.save_schedule_diff(
                        user_id, group_id, 'added',
                        curr_entry.subject, curr_entry.day_of_week, time_str,
                        f"Новая пара: {curr_entry.subject}"
                    )
                    changes['added'].append({
                        'subject': curr_entry.subject,
                        'day': curr_entry.day_of_week,
                        'time': time_str
                    })

            # Detect removed lessons
            for key, prev_entry in previous_map.items():
                if key not in current_map:
                    time_str = f"{prev_entry.start_time}-{prev_entry.end_time}"
                    DiffStorage.save_schedule_diff(
                        user_id, group_id, 'removed',
                        prev_entry.subject, prev_entry.day_of_week, time_str,
                        f"Отменена пара: {prev_entry.subject}"
                    )
                    changes['removed'].append({
                        'subject': prev_entry.subject,
                        'day': prev_entry.day_of_week,
                        'time': time_str
                    })

            # Detect modified lessons
            for key in set(current_map.keys()) & set(previous_map.keys()):
                curr_entry = current_map[key]
                prev_entry = previous_map[key]

                if curr_entry.subject != prev_entry.subject:
                    time_str = f"{curr_entry.start_time}-{curr_entry.end_time}"
                    change_detail = f"Дисциплина: {prev_entry.subject} → {curr_entry.subject}"
                    DiffStorage.save_schedule_diff(
                        user_id, group_id, 'modified',
                        curr_entry.subject, curr_entry.day_of_week, time_str,
                        change_detail
                    )
                    changes['modified'].append({
                        'type': 'subject',
                        'subject': curr_entry.subject,
                        'day': curr_entry.day_of_week,
                        'time': time_str,
                        'old': prev_entry.subject,
                        'new': curr_entry.subject
                    })

            return {
                'status': 'success',
                'total_changes': len(changes['added']) + len(changes['removed']) + len(changes['modified']),
                'changes': changes
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_schedule_changes(user_id: int) -> list:
        """Get all recent schedule changes for display."""
        diffs = DiffStorage.get_schedule_diffs_for_user(user_id)
        result = []
        for diff in diffs:
            result.append({
                'change_type': diff.change_type,
                'subject': diff.lesson_subject,
                'day': diff.lesson_day,
                'time': diff.lesson_time,
                'details': diff.change_details,
                'created_at': diff.created_at.isoformat() if diff.created_at else None
            })
        return result

    @staticmethod
    def auto_generate_subject_groups_from_schedule(user_id: int, group_id: int, group_number: str) -> dict:
        """E2: Auto-generate subject_chat groups from the current schedule."""
        try:
            entries = ScheduleStorage.get_schedule_entries(user_id)
            if not entries:
                return {"status": "success", "message": "Нет занятий в расписании", "created_count": 0}

            # Extract unique subjects from schedule
            unique_subjects = set()
            for entry in entries:
                subject_name = entry.subject.split('(')[0].strip()
                if subject_name:
                    unique_subjects.add(subject_name)

            # Create subject_chat group for each unique subject
            created_groups = []
            for subject in sorted(unique_subjects):
                subject_group_name = f"[{group_number}] {subject}"
                subject_group = GroupStorage.create_group_if_not_exists(subject_group_name, group_type="subject_chat")
                created_groups.append({
                    "id": subject_group.id,
                    "name": subject_group_name,
                    "type": subject_group.group_type,
                    "subject": subject
                })

            return {
                "status": "success",
                "message": f"Создано {len(created_groups)} групп-чатов по предметам",
                "created_count": len(created_groups),
                "groups": created_groups
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка при создании групп-чатов: {str(e)}",
                "created_count": 0
            }


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


class NoteController:
    @staticmethod
    def create_personal_note(user_id: int, title: str, content: str) -> dict:
        try:
            note = NoteStorage.create_note(
                owner_id=user_id,
                title=title,
                content=content,
                visibility='personal',
            )
            return {'status': 'success', 'note': note}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_personal_notes(user_id: int) -> list:
        return NoteStorage.get_personal_notes(user_id)

    @staticmethod
    def update_personal_note(user_id: int, note_id: int, updates: dict) -> dict:
        note = NoteStorage.get_note_by_id(note_id)
        if not note:
            return {'status': 'error', 'message': 'Заметка не найдена'}
        if note.owner_id != user_id:
            return {'status': 'error', 'message': 'Нет доступа к этой заметке'}
        if note.visibility != 'personal':
            return {'status': 'error', 'message': 'Это не личная заметка'}
        allowed = {'title', 'content'}
        filtered = {k: v for k, v in updates.items() if k in allowed}
        if not filtered:
            return {'status': 'error', 'message': 'Нет допустимых полей для обновления'}
        if NoteStorage.update_note(note_id, filtered):
            return {'status': 'success'}
        return {'status': 'error', 'message': 'Не удалось обновить заметку'}

    @staticmethod
    def delete_personal_note(user_id: int, note_id: int) -> dict:
        note = NoteStorage.get_note_by_id(note_id)
        if not note:
            return {'status': 'error', 'message': 'Заметка не найдена'}
        if note.owner_id != user_id:
            return {'status': 'error', 'message': 'Нет доступа к этой заметке'}
        if note.visibility != 'personal':
            return {'status': 'error', 'message': 'Это не личная заметка'}
        if NoteStorage.delete_note(note_id):
            return {'status': 'success'}
        return {'status': 'error', 'message': 'Не удалось удалить заметку'}

    @staticmethod
    def display_personal_notes(user_id: int) -> str:
        notes = NoteStorage.get_personal_notes(user_id)
        if not notes:
            return '❌ Личных заметок не найдено'
        result = '📒 Ваши личные заметки\n\n'
        for note in notes:
            result += f'📝 [{note.id}] {note.title}\n'
            result += f'{note.content[:100]}{"..." if len(note.content) > 100 else ""}\n'
            result += f'🔄 v{note.version}\n\n'
        return result

    @staticmethod
    def create_discipline_note(user_id: int, group_id: int, title: str, content: str, subject_name: str) -> dict:
        try:
            user_group = GroupStorage.get_student_group(user_id)
            if not user_group or user_group.id != group_id:
                return {'status': 'error', 'message': 'Нет доступа к этой группе'}

            note = NoteStorage.create_discipline_note(user_id, group_id, title, content, subject_name)
            return {'status': 'success', 'note': note}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_discipline_notes(user_id: int, group_id: int, subject_name: str = None) -> dict:
        try:
            user_group = GroupStorage.get_student_group(user_id)
            if not user_group or user_group.id != group_id:
                return {'status': 'error', 'message': 'Нет доступа', 'notes': []}

            notes = NoteStorage.get_discipline_notes(group_id, subject_name)
            return {'status': 'success', 'notes': notes}
        except Exception as e:
            return {'status': 'error', 'message': str(e), 'notes': []}

    @staticmethod
    def update_discipline_note(user_id: int, note_id: int, updates: dict) -> dict:
        try:
            note = NoteStorage.get_note_by_id(note_id)
            if not note:
                return {'status': 'error', 'message': 'Заметка не найдена'}

            user_group = GroupStorage.get_student_group(user_id)
            if not user_group or user_group.id != note.group_id:
                return {'status': 'error', 'message': 'Нет прав для редактирования'}

            allowed = {'title', 'content'}
            filtered = {k: v for k, v in updates.items() if k in allowed}
            if not filtered:
                return {'status': 'error', 'message': 'Нет допустимых полей для обновления'}

            if NoteStorage.update_note(note_id, filtered):
                return {'status': 'success'}
            return {'status': 'error', 'message': 'Не удалось обновить заметку'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def delete_discipline_note(user_id: int, note_id: int) -> dict:
        try:
            note = NoteStorage.get_note_by_id(note_id)
            if not note:
                return {'status': 'error', 'message': 'Заметка не найдена'}

            user_group = GroupStorage.get_student_group(user_id)
            if not user_group or user_group.id != note.group_id:
                return {'status': 'error', 'message': 'Нет прав для удаления'}

            if NoteStorage.delete_note(note_id):
                return {'status': 'success'}
            return {'status': 'error', 'message': 'Не удалось удалить заметку'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


class GmailController:
    _AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
    _SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
    _STATE_TTL_MINUTES = 10

    @staticmethod
    def generate_oauth_url(user_id: int) -> str:
        """Создаёт state-токен в БД и возвращает ссылку для авторизации Gmail."""
        state = secrets.token_urlsafe(32)
        db = get_db()
        try:
            db.query(GmailOAuthState).filter_by(user_id=user_id).delete()
            db.add(GmailOAuthState(state=state, user_id=user_id, created_at=datetime.utcnow()))
            db.commit()
        finally:
            db.close()
        params = {
            "client_id": GMAIL_CLIENT_ID,
            "redirect_uri": GMAIL_REDIRECT_URI,
            "response_type": "code",
            "scope": GmailController._SCOPE,
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        return GmailController._AUTH_URL + "?" + urllib.parse.urlencode(params)

    @staticmethod
    def validate_and_consume_state(state: str) -> int | None:
        """Проверяет state из БД, удаляет его и возвращает user_id. None если невалидный."""
        db = get_db()
        try:
            record = db.query(GmailOAuthState).filter_by(state=state).first()
            if not record:
                return None
            expired = (datetime.utcnow() - record.created_at).total_seconds() > GmailController._STATE_TTL_MINUTES * 60
            db.delete(record)
            db.commit()
            return None if expired else record.user_id
        finally:
            db.close()

    @staticmethod
    def save_tokens(user_id: int, access_token: str, refresh_token: str | None,
                    token_expiry: datetime, scope: str) -> None:
        """Шифрует и сохраняет токены в GmailToken. Обновляет запись если уже есть."""
        db = get_db()
        try:
            record = db.query(GmailToken).filter_by(user_id=user_id).first()
            if not record:
                record = GmailToken(user_id=user_id)
                db.add(record)
            record.access_token = crypto.encrypt(access_token)
            record.refresh_token = crypto.encrypt(refresh_token) if refresh_token else None
            record.token_expiry = token_expiry
            record.is_linked = True
            record.linked_at = datetime.utcnow()
            record.scope = scope
            db.commit()
        finally:
            db.close()

    @staticmethod
    def get_link_status(user_id: int) -> bool:
        """Возвращает True если Gmail привязан."""
        db = get_db()
        try:
            record = db.query(GmailToken).filter_by(user_id=user_id).first()
            return record is not None and record.is_linked
        finally:
            db.close()

    @staticmethod
    def get_inbox_messages(user_id: int, max_results: int = 10) -> list:
        """Возвращает входящие письма пользователя. Автоматически обновляет истёкший токен."""
        db = get_db()
        try:
            record = db.query(GmailToken).filter_by(user_id=user_id).first()
            if not record or not record.is_linked:
                raise GmailIntegrationError("Gmail не привязан. Используйте кнопку '📧 Привязать Gmail'.")

            access_token = crypto.decrypt(record.access_token)
            token_expiry = record.token_expiry
            encrypted_refresh = record.refresh_token

            if token_expiry and datetime.utcnow() >= token_expiry - timedelta(seconds=60):
                if not encrypted_refresh:
                    raise GmailIntegrationError("Токен истёк. Привяжите Gmail заново.")
                token_resp = GmailService.refresh_access_token(
                    refresh_token=crypto.decrypt(encrypted_refresh),
                    client_id=GMAIL_CLIENT_ID,
                    client_secret=GMAIL_CLIENT_SECRET,
                )
                access_token = token_resp["access_token"]
                record.access_token = crypto.encrypt(access_token)
                record.token_expiry = datetime.utcnow() + timedelta(seconds=token_resp.get("expires_in", 3600))
                db.commit()
        finally:
            db.close()

        return GmailService.fetch_messages(access_token, max_results)

    @staticmethod
    def get_important_inbox(user_id: int, max_results: int = 20) -> list:
        """Возвращает только важные письма (от доменов НГУ). Читает с запасом, т.к. фильтр сужает выборку."""
        messages = GmailController.get_inbox_messages(user_id, max_results)
        return GmailFilter.filter_important(messages)
