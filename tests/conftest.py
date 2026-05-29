import io

import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from propylon_document_manager.file_versions.models import User

from .factories import UserFactory


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory()


@pytest.fixture
def api_client():
    return APIClient()


def make_auth_client(user):
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.fixture
def auth_client(user):
    return make_auth_client(user)


@pytest.fixture
def other_auth_client(db):
    return make_auth_client(UserFactory())


def make_file(content: bytes = b"hello", name: str = "test.txt") -> io.BytesIO:
    f = io.BytesIO(content)
    f.name = name
    return f
