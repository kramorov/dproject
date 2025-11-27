from django.contrib import admin

from django.utils.html import format_html

from pneumatic_actuators.models.pa_actuator_selected import PneumaticActuatorSelected
from pneumatic_actuators.models.pa_options import PneumaticSafetyPositionOption , PneumaticSpringsQtyOption , \
    PneumaticTemperatureOption , PneumaticIpOption , PneumaticExdOption , PneumaticBodyCoatingOption


@admin.register(PneumaticActuatorSelected)
class PneumaticActuatorSelectedAdmin(admin.ModelAdmin) :
    list_display = [
        'name' , 'code' , 'selected_model_display' ,
        'safety_position_display' , 'springs_qty_display' ,
        'temperature_display' , 'ip_display' , 'exd_display' , 'body_coating_display' ,
        'sorting_order' , 'is_active'
    ]
    list_filter = [
        'is_active' , 'selected_model' ,
        'selected_safety_position__safety_position' ,
        'selected_springs_qty__springs_qty' ,
        'selected_temperature' ,
        'selected_ip__ip_option' ,
        'selected_exd__exd_option' ,
        'selected_body_coating__body_coating_option'
    ]
    search_fields = ['name' , 'code' , 'description']
    # autocomplete_fields = ['selected_model' , 'selected_safety_position' , 'selected_springs_qty']
    fieldsets = (
        ('Основная информация' , {
            'fields' : (
                'selected_model' ,
                'is_active' ,
                'sorting_order'
            )
        }) ,
        ('Опции привода' , {
            'fields' : (
                'selected_safety_position' ,
                'selected_springs_qty' ,
            )
        }) ,
        ('Дополнительные опции' , {
            'fields' : (
                'selected_temperature' ,
                'selected_ip' ,
                'selected_exd' ,
                'selected_body_coating' ,
            ) ,
            'classes' : ('collapse' ,)
        }) ,
        ('Автоматически генерируемые поля' , {
            'fields' : (
                'name' ,
                'code' ,
                'description' ,
            ) ,
            'classes' : ('collapse' ,)
        })
    )

    class Media :
        js = ('admin/js/pneumatic_admin.js' ,)  # новый файл
        # js = ('admin/js/pneumatic_actuator_selected.js' ,)

    def save_model(self , request , obj , form , change) :
        """Логирование при сохранении"""
        print(f"🎯 === ADMIN SAVE DEBUG ===")
        print(f"🎯 obj_id: {obj.id if obj.id else 'NEW'}")
        print(f"🎯 change: {change}")

        # Принудительно выводим ВСЕ выбранные опции
        print(f"🎯 selected_model: {obj.selected_model.id if obj.selected_model else 'None'}")
        print(
            f"🎯 selected_safety_position: {obj.selected_safety_position.id if obj.selected_safety_position else 'None'}")
        print(f"🎯 selected_springs_qty: {obj.selected_springs_qty.id if obj.selected_springs_qty else 'None'}")
        print(f"🎯 selected_temperature: {obj.selected_temperature.id if obj.selected_temperature else 'None'}")
        print(f"🎯 selected_ip: {obj.selected_ip.id if obj.selected_ip else 'None'}")
        print(f"🎯 selected_exd: {obj.selected_exd.id if obj.selected_exd else 'None'}")
        print(f"🎯 selected_body_coating: {obj.selected_body_coating.id if obj.selected_body_coating else 'None'}")

        # Проверяем принадлежность опций к модели
        if obj.selected_model and obj.selected_safety_position :
            is_valid_safety = PneumaticSafetyPositionOption.objects.filter(
                model_line_item=obj.selected_model ,
                id=obj.selected_safety_position.id
            ).exists()
            print(f"🎯 safety_position valid: {is_valid_safety}")

        if obj.selected_model and obj.selected_springs_qty :
            is_valid_springs = PneumaticSpringsQtyOption.objects.filter(
                model_line_item=obj.selected_model ,
                id=obj.selected_springs_qty.id
            ).exists()
            print(f"🎯 springs_qty valid: {is_valid_springs}")

        print(f"🎯 === END ADMIN SAVE DEBUG ===")

        super().save_model(request , obj , form , change)

    def get_form(self , request , obj=None , **kwargs) :
        form = super().get_form(request , obj , **kwargs)
        if obj and obj.selected_model :
            is_da = (obj.selected_model.pneumatic_actuator_variety and
                     obj.selected_model.pneumatic_actuator_variety.code == 'DA')
            if is_da :
                form.base_fields['selected_safety_position'].required = False
        return form


    def get_queryset(self , request) :
        return super().get_queryset(request).select_related(
            'selected_model' ,
            'selected_safety_position__safety_position' ,
            'selected_springs_qty__springs_qty' ,
            'selected_temperature__model_line' ,  # ЕСЛИ НУЖНА СВЯЗЬ С MODEL_LINE
            'selected_ip__model_line' ,
            'selected_exd__model_line' ,
            'selected_body_coating__model_line'
        )

    def formfield_for_foreignkey(self , db_field , request , **kwargs) :
        """Фильтрация опций в зависимости от выбранной модели"""
        import logging
        logger = logging.getLogger(__name__)
        from pneumatic_actuators.models.pa_model_line import PneumaticActuatorModelLineItem
        print(f"🔧 === FORM FIELD DEBUG: {db_field.name} ===")
        print(f"🔧 obj_id: {request.resolver_match.kwargs.get('object_id')}")
        print(f"🔧 method: {request.method}")

        if db_field.name in [
            'selected_safety_position' , 'selected_springs_qty' ,
            'selected_temperature' , 'selected_ip' , 'selected_exd' , 'selected_body_coating'
        ] :
            obj_id = request.resolver_match.kwargs.get('object_id')
            logger.info(f"=== ADMIN DEBUG: db_field={db_field.name}, obj_id={obj_id}, method={request.method}")

            if obj_id :
                try :
                    obj = self.get_queryset(request).get(pk=obj_id)
                    logger.info(f"=== ADMIN DEBUG: Found object, selected_model={obj.selected_model}")

                    if obj.selected_model :
                        if db_field.name == 'selected_safety_position' :
                            base_qs = PneumaticSafetyPositionOption.objects.filter(
                                model_line_item=obj.selected_model ,
                                is_active=True
                            )
                            logger.info(f"=== ADMIN DEBUG: Safety base options count: {base_qs.count()}")

                            # Добавляем выбранную опцию
                            if obj.selected_safety_position :
                                selected_qs = PneumaticSafetyPositionOption.objects.filter(
                                    id=obj.selected_safety_position.id
                                )
                                base_qs = base_qs | selected_qs
                                logger.info(
                                    f"=== ADMIN DEBUG: Added selected safety option: {obj.selected_safety_position.id}")

                            kwargs["queryset"] = base_qs.distinct()
                            logger.info(f"=== ADMIN DEBUG: Final safety options count: {kwargs['queryset'].count()}")

                        elif db_field.name == 'selected_springs_qty' :
                            base_qs = PneumaticSpringsQtyOption.objects.filter(
                                model_line_item=obj.selected_model ,
                                is_active=True
                            )
                            logger.info(f"=== ADMIN DEBUG: Springs base options count: {base_qs.count()}")

                            if obj.selected_springs_qty :
                                selected_qs = PneumaticSpringsQtyOption.objects.filter(
                                    id=obj.selected_springs_qty.id
                                )
                                base_qs = base_qs | selected_qs
                                logger.info(
                                    f"=== ADMIN DEBUG: Added selected springs option: {obj.selected_springs_qty.id}")

                            kwargs["queryset"] = base_qs.distinct()
                            logger.info(f"=== ADMIN DEBUG: Final springs options count: {kwargs['queryset'].count()}")

                        elif db_field.name == 'selected_temperature' and obj.selected_model.model_line :
                            base_qs = PneumaticTemperatureOption.objects.filter(
                                model_line=obj.selected_model.model_line ,
                                is_active=True
                            )
                            logger.info(f"=== ADMIN DEBUG: Temperature base options count: {base_qs.count()}")

                            if obj.selected_temperature :
                                selected_qs = PneumaticTemperatureOption.objects.filter(
                                    id=obj.selected_temperature.id
                                )
                                base_qs = base_qs | selected_qs
                                logger.info(
                                    f"=== ADMIN DEBUG: Added selected temperature option: {obj.selected_temperature.id}")

                            kwargs["queryset"] = base_qs.distinct()

                        elif db_field.name == 'selected_ip' and obj.selected_model.model_line :
                            base_qs = PneumaticIpOption.objects.filter(
                                model_line=obj.selected_model.model_line ,
                                is_active=True
                            )
                            logger.info(f"=== ADMIN DEBUG: IP base options count: {base_qs.count()}")

                            if obj.selected_ip :
                                selected_qs = PneumaticIpOption.objects.filter(
                                    id=obj.selected_ip.id
                                )
                                base_qs = base_qs | selected_qs
                                logger.info(f"=== ADMIN DEBUG: Added selected IP option: {obj.selected_ip.id}")

                            kwargs["queryset"] = base_qs.distinct()

                        elif db_field.name == 'selected_exd' and obj.selected_model.model_line :
                            base_qs = PneumaticExdOption.objects.filter(
                                model_line=obj.selected_model.model_line ,
                                is_active=True
                            )
                            logger.info(f"=== ADMIN DEBUG: Exd base options count: {base_qs.count()}")

                            if obj.selected_exd :
                                selected_qs = PneumaticExdOption.objects.filter(
                                    id=obj.selected_exd.id
                                )
                                base_qs = base_qs | selected_qs
                                logger.info(f"=== ADMIN DEBUG: Added selected Exd option: {obj.selected_exd.id}")

                            kwargs["queryset"] = base_qs.distinct()

                        elif db_field.name == 'selected_body_coating' and obj.selected_model.model_line :
                            base_qs = PneumaticBodyCoatingOption.objects.filter(
                                model_line=obj.selected_model.model_line ,
                                is_active=True
                            )
                            logger.info(f"=== ADMIN DEBUG: Coating base options count: {base_qs.count()}")

                            if obj.selected_body_coating :
                                selected_qs = PneumaticBodyCoatingOption.objects.filter(
                                    id=obj.selected_body_coating.id
                                )
                                base_qs = base_qs | selected_qs
                                logger.info(
                                    f"=== ADMIN DEBUG: Added selected coating option: {obj.selected_body_coating.id}")

                            kwargs["queryset"] = base_qs.distinct()

                except PneumaticActuatorSelected.DoesNotExist :
                    logger.error("=== ADMIN DEBUG: Object does not exist")
                except Exception as e :
                    logger.error(f"=== ADMIN DEBUG: Error in formfield_for_foreignkey: {e}")
            else :
                # Для новых объектов - обычная фильтрация
                selected_model_id = request.POST.get('selected_model')
                if selected_model_id :
                    try :

                        model = PneumaticActuatorModelLineItem.objects.get(id=selected_model_id)
                        logger.info(f"=== ADMIN DEBUG: New object, selected_model_id={selected_model_id}")

                        if db_field.name == 'selected_safety_position' :
                            kwargs["queryset"] = PneumaticSafetyPositionOption.objects.filter(
                                model_line_item=model ,
                                is_active=True
                            )
                        elif db_field.name == 'selected_springs_qty' :
                            kwargs["queryset"] = PneumaticSpringsQtyOption.objects.filter(
                                model_line_item=model ,
                                is_active=True
                            )
                        elif db_field.name == 'selected_temperature' and model.model_line :
                            kwargs["queryset"] = PneumaticTemperatureOption.objects.filter(
                                model_line=model.model_line ,
                                is_active=True
                            )
                        elif db_field.name == 'selected_ip' and model.model_line :
                            kwargs["queryset"] = PneumaticIpOption.objects.filter(
                                model_line=model.model_line ,
                                is_active=True
                            )
                        elif db_field.name == 'selected_exd' and model.model_line :
                            kwargs["queryset"] = PneumaticExdOption.objects.filter(
                                model_line=model.model_line ,
                                is_active=True
                            )
                        elif db_field.name == 'selected_body_coating' and model.model_line :
                            kwargs["queryset"] = PneumaticBodyCoatingOption.objects.filter(
                                model_line=model.model_line ,
                                is_active=True
                            )

                    except PneumaticActuatorModelLineItem.DoesNotExist :
                        logger.error(f"=== ADMIN DEBUG: Model not found for id={selected_model_id}")
        print(f"🔧 Final queryset count: {kwargs.get('queryset').count() if kwargs.get('queryset') else 'NOT SET'}")
        print(f"🔧 === END FORM FIELD DEBUG ===")
        return super().formfield_for_foreignkey(db_field , request , **kwargs)