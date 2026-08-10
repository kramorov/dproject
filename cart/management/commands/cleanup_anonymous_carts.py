# cart/management/commands/cleanup_anonymous_carts.py
"""
Очистка анонимных корзин старше N дней.

Использование:
    python manage.py cleanup_anonymous_carts --days 30
    python manage.py cleanup_anonymous_carts --days 30 --dry-run
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from cart.models import Cart, CartEvent


class Command(BaseCommand):
    help = 'Удаляет (abandoned) анонимные корзины старше N дней.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30,
                            help='Возраст в днях (по умолчанию 30)')
        parser.add_argument('--dry-run', action='store_true',
                            help='Только показать, не удалять')

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        cutoff = timezone.now() - timedelta(days=days)

        # Анонимные корзины: user IS NULL, session_key IS NOT NULL, активные, старые
        qs = Cart.objects.filter(
            user__isnull=True,
            session_key__isnull=False,
            status=Cart.Status.ACTIVE,
            updated_at__lt=cutoff,
        )

        count = qs.count()
        self.stdout.write(f'Анонимных корзин старше {days} дн.: {count}')

        if dry_run:
            self.stdout.write('[DRY RUN] Будут помечены как abandoned:')
            for cart in qs[:10]:
                self.stdout.write(f'  {cart.id} ({cart.item_count} поз., {cart.updated_at})')
            if count > 10:
                self.stdout.write(f'  ... и ещё {count - 10}')
            return

        ids = list(qs.values_list('id', flat=True))
        qs.update(status=Cart.Status.ABANDONED)

        # Логируем
        for cid in ids:
            CartEvent.objects.create(
                cart_id=cid,
                event_type=CartEvent.EventType.ABANDONED,
                data={'auto_cleanup': True, 'days': days},
            )

        self.stdout.write(self.style.SUCCESS(f'Очищено: {len(ids)} корзин'))
