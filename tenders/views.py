# views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import CSVImportSerializer
from .models import ImportLog


class CSVImportView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = CSVImportSerializer(data=request.data)

        if serializer.is_valid():
            try:
                result = serializer.save()

                response_data = {
                    'message': 'Импорт завершен',
                    'details': result,
                    'success': result['status'] == 'success'
                }

                status_code = status.HTTP_200_OK if result['status'] != 'failed' else status.HTTP_400_BAD_REQUEST

                return Response(response_data, status=status_code)

            except Exception as e:
                return Response(
                    {'error': f'Ошибка импорта: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ImportHistoryView(APIView):
    def get(self, request):
        logs = ImportLog.objects.all()[:10]  # Последние 10 импортов
        data = [
            {
                'filename': log.filename,
                'imported_at': log.imported_at,
                'total_rows': log.total_rows,
                'imported_rows': log.imported_rows,
                'skipped_rows': log.skipped_rows,
                'status': log.status
            }
            for log in logs
        ]
        return Response(data)