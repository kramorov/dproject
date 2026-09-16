# commercial/services/numbering.py
"""
Нумерация КП (quotation) на основе существующих счётчиков, привязанных к
компании/пользователю.

Использует RequestNumberCounter (company + user) и шаблон из UserParameter
(code='quotation_number_template'), аналогично ClientRequest.generate_request_number().
Для корзин без компании/пользователя — фоллбэк на DocumentNumerator.
"""
import re

from django.utils import timezone

from client_requests.models.request_number_counter import RequestNumberCounter
from project_customers.models.user_parameter import get_user_parameter

DEFAULT_QUOTATION_NUMBER_TEMPLATE = 'КП-{year}-{company_seq}-{user_seq}'


def render_number_template(template, company_seq, user_seq):
    now = timezone.now()
    context = {
        'year': now.strftime('%Y'),
        'year_short': now.strftime('%y'),
        'month': now.strftime('%m'),
        'day': now.strftime('%d'),
        'company_seq': company_seq or '',
        'user_seq': user_seq or '',
    }

    result = template or DEFAULT_QUOTATION_NUMBER_TEMPLATE
    for key, value in context.items():
        result = result.replace('{' + key + '}', str(value))

    # {company_seq:05d} / {user_seq:05d}
    pattern = r'\{(company_seq|user_seq):(\d+)d\}'

    def replace(match):
        var_name = match.group(1)
        width = int(match.group(2))
        val = context.get(var_name, 0)
        try:
            return str(int(val)).zfill(width)
        except (TypeError, ValueError):
            return '0' * width

    return re.sub(pattern, replace, result)


def generate_quotation_number(project_customer, project_customer_user):
    """Вернуть номер КП. Если есть компания+пользователь — счётчик компании/пользователя."""
    template = DEFAULT_QUOTATION_NUMBER_TEMPLATE
    if project_customer_user is not None:
        template = get_user_parameter(
            project_customer_user,
            'quotation_number_template',
            default_value=DEFAULT_QUOTATION_NUMBER_TEMPLATE,
        ) or DEFAULT_QUOTATION_NUMBER_TEMPLATE

    company_seq = None
    user_seq = None

    if project_customer is not None and project_customer_user is not None:
        try:
            company_seq, user_seq = RequestNumberCounter.get_next_numbers(
                project_customer=project_customer,
                project_customer_user=project_customer_user,
            )
        except Exception:
            company_seq = user_seq = None

    if company_seq is None and user_seq is None:
        # Фоллбэк для корзин без компании/пользователя — универсальный нумератор.
        from documents.models.document_numerator import DocumentNumerator
        return DocumentNumerator.get_next_code('КП', year=timezone.now().year)

    return render_number_template(template, company_seq, user_seq)
