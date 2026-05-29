from django.contrib.auth import authenticate, password_validation
from rest_framework import serializers

from ..models import FileVersion, ReadPermission, User


class RegisterSerializer(serializers.ModelSerializer):
    """Validates and creates a new user."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ["email", "name", "password"]

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def create(self, validated_data):
        user = User(
            email=validated_data["email"],
            name=validated_data.get("name", ""),
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class EmailAuthTokenSerializer(serializers.Serializer):
    """
    Validates email + password and returns user obj in validated data
    """

    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    token = serializers.CharField(read_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if not email or not password:
            raise serializers.ValidationError(
                'Must include "email" and "password".',
                code="authorization",
            )

        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )
        if not user:
            raise serializers.ValidationError(
                "Unable to log in with provided credentials.",
                code="authorization",
            )

        attrs["user"] = user
        return attrs


class FileVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileVersion
        fields = [
            "id",
            "file_name",
            "file_url",
            "version_number",
            "file_hash",
            "file_size",
            "content_type",
            "created_at",
            "read_permission",
        ]
        read_only_fields = fields


class FileVersionUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    file_url = serializers.CharField(max_length=2048)
    read_permission = serializers.ChoiceField(
        choices=ReadPermission.choices,
        default=ReadPermission.PRIVATE,
        required=False,
    )

    def validate_file_url(self, value):
        cleaned = value.strip("/")
        if not cleaned:
            raise serializers.ValidationError("file_url cannot be empty.")
        return cleaned
