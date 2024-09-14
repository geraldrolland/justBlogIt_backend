from django.shortcuts import redirect, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_ratelimit.decorators import ratelimit
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.cache  import cache_page, never_cache, cache_control
from django.core.cache import cache
from django.views.decorators.vary import vary_on_cookie
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes, authentication_classes, parser_classes
from .serializers import *
from .custompermission import *
import random
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMessage
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
import requests
import base64
import uuid
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import datetime
channel_layer = get_channel_layer()
from .formatdate import FormatDate

class UserViewSet(viewsets.ViewSet):
    @action(detail=False, permission_classes=[AllowAny], methods=["post"])
    def create_user(self, request):
        print(request.data)
        serializer = CustomUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login_user(self, request):
        user = get_object_or_404(CustomUser, email=request.data.get("email"))
        print("error")
        print(request.data.get("password"))
        print(request.data.get("email"))
        print(user.check_password(request.data.get("password")))
        if user.check_password(request.data.get("password")):
            refresh = RefreshToken.for_user(user=user)
            print(user.email)
            return Response({
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "profile_image": user.profile_image,
                "bio": user.bio,
                "email": user.email,
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }, status=status.HTTP_200_OK)
        return Response({"detail": "incorrect password"}, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated], authentication_classes=[JWTAuthentication, BasicAuthentication, SessionAuthentication])
    def get_userprofile(self, request, format=None):
        user = get_object_or_404(CustomUser, email=request.user.email)
        return Response({
            "id": user.id,
            "username": user.username,
            "last_name": user.last_name,
            "first_name": user.first_name,
            "follower_count": user.follower_count,
            "following_count": user.following_count,
            "profile_image": user.profile_image,
            "post_count": user.posts.count(),
            "bio": user.bio,
            "email": user.email,
            
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, authentication_classes=[JWTAuthentication, BasicAuthentication, SessionAuthentication], permission_classes=[IsAuthenticated], methods=["get"])
    def get_userposts(self, request, format=None):
        user = get_object_or_404(CustomUser, email=request.user.email)
        posts = user.posts.order_by("-createdAt")
        if posts:
            userposts_list = []
            for post in posts:
                print("this is the username", user.username)
                date = FormatDate.format_date(post.createdAt)
                userpost_obj = {
                    "postId": post.postId,
                    "createdAt": date,
                    "postTitle": post.postTitle,
                    "postText": post.postText,
                    "postImage": post.postImage,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "image": user.profile_image,
                    },
                    "likes": post.likes,
                    "commentCount": post.commentCount,
                }
                userposts_list.append(userpost_obj)
            return Response(userposts_list, status=status.HTTP_200_OK)
        return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, authentication_classes=[JWTAuthentication, SessionAuthentication, BasicAuthentication], permission_classes=[IsAuthenticated], methods=["get"])
    def follow_user(self, request, pk=None, format=None):

        post = get_object_or_404(Post, postId=pk)
        user = get_object_or_404(CustomUser, email=request.user.email)
        other_user = post.user
        if user in other_user.followers.all():
            return Response({"error": "bad request"}, status=status.HTTP_400_BAD_REQUEST)
        other_user.followers.add(user)
        user.following_count += 1
        other_user.follower_count += 1
        user.save()
        other_user.save()
        notification = {
            "notificationType": "Follow",
            "user": user,
            "receipient": other_user,
        }
        notification = Notification.objects.create(**notification)
        notification.save()
        async_to_sync(channel_layer.group_send)("broadcastNotification", {
            "type": "handle.notification",
            "message": {
                "notificationId": str(notification.notificationId),
                "notificationType": "Follow",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "image": user.profile_image if user.profile_image else None
                },
                "commentText": None,
                "postText": None,
                "postImage": None,
                "createdAt": str(notification.createdAt),
                "receipient": other_user.id
            }
        })

        return Response({"detail": "following succesfully"}, status=status.HTTP_200_OK)
    
    @action(detail=True, authentication_classes=[JWTAuthentication, SessionAuthentication, BasicAuthentication], permission_classes=[IsAuthenticated], methods=["get"])
    def unfollow_user(self, request, pk=None, format=None):
        user = get_object_or_404(CustomUser, email=request.user.email)
        post = get_object_or_404(Post, postId=pk)
        other_user = post.user
        if user not in other_user.followers.all():
            return Response({"error": "bad request"}, status=status.HTTP_400_BAD_REQUEST)
        other_user.followers.remove(user)
        other_user.follower_count -= 1
        user.following_count -= 1
        user.following.remove(other_user)
        other_user.save()
        user.save()
        notification = {
            "notificationType": "Unfollow",
            "user": user,
            "receipient": other_user,
        }
        notification = Notification.objects.create(**notification)
        notification.save()
        async_to_sync(channel_layer.group_send)("broadcastNotification", {
            "type": "handle.notification",
            "message": {
                "notificationId": str(notification.notificationId),
                "notificationType": notification.notificationType,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "image": user.profile_image if user.profile_image else None
                },
                "commentText": None,
                "postText": None,
                "postImage": None,
                "postTitle": None,
                "createdAt": str(notification.createdAt),
                "receipient": other_user.id
            }
        })

        return Response({"detail": "following succesfully"}, status=status.HTTP_200_OK)

    @action(detail=False, authentication_classes=[JWTAuthentication, BasicAuthentication, SessionAuthentication], permission_classes=[IsAuthenticated], methods=["get"])
    def get_notifications(self, request, format=None):
        user = get_object_or_404(CustomUser, email=request.user.email)
        notifications = user.receipient.order_by("-createdAt")
        if notifications != []:
            print(notifications)
            notifications_list = []
            for notify in notifications:
                if notify.user.id == user.id:
                    continue
                date = FormatDate.format_date(notify.createdAt)
                not_obj = {
                    "notificationId": str(notify.notificationId),
                    "notificationType": notify.notificationType,
                    "postText": notify.postText if notify.postText else None ,
                    "commentText": notify.commentText if notify.commentText else None,
                    "postImage": notify.postImage if notify.postImage else None,
                    "postTitle": notify.postTitle if notify.postTitle else None,
                    "createdAt": date,
                    "user": {
                        "id": notify.user.id,
                        "image": notify.user.profile_image if notify.user.profile_image else None,
                        "username": notify.user.username,
                    },
                    "receipient": user.id
                }
                notifications_list.append(not_obj)
            if notifications_list == []:
                return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response(notifications_list, status=status.HTTP_200_OK)
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
    



    
    @action(detail=False, permission_classes=[IsAuthenticated], authentication_classes=[SessionAuthentication, BasicAuthentication, JWTAuthentication], methods=["post"])
    def update_userprofile(self, request):
        user =  get_object_or_404(CustomUser, email=request.user.email)
        for key , value in request.data.items():
            if key == "password":
                user.set_password(value)
                continue
            if value:
                setattr(user, key, value)
        user.save()
        return Response({"detail": "profile updated succesfully"}, status=status.HTTP_200_OK)


class PostViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"], authentication_classes=[JWTAuthentication, SessionAuthentication, BasicAuthentication], permission_classes=[IsAuthenticated])
    def create_post(self, request):
        user = get_object_or_404(CustomUser, email=request.user.email)
        post = {
            "postTitle": request.data.get("postTitle"),
            "postText": request.data.get("postText"),
            "postImage": request.data.get("postImage") if request.data.get('postImage') else None,
            "user": user.id
        }

        serializer = PostSerializer(data=post)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        async_to_sync(channel_layer.group_send)("broadcastPost", {
            "type": "handle.post",
            "message": {
                "postId": serializer.data.get("postId"),
                "createdAt": serializer.data.get("createdAt"),
                "postTitle": serializer.data.get("postTitle"),
                "postText": serializer.data.get("postText"),
                "postImage": serializer.data.get("postImage"),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "image": user.profile_image,
                    "bio": user.bio
                },
                "likes": serializer.data.get("likes"),
                "commentCount": serializer.data.get("commentCount"),
                "isFollowing": False,
                "createdAt": serializer.data.get("createdAt"),
            }
        })
        return Response({"detail": "post created successfully"}, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=["delete"], authentication_classes=[SessionAuthentication, BasicAuthentication, JWTAuthentication], permission_classes=[IsAuthenticated])
    def delete_post(self, request, pk=None):
        post = get_object_or_404(Post, postId=pk)
        post.delete()
        return Response({"detail": "post deleted succesfully"}, status=status.HTTP_200_OK)

    @action(detail=False, permission_classes=[IsAuthenticated], authentication_classes=[JWTAuthentication, BasicAuthentication, SessionAuthentication], methods=["get"])
    def get_posts(self, request):
        user = get_object_or_404(CustomUser, email=request.user.email)
        posts = Post.objects.order_by("-createdAt")
        if posts:
            posts_list = []
            for post in posts:
                isFollowing = False
                if user in post.user.followers.all():
                    isFollowing = True
                    print(post.postTitle)
                    print(post.user.username)
                if user.id == post.user.id:
                    isFollowing = None

                date = FormatDate.format_date(post.createdAt)
                post_obj = {
                    "postId": post.postId,
                    "createdAt": post.createdAt.isoformat(),
                    "postTitle": post.postTitle,
                    "postText": post.postText,
                    "postImage": post.postImage,
                    "createdAt": date,
                    "user": {
                        "id": post.user.id,
                        "username": post.user.username,
                        "image": post.user.profile_image,
                        "bio": post.user.bio
                    },
                    "likes": post.likes,
                    "commentCount": post.commentCount,
                    "isFollowing": isFollowing
                }
                posts_list.append(post_obj)
            return Response(posts_list, status=status.HTTP_200_OK)
        print("it is empty")
        return Response({"error": "not Found"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, permission_classes=[IsAuthenticated], authentication_classes=[JWTAuthentication, BasicAuthentication,  SessionAuthentication], methods=["get"])
    def get_comments(self, request, pk=None):
        post =  get_object_or_404(Post, postId=pk)
        comments = post.comments.order_by("-createdAt")
        if comments:
            comment_list = []
            for comment in comments:
                date = FormatDate.format_date(comment.createdAt)
                comment_obj = {
                    "commentId": str(comment.commentId),
                    "createdAt": date,
                    "commentText": comment.commentText,
                    "likes": comment.likes,
                    "replyCount": comment.replyCount,
                    "user": {
                        "id": comment.user.id,
                        "username": comment.user.username,
                        "bio": comment.user.bio,
                        "image": comment.user.profile_image,
                    }
                }
                comment_list.append(comment_obj)
            return Response(comment_list, status=status.HTTP_200_OK)
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)


    @action(detail=True, permission_classes=[IsAuthenticated], authentication_classes=[JWTAuthentication, SessionAuthentication, BasicAuthentication], methods=["get"])
    def like_post(self,  request, pk=None):
        user = get_object_or_404(CustomUser, email=request.user.email)
        post = get_object_or_404(Post, postId=pk)
        post.likes += 1
        post.save()
        other_user = post.user
        other_user = get_object_or_404(CustomUser, id=other_user.id)
        notification = {
            "notificationType": "Like",
            "user": user,
            "receipient": other_user,
            "postImage": post.postImage if post.postImage else None,
            "postText": post.postText if post.postText else None,
            "postTitle": post.postTitle if post.postTitle else None
        }

        notification = Notification.objects.create(**notification)
        notification.save()
        async_to_sync(channel_layer.group_send)("broadcastNotification", {
            "type": "handle.notification",
            "message": {
                "notificationId": str(notification.notificationId),
                "notificationType": notification.notificationType,
                "createdAt": str(notification.createdAt),
                    "user": {
                    "id": user.id,
                    "username": user.username,
                    "image": user.profile_image if user.profile_image else None
                },
                "postImage": post.postImage if post.postImage else None,
                "postText": post.postText if post.postText else None,
                "postTitle": post.postTitle if post.postTitle else None,
                "commentText": None,
                "receipient": str(other_user.id)
            }
        })
        return Response({"detail": "liked post successfully"}, status=status.HTTP_200_OK)
    

    @action(detail=True, permission_classes=[IsAuthenticated], authentication_classes=[JWTAuthentication, SessionAuthentication, BasicAuthentication], methods=["get"])
    def unlike_post(self,  request, pk=None):
        user = get_object_or_404(CustomUser, email=request.user.email)
        post = get_object_or_404(Post, postId=pk)
        post.likes -= 1
        post.save()
        other_user = post.user
        other_user = get_object_or_404(CustomUser, id=other_user.id)
        notification = {
            "notificationType": "Unlike",
            "user": user,
            "receipient": other_user,
            "postImage": post.postImage if post.postImage else None,
            "postText": post.postText if post.postText else None,
            "postTitle": post.postTitle if post.postTitle else None,
        }
        notification = Notification.objects.create(**notification)
        notification.save()
        async_to_sync(channel_layer.group_send)("broadcastNotification", {
            "type": "handle.notification",
            "message": {
                "notificationId": str(notification.notificationId),
                "notificationType": notification.notificationType,
                "createdAt": str(notification.createdAt),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "image": user.profile_image if user.profile_image else None
                },
                "postImage": post.postImage if post.postImage else None,
                "postText": post.postText if post.postText else None,
                "postTitle": post.postTitle if post.postTitle else None,
                "commenText": None,
                "receipient": other_user.id
            }

        })

        return Response({"detail": "liked post successfully"}, status=status.HTTP_200_OK)
    
    @action(detail=True, authentication_classes=[SessionAuthentication, BasicAuthentication, JWTAuthentication], permission_classes=[IsAuthenticated], methods=["post"])
    def post_comment(self, request, pk=None):
        post = get_object_or_404(Post, postId=pk)
        user = get_object_or_404(CustomUser, email=request.user.email)
        post.commentCount += 1
        comment = {
            "commentText": request.data.get("commentText"),
            "user": user.id,
            "post": post.postId
        }
        s = CommentSerializer(data=comment)
        s.is_valid(raise_exception=True)
        s.save()
        post.save()
        other_user = post.user
        other_user = get_object_or_404(CustomUser, id=other_user.id)

        notification = {
            "notificationType": "Comment",
            "user": user,
            "receipient": other_user,
            "commentText": comment["commentText"],
            "postImage": post.postImage if post.postImage else None,
            "postText": post.postText,
            "postTitle": post.postTitle,
        }
        notification = Notification.objects.create(**notification)
        notification.save()
        async_to_sync(channel_layer.group_send)("broadcastNotification", {
            "type": "handle.notification",
            "message": {
                "notificationId": str(notification.notificationId),
                "notificationType": "Comment",
                "postText": post.postText,
                "postImage": post.postImage if post.postImage else None,
                "postTitle": post.postTitle if post.postTitle else None,
                "commentText": comment['commentText'],
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "image": user.profile_image if user.profile_image else None
                },
                "receipient": other_user.id,
                "createdAt": str(notification.createdAt),
            }
        })

        comment = get_object_or_404(Comment, commentId=s.data["commentId"])
        date = FormatDate.format_date(comment.createdAt)
        comment = {
            "commentId": str(comment.commentId),
            "createdAt": date,
            "commentText": comment.commentText,
            "likes": comment.likes,
            "replyCount": comment.replyCount,
            "postId": str(post.postId),
            "user": {
                "id": user.id,
                "username": user.username,
                "image": user.profile_image,
            }
        }

        async_to_sync(channel_layer.group_send)("broadcastPostComment", {
            "type": "handle.postcomment",
            "message": comment,
        })
        return Response(comment, status=status.HTTP_200_OK)


        

