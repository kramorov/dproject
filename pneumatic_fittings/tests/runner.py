# pneumatic_fittings/tests/runner.py
from django.test.runner import DiscoverRunner
from django.db.backends.sqlite3 import schema as sqlite3_schema

_NOOP_EXIT = lambda self , *a , **kw : False


class NoFKCheckRunner(DiscoverRunner) :
    def setup_databases(self , **kwargs) :
        # Отключаем check_constraints на время создания тестовой БД
        original_exit = sqlite3_schema.DatabaseSchemaEditor.__exit__
        sqlite3_schema.DatabaseSchemaEditor.__exit__ = _NOOP_EXIT
        try :
            return super().setup_databases(**kwargs)
        finally :
            sqlite3_schema.DatabaseSchemaEditor.__exit__ = original_exit