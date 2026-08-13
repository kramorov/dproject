"""Standalone test runner для assemblies — копия рабочей БД.

Запуск: python assemblies/tests/runtests.py [-v]

Делает копию рабочей БД (db.sqlite3), тесты работают на копии,
оригинал не трогается. Копия удаляется после прогона.
"""
import os
import sys
import shutil
import atexit
import unittest

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoProject1.settings")

import django
from django.conf import settings

_working_db = os.path.join(_PROJECT_ROOT, "db.sqlite3")
if not os.path.exists(_working_db):
    print(f"ERROR: Working DB not found at {_working_db}")
    sys.exit(1)

_test_db_path = os.path.join(_PROJECT_ROOT, "_test_db_copy.sqlite3")
shutil.copy2(_working_db, _test_db_path)

def _cleanup():
    try:
        from django.db import connections
        connections.close_all()
    except Exception:
        pass
    try:
        if os.path.exists(_test_db_path):
            os.remove(_test_db_path)
    except OSError:
        pass

atexit.register(_cleanup)
print(f"Using working DB copy: {_test_db_path}")

settings.DATABASES["default"]["NAME"] = _test_db_path
settings.DATABASES["default"]["TEST"] = {"NAME": _test_db_path, "MIRROR": None}

from django.test.runner import DiscoverRunner
DiscoverRunner.setup_databases = lambda self, *a, **kw: []
DiscoverRunner.teardown_databases = lambda self, *a, **kw: None

django.setup()

from assemblies.tests.test_services import ForkTest, FixateTest, ValidatorTest, ResolutionTest
from assemblies.tests.test_scenarios import ScenarioTest

if __name__ == "__main__":
    verbose = "-v" in sys.argv
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for tc in [ForkTest, FixateTest, ValidatorTest, ResolutionTest, ScenarioTest]:
        suite.addTests(loader.loadTestsFromTestCase(tc))

    verbosity = 2 if verbose else 1
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)

    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"\n{'=' * 60}")
    print(f"Ran {result.testsRun} tests")
    print(f"  OK:    {passed}")
    print(f"  FAIL:  {len(result.failures)}")
    print(f"  ERROR: {len(result.errors)}")

    if result.failures or result.errors:
        for t, tb in (result.failures + result.errors):
            print(f"\n{t}")
            for line in tb.strip().split("\n")[-8:]:
                print(f"    {line.strip()}")

    sys.exit(0 if result.wasSuccessful() else 1)
