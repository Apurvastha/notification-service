import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import get_db
from app.test_config import (
    create_test_tables,
    drop_test_tables,
    get_test_db,
)


@pytest_asyncio.fixture(scope='session', autouse=True)
async def setup_test_database():
    """
    Create tables once before all tests, drop after all tests.
    scope='session' means this runs once for the entire test session.
    autouse=True means it applies to every test automatically.
    """
    await create_test_tables()
    yield
    await drop_test_tables()


@pytest_asyncio.fixture(autouse=True)
async def clean_database():
    """
    Clean all data between tests — prevents test bleeding.
    Runs before every single test.
    Same as Django's transaction rollback between tests.
    """
    from app.test_config import TestAsyncSessionLocal
    from app.models import Notification, User
    from sqlalchemy import delete

    yield  # test runs here

    # clean up after each test
    async with TestAsyncSessionLocal() as session:
        await session.execute(delete(Notification))
        await session.execute(delete(User))
        await session.commit()


@pytest_asyncio.fixture
async def client():
    """
    Async HTTP test client.
    Overrides the real database with the test database.
    Same concept as Django's APIClient.
    """
    # override get_db dependency with test version
    app.dependency_overrides[get_db] = get_test_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as ac:
        yield ac

    # clean up overrides after test
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def registered_user(client):
    """
    Creates a registered user and returns their credentials.
    Used by tests that need an existing user.
    """
    user_data = {
        'email': 'alice@test.com',
        'username': 'alice',
        'password': 'testpass123',
    }
    response = await client.post('/auth/register', json=user_data)
    assert response.status_code == 201
    return {**user_data, 'id': response.json()['id']}


@pytest_asyncio.fixture
async def auth_headers(client, registered_user):
    """
    Logs in the registered user and returns Authorization headers.
    Used by tests that need authenticated requests.
    """
    response = await client.post(
        '/auth/token',
        data={
            'username': registered_user['username'],
            'password': registered_user['password'],
        },
    )
    assert response.status_code == 200
    token = response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest_asyncio.fixture
async def sample_notification(client, registered_user):
    """
    Creates a notification for the registered user.
    Used by tests that need an existing notification.
    """
    response = await client.post(
        '/notifications/',
        json={
            'user_id': registered_user['id'],
            'title': 'Test notification',
            'message': 'This is a test notification message.',
            'notification_type': 'info',
        },
    )
    assert response.status_code == 201
    return response.json()