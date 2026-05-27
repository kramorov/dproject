"""
POST /api/auth/login/  — аутентификация через Django session
POST /api/auth/logout/ — выход
GET  /api/auth/me/     — текущий пользователь
"""
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from project_customers.models.user import ProjectCustomerUser


class LoginView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({'csrftoken': request.META.get('CSRF_COOKIE', '')})

    @method_decorator(ensure_csrf_cookie)
    def post(self, request):
        username = request.data.get('username', '')
        password = request.data.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            role = 'viewer'
            try:
                profile = ProjectCustomerUser.objects.get(user=user)
                role = profile.role
            except ProjectCustomerUser.DoesNotExist:
                pass
            return Response({'username': user.username, 'role': role})
        return Response({'error': 'Неверный логин или пароль'}, status=400)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'ok': True})


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        role = 'admin' if user.is_superuser else 'viewer'
        customer_name = ''
        try:
            profile = ProjectCustomerUser.objects.get(user=user)
            role = profile.role
            customer_name = profile.customer.name if profile.customer else ''
        except ProjectCustomerUser.DoesNotExist:
            pass
        return Response({
            'username': user.username,
            'email': user.email,
            'role': role,
            'customer': customer_name,
        })