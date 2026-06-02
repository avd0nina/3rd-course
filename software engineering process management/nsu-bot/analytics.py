import json
from datetime import datetime

from database import EventLog as EventLogModel
from storage import get_db
from notifier import Notifier


class AnalyticsTracker:
    """
    NSU-053 / F8:
    Метрики открытий и кликов по уведомлениям.

    metric_type:
    - open
    - click
    """

    VALID_METRICS = ["open", "click"]

    @staticmethod
    def validate_metric_type(metric_type: str) -> str:
        if metric_type not in AnalyticsTracker.VALID_METRICS:
            return "open"
        return metric_type

    @staticmethod
    def track_notification_metric(
        user_id: int,
        metric_type: str,
        notification_id: int = None,
        event_type: str = None,
        target: str = None,
        metadata: dict = None
    ) -> dict:
        """
        Записать метрику открытия/клика уведомления.
        """
        try:
            normalized_metric = AnalyticsTracker.validate_metric_type(metric_type)

            event_data = {
                "metric_type": normalized_metric,
                "notification_id": notification_id,
                "source_event_type": event_type,
                "target": target,
                "metadata": metadata or {},
                "tracked_at": datetime.utcnow().isoformat()
            }

            Notifier.log_event(
                event_type=f"notification_{normalized_metric}",
                user_id=user_id,
                group_id=None,
                event_data=event_data
            )

            return {
                "status": "success",
                "message": f"Метрика {normalized_metric} сохранена",
                "metric": event_data
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка сохранения метрики: {str(e)}"
            }

    @staticmethod
    def get_notification_metrics(user_id: int = None, metric_type: str = None, limit: int = 100) -> dict:
        """
        Получить список метрик открытий/кликов.
        """
        try:
            db = get_db()

            allowed_event_types = ["notification_open", "notification_click"]

            query = db.query(EventLogModel).filter(
                EventLogModel.event_type.in_(allowed_event_types)
            )

            if user_id is not None:
                query = query.filter(EventLogModel.user_id == user_id)

            if metric_type in AnalyticsTracker.VALID_METRICS:
                query = query.filter(EventLogModel.event_type == f"notification_{metric_type}")

            events = query.order_by(EventLogModel.created_at.desc()).limit(limit).all()

            metrics = []
            for event in events:
                event_data = {}
                if event.event_data:
                    try:
                        event_data = json.loads(event.event_data)
                    except Exception:
                        event_data = {}

                metrics.append({
                    "id": event.id,
                    "user_id": event.user_id,
                    "event_type": event.event_type,
                    "metric_type": event_data.get("metric_type"),
                    "notification_id": event_data.get("notification_id"),
                    "source_event_type": event_data.get("source_event_type"),
                    "target": event_data.get("target"),
                    "metadata": event_data.get("metadata", {}),
                    "tracked_at": event_data.get("tracked_at"),
                    "created_at": event.created_at.isoformat() if event.created_at else None
                })

            db.close()

            return {
                "status": "success",
                "metrics_count": len(metrics),
                "metrics": metrics
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка получения метрик: {str(e)}"
            }

    @staticmethod
    def get_notification_metrics_summary(user_id: int = None) -> dict:
        """
        Получить краткую сводку по открытиям и кликам.
        """
        try:
            metrics_result = AnalyticsTracker.get_notification_metrics(user_id=user_id, limit=1000)

            if metrics_result["status"] != "success":
                return metrics_result

            metrics = metrics_result["metrics"]

            opens_count = len([m for m in metrics if m["metric_type"] == "open"])
            clicks_count = len([m for m in metrics if m["metric_type"] == "click"])

            ctr = 0
            if opens_count > 0:
                ctr = round(clicks_count / opens_count, 4)

            return {
                "status": "success",
                "user_id": user_id,
                "opens_count": opens_count,
                "clicks_count": clicks_count,
                "ctr": ctr
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка получения сводки метрик: {str(e)}"
            }