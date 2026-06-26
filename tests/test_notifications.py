import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app
from starlette.websockets import WebSocketDisconnect


class TestCreateNotification:

    async def test_create_notification_success(self, client: AsyncClient, registered_user):
        """Successfully creates a notification."""
        response = await client.post('/notifications/', json={
            'user_id': registered_user['id'],
            'title': 'New application',
            'message': 'You have a new application.',
            'notification_type': 'application',
        })

        assert response.status_code == 201
        data = response.json()
        assert data['title'] == 'New application'
        assert data['message'] == 'You have a new application.'
        assert data['notification_type'] == 'application'
        assert data['is_read'] is False
        assert data['read_at'] is None
        assert 'id' in data
        assert 'created_at' in data

    async def test_create_notification_empty_title_rejected(
        self, client: AsyncClient, registered_user
    ):
        """Empty title rejected by Pydantic validation."""
        response = await client.post('/notifications/', json={
            'user_id': registered_user['id'],
            'title': '',  # empty
            'message': 'Valid message.',
        })

        assert response.status_code == 422

    async def test_create_notification_default_type(
        self, client: AsyncClient, registered_user
    ):
        """Notification type defaults to info if not provided."""
        response = await client.post('/notifications/', json={
            'user_id': registered_user['id'],
            'title': 'Test',
            'message': 'Test message.',
        })

        assert response.status_code == 201
        assert response.json()['notification_type'] == 'info'

    async def test_create_notification_with_extra_data(
        self, client: AsyncClient, registered_user
    ):
        """Notification with extra_data stores and returns JSON."""
        response = await client.post('/notifications/', json={
            'user_id': registered_user['id'],
            'title': 'Status changed',
            'message': 'Your application status changed.',
            'extra_data': {'job_id': 42, 'old_status': 'pending', 'new_status': 'reviewing'},
        })

        assert response.status_code == 201
        data = response.json()
        assert data['extra_data']['job_id'] == 42
        assert data['extra_data']['old_status'] == 'pending'


