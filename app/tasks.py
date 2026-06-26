import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def log_notification_created(notification_id: int, user_id: int, title: str) -> None:
    """
    Logs notification creation after the response is sent
    Runs in background - client doesnt wait for this
    """

    logger.info(
        f"[NOTIFICATION CREATED] id={notification_id} "
        f"user_id={user_id} titile='{title}' "
        f"at={datetime.now(timezone.utc).isoformat()}"
    )


def simulate_push_notification(user_id: int, title: str, message: str) -> None:
    """
    Simulation of sending a push notification to a mobile device
    """
    logger.info(
        f"[PUSH NOTIFICATION] -> user_id={user_id} "
        f"title='{title}' message='{message[:50]}...'"
    )
    # in prod we use:
    # firebase_client.send(user_id=user_id, title=title, body=message)


def log_notification_read(notification_id: int, user_id: int) -> None:
    """
    Logs when a notification is marked read
    used for analytics - example: which notifications get read, how quickly
    """
    logger.info(
        f"[NOTIFICATION READ] id={notification_id} "
        f"user_id={user_id} "
        f"at={datetime.now(timezone.utc).isoformat()}"
    )


async def push_websocket_notification(user_id: int, notification_data: dict) -> None:
    """
    Push a real-time notifiation to the user via ws
    runs as a background task after the http response is sent
    """
    from app.websocket_manager import manager

    await manager.send_to_user(
        user_id=user_id,
        message={
            'type': 'new_notification',
            'data': notification_data
        }
    )
