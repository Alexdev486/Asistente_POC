-- Additional seed data: more FAQs, diagnostic trees, and historical cases
-- Covers new symptom categories: brakes, suspension, cooling, electrical, battery, ignition
-- All inserts use ON CONFLICT to be safely re-runnable.

-- ── Additional FAQs for AK550 ────────────────────────────────────────
INSERT INTO faqs (model, category, question, answer, usage_count, active)
VALUES
    ('AK550', 'Frenos', 'El freno delantero vibra o pulsa al frenar fuerte',
     'En esta POC sugiere discos de freno alabeados por sobrecalentamiento o pastillas desgastadas irregularmente. Revisar estado de discos y pastillas.',
     0, TRUE),
    ('AK550', 'Frenos', 'Al frenar se escucha un chirrido agudo',
     'En esta POC indica pastillas gastadas (aviso de testigo de desgaste) o discos con superficie irregular. Verificar espesor de pastillas.',
     0, TRUE),
    ('AK550', 'Suspension', 'La horquilla delantera pierde aceite',
     'En esta POC se asocia a retenes de horquilla desgastados o barra rayada. Revision inmediata recomendada.',
     0, TRUE),
    ('AK550', 'Suspension', 'La moto se hunde al frenar o en curvas',
     'En esta POC indica precarga de suspension mal ajustada o amortiguador trasero desgastado. Reglar precarga o revisar amortiguador.',
     0, TRUE),
    ('AK550', 'Refrigeracion', 'El motor se sobrecalienta en ciudad',
     'En esta POC sugiere nivel bajo de liquido refrigerante, termostato atascado o ventilador defectuoso. Revisar nivel y funcionamiento del ventilador.',
     0, TRUE),
    ('AK550', 'Refrigeracion', 'El ventilador no se enciende al calentar el motor',
     'En esta POC causas posibles: fusible quemado, sensor de temperatura del refrigerante defectuoso, o motor del ventilador danado.',
     0, TRUE),
    ('AK550', 'Electrico', 'El cuadro de instrumentos parpadea intermitentemente',
     'En esta POC sugiere conexion suelta en el mazo principal, masa de bateria oxidada, o regulador de voltaje defectuoso.',
     0, TRUE),
    ('AK550', 'Bateria', 'La bateria se descarga si la moto para mas de una semana',
     'En esta POC indica consumo parasitic o bateria sulfatada. Medir corriente de reposo (< 5mA) o cambiar bateria.',
     0, TRUE),
    ('AK550', 'Bateria', 'Arranque lento y las luces se atenuan al arrancar',
     'En esta POC sugiere bateria debil (menos de 12.4V en reposo) o bornes sucios/oxidados. Limpiar bornes y cargar bateria.',
     0, TRUE),
    ('AK550', 'General', 'Se ha encendido el testigo de presion de aceite',
     'En esta POC detener inmediatamente. Puede ser nivel bajo de aceite, bomba de aceite defectuosa o filtro obstruido.',
     0, TRUE)
ON CONFLICT DO NOTHING;

-- ── Additional FAQs for Xciting 400 ──────────────────────────────────
INSERT INTO faqs (model, category, question, answer, usage_count, active)
VALUES
    ('Xciting 400', 'Frenos', 'La palanca de freno delantero se siente esponjosa',
     'En esta POC indica aire en el circuito hidraulico o nivel bajo de liquido de frenos. Sangrar frenos y revisar nivel.',
     0, TRUE),
    ('Xciting 400', 'Frenos', 'El freno trasero no frena igual que antes',
     'En esta POC sugiere pastillas traseras desgastadas o tambor de freno con desgaste irregular.',
     0, TRUE),
    ('Xciting 400', 'Suspension', 'Golpeteo en la direccion al pasar badenes',
     'En esta POC indica rodamiento de direccion desgastado o apriete incorrecto. Revisar y ajustar juego de direccion.',
     0, TRUE),
    ('Xciting 400', 'Suspension', 'La parte trasera rebota varias veces tras un bache',
     'En esta POC sugiere amortiguador trasero sin presion de gas o desgastado. Revisar posible cambio.',
     0, TRUE),
    ('Xciting 400', 'Refrigeracion', 'Se pierde liquido refrigerante sin marcar perdidas visibles',
     'En esta POC posible junta de culata dañada o microfisura en radiador. Revisar con prueba de presion.',
     0, TRUE),
    ('Xciting 400', 'Bateria', 'La bateria hierve o el electrolito se consume rapido',
     'En esta POC indica sobrecarga por regulador defectuoso. Medir voltaje de carga (max 14.5V en reposo).',
     0, TRUE),
    ('Xciting 400', 'Encendido', 'Fallo de encendido aleatorio, motor da tirones',
     'En esta POC sugiere bujias en mal estado, bobina de encendido debil, o cable de bujia con fuga.',
     0, TRUE),
    ('Xciting 400', 'Encendido', 'La moto solo funciona con una bujia',
     'En esta POC bobina de encendido doble con una salida fallando o cable de bujia desconectado.',
     0, TRUE),
    ('Xciting 400', 'General', 'Se escucha un silbido agudo al acelerar',
     'En esta POC sugiere fuga en el colector de admision o junta del cuerpo de mariposa. Revisar con spray de carburador.',
     0, TRUE),
    ('Xciting 400', 'General', 'Olor a gasolina sin perdidas visibles',
     'En esta POC indica carburador/invector con fuga interna o canister de vapor saturado. Revisar lineas de combustible.',
     0, TRUE)
