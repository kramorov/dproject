# core/utils/ts_config.py
"""
Конфигурация генератора TypeScript.
"""

from django.conf import settings


class TypeScriptConfig :
    """Конфигурация генератора"""

    @classmethod
    def get_config(cls) :
        """Получить конфигурацию из settings.py"""
        return getattr(settings , 'TYPESCRIPT_GENERATOR' , {
            'output_dir' : None ,  # Автоопределение
            'include_apps' : None ,  # Все приложения
            'exclude_apps' : ['auth' , 'admin' , 'sessions' , 'contenttypes'] ,
            'type_mapping' : {
                'CharField' : 'string' ,
                'TextField' : 'string' ,
                'IntegerField' : 'number' ,
                'BooleanField' : 'boolean' ,
                'DateField' : 'string' ,
                'DateTimeField' : 'string' ,
                'FloatField' : 'number' ,
                'DecimalField' : 'number' ,
                'EmailField' : 'string' ,
                'URLField' : 'string' ,
                'JSONField' : 'any' ,
            } ,
            'graphql' : {
                'enabled' : True ,
                'fragments' : True ,
                'operations' : True ,
            } ,
            'formatting' : {
                'indent' : 2 ,
                'single_quote' : True ,
                'trailing_comma' : 'es5' ,
            }
        })

    @classmethod
    def get_output_dir(cls) :
        """Получить выходную директорию"""
        config = cls.get_config()

        if config.get('output_dir') :
            return config['output_dir']

        # Автоопределение
        import os
        base_dir = settings.BASE_DIR

        # Пробуем разные варианты
        possible_paths = [
            os.path.join(base_dir , 'frontend/src/types/auto-generated') ,
            os.path.join(base_dir , '../frontend/src/types/auto-generated') ,
            os.path.join(base_dir , 'types/auto-generated') ,
        ]

        for path in possible_paths :
            if os.path.exists(os.path.dirname(path)) :
                os.makedirs(path , exist_ok=True)
                return path

        # Создаем в корне
        default_path = os.path.join(base_dir , 'types/auto-generated')
        os.makedirs(default_path , exist_ok=True)
        return default_path