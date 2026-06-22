import time
import uuid
import logging
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """
    Pure ASGI middleware — no BaseHTTPMiddleware issues.
    Logs every request with method, path, status, and timing.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        # only handle HTTP requests — ignore websockets and lifespan events
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        method = scope.get('method', '')
        path = scope.get('path', '')
        status_code = 500

        # store request_id in scope state for endpoints to access
        if 'state' not in scope:
            scope['state'] = {}
        scope['state']['request_id'] = request_id

        logger.info(f"[{request_id}] -> {method} {path}")

        async def send_wrapper(message):
            nonlocal status_code
            if message['type'] == 'http.response.start':
                status_code = message.get('status', 500)
                # inject X-Request-ID into response headers
                headers = list(message.get('headers', []))
                headers.append((b'x-request-id', request_id.encode()))
                message = {**message, 'headers': headers}
            await send(message)

        await self.app(scope, receive, send_wrapper)

        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(
            f"[{request_id} <- {method} {path}]"
            f" status={status_code} duration={duration_ms}ms"
        )


class AuditMiddleware:
    """
    Pure ASGI middleware for audit trail.
    Logs authenticated user actions on state-changing requests.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        method = scope.get('method', '')
        path = scope.get('path', '')

        # extract user info from Authorization header
        headers = dict(scope.get('headers', []))
        auth_header = headers.get(b'authorization', b'').decode()
        user_info = 'anonymous'

        if auth_header.startswith('Bearer '):
            try:
                from app.auth import decode_access_token
                token = auth_header.split(' ')[1]
                payload = decode_access_token(token)
                if payload:
                    user_info = (
                        f"user_id={payload.get('user_id')} "
                        f"username={payload.get('username')}"
                    )
            except Exception:
                pass

        status_code = 500

        async def send_wrapper(message):
            nonlocal status_code
            if message['type'] == 'http.response.start':
                status_code = message.get('status', 500)
            await send(message)

        await self.app(scope, receive, send_wrapper)

        if method in ('POST', 'PATCH', 'PUT', 'DELETE'):
            logger.info(
                f"[AUDIT] {user_info} | "
                f"{method} {path} | "
                f"status={status_code}"
            )