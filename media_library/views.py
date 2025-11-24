# media_library/views.py
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse , Http404 , HttpResponseForbidden , JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

from .models import MediaLibraryItem

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def download_media(request , pk) :
    """
    View для скачивания медиафайла с проверкой прав доступа
    """
    try :
        # Получаем объект медиа с проверкой активности
        media_item = get_object_or_404(MediaLibraryItem , pk=pk , is_active=True)

        # Проверяем права доступа
        if not _check_media_access(request.user , media_item) :
            logger.warning(f"Попытка несанкционированного доступа к файлу {pk} пользователем {request.user}")
            return HttpResponseForbidden(_("У вас нет прав для доступа к этому файлу"))

        # Проверяем существование файла в хранилище
        if not media_item.media_file or not media_item.media_file.name :
            logger.error(f"Файл не найден для медиа-элемента {pk}")
            raise Http404(_("Файл не найден"))

        # Логируем скачивание
        logger.info(f"Скачивание файла {media_item.filename} (ID: {pk}) пользователем {request.user}")

        # Создаем HTTP response для скачивания
        response = HttpResponse(
            media_item.media_file ,
            content_type=media_item.mime_type or 'application/octet-stream'
        )

        # Настраиваем заголовки для скачивания
        response['Content-Disposition'] = f'attachment; filename="{media_item.filename}"'
        response['Content-Length'] = media_item.media_file.size
        response['X-Content-Type-Options'] = 'nosniff'

        return response

    except Http404 :
        logger.error(f"Медиа-элемент не найден: {pk}")
        raise
    except PermissionDenied :
        logger.warning(f"Доступ запрещен к медиа-элементу {pk}")
        raise
    except Exception as e :
        logger.error(f"Ошибка при скачивании файла {pk}: {str(e)}" , exc_info=True)
        raise Http404(_("Произошла ошибка при загрузке файла"))


@require_http_methods(["GET"])
@login_required
def download_media_authenticated(request , pk) :
    """
    Версия для скачивания только для авторизованных пользователей
    """
    return download_media(request , pk)


@require_http_methods(["GET"])
def view_media(request , pk) :
    """
    View для просмотра медиафайла в браузере (вместо скачивания)
    """
    try :
        media_item = get_object_or_404(MediaLibraryItem , pk=pk , is_active=True)

        if not _check_media_access(request.user , media_item) :
            return HttpResponseForbidden(_("У вас нет прав для просмотра этого файла"))

        if not media_item.media_file or not media_item.media_file.name :
            raise Http404(_("Файл не найден"))

        # Для безопасных типов файлов показываем в браузере
        if _is_safe_for_browser(media_item) :
            response = HttpResponse(
                media_item.media_file ,
                content_type=media_item.mime_type or 'application/octet-stream'
            )
            response['Content-Disposition'] = f'inline; filename="{media_item.filename}"'
            response['Content-Length'] = media_item.media_file.size
            response['X-Content-Type-Options'] = 'nosniff'

            logger.info(f"Просмотр файла {media_item.filename} (ID: {pk})")
            return response
        else :
            # Для небезопасных типов все равно предлагаем скачать
            return download_media(request , pk)

    except Exception as e :
        logger.error(f"Ошибка при просмотре файла {pk}: {str(e)}")
        raise Http404(_("Произошла ошибка при загрузке файла"))


def _check_media_access(user , media_item) :
    """
    Проверяет права доступа к медиафайлу
    """
    # Публичные файлы доступны всем
    if media_item.is_public :
        return True

    # Непубличные файлы только авторизованным пользователям
    if not user.is_authenticated :
        return False

    # Дополнительные проверки можно добавить здесь:
    # - Проверка принадлежности пользователю
    # - Проверка групп/ролей
    # - Проверка разрешений

    return True

