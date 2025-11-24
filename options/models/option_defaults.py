# # options/services/option_defaults.py
# class OptionDefaultsService :
#     """Сервис для управления опциями по умолчанию"""
#
#     @staticmethod
#     def ensure_default_exists(option_model_class , parent_obj) :
#         """Гарантировать наличие дефолтной опции"""
#         parent_field = option_model_class._get_parent_field_name()
#
#         # Проверяем, есть ли уже дефолтная опция
#         if option_model_class.objects.filter(
#                 **{parent_field : parent_obj , 'is_default' : True , 'is_active' : True}).exists() :
#             return
#
#         # Если нет опций вообще - создаем дефолтную
#         if not option_model_class.objects.filter(**{parent_field : parent_obj , 'is_active' : True}).exists() :
#             option_model_class.create_default_option(parent_obj)
#             return
#
#         # Если есть опции, но нет дефолтной - делаем первую дефолтной
#         first_option = option_model_class.objects.filter(**{parent_field : parent_obj , 'is_active' : True}).first()
#         if first_option :
#             first_option.is_default = True
#             first_option.save()