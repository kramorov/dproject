   # SKU, MBOM, Assembly — структура и связи 
                                             
   > Проект: 2026-07-29. Концепция.          
   >    ## Уровни                                                              
                                                                          
   Уровень 1: Nomenclature       Атомарный SKU (артикул на складе)        
   Уровень 2: EquipmentType      Классификатор + правила комплектации     
   Уровень 3: MBOM               Конкретный подбор (результат AI)         
   Уровень 4: MBOMLabel          Имя сборки (общее или для партнёра)      
   Уровень 5: Document/DocumentLine  КП, счёт — ссылаются на SKU или MBOM 
                                                                          
   ---                                                                    
                                                                          
   ## Модели                                                              
                                                                          
   ### Nomenclature (существует)                                          
                                                                          
   class Nomenclature(models.Model):                                      
       """Атомарный SKU. Никаких сборок, никакого self-FK."""             
       code = CharField(unique=True)                                      
       name = CharField                                                   
       equipment_type = FK → EquipmentType                                
       price = DecimalField                                               
       is_active = BooleanField                                           
                                                                          
   ### EquipmentType (core.models — существует, расширяется)              
                                                                          
   class EquipmentType(BaseAbstractModel):                                
       code = CharField(unique=True)                                      
       name = CharField                                                   
       parent = FK → self               # иерархия классификатора         
       level = IntegerField                                               
                                                                          
       # AI-поля                                                          
       param_semantics = JSONField       # семантика сравнения            
       filter_endpoint = CharField       # API для filter-фазы            
                                                                          
       # Правила комплектации (концепция)                                 
       required_children = M2M('self')   # БКВ → cable_gland (всегда)     
       optional_children = M2M('self')   # actuator → solenoid, positioner  
       publish_on_site = BooleanField    # показывать в «Готовых решениях»  
                                                                            
   Сборка "Кран с ПП" — это EquipmentType с CompositionGroup.               
                                                                            
   ### CompositionRule (новая)                                              
                                                                            
   class CompositionRule(models.Model):                                     
       equipment_type = FK → EquipmentType                                  
       child_type = FK → EquipmentType                                      
       exclusive_group = CharField       # XORM-группа                      
       is_default = BooleanField                                            
       is_required = BooleanField                                           
                                                                            
   ### MBOM (новая)                                                         
                                                                            
   class MBOM(models.Model):                                                
       equipment_type = FK → EquipmentType  # тип сборки                    
       label = CharField                    # 'Кран LD-50-40 + ABRA-DA-150' 
       project = FK → Project                                               
       conversation = FK → AIConversation                                   
       is_published = BooleanField                                          
                                                                            
   class MBOMLine(models.Model):                                            
       mbom = FK → MBOM                                                     
       parent = FK → self (null=root)                                       
       sku = FK → Nomenclature              # конкретный подобранный SKU    
       quantity = FloatField                                                
       unit = CharField                                                     
       price_override = DecimalField(null=True)                             
       level = IntegerField                                                 
       path = CharField                     # '1/1/2'                       
                                                                            
   ### MBOMLabel (новая)                                                    
                                                                            
   class MBOMLabel(models.Model):                                           
           mbom = FK → MBOM                                                
        customer = FK → ProjectCustomer(null=True)                      
        label = CharField                                               
                                                                        
    ### Document / DocumentLine (новая)                                 
                                                                        
    class Document(models.Model):                                       
        type = CharField  # 'quotation', 'invoice', 'spec'              
        project = FK → Project                                          
        number = CharField                                              
        date = DateField                                                
                                                                        
    class DocumentLine(models.Model):                                   
        document = FK → Document                                        
        position = IntegerField                                         
        quantity = FloatField                                           
        unit = CharField                                                
        nomenclature = FK → Nomenclature(null=True)   # атомарный SKU   
        mbom = FK → MBOM(null=True)                  # сборка           
        price_override = DecimalField(null=True)                        
        # Констрейнт: ровно одно из двух заполнено                      
                                                                        
    ---                                                                 
                                                                        
    ## ER-диаграмма                                                     
                          ·                                             
    EquipmentType ──< CompositionRule >── EquipmentType (child_type)    
         │                                                              
         ├──< MBOM ──< MBOMLine >── Nomenclature                        
         │              └──< MBOMLabel >── ProjectCustomer              
         │                                                              
         ├──< Nomenclature (атомарные SKU)                              
         │                                                              
    Document ──< DocumentLine                                           
                    ├── Nomenclature (FK, nullable)                     
                    └── MBOM (FK, nullable)                             
                                                                                       
    ---                                                                                
                                                                                       
    ## Пример: сборка как EquipmentType                                                
                                                                                       
    EquipmentType: code='ball-valve-with-pa'                                           
    CompositionGroup:                                                                  
      required: [ball-valve, pneumatic-actuator, pneumatic-fitting]                    
      optional:                                                                        
        Управление (XOR): solenoid(default) | positioner                               
        Контроль (any): bkv, filter-regulator                                          
                                                                                       
    ## Пример: конкретный MBOM                                                         
                                                                                       
    MBOM #42: equipment_type = 'ball-valve-with-pa'                                    
    MBOMLine (корень): sku = #142 (Кран LD Ду50), qty=1                                
      ├── MBOMLine: sku = #301 (ABRA-DA-150), qty=1                                    
      │     ├── MBOMLine: sku = #310 (Фитинг G1/4), qty=1                              
      │     └── MBOMLine: sku = #88 (Соленоид 24V), qty=1                              
      └── MBOMLine: sku = #15 (БКВ Ex d), qty=1                                        
                                                                                       
    ## Пример: КП со сборкой                                                           
                                                                                       
    DocumentLine #1: mbom = MBOM #42        ← сборка (раскрывается)                    
    DocumentLine #2: nomenclature = SKU #55 ← атомарный SKU                            
    DocumentLine #3: mbom = MBOM #17        ← другая сборка                            
                                                                                       
    ---                                                                                
                                                                                       
    ## Правила                                                                         
                                                                                       
    1. Номенклатура — только атомарные SKU. Никаких сборок.                            
    2. Сборка — EquipmentType с CompositionGroup.                                      
    3. MBOM — конкретный подбор, ссылается на тип сборки.                              
    4. Документ — плоский список. Строка = SKU ИЛИ MBOM.                               
    5. Dedup — два проекта с одинаковым подбором = два MBOM с одним equipment_type_id. 
