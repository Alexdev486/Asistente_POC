# Asistente POC - Diagnostico conversacional por bastidor

POC de asistente tecnico para motocicletas con logica hibrida:
**VIN obligatorio + arboles + FAQ + casos historicos + apoyo LLM**.

Este README sirve como **entregable de fase** y tambien como **handoff tecnico** para futuras sesiones.

---

## Tabla de contenido

1. [Checklist del entregable](#checklist-del-entregable)
2. [Handoff rapido](#handoff-rapido)
3. [Arquitectura y flujo del asistente](#arquitectura-y-flujo-del-asistente)
4. [Tecnologias y stack](#tecnologias-y-stack)
5. [Herramientas open source evaluadas](#herramientas-open-source-evaluadas)
6. [Estructura del proyecto en GitHub](#estructura-del-proyecto-en-github)
7. [Estado actual del backend](#estado-actual-del-backend)
8. [Diseno y creacion de BBDD (core + vectorial)](#diseno-y-creacion-de-bbdd-core--vectorial)
9. [Datos iniciales cargados](#datos-iniciales-cargados)
10. [Arranque local](#arranque-local)
11. [Cronograma de trabajo por tareas](#cronograma-de-trabajo-por-tareas)
12. [Criterios de cierre POC](#criterios-de-cierre-poc)
13. [Instrucciones para la siguiente sesion](#instrucciones-para-la-siguiente-sesion)

---

## Checklist del entregable

| Requisito de la fase | Estado | Seccion |
|---|---|---|
| Arquitectura y flujo del asistente | Completado | Seccion 3 |
| Estructura del proyecto en carpetas GitHub | Completado | Seccion 6 |
| Diseno y creacion de BBDD + vectorial | Completado | Seccion 8 |
| Investigacion herramientas open source para produccion | Completado | Seccion 5 |
| Cronograma de trabajo | Completado | Seccion 11 |
| Contexto util para otra sesion | Completado | Secciones 2 y 13 |

---

## Handoff rapido

Si entras en una nueva sesion, este es el resumen operativo:

- Estructura base creada: `apps`, `infra`, `data`, `scripts`, `packages`.
- BBDD core + vectorial creada por migraciones SQL idempotentes.
- Endpoints base implementados para sesion/feedback/metricas.
- `SessionUseCases` ya esta conectado a persistencia SQL real (`sessions` + `session_state`).
- `decision_logs` incorpora `confidence` por turno con migracion dedicada.
- Modulos de lectura de conocimiento conectados a BD real (`vehicles`, `faqs`, `diagnostic_trees`, `historical_cases`).

Referencia funcional del negocio:
`DDT_POC_Asistente_Conversacional.docx`.

---

## Arquitectura y flujo del asistente

### Diagrama visual de arquitectura

![Diagrama de arquitectura](./diagrama-arquitectura.png)

### Explicacion de la arquitectura

La arquitectura implementada es un **monolito modular por capas**, pensada para una POC rapida pero con estructura de crecimiento a MVP.

| Capa / Bloque | Responsabilidad | Componentes actuales |
|---|---|---|
| UI | Interfaz conversacional y menu guiado | Next.js (Chat UI) |
| API Layer | Contrato HTTP, validacion de entrada/salida | FastAPI (`/session/*`, `/metrics/summary`) |
| Application | Orquestacion del flujo conversacional | LangGraph + use cases |
| Domain Modules | Logica de negocio por capacidad | VIN, FAQ, Tree Engine, Free Text, Retrieval, Ranking, Response Builder |
| Data | Estado transaccional y conocimiento tecnico | PostgreSQL + pgvector |
| AI | Clasificacion/redaccion con fallback multi-proveedor | LLM Gateway (Groq primario, OpenRouter fallback) |
| Observability | Trazas y diagnostico operativo | decision logs + base OTEL/logging |

#### Como fluye un turno en esta arquitectura

1. La UI envia el mensaje a FastAPI.
2. El orquestador decide la ruta (VIN, FAQ, Tree u Otros).
3. El modulo correspondiente consulta BD y, si aplica, usa el gateway LLM.
4. Response Builder genera salida estandar.
5. Se persisten `messages`, `decision_logs` y `session_state`.
6. La API devuelve respuesta final a la UI.

### Flujos adaptados (Mermaid)

#### 1) Flujo general por capas (adaptado para presentacion)

```mermaid
flowchart LR
  subgraph UI[Canal conversacional]
    U1[Usuario]
    U2[Chat UI]
    U1 --> U2
  end

  subgraph API[API Layer - FastAPI]
    A1[POST /session/start]
    A2[POST /session/message]
    A3[POST /session/{id}/feedback]
  end

  subgraph ORCH[Orquestacion - LangGraph]
    O1[Validar VIN]
    O2[Resolver modelo por bastidor]
    O3[Seleccionar ruta]
    O4[Construir respuesta estandar]
  end

  subgraph MOD[Modulos de dominio]
    M1[Tree Engine]
    M2[FAQ Matcher]
    M3[Modulo Otros: Free Text + Tags + Retrieval + Ranking]
  end

  subgraph DATA[Persistencia]
    D1[(session_state)]
    D2[(messages)]
    D3[(decision_logs)]
    D4[(feedback)]
  end

  subgraph AI[LLM Gateway]
    L1[Groq primario]
    L2[OpenRouter fallback]
  end

  U2 --> A1 --> O1
  U2 --> A2 --> O3
  O1 -->|VIN valido| O2 --> D1
  O3 -->|Sintomas| M1 --> O4
  O3 -->|FAQ| M2 --> O4
  O3 -->|Otros| M3 --> O4
  M3 --> L1
  L1 -. fallback .-> L2
  O4 --> D2
  O4 --> D3
  U2 --> A3 --> D4
  O4 --> U2
```

#### 2) Flujo operativo de un turno (VIN obligatorio + rutas)

```mermaid
flowchart TD
  A[Inicio sesion] --> B[Solicitar bastidor]
  B --> C{VIN valido?}
  C -- No --> B
  C -- Si --> D[Fijar modelo en session_state]
  D --> E[Mostrar menu: Sintomas / FAQ / Otros]
  E --> F{Ruta elegida}
  F -- Sintomas --> G[Tree Engine]
  F -- FAQ --> H[FAQ Matcher]
  F -- Otros --> I[Free Text + Hybrid Search + Ranking]
  G --> J[Response Builder]
  H --> J
  I --> J
  J --> K[Persistir messages + decision_logs + session_state]
  K --> L[Responder al usuario]
  L --> M{Fin diagnostico?}
  M -- No --> E
  M -- Si --> N[Solicitar feedback y cerrar]
```

#### 3) Diseno del modulo "Otros" (alineado con DDT)

Objetivo: traducir texto libre a hipotesis tecnica util y, cuando proceda, reconducir a un flujo estructurado.

```mermaid
flowchart TD
  O1[Recibir texto libre] --> O2[Asociar mensaje a session_id]
  O2 --> O3[Normalizar texto: minusculas + limpieza basica]
  O3 --> O4[Extraer tags/atributos: reglas y/o LLM]
  O4 --> O5[Leer modelo desde session_state]
  O5 --> O6[Filtrar historical_cases por modelo]
  O6 --> O7[Buscar coincidencias en historical_cases y FAQs]
  O7 --> O8[Calcular ranking hibrido]
  O8 --> O9[Seleccionar top-3 hipotesis]
  O9 --> O10[Construir respuesta + siguiente comprobacion]
  O10 --> O11{Reconducible a flujo conocido?}
  O11 -- Si --> O12[Sugerir categoria/flujo: FAQ o Tree]
  O11 -- No --> O13[Mantener en ruta Otros]
  O12 --> O14[Persistir messages + decision_logs + session_state]
  O13 --> O14
```

Senales minimas del ranking hibrido en "Otros":
- similitud semantica del texto con `historical_cases`
- coincidencia de modelo (`session_state.model`)
- frecuencia historica del caso
- `base_confidence` del caso

Nota clave para defensa: `historical_cases` es la fuente de conocimiento para comparar y proponer hipotesis; `decision_logs` solo audita por que decidio el sistema en ese turno.

### Principios de arquitectura

- VIN obligatorio antes de diagnostico.
- Modelo fijado por lookup, no por inferencia de texto.
- Estado de sesion en BD como fuente de verdad.
- LLM como apoyo, no como motor unico.
- Trazabilidad completa por turno y modulo.
- POC simple de operar, preparada para escalar a MVP.

---

## Tecnologias y stack

| Capa | Tecnologia elegida | Motivo |
|---|---|---|
| UI | Next.js + React + TypeScript | Rapidez para chat UI y despliegue |
| API | FastAPI + Python | Productividad alta para integracion IA |
| Orquestacion | LangGraph | Flujo conversacional controlado |
| BBDD core | PostgreSQL | Solida, portable y estandar |
| BBDD vectorial | pgvector sobre PostgreSQL | OLTP + vector en un solo sistema |
| LLM | Groq + OpenRouter | Buen coste/rendimiento y fallback |
| Observabilidad | OpenTelemetry + logs estructurados | Trazabilidad tecnica |
| Infra local | Docker Compose | Entorno reproducible |

---

## Herramientas open source evaluadas

### Base de datos y vector DB

| Categoria | Opcion | Pros | Contras | Recomendacion |
|---|---|---|---|---|
| SQL + vector unificado | PostgreSQL + pgvector | Menor complejidad, un solo motor | Menos especializado que vector DB puro | **Elegida para POC** |
| Vector DB dedicada | Qdrant | Muy buena para retrieval vectorial | Segundo sistema a operar | Opcional para alta escala |
| Vector DB dedicada | Weaviate | Buen ecosistema semantic search | Complejidad operativa mayor | Opcional para alta escala |
| Managed Postgres + vector | Supabase | Rapido de operar, auth/storage extra | Dependencia de proveedor | **Muy buena para MVP/produccion inicial** |

### LLM y gateway

| Opcion | Rol recomendado |
|---|---|
| Groq | Proveedor primario por latencia/coste |
| OpenRouter | Fallback multi-modelo |
| Gateway propio backend | Evita acoplar dominio a proveedor |

### Despliegue

| Capa | Opcion recomendada | Alternativas |
|---|---|---|
| Frontend | Vercel | Netlify, Cloudflare Pages |
| Backend API | Render / Fly.io / Railway | Kubernetes, ECS/Fargate |
| BBDD | Supabase Postgres + pgvector o Neon + pgvector | Postgres autogestionado |
| Observabilidad | Grafana stack + OTEL | Soluciones SaaS |

Stack sugerido para MVP:
- Front en **Vercel**
- API en **Render/Fly**
- DB en **Supabase (Postgres + pgvector)**
- LLM via **Groq + OpenRouter**

---

## Estructura del proyecto en GitHub

```text
.
|-- apps/
|   |-- api/
|   |   |-- app/
|   |   |   |-- api/v1/endpoints/
|   |   |   |-- application/
|   |   |   |-- core/
|   |   |   |-- domain/
|   |   |   |-- infrastructure/
|   |   |   |-- modules/
|   |   |   `-- schemas/
|   |   `-- tests/
|   `-- web/
|       `-- src/
|-- infra/
|   |-- db/{migrations,seeds}
|   |-- docker/
|   `-- observability/
|-- data/
|   |-- diagnostic_trees/
|   |-- prompts/
|   `-- seeds/
|-- scripts/{db,dev}
|-- packages/{contracts,shared-utils}
|-- diagrama-arquitectura.png
|-- Makefile
|-- .env.example
`-- README.md
```

### Carpetas/ficheros principales ya completados

| Ruta | Estado | Objetivo |
|---|---|---|
| `apps/api/app/main.py` | Creado | Arranque FastAPI |
| `apps/api/app/api/v1/endpoints/*` | Creado | Endpoints base |
| `apps/api/app/modules/*` | Creado | Modulos funcionales base |
| `apps/api/app/infrastructure/llm/*` | Creado | Gateway + providers |
| `infra/db/migrations/*.sql` | Creado | Esquema core + vectorial |
| `infra/db/seeds/001_seed_mock.sql` | Creado | Seed de POC |
| `data/diagnostic_trees/*.json` | Creado | Arboles de diagnostico |
| `data/seeds/*.json` | Creado | Datos mock JSON |
| `scripts/db/*` y `scripts/dev/*` | Creado | Operacion local |
| `apps/web/*` base | Creado | UI bootstrap |

---

## Estado actual del backend

### Endpoints disponibles

- `POST /api/v1/session/start`
- `POST /api/v1/session/message`
- `GET /api/v1/session/{session_id}`
- `POST /api/v1/session/{session_id}/feedback`
- `GET /api/v1/metrics/summary`
- `GET /api/v1/health`

### Implementado

- Router de sesion y metricas.
- Orquestador base de rutas conversacionales.
- Servicios base VIN/FAQ/Tree/Otros.
- LLM gateway Groq/OpenRouter.

### Pendiente critico

- Consolidar estado tipado de orquestacion (ORCH-01) y cerrar flujo completo ORCH-02.

---

## Diseno y creacion de BBDD (core + vectorial)

Migraciones SQL en `infra/db/migrations`:

1. `000_extensions.sql` (`pgcrypto`, `vector`)
2. `001_core_schema.sql`
3. `002_core_indexes.sql`
4. `003_vector_schema.sql`
5. `004_metrics_views.sql`
6. `005_hardening_and_vector_ops.sql`
7. `006_decision_logs_confidence.sql`

### ER simplificado (core)

```mermaid
erDiagram
  VEHICLES ||--o{ SESSIONS : has
  SESSIONS ||--|| SESSION_STATE : has
  SESSIONS ||--o{ MESSAGES : logs
  SESSIONS ||--o{ DECISION_LOGS : traces
  SESSIONS ||--o| FEEDBACK : gets
```

### Tablas core

| Tabla | Funcion |
|---|---|
| `vehicles` | Catalogo de bastidores y metadatos |
| `sessions` | Cabecera de sesion de diagnostico |
| `session_state` | Estado vivo de la conversacion/diagnostico |
| `messages` | Registro de mensajes usuario/asistente |
| `decision_logs` | Registro de decisiones por modulo (incluye `confidence` por turno) |
| `feedback` | Evaluacion final |
| `faqs` | FAQ por modelo/categoria |
| `diagnostic_trees` | Arboles JSON versionados |
| `historical_cases` | Casos historicos para apoyo en Otros |

### Capa vectorial

#### `knowledge_chunks`
- Fuente unificada (`faq`, `historical_case`, `tree_node`)
- `embedding vector(1024)` + `tsvector lexical`
- `embedding_status` (`pending`, `ready`, `failed`)
- `embedding_provider`, `embedding_model`, `metadata`

#### `embedding_jobs`
- Cola para generar embeddings de forma asincrona
- Reintentos y registro de ultimo error

### Retrieval hibrido

Funcion SQL `hybrid_search(...)`:
- score vectorial + lexical ponderado
- filtro por modelo/sintoma con fallback global
- salida top candidatos para ranking de hipotesis

### Hardening aplicado

- Constraints de estados y rangos.
- Controles de no negativos.
- Indices HNSW/GIN/BTREE.
- Triggers `updated_at`.

---

## Datos iniciales cargados

### Seed SQL

`infra/db/seeds/001_seed_mock.sql`:
- 4 VIN mock
- 4 FAQ
- 5 casos historicos
- 2 arboles (`AK550_PARADAS_V1`, `AK550_CELP_V1`)

### JSON y prompts

- `data/seeds/vehicles.json`
- `data/seeds/faqs.json`
- `data/seeds/historical_cases.json`
- `data/diagnostic_trees/AK550_PARADAS_V1.json`
- `data/diagnostic_trees/AK550_CELP_V1.json`
- `data/prompts/free_text_parser.system.txt`
- `data/prompts/response_builder.system.txt`

---

## Arranque local

### 1) Variables de entorno

Copiar `.env.example` a `.env` y completar:
- `GROQ_API_KEY`
- `OPENROUTER_API_KEY`

### 2) Base de datos

```bash
make db-up
make db-migrate
make db-seed
```

### 3) Backend

```bash
make api-install
make api-run
```

### 4) Frontend

```bash
make web-install
make web-run
```

---

## Cronograma de trabajo por tareas

### Estado general

- Completado: estructura base, migraciones, seed, persistencia SQL core y validacion E2E backend.
- Siguiente foco: orquestacion tipada (ORCH-01/02), cierre de modulos diagnostico y QA/release.

### Fases

| Fase | Objetivo | Tareas |
|---|---|---|
| F1 | Persistencia real | BE-01, BE-02, BE-03, BE-04 |
| F2 | Orquestacion completa | ORCH-01, ORCH-02 |
| F3 | Modulos diagnostico | TREE-01, FAQ-01, OTH-01..OTH-04 |
| F4 | API y UI E2E | API-01, API-02, FE-01 |
| F5 | Calidad y release | QA-01, REL-01 |

### Backlog detallado

> Objetivo de este backlog: **demo 100% funcional para portfolio GitHub**, priorizando rapidez y estabilidad con Groq/OpenRouter en plan gratuito.

| ID | Fase | Bloque | Tarea | Estado | Entregable | Depende de |
|---|---|---|---|---|---|---|
| BE-01 | F1 | Persistencia | Repositorios SQL para `sessions` y `session_state` | ✅ Hecho | Estado real en BD | PLAT-01 |
| BE-02 | F1/F4 | Persistencia/API | Repositorios SQL para `messages`, `decision_logs`, `feedback` | ✅ Hecho | Trazabilidad persistente | BE-01 |
| BE-03 | F1 | Persistencia | Repositorios SQL para `vehicles`, `faqs`, `diagnostic_trees`, `historical_cases` | ✅ Hecho | Lectura de conocimiento real | BE-01 |
| BE-04 | F1 | Persistencia | Sustituir in-memory en `SessionUseCases` | ✅ Hecho | Casos de uso DB-backed | BE-01, BE-02 |
| ORCH-01 | F2 | Orquestacion | Estado tipado de LangGraph | ✅ Hecho | Contrato de flujo estable | BE-04 |
| ORCH-02 | F2 | Orquestacion | Grafo completo (VIN/menu/FAQ/tree/otros/response) | ✅ Hecho | Orquestador productivo | ORCH-01 |
| TREE-01 | F3 | Arbol | Ejecucion real desde `diagnostic_trees` | ✅ Hecho | Diagnostico guiado real | BE-03, ORCH-02 |
| FAQ-01 | F3 | FAQ | Matcher final por modelo + fallback general | ✅ Hecho | FAQ operativa final | BE-03, ORCH-02 |
| OTH-01 | F3 | Otros | Parsing libre (reglas + LLM) con Groq/OpenRouter | ✅ Hecho | Tags/categoria robusta en demo | ORCH-02 |
| OTH-02 | F3 | Otros | Ingestion de `knowledge_chunks` | ⬜ Pendiente | Corpus vectorial inicial | BE-03 |
| OTH-03 | F3 | Otros | Worker de `embedding_jobs` | ⬜ Pendiente | Embeddings operativos | OTH-02 |
| OTH-04 | F3 | Otros | Retrieval `hybrid_search` + top-3 definitivo | ⬜ Pendiente | Modulo Otros completo | OTH-03 |
| API-01 | F4 | API | Endpoints conectados al orquestador completo + BD real | ⬜ Pendiente | API E2E final | ORCH-02, BE-04 |
| API-02 | F4 | API | `/metrics/summary` desde `v_metrics_summary` | ✅ Hecho | KPIs reales | BE-02 |
| FE-01 | F4 | Frontend | Chat completo + salida estandar | ⬜ Pendiente | UX demo completa | API-01 |
| QA-01 | F5 | QA | Unit + integration + e2e (CA-001..CA-010) | ⬜ Pendiente | Validacion tecnica de demo | FE-01, API-02 |
| REL-01 | F5 | Release | Checklist final de entrega | ⬜ Pendiente | Demo estable publicable | QA-01 |

### Tareas manuales tuyas (detalle por fase, solo lo no automatizable aqui)

| Fase | Tarea manual (tuya) | Detalle operativo recomendado para demo profesional |
|---|---|---|
| F1 | Gestion de secretos locales | 1) Crear `.env` local con `GROQ_API_KEY` y `OPENROUTER_API_KEY`. 2) No commitear nunca `.env` (solo `.env.example`). 3) Probar arranque con claves reales y dejar notas de setup en README. |
| F2 | Cierre funcional del flujo | 1) Validar contigo mismo el guion final de demo (VIN->menu->FAQ/Tree/Otros->feedback). 2) Definir textos exactos que vas a enseñar en la demo. 3) Congelar contrato de estados para evitar cambios de ultima hora. |
| F3 | Alta y uso free-tier Groq/OpenRouter | 1) Crear cuentas gratuitas y generar API keys. 2) Configurar modelos low-cost/free en `.env`. 3) Definir fallback (Groq primario, OpenRouter secundario). 4) Fijar limites de tokens/timeout para no agotar cuota durante demos. 5) Probar prompts reales con 10-20 ejemplos y guardar los casos que fallan para iterar. |
| F3 | Control de coste/cuota para demos | 1) Preparar un modo “demo segura” (prompts cortos, max tokens bajo). 2) Revisar consumo antes de cada presentacion. 3) Tener un plan B sin LLM (respuestas guiadas) si la cuota se agota. |
| F4 | Publicacion de demo en nube | 1) Crear proyecto en Vercel (web) y Render/Fly/Railway (api). 2) Configurar variables de entorno en plataforma. 3) Conectar DB gestionada o tunel seguro. 4) Verificar dominio, HTTPS y CORS. 5) Ejecutar smoke test desde URL publica. |
| F4 | Presentacion en GitHub | 1) Preparar `README` con GIF/capturas del flujo completo. 2) Documentar comandos de arranque en 5 minutos. 3) Añadir seccion “Arquitectura y decisiones” para recruiters. |
| F5 | Checklist de release demo | 1) Ejecutar bateria E2E final justo antes de publicar. 2) Comprobar que las claves no aparecen en logs/commits. 3) Etiquetar version (`v0.x-demo`) y dejar changelog corto. 4) Publicar enlace de demo y video corto (1-3 min). |

### Siguiente tarea concreta

**OTH-02**: ingestion de `knowledge_chunks` para inicializar corpus vectorial.

---

## Criterios de cierre POC

La POC se considera cerrada cuando:

- VIN obligatorio se respeta en todo flujo.
- `session_state` es fuente de verdad real en BD.
- FAQ, Tree y Otros funcionan con trazabilidad completa.
- Otros devuelve top-3 por modelo usando retrieval hibrido.
- UI y API cubren flujo completo hasta feedback.
- Se cumplen CA-001..CA-010 del DDT.

---

## Instrucciones para la siguiente sesion

1. Leer este `README.md` completo.
2. Continuar por **OTH-02**.
3. Mantener foco en:
   - estado en BD,
   - trazabilidad (`messages`, `decision_logs`),
   - contrato de salida estandar.
