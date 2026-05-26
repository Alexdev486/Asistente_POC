-- Expansion of seed data for better POC demo coverage

-- More FAQs for AK550
INSERT INTO faqs (model, category, question, answer, usage_count, active)
VALUES
    ('AK550', 'Paradas de motor', 'La moto se para al pasar baches o en terreno irregular?', 
     'En esta POC, indica sensor de inclinacion defectuoso o suspension desgastada. Revisar sensor de kickstand.',
     0, TRUE),
    ('AK550', 'Arranque', 'La moto no arranca cuando hace mucho frio', 
     'En esta POC se recomienda: revisar bateria (voltaje debe ser > 11V), bujias sucias o mojadas, combustible con agua.',
     0, TRUE),
    ('AK550', 'Combustible', 'El motor pierde potencia tras repostar', 
     'En esta POC apunta a agua en el deposito o filtro de combustible obstruido. Vaciar deposito y revisar filtro.',
     0, TRUE),
    ('AK550', 'Testigo CELP', 'El testigo CELP parpadea y la moto funciona con tirones', 
     'En esta POC sugiere fallo en sensor de temperatura, TPS, o sistema de inyeccion. Leer codigos de error.',
     0, TRUE),
    ('AK550', 'Mantenimiento', 'Cada cuanto debo cambiar las bujias?', 
     'En esta POC se recomienda revisar cada 1000 km y cambiar cada 3000-5000 km segun desgaste.',
     0, TRUE),
    ('AK550', 'Embrague', 'El embrague suena al soltarlo rapidamente', 
     'En esta POC se asocia a cable seco o resorte de recuperacion desgastado. Lubricar o cambiar cable.',
     0, TRUE)
ON CONFLICT DO NOTHING;

-- More FAQs for Xciting 400
INSERT INTO faqs (model, category, question, answer, usage_count, active)
VALUES
    ('Xciting 400', 'Arranque', 'Demora mucho en arrancar, especialmente en frio', 
     'En esta POC se recomienda revisar: bateria, bujias, combustible limpio, limpieza de cuerpo de mariposa.',
     0, TRUE),
    ('Xciting 400', 'Paradas de motor', 'El motor se apaga cuando dejo de acelerar', 
     'En esta POC indica ralenti bajo o admision obstruida. Revisar buscador de aire y reglaje de ralenti.',
     0, TRUE),
    ('Xciting 400', 'Ruido', 'Escucho un ruido metalico ritmico del motor', 
     'En esta POC sugiere picado de motor (gasolina de baja octanaje) o valvulas desajustadas.',
     0, TRUE),
    ('Xciting 400', 'Escape', 'Sale humo negro del escape', 
     'En esta POC indica mezcla pobre o inyector sucio. Limpiar inyector o revisar sensor lambda.',
     0, TRUE),
    ('Xciting 400', 'Combustible', 'Consumo muy elevado de gasolina', 
     'En esta POC causas comunes: carburador mal reglado, aire obstruido, inyector sucio o bujias desgastadas.',
     0, TRUE),
    ('Xciting 400', 'Transmision', 'Traqueteo al subir pendientes', 
     'En esta POC indica correa de transmision desgastada o poleas con desgaste desigual. Revisar y cambiar.',
     0, TRUE),
    ('Xciting 400', 'Sistema electrico', 'Las luces parpadean al ralenti', 
     'En esta POC sugiere carga baja (generador defectuoso) o bateria agotada. Revisar voltaje de carga.',
     0, TRUE)
ON CONFLICT DO NOTHING;

-- More historical cases for AK550
INSERT INTO historical_cases (case_id, model, symptom_category, case_text, final_diagnosis, base_confidence)
VALUES
    ('CASE-AK-006', 'AK550', 'Paradas de motor',
     'Moto arranca bien pero se para de forma intermitente al conducir durante 5-10 minutos. Despues vuelve a funcionar.',
     'Sensor de inclinacion defectuoso con contactos oxidados',
     0.82),
    ('CASE-AK-007', 'AK550', 'Combustible',
     'No se escucha bomba de gasolina pero bateria y fusibles estan bien. Motor no arranca.',
     'Bomba de gasolina defectuosa con desgaste interno',
     0.90),
    ('CASE-AK-008', 'AK550', 'Arranque',
     'En invierno cuesta mucho trabajo arrancar, especialmente si hace frio durante la noche.',
     'Bateria debil (8V) con bajo amperaje de arranque',
     0.75),
    ('CASE-AK-009', 'AK550', 'Testigo CELP',
     'Testigo CELP encendido, motor funciona pero con cierta irregularidad al ralenti.',
     'Sensor de temperatura defectuoso (NTC)',
     0.78),
    ('CASE-AK-010', 'AK550', 'Embrague',
     'Al soltar lentamente la maneta del embrague escucho chirrido metalico continuo.',
     'Cable de embrague seco, falta lubricacion',
     0.68),
    ('CASE-AK-011', 'AK550', 'Mantenimiento',
     'Motor funciona bien en frio pero se apaga cuando alcanza temperatura de operacion.',
     'Reglaje de valvulas pisado (valvulas no cierran completamente en caliente)',
     0.85),
    ('CASE-AK-012', 'AK550', 'Paradas de motor',
     'Tras llenar el deposito con gasolina, motor presenta tirones y paradas intermitentes.',
     'Agua o contaminacion en nuevo combustible, filtro colapsado',
     0.76)
