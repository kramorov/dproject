# cart/urls.py
from django.urls import path

from . import views

urlpatterns = [
    # GET — список корзин
    path('', views.cart_list, name='cart-list'),

    # GET — активная корзина с позициями
    path('active/', views.cart_detail, name='cart-active'),

    # GET — избранное
    path('favorites/', views.favorites, name='favorites'),

    # POST — добавить позицию
    path('add/', views.add_item, name='cart-add'),

    # POST — создать новую корзину
    path('create/', views.create_cart, name='cart-create'),

    # POST — оформить заказ
    path('checkout/', views.checkout, name='cart-checkout'),

    # DELETE — удалить позицию
    path('items/<str:item_id>/', views.remove_item, name='cart-item-delete'),

    # PATCH — изменить количество
    path('items/<str:item_id>/update/', views.update_item, name='cart-item-update'),

    # GET — деталировка товара для popup
    path('items/<str:item_id>/detail/', views.item_detail, name='cart-item-detail'),

    # GET — конкретная корзина
    path('<str:cart_id>/', views.cart_detail, name='cart-detail'),

    # PATCH/DELETE — управление корзиной
    path('<str:cart_id>/manage/', views.manage_cart, name='cart-manage'),

    # POST — сделать корзину активной
    path('<str:cart_id>/activate/', views.activate_cart, name='cart-activate'),
]