def _is_safe_for_browser(media_item) :
    """
    Проверяет, безопасно ли показывать файл в браузере
    """
    safe_types = {
        'image/jpeg' , 'image/png' , 'image/gif' , 'image/webp' , 'image/svg+xml' ,
        'application/pdf' ,
        'text/plain' , 'text/html' , 'text/css' ,
        'audio/mpeg' , 'audio/wav' , 'audio/ogg' ,
        'video/mp4' , 'video/webm' , 'video/ogg' ,
    }

    unsafe_extensions = {'.exe' , '.bat' , '.cmd' , '.sh' , '.zip' , '.rar' , '.7z'}

    # Проверяем по MIME-типу
    if media_item.mime_type in safe_types :
        return True

    # Дополнительная проверка по расширению
    file_extension = f".{media_item.file_extension}".lower()
    if file_extension in unsafe_extensions :
        return False

    return media_item.is_image() or media_item.is_video() or media_item.is_document()


# Дополнительные utility views
def media_info(request , pk) :
    """
    Возвращает информацию о медиафайле в JSON формате
    """
    try :
        media_item = get_object_or_404(MediaLibraryItem , pk=pk , is_active=True)

        if not _check_media_access(request.user , media_item) :
            return HttpResponseForbidden(_("Доступ запрещен"))

        info = {
            'id' : media_item.pk ,
            'title' : media_item.title ,
            'filename' : media_item.filename ,
            'file_size' : media_item.file_size_display ,
            'mime_type' : media_item.mime_type ,
            'category' : media_item.category.name ,
            'created_at' : media_item.created_at.isoformat() ,
            'download_url' : f"/media/library/{pk}/download/" ,
            'view_url' : f"/media/library/{pk}/view/" ,
        }

        return JsonResponse(info)

    except Exception as e :
        logger.error(f"Ошибка получения информации о файле {pk}: {str(e)}")
        return JsonResponse({'error' : _('Файл не найден')} , status=404)


def media_detail(request , pk) :
    """
    Детальная страница медиафайла с проверкой прав доступа
    """
    try :
        media_item = get_object_or_404(MediaLibraryItem , pk=pk , is_active=True)

        # Проверяем права доступа
        if not _check_media_access(request.user , media_item) :
            return HttpResponseForbidden(_("У вас нет прав для просмотра этого файла"))

        context = {
            'object' : media_item ,
            'media_item' : media_item ,  # Дублируем для совместимости
        }

        return render(request , 'media_library/media_detail.html' , context)

    except Exception as e :
        logger.error(f"Ошибка при загрузке детальной страницы {pk}: {str(e)}")
        raise Http404(_("Медиафайл не найден"))


@staff_member_required
def replace_file_view(request , pk) :
    """
    Отдельная страница для замены файла через форму
    """
    media_item = get_object_or_404(MediaLibraryItem , pk=pk)

    if request.method == 'POST' :
        new_file = request.FILES.get('new_file')

        if not new_file :
            messages.error(request , 'Пожалуйста, выберите файл для замены')
        elif new_file.size > 100 * 1024 * 1024 :  # 100MB
            messages.error(request , 'Размер файла не должен превышать 100 МБ')
        else :
            try :
                if media_item.replace_file(new_file , create_preview=True) :
                    messages.success(request , 'Файл успешно заменен')

                    # Обновляем описание если оно стандартное
                    if not media_item.description or media_item.description.startswith("Файл: ") :
                        filename_without_ext = os.path.splitext(new_file.name)[0]
                        separators = ['_' , '-' , '.' , ',' , ';' , '—' , '–']
                        for sep in separators :
                            filename_without_ext = filename_without_ext.replace(sep , ' ')
                        media_item.description = f"Файл: {filename_without_ext.strip()}"
                        media_item.save()

                    return redirect('admin:media_library_medialibraryitem_change' , media_item.pk)
                else :
                    messages.error(request , 'Ошибка при замене файла')
            except Exception as e :
                messages.error(request , f'Ошибка: {str(e)}')

    context = {
        'media_item' : media_item ,
        'title' : f'Замена файла: {media_item.title}' ,
    }

    return render(request , 'admin/media_library/replace_file.html' , context)