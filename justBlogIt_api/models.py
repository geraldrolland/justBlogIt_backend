from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .customusermanager import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=64, null=False, default="")
    email = models.EmailField(_("email address"), unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    bio = models.TextField(null=False)
    follower_count = models.IntegerField(null=False, default=0)
    following_count = models.IntegerField(null=False, default=0)
    followers = models.ManyToManyField("self", null=True, blank=True)
    following = models.ManyToManyField("self", null=True, blank=True)
    first_name = models.CharField(max_length=64, null=False)
    last_name = models.CharField(max_length=64, null=False)
    profile_image = models.ImageField(upload_to="images/", null=False, blank=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name", "bio", "profile_image"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email