ON CONFLICT DO NOTHING;

-- ── More diagnostic trees ────────────────────────────────────────────

-- AK550: Brake diagnosis tree
INSERT INTO diagnostic_trees (tree_id, model, symptom, version, tree_json, active)
VALUES
    ('AK550_FRENOS_V1', 'AK550', 'Frenos', 1,
     '{
       "start_node": "b1",
       "nodes": {
         "b1": {"type":"question","text":"Sientes vibracion en la maneta al frenar?","answers":{"si":"b2","no":"b3"}},
         "b2": {"type":"diagnosis","result":"Discos de freno alabeados; rectificar o cambiar discos"},
         "b3": {"type":"question","text":"Escuchas ruido al frenar?","answers":{"si":"b4","no":"b6"}},
         "b4": {"type":"question","text":"El ruido es chirrido o rechinido?","answers":{"si":"b5","no":"b6"}},
         "b5": {"type":"diagnosis","result":"Pastillas gastadas al limite; cambiar pastillas urgentemente"},
         "b6": {"type":"question","text":"La palanca se siente blanda o esponjosa?","answers":{"si":"b7","no":"b8"}},
         "b7": {"type":"diagnosis","result":"Aire en circuito hidraulico; sangrar frenos y revisar nivel"},
         "b8": {"type":"diagnosis","result":"Sistema de frenos aparentemente normal; revision general recomendada"}
       }
     }'::jsonb,
     TRUE)
ON CONFLICT (tree_id) DO NOTHING;

-- AK550: Cooling system tree
INSERT INTO diagnostic_trees (tree_id, model, symptom, version, tree_json, active)
VALUES
    ('AK550_REFRIGERACION_V1', 'AK550', 'Refrigeracion', 1,
     '{
       "start_node": "c1",
       "nodes": {
         "c1": {"type":"question","text":"El testigo de temperatura se enciende en rojo?","answers":{"si":"c2","no":"c3"}},
         "c2": {"type":"diagnosis","result":"Motor sobrecalentado; detener inmediatamente. Revisar nivel refrigerante y ventilador"},
         "c3": {"type":"question","text":"El ventilador del radiador se enciende?","answers":{"si":"c5","no":"c4"}},
         "c4": {"type":"diagnosis","result":"Ventilador no funciona; revisar fusible, relé o motor del ventilador"},
         "c5": {"type":"question","text":"Hay perdida visible de refrigerante?","answers":{"si":"c6","no":"c7"}},
         "c6": {"type":"diagnosis","result":"Circuito abierto o perdida localizada; revisar manguitos, bomba y radiador"},
         "c7": {"type":"diagnosis","result":"Revisar termostato que no abre correctamente o tapa del radiador defectuosa"}
       }
     }'::jsonb,
     TRUE)
ON CONFLICT (tree_id) DO NOTHING;

-- Xciting 400: Brake tree
INSERT INTO diagnostic_trees (tree_id, model, symptom, version, tree_json, active)
VALUES
    ('XCITING_FRENOS_V1', 'Xciting 400', 'Frenos', 1,
     '{
       "start_node": "fx1",
       "nodes": {
         "fx1": {"type":"question","text":"Que freno presenta el problema?","answers":{"delantero":"fx2","trasero":"fx3"}},
         "fx2": {"type":"question","text":"La palanca delantera va hasta el manillar?","answers":{"si":"fx4","no":"fx5"}},
         "fx4": {"type":"diagnosis","result":"Nivel de liquido bajo o aire en circuito; rellenar y sangrar"},
         "fx5": {"type":"diagnosis","result":"Pastillas delanteras desgastadas; cambiar pastillas"},
         "fx3": {"type":"question","text":"El freno trasero es de tambor?","answers":{"si":"fx6","no":"fx7"}},
         "fx6": {"type":"diagnosis","result":"Zapatas traseras desgastadas o tambor ovalado; cambiar zapatas"},
         "fx7": {"type":"diagnosis","result":"Pastillas traseras desgastadas o disco sucio; revisar y limpiar"}
       }
     }'::jsonb,
     TRUE)
ON CONFLICT (tree_id) DO NOTHING;

