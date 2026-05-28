import hashlib

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from tests.conftest import make_file
from tests.factories import UserFactory


class TestDocumentRetrieve:
    UPLOAD_URL = "/api/file_versions/upload/"

    def test_returns_latest_version_by_default(self, auth_client):
        auth_client.post(
            self.UPLOAD_URL,
            {"file": make_file(b"v0", "review.pdf"), "file_url": "reviews/review.pdf"},
            format="multipart",
        )
        auth_client.post(
            self.UPLOAD_URL,
            {"file": make_file(b"v1", "review.pdf"), "file_url": "reviews/review.pdf"},
            format="multipart",
        )

        resp = auth_client.get("/api/documents/reviews/review.pdf")
        assert resp.status_code == 200
        assert resp["X-File-Version"] == "1"
        assert b"v1" in b"".join(resp.streaming_content)

    def test_returns_specific_revision(self, auth_client):
        auth_client.post(
            self.UPLOAD_URL,
            {"file": make_file(b"original", "review.pdf"), "file_url": "reviews/review.pdf"},
            format="multipart",
        )
        auth_client.post(
            self.UPLOAD_URL,
            {"file": make_file(b"updated", "review.pdf"), "file_url": "reviews/review.pdf"},
            format="multipart",
        )

        resp = auth_client.get("/api/documents/reviews/review.pdf?revision=0")
        assert resp.status_code == 200
        assert resp["X-File-Version"] == "0"
        assert b"original" in b"".join(resp.streaming_content)

    def test_hash_header_is_returned(self, auth_client):
        content = b"check hash"
        auth_client.post(
            self.UPLOAD_URL,
            {"file": make_file(content, "hash.txt"), "file_url": "docs/hash.txt"},
            format="multipart",
        )

        resp = auth_client.get("/api/documents/docs/hash.txt")
        assert resp.status_code == 200
        assert resp["X-File-Hash"] == hashlib.sha256(content).hexdigest()

    def test_nonexistent_file_returns_404(self, auth_client):
        resp = auth_client.get("/api/documents/does/not/exist.txt")
        assert resp.status_code == 404

    def test_invalid_revision_returns_400(self, auth_client):
        auth_client.post(
            self.UPLOAD_URL,
            {"file": make_file(b"x", "x.txt"), "file_url": "docs/x.txt"},
            format="multipart",
        )
        resp = auth_client.get("/api/documents/docs/x.txt?revision=abc")
        assert resp.status_code == 400

    def test_revision_not_found_returns_404(self, auth_client):
        auth_client.post(
            self.UPLOAD_URL,
            {"file": make_file(b"x", "x.txt"), "file_url": "docs/x.txt"},
            format="multipart",
        )
        resp = auth_client.get("/api/documents/docs/x.txt?revision=99")
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get("/api/documents/reviews/review.pdf")
        assert resp.status_code == 401

    def test_cannot_access_other_users_file(self, auth_client):
        other_user = UserFactory()
        other_token, _ = Token.objects.get_or_create(user=other_user)
        other_client = APIClient()
        other_client.credentials(HTTP_AUTHORIZATION=f"Token {other_token.key}")

        other_client.post(
            self.UPLOAD_URL,
            {"file": make_file(b"secret", "secret.pdf"), "file_url": "private/secret.pdf"},
            format="multipart",
        )

        resp = auth_client.get("/api/documents/private/secret.pdf")
        assert resp.status_code == 404
