# Generated by Django 5.2.3 on 2025-06-13 06:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('imageapp', '0002_imageupload_delete_imagemodel'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ImageUpload',
            new_name='ImageModel',
        ),
    ]