class CommentViewSet(viewsets.ViewSet):
    @action(detail=True, permission_classes=[IsAuthenticated], authentication_classes=[JWTAuthentication, SessionAuthentication, BasicAuthentication])
    def get_replies(self, request, pk=None):
        comment = get_object_or_404(Comment, commentId=pk)
        replies = comment.replies.order_by("-createdAt")
        print("this is empty", replies)
        if replies:
            reply_list =[]
            for reply in replies:
                date = FormatDate.format_date(reply.createdAt)
                reply_obj = {
                    "commentId": str(reply.commentId),
                    "createdAt": date,
                    "commentText": reply.commentText,
                    "likes": reply.likes,
                    "replyCount": reply.replyCount,
                    "user": {
                        "id": reply.user.id,
                        "username": reply.user.username,
                        "image": reply.user.profile_image if reply.user.profile_image else None,
                        "bio": reply.user.bio,
                    }
                }
                reply_list.append(reply_obj)
            return Response(reply_list, status=status.HTTP_200_OK)


    @action(detail=True, permission_classes=[IsAuthenticated], authentication_classes=[JWTAuthentication, SessionAuthentication, BasicAuthentication], methods=["post"])
    def post_reply(self, request, pk=None):
        user = get_object_or_404(CustomUser, email=request.user.email)
        comment = get_object_or_404(Comment, commentId=pk)
        other_user = comment.user
        reply = {
            "commentText": request.data.get("commentText"),
            "user": user,
        }

        reply = Comment.objects.create(**reply)
        comment.replyCount += 1
        comment.replies.add(reply)
        comment.save()
        reply.save()

        notification = {
            "notificationType": "Reply",
            "user": user,
            "receipient": other_user,
            "commentText": comment.commentText
        }

        notification = Notification.objects.create(**notification)
        notification.save()
        async_to_sync(channel_layer.group_send)("broadcastNotification", {
            "type": "handle.notification",
            "message": {
                "notificationId": str(notification.notificationId),
                "notificationType": notification.notificationType,
                "createdAt": str(notification.createdAt),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "image": user.profile_image if user.profile_image else None
                },
                "receipient": other_user.id,
                "commentText": comment.commentText,
                "postText": None,
                "postImage": None,
                "postTitle": None,
            }
        })
        date = FormatDate.format_date(reply.createdAt)
        reply = {
            "commentId": str(reply.commentId),
            "createdAt": date,
            "commentText": reply.commentText,
            "likes": reply.likes,
            "replyCount": reply.replyCount,
            "user": {
                "id": user.id,
                "username": user.username,
                "image": user.profile_image,
                "bio": user.bio,
            }
        }
        return Response(reply, status=status.HTTP_200_OK)
    
    
    @action(detail=True, permission_classes=[IsAuthenticated], authentication_classes=[JWTAuthentication, SessionAuthentication, BasicAuthentication], methods=["get"])
    def like_comment(self, request, pk=None):
        comment = get_object_or_404(Comment, commentId=pk)
        comment.likes += 1
        other_user = comment.user
        user = get_object_or_404(CustomUser, email=request.user.email)
        comment.save()
        notification = {
            "notificationType": "Like",
            "commentText": comment.commentText,
            "user": user,
            "receipient": other_user,
        }
        notification = Notification.objects.create(**notification)
        notification.save()
        return Response({"detail": "liked sucessfully"}, status=status.HTTP_200_OK)
    
    @action(detail=True, permission_classes=[IsAuthenticated], authentication_classes=[JWTAuthentication, SessionAuthentication, BasicAuthentication], methods=["get"])
    def unlike_comment(self, request, pk=None):
        comment = get_object_or_404(Comment, commentId=pk)
        comment.likes -= 1
        other_user = comment.user
        user = get_object_or_404(CustomUser, email=request.user.email)
        comment.save()
        notification = {
            "notificationType": "Unlike",
            "commentText": comment.commentText,
            "user": user,
            "receipient": other_user,
        }
        notification = Notification.objects.create(**notification)
        notification.save()
        return Response({"detail": "liked sucessfully"}, status=status.HTTP_200_OK)