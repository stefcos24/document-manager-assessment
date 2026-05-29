import hashlib

from tests.conftest import make_file


class TestReadPermissions:
    UPLOAD_URL = "/api/file_versions/upload/"

    def test_default_permission_is_private(self, auth_client):
        resp = auth_client.post(
            self.UPLOAD_URL,
            {"file": make_file(b"data", "doc.txt"), "file_url": "docs/doc.txt"},
            format="multipart",
        )
        assert resp.json()["read_permission"] == "private"

    def test_private_file_not_accessible_by_other_user_via_document(self, auth_client, other_auth_client):
        auth_client.post(
            self.UPLOAD_URL,
            {
                "file": make_file(b"secret", "secret.txt"),
                "file_url": "docs/secret.txt",
                "read_permission": "private",
            },
            format="multipart",
        )
        resp = other_auth_client.get("/api/documents/docs/secret.txt")
        assert resp.status_code == 404

    def test_private_file_not_accessible_by_other_user_via_cas(self, auth_client, other_auth_client):
        content = b"private content"
        file_hash = hashlib.sha256(content).hexdigest()
        auth_client.post(
            self.UPLOAD_URL,
            {
                "file": make_file(content, "priv.txt"),
                "file_url": "docs/priv.txt",
                "read_permission": "private",
            },
            format="multipart",
        )
        resp = other_auth_client.get(f"/api/cas/{file_hash}/")
        assert resp.status_code == 404

    def test_public_file_accessible_by_other_user_via_document(self, auth_client, other_auth_client):
        auth_client.post(
            self.UPLOAD_URL,
            {
                "file": make_file(b"shared", "shared.txt"),
                "file_url": "docs/shared.txt",
                "read_permission": "public",
            },
            format="multipart",
        )
        resp = other_auth_client.get("/api/documents/docs/shared.txt")
        assert resp.status_code == 200
        assert b"shared" in b"".join(resp.streaming_content)

    def test_public_file_accessible_by_other_user_via_cas(self, auth_client, other_auth_client):
        content = b"public content"
        file_hash = hashlib.sha256(content).hexdigest()
        auth_client.post(
            self.UPLOAD_URL,
            {
                "file": make_file(content, "pub.txt"),
                "file_url": "docs/pub.txt",
                "read_permission": "public",
            },
            format="multipart",
        )
        resp = other_auth_client.get(f"/api/cas/{file_hash}/")
        assert resp.status_code == 200

    def test_owner_can_always_read_own_private_file(self, auth_client):
        auth_client.post(
            self.UPLOAD_URL,
            {
                "file": make_file(b"mine", "mine.txt"),
                "file_url": "docs/mine.txt",
                "read_permission": "private",
            },
            format="multipart",
        )
        resp = auth_client.get("/api/documents/docs/mine.txt")
        assert resp.status_code == 200

    def test_other_user_cannot_upload_to_existing_url(self, auth_client, other_auth_client):
        auth_client.post(
            self.UPLOAD_URL,
            {
                "file": make_file(b"v0", "doc.txt"),
                "file_url": "docs/doc.txt",
                "read_permission": "public",
            },
            format="multipart",
        )
        resp = other_auth_client.post(
            self.UPLOAD_URL,
            {"file": make_file(b"hijack", "doc.txt"), "file_url": "docs/doc.txt"},
            format="multipart",
        )
        assert resp.status_code == 201
        assert resp.json()["version_number"] == 0
