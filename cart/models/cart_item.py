# cart/models/cart_item.py
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class CartItem(models.Model):
    """
    Позиция корзины — ссылка на SKU (единицу номенклатуры).

    SKU унифицирует все товары: артикул, наименование, бренд, тип,
    связь с моделью-источником через source_object (GFK), цены через PriceHistory.
    Сборки (MBOM) — через отдельный flow, не через корзину.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    cart = models.ForeignKey(
        'cart.Cart',
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Корзина'),
    )

    sku = models.ForeignKey(
        'sku.SKU',
        on_delete=models.PROTECT,
        related_name='cart_items',
        verbose_name=_('SKU'),
    )

    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Количество'),
    )

    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Добавлено'),
    )

    # ── Кеш цены: обновляется раз в день ──
    price_snapshot = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True,
        verbose_name=_('Цена (кеш)'),
        help_text=_('Цена в RUB на дату price_date. Обновляется раз в день.'),
    )
    price_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Дата цены'),
        help_text=_('Если < сегодня → пересчитать по курсу.'),
    )
    price_currency = models.CharField(
        max_length=3, blank=True,
        verbose_name=_('Валюта цены'),
        help_text=_('RUB — после конвертации из USD по курсу.'),
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Заметки'),
    )

    class Meta:
        verbose_name = _('Позиция корзины')
        verbose_name_plural = _('Позиции корзины')
        ordering = ['added_at']
        indexes = [
            models.Index(fields=['sku']),
        ]

    def __str__(self):
        return f'{self.sku.code} — {self.sku.name} ×{self.quantity}'

    def get_equipment_summary(self):
        """Расширенная информация: артикул, название, бренд, фото, хар-ки."""
        s = self.sku
        summary = {
            'code': s.code,
            'name': s.name,
            'brand': s.brand.name if s.brand else '',
            'image': None,
            'specs': [],
            'source': {'ct': s.source_content_type_id, 'oid': s.source_object_id},
        }

        try:
            source = s.source_object
            if not source:
                return summary

            # ── Изображения (источник → model_line → images) ──
            def _first_image_url(gallery_obj):
                """Извлечь preview_url из первого элемента gallery."""
                if not gallery_obj:
                    return None
                items = getattr(gallery_obj, 'items', None)
                if not items or not hasattr(items, 'all'):
                    return None
                gi = items.first()
                if gi and gi.image:
                    return getattr(gi.image, 'preview_url', None) or getattr(gi.image, 'url', None)
                return None

            summary['image'] = _first_image_url(getattr(source, 'image_gallery', None))
            # Fallback: model_line
            if not summary['image']:
                ml = getattr(source, 'model_line', None)
                if ml:
                    summary['image'] = _first_image_url(getattr(ml, 'image_gallery', None))
            # Fallback: images (M2M)
            if not summary['image']:
                imgs = getattr(source, 'images', None)
                if imgs and hasattr(imgs, 'all'):
                    first_img = imgs.first()
                    if first_img:
                        summary['image'] = getattr(first_img, 'preview_url', None) or getattr(first_img, 'url', None)

            # ── Характеристики (общие для всех типов оборудования) ──
            specs = summary['specs']

            # IP
            ip = getattr(source, 'ip', None)
            if ip:
                specs.append({'label': 'IP', 'value': getattr(ip, 'name', '') or str(ip)})

            # Взрывозащита
            exd = getattr(source, 'exd', None)
            if exd:
                if hasattr(exd, 'all'):
                    exd_names = [getattr(e, 'name', str(e)) for e in exd.all()[:3]]
                    if exd_names:
                        specs.append({'label': 'Ex', 'value': ', '.join(exd_names)})

            # Температура
            tmin = getattr(source, 'work_temp_min', None)
            tmax = getattr(source, 'work_temp_max', None)
            if tmin is not None or tmax is not None:
                specs.append({'label': 't, °C', 'value': f'{tmin or "…"}…{tmax or "…"}'})

            # Материал корпуса
            bm = getattr(source, 'body_material', None)
            if bm:
                specs.append({'label': 'Корпус', 'value': getattr(bm, 'name', '') or str(bm)})

            # Момент (gearbox)
            torque = getattr(source, 'max_work_torque', None) or getattr(source, 'torque', None)
            if torque is not None:
                specs.append({'label': 'Момент, Нм', 'value': str(torque)})

            # Расход (filter-regulator)
            flow = getattr(source, 'flow_rate', None)
            if flow is not None:
                specs.append({'label': 'Расход, л/мин', 'value': str(flow)})

            # Тип сенсора (БКВ)
            sv = getattr(source, 'sensor_variety', None)
            if sv:
                specs.append({'label': 'Датчики', 'value': getattr(sv, 'name', '') or str(sv)})

            # Количество контактов (БКВ)
            pts = getattr(source, 'points', None) or getattr(source, 'points_option', None)
            if pts:
                specs.append({'label': 'Контакты', 'value': str(getattr(pts, 'name', pts)) if hasattr(pts, 'name') else str(pts)})

            # Функция клапана (solenoid)
            func = getattr(source, 'function', None)
            if func:
                specs.append({'label': 'Функция', 'value': getattr(func, 'name', '') or str(func)})

            # Управление (solenoid)
            act = getattr(source, 'actuation', None)
            if act:
                specs.append({'label': 'Управление', 'value': getattr(act, 'name', '') or str(act)})

            # Напряжение (solenoid)
            ps = getattr(source, 'power_supply', None)
            if ps:
                specs.append({'label': 'Питание', 'value': getattr(ps, 'name', '') or str(ps)})

            # Пневмоприсоединение
            pc = getattr(source, 'pneumatic_connection', None)
            if pc:
                specs.append({'label': 'Пневмо', 'value': getattr(pc, 'name', '') or str(pc)})

            # Тип фитинга
            fv = getattr(source, 'fitting_variety', None)
            if fv:
                specs.append({'label': 'Тип', 'value': getattr(fv, 'name', '') or str(fv)})

            # Резьба
            thread = getattr(source, 'thread', None)
            if thread:
                specs.append({'label': 'Резьба', 'value': getattr(thread, 'name', '') or str(thread)})

            # Монтажная площадка (gearbox)
            mp = getattr(source, 'mounting_plate_top', None)
            if mp:
                specs.append({'label': 'Площадка', 'value': getattr(mp, 'name', '') or str(mp)})

        except Exception:
            pass
        return summary
