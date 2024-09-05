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
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from .serializers import *
from .custompermission import *
import random
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMessage
from django.http import JsonResponse
import requests
import base64
import uuid
import json