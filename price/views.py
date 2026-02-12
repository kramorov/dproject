# price/views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
from django.contrib import messages
from .services.cbr_exchange import CBRExchangeService

@staff_member_required
def update_exchange_rates(request):
    try:
        CBRExchangeService.fetch_and_save_rates()
        messages.success(request, 'Курсы валют успешно обновлены')
    except Exception as e:
        messages.error(request, f'Ошибка обновления: {e}')
    return redirect(request.META.get('HTTP_REFERER', 'admin:price_exchangerate_changelist'))