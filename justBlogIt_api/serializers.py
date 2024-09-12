from rest_framework.serializers import ModelSerializer, CharField
from .models import *


class CustomUserSerializer(ModelSerializer):
    password = CharField(write_only=True)
    class Meta:
        model = CustomUser
        fields = "__all__"

    def create(self, validated_data):
        print("error in user")
        password = validated_data.pop("password")
        user = CustomUser.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        print("user error")
        for key, value in validated_data.items():
            if key == "password":
                instance.set_password(value)
                continue
            if value:
                setattr(instance, key, value)
        instance.save()
        return instance
    

class PostSerializer(ModelSerializer):
    class Meta:
        model = Post
        fields = "__all__"

    def create(self, validated_data):
        post = Post.objects.create(**validated_data)
        post.save()
        return post

class CommentSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = ["commentId", "createdAt", "commentText", "likes", "replyCount", "post", "user"]
    
    def create(self, validated_data):
        comment = Comment.objects.create(**validated_data)
        comment.save()
        return comment
    

class NotificationSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = "__all__"
    
    def create(self, validated_data):
        notification = Notification.objects.create(**validated_data)
        notification.save()
        return notification
    