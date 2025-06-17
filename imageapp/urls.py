from django.urls import path
from .views import upload_image
from django.conf import settings
from django.conf.urls.static import static 
import os

urlpatterns = [
    path('', upload_image, name='upload_image'),
]
if settings.DEBUG or 'RENDER' in os.environ:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)