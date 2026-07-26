"""Admin registration for ai_assistant.

All admin classes are defined in the ``admin/`` package and auto-discovered
through ``admin.register`` decorators. This file imports the package to
trigger registration.
"""

from ai_assistant.admin import *  # noqa: F401, F403
