import json
from datetime import datetime
from database import ScheduleUpdatedEvent as ScheduleUpdatedEventModel
from database import EventLog as EventLogModel
from storage import get_db


class ScheduleUpdatedEvent:
    """Событие об обновлении расписания"""
    
    def __init__(self, user_id: int, group_id: int, changes: dict = None):
        self.user_id = user_id
        self.group_id = group_id
        self.timestamp = datetime.utcnow()
        self.changes = changes or {}
        self.event_type = 'schedule_updated'
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'group_id': self.group_id,
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
            'changes': self.changes
        }

class EventPublisher:
    """Публикатор событий"""
    
    @staticmethod
    def publish_schedule_updated(user_id: int, group_id: int, changes: dict = None) -> dict:
        """Опубликовать событие об обновлении расписания"""
        try:
            event = ScheduleUpdatedEvent(user_id, group_id, changes)
            db = get_db()
            
            event_record = ScheduleUpdatedEventModel(
                user_id=user_id,
                group_id=group_id,
                event_type='schedule_updated',
                timestamp=event.timestamp,
                changes_json=json.dumps(event.to_dict()),
                is_processed=False
            )
            
            db.add(event_record)
            db.commit()
            db.refresh(event_record)
            db.close()
            
            Notifier.log_event('schedule_updated', user_id, group_id, event.to_dict())
            
            return {
                'status': 'published',
                'event_id': event_record.id,
                'message': 'Событие об обновлении расписания опубликовано'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }


class Notifier:
    """Система уведомлений и логирования событий"""
    
    @staticmethod
    def log_event(event_type: str, user_id: int = None, group_id: int = None, event_data: dict = None) -> None:
        """Залогировать событие"""
        try:
            db = get_db()
            
            log_record = EventLogModel(
                event_type=event_type,
                user_id=user_id,
                group_id=group_id,
                event_data=json.dumps(event_data) if event_data else None,
                status='logged',
                created_at=datetime.utcnow()
            )
            
            db.add(log_record)
            db.commit()
            db.close()
        except Exception as e:
            print(f"Ошибка при логировании события: {str(e)}")

    @staticmethod
    def get_group_events(group_id: int, event_type_prefix: str = None, limit: int = 100) -> list:
        """Получить события EventLog для группы"""
        try:
            db = get_db()

            query = db.query(EventLogModel).filter(
                EventLogModel.group_id == group_id
            )

            events = query.order_by(EventLogModel.created_at.desc()).limit(limit).all()

            db.close()

            result = []
            for event in events:
                event_data = {}
                if event.event_data:
                    try:
                        event_data = json.loads(event.event_data)
                    except Exception:
                        event_data = {}

                if event_type_prefix and not event.event_type.startswith(event_type_prefix):
                    continue

                result.append({
                    "id": event.id,
                    "event_type": event.event_type,
                    "user_id": event.user_id,
                    "group_id": event.group_id,
                    "event_data": event_data,
                    "status": event.status,
                    "created_at": event.created_at.isoformat() if event.created_at else None
                })

            return result

        except Exception as e:
            print(f"Ошибка при получении событий группы: {str(e)}")
            return []
    
    @staticmethod
    def get_events_for_user(user_id: int, event_type: str = None, limit: int = 20) -> list:
        """Получить события для студента"""
        try:
            db = get_db()
            
            query = db.query(ScheduleUpdatedEventModel).filter(
                ScheduleUpdatedEventModel.user_id == user_id
            )
            
            if event_type:
                query = query.filter(ScheduleUpdatedEventModel.event_type == event_type)
            
            events = query.order_by(ScheduleUpdatedEventModel.created_at.desc()).limit(limit).all()
            db.close()
            
            result = []
            for event in events:
                result.append({
                    'id': event.id,
                    'event_type': event.event_type,
                    'user_id': event.user_id,
                    'group_id': event.group_id,
                    'timestamp': event.timestamp.isoformat(),
                    'changes': json.loads(event.changes_json) if event.changes_json else None,
                    'is_processed': event.is_processed,
                    'created_at': event.created_at.isoformat()
                })
            
            return result
        except Exception as e:
            print(f"Ошибка при получении событий: {str(e)}")
            return []
    
    @staticmethod
    def mark_event_processed(event_id: int) -> bool:
        """Отметить событие как обработанное"""
        try:
            db = get_db()
            
            event = db.query(ScheduleUpdatedEventModel).filter(
                ScheduleUpdatedEventModel.id == event_id
            ).first()
            
            if event:
                event.is_processed = True
                db.commit()
                db.close()
                return True
            
            db.close()
            return False
        except Exception as e:
            print(f"Ошибка при обновлении статуса события: {str(e)}")
            return False
    
    @staticmethod
    def get_unprocessed_events(limit: int = 50) -> list:
        """Получить необработанные события"""
        try:
            db = get_db()
            
            events = db.query(ScheduleUpdatedEventModel).filter(
                ScheduleUpdatedEventModel.is_processed == False
            ).order_by(ScheduleUpdatedEventModel.created_at.asc()).limit(limit).all()
            
            db.close()
            
            result = []
            for event in events:
                result.append({
                    'id': event.id,
                    'event_type': event.event_type,
                    'user_id': event.user_id,
                    'group_id': event.group_id,
                    'timestamp': event.timestamp.isoformat(),
                    'changes': json.loads(event.changes_json) if event.changes_json else None
                })
            
            return result
        except Exception as e:
            print(f"Ошибка при получении необработанных событий: {str(e)}")
            return []


    PRIORITY_LEVELS = ["critical", "high", "normal", "low"]

    @staticmethod
    def validate_priority(priority: str) -> str:
        """Проверка уровня приоритета"""
        if priority not in Notifier.PRIORITY_LEVELS:
            return "normal"  # дефолтный уровень
        return priority

    @staticmethod
    def should_send_immediately(priority: str) -> bool:
        """
        NSU-048 / F3:
        high и critical отправляются сразу.
        normal и low уходят в обычную очередь/дайджест.
        """
        normalized_priority = Notifier.validate_priority(priority)
        return normalized_priority in ["high", "critical"]

    @staticmethod
    def send_notification(user_id: int, event_type: str, message: str, priority: str = "normal",
                          channels: list = None, group_id: int = None, event_data: dict = None) -> dict:
        """
        NSU-048 / F3:
        Отправка уведомления с учётом приоритета.

        - critical/high: мгновенная отправка
        - normal/low: логируется как queued_for_digest, будет обработано в F4
        """
        try:
            normalized_priority = Notifier.validate_priority(priority)
            delivery_channels = channels or ["telegram"]

            notification_data = {
                "event_type": event_type,
                "message": message,
                "priority": normalized_priority,
                "channels": delivery_channels,
                "delivery_mode": "instant" if Notifier.should_send_immediately(normalized_priority) else "digest",
            }

            if event_data:
                notification_data.update(event_data)

            if Notifier.should_send_immediately(normalized_priority):
                Notifier.log_event(
                    event_type="notification_sent_instant",
                    user_id=user_id,
                    group_id=group_id,
                    event_data={
                        **notification_data,
                        "delivery_status": "sent",
                        "sent_at": datetime.utcnow().isoformat()
                    }
                )

                return {
                    "status": "sent",
                    "delivery_mode": "instant",
                    "priority": normalized_priority,
                    "channels": delivery_channels,
                    "message": "Уведомление отправлено мгновенно"
                }

            Notifier.log_event(
                event_type="notification_queued_for_digest",
                user_id=user_id,
                group_id=group_id,
                event_data={
                    **notification_data,
                    "delivery_status": "queued",
                    "queued_at": datetime.utcnow().isoformat()
                }
            )

            return {
                "status": "queued",
                "delivery_mode": "digest",
                "priority": normalized_priority,
                "channels": delivery_channels,
                "message": "Уведомление добавлено в дайджест"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка отправки уведомления: {str(e)}"
            }

    @staticmethod
    def get_queued_digest_events(user_id: int = None, limit: int = 100) -> list:
        """
        NSU-049 / F4:
        Получить normal/low уведомления, которые ждут батч-дайджеста.
        """
        try:
            db = get_db()

            query = db.query(EventLogModel).filter(
                EventLogModel.event_type == "notification_queued_for_digest",
                EventLogModel.status == "logged"
            )

            if user_id is not None:
                query = query.filter(EventLogModel.user_id == user_id)

            events = query.order_by(EventLogModel.created_at.asc()).limit(limit).all()

            result = []
            for event in events:
                event_data = {}
                if event.event_data:
                    try:
                        event_data = json.loads(event.event_data)
                    except Exception:
                        event_data = {}

                result.append({
                    "id": event.id,
                    "user_id": event.user_id,
                    "group_id": event.group_id,
                    "event_type": event_data.get("event_type"),
                    "message": event_data.get("message"),
                    "priority": event_data.get("priority", "normal"),
                    "channels": event_data.get("channels", ["telegram"]),
                    "queued_at": event_data.get("queued_at"),
                    "created_at": event.created_at.isoformat() if event.created_at else None
                })

            db.close()
            return result

        except Exception as e:
            print(f"Ошибка при получении уведомлений для дайджеста: {str(e)}")
            return []

    @staticmethod
    def send_batch_digest(user_id: int = None, limit: int = 100) -> dict:
        """
        NSU-049 / F4:
        Сформировать батч-дайджест для normal/low уведомлений.

        Берёт queued уведомления, группирует по пользователю,
        логирует отправку digest и помечает исходные события как processed.
        """
        try:
            queued_events = Notifier.get_queued_digest_events(user_id=user_id, limit=limit)

            if not queued_events:
                return {
                    "status": "success",
                    "message": "Нет уведомлений для дайджеста",
                    "digests_sent": 0,
                    "events_processed": 0,
                    "digests": []
                }

            events_by_user = {}
            for event in queued_events:
                events_by_user.setdefault(event["user_id"], []).append(event)

            db = get_db()
            digests = []
            processed_event_ids = []

            for target_user_id, events in events_by_user.items():
                digest_items = []

                for event in events:
                    digest_items.append({
                        "event_id": event["id"],
                        "event_type": event["event_type"],
                        "message": event["message"],
                        "priority": event["priority"],
                        "queued_at": event["queued_at"] or event["created_at"]
                    })
                    processed_event_ids.append(event["id"])

                digest_text = "📬 Дайджест уведомлений\n\n"
                for index, item in enumerate(digest_items, 1):
                    digest_text += (
                        f"{index}. [{item['priority']}] "
                        f"{item['event_type']}: {item['message']}\n"
                    )

                Notifier.log_event(
                    event_type="notification_digest_sent",
                    user_id=target_user_id,
                    group_id=None,
                    event_data={
                        "delivery_mode": "digest",
                        "items_count": len(digest_items),
                        "items": digest_items,
                        "digest_text": digest_text,
                        "sent_at": datetime.utcnow().isoformat()
                    }
                )

                digests.append({
                    "user_id": target_user_id,
                    "items_count": len(digest_items),
                    "digest_text": digest_text
                })

            if processed_event_ids:
                db.query(EventLogModel).filter(
                    EventLogModel.id.in_(processed_event_ids)
                ).update(
                    {"status": "processed"},
                    synchronize_session=False
                )
                db.commit()

            db.close()

            return {
                "status": "success",
                "message": f"Сформировано дайджестов: {len(digests)}",
                "digests_sent": len(digests),
                "events_processed": len(processed_event_ids),
                "digests": digests
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка формирования дайджеста: {str(e)}"
            }