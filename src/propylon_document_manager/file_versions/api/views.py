from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from ..models import FileVersion
from .serializers import (
    EmailAuthTokenSerializer,
    FileVersionSerializer,
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
