import hashlib

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from ..models import FileVersion
from .serializers import (
    EmailAuthTokenSerializer,
    FileVersionSerializer,
    FileVersionUploadSerializer,
    RegisterSerializer,
)


class RegisterView(APIView):
    """
    Returns the new user + an auth token in a single response
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "user": {"id": user.id, "email": user.email, "name": user.name},
                "token": token.key,
            },
            status=status.HTTP_201_CREATED,
        )


class EmailObtainAuthToken(APIView):
    """
    Returns an auth token
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailAuthTokenSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {"token": token.key, "user_id": user.id, "email": user.email}
        )


class FileVersionViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    serializer_class = FileVersionSerializer
    lookup_field = "id"

    def get_queryset(self):
        return FileVersion.objects.filter(owner=self.request.user).order_by(
            "file_url", "version_number"
        )

    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        serializer = FileVersionUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        file_url = serializer.validated_data["file_url"]

        content = uploaded_file.read()
        file_hash = hashlib.sha256(content).hexdigest()
        uploaded_file.seek(0)

        last_version = (
            FileVersion.objects.filter(owner=request.user, file_url=file_url)
            .order_by("-version_number")
            .first()
        )
        version_number = 0 if last_version is None else last_version.version_number + 1

        file_version = FileVersion.objects.create(
            owner=request.user,
            file_name=uploaded_file.name,
            file_url=file_url,
            version_number=version_number,
            file=uploaded_file,
            file_hash=file_hash,
            file_size=uploaded_file.size,
            content_type=uploaded_file.content_type or "application/octet-stream",
        )

        return Response(
            FileVersionSerializer(file_version).data,
            status=status.HTTP_201_CREATED,
        )


class DocumentRetrieveView(APIView):
    def get(self, request, file_url):
        file_url = file_url.strip("/")
        revision = request.query_params.get("revision")

        queryset = FileVersion.objects.filter(owner=request.user, file_url=file_url)

        if not queryset.exists():
            return Response(
                {"detail": f"No file found at '{file_url}'."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if revision is not None:
            try:
                revision_int = int(revision)
            except ValueError:
                return Response(
                    {"detail": "revision must be an integer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            file_version = get_object_or_404(queryset, version_number=revision_int)
        else:
            file_version = queryset.order_by("-version_number").first()

        response = FileResponse(
            file_version.file.open("rb"),
            content_type=file_version.content_type,
        )
        response["Content-Disposition"] = f'attachment; filename="{file_version.file_name}"'
        response["X-File-Hash"] = file_version.file_hash
        response["X-File-Version"] = str(file_version.version_number)
        return response


class CASRetrieveView(APIView):
    """
    Retrieve a file by its SHA-256 content hash (Content Addressable Storage).
    """

    def get(self, request, file_hash):
        if len(file_hash) != 64 or not all(c in "0123456789abcdef" for c in file_hash.lower()):
            return Response(
                {"detail": "Invalid hash format. Expected 64-character hex string (SHA-256)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_version = get_object_or_404(
            FileVersion,
            owner=request.user,
            file_hash=file_hash.lower(),
        )

        response = FileResponse(
            file_version.file.open("rb"),
            content_type=file_version.content_type,
        )
        response["Content-Disposition"] = f'attachment; filename="{file_version.file_name}"'
        response["X-File-Hash"] = file_version.file_hash
        response["X-File-Version"] = str(file_version.version_number)
        response["X-File-Url"] = file_version.file_url
        return response
