from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField, UUIDField


class User(AbstractUser):
    """
    Model representing users.
    """


class Project(models.Model):
    id = UUIDField(primary_key=True, default=uuid4, editable=False)
    name = CharField(max_length=150)
