from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from project_customers.models import SiteSection, AllowedApp
from django.contrib.auth.models import User


class SectionsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        sections = [{'code': s.code, 'name': s.name, 'is_active': s.is_active}
                    for s in SiteSection.objects.filter(is_active=True).order_by('sorting_order')]
        return Response({'sections': sections})


class AllowedAppsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        apps = [{'code': a.code, 'name': a.name, 'has_brand_filter': a.has_brand_filter, 'is_active': a.is_active}
                for a in AllowedApp.objects.filter(is_active=True).order_by('sorting_order')]
        return Response({'apps': apps})


class BrandsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        from producers.models import Brands
        brands = [{'id': b.id, 'name': b.name, 'code': b.code, 'is_active': b.is_active}
                  for b in Brands.objects.filter(is_active=True).order_by('sorting_order', 'name')]
        return Response({'brands': brands})


class DjangoUsersView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        users = [{'id': u.id, 'username': u.username, 'is_active': u.is_active}
                 for u in User.objects.filter(is_active=True).order_by('username')]
        return Response({'users': users})
