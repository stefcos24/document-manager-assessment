import hashlib

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from tests.conftest import make_file
from tests.factories import UserFactory


class TestCASRetrieval:
    UPLOAD_URL = "/api/file_versions/upload/"

    def test_retrieve_by_hash(self, auth_client):
        content = b"cas content"
        expected_hash = hashlib.sha256(content).hexdigest()
        auth_client.post(
            self.UPLOAD_URL,
            {"file": make_file(content, "cas.txt"), "file_url": "documents/cas.txt"},
            format="multipart",
        )
        resp = auth_client.get(f"/api/cas/{expected_hash}/")
        assert resp.status_code == 200
        assert resp["X-File-Hash"] == expected_hash
        assert resp["X-File-Url"] == "documents/cas.txt"

    def test_response_contains_correct_content(self, auth_client):
        content = b"verifiable content"
        file_hash = hashlib.sha256(content).hexdigest()
        auth_client.post(
            self.UPLOAD_URL,
            {"file": make_file(content, "verify.txt"), "file_url": "documents/verify.txt"},
            format="multipart",
        )
        resp = auth_client.get(f"/api/cas/{file_hash}/")
        assert resp.status_code == 200
        assert b"verifiable content" in b"".join(resp.streaming_content)

    def test_invalid_hash_format_returns_400(self, auth_client):
        resp = auth_client.get("/api/cas/not-a-valid-hash/")
        assert resp.status_code == 400

    def test_hash_too_short_returns_400(self, auth_client):
        resp = auth_client.get("/api/cas/abc123/")
        assert resp.status_code == 400

    def test_nonexistent_hash_returns_404(self, auth_client):
        resp = auth_client.get(f"/api/cas/{'a' * 64}/")
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(f"/api/cas/{'a' * 64}/")
        assert resp.status_code == 401

    def test_cannot_access_other_users_file_by_hash(self, auth_client):
        other_user = UserFactory()
        other_token, _ = Token.objects.get_or_create(user=other_user)
        other_client = APIClient()
        other_client.credentials(HTTP_AUTHORIZATION=f"Token {other_token.key}")

        content = b"private content"
        file_hash = hashlib.sha256(content).hexdigest()
        other_client.post(
            self.UPLOAD_URL,
            {"file": make_file(content, "private.txt"), "file_url": "documents/private.txt"},
            format="multipart",
        )

        resp = auth_client.get(f"/api/cas/{file_hash}/")
        assert resp.status_code == 404