-- Xciting 400: Electrical system tree
INSERT INTO diagnostic_trees (tree_id, model, symptom, version, tree_json, active)
VALUES
    ('XCITING_ELECTRICO_V1', 'Xciting 400', 'Sistema electrico', 1,
     '{
       "start_node": "e1",
       "nodes": {
         "e1": {"type":"question","text":"Las luces se atenuan al ralentí?","answers":{"si":"e2","no":"e3"}},
         "e2": {"type":"question","text":"El problema empeora al conectar accesorios?","answers":{"si":"e4","no":"e5"}},
         "e4": {"type":"diagnosis","result":"Generador defectuoso o regulador no mantiene carga; revisar voltaje en bateria"},
         "e5": {"type":"diagnosis","result":"Bateria debil o sulfatada; cargar y realizar prueba de carga"},
         "e3": {"type":"question","text":"Hay componentes que no funcionan (intermitentes, claxon)?","answers":{"si":"e6","no":"e7"}},
         "e6": {"type":"diagnosis","result":"Fusible fundido o masa suelta; revisar caja de fusibles y conexiones a masa"},
         "e7": {"type":"diagnosis","result":"Carga de bateria normal; revisar conexion de masa general y mazo principal"}
       }
     }'::jsonb,
     TRUE)
ON CONFLICT (tree_id) DO NOTHING;

-- ── More historical cases for AK550 ──────────────────────────────────
INSERT INTO historical_cases (case_id, model, symptom_category, case_text, final_diagnosis, base_confidence)
VALUES
    ('CASE-AK-013', 'AK550', 'Frenos',
     'Freno delantero vibra al frenar desde 60 km/h. Disco caliente al tacto tras conduccion normal.',
     'Discos de freno alabeados por sobrecalentamiento. Rectificado de discos y cambio de pastillas.',
     0.83),
    ('CASE-AK-014', 'AK550', 'Suspension',
     'Horquilla delantera pierde aceite por el reteno izquierdo. Mancha de aceite en la pierna de horquilla.',
     'Reten de horquilla desgastado, barra con ligera oxidacion. Cambio de retenes y revision de barras.',
     0.88),
    ('CASE-AK-015', 'AK550', 'Refrigeracion',
     'Motor alcanza temperatura alta en trafico urbano. Ventilador no se enciende. Fusible OK.',
     'Motor del ventilador defectuoso o relay de ventilador fundido. Reemplazo de motor/ventilador.',
     0.79),
    ('CASE-AK-016', 'AK550', 'Electrico',
     'Testigo de ABS encendido en cuadro pero frenos funcionan normalmente.',
     'Sensor de velocidad de rueda delantera sucio o con holgura. Limpieza y ajuste de sensor ABS.',
     0.74),
    ('CASE-AK-017', 'AK550', 'Bateria',
     'Bateria original descargada tras 10 dias parado. Arranque por empuje funciona.',
     'Bateria sulfatada con capacidad reducida. Corriente de reposo 8mA (elevada). Cambio de bateria.',
     0.86)
ON CONFLICT (case_id) DO NOTHING;

-- ── More historical cases for Xciting 400 ────────────────────────────
INSERT INTO historical_cases (case_id, model, symptom_category, case_text, final_diagnosis, base_confidence)
VALUES
    ('CASE-XC-011', 'Xciting 400', 'Frenos',
     'Freno trasero no detiene la moto correctamente. Pedal de freno tiene mucho recorrido.',
     'Zapatas de freno trasero desgastadas. Tambor con ligero ovalamiento. Cambio de zapatas.',
     0.81),
    ('CASE-XC-012', 'Xciting 400', 'Suspension',
     'Golpeteo en la direccion al pasar reductores de velocidad. Juego noticeable en la direccion.',
     'Rodamiento de direccion con desgaste por falta de engrase. Ajuste y engrase o cambio.',
     0.76),
    ('CASE-XC-013', 'Xciting 400', 'Sistema electrico',
     'Intermitentes dejan de funcionar tras lluvia. Al secarse vuelven a funcionar.',
     'Agua en el conector del relé de intermitentes. Limpieza de conectores y sellado con grasa dielectrica.',
     0.72),
    ('CASE-XC-014', 'Xciting 400', 'Refrigeracion',
     'Perdida lenta de refrigerante sin marcar charco. Nivel baja cada 2 semanas.',
     'Microfisura en radiador detectada con prueba de presion. Reparacion o sustitucion del radiador.',
     0.82),
    ('CASE-XC-015', 'Xciting 400', 'Encendido',
     'Fallo intermitente de encendido en humedo. En dias secos funciona correctamente.',
     'Cable de bujia con fuga de alta tension. Bobina de encendido con corrosion interna. Cambio de bobina y cables.',
     0.78)
ON CONFLICT (case_id) DO NOTHING;
