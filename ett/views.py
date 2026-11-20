import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services import decode_ett

logger = logging.getLogger(__name__)


class EttDecodeView(APIView):
    """Принимает код ЕТТ и возвращает его расшифровку."""

    def post(self, request, *args, **kwargs):
        data = request.data or {}
        if not hasattr(data, 'get'):
            # Некорректное тело (массив/строка) — обрабатываем как пустой ввод.
            data = {}

        code = data.get('code') or data.get('input_string') or ''
        if not isinstance(code, str):
            code = str(code)
        code = code.strip()
        if not code:
            return Response(
                {'error': 'Код ЕТТ не может быть пустым.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = decode_ett(code)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:  # noqa: BLE001 — не роняем запрос, не отдаём внутренности клиенту
            logger.exception('Ошибка расшифровки ЕТТ-кода %r', code)
            return Response(
                {'error': 'Внутренняя ошибка при расшифровке кода ЕТТ.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({'code': code, **result}, status=status.HTTP_200_OK)
