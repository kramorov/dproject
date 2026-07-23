#project_customers/admin/__init__.py
from .customer_admin import ProjectCustomerAdmin
from .legal_entity_admin import LegalEntityAdmin
from .user_admin import ProjectCustomerUserAdmin
from .settings_admin import CustomerSettingsAdmin, UserSettingsAdmin
from .user_parameter_admin import UserParameterAdmin
from .site_section_admin import SiteSectionAdmin
from .allowed_app_admin import AllowedAppAdmin
from .customer_app_access_admin import CustomerAppAccessAdmin
from .customer_email_admin import CustomerEmailAdmin
from .role_admin import RoleAdmin
from .favorite_brand_admin import FavoriteBrandAdmin
from .customer_api_key_admin import CustomerApiKeyAdmin

__all__ = [
    'ProjectCustomerAdmin',
    'LegalEntityAdmin',
    'ProjectCustomerUserAdmin',
    'CustomerSettingsAdmin',
    'UserSettingsAdmin',
    'UserParameterAdmin',
    'SiteSectionAdmin',
    'AllowedAppAdmin',
    'CustomerAppAccessAdmin',
    'CustomerEmailAdmin',
    'RoleAdmin',
    'FavoriteBrandAdmin',
    'CustomerApiKeyAdmin',
]
