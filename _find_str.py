f=open('solenoid_valves/models.py','r',encoding='utf-8')
for i,l in enumerate(f,1):
    if 'def __str__' in l and i>800:
        print(f"{i}:{l}",end='')
f.close()
