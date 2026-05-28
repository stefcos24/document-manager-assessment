import pytest

from tests.conftest import make_file


class TestRegister:
    URL = "/api/auth/register/"

    def test_creates_user_and_returns_token(self, api_client):
        resp = api_client.post(
            self.URL,
            {"email": "test@example.com", "password": "test1234", "name": "New User"},
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "token" in data
        assert data["user"]["email"] == "test@example.com"

    def test_duplicate_email_returns_400(self, api_client):
        payload = {"email": "test_two@example.com", "password": "test1234", "name": "Test User"}
        api_client.post(self.URL, payload, format="json")
        resp = api_client.post(self.URL, payload, format="json")
        assert resp.status_code == 400

    def test_short_password_returns_400(self, api_client):
        resp = api_client.post(
            self.URL,
            {"email": "test@example.com", "password": "abc", "name": "New User"},
            format="json",
        )
        assert resp.status_code == 400

    def test_missing_email_returns_400(self, api_client):
        resp = api_client.post(self.URL, {"password": "test1234"}, format="json")
        assert resp.status_code == 400


class TestLogin:
    REGISTER_URL = "/api/auth/register/"
    URL = "/api/auth/login/"

    @pytest.fixture(autouse=True)
    def registered_user(self, api_client):
        api_client.post(
            self.REGISTER_URL,
            {"email": "test@example.com", "password": "test1234", "name": "Login User"},
            format="json",
        )

    def test_returns_token(self, api_client):
        resp = api_client.post(
            self.URL,
            {"email": "test@example.com", "password": "test1234"},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["email"] == "test@example.com"

    def test_wrong_password_returns_400(self, api_client):
        resp = api_client.post(
            self.URL,
            {"email": "login@example.com", "password": "testtest1234"},
            format="json",
        )
        assert resp.status_code == 400

    def test_unknown_email_returns_400(self, api_client):
        resp = api_client.post(
            self.URL,
            {"email": "nobody@example.com", "password": "test1234"},
            format="json",
        )
        assert resp.status_code == 400

    def test_missing_fields_returns_400(self, api_client):
        resp = api_client.post(self.URL, {}, format="json")
        assert resp.status_code == 400
