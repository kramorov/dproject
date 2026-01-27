# features/models/equipment_type.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import BaseAbstractModel


class EquipmentType(BaseAbstractModel):
    """
    Тип оборудования (классификатор)
    Примеры: 'Пневмопривод', 'Электропривод', 'Клапан', 'Задвижка'
    """
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_("Родительский тип"),
        help_text=_("Родительский тип оборудования для иерархии")
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Иконка"),
        help_text=_("Иконка для отображения (emoji или название класса CSS)")
    )

    # Уровень в иерархии (для удобства)
    level = models.IntegerField(
        default=0,
        verbose_name=_("Уровень иерархии"),
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )

    class Meta:
        verbose_name = _("Тип оборудования")
        verbose_name_plural = _("Типы оборудования")
        ordering = ['level', 'sorting_order', 'name']

    def get_descendants_ids(self) :
        """Получить ID всех потомков (включая вложенные)"""
        from django.db.models import Q
        from django.db import connection

        # Способ 1: Рекурсивный SQL запрос (если база поддерживает)
        if connection.vendor == 'postgresql' :
            # Для PostgreSQL с рекурсивными CTE
            from django.db import connection
            with connection.cursor() as cursor :
                cursor.execute("""
                    WITH RECURSIVE descendants AS (
                        SELECT id, parent_id
                        FROM features_equipmenttype
                        WHERE id = %s
                        UNION ALL
                        SELECT child.id, child.parent_id
                        FROM features_equipmenttype child
                        INNER JOIN descendants parent ON child.parent_id = parent.id
                    )
                    SELECT id FROM descendants WHERE id != %s
                """ , [self.id , self.id])
                return [row[0] for row in cursor.fetchall()]

        # Способ 2: Рекурсивный Python (универсальный, но медленнее для больших деревьев)
        def get_children_ids(parent_id) :
            children = EquipmentType.objects.filter(parent_id=parent_id).values_list('id' , flat=True)
            result = list(children)
            for child_id in children :
                result.extend(get_children_ids(child_id))
            return result

        return get_children_ids(self.id)

    def get_descendants(self) :
        """Получить всех потомков (включая вложенные)"""
        ids = self.get_descendants_ids()
        return EquipmentType.objects.filter(id__in=ids) if ids else EquipmentType.objects.none()

    def get_all_children_ids(self) :
        """Алиас для совместимости (если где-то используется это название)"""
        return self.get_descendants_ids()

    def save(self, *args, **kwargs):
        """Автоматически вычисляем уровень при сохранении"""
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 0
        super().save(*args, **kwargs)

    def get_full_path(self):
        """Получить полный путь в иерархии"""
        path = []
        current = self
        while current:
            path.insert(0, current.name)
            current = current.parent
        return " → ".join(path)

    def get_children_count(self):
        """Количество дочерних элементов"""
        return self.children.count()

    # ==================== StructuredDataMixin методы ====================

    def get_compact_data(self) -> dict:
        data = super().get_compact_data()
        data.update({
            'level': self.level,
            'parent_id': self.parent_id,
            'icon': self.icon,
            'full_path': self.get_full_path(),
            'children_count': self.get_children_count(),
        })
        return data

    def get_display_data(self, view_type: str = 'detail') -> dict:
        if view_type == self.LIST:
            return {
                'id': self.id,
                'name': self.name,
                'code': self.code,
                'level': self.level,
                'full_path': self.get_full_path(),
                'is_active': self.is_active,
                'children_count': self.get_children_count(),
            }

        fields = self._get_base_display_fields()
        fields.update({
            'parent': self._format_foreign_key(
                self.parent,
                label=_("Родительский тип"),
                icon='↕️',
                priority=5,
                include_data='compact'
            ),
            'level': self._format_field(
                self.level,
                'number',
                label=_("Уровень иерархии"),
                icon='📊',
                priority=6
            ),
            'icon': self._format_field(
                self.icon,
                'text',
                label=_("Иконка"),
                icon='🎨',
                priority=7
            ),
            'children': self._format_many_to_many(
                self.children.all(),
                label=_("Дочерние типы"),
                icon='📂',
                priority=8,
                include_data='compact'
            ),
        })

        return {
            'title': self.name,
            'subtitle': f'{self.get_full_path()}',
            'fields': fields,
            'actions': self._get_actions()
        }