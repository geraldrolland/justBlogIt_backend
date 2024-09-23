from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timezone, datetime
from .customusermanager import CustomUserManager
import uuid


class NotificationTypeCategory(models.TextChoices):
    """
    Enum-like class for defining the types of notifications.
    Used in the Notification model to categorize notifications.
    """
    FOLLOW = "follow", "Follow",
    UNFOLLOW = "unfollow", "Unfollow"
    COMMENT = "Comment", "comment"
    REPLY = "Reply", "reply"
    NONE = "None", "none"
    LIKE ="Like", "like"
    UNLIKE = "unlike", "Unlike"


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that extends AbstractBaseUser and PermissionsMixin.
    This model represents the user in the system with extended fields for 
    social media-like functionality (followers, following, profile, etc.).
    """
    username = models.CharField(max_length=64, null=False, default="")
    email = models.EmailField(_("email address"), unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    bio = models.TextField(null=False)
    follower_count = models.IntegerField(null=False, default=0)
    following_count = models.IntegerField(null=False, default=0)
    followers = models.ManyToManyField("self", blank=True, symmetrical=False, related_name="follow")
    following = models.ManyToManyField("self",  blank=True, symmetrical=False, related_name="foll")
    first_name = models.CharField(max_length=64, null=False)
    last_name = models.CharField(max_length=64, null=False)
    post_count = models.IntegerField(default=0)
    profile_image = models.TextField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name", "bio"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class Post(models.Model):
    """
    Model representing a post created by a user. Each post includes a title, text content,
    an optional image, and tracks metadata such as the number of likes and comments.
    """
    postId = models.UUIDField(null=False, primary_key=True, editable=False, default=uuid.uuid4)
    createdAt = models.DateTimeField(default=datetime.now, editable=False)
    postTitle = models.CharField(null=False, blank=False, max_length=120)
    postText = models.TextField(null=False)
    postImage = models.TextField(blank=True, null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="posts")
    likes = models.IntegerField(default=0)
    commentCount = models.IntegerField(default=0)

    def __str__(self):
        return self.postTitle

class Comment(models.Model):
    commentId = models.UUIDField(null=False, editable=False, primary_key=True, default=uuid.uuid4)
    createdAt = models.DateTimeField(default=datetime.now, editable=False)
    commentText = models.TextField(null=False)
    likes = models.IntegerField(default=0)
    replyCount = models.IntegerField(default=0)
    replies = models.ManyToManyField("self",  blank=True, symmetrical=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, related_name="comments")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="comments")

    def __str__(self) -> str:
        return self.commentText
 
class Notification(models.Model):
    notificationId = models.UUIDField(null=False, editable=False, primary_key=True, default=uuid.uuid4)
    notificationType = models.CharField(max_length=32,  choices=NotificationTypeCategory.choices, default=NotificationTypeCategory.NONE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    receipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="receipient")
    postText = models.TextField(blank=True, null=True)
    commentText = models.TextField(blank=True, null=True)
    postImage = models.TextField(blank=True, null=True)
    postTitle = models.CharField(max_length=120, blank=True, null=True)
    createdAt = models.DateTimeField(default=datetime.now)

    def __str__(self) -> str:
        return self.notificationType