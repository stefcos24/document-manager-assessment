import hashlib

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from propylon_document_manager.file_versions.models import FileVersion
from tests.conftest import make_file
from tests.factories import UserFactory


class TestBasicModel:
    def test_create_file_version(self, user):
        fv = FileVersion.objects.create(
            file_name="report.pdf",
            version_number=1,
            owner=user,
            file_url="documents/reports/report.pdf",
        )
        assert FileVersion.objects.filter(pk=fv.pk).count() == 1
        assert fv.file_name == "report.pdf"
        assert fv.version_number == 1


class TestUpload:
    URL = "/api/file_versions/upload/"

    def test_creates_file_version(self, auth_client):
        resp = auth_client.post(
            self.URL,
            {"file": make_file(b"data", "cv.pdf"), "file_url": "documents/cv.pdf"},
            format="multipart",
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["version_number"] == 0
        assert body["file_url"] == "documents/cv.pdf"
        assert body["file_name"] == "cv.pdf"

    def test_second_upload_same_url_increments_version(self, auth_client):
        auth_client.post(
            self.URL,
            {"file": make_file(b"v0", "doc.txt"), "file_url": "documents/doc.txt"},
            format="multipart",
        )
        resp = auth_client.post(
            self.URL,
            {"file": make_file(b"v1", "doc.txt"), "file_url": "documents/doc.txt"},
            format="multipart",
        )
        assert resp.status_code == 201
        assert resp.json()["version_number"] == 1

    def test_different_urls_are_independent(self, auth_client):
        auth_client.post(
            self.URL,
            {"file": make_file(b"a", "a.txt"), "file_url": "documents/a.txt"},
            format="multipart",
        )
        resp = auth_client.post(
            self.URL,
            {"file": make_file(b"b", "b.txt"), "file_url": "documents/b.txt"},
            format="multipart",
        )
        assert resp.status_code == 201
        assert resp.json()["version_number"] == 0

    def test_hash_is_computed_correctly(self, auth_client):
        content = b"important content"
        resp = auth_client.post(
            self.URL,
            {"file": make_file(content, "h.txt"), "file_url": "documents/h.txt"},
            format="multipart",
        )
        assert resp.status_code == 201
        assert resp.json()["file_hash"] == hashlib.sha256(content).hexdigest()

    def test_file_size_is_stored(self, auth_client):
        content = b"12345"
        resp = auth_client.post(
            self.URL,
            {"file": make_file(content, "size.txt"), "file_url": "documents/size.txt"},
            format="multipart",
        )
        assert resp.status_code == 201
        assert resp.json()["file_size"] == len(content)

    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.post(
            self.URL,
            {"file": make_file(), "file_url": "documents/test.txt"},
            format="multipart",
        )
        assert resp.status_code == 401

    def test_missing_file_returns_400(self, auth_client):
        resp = auth_client.post(self.URL, {"file_url": "documents/x.txt"}, format="multipart")
        assert resp.status_code == 400

    def test_missing_file_url_returns_400(self, auth_client):
        resp = auth_client.post(self.URL, {"file": make_file()}, format="multipart")
        assert resp.status_code == 400


class TestFileVersionList:
    URL = "/api/file_versions/"
    UPLOAD_URL = "/api/file_versions/upload/"

    def test_returns_own_files_only(self, auth_client):
        other_user = UserFactory()
        other_token, _ = Token.objects.get_or_create(user=other_user)
        other_client = APIClient()
        other_client.credentials(HTTP_AUTHORIZATION=f"Token {other_token.key}")

        auth_client.post(
            self.UPLOAD_URL,
            {"file": make_file(b"mine", "mine.txt"), "file_url": "documents/mine.txt"},
            format="multipart",
        )
        other_client.post(
            self.UPLOAD_URL,
            {"file": make_file(b"theirs", "theirs.txt"), "file_url": "documents/theirs.txt"},
            format="multipart",
        )

        resp = auth_client.get(self.URL)
        assert resp.status_code == 200
        urls = [v["file_url"] for v in resp.json()]
        assert "documents/mine.txt" in urls
        assert "documents/theirs.txt" not in urls

    def test_returns_all_versions_of_same_file(self, auth_client):
        auth_client.post(
            self.UPLOAD_URL,
            {"file": make_file(b"v0", "rep.txt"), "file_url": "documents/rep.txt"},
            format="multipart",
        )
        auth_client.post(
            self.UPLOAD_URL,
            {"file": make_file(b"v1", "rep.txt"), "file_url": "documents/rep.txt"},
            format="multipart",
        )

        resp = auth_client.get(self.URL)
        assert resp.status_code == 200
        versions = [v["version_number"] for v in resp.json() if v["file_url"] == "documents/rep.txt"]
        assert sorted(versions) == [0, 1]

    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(self.URL)
        assert resp.status_code == 401
