# Generated by Django 5.0.6 on 2024-09-11 15:19

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('justBlogIt_api', '0008_alter_post_createdat'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='createdAt',
            field=models.DateTimeField(default=datetime.datetime.now, editable=False),
        ),
    ]
