# valve_data/models/dimensions/valve_dimension_table.py
# valve_data/models/dimension_models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from collections import defaultdict

from media_library.models import MediaLibraryItem
from params.models import DnVariety, PnVariety
from producers.models import Brands
# from valve_data.models import ValveVariety, DimensionTableParameter, DimensionTableDrawingItem

import logging
logger = logging.getLogger(__name__)

class ValveDimensionTable(models.Model):
    """Таблица ВГХ для линейки арматуры - к этой таблице привязываем все данные - чертежи, таблицы значений"""
    name = models.CharField(
        max_length=100,
        verbose_name=_('Название таблицы'),
        help_text=_('Название таблицы ВГХ')
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text=_('Код шаблона ВГХ'),
        verbose_name=_('Код шаблона')
    )
    valve_brand = models.ForeignKey(
        Brands,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='dimension_table_valve_brand',
        help_text=_('Бренд серии арматуры'),
        verbose_name=_("Бренд")
    )
    valve_variety = models.ForeignKey(
        # ValveVariety,
        'valve_data.ValveVariety',  # ← строковая ссылка вместо импорта
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='dimension_table_valve_variety',
        help_text=_('Тип арматуры'),
        verbose_name=_("Тип арматуры")
    )
    # Связь с чертежами из медиабиблиотеки
    drawings = models.ManyToManyField(
        MediaLibraryItem,
        through='DimensionTableDrawingItem',
        through_fields=('dimension_table', 'drawing'),
        related_name='dimension_tables',
        verbose_name=_("Чертежи"),
        help_text=_("Чертежи, связанные с этой таблицей ВГХ")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание'),
        help_text=_('Описание таблицы ВГХ')
    )

    class Meta:
        verbose_name = _("Таблица ВГХ")
        verbose_name_plural = _("Таблицы ВГХ")

    def __str__(self):
        return f"{self.name}"

    def get_dimension_data(self , dn_list=None , pn_list=None , export=False) :
        """
        Универсальный геттер для получения данных ВГХ

        Args:
            dn_list: список значений DN (строки или объекты)
            pn_list: список значений PN (строки или объекты)
            export: флаг экспортного формата

        Returns:
            dict: структура с изображениями и матрицами данных
        """
        try :
            logger.info(f"=== Начало get_dimension_data ===")
            logger.info(f"Входные параметры: dn_list={dn_list}, pn_list={pn_list}, export={export}")
            from valve_data.models import ValveDimensionData

            dn_objects = []
            dn_errors = []
            pn_objects = []
            pn_errors = []

            # Обрабатываем DN
            if dn_list is not None :
                # Получаем объекты DN с помощью универсального геттера
                dn_objects , dn_errors = DnVariety.get_dn_objects(dn_list)
                # Логируем ошибки поиска DN
                for error in dn_errors :
                    logger.warning(error)
            else :
                # Если dn_list=None, получаем все доступные DN для этой таблицы
                logger.info("dn_list=None - получаем все доступные DN для таблицы")
                unique_dns = ValveDimensionData.objects.filter(
                    parameter__dimension_table=self
                ).values_list('dn' , flat=True).distinct()
                dn_objects = DnVariety.objects.filter(id__in=unique_dns)
                logger.info(f"Получено всех доступных DN: {dn_objects.count()}")

            # Обрабатываем PN
            if pn_list is not None :
                # Получаем объекты PN с помощью универсального геттера
                pn_objects , pn_errors = PnVariety.get_pn_objects(pn_list)
                # Логируем ошибки поиска PN
                for error in pn_errors :
                    logger.warning(error)
            else :
                # Если pn_list=None, получаем все доступные PN для этой таблицы
                logger.info("pn_list=None - получаем все доступные PN для таблицы")
                unique_pns = ValveDimensionData.objects.filter(
                    parameter__dimension_table=self
                ).values_list('pn' , flat=True).distinct()
                pn_objects = PnVariety.objects.filter(id__in=unique_pns)
                logger.info(f"Получено всех доступных PN: {pn_objects.count()}")

            # СОРТИРУЕМ объекты по sorting_order
            dn_objects = sorted(dn_objects , key=lambda x : x.sorting_order)
            pn_objects = sorted(pn_objects , key=lambda x : x.sorting_order)

            # Получаем все данные для текущей таблицы и фильтруем по DN/PN
            all_data = ValveDimensionData.objects.filter(
                parameter__dimension_table=self
            )

            if dn_objects :
                all_data = all_data.filter(dn__in=dn_objects)
            if pn_objects :
                all_data = all_data.filter(pn__in=pn_objects)

            logger.info(f"Фильтрация данных: DN={len(dn_objects)}, PN={len(pn_objects)}")
            logger.info(f"Найдено записей ValveDimensionData: {all_data.count()}")

            all_data = all_data.select_related(
                'dn' , 'pn' , 'parameter' , 'parameter__parameter_variety'
            ).order_by('parameter__sorting_order' , 'pn__sorting_order' , 'dn__sorting_order')

            if not all_data.exists() :
                logger.warning("Нет данных ValveDimensionData для указанных параметров")
                return {
                    'images' : [] ,
                    'matrices' : [] ,
                    'errors' : dn_errors + pn_errors  # Объединяем все ошибки
                }

            # Получаем изображения для запрошенных DN
            images_data = self._get_images_for_dn_list(dn_objects , export)

            # Группируем данные по PN для создания отдельных матриц
            matrices = self._build_matrices(all_data , dn_objects , pn_objects , export)

            logger.info(f"=== Завершение get_dimension_data ===")
            logger.info(f"Результат: {len(images_data)} изображений, {len(matrices)} матриц")

            return {
                'images' : images_data ,
                'matrices' : matrices ,
                'errors' : dn_errors + pn_errors  # Объединяем все ошибки
            }

        except Exception as e :
            logger.error(f"Ошибка в универсальном геттере ВГХ: {e}")
            return {
                'images' : [] ,
                'matrices' : [] ,
                'errors' : [f"Системная ошибка: {str(e)}"]
            }

    def _get_images_for_dn_list(self , dn_objects , export=False) :
        """Получение изображений для списка DN"""
        try :
            logger.info(f"=== Поиск изображений по совпадению DN ===")
            logger.info(f"Количество DN для поиска изображений: {len(dn_objects)}")
            logger.info(f"DN список: {[dn.name for dn in dn_objects]}")

            from valve_data.models import DimensionTableDrawingItem

            # Получаем все связи с чертежами для этой таблицы
            all_drawing_relations = DimensionTableDrawingItem.objects.filter(
                dimension_table=self
            ).select_related('drawing').prefetch_related('allowed_dn').order_by('display_order')

            logger.info(f"Всего связей с чертежами для таблицы: {all_drawing_relations.count()}")

            images_data = []
            requested_dn_ids = {dn.id for dn in dn_objects}  # Множество ID запрошенных DN

            logger.debug(f"ID запрошенных DN: {requested_dn_ids}")

            for i , relation in enumerate(all_drawing_relations) :
                # Получаем allowed_dn для этого изображения
                allowed_dns = list(relation.allowed_dn.all())
                allowed_dn_ids = {dn.id for dn in allowed_dns}

                logger.debug(f"Изображение[{i}]: '{relation.drawing.title}'")
                logger.debug(f"Allowed DN IDs: {allowed_dn_ids}")

                # Проверяем, есть ли пересечение между allowed_dn и запрошенными dn
                has_intersection = bool(requested_dn_ids & allowed_dn_ids)

                if has_intersection :
                    # Находим конкретные DN, которые совпадают
                    matching_dns = [dn for dn in dn_objects if dn.id in allowed_dn_ids]
                    matching_dn_names = [dn.name for dn in matching_dns]

                    logger.debug(f"Совпадение найдено! Подходящие DN: {matching_dn_names}")

                    image_info = {
                        'drawing_title' : relation.drawing.title ,
                        'drawing_description' : relation.description or relation.drawing.description ,
                        'display_order' : relation.display_order ,
                        'allowed_dns' : [dn.code if export else dn.name for dn in allowed_dns] ,
                        'matching_dns' : [dn.code if export else dn.name for dn in matching_dns] ,
                        'drawing_id' : relation.drawing.id
                    }

                    if not export :
                        image_info['drawing_object'] = relation.drawing
                        image_info['relation_object'] = relation
                        image_info['allowed_dn_objects'] = allowed_dns
                        image_info['matching_dn_objects'] = matching_dns

                    images_data.append(image_info)
                    logger.info(f"Добавлено изображение: '{relation.drawing.title}' для DN: {matching_dn_names}")
                else :
                    logger.debug(f"Изображение '{relation.drawing.title}' не подходит - нет совпадений по DN")

            logger.info(f"Всего найдено изображений: {len(images_data)}")
            return images_data

        except Exception as e :
            logger.error(f"Ошибка при получении изображений для списка DN: {e}")
            return []

    def _build_matrices(self , data_queryset , dn_objects , pn_objects , export=False) :
        """Построение матриц данных с учетом переданных отсортированных DN и PN"""
        logger.info(f"=== Построение матриц ===")
        logger.info(f"Количество данных для обработки: {data_queryset.count()}")
        logger.info(f"DN объектов: {len(dn_objects)}, PN объектов: {len(pn_objects)}")
        logger.info(f"Режим export: {export}")

        # Группируем данные по PN
        data_by_pn = {}
        for data in data_queryset :
            pn_key = data.pn.code if export else data.pn.name
            if pn_key not in data_by_pn :
                data_by_pn[pn_key] = []
            data_by_pn[pn_key].append(data)

        logger.info(f"Сгруппировано по PN: {len(data_by_pn)} групп")

        matrices = []

        # Создаем списки ключей DN и PN в правильном порядке сортировки
        sorted_dn_keys = [dn.code if export else dn.name for dn in dn_objects]
        sorted_pn_keys = [pn.code if export else pn.name for pn in pn_objects]

        # Итерируемся по PN в отсортированном порядке
        for pn_key in sorted_pn_keys :
            # Пропускаем PN, для которых нет данных
            if pn_key not in data_by_pn :
                logger.debug(f"Пропускаем PN {pn_key} - нет данных")
                continue

            pn_data = data_by_pn[pn_key]
            logger.debug(f"Обработка PN: {pn_key}, количество записей: {len(pn_data)}")

            # Группируем данные по параметрам и DN
            param_dn_data = {}
            unique_params = set()

            for data in pn_data :
                param_key = data.parameter.id
                dn_key = data.dn.code if export else data.dn.name

                unique_params.add(data.parameter)

                if param_key not in param_dn_data :
                    param_dn_data[param_key] = {}

                param_dn_data[param_key][dn_key] = data.get_display_value()

            # СОРТИРУЕМ параметры по sorting_order
            sorted_params = sorted(unique_params , key=lambda x : x.sorting_order)

            # Фильтруем DN ключи - оставляем только те, для которых есть данные
            # и сохраняем порядок из sorted_dn_keys
            available_dn_keys = [dn_key for dn_key in sorted_dn_keys
                                 if any(dn_key in param_dn_data.get(param.id , {})
                                        for param in sorted_params)]

            logger.debug(f"Доступные DN ключи для PN {pn_key}: {available_dn_keys}")

            # Создаем матрицу
            matrix = []

            # Заголовок строки в зависимости от режима
            if export :
                # Для экспорта: первая строка - DN коды
                header_row = ['legend' , 'parame_name', 'parameter_variety_code' , pn_key] + available_dn_keys
            else :
                # Для обычного режима: первая строка - DN названия
                header_row = ['legend' , 'parameter_variety_name'] + available_dn_keys

            matrix.append(header_row)

            # Заполняем данные параметров
            for param in sorted_params :
                row = []

                if export :
                    # Для экспорта
                    row.extend([
                        param.legend or '' ,
                        param.name or '' ,
                        param.parameter_variety.code if param.parameter_variety else '' ,
                        pn_key
                    ])
                else :
                    # Для обычного режима
                    row.extend([
                        param.legend or '' ,
                        param.parameter_variety.name if param.parameter_variety else param.name or '' ,
                    ])

                # Добавляем значения для каждого DN (в отсортированном порядке)
                for dn_key in available_dn_keys :
                    value = param_dn_data.get(param.id , {}).get(dn_key , None)
                    row.append(value)

                matrix.append(row)

            matrices.append({
                'pn' : pn_key ,
                'matrix' : matrix
            })

        logger.info(f"Всего построено матриц: {len(matrices)}")
        return matrices
    # def _build_matrices(self , data_queryset , dn_objects , pn_objects , export=False) :
    #     """Построение матриц данных"""
    #     logger.info(f"=== Построение матриц ===")
    #     logger.info(f"Количество данных для обработки: {data_queryset.count()}")
    #     logger.info(f"Режим export: {export}")
    #
    #     # Группируем данные по PN
    #     data_by_pn = {}
    #     for data in data_queryset :
    #         pn_key = data.pn.code if export else data.pn.name
    #         if pn_key not in data_by_pn :
    #             data_by_pn[pn_key] = []
    #         data_by_pn[pn_key].append(data)
    #
    #     logger.info(f"Сгруппировано по PN: {len(data_by_pn)} групп")
    #
    #     matrices = []
    #
    #     for pn_key , pn_data in data_by_pn.items() :
    #         logger.debug(f"Обработка PN: {pn_key}, количество записей: {len(pn_data)}")
    #
    #         # Группируем данные по параметрам и DN
    #         param_dn_data = {}
    #         unique_params = set()
    #         unique_dns = set()
    #
    #         for data in pn_data :
    #             param_key = data.parameter.id
    #             dn_key = data.dn.code if export else data.dn.name
    #
    #             unique_params.add(data.parameter)
    #             unique_dns.add(dn_key)
    #
    #             if param_key not in param_dn_data :
    #                 param_dn_data[param_key] = {}
    #
    #             param_dn_data[param_key][dn_key] = data.get_display_value()
    #
    #         # СОРТИРУЕМ параметры и DN
    #         sorted_params = sorted(unique_params , key=lambda x : x.sorting_order)
    #
    #         # СОРТИРУЕМ DN по числовому значению (извлекаем число из кода)
    #         def get_dn_numeric_value(dn_code) :
    #             try :
    #                 # Извлекаем числа из строки DN (например, "50" из "DN50")
    #                 numbers = ''.join(filter(str.isdigit , str(dn_code)))
    #                 return int(numbers) if numbers else 0
    #             except (ValueError , TypeError) :
    #                 return 0
    #
    #         sorted_dns = sorted(unique_dns , key=get_dn_numeric_value)
    #
    #         # Создаем матрицу
    #         matrix = []
    #
    #         # Заголовок строки в зависимости от режима
    #         if export :
    #             # Для экспорта: первая строка - DN коды
    #             header_row = ['legend' , 'parameter_variety_code' , pn_key] + sorted_dns
    #         else :
    #             # Для обычного режима: первая строка - DN названия
    #             header_row = ['legend' , 'parameter_variety_name'] + sorted_dns
    #
    #         matrix.append(header_row)
    #
    #         # Заполняем данные параметров
    #         for param in sorted_params :
    #             row = []
    #
    #             if export :
    #                 # Для экспорта - УБРАЛ text_value, которого нет в модели
    #                 row.extend([
    #                     param.legend or '' ,
    #                     param.name or '' ,
    #                     param.parameter_variety.code if param.parameter_variety else '' ,
    #                     pn_key
    #                 ])
    #             else :
    #                 # Для обычного режима
    #                 row.extend([
    #                     param.legend or '' ,
    #                     param.parameter_variety.name if param.parameter_variety else param.name or '',
    #                 ])
    #
    #             # Добавляем значения для каждого DN (в отсортированном порядке)
    #             for dn in sorted_dns :
    #                 value = param_dn_data.get(param.id , {}).get(dn , None)
    #                 row.append(value)
    #
    #             matrix.append(row)
    #
    #         matrices.append({
    #             'pn' : pn_key ,
    #             'matrix' : matrix
    #         })
    #
    #     logger.info(f"Всего построено матриц: {len(matrices)}")
    #     return matrices

    # Удаляем старые геттеры и оставляем только универсальный
    def get_complete_dimension_data(self , dn_value , pn_value , include_objects=False) :
        """
        Комплексный метод для получения всех данных (параметры + изображения)
        Использует универсальный геттер
        """
        result = self.get_dimension_data(
            dn_list=[dn_value] if dn_value else None ,
            pn_list=[pn_value] if pn_value else None ,
            export=False
        )

        # Адаптируем результат под старый формат
        table_name = getattr(self , 'name' , 'Неизвестная таблица')
        table_code = getattr(self , 'code' , 'Неизвестный код')

        # Преобразуем матрицы в старый формат параметров
        parameters = None
        if result['matrices'] :
            # Берем первую матрицу (для запрошенного PN)
            matrix_data = result['matrices'][0]['matrix']
            if len(matrix_data) > 1 :  # Есть данные кроме заголовка
                parameters = []
                for row in matrix_data[1 :] :  # Пропускаем заголовок
                    param_info = {
                        'legend' : row[0] ,
                        'parameter_variety' : row[1] ,
                        'value' : row[3] if len(row) > 3 else None  # Первое значение DN
                    }
                    parameters.append(param_info)

        return {
            'parameters' : parameters ,
            'images' : result['images'] ,
            'message' : "Данные получены" if parameters or result['images'] else "Данные не найдены" ,
            'alternatives' : None ,  # Упрощаем, убираем альтернативы
            'dn' : dn_value ,
            'pn' : pn_value ,
            'table_name' : table_name ,
            'table_code' : table_code
        }

    def duplicate_table(self, new_name=None, new_code=None):
        """
        Создание копии таблицы ВГХ со всеми связанными данными

        Args:
            new_name: новое название таблицы (опционально)
            new_code: новый код таблицы (опционально)

        Returns:
            ValveDimensionTable: новая таблица-копия
        """
        try:
            # Генерируем названия если не указаны
            if not new_name:
                new_name = f"{self.name} (Копия)"
            if not new_code:
                new_code = f"{self.code}_copy"

            # Создаем основную таблицу
            new_table = ValveDimensionTable.objects.create(
                name=new_name,
                code=new_code,
                valve_brand=self.valve_brand,
                valve_variety=self.valve_variety,
                description=self.description
            )

            # Копируем параметры
            param_mapping=[]
            for param in self.table_parameters.all():
                new_param = DimensionTableParameter.objects.create(
                    dimension_table=new_table,
                    name=param.name,
                    legend=param.legend,
                    parameter_variety=param.parameter_variety,
                    sorting_order=param.sorting_order
                )

                # Создаем mapping старых параметров к новым для копирования данных
                param_mapping[param.id] = new_param.id

            # Копируем связи с чертежами
            for drawing_relation in self.drawing_relations.all():
                new_relation = DimensionTableDrawingItem.objects.create(
                    dimension_table=new_table,
                    drawing=drawing_relation.drawing,
                    description=drawing_relation.description,
                    display_order=drawing_relation.display_order
                )
                new_relation.allowed_dn.set(drawing_relation.allowed_dn.all())

            # Копируем данные ВГХ
            self._copy_dimension_data(new_table, param_mapping)

            logger.info(f"Успешно создана копия таблицы: {self.name} -> {new_table.name}")
            return new_table

        except Exception as e:
            logger.error(f"Ошибка при копировании таблицы {self.name}: {e}")
            raise

    def _copy_dimension_data(self, new_table, param_mapping):
        """
        Копирование данных ВГХ в новую таблицу

        Args:
            new_table: новая таблица ВГХ
            param_mapping: словарь соответствия старых и новых ID параметров
        """
        from .valve_dimension_data import ValveDimensionData

        dimension_data = ValveDimensionData.objects.filter(
            parameter__dimension_table=self
        ).select_related('parameter')

        new_data_objects = []
        for data in dimension_data:
            new_param_id = param_mapping.get(data.parameter.id)
            if new_param_id:
                new_data_objects.append(
                    ValveDimensionData(
                        dn=data.dn,
                        pn=data.pn,
                        parameter_id=new_param_id,
                        value=data.value,
                        text_value=data.text_value
                    )
                )

        # Массовое создание для оптимизации
        if new_data_objects:
            ValveDimensionData.objects.bulk_create(new_data_objects)
            logger.info(f"Скопировано {len(new_data_objects)} записей данных ВГХ")