class TestListNotifications:

    async def test_list_requires_auth(self, client: AsyncClient):
        """Unauthenticated list returns 401."""
        response = await client.get('/notifications/')
        assert response.status_code == 401

    async def test_list_returns_user_notifications(
        self, client: AsyncClient, registered_user, auth_headers, sample_notification
    ):
        """Authenticated user sees their own notifications."""
        response = await client.get('/notifications/', headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['id'] == sample_notification['id']

    async def test_list_filter_unread_only(
        self, client: AsyncClient, registered_user, auth_headers
    ):
        """unread_only=true filters out read notifications."""
        # create two notifications
        for i in range(2):
            await client.post('/notifications/', json={
                'user_id': registered_user['id'],
                'title': f'Notification {i}',
                'message': 'Test.',
            })

        # mark first one as read
        all_notifications = await client.get(
            '/notifications/', headers=auth_headers
        )
        first_id = all_notifications.json()[0]['id']
        await client.patch(
            f'/notifications/{first_id}/read',
            headers=auth_headers
        )

        # filter unread only
        response = await client.get(
            '/notifications/?unread_only=true',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert all(not n['is_read'] for n in data)

    async def test_list_filter_by_type(
        self, client: AsyncClient, registered_user, auth_headers
    ):
        """notification_type filter returns only matching type."""
        # create two different types
        await client.post('/notifications/', json={
            'user_id': registered_user['id'],
            'title': 'App notification',
            'message': 'Test.',
            'notification_type': 'application',
        })
        await client.post('/notifications/', json={
            'user_id': registered_user['id'],
            'title': 'Info notification',
            'message': 'Test.',
            'notification_type': 'info',
        })

        response = await client.get(
            '/notifications/?notification_type=application',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['notification_type'] == 'application'

    async def test_list_pagination(
        self, client: AsyncClient, registered_user, auth_headers
    ):
        """Pagination skip and limit work correctly."""
        # create 5 notifications
        for i in range(5):
            await client.post('/notifications/', json={
                'user_id': registered_user['id'],
                'title': f'Notification {i}',
                'message': 'Test.',
            })

        # get first 3
        response = await client.get(
            '/notifications/?skip=0&limit=3',
            headers=auth_headers
        )
        assert len(response.json()) == 3

        # get next 2
        response = await client.get(
            '/notifications/?skip=3&limit=3',
            headers=auth_headers
        )
        assert len(response.json()) == 2

    async def test_user_cannot_see_other_users_notifications(
        self, client: AsyncClient, registered_user, auth_headers
    ):
        """User only sees their own notifications — not others'."""
        # create notification for user 999 (different user)
        await client.post('/notifications/', json={
            'user_id': 999,
            'title': 'Other user notification',
            'message': 'Should not be visible.',
        })

        # alice should not see user 999's notification
        response = await client.get('/notifications/', headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(n['user_id'] == registered_user['id'] for n in data)


class TestMarkAsRead:

    async def test_mark_as_read_success(
        self, client: AsyncClient, auth_headers, sample_notification
    ):
        """Marking notification as read sets is_read=True and read_at."""
        notification_id = sample_notification['id']

        response = await client.patch(
            f'/notifications/{notification_id}/read',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['is_read'] is True
        assert data['read_at'] is not None

    async def test_mark_nonexistent_notification(
        self, client: AsyncClient, auth_headers
    ):
        """Marking a non-existent notification returns 404."""
        response = await client.patch(
            '/notifications/99999/read',
            headers=auth_headers
        )
        assert response.status_code == 404

    async def test_cannot_mark_other_users_notification(
        self, client: AsyncClient, auth_headers, registered_user
    ):
        """Cannot mark another user's notification as read."""
        # create notification for user 999
        other_notification = await client.post('/notifications/', json={
            'user_id': 999,
            'title': 'Other user',
            'message': 'Not yours.',
        })
        other_id = other_notification.json()['id']

        # alice tries to mark it — should get 404
        response = await client.patch(
            f'/notifications/{other_id}/read',
            headers=auth_headers
        )
        assert response.status_code == 404


class TestUnreadCount:

    async def test_unread_count_empty(
        self, client: AsyncClient, auth_headers
    ):
        """Unread count is 0 when no notifications exist."""
        response = await client.get('/notifications/unread-count', headers=auth_headers)

        assert response.status_code == 200
        assert response.json()['count'] == 0

    async def test_unread_count_decreases_after_read(
        self, client: AsyncClient, registered_user, auth_headers
    ):
        """Unread count decreases after marking notifications as read."""
        # create 3 notifications
        ids = []
        for i in range(3):
            r = await client.post('/notifications/', json={
                'user_id': registered_user['id'],
                'title': f'Notification {i}',
                'message': 'Test.',
            })
            ids.append(r.json()['id'])

        # count should be 3
        response = await client.get(
            '/notifications/unread-count', headers=auth_headers
        )
        assert response.json()['count'] == 3

        # mark one as read
        await client.patch(f'/notifications/{ids[0]}/read', headers=auth_headers)

        # count should be 2
        response = await client.get(
            '/notifications/unread-count', headers=auth_headers
        )
        assert response.json()['count'] == 2


class TestMarkAllRead:

    async def test_mark_all_read(
        self, client: AsyncClient, registered_user, auth_headers
    ):
        """Mark all read updates all unread notifications."""
        # create 3 notifications
        for i in range(3):
            await client.post('/notifications/', json={
                'user_id': registered_user['id'],
                'title': f'Notification {i}',
                'message': 'Test.',
            })

        response = await client.patch(
            '/notifications/read-all',
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()['updated'] == 3

        # verify all are now read
        count_response = await client.get(
            '/notifications/unread-count', headers=auth_headers
        )
        assert count_response.json()['count'] == 0


class TestDeleteNotification:

    async def test_delete_notification(
        self, client: AsyncClient, auth_headers, sample_notification
    ):
        """Deleting a notification removes it."""
        notification_id = sample_notification['id']

        response = await client.delete(
            f'/notifications/{notification_id}',
            headers=auth_headers
        )
        assert response.status_code == 204

        # verify it's gone
        get_response = await client.get(
            f'/notifications/{notification_id}',
            headers=auth_headers
        )
        assert get_response.status_code == 404

    async def test_cannot_delete_other_users_notification(
        self, client: AsyncClient, auth_headers
    ):
        """Cannot delete another user's notification."""
        other_notification = await client.post('/notifications/', json={
            'user_id': 999,
            'title': 'Other user',
            'message': 'Not yours.',
        })
        other_id = other_notification.json()['id']

        response = await client.delete(
            f'/notifications/{other_id}',
            headers=auth_headers
        )
        assert response.status_code == 404


class TestWebSocket:

    def test_websocket_rejects_invalid_token(self):
        """WebSocket with invalid token is rejected."""
        client = TestClient(app)
        try:
            with client.websocket_connect(
                '/ws/notifications?token=invalidtoken'
            ) as ws:
                # connection should be closed with code 4001
                ws.receive_json()
            assert False, "Should have been rejected"
        except WebSocketDisconnect as e:
            assert e.code == 4001
                # if server doesn't close immediately check close code
            # no exception means it connected — that's wrong
            # WebSocket should have closed with 4001

    def test_websocket_connects_with_valid_token(self, registered_user):
        pass