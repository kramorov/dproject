#project_customers/admin/__init__.py
from .customer_admin import ProjectCustomerAdmin
from .legal_entity_admin import LegalEntityAdmin
from .user_admin import ProjectCustomerUserAdmin
from .settings_admin import CustomerSettingsAdmin, UserSettingsAdmin
from .user_parameter_admin import UserParameterAdmin

__all__ = [
    'ProjectCustomerAdmin',
    'LegalEntityAdmin',
    'ProjectCustomerUserAdmin',
    'CustomerSettingsAdmin',
    'UserSettingsAdmin',
    'UserParameterAdmin',
]