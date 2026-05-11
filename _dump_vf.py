f=open('solenoid_valves/models.py','r',encoding='utf-8')
lines=f.readlines()
f.close()
open('_valve_func.txt','w',encoding='utf-8').writelines(lines[272:285])
