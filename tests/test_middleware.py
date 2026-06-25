import pytest
from httpx import AsyncClient


class TestRequestLoggingMiddleware:

    async def test_request_id_in_response_headers(self, client: AsyncClient):
        """Every response includes X-Request-ID header."""
        response = await client.get('/health')

        assert response.status_code == 200
        assert 'x-request-id' in response.headers
        assert len(response.headers['x-request-id']) == 8

    async def test_each_request_has_unique_id(self, client: AsyncClient):
        """Each request gets a unique request ID."""
        response1 = await client.get('/health')
        response2 = await client.get('/health')

        id1 = response1.headers['x-request-id']
        id2 = response2.headers['x-request-id']

        assert id1 != id2


class TestHealthEndpoint:

    async def test_health_returns_ok(self, client: AsyncClient):
        """Health endpoint returns ok status."""
        response = await client.get('/health')

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ok'
        assert 'service' in data