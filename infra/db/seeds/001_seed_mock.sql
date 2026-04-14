INSERT INTO vehicles (vin, model, family, displacement_cc, market, model_year)
VALUES
    ('AK550-POC-0001', 'AK550', 'Scooter GT', 550, 'ES', 2022),
    ('AK550-POC-0002', 'AK550', 'Scooter GT', 550, 'ES', 2023),
    ('AK550-POC-0003', 'AK550', 'Scooter GT', 550, 'ES', 2024),
    ('XCITING-POC-0001', 'Xciting 400', 'Scooter GT', 400, 'ES', 2021)
ON CONFLICT (vin) DO UPDATE
SET
    model = EXCLUDED.model,
    family = EXCLUDED.family,
    displacement_cc = EXCLUDED.displacement_cc,
    market = EXCLUDED.market,
    model_year = EXCLUDED.model_year;

INSERT INTO faqs (faq_id, model, category, question, answer, usage_count, active)
VALUES
    (
        1,
        'AK550',
        'Paradas de motor',
        'Por que puede pararse la moto en marcha de forma intermitente?',
        'Las causas mas probables en esta POC son: sensor de inclinacion defectuoso, bomba de gasolina defectuosa, reglaje de valvulas pisado, agua en el deposito o mal contacto en pipa de bujia.',
        0,
        TRUE
    ),
    (
        2,
        'AK550',
        'Combustible',
        'Que significa que no se escuche la bomba de gasolina al dar contacto?',
        'En esta POC se interpreta como una senal compatible con fallo de bomba de gasolina o falta de alimentacion electrica al sistema de combustible.',
        0,
        TRUE
    ),
    (
        3,
        NULL,
        'General',
        'Que significa el testigo CELP encendido?',
        'En esta POC, el testigo CELP indica una averia relacionada con la gestion electronica del motor o el sistema de inyeccion y debe orientar la diagnosis hacia la rama especifica de CELP.',
        0,
        TRUE
    ),
    (
        4,
        'AK550',
        'Mantenimiento',
        'Que puede indicar que falle en caliente y vuelva a arrancar en frio?',
        'En esta POC, ese patron es compatible con reglaje de valvulas pisado y perdida de compresion en caliente.',
        0,
        TRUE
    )
ON CONFLICT (faq_id) DO UPDATE
SET
    model = EXCLUDED.model,
    category = EXCLUDED.category,
    question = EXCLUDED.question,
    answer = EXCLUDED.answer,
    usage_count = EXCLUDED.usage_count,
    active = EXCLUDED.active;

SELECT setval('faqs_faq_id_seq', (SELECT MAX(faq_id) FROM faqs));

INSERT INTO historical_cases (
    case_id,
    model,
    symptom_category,
    case_text,
    final_diagnosis,
    base_confidence
)
VALUES
    (
        'CASE-001',
        'AK550',
        'Paradas de motor',
        'La moto se para en marcha al pasar por baches y vuelve a arrancar despues de quitar y dar contacto.',
        'Sensor de inclinacion defectuoso',
        0.8500
    ),
    (
        'CASE-002',
        'AK550',
        'Paradas de motor',
        'La moto se para y al volver a dar contacto no se escucha la bomba de gasolina.',
        'Bomba de gasolina defectuosa',
        0.9000
    ),
    (
        'CASE-003',
        'AK550',
        'Paradas de motor',
        'La moto se para en caliente y despues de enfriar vuelve a arrancar con normalidad.',
        'Reglaje de valvulas pisado',
        0.8800
    ),
    (
        'CASE-004',
        'AK550',
        'Paradas de motor',
        'Tras repostar, la moto presenta paradas intermitentes y funcionamiento irregular.',
        'Agua en el deposito',
        0.7500
    ),
    (
        'CASE-005',
        'AK550',
        'Paradas de motor',
        'La moto se para de forma intermitente pero a veces rearranca sin necesidad de quitar contacto.',
        'Mal contacto en pipa de bujia',
        0.7000
    )
ON CONFLICT (case_id) DO UPDATE
SET
    model = EXCLUDED.model,
    symptom_category = EXCLUDED.symptom_category,
    case_text = EXCLUDED.case_text,
    final_diagnosis = EXCLUDED.final_diagnosis,
    base_confidence = EXCLUDED.base_confidence;

INSERT INTO diagnostic_trees (tree_id, model, symptom, version, tree_json, active)
VALUES
    (
        'AK550_PARADAS_V1',
        'AK550',
        'Paradas de motor',
        1,
        '{
            "start_node": "n1",
            "nodes": {
                "n1": {"type":"question","text":"Cuando se para, arranca sin quitar contacto?","answers":{"si":"n2","no":"n3"}},
                "n2": {"type":"diagnosis","result":"Mal contacto en pipa de bujia"},
                "n3": {"type":"question","text":"Quita contacto y vuelve a intentar. Arranca?","answers":{"si":"n4","no":"n5"}},
                "n4": {"type":"diagnosis","result":"Sensor de inclinacion defectuoso"},
                "n5": {"type":"question","text":"Se escucha la bomba de gasolina?","answers":{"si":"n6","no":"n7"}},
                "n7": {"type":"diagnosis","result":"Bomba de gasolina defectuosa"},
                "n6": {"type":"question","text":"Arranca despues de enfriar?","answers":{"si":"n8","no":"n9"}},
                "n8": {"type":"diagnosis","result":"Reglaje de valvulas pisado"},
                "n9": {"type":"diagnosis","result":"Agua en el deposito"}
            }
        }'::jsonb,
        TRUE
    ),
    (
        'AK550_CELP_V1',
        'AK550',
        'Testigo CELP encendido',
        1,
        '{
            "start_node": "c1",
            "nodes": {
                "c1": {
                    "type": "question",
                    "text": "La moto arranca y funciona, aunque con el testigo CELP encendido?",
                    "answers": {"si": "c2", "no": "c3"}
                },
                "c2": {"type": "diagnosis", "result": "Fallo electronico no bloqueante; revisar sensor TPS, sensor de temperatura o lectura de codigos"},
                "c3": {
                    "type": "question",
                    "text": "Ademas del testigo CELP, hay dificultad de arranque o parada del motor?",
                    "answers": {"si": "c4", "no": "c5"}
                },
                "c4": {"type": "diagnosis", "result": "Posible fallo de alimentacion o gestion electronica del combustible"},
                "c5": {"type": "diagnosis", "result": "Revisar lectura de codigos y comprobaciones electricas basicas"}
            }
        }'::jsonb,
        TRUE
    )
ON CONFLICT (tree_id) DO UPDATE
SET
    model = EXCLUDED.model,
    symptom = EXCLUDED.symptom,
    version = EXCLUDED.version,
    tree_json = EXCLUDED.tree_json,
    active = EXCLUDED.active;
