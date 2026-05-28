import os

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, EmailField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Default custom user model for Propylon Document Manager.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})


def file_upload_path(instance, filename):
    """Organise uploads by user ID to avoid collisions between users."""
    return os.path.join("uploads", str(instance.owner_id), filename)


class FileVersion(models.Model):
    file_name = models.fields.CharField(max_length=512)
    version_number = models.fields.IntegerField()
    owner = models.ForeignKey(
        "file_versions.User",
        on_delete=models.CASCADE,
        related_name="file_versions",
    )
    file_url = models.CharField(
        max_length=2048,
        db_index=True,
    )
    file = models.FileField(
        upload_to=file_upload_path,
        null=True,
        blank=True,
    )
    file_hash = models.CharField(
        max_length=64,
        db_index=True,
        null=True,
        blank=True,
    )
    file_size = models.BigIntegerField(default=0)
    content_type = models.CharField(
        max_length=255,
        blank=True,
        default="application/octet-stream",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("owner", "file_url", "version_number")]
        ordering = ["file_url", "version_number"]

    def __str__(self):
        return f"{self.file_url} v{self.version_number} ({self.owner.email})"
