from django.contrib import admin
from .models import  ImageModel


admin.site.register(ImageModel)

# class ImageModelAdmin(admin.ModelAdmin):
#     list_display = ('image', 'phash')
#     search_fields = ('phash',)
#     list_filter = ('created_at',)
#     readonly_fields = ('phash', 'created_at', 'updated_at')
#     fieldsets = (
#         (None, {
#             'fields': ('image',)
#         }),
#         ('Advanced', {
#             'classes': ('collapse',),
#             'fields': ('phash', 'created_at', 'updated_at')
#         }),
#     )
#     prepopulated_fields = {'slug': ('title',)}


