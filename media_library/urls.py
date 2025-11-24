# media_library/urls.py
from django.urls import path
from . import views

app_name = 'media_library'

urlpatterns = [
    # Детальная страница медиафайла с проверкой доступа
    path('media/<int:pk>/' ,
         views.media_detail ,
         name='media_detail') ,

    # Скачивание медиафайла
    path('media/<int:pk>/download/' ,
         views.download_media ,
         name='download_media') ,

    # Просмотр медиафайла в браузере
    path('media/<int:pk>/view/' ,
         views.view_media ,
         name='view_media') ,

    # Информация о медиафайле (JSON)
    path('media/<int:pk>/info/' ,
         views.media_info ,
         name='media_info') ,
]