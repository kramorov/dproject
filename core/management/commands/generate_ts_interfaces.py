# core/management/commands/generate_ts_interfaces.py
from django.apps import apps
from django.core.management.base import BaseCommand
from django.conf import settings
from core.utils.ts_generator import generate_typescript_interfaces
import os
import time


class Command(BaseCommand) :
    help = 'Генерирует TypeScript интерфейсы из Django моделей'

    def add_arguments(self , parser) :
        parser.add_argument(
            '--output' ,
            dest='output_dir' ,
            type=str ,
            help='Директория для сохранения TypeScript файлов'
        )
        parser.add_argument(
            '--apps' ,
            type=str ,
            nargs='+' ,
            help='Список приложений для обработки (через пробел)'
        )
        parser.add_argument(
            '--watch' ,
            action='store_true' ,
            help='Режим отслеживания изменений моделей'
        )
        parser.add_argument(
            '--clear' ,
            action='store_true' ,
            help='Очистить сгенерированные файлы перед генерацией'
        )

    def handle(self , *args , **options) :
        output_dir = options.get('output_dir')
        include_apps = options.get('apps')
        watch_mode = options.get('watch')
        clear_mode = options.get('clear')

        if clear_mode and output_dir and os.path.exists(output_dir) :
            self.stdout.write(f"🧹 Очистка директории: {output_dir}")
            for file in os.listdir(output_dir) :
                if file.endswith('.ts') :
                    os.remove(os.path.join(output_dir , file))

        try :
            self.stdout.write(self.style.SUCCESS('🔄 Генерация TypeScript интерфейсов...'))

            # Генерируем интерфейсы
            result = generate_typescript_interfaces(output_dir , include_apps)

            self.stdout.write(self.style.SUCCESS('✅ Генерация завершена!'))
            self.stdout.write(f"📁 Выходная директория: {output_dir or 'автоопределена'}")

            for filename in result.keys() :
                self.stdout.write(f"  📄 {filename}.ts")

            # Режим отслеживания
            if watch_mode :
                self._start_watch_mode(output_dir , include_apps)

        except Exception as e :
            self.stdout.write(self.style.ERROR(f'❌ Ошибка генерации: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())

    def _start_watch_mode(self , output_dir , include_apps) :
        """Запуск режима отслеживания"""
        self.stdout.write(self.style.WARNING('\n👀 Режим отслеживания активирован...'))
        self.stdout.write('Для выхода нажмите Ctrl+C\n')

        # Простой polling вместо watchdog для упрощения
        last_check = time.time()
        monitored_files = {}

        # Собираем все models.py файлы
        for app_config in apps.get_app_configs() :
            if include_apps and app_config.label not in include_apps :
                continue

            try :
                app_module = __import__(app_config.name)
                app_path = os.path.dirname(app_module.__file__)
                models_file = os.path.join(app_path , 'models.py')

                if os.path.exists(models_file) :
                    monitored_files[models_file] = os.path.getmtime(models_file)
            except (ImportError , AttributeError) :
                continue

        try :
            while True :
                time.sleep(1)  # Проверяем каждую секунду

                current_time = time.time()
                if current_time - last_check < 2 :  # Не чаще чем раз в 2 секунды
                    continue

                changed = False
                for filepath , last_mtime in list(monitored_files.items()) :
                    if not os.path.exists(filepath) :
                        continue

                    current_mtime = os.path.getmtime(filepath)
                    if current_mtime > last_mtime :
                        self.stdout.write(
                            self.style.NOTICE(f'\n📁 Изменен: {filepath}')
                        )
                        monitored_files[filepath] = current_mtime
                        changed = True

                if changed :
                    self.stdout.write('🔄 Перегенерация интерфейсов...')
                    generate_typescript_interfaces(output_dir , include_apps)
                    self.stdout.write(self.style.SUCCESS('✅ Интерфейсы обновлены!'))

                last_check = current_time

        except KeyboardInterrupt :
            self.stdout.write(self.style.WARNING('\n👋 Остановлено пользователем'))