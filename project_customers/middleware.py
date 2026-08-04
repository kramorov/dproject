"""
CustomerMiddleware — attaches request.customer and request.customer_user from session.
"""
from project_customers.models import ProjectCustomerUser


class CustomerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        profile_id = request.session.get('customer_user_id')
        if profile_id:
            try:
                profile = ProjectCustomerUser.objects.select_related('customer').get(
                    id=profile_id, is_active=True
                )
                request.customer_user = profile
                request.customer = profile.customer
            except ProjectCustomerUser.DoesNotExist:
                pass
        return self.get_response(request)
