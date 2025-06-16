from django.db import models

# Create your models here.
class ImageModel(models.Model):
    image = models.ImageField(upload_to='uploads/')
    hash = models.CharField(max_length=100)
    color_histogram = models.JSONField()
    object_list = models.JSONField()