ON CONFLICT (case_id) DO NOTHING;

-- More historical cases for Xciting 400
INSERT INTO historical_cases (case_id, model, symptom_category, case_text, final_diagnosis, base_confidence)
VALUES
    ('CASE-XC-004', 'Xciting 400', 'Paradas de motor',
     'Moto arranca en frio pero se apaga al primer cambio de marchas. Vuelve a arrancar tras esperar.',
     'Ralenti bajo, necesita limpieza de cuerpo de mariposa',
     0.80),
    ('CASE-XC-005', 'Xciting 400', 'Ruido al embrague',
     'Maneta de embrague se siente dura y al accionarla escucho un chasquido.',
     'Rodamiento de embrague con juego excesivo o componentes desgastados',
     0.72),
    ('CASE-XC-006', 'Xciting 400', 'Escape',
     'Moto funciona pero por el escape sale mucho humo negro especialmente en aceleraciones.',
     'Mezcla rica, inyector sucio o sensor lambda defectuoso',
     0.74),
    ('CASE-XC-007', 'Xciting 400', 'Combustible',
     'Consumo de gasolina duplicado respecto al normal, motor no tira con potencia normal.',
     'Filtro de aire muy obstruido, inyector sucio',
     0.79),
    ('CASE-XC-008', 'Xciting 400', 'Arranque',
     'Motor dificil de arrancar, especialmente sin acelerar durante el arranque.',
     'Problemas de chispa o bateria debil, bujias sucias',
     0.73),
    ('CASE-XC-009', 'Xciting 400', 'Transmision',
     'Al acelerar fuerte escucho traqueteo ritmico y perdida de traccion momentanea.',
     'Correa de transmision deshilachada, poleas con desgaste desigual',
     0.81),
    ('CASE-XC-010', 'Xciting 400', 'Sistema electrico',
     'Luces delanteras e indicadores parpadean al ralenti, especialmente al conectar accesorios.',
     'Generador defectuoso o conexiones oxidadas, baja carga en bateria',
     0.77)
ON CONFLICT (case_id) DO NOTHING;

-- Additional diagnostic tree for AK550 - Testigo CELP (if not exists)
INSERT INTO diagnostic_trees (tree_id, model, symptom, version, tree_json, active)
VALUES
    ('AK550_ARRANQUE_V1', 'AK550', 'Dificultad de arranque', 1,
     '{
       "start_node": "a1",
       "nodes": {
         "a1": {"type":"question","text":"Escuchas el motor de arranque girar?","answers":{"si":"a2","no":"a3"}},
         "a2": {"type":"question","text":"Escuchas la bomba de gasolina?","answers":{"si":"a4","no":"a5"}},
         "a4": {"type":"diagnosis","result":"Bujias mojadas o sucias; revisar o cambiar"},
         "a5": {"type":"diagnosis","result":"Problemas de alimentacion de combustible"},
         "a3": {"type":"question","text":"La bateria muestra voltaje?","answers":{"si":"a6","no":"a7"}},
         "a6": {"type":"diagnosis","result":"Motor de arranque defectuoso"},
         "a7": {"type":"diagnosis","result":"Bateria descargada o desconectada"}
       }
     }'::jsonb,
     TRUE)
ON CONFLICT (tree_id) DO NOTHING;

-- Additional diagnostic tree for Xciting - Escape y humos
INSERT INTO diagnostic_trees (tree_id, model, symptom, version, tree_json, active)
VALUES
    ('XCITING_ESCAPE_V1', 'Xciting 400', 'Humo en el escape', 1,
     '{
       "start_node": "esc1",
       "nodes": {
         "esc1": {"type":"question","text":"De que color es el humo?","answers":{"negro":"esc2","azul":"esc3","blanco":"esc4"}},
         "esc2": {"type":"question","text":"El motor pierde potencia?","answers":{"si":"esc2a","no":"esc2b"}},
         "esc2a": {"type":"diagnosis","result":"Mezcla rica; limpiar inyector o revisar sensor lambda"},
         "esc2b": {"type":"diagnosis","result":"Valvula EGR atascada; limpiar"},
         "esc3": {"type":"diagnosis","result":"Aceite quemado; revisar nivel y cambiar aceite"},
         "esc4": {"type":"diagnosis","result":"Agua en combustible o capilares mojados; secar sistema"}
       }
     }'::jsonb,
     TRUE)
ON CONFLICT (tree_id) DO NOTHING;
