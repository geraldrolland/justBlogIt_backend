from django.contrib import admin
from .models import *
admin.site.register(CustomUser)
admin.site.register(Notification)
admin.site.register(Post)
admin.site.register(Comment)