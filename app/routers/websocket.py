import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.websocket_manager import manager
from app.auth import decode_access_token


logger = logging.getLogger(__name__)

router = APIRouter(tags=['WebSocket'])


@router.websocket('/ws/notifications')
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(...)  # jwt token passed as query params
):
    """
    WebSocket endpoint for real-time notifications.

    Connect with:
        ws://localhost:8001/ws/notifications?token=<access_token>

    Server pushes messages in this format:
        {
            "type": "new_notification",
            "data": {
                "id": 1,
                "title": "Application received",
                "message": "...",
                "notification_type": "application",
                "is_read": false,
                "created_at": "2026-06-22T..."
            }
        }
    """
    # validate jwt token before accepting connection
    payload = decode_access_token(token)

    if not payload:
        # reject connection with 4001 (custom code -auth failed)
        await websocket.close(code=4001, reason='Invalid or expired token')
        return

    user_id = payload.get('user_id')
    if not user_id:
        await websocket.close(code=4001, reason='Invalid token payload')
        return

    # accept and register the conn
    await manager.connect(websocket, user_id)

    # send connection confirmation
    await websocket.send_json({
        'type': 'connected',
        'data': {
            'user_id': user_id,
            'message': 'Connected to notification stream',

        }
    })
    try:
        # keep the connection alive - wait for messages from client
        while True:
            # recive kepps the conn open
            # client can send ping or any message to keep alive
            data = await websocket.receive_text()
            logger.info(f"[WS] recieved from user_id={user_id}: {data}")

            # respond to ping with pong
            if data == 'ping':
                await websocket.send_json({'type': 'pong'})

    except WebSocketDisconnect:
        # cleimt disconnected - clean uo
        manager.disconnect(websocket, user_id)
