# params/migrations/0022_create_initial_pneumatic_pressure_data.py
from django.db import migrations


def create_initial_pneumatic_pressure_data(apps , schema_editor) :
    PneumaticAirSupplyPressure = apps.get_model('params' , 'PneumaticAirSupplyPressure')

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
                'description' : f"Давление питания {data['name']} бар" ,
                'is_active' : True
            }
        )


def reverse_create_initial_pneumatic_pressure_data(apps , schema_editor) :
    PneumaticAirSupplyPressure = apps.get_model('params' , 'PneumaticAirSupplyPressure')
    codes_to_delete = ['spring' , '0.5' , '1' , '1.5' , '2' , '2.5' , '3' , '3.5' , '4' , '4.5' , '5' , '5.5' , '6' ,
                       '7' , '8' , '10']
    PneumaticAirSupplyPressure.objects.filter(code__in=codes_to_delete).delete()


class Migration(migrations.Migration) :
    dependencies = [
        ('params' , '0021_pneumaticairsupplypressure_delete_temperaturerange') ,
    ]

    operations = [
        migrations.RunPython(
            create_initial_pneumatic_pressure_data ,
            reverse_create_initial_pneumatic_pressure_data
        ) ,
    ]