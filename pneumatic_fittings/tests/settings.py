# pneumatic_fittings/tests/settings.py
import shutil , os
from djangoProject1.settings import *

TEST_RUNNER = 'pneumatic_fittings.tests.runner.NoFKCheckRunner'

# Копируем основную БД как тестовую
original_db = os.path.join(BASE_DIR , 'db.sqlite3')
test_db = os.path.join(BASE_DIR , 'test_db_copy.sqlite3')
shutil.copy2(original_db , test_db)

DATABASES = {
    'default' : {
        'ENGINE' : 'django.db.backends.sqlite3' ,
        'NAME' : test_db ,
        'TEST' : {
            'NAME' : test_db ,
            'MIGRATE' : False ,     # ← не гонять миграции на копии
        } ,
    }
}
