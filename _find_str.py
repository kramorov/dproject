f=open('solenoid_valves/models.py','r',encoding='utf-8')
for i,l in enumerate(f,1):
    if 'def __str__' in l and 260 <= i <= 300:
        print(f"{i}:{l}",end='')
        break
f.close()
