# Asistente Diagnóstico Conversacional POC

[![Tests](https://img.shields.io/badge/tests-133%20passed-brightgreen)](#)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.74-FF6F00)](https://langchain-ai.github.io/langgraph/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)](https://www.postgresql.org/)
[![pgvector](https://img.shields.io/badge/pgvector-0.3-336791)](https://github.com/pgvector/pgvector)
[![Groq](https://img.shields.io/badge/Groq-llama--3.1--8b-F97316)](https://groq.com/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-fallback-8B5CF6)](https://openrouter.ai/)

Asistente técnico conversacional para diagnóstico de motocicletas. Combina **árboles de diagnóstico estructurados**, **FAQ por modelo**, **búsqueda híbrida sobre casos históricos** y **LLM** (Groq + OpenRouter) para interpretar texto libre. Todo orquestado con **LangGraph** con trazabilidad completa por turno.

---

## Tabla de contenido

- [Demo rápida](#demo-rápida)
- [Tecnologías](#tecnologías)
- [Arquitectura](#arquitectura)
- [Flujo conversacional](#flujo-conversacional)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Cómo empezar](#cómo-empezar)
- [Datos de prueba](#datos-de-prueba)
- [Endpoints de la API](#endpoints-de-la-api)
- [Tests](#tests)
- [Pruebas de carga](#pruebas-de-carga)
- [Capturas](#capturas)

---

## Demo rápida

```bash
# 1. Clonar e instalar dependencias
git clone <repo>
cd Asistente_POC
python -m venv .venv && source .venv/bin/activate
pip install -r apps/api/requirements.txt
cd apps/web && npm install && cd -

# 2. Configurar variables de entorno
cp .env.example apps/api/.env
# Editar apps/api/.env: añadir GROQ_API_KEY y OPENROUTER_API_KEY

# 3. Iniciar base de datos
make db-up
make db-migrate
make db-seed
make db-ingest-chunks

# 4. Iniciar backend (puerto 8000)
make api-run

# 5. En otra terminal, iniciar frontend (puerto 3000)
make web-run

# 6. Probar
curl -X POST http://localhost:8000/api/v1/session/start
curl -X POST http://localhost:8000/api/v1/health

# 7. Para detener todo
make api-stop      # Detiene backend (puerto 8000)
make web-stop      # Detiene frontend (puerto 3000)
make db-down       # Detiene PostgreSQL
```

---

## Tecnologías

| Capa | Tecnología | Propósito |
|------|-----------|-----------|
| **Frontend** | Next.js 14 + React + TypeScript + Tailwind + Framer Motion | Chat UI responsiva con animaciones y modo oscuro |
| **API** | FastAPI + Python 3.12 | Backend monolítico modular por capas |
| **Orquestación** | LangGraph 0.2.74 | Grafo de estado conversacional con nodos y aristas condicionales |
| **Base de datos** | PostgreSQL 16 + pgvector | Datos transaccionales + búsqueda vectorial híbrida |
| **LLM primario** | Groq (llama-3.1-8b-instant) | Análisis de texto libre en módulo Otros |
| **LLM fallback** | OpenRouter (meta-llama/llama-3.1-8b-instruct:free) | Resiliencia ante fallos del proveedor primario |
| **Embeddings** | SHA-256 determinista (POC) | Búsqueda semántica híbrida (vectorial + léxica) |
| **Trazabilidad** | Logs estructurados + decision_logs en BD | Auditoría completa por turno y módulo |

---

## Arquitectura

```
┌──────────────────────────────────────────────┐
│           Frontend (Next.js)                  │
│  ChatShell + useSession + feedback UI        │
├──────────────────────────────────────────────┤
│           API (FastAPI)                       │
│  /session/start  /session/message            │
│  /session/{id}/feedback  /metrics/summary    │
├──────────────────────────────────────────────┤
│      SessionUseCases (capa de aplicación)     │
│  orquesta: LangGraph → módulos → persistencia │
├──────────────────┬───────────────────────────┤
│   LangGraph      │   Módulos de dominio      │
│   StateGraph     │   ├─ VINLookupService     │
│   ┌──────────┐   │   ├─ DiagnosticTreeEngine │
│   │START────→│   │   ├─ FAQMatcherService    │
│   │vin_lookup│   │   ├─ FreeTextParserService│
│   │tree_engine│  │   ├─ HybridRankingService │
│   │faq_matcher│  │   └─ HistoricalRetrieval  │
│   │free_text  │   ├──────────────────────────┤
│   │→ END     │   │   LLM Gateway             │
│   └──────────┘   │   ├─ Groq (primario)      │
│                  │   └─ OpenRouter (fallback) │
├──────────────────┴───────────────────────────┤
│    Infraestructura                           │
│  ThreadedConnectionPool (1-10)               │
│  Repositorios SQL (8) + decision_logs        │
├──────────────────────────────────────────────┤
│    PostgreSQL + pgvector                     │
│  sessions / session_state / messages         │
│  feedback / decision_logs / vehicles         │
│  faqs / diagnostic_trees / historical_cases  │
│  knowledge_chunks / embedding_jobs           │
└──────────────────────────────────────────────┘
```

### Principios de diseño

- **VIN obligatorio** antes de cualquier diagnóstico. El modelo se obtiene por lookup, no por inferencia.
- **Estado en BD como fuente de verdad**. El LLM es apoyo, no memoria.
- **LangGraph** orquesta el flujo conversacional con nodos y aristas condicionales.
- **Trazabilidad total**: cada decisión queda registrada en `decision_logs` con `turn_id` y `confidence`.
- **LLM con fallback**: Groq → OpenRouter → reglas locales → guardrail `weak_evidence`.
- **POC preparada para MVP**: monolito modular, fácil de extraer a microservicios.

---

## Flujo conversacional

### Mapa general

```
Usuario → POST /session/start
  ↓
[Asistente solicita bastidor]
  ↓
Usuario → envía VIN → POST /session/message
  ↓
VINLookup → ¿Válido?
  ├─ No → "No identificado, intenta de nuevo"
  └─ Sí  → Fija modelo en session_state → Muestra menú
            ↓
       ┌────┼────┐
       │    │    │
   Sintomas FAQ  Otros
   frecuentes     (texto libre)
       │    │    │
   Tree   FAQ   FreeTextParser
   Engine Matcher ↓
       │    │   HybridSearch
       │    │   + Ranking
       │    │   + LLM (Groq)
       │    │    │
       └────┼────┘
            ↓
   Response Builder → mensaje + quick_replies
            ↓
   Persistir: messages + decision_logs + session_state
            ↓
   ¿Feedback? → POST /session/{id}/feedback → sesión completa
```

### Routing condicional (LangGraph)

El grafo de LangGraph tiene 6 nodos conectados desde `START` mediante una arista condicional:

```
START → _route_turn(state) → {
  "vin_lookup"       → Node: VINLookup
  "tree_engine"       → Node: TreeEngine
  "faq_matcher"       → Node: FAQMatcher
  "free_text_parser"  → Node: FreeTextParser
  "menu_selection"    → Node: MenuSelection
  "out_of_scope"      → Node: OutOfScope
} → END
```

Cada nodo ejecuta su lógica de dominio, muta el estado y lo retorna. El multi-turno se maneja mediante persistencia en BD entre invocaciones.

### Módulo Otros (texto libre)

```
Texto libre → FreeTextParserService
  ├─ ¿LLM disponible? → Groq (con prompt + taxonomy)
  │   └─ ¿Falla? → OpenRouter (fallback)
  │       └─ ¿Falla ambos? → Reglas locales (keywords)
  └─ Embedding (SHA-256) → hybrid_search() en knowledge_chunks
  └─ HybridRankingService → top-3 hipótesis
      ├─ ¿Confianza ≥ 0.35? → Diagnóstico con fuentes
      ├─ ¿FAQ match? → Fallback a FAQ
      └─ ¿Nada? → "weak_evidence" (no inventa)
```

---

## Estructura del proyecto

```
Asistente_POC/
├── apps/
│   ├── api/                      # Backend FastAPI
│   │   ├── app/
│   │   │   ├── api/v1/endpoints/ # session.py, health.py, metrics.py
│   │   │   ├── application/
│   │   │   │   ├── orchestrator/ # langgraph_flow.py (ConversationGraph)
│   │   │   │   └── use_cases/    # session_use_cases.py
│   │   │   ├── core/             # config.py
│   │   │   ├── infrastructure/
│   │   │   │   ├── db/           # sync_connection.py, repositories/
│   │   │   │   ├── llm/          # gateway.py, providers/ (groq, openrouter)
│   │   │   │   └── retrieval/    # embeddings.py
│   │   │   ├── modules/          # vin_lookup, faq_matcher, tree_engine,
│   │   │   │                     # free_text_parser, hybrid_ranking,
│   │   │   │                     # historical_retrieval
│   │   │   └── schemas/          # requests.py, responses.py
│   │   └── tests/                # 133 tests
│   └── web/                      # Frontend Next.js
│       └── src/
│           ├── app/              # page.tsx (chat UI)
│           ├── components/       # ChatShell.tsx
│           ├── features/session/ # useSession.ts
│           ├── lib/api/          # client.ts
│           └── types/            # session.ts
├── infra/
│   └── db/
│       ├── migrations/           # 7 SQL migraciones idempotentes
│       └── seeds/                # seed SQL + expand
├── data/
│   ├── diagnostic_trees/         # Árboles JSON (paradas, CELP, arranque...)
│   ├── prompts/                  # System prompts para LLM
│   └── seeds/                    # Datos mock JSON
├── scripts/
│   ├── db/                       # seed.sh, migrate.sh, ingest chunks
│   └── dev/                      # run_api, run_web, run_load_test, run_qa
├── packages/                     # Compartidos (contracts, shared-utils)
├── Makefile                      # Comandos principales
└── .env.example                  # Template de variables de entorno
```

---

## Cómo empezar

### Requisitos

- Python 3.12+
- Node.js 18+
- Docker + Docker Compose (para PostgreSQL)
- Cuentas gratuitas en [Groq](https://groq.com) y [OpenRouter](https://openrouter.ai)

### Instalación

```bash
# 1. Clonar
git clone <repo>
cd Asistente_POC

# 2. Entorno Python
python -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt

# 3. Frontend
cd apps/web && npm install && cd -

# 4. Variables de entorno
cp .env.example apps/api/.env
# Editar apps/api/.env y añadir:
#   GROQ_API_KEY="gsk_tu_clave"
#   OPENROUTER_API_KEY="sk-or-tu_clave"

# 5. Base de datos
make db-up              # Inicia PostgreSQL + pgvector en Docker
make db-migrate         # Ejecuta migraciones SQL
make db-seed            # Carga datos de prueba
make db-ingest-chunks   # Genera knowledge_chunks + embeddings

# 6. Backend
make api-run            # http://localhost:8000

# 7. Frontend
make web-run            # http://localhost:3000
```

### Detener

```bash
make api-stop      # Detiene backend (puerto 8000)
make web-stop      # Detiene frontend (puerto 3000)
make db-down       # Detiene PostgreSQL
```

### Ver estado

```bash
curl http://localhost:8000/api/v1/health
# {"status":"ok"}

curl http://localhost:8000/api/v1/metrics/summary
# {"total_sessions":0,"completed_sessions":0,...}
```

### Añadir fotos de los modelos

Para que el frontend muestre la foto del modelo al identificar el bastidor:

1. Coloca las imágenes en `data/vehicle_photos/`
2. El nombre del archivo debe coincidir con el nombre del modelo (espacios → guion bajo):
   - `AK550.jpg` (o `.png`, `.jpeg`, `.webp`)
   - `Xciting_400.jpg`
3. Si el archivo existe, la API lo sirve en `/api/v1/photos/<nombre>` y el frontend lo muestra automáticamente

Ejemplo:
```bash
cp ~/Descargas/ak550.jpg data/vehicle_photos/AK550.jpg
cp ~/Descargas/xciting400.jpg data/vehicle_photos/Xciting_400.jpg
```

---

## Datos de prueba

### Bastidores (VIN) disponibles

| VIN | Modelo | Año |
|-----|--------|-----|
| `AK550-POC-0001` | AK550 | 2022 |
| `AK550-POC-0002` | AK550 | 2023 |
| `AK550-POC-0003` | AK550 | 2024 |
| `XCITING-POC-0001` | Xciting 400 | 2021 |

### FAQs precargadas

**AK550** (10 preguntas): testigo CELP, paradas de motor, ruido en aceleración, humo en escape, batería después de reposo, revisión de pastillas de freno, tipo de aceite, presión de neumáticos, intervalo de cambio de correa, revisión de 1000 km.

**Xciting 400** (10 preguntas): similares adaptadas al modelo.

### Árboles de diagnóstico

| ID | Modelo | Síntoma |
|----|--------|---------|
| `AK550_PARADAS_V1` | AK550 | Paradas de motor |
| `AK550_CELP_V1` | AK550 | Testigo CELP encendido |
| `AK550_ARRANQUE_V1` | AK550 | Dificultad de arranque |
| `XCITING_PARADAS_V1` | Xciting 400 | Paradas de motor |
| `XCITING_EMBRAGUE_V1` | Xciting 400 | Ruido al embrague |
| `XCITING_ESCAPE_V1` | Xciting 400 | Humo en el escape |

### Casos históricos

- **22 casos** (12 AK550 + 10 Xciting 400) con diagnósticos realistas.
- Usados por el módulo Otros para búsqueda híbrida y ranking.

### Guion de demo recomendado

```bash
# 1. Iniciar sesión
curl -X POST http://localhost:8000/api/v1/session/start

# 2. Enviar bastidor
curl -X POST http://localhost:8000/api/v1/session/message \
  -H "Content-Type: application/json" \
  -d '{"session_id":"<ID>","message":"AK550-POC-0001"}'

# 3. Seleccionar síntomas frecuentes
curl -X POST http://localhost:8000/api/v1/session/message \
  -H "Content-Type: application/json" \
  -d '{"session_id":"<ID>","message":"Sintomas frecuentes"}'

# 4. Seleccionar un síntoma
curl -X POST http://localhost:8000/api/v1/session/message \
  -H "Content-Type: application/json" \
  -d '{"session_id":"<ID>","message":"Paradas de motor"}'

# 5. Preguntar una FAQ
curl -X POST http://localhost:8000/api/v1/session/message \
  -H "Content-Type: application/json" \
  -d '{"session_id":"<ID>","message":"Consultas frecuentes"}'
# Luego: "Por que se enciende el testigo CELP?"

# 6. Texto libre
curl -X POST http://localhost:8000/api/v1/session/message \
  -H "Content-Type: application/json" \
  -d '{"session_id":"<ID>","message":"Otros"}'
# Luego: "La moto se calienta mucho en ciudad"

# 7. Feedback
curl -X POST http://localhost:8000/api/v1/session/<ID>/feedback \
  -H "Content-Type: application/json" \
  -d '{"useful":true,"comment":"Demo funcional"}'
```

---

## Endpoints de la API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/session/start` | Inicia sesión de diagnóstico |
| `POST` | `/api/v1/session/message` | Envía mensaje del usuario |
| `GET` | `/api/v1/session/{id}` | Obtiene estado de sesión |
| `GET` | `/api/v1/session/{id}/messages` | Historial de mensajes |
| `POST` | `/api/v1/session/{id}/feedback` | Guarda feedback y cierra sesión |
| `GET` | `/api/v1/metrics/summary` | Resumen de métricas de uso |

### Esquema de respuesta estándar

Todos los mensajes devuelven:

```json
{
  "session_id": "uuid",
  "message": "texto del asistente",
  "state": {
    "vin": "string | null",
    "model": "string | null",
    "current_symptom": "string | null",
    "current_node": "string | null"
  },
  "diagnostic_output": {
    "primary_hypothesis": "string",
    "alternatives": ["string"],
    "next_check": "string",
    "short_explanation": "string",
    "confidence": 0.0-1.0
  } | null,
  "quick_replies": ["string"] | null
}
```

---

## Tests

```bash
cd apps/api
PYTHONPATH="tests:$PYTHONPATH" python -m pytest tests/ -v
```

**133 tests** — 0 failures, 0 errors:

| Fichero | Tests | Cobertura |
|---------|-------|-----------|
| `test_conversation_graph.py` | 37 | Routing, VIN, tree, FAQ, free text, state clearing |
| `test_session_use_cases.py` | 23 | Start, message, feedback, state updates, logs |
| `test_free_text_parser.py` | 18 | LLM path, rules fallback, edge cases |
| `test_api_endpoints.py` | 19 | Endpoints E2E, flujo completo, métricas |
| `test_edge_cases.py` | 25 | Schemas, VIN, tree, FAQ, ranking, retrieval |
| `test_faq_matcher.py` | 5 | Scope priority, fallback |
| `test_tree_engine.py` | 2 | Advance to diagnosis |
| `test_hybrid_ranking.py` | 3 | Score ordering |
| `test_integration_repository.py` | 1 | DB integration |

```bash
# QA completa
bash scripts/dev/run_qa.sh

# O matriz exhaustiva
bash scripts/dev/run_qa_matrix.sh
```

---

## Pruebas de carga

```bash
source .venv/bin/activate
python scripts/dev/run_load_test.py --concurrency 3 --sessions 5
```

Simula sesiones concurrentes (Start → VIN → FAQ → Feedback) contra la API. Verifica conexiones al pool (ThreadedConnectionPool 1-10) y mide tiempos de respuesta. Salida:

```
  LOAD TEST SUMMARY
  Sessions successful:   5/5
  Avg session time:     432.1ms
  Min session time:     210.3ms
  Max session time:     891.7ms
  Avg VIN lookup:       45.2ms
  Avg FAQ match:        120.8ms
  Avg Feedback save:    15.3ms
```

---

## Licencia

POC — solo para evaluación técnica.
