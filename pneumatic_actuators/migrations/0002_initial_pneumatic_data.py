# pneumatic_actuators/migrations/0002_initial_data.py
from django.db import migrations


def create_initial_pneumatic_data(apps , schema_editor) :
    # Давления питания
    PneumaticAirSupplyPressure = apps.get_model('pneumatic_actuators' , 'PneumaticAirSupplyPressure')
    pressure_data = [
        {'name' : 'SPRING' , 'code' : 'spring' , 'pressure_bar' : 0.0 , 'sorting_order' : 1} ,
        {'name' : '0.5' , 'code' : '0.5' , 'pressure_bar' : 0.5 , 'sorting_order' : 5} ,
        {'name' : '1' , 'code' : '1' , 'pressure_bar' : 1.0 , 'sorting_order' : 10} ,
        {'name' : '1.5' , 'code' : '1.5' , 'pressure_bar' : 1.5 , 'sorting_order' : 15} ,
        {'name' : '2' , 'code' : '2' , 'pressure_bar' : 2.0 , 'sorting_order' : 20} ,
        {'name' : '2.5' , 'code' : '2.5' , 'pressure_bar' : 2.5 , 'sorting_order' : 25} ,
        {'name' : '3' , 'code' : '3' , 'pressure_bar' : 3.0 , 'sorting_order' : 30} ,
        {'name' : '3.5' , 'code' : '3.5' , 'pressure_bar' : 3.5 , 'sorting_order' : 35} ,
        {'name' : '4' , 'code' : '4' , 'pressure_bar' : 4.0 , 'sorting_order' : 40} ,
        {'name' : '4.5' , 'code' : '4.5' , 'pressure_bar' : 4.5 , 'sorting_order' : 45} ,
        {'name' : '5' , 'code' : '5' , 'pressure_bar' : 5.0 , 'sorting_order' : 50} ,
        {'name' : '5.5' , 'code' : '5.5' , 'pressure_bar' : 5.5 , 'sorting_order' : 55} ,
        {'name' : '6' , 'code' : '6' , 'pressure_bar' : 6.0 , 'sorting_order' : 60} ,
        {'name' : '7' , 'code' : '7' , 'pressure_bar' : 7.0 , 'sorting_order' : 70} ,
        {'name' : '8' , 'code' : '8' , 'pressure_bar' : 8.0 , 'sorting_order' : 80} ,
        {'name' : '10' , 'code' : '10' , 'pressure_bar' : 10.0 , 'sorting_order' : 100} ,
    ]

    for data in pressure_data :
        PneumaticAirSupplyPressure.objects.get_or_create(
            code=data['code'] ,
            defaults={
                'name' : data['name'] ,
                'pressure_bar' : data['pressure_bar'] ,
                'sorting_order' : data['sorting_order'] ,
                'description' : f"Давление питания {data['name']} бар"
            }
        )

    # Количество пружин
    PneumaticActuatorSpringsQty = apps.get_model('pneumatic_actuators' , 'PneumaticActuatorSpringsQty')
    springs_qty_data = [
        {'name' : 'DA' , 'code' : 'DA' , 'sorting_order' : 1} ,
        {'name' : "05 пружин" , 'code' : '05' , 'sorting_order' : 5} ,
        {'name' : "06 пружин" , 'code' : '06' , 'sorting_order' : 6} ,
        {'name' : "07 пружин" , 'code' : '07' , 'sorting_order' : 7} ,
        {'name' : "08 пружин" , 'code' : '08' , 'sorting_order' : 8} ,
        {'name' : "09 пружин" , 'code' : '09' , 'sorting_order' : 9} ,
        {'name' : "10 пружин" , 'code' : '10' , 'sorting_order' : 10} ,
        {'name' : "11 пружин" , 'code' : '11' , 'sorting_order' : 11} ,
        {'name' : "12 пружин" , 'code' : '12' , 'sorting_order' : 12} ,
    ]

    for data in springs_qty_data :
        springs_data = {
            'name' : data['name'] ,
            'code' : data['code'] ,
            'description' : data['name'] ,
            'sorting_order' : data['sorting_order'] ,
            'is_active' : True
        }
        PneumaticActuatorSpringsQty.objects.get_or_create(
            code=data['code'] ,
            defaults=springs_data
        )

    # Разновидности пневмоприводов
    PneumaticActuatorVariety = apps.get_model('pneumatic_actuators' , 'PneumaticActuatorVariety')
    varieties_data = [
        {
            'name' : 'DA' ,
            'code' : 'DA' ,
            'description' : 'Пневмопривод двойного действия' ,
            'sorting_order' : 1 ,
            'is_active' : True
        } ,
        {
            'name' : 'SR' ,
            'code' : 'SR' ,
            'description' : 'Пневмопривод с возвратными пружинами' ,
            'sorting_order' : 2 ,
            'is_active' : True
        }
    ]

    for data in varieties_data :
        PneumaticActuatorVariety.objects.get_or_create(
            code=data['code'] ,
            defaults=data
        )

    # Разновидности конструкций
    PneumaticActuatorConstructionVariety = apps.get_model('pneumatic_actuators' ,
                                                          'PneumaticActuatorConstructionVariety')
    construction_varieties_data = [
        {
            'name' : 'Шестерня-рейка' ,
            'code' : 'RP' ,
            'description' : 'Конструкция шестерня-рейка (rack & pinion)' ,
            'sorting_order' : 1 ,
            'is_active' : True
        } ,
        {
            'name' : 'Кулисный' ,
            'code' : 'SY' ,
            'description' : 'Конструкция с кулисой (skotch-yoke)' ,
            'sorting_order' : 2 ,
            'is_active' : True
        }
    ]

    for data in construction_varieties_data :
        PneumaticActuatorConstructionVariety.objects.get_or_create(
            code=data['code'] ,
            defaults=data
        )


def reverse_initial_data(apps , schema_editor) :
    """Удаление начальных данных при откате миграции"""
    PneumaticAirSupplyPressure = apps.get_model('pneumatic_actuators' , 'PneumaticAirSupplyPressure')
    PneumaticActuatorSpringsQty = apps.get_model('pneumatic_actuators' , 'PneumaticActuatorSpringsQty')
    PneumaticActuatorVariety = apps.get_model('pneumatic_actuators' , 'PneumaticActuatorVariety')
    PneumaticActuatorConstructionVariety = apps.get_model('pneumatic_actuators' ,
                                                          'PneumaticActuatorConstructionVariety')

    # Удаляем созданные данные
    PneumaticAirSupplyPressure.objects.all().delete()
    PneumaticActuatorSpringsQty.objects.all().delete()
    PneumaticActuatorVariety.objects.all().delete()
    PneumaticActuatorConstructionVariety.objects.all().delete()


class Migration(migrations.Migration) :
    dependencies = [
        ('pneumatic_actuators' , '0001_initial') ,  # Зависит от начальной миграции
    ]

    operations = [
        migrations.RunPython(create_initial_pneumatic_data , reverse_initial_data) ,
    ]