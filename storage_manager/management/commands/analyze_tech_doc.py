"""
python manage.py analyze_tech_doc — анализ TECH_DOC на дубли.
"""
from django.core.management.base import BaseCommand
from media_library.models import MediaLibraryItem
from collections import defaultdict


class Command(BaseCommand):
    help = 'Анализ TECH_DOC: дубликаты, группы похожих'

    def handle(self, **options):
        items = MediaLibraryItem.objects.filter(
            category__code='TECH_DOC', is_active=True
        ).order_by('name')

        self.stdout.write(f'Всего TECH_DOC: {items.count()}')
        self.stdout.write()

        # 1. По имени файла (без расширения)
        by_filename = defaultdict(list)
        for item in items:
            if item.media_file:
                name = item.media_file.name.split('/')[-1].rsplit('.', 1)[0].lower()
                by_filename[name].append(item)

        dupes = {k: v for k, v in by_filename.items() if len(v) > 1}
        if dupes:
            self.stdout.write('=== ДУБЛИ ПО ИМЕНИ ФАЙЛА ===')
            for name, group in sorted(dupes.items()):
                self.stdout.write(f'\n  {name}:')
                for item in group:
                    size = item.media_file.size if item.media_file else 0
                    self.stdout.write(f'    #{item.id} {item.name[:70]} ({self._fmt(size)})')
        else:
            self.stdout.write('Дублей по имени файла нет.')

        # 2. По размеру файла
        by_size = defaultdict(list)
        for item in items:
            if item.media_file:
                size = item.media_file.size
                if size > 0:
                    by_size[size].append(item)

        size_dupes = {k: v for k, v in by_size.items() if len(v) > 1}
        if size_dupes:
            self.stdout.write('\n=== ДУБЛИ ПО РАЗМЕРУ ФАЙЛА ===')
            for size, group in sorted(size_dupes.items(), reverse=True):
                self.stdout.write(f'\n  {self._fmt(size)}:')
                for item in group:
                    fname = item.media_file.name.split('/')[-1] if item.media_file else '-'
                    self.stdout.write(f'    #{item.id} {item.name[:60]} | {fname}')
        else:
            self.stdout.write('\nДублей по размеру нет.')

        # 3. Все элементы TECH_DOC с именами файлов
        self.stdout.write('\n=== ВСЕ TECH_DOC ===')
        self.stdout.write(f'{"#":<6s} {"Размер":>10s} {"Имя файла":<50s} {"Название"}')
        self.stdout.write('-' * 120)
        total = 0
        for item in items:
            fname = item.media_file.name.split('/')[-1] if item.media_file else '-'
            size = item.media_file.size if item.media_file else 0
            total += size
            self.stdout.write(f'{item.id:<6d} {self._fmt(size):>10s} {fname:<50s} {item.name[:60]}')
        self.stdout.write(f'\nВсего: {items.count()} элементов, {self._fmt(total)}')

        # 4. Группировка по первой части имени
        by_prefix = defaultdict(lambda: {'count': 0, 'size': 0, 'items': []})
        for item in items:
            # Извлекаем «семейство» из названия
            name = item.name.lower()
            if 'ямлл' in name or 'ямал' in name:
                prefix = 'ЯМАЛ'
            elif 'амур' in name:
                prefix = 'АМУР'
            elif 'урал' in name:
                prefix = 'УРАЛ'
            elif 'apl' in name:
                prefix = 'APL'
            elif 'фильтр' in name or 'bpfr' in name or 'bpafr' in name:
                prefix = 'Фильтр-регуляторы'
            elif 'соленоид' in name or 'solenoid' in name:
                prefix = 'Соленоидные клапаны'
            else:
                prefix = 'Прочее'
            by_prefix[prefix]['count'] += 1
            by_prefix[prefix]['size'] += (item.media_file.size if item.media_file else 0)
            by_prefix[prefix]['items'].append(item)

        self.stdout.write('\n=== ПО СЕМЕЙСТВАМ ===')
        for prefix in sorted(by_prefix, key=lambda p: -by_prefix[p]['size']):
            info = by_prefix[prefix]
            self.stdout.write(f'  {prefix:<20s} {info["count"]:>4d} шт  {self._fmt(info["size"]):>10s}')

    @staticmethod
    def _fmt(s):
        for unit in ('Б', 'КБ', 'МБ', 'ГБ'):
            if s < 1024:
                return f'{s:.1f} {unit}'
            s /= 1024
        return f'{s:.1f} ГБ'
