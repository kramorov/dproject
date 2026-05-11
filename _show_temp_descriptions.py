f=open('solenoid_valves/models.py','r',encoding='utf-8')
for i,l in enumerate(f,1):
    if 258 <= i <= 272:
        print(f"{i}:{l}",end='')
f.close()
