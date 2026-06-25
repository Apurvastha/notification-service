import pytest
from httpx import AsyncClient


class TestRegistration:

    async def test_register_success(self, client: AsyncClient):
        """Valid registration creates a user and returns user data."""
        response = await client.post('/auth/register', json={
            'email': 'bob@test.com',
            'username': 'bob',
            'password': 'testpass123',
        })

        assert response.status_code == 201
        data = response.json()
        assert data['email'] == 'bob@test.com'
        assert data['username'] == 'bob'
        assert data['is_active'] is True
        assert 'id' in data
        assert 'created_at' in data
        assert 'password' not in data         # ← never expose password
        assert 'hashed_password' not in data  # ← never expose hash

    async def test_register_duplicate_email(self, client: AsyncClient, registered_user):
        """Cannot register with an email that already exists."""
        response = await client.post('/auth/register', json={
            'email': registered_user['email'],  # same email
            'username': 'different_username',
            'password': 'testpass123',
        })

        assert response.status_code == 400
        assert 'Email already registered' in response.json()['detail']

    async def test_register_duplicate_username(self, client: AsyncClient, registered_user):
        """Cannot register with a username that already exists."""
        response = await client.post('/auth/register', json={
            'email': 'different@test.com',
            'username': registered_user['username'],  # same username
            'password': 'testpass123',
        })

        assert response.status_code == 400
        assert 'Username already taken' in response.json()['detail']

    async def test_register_invalid_email(self, client: AsyncClient):
        """Invalid email format rejected by Pydantic."""
        response = await client.post('/auth/register', json={
            'email': 'notanemail',
            'username': 'testuser',
            'password': 'testpass123',
        })

        assert response.status_code == 422  # Unprocessable Entity

    async def test_register_short_password(self, client: AsyncClient):
        """Password shorter than 8 characters rejected."""
        response = await client.post('/auth/register', json={
            'email': 'test@test.com',
            'username': 'testuser',
            'password': 'short',  # less than 8 chars
        })

        assert response.status_code == 422

    async def test_register_short_username(self, client: AsyncClient):
        """Username shorter than 3 characters rejected."""
        response = await client.post('/auth/register', json={
            'email': 'test@test.com',
            'username': 'ab',  # less than 3 chars
            'password': 'testpass123',
        })

        assert response.status_code == 422


class TestLogin:

    async def test_login_success(self, client: AsyncClient, registered_user):
        """Valid credentials return JWT access token."""
        response = await client.post('/auth/token', data={
            'username': registered_user['username'],
            'password': registered_user['password'],
        })

        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert data['token_type'] == 'bearer'
        assert len(data['access_token']) > 0

    async def test_login_wrong_password(self, client: AsyncClient, registered_user):
        """Wrong password returns 401."""
        response = await client.post('/auth/token', data={
            'username': registered_user['username'],
            'password': 'wrongpassword',
        })

        assert response.status_code == 401
        assert 'Incorrect username or password' in response.json()['detail']

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Non-existent username returns 401."""
        response = await client.post('/auth/token', data={
            'username': 'doesnotexist',
            'password': 'testpass123',
        })

        assert response.status_code == 401

    async def test_login_returns_same_error_for_wrong_user_and_wrong_password(
        self, client: AsyncClient, registered_user
    ):
        """
        Wrong password and wrong username return identical error.
        Prevents username enumeration attacks.
        """
        wrong_user_response = await client.post('/auth/token', data={
            'username': 'doesnotexist',
            'password': 'testpass123',
        })

        wrong_pass_response = await client.post('/auth/token', data={
            'username': registered_user['username'],
            'password': 'wrongpassword',
        })

        # same status code
        assert wrong_user_response.status_code == wrong_pass_response.status_code
        # same error message
        assert wrong_user_response.json()['detail'] == wrong_pass_response.json()['detail']


class TestMe:

    async def test_me_returns_current_user(self, client: AsyncClient, registered_user, auth_headers):
        """Authenticated /auth/me returns current user data."""
        response = await client.get('/auth/me', headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data['username'] == registered_user['username']
        assert data['email'] == registered_user['email']

    async def test_me_requires_auth(self, client: AsyncClient):
        """Unauthenticated /auth/me returns 401."""
        response = await client.get('/auth/me')
        assert response.status_code == 401

    async def test_me_rejects_invalid_token(self, client: AsyncClient):
        """Invalid token returns 401."""
        response = await client.get(
            '/auth/me',
            headers={'Authorization': 'Bearer invalidtoken'}
        )
        assert response.status_code == 401