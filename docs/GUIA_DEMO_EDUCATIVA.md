# Guía Educativa — Asistente de Diagnóstico Inteligente para Motocicletas

## ¿Qué hace esta aplicación?

Imagina un **asistente virtual especializado en mecánica de motocicletas**. El usuario introduce el número de bastidor (VIN) de su moto, y el asistente le hace preguntas para averiguar qué problema tiene. No es un chat libre como ChatGPT: el asistente **guía** la conversación paso a paso, usando conocimiento técnico real almacenado en una base de datos.

---

## El flujo de la conversación (paso a paso)

```
Bienvenida → Introducir bastidor → Elegir modo de consulta → Diagnóstico → Feedback
```

### 1. Pantalla de bienvenida
El usuario llega a la aplicación y ve una pantalla con el logotipo y un campo para introducir el **bastidor (VIN)** de la motocicleta. El VIN es un código único de 17 caracteres que identifica cada vehículo.

### 2. Identificación del vehículo
Al introducir el VIN, el sistema busca en su base de datos interna qué modelo de moto es. Si lo encuentra, responde algo como:

> *"He identificado el vehículo como AK550 (2022). Selecciona una opción: Síntomas frecuentes, Consultas frecuentes u Otros."*

Si el VIN no está registrado, pide que lo intenten de nuevo.

### 3. Elegir cómo se quiere diagnosticar
Aquí el usuario elige **cómo** quiere describir el problema. Hay tres caminos distintos:

| Opción | ¿Qué hace? | ¿Cuándo usarlo? |
|--------|-----------|-----------------|
| **Síntomas frecuentes** | Un árbol de preguntas sí/no | Cuando el síntoma es común y conocido |
| **Consultas frecuentes (FAQ)** | Busca en una lista de preguntas típicas | Cuando el usuario recuerda una pregunta concreta |
| **Otros** | Usa inteligencia artificial para analizar el texto libre | Cuando el problema es raro o el usuario no sabe qué opción elegir |

---

## El cerebro que orquesta: LangGraph

Para entender cómo la aplicación decide **qué hacer en cada momento**, hay que conocer **LangGraph**. Piensa en LangGraph como un **director de orquesta**: recibe el mensaje del usuario, mira en qué punto está la conversación, y decide qué "músico" (módulo) debe tocar.

### ¿Qué es un grafo?

Un **grafo** es una estructura formada por **nodos** (cajitas) y **flechas** (conexiones). Cada nodo hace una tarea concreta, y las flechas indican qué nodo se ejecuta después. En nuestro caso:

```
                     ┌─────────────────────┐
                     │   INICIO (START)    │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │  El "director" de   │
                     │  ruta decide qué    │
                     │  nodo ejecutar      │
                     └──┬──┬──┬──┬──┬──┬──┘
                        │  │  │  │  │  │
         ┌──────────────┘  │  │  │  │  └──────────────┐
         ▼                 ▼  ▼  ▼  ▼                 ▼
   ┌──────────┐    ┌────────┐ ┌──────┐ ┌──────────┐ ┌──────────┐
   │ VIN      │    │ Árbol  │ │ FAQ  │ │ Texto    │ │ Finalizar│
   │ Lookup   │    │ (tree) │ │(faq) │ │ Libre    │ │Diagnóstico│
   └──────────┘    └────────┘ └──────┘ └──────────┘ └──────────┘
        │              │         │          │              │
        └──────────────┴─────────┴──────────┴──────────────┘
                                │
                                ▼
                      ┌──────────────────┐
                      │      FIN (END)   │
                      └──────────────────┘
```

### Los 7 nodos (músicos) del grafo

| Nodo | ¿Qué hace? | ¿Cuándo se activa? |
|------|-----------|-------------------|
| **`vin_lookup`** | Busca el VIN en la base de datos | Cuando el usuario aún no ha identificado su moto |
| **`tree_engine`** | Navega por el árbol de diagnóstico | Cuando el usuario elige "Síntomas frecuentes" o su entrada_point es "tree" |
| **`faq_matcher`** | Busca la pregunta en la lista de FAQs | Cuando el usuario elige "Consultas frecuentes" o su entrada_point es "faq" |
| **`free_text_parser`** | Analiza el texto libre con IA + búsqueda | Cuando el usuario elige "Otros" o escribe libremente |
| **`menu_selection`** | Muestra el menú de opciones | Cuando el usuario pide "Volver al menú" |
| **`out_of_scope`** | Informa que la consulta no está cubierta | Cuando el mensaje no coincide con nada conocido |
| **`finish_diagnosis`** | Limpia el estado y finaliza el diagnóstico | Cuando el usuario dice "Finalizar diagnóstico" |

### ¿Cómo decide el director qué nodo ejecutar?

Cada vez que el usuario envía un mensaje, el "director" (la función **`_route_turn`**) aplica estas reglas en orden:

1. **¿No hay VIN?** → Ve al nodo `vin_lookup` (pide el bastidor)
2. **¿El usuario dijo "finalizar"?** → Ve a `finish_diagnosis`
3. **¿El usuario dijo "volver al menú"?** → Ve a `menu_selection`
4. **¿Dijo "síntomas frecuentes"?** → Ve a `tree_engine`
5. **¿Dijo "consultas frecuentes"?** → Ve a `faq_matcher`
6. **¿Dijo "otros"?** → Ve a `free_text_parser`
7. **¿Estaba en medio de un árbol/FAQ/otros?** → Vuelve al mismo nodo
8. **¿No hay ninguna pista?** → Ve a `free_text_parser` (intenta adivinar)
9. **Si nada de lo anterior funciona** → Ve a `out_of_scope`

### ¿Qué es el "estado de la conversación"?

Cuando hablas con el asistente, él guarda un **estado** en la base de datos. Es como una ficha que contiene:

- **VIN** y **modelo** de la moto
- **Síntoma actual** (ej: "Paradas de motor")
- **Nodo actual** (en qué paso del árbol estás)
- **entry_point** (en qué modo estás: tree, faq, u other)
- **Preguntas ya hechas** (para no repetir)

Este estado es la **fuente de verdad** del sistema. Cada mensaje pasa por LangGraph, que consulta y actualiza este estado. Así, si el usuario se va y vuelve, la conversación continúa exactamente donde la dejó.

### ¿Por qué LangGraph y no un simple `if-else`?

Porque el grafo permite:
- **Añadir nuevos nodos** sin romper los existentes (ej: añadir un nodo de "búsqueda por imagen")
- **Trazabilidad**: cada decisión se registra (qué nodo, qué entrada, qué salida, qué confianza)
- **Múltiples rutas**: el director puede decidir cosas complejas, como "si el FAQ falla y hay texto libre, intenta con IA"

---

## ¿Cómo llega el asistente a un diagnóstico? (El corazón de la app)

El asistente tiene **tres fuentes de conocimiento** para diagnosticar. Puedes pensar en ellas como tres libros de mecánica diferentes:

### 🔹 Árboles de decisión (Síntomas frecuentes)

Un **árbol de decisión** es como un cuestionario de preguntas sí/no que sigue una rama según las respuestas:

```
¿El motor se para?
  ├── Sí → ¿Se escucha la bomba de gasolina?
  │        ├── Sí → ¿Arranca después de enfriar?
  │        │        ├── Sí → Diagnóstico: Reglaje de válvulas
  │        │        └── No → Diagnóstico: Agua en el depósito
  │        └── No → Diagnóstico: Bomba de gasolina defectuosa
  └── No → ¿Al apagar y encender funciona?
           ├── Sí → Diagnóstico: Sensor de inclinación defectuoso
           └── No → ...
```

**¿Cómo funciona?**
1. El usuario selecciona un síntoma (ej: "Paradas de motor")
2. El sistema encuentra el árbol correspondiente para ese modelo y síntoma en la base de datos
3. Empieza con la primera pregunta y el usuario responde "sí" o "no" (el sistema también entiende "vale", "ok", "sí" con tilde, etc. — tiene un **diccionario de sinónimos**)
4. Según la respuesta, avanza por una rama del árbol
5. Cuando llega a una **hoja** del árbol, muestra el diagnóstico final

**Ventaja:** Es rápido, predecible y no necesita internet.
**Limitación:** Solo cubre los síntomas que se han programado previamente.

### 🔹 Preguntas Frecuentes (FAQ)

Es una base de datos con preguntas y respuestas típicas, como:

| Pregunta | Respuesta |
|----------|-----------|
| "¿Cada cuánto cambiar las bujías?" | Revisar cada 1000 km, cambiar cada 3000-5000 km |
| "Sale humo negro del escape" | Mezcla rica, limpiar inyector o revisar sensor lambda |
| "La moto se para al pasar baches" | Sensor de inclinación defectuoso o suspensión desgastada |

**¿Cómo funciona?**
1. El usuario escribe una pregunta (o la selecciona de las sugeridas)
2. El sistema **compara** las palabras de la pregunta con las de su base de datos
3. Para ello, separa el texto en **tokens** (palabras individuales), elimina palabras vacías como "la", "el", "de", y calcula cuánto coinciden usando una fórmula de **solapamiento de tokens** (token overlap)
4. Si el texto coincide mucho con una pregunta específica del modelo (>25%) o con una pregunta general (>28%), devuelve esa respuesta
5. Si no hay coincidencia, sugiere preguntas parecidas para guiar al usuario

**Ventaja:** Responde rápidamente preguntas concretas muy habituales.
**Limitación:** Solo funciona si la pregunta es parecida a alguna ya registrada.

### 🔹 Texto libre con inteligencia artificial (Otros)

Cuando el usuario describe el problema con sus propias palabras —sin limitarse a un menú— el sistema activa su **módulo más complejo**. Analicémoslo archivo por archivo, desde que el usuario pulsa Enter hasta que ve el diagnóstico.

---

### 🧭 Mapa del módulo Otros (vista general)

```
Usuario escribe: "La moto se para en caliente"
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  1. apps/api/app/application/orchestrator/langraph_flow.py   │
│     _node_free_text_parser() — El director de orquesta       │
│     (línea 580)                                              │
└────────────────────────────────┬─────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────┐
│  2. apps/api/app/modules/free_text_parser/service.py         │
│     FreeTextParserService.parse() — Clasifica el síntoma     │
│     ├── ¿Hay IA? → _parse_with_llm() → Groq o OpenRouter    │
│     │     ├── Construye el prompt con la taxonomía           │
│     │     ├── Llama al LLM (system prompt + user prompt)     │
│     │     ├── Extrae el JSON de la respuesta                 │
│     │     └── Valida que la categoría exista en taxonomía    │
│     └── ¿Fallo? → _parse_with_rules() → palabras clave      │
└────────────────────────────────┬─────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────┐
│  3. apps/api/app/infrastructure/retrieval/embeddings.py      │
│     EmbeddingService.embed() — Texto → Vector numérico       │
│     ├── ¿Hay API key? → OpenRouter (bge-m3, 1024 números)   │
│     └── ¿Sin conexión? → SHA-256 (placeholder determinista)  │
└────────────────────────────────┬─────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────┐
│  4. apps/api/app/infrastructure/db/repositories/             │
│     knowledge_repository.py                                  │
│     KnowledgeRepository.search_hybrid() — Búsqueda híbrida   │
│     ├── Llama a la función SQL hybrid_search()               │
│     ├── 75% semántica (coseno entre vectores)                │
│     ├── 25% léxica (tsvector + websearch_to_tsquery)         │
│     └── Devuelve objetos RetrievalCandidate                  │
└────────────────────────────────┬─────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────┐
│  5. apps/api/app/modules/hybrid_ranking/service.py            │
│     HybridRankingService.rank() — Ordena por puntuación      │
│     Fórmula: 55% vector + 20% léxico + 15% modelo + 10% base│
│     Devuelve top 3 hipótesis                                 │
└────────────────────────────────┬─────────────────────────────┘
                                 │
           ┌─────────────────────┴─────────────────────┐
           ▼                                           ▼
┌──────────────────────────┐    ┌──────────────────────────────┐
│  ¿Confianza ≥ 35%?       │    │  ¿Sin candidatos históricos? │
│  → Muestra hipótesis     │    │  → FAQMatcherService.match() │
│    principal + alternat. │    │    (apps/api/app/modules/    │
│                          │    │     faq_matcher/service.py)  │
└──────────────────────────┘    └──────────────┬───────────────┘
                                                ▼
                                     ¿FAQ coincide?
                                     ├── Sí → Muestra respuesta FAQ
                                     └── No → "No tengo suficiente info"
```

---

## Paso a paso, archivo por archivo

---

### 🔹 Paso 1: El director de orquesta — `langraph_flow.py`

> **Archivo:** `apps/api/app/application/orchestrator/langraph_flow.py`
> **Método:** `_node_free_text_parser` (línea 580)

Cuando el usuario escribe "Otros" (o simplemente describe un problema sin haber elegido nada), LangGraph activa este nodo. Es el **director** que coordina todo el flujo. Esto es lo que hace, paso a paso:

**1. Configura el modo de la conversación:**
```python
state["entry_point"] = "other"
```
Marca que el usuario está en el modo "Otros", para que los siguientes mensajes sigan en este mismo flujo.

**2. Limpia el estado del árbol (si venía de otro lado):**
```python
if state["current_node"] or state["current_symptom"]:
    state["state_updates"]["current_node"] = None
    state["state_updates"]["current_symptom"] = None
```
Si el usuario antes estaba en un árbol de diagnóstico y ahora dice "Otros", se borran los datos del árbol para que no interfieran.

**3. Detecta si solo dijo "Otros" sin describir el problema:**
```python
if state["normalized_message"] in {"otros", "otra consulta", "texto libre"}:
```
Si el mensaje es solo la palabra "Otros", el sistema responde: *"Describe el problema con tus palabras para analizarlo en la vía Otros."* con confianza 0.2 y botones para ir a Síntomas frecuentes o FAQ. Devuelve `result: "awaiting_free_text"`.

**4. Llama al clasificador de texto libre (FreeTextParserService):**
```python
parsed = self._parse_free_text(state["user_message"])
```
Aquí es donde ocurre la **magia**. Se pasa el texto original del usuario al FreeTextParserService (que veremos en detalle en el Paso 2). El resultado es un objeto `ParsedFreeText` que contiene:
- `normalized_text`: el texto limpio (sin acentos, minúsculas)
- `tags`: etiquetas técnicas como `["hot_engine", "fuel_pump"]`
- `symptom_category`: la categoría del síntoma (ej: "Paradas de motor") o `None`
- `reasoning_short`: una breve explicación de cómo se clasificó
- `parser_source`: `"llm"`, `"rules"`, o `"rules_fallback"`

**5. Verifica que el modelo de moto sea conocido:**
```python
if not state["model"]:
```
Si aún no se ha identificado el vehículo (no hay VIN registrado), el sistema pide más detalles y devuelve `result: "model_missing"`.

**6. Convierte el texto a vector (EmbeddingService):**
```python
query_embedding = self._embed_text(parsed.normalized_text or query_text)
```
Llama al servicio que convierte el texto en un vector de números (Paso 3).

**7. Busca casos históricos (búsqueda híbrida):**
```python
candidates = self._hybrid_search(
    query_embedding=query_embedding,
    query_text=query_text,
    model=state["model"],
    symptom=parsed.symptom_category,
    limit=12,
)
```
Busca en la base de datos hasta 12 candidatos que tengan un significado parecido al texto del usuario (Paso 4).

**8. Filtra candidatos débiles:**
```python
min_score_threshold = 0.25
filtered_candidates = [
    c for c in candidates
    if c.vector_score >= min_score_threshold or c.lexical_score >= min_score_threshold
]
```
Descarta candidatos con puntuaciones muy bajas (ambas < 0.25). No vale la pena considerarlos.

**9. Prefiere casos históricos reales:**
```python
preferred = [candidate for candidate in filtered_candidates if candidate.source_type == "historical_case"]
```
Separa los que son casos históricos reales del resto. Si no hay ninguno:
- Intenta con **FAQ** como plan de respaldo (`_faq_match`)
- Si la FAQ coincide, devuelve ese resultado con `result: "faq_fallback"`
- Si la FAQ tampoco coincide, `ranked = []` → va al guardarraíl de "evidencia débil"

**10. Ordena por relevancia (HybridRankingService):**
```python
ranked = self._rank_hypotheses(preferred, 3)
```
Toma los mejores candidatos y los ordena con una fórmula matemática (Paso 6). Se queda con el top 3.

**11. Decisión final: ¿confianza suficiente?**
```python
min_confidence_threshold = 0.35
if ranked and ranked[0].score >= min_confidence_threshold:
```
- **Sí** (≥ 0.35): construye un diagnóstico con `_build_diagnostic_output()` y lo muestra al usuario con la hipótesis principal y alternativas. Añade botones de "Finalizar diagnóstico", "Síntomas frecuentes", "Consultas frecuentes".
- **No** (< 0.35): explica que no tiene suficiente información y sugiere usar FAQ o árbol. Devuelve `result: "weak_evidence"`.

La función `_build_diagnostic_output()` (línea 783) es la que da **formato a la respuesta final** siguiendo el contrato del sistema:
```python
{
    "primary_hypothesis": "Bomba de gasolina defectuosa",
    "alternatives": ["Filtro obstruido"],
    "next_check": "Verificar hipotesis principal: Bomba de gasolina defectuosa.",
    "short_explanation": "...",
    "confidence": 0.78   # (siempre entre 0.0 y 1.0)
}
```
La confianza se "clampa" (recorta) entre 0.0 y 1.0 con `max(0.0, min(confidence, 1.0))` para asegurar que nunca dé un valor inválido.

---

### 🔹 Paso 2: Clasificar el síntoma — `free_text_parser/service.py`

> **Archivo:** `apps/api/app/modules/free_text_parser/service.py`
> **Clase:** `FreeTextParserService`
> **Método principal:** `parse(text)`

Este archivo es el que **entiende lo que escribió el usuario**. Tiene dos estrategias: una con inteligencia artificial (Groq/OpenRouter) y otra con reglas locales (palabras clave).

---

#### 📋 2A. El método `parse(text)` — la entrada al módulo

```python
def parse(self, text: str) -> ParsedFreeText:
    normalized = self._normalize(text)
    if self._llm_gateway is not None:
        try:
            return self._parse_with_llm(text, raw_text, normalized)
        except (RuntimeError, httpx.HTTPError, json.JSONDecodeError, ValueError) as exc:
            # Si falla, usa reglas locales
            return self._parse_with_rules(normalized)
    return self._parse_with_rules(normalized)
```

**Flujo:**
1. Normaliza el texto (quita acentos, mayúsculas, caracteres raros).
2. Si hay un gateway de IA configurado → intenta con LLM.
3. Si el LLM falla (error de conexión, JSON inválido, timeout) → cae en reglas locales.
4. Si no hay gateway IA → directamente reglas locales.

---

#### 📋 2B. `_normalize(text)` — limpieza del texto

```python
@staticmethod
def _normalize(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())
```

**¿Qué hace exactamente?**
1. `text.lower()` → todo a minúsculas: `"La Moto"` → `"la moto"`
2. `unicodedata.normalize("NFKD", text)` → separa caracteres acentuados en dos: por ejemplo, `"é"` se convierte en `"e"` + un carácter de acento combinante invisible
3. `"".join(...)` → elimina los caracteres de acento combinante, dejando solo la letra base: `"é"` → `"e"`
4. `re.sub(r"[^a-z0-9\s]", " ", text)` → reemplaza todo lo que no sea letra, número o espacio por un espacio
5. `" ".join(text.split())` → colapsa espacios múltiples en uno solo

**Ejemplo real:**
```
"La moto se para en caliente!!!" 
→ "la moto se para en caliente"
```

```
"¿Por qué no arranca mi AK550?"
→ "por que no arranca mi ak550"
```

---

#### 📋 2C. El sistema prompt (las instrucciones que recibe la IA)

> **Archivo:** `data/prompts/free_text_parser.system.txt`

Este archivo contiene las **instrucciones permanentes** que se le dan al modelo de lenguaje. Es el "rol" que debe adoptar la IA:

```
Eres un clasificador tecnico de averias para motocicletas.
Tu tarea es:
1) Extraer tags tecnicos.
2) Identificar categoria de sintoma.
3) Devolver JSON valido con campos: tags, symptom_category, reasoning_short.
No inventes diagnosticos finales.
```

Este prompt se carga al iniciar el servicio:
```python
@staticmethod
def _load_system_prompt() -> str:
    root = Path(__file__).resolve().parents[5]
    prompt_path = root / "data" / "prompts" / "free_text_parser.system.txt"
    return prompt_path.read_text(encoding="utf-8").strip()
```

**¿Qué significa `parents[5]`?** El archivo `service.py` está en:
```
apps/api/app/modules/free_text_parser/service.py
```
Subir 5 niveles con `parents[5]` lleva a la raíz del proyecto:
```
1. apps/api/app/modules/free_text_parser/  (parents[1] = modules)
2. apps/api/app/modules/                     (parents[2] = app)
3. apps/api/app/                              (parents[3] = api)
4. apps/api/                                   (parents[4] = apps)
5. apps/                                        (parents[5] = raíz del proyecto)
```

---

#### 📋 2D. `_build_taxonomy_prompt()` — la lista de categorías válidas

```python
def _build_taxonomy_prompt(self) -> str:
    all_categories = (
        self._taxonomy.get("tree_symptoms", []) +
        self._taxonomy.get("faq_categories", []) +
        self._taxonomy.get("case_categories", [])
    )
    unique_categories = sorted(set(all_categories))
    if not unique_categories:
        return "Categorias disponibles: ninguna (usa null para symptom_category)."
    categories_str = ", ".join(unique_categories)
    return f"Categorias de sintoma disponibles: {categories_str}."
```

Esta función junta **todas las categorías de síntoma** que existen en el sistema (tanto de árboles como de FAQs y de casos históricos), las ordena alfabéticamente, y genera un texto como:

> `"Categorias de sintoma disponibles: Dificultad de arranque, Frenos, Paradas de motor, Refrigeracion, Testigo CELP encendido."`

Esto se inyecta en el prompt para que la IA **solo pueda elegir entre categorías que realmente existen** en el sistema.

La taxonomía se establece antes de cada turno con:
```python
def set_taxonomy(self, taxonomy):
    self._taxonomy = taxonomy
```
que es llamado por `SessionUseCases` con los datos obtenidos de `KnowledgeRepository.build_symptom_taxonomy()`.

---

#### 📋 2E. `_parse_with_llm(raw_text, normalized)` — el corazón de la clasificación por IA

```python
def _parse_with_llm(self, raw_text: str, normalized: str) -> ParsedFreeText:
    taxonomy_str = self._build_taxonomy_prompt()
    llm_prompt = (
        "Texto del usuario:\n"
        f"{raw_text}\n\n"
        f"{taxonomy_str}\n"
        "Devuelve exclusivamente un JSON con campos:\n"
        "{\n"
        '  "tags": ["tag1","tag2"],\n'
        '  "symptom_category": <una de las categorias arriba, o null si no aplica>,\n'
        '  "reasoning_short": "razon breve"\n'
        "}\n"
        "Importante: symptom_category SOLO puede ser null o una de las categorias listadas."
    )
    raw = self._llm_gateway.complete(prompt=llm_prompt, system_prompt=self._system_prompt)
    data = self._extract_json(raw)
    # ... extrae tags, category, reasoning del JSON ...
    return ParsedFreeText(
        normalized_text=normalized,
        tags=tags,
        symptom_category=symptom_category,
        reasoning_short=reasoning_short,
        parser_source="llm",
    )
```

**El prompt completo que recibe la IA se construye así:**

```
System prompt:
"Eres un clasificador tecnico de averias para motocicletas.
 Tu tarea es:
 1) Extraer tags tecnicos.
 2) Identificar categoria de sintoma.
 3) Devolver JSON valido con campos: tags, symptom_category, reasoning_short.
 No inventes diagnosticos finales."

User prompt:
"Texto del usuario:
La moto se para en caliente cuando ando en baches

Categorias de sintoma disponibles: Dificultad de arranque, Frenos, Paradas de motor, Refrigeracion, Testigo CELP encendido.
Devuelve exclusivamente un JSON con campos:
{
  "tags": ["tag1","tag2"],
  "symptom_category": <una de las categorias arriba, o null si no aplica>,
  "reasoning_short": "razon breve"
}
Importante: symptom_category SOLO puede ser null o una de las categorias listadas."
```

**¿Qué pasaría si el usuario escribe en inglés?** Como el sistema prompt está en español y las categorías están en español, la IA entendería igual (los LLMs son multilingües). Pero el sistema está diseñado para español.

---

#### 📋 2F. `_llm_gateway.complete()` — cómo se envía la petición a la IA

Aquí ocurre la llamada real a un servicio externo. El gateway está definido en:

> **Archivo:** `apps/api/app/infrastructure/llm/gateway.py`

```python
class LLMGateway:
    def __init__(self, primary: LLMProvider, fallback: LLMProvider):
        self.primary = primary    # GroqProvider (intento principal)
        self.fallback = fallback  # OpenRouterProvider (respaldo)

    def complete(self, prompt: str, system_prompt: str | None = None) -> str:
        try:
            return self.primary.complete(prompt=prompt, system_prompt=system_prompt)
        except Exception as exc:
            logger.warning("LLM primary failed, switching to fallback", ...)
            return self.fallback.complete(prompt=prompt, system_prompt=system_prompt)
```

**Primero intenta con Groq** (el proveedor principal). Groq tiene chips especializados (LPU) que ejecutan modelos de lenguaje a velocidades increíbles (hasta 1000 tokens/segundo). El modelo usado es `llama-3.1-8b-instant`.

**Si Groq falla** (error de red, timeout, clave API inválida), automáticamente intenta con **OpenRouter** como respaldo. OpenRouter usa el modelo `llama-3.1-8b-instruct`.

**Si ambos fallan**, el gateway lanza una excepción que es capturada por `parse()`, y entonces se usan las reglas locales.

---

#### 📋 2G. `GroqProvider.complete()` — la llamada HTTP real

> **Archivo:** `apps/api/app/infrastructure/llm/providers/groq.py`

```python
class GroqProvider:
    def __init__(self):
        settings = get_settings()
        self._api_key = settings.groq_api_key
        self._model = settings.groq_model        # "llama-3.1-8b-instant"
        self._timeout = settings.request_timeout_seconds
        self._url = "https://api.groq.com/openai/v1/chat/completions"

    def complete(self, prompt: str, system_prompt: str | None = None) -> str:
        if not self._api_key:
            raise RuntimeError("GROQ_API_KEY no configurada")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": 0       # ← Importante: temperatura 0 = siempre la misma respuesta
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(self._url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"]
```

**¿Qué es `temperature=0`?** Controla la creatividad de la IA. Cuanto más baja la temperatura, más determinista es la respuesta. Con temperatura 0, el modelo siempre dará la misma respuesta para la misma entrada. Esto es importante para un sistema de diagnóstico —no queremos que invente cosas diferentes cada vez.

**El payload JSON que se envía a Groq es:**
```json
{
  "model": "llama-3.1-8b-instant",
  "messages": [
    {
      "role": "system",
      "content": "Eres un clasificador tecnico de averias para motocicletas..."
    },
    {
      "role": "user",
      "content": "Texto del usuario:\nLa moto se para en caliente..."
    }
  ],
  "temperature": 0
}
```

**La respuesta de Groq es algo como:**
```json
{
  "choices": [
    {
      "message": {
        "content": "{\n  \"tags\": [\"hot_engine\", \"bumps\"],\n  \"symptom_category\": \"Paradas de motor\",\n  \"reasoning_short\": \"El usuario describe paradas en caliente y al pasar baches\"\n}"
      }
    }
  ]
}
```

El método extrae `data["choices"][0]["message"]["content"]` y devuelve el texto del JSON.

**OpenRouter funciona exactamente igual** pero con otra URL:
> `https://openrouter.ai/api/v1/chat/completions`

Y se configuran ambas en `session_use_cases.py` línea 52:
```python
self._llm_gateway = LLMGateway(
    primary=GroqProvider(),
    fallback=OpenRouterProvider()
)
```

---

#### 📋 2H. `_extract_json(raw_content)` — cómo se limpia la respuesta de la IA

```python
@staticmethod
def _extract_json(raw_content: str) -> dict:
    content = raw_content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if "\n" in content:
            content = content.split("\n", 1)[1]
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No se encontro JSON en salida LLM")
    return json.loads(content[start : end + 1])
```

**Este método es importante porque los LLM a veces devuelven el JSON envuelto en marcas de código de Markdown.** Por ejemplo, en lugar de devolver:

```
{"tags": ["hot_engine"], "symptom_category": "Paradas de motor", ...}
```

Pueden devolver:

```json
{"tags": ["hot_engine"], "symptom_category": "Paradas de motor", ...}
```

El método `_extract_json` **limpia esa envoltura**:

1. **Quita espacios** al inicio y final con `.strip()`
2. **Detecta si empieza con ```** (marca de código) y la elimina
3. Si hay un salto de línea después de ```, lo separa y se queda con la segunda parte
4. **Busca el primer `{`** y el **último `}`**
5. Si no encuentra ambos, o si el `}` está antes que el `{`, lanza `ValueError` (esto dispara el fallback a reglas locales)
6. **Convierte el texto JSON a diccionario Python** con `json.loads()`

---

#### 📋 2I. `_is_valid_category()` — validación de la categoría

```python
def _is_valid_category(self, category: str) -> bool:
    if not category:
        return False
    all_categories = (
        self._taxonomy.get("tree_symptoms", []) +
        self._taxonomy.get("faq_categories", []) +
        self._taxonomy.get("case_categories", [])
    )
    category_lower = category.lower().strip()
    for valid in all_categories:
        if valid and valid.lower().strip() == category_lower:
            return True
    return False
```

Aunque la IA haya respondido con una categoría, el sistema **no se fía ciegamente**. Comprueba que la categoría devuelta esté realmente en la lista de categorías válidas. Si no está, la categoría se descarta (`symptom_category = None`).

**Ejemplo:** Si el usuario dice "tengo un problema con el embrague" y la IA responde `"symptom_category": "Embrague"`, pero "Embrague" no está en la taxonomía del sistema, se ignora y se trata como si no hubiera categoría.

---

#### 📋 2J. `_parse_with_rules()` — el plan B (sin IA)

```python
def _parse_with_rules(self, normalized: str) -> ParsedFreeText:
    tags = self._infer_tags(normalized)
    symptom_category = self._infer_category(tags)
    if symptom_category and not self._is_valid_category(symptom_category):
        symptom_category = None
    return ParsedFreeText(
        normalized_text=normalized,
        tags=tags,
        symptom_category=symptom_category,
        reasoning_short="Clasificacion por reglas locales.",
        parser_source="rules",
    )
```

Cuando la IA no está disponible, el sistema usa **reglas locales** con detección de palabras clave.

---

#### 📋 2K. `_infer_tags()` — palabras clave técnicas

```python
def _infer_tags(self, text: str) -> list[str]:
    keywords = [
        ("caliente", "hot_engine"),
        ("enfr", "cold_restart"),
        ("bomba", "fuel_pump"),
        ("celp", "celp_light"),
        ("baches", "bumps"),
        ("repost", "after_refuel"),
    ]
    return [tag for token, tag in keywords if token in text]
```

Es una simple búsqueda de subcadenas (substrings): si el texto contiene la palabra "caliente", se añade la etiqueta `hot_engine`. **Nota:** "enfr" detecta tanto "enfría" como "enfríar" como "refrigeración" (porque "enfr" está dentro de esas palabras).

---

#### 📋 2L. `_infer_category()` — de etiquetas a categoría

```python
def _infer_category(self, tags: list[str]) -> str | None:
    if "celp_light" in tags:
        return "Testigo CELP encendido"
    if {"hot_engine", "fuel_pump", "after_refuel"} & set(tags):
        return "Paradas de motor"
    return None
```

Agrupa etiquetas en categorías más generales. Si hay varias etiquetas relacionadas (ej: "motor caliente" + "bomba de gasolina"), infiere que la categoría es "Paradas de motor".

---

### 🔹 Paso 3: Convertir texto en vector — `embeddings.py`

> **Archivo:** `apps/api/app/infrastructure/retrieval/embeddings.py`
> **Clase:** `EmbeddingService`
> **Método:** `embed(text)`

Para buscar casos parecidos, el sistema necesita convertir el texto del usuario en un **vector numérico** (una lista de números que representan el significado del texto).

```python
class EmbeddingService:
    def __init__(self):
        settings = get_settings()
        self._api_key = settings.openrouter_api_key
        self._model = settings.openrouter_embedding_model   # "BAAI/bge-m3"
        self._url = "https://openrouter.ai/api/v1/embeddings"

    def embed(self, text: str) -> list[float]:
        if not self._api_key:
            return self._placeholder_embed(text)
        try:
            return self._embed_via_api(text)
        except Exception:
            return self._placeholder_embed(text)
```

**Dos caminos:**

#### 📋 3A. Con API key — llamada real a OpenRouter

```python
def _embed_via_api(self, text: str) -> list[float]:
    payload = {
        "model": self._model,    # "BAAI/bge-m3"
        "input": text,
    }
    headers = {
        "Authorization": f"Bearer {self._api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=30) as client:
        response = client.post(self._url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
    return data["data"][0]["embedding"]
```

Envía una petición HTTP POST a OpenRouter:
```
POST https://openrouter.ai/api/v1/embeddings
Authorization: Bearer sk-...
Content-Type: application/json

{
  "model": "BAAI/bge-m3",
  "input": "la moto se para en caliente cuando ando en baches"
}
```

La respuesta es:
```json
{
  "data": [
    {
      "embedding": [0.0123, -0.0456, 0.0789, ...]  // 1024 números
    }
  ]
}
```

El modelo `bge-m3` (`BAAI/bge-m3`) es un modelo de embeddings de última generación que produce vectores de **1024 dimensiones**. Cada valor es un número decimal entre -1 y 1 aproximadamente.

**¿Qué significa "1024 dimensiones"?** Piensa en un punto en el espacio. Un punto en una línea tiene 1 coordenada. En un plano tiene 2. En el mundo real tiene 3. Un vector de 1024 dimensiones es un punto en un espacio de 1024 dimensiones —no podemos visualizarlo, pero las matemáticas funcionan igual. Dos textos con significados parecidos tienen puntos cercanos en ese espacio de 1024 dimensiones.

#### 📋 3B. Sin API key — placeholder SHA-256

```python
@staticmethod
def _placeholder_embed(text: str) -> list[float]:
    import hashlib
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return [digest[idx % len(digest)] / 255.0 for idx in range(1024)]
```

Si no hay clave API configurada (por ejemplo, en desarrollo), se genera un vector "de mentira" usando SHA-256. SHA-256 produce 32 bytes a partir de cualquier texto. Luego se extienden esos 32 bytes a 1024 números (simplemente repitiéndolos: `idx % 32`). El resultado es un vector **determinista** (siempre el mismo para el mismo texto), pero **no tiene significado semántico real**. Sirve para que el sistema funcione offline.

---

### 🔹 Paso 4: Búsqueda híbrida en la base de datos — `knowledge_repository.py`

> **Archivo:** `apps/api/app/infrastructure/db/repositories/knowledge_repository.py`
> **Método:** `search_hybrid()`

Este es el momento en que el sistema busca en su base de datos interna si hay **casos históricos parecidos** al texto del usuario. No busca solo por palabras, sino también por **significado**.

```python
def search_hybrid(self, *, query_embedding, query_text, model, symptom, limit=10):
    vector_literal = self._to_vector_literal(query_embedding)
    with db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT hs.chunk_id, hs.source_type, hs.source_id, hs.model,
                   hs.symptom_category, hs.text_chunk, hs.vector_score,
                   hs.lexical_score, hs.hybrid_score, kc.base_confidence
            FROM hybrid_search(
                %s::vector,          -- vector del usuario
                %s::text,            -- texto original
                %s::varchar,         -- modelo de moto
                %s::varchar,         -- categoría del síntoma
                %s::integer,         -- límite (12)
                %s::double precision, -- peso vectorial (0.75)
                %s::double precision  -- peso léxico (0.25)
            ) AS hs
            JOIN knowledge_chunks kc ON kc.chunk_id = hs.chunk_id
            """,
            (vector_literal, query_text, model, symptom, limit, 0.75, 0.25),
        )
        rows = cur.fetchall()
```

Llama a una **función SQL** llamada `hybrid_search()` que está definida dentro de la base de datos PostgreSQL. Esta función recibe 7 parámetros:

| Parámetro | Ejemplo | ¿Qué es? |
|-----------|---------|----------|
| `%s::vector` | `[0.0123, -0.0456, ...]` | El embedding del texto del usuario (1024 números) |
| `%s::text` | `"la moto se para en caliente"` | El texto original para búsqueda léxica |
| `%s::varchar` | `"AK550"` | El modelo de moto (filtro) |
| `%s::varchar` | `"Paradas de motor"` | La categoría del síntoma (filtro) |
| `%s::integer` | `12` | Número máximo de resultados |
| `0.75` | (fijo) | Peso de la búsqueda semántica |
| `0.25` | (fijo) | Peso de la búsqueda léxica |

Dentro de PostgreSQL, `hybrid_search()` hace esto:

**Búsqueda semántica (75%):**
```sql
1 - (embedding <=> query_embedding)
```
El operador `<=>` es el operador de **distancia del coseno** de pgvector. Calcula el ángulo entre el vector del chunk y el vector del texto del usuario. El resultado es un número entre 0 (idénticos) y 2 (opuestos). `1 - distancia` lo convierte en similitud: 1 = muy parecido, 0 = nada parecido.

**Búsqueda léxica (25%):**
```sql
ts_rank(lexical, websearch_to_tsquery('spanish', query_text))
```
`websearch_to_tsquery('spanish', ...)` convierte el texto del usuario en una consulta de búsqueda de texto completa en español. La columna `lexical` es un `tsvector` que precalcula las palabras de cada chunk. `ts_rank()` mide cuántas palabras coinciden.

**Fórmula híbrida final:**
```sql
(0.75 * vector_score + 0.25 * lexical_score) / (0.75 + 0.25)
```

Se filtran además por modelo y categoría de síntoma si se proporcionan.

Para convertir el vector Python a un literal que PostgreSQL entienda:
```python
@staticmethod
def _to_vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.6f}" for value in values) + "]"
```
Esto produce algo como: `[0.012345,-0.045678,0.078901,...]`

Por cada resultado, se construye un objeto `RetrievalCandidate`:
```python
RetrievalCandidate(
    case_id=str(row["chunk_id"]),
    diagnosis=diagnosis,        # extraído del texto del chunk
    vector_score=float(row["vector_score"] or 0.0),
    lexical_score=float(row["lexical_score"] or 0.0),
    model_match=model_match,    # 1.0 si coincide el modelo, 0.8 si no
    base_confidence=base_confidence,  # confianza del caso histórico
    frequency=1,
    source_type=row["source_type"],  # "historical_case", "faq", "tree_node"
    source_id=row["source_id"],
    text_chunk=row["text_chunk"],
)
```

Este `RetrievalCandidate` está definido en:

> **Archivo:** `apps/api/app/modules/historical_retrieval/service.py`

```python
@dataclass
class RetrievalCandidate:
    case_id: str
    diagnosis: str
    vector_score: float
    lexical_score: float
    model_match: float
    base_confidence: float
    frequency: int
    source_type: str
    source_id: str
    text_chunk: str | None = None
```

El **diagnóstico** se extrae del texto del chunk según su tipo de fuente:

```python
@staticmethod
def _extract_diagnosis(source_type, text_chunk):
    if source_type == "historical_case":
        # Busca "Diagnostico final: ..." en el texto
        match = re.search(r"Diagnostico final:\s*(.+)", text_chunk, re.IGNORECASE)
        if match: return match.group(1).strip()
    if source_type == "tree_node":
        # Busca "]: ..." (el texto después de la flecha)
        match = re.search(r"\]:\s*(.+)", text_chunk)
        if match: return match.group(1).strip()
    if source_type == "faq":
        # Busca "FAQ: ..." en el texto
        match = re.search(r"FAQ:\s*(.+)", text_chunk, re.IGNORECASE)
        if match: return match.group(1).strip()
    return text_chunk.strip()[:160]  # fallback: primeros 160 caracteres
```

---

### 🔹 Paso 5: El objeto que transporta los datos — `historical_retrieval/service.py`

> **Archivo:** `apps/api/app/modules/historical_retrieval/service.py`

Este archivo es pequeño pero importante. Define los dos **objetos de datos** (dataclasses) que se usan en todo el flujo de recuperación y ranking:

```python
@dataclass
class HistoricalCase:
    case_id: str
    model: str
    case_text: str
    final_diagnosis: str
    base_confidence: float
    frequency: int = 1

@dataclass
class RetrievalCandidate:
    case_id: str
    diagnosis: str
    vector_score: float
    lexical_score: float
    model_match: float
    base_confidence: float
    frequency: int
    source_type: str
    source_id: str
    text_chunk: str | None = None
```

Piensa en `RetrievalCandidate` como una **ficha de candidato** que viaja desde la base de datos hasta el ranking. Cada ficha guarda:
- **Qué** se diagnosticó (`diagnosis`)
- **Cómo** de parecido es en significado (`vector_score`)
- **Cómo** de parecido es en palabras (`lexical_score`)
- **Si** es del mismo modelo de moto (`model_match`)
- **Qué** fiabilidad tiene el caso original (`base_confidence`)
- **De dónde** viene (`source_type`: histórico, FAQ, o árbol)

---

### 🔹 Paso 6: Ordenar por relevancia — `hybrid_ranking/service.py`

> **Archivo:** `apps/api/app/modules/hybrid_ranking/service.py`
> **Clase:** `HybridRankingService`

Cuando el sistema tiene varios candidatos, necesita **ordenarlos** para quedarse con los mejores:

```python
class HybridRankingService:
    def rank(self, candidates: list[RetrievalCandidate], top_k: int = 3) -> list[RankedHypothesis]:
        ranked = [
            RankedHypothesis(
                diagnosis=c.diagnosis,
                source_case_id=c.case_id,
                score=(
                    0.55 * c.vector_score     # 55% significado
                    + 0.20 * c.lexical_score   # 20% palabras
                    + 0.15 * c.model_match     # 15% mismo modelo
                    + 0.10 * c.base_confidence # 10% fiabilidad histórica
                ),
            )
            for c in candidates
        ]
        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:top_k]
```

**La fórmula de puntuación:**

| Componente | Peso | ¿Por qué ese peso? |
|-----------|------|-------------------|
| **vector_score** (similitud semántica) | **55%** | Es el más importante porque capta el significado, no solo las palabras |
| **lexical_score** (similitud léxica) | **20%** | Aporta precisión de palabras clave |
| **model_match** (coincidencia de modelo) | **15%** | Los diagnósticos del mismo modelo de moto son más relevantes |
| **base_confidence** (confianza histórica) | **10%** | Algunos casos son más fiables que otros |

**Ejemplo de cálculo:**
```
Candidato: vector_score=0.80, lexical_score=0.60, model_match=1.0, base_confidence=0.90
Puntuación = 0.55×0.80 + 0.20×0.60 + 0.15×1.0 + 0.10×0.90
           = 0.44      + 0.12      + 0.15      + 0.09
           = 0.80
```

El resultado es un `RankedHypothesis` con el diagnóstico y la puntuación calculada.

---

### 🔹 Paso 7: Plan de respaldo (FAQ) — `faq_matcher/service.py`

> **Archivo:** `apps/api/app/modules/faq_matcher/service.py`
> **Clase:** `FAQMatcherService`

Si la búsqueda híbrida **no encuentra casos históricos** relevantes, el sistema no se rinde. Activa un **plan B**: buscar en las **preguntas frecuentes**.

```python
def match(self, model, query, faqs):
    all_faqs = list(faqs)
    model_faqs = [faq for faq in all_faqs if faq.model == model]
    global_faqs = [faq for faq in all_faqs if faq.model is None]

    best_model = self._best_match(query, model_faqs, scope="model")
    if best_model and best_model.score >= 0.25:
        return best_model

    best_global = self._best_match(query, global_faqs, scope="global")
    if best_global and best_global.score >= 0.28:
        return best_global

    return None
```

**Dos niveles de coincidencia:**
1. **FAQs específicas del modelo** (ej: solo para AK550) → umbral mínimo 0.25 (25%)
2. **FAQs generales** (válidas para cualquier modelo) → umbral mínimo 0.28 (28%, más restrictivo porque son menos precisas)

**¿Cómo se calcula la puntuación?** El método `_best_match()` hace:

```python
def _best_match(self, query, faqs, scope):
    query_tokens = set(self._tokenize(query))   # separa en palabras
    query_norm = self._normalize(query)
    best = None
    for faq in faqs:
        # 1. Puntuación base: solapamiento de tokens
        score = self._overlap_score(query_tokens, set(self._tokenize(faq.question)))
        
        # 2. Bonus si una cadena contiene a la otra
        if query_norm and (query_norm in question_norm or question_norm in query_norm):
            score += 0.15
        
        # 3. Bonus por popularidad (hasta +0.05)
        score += min(faq.usage_count / 20, 1) * 0.05
        
        if best is None or score > best.score:
            best = FAQMatch(item=faq, score=score, scope=scope)
    return best
```

**Paso a paso:**
1. **Tokenizar:** divide la consulta y la pregunta de FAQ en palabras individuales, quitando palabras vacías (stopwords como "el", "la", "de", "que") y palabras de menos de 3 letras
2. **Solapamiento:** calcula cuántas palabras comunes hay entre la consulta y la pregunta: `len(intersección) / max(min(len(A), len(B)), 1)`
3. **Bonus de subcadena:** +0.15 si una cadena contiene a la otra
4. **Bonus de popularidad:** hasta +0.05 si la FAQ se ha usado muchas veces
5. **Umbral:** si la puntuación total es ≥ 0.25 (modelo) o ≥ 0.28 (global), se acepta

**Los tokens se obtienen así:**
```python
@staticmethod
def _tokenize(text):
    normalized = FAQMatcherService._normalize(text)
    stopwords = {
        "que", "el", "la", "los", "las", "de", "del", "en", "al", "por",
        "con", "y", "o", "un", "una", "unos", "unas", "se", "es", "son",
        "puede", "pueden", "significa", "ser",
    }
    return [token for token in normalized.split()
            if token and len(token) > 2 and token not in stopwords]
```

Se eliminan palabras como "que", "el", "la", "de", "en"... porque no aportan significado para la comparación.

---

### 🔹 Paso 8: El contrato de salida — `_build_diagnostic_output()`

Independientemente del camino seguido, la respuesta final se construye con esta función (línea 783 de `langraph_flow.py`):

```python
@staticmethod
def _build_diagnostic_output(*, primary, alternatives, next_check, short_explanation, confidence):
    return {
        "primary_hypothesis": primary,
        "alternatives": alternatives,
        "next_check": next_check,
        "short_explanation": short_explanation,
        "confidence": max(0.0, min(confidence, 1.0)),  # clamp entre 0 y 1
    }
```

**Garantías:**
- La confianza siempre está entre 0.0 y 1.0 (se "clampa" con `max(0.0, min(conf, 1.0))`)
- Siempre tiene los 5 campos: `primary_hypothesis`, `alternatives`, `next_check`, `short_explanation`, `confidence`
- Todos los nodos (árbol, FAQ, texto libre) usan esta misma función, asegurando que todas las respuestas tengan el mismo formato

**Ejemplo de respuesta completa al usuario:**
```
Hipotesis principal: Bomba de gasolina defectuosa.
Alternativas: Inyector sucio, Filtro de combustible obstruido.
¿Te ha sido util este resultado? Puedes responder desde feedback.
```

Y en los registros internos (decision_logs) se guarda el `decision_output` completo con toda la trazabilidad.

---

### 📁 Resumen: todos los archivos del módulo Otros

| # | Archivo | ¿Qué hace? |
|---|--------|-----------|
| 1 | `apps/api/app/application/orchestrator/langraph_flow.py` (línea 580) | Nodo orquestador: coordina los 7 pasos y decide si mostrar diagnóstico o pedir más información |
| 2 | `apps/api/app/modules/free_text_parser/service.py` | Clasifica el síntoma usando IA (Groq/OpenRouter) o reglas locales con palabras clave |
| 3 | `data/prompts/free_text_parser.system.txt` | El "rol" que se le da a la IA: "Eres un clasificador técnico de averías..." |
| 4 | `apps/api/app/infrastructure/llm/gateway.py` | Gateway con doble proveedor: intenta Groq primero, si falla usa OpenRouter |
| 5 | `apps/api/app/infrastructure/llm/providers/groq.py` | Proveedor principal (Groq, modelo llama-3.1-8b-instant) |
| 6 | `apps/api/app/infrastructure/llm/providers/openrouter.py` | Proveedor de respaldo (OpenRouter, modelo llama-3.1-8b-instruct) |
| 7 | `apps/api/app/infrastructure/retrieval/embeddings.py` | Convierte texto en vector de 1024 números (OpenRouter o SHA-256) |
| 8 | `apps/api/app/infrastructure/db/repositories/knowledge_repository.py` | Búsqueda híbrida en BD: 75% semántica + 25% léxica |
| 9 | `apps/api/app/modules/historical_retrieval/service.py` | Objetos de datos: `HistoricalCase` y `RetrievalCandidate` |
| 10 | `apps/api/app/modules/hybrid_ranking/service.py` | Ordena candidatos por fórmula: 55% vector + 20% léxico + 15% modelo + 10% base |
| 11 | `apps/api/app/modules/faq_matcher/service.py` | Plan B: si no hay casos históricos, busca en FAQs (token overlap) |
Esto da lo mejor de ambos mundos: el **significado** (75%) y las **palabras exactas** (25%).

Los resultados de esta búsqueda son objetos `RetrievalCandidate`, definidos en:

> 📁 `apps/api/app/modules/historical_retrieval/service.py`

Cada `RetrievalCandidate` contiene: el diagnóstico del caso, las puntuaciones individuales (vector, léxica, coincidencia de modelo, confianza base), y metadatos sobre su origen.

#### Paso 4: Ordenar y elegir la mejor hipótesis
Los candidatos devueltos por la búsqueda híbrida se ordenan para quedarse con los mejores. Esto lo hace el **HybridRankingService**:

> 📁 `apps/api/app/modules/hybrid_ranking/service.py`

Su método `rank(candidates, top_k=3)` aplica esta fórmula a cada candidato:

```
Puntuación final = 55% × puntuación semántica
                 + 20% × puntuación léxica
                 + 15% × coincidencia de modelo
                 + 10% × confianza base del caso
```

| Componente | Peso | ¿Qué mide? |
|-----------|------|-----------|
| vector_score | 55% | Qué parecido es el significado (semántica) |
| lexical_score | 20% | Cuántas palabras coinciden (léxico) |
| model_match | 15% | Si es el mismo modelo de moto |
| base_confidence | 10% | La fiabilidad histórica del caso |

Una vez ordenados, el sistema coge el **mejor candidato** (top-1). Si su puntuación supera el **35% de confianza**, se muestra como diagnóstico principal, junto con hasta 2 alternativas.

#### Paso 5: El director de orquesta que coordina todo (el nodo LangGraph)
Todo esto no ocurre solo: hay un **nodo de LangGraph** que orquesta el flujo completo del módulo Otros. Es el método `_node_free_text_parser` en:

> 📁 `apps/api/app/application/orchestrator/langgraph_flow.py` (línea 580)

Este nodo:
1. Llama a `FreeTextParserService.parse(text)` para clasificar el síntoma
2. Llama a `EmbeddingService.embed(text)` para obtener el vector
3. Llama a `KnowledgeRepository.search_hybrid(...)` para buscar casos
4. **Filtra candidatos débiles**: descarta aquellos con puntuaciones muy bajas (< 0.25)
5. Si hay candidatos de casos históricos, los ordena con `HybridRankingService.rank()`
6. Si **no hay** candidatos históricos, usa el **FAQMatcherService** como plan de respaldo (fallback):
   > 📁 `apps/api/app/modules/faq_matcher/service.py`
7. Si la confianza es suficiente (> 0.35), construye la respuesta con `_build_diagnostic_output()` y la devuelve
8. Si la confianza es baja (o no hay candidatos), responde con un mensaje amable sugiriendo usar los árboles o FAQs

**Resumen del flujo completo** (con sus archivos):

```
Usuario escribe texto libre
       │
       ▼
1. apps/api/app/modules/free_text_parser/service.py
   └── FreeTextParserService.parse(text) → clasifica el síntoma
       │
       ▼
2. apps/api/app/infrastructure/retrieval/embeddings.py
   └── EmbeddingService.embed(text) → convierte a vector 1024d
       │
       ▼
3. apps/api/app/infrastructure/db/repositories/knowledge_repository.py
   └── KnowledgeRepository.search_hybrid(...) → busca casos
       │
       ▼
4. apps/api/app/modules/hybrid_ranking/service.py
   └── HybridRankingService.rank(candidates) → ordena por puntuación
       │
       ▼
5. apps/api/app/application/orchestrator/langraph_flow.py (línea 580)
   └── _node_free_text_parser() → construye la respuesta final
       │
       ▼
   Diagnóstico mostrado al usuario
```

#### Resumen visual del módulo Otros y sus archivos

```
                    TEXTO DEL USUARIO
                           │
                           ▼
    ┌──────────────────────────────────────────────────────┐
    │  free_text_parser/service.py                         │
    │  FreeTextParserService.parse()                       │
    │  ├─ ¿IA disponible? → _parse_with_llm() → Groq API  │
    │  └─ ¿Fallo? → _parse_with_rules() → palabras clave  │
    │  Resultado: ParsedFreeText (categoría + etiquetas)   │
    └──────────────────────┬───────────────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────────────┐
    │  infrastructure/retrieval/embeddings.py               │
    │  EmbeddingService.embed()                            │
    │  ├→ OpenRouter API (bge-m3, vector 1024d)            │
    │  └→ Fallback: SHA-256 (sin conexión)                 │
    │  Resultado: vector numérico                          │
    └──────────────────────┬───────────────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────────────┐
    │  db/repositories/knowledge_repository.py              │
    │  KnowledgeRepository.search_hybrid()                 │
    │  ├→ 75% búsqueda semántica (vectores)                │
    │  └→ 25% búsqueda léxica (tsvector)                   │
    │  Resultado: lista de RetrievalCandidate               │
    └──────────────────────┬───────────────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────────────┐
    │  Si hay candidatos históricos:                       │
    │  hybrid_ranking/service.py                           │
    │  HybridRankingService.rank()                         │
    │  Fórmula: 55% vector + 20% léxico + 15% modelo + 10%│
    │  Resultado: top 3 hipótesis ordenadas                │
    └──────────────────────┬───────────────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────────────┐
    │  Si NO hay candidatos históricos:                    │
    │  faq_matcher/service.py                              │
    │  FAQMatcherService.match() → respuesta desde FAQ     │
    └──────────────────────┬───────────────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────────────┐
    │  application/orchestrator/langraph_flow.py           │
    │  _node_free_text_parser() (línea 580)                │
    │  ├→ ¿Confianza ≥ 35%? → Muestra diagnóstico         │
    │  └→ ¿Confianza < 35%? → "No tengo suficiente info"  │
    │  Resultado: respuesta al usuario                     │
    └──────────────────────────────────────────────────────┘
```

---

## Los asistentes de IA: Groq y OpenRouter

Cuando el sistema necesita usar inteligencia artificial (en el modo "Otros"), no tiene un cerebro propio. En su lugar, **llama a servicios externos** especializados en entender lenguaje. La aplicación usa **dos proveedores** para no depender de uno solo:

### 🟢 Groq (proveedor principal)
- **Modelo:** `llama-3.1-8b-instant`
- **Ventaja:** Es **muy rápido** (procesa hasta 1000 tokens por segundo)
- **Cómo funciona:** Groq tiene chips especializados (LPU) diseñados solo para ejecutar modelos de lenguaje, por lo que las respuestas llegan en milisegundos
- **Uso:** Es el primer intento. Si responde correctamente, perfecto

### 🔵 OpenRouter (proveedor de respaldo)
- **Modelo:** `llama-3.1-8b-instruct`
- **Ventaja:** Tiene mayor disponibilidad y funciona como **plan B** si Groq falla
- **Cómo funciona:** OpenRouter es como un "agente de viajes" de IA: tiene acceso a múltiples modelos de diferentes proveedores y elige el que mejor funciona
- **Uso:** Solo se usa si Groq da error (timeout, límite de peticiones, etc.)

### ¿Qué pasa si ambos fallan?

El sistema tiene un **plan C**: las **reglas locales** (las 40 palabras clave). Aunque son menos precisas que la IA, al menos dan una respuesta en lugar de quedarse bloqueado. Esto se llama **encadenamiento de fallos** o *fallback chain*:

```
Groq 🟢 → ¿Falla? → OpenRouter 🔵 → ¿Falla? → Reglas locales ⚙️
```

Este diseño hace que el sistema sea **robusto**: incluso sin internet, puede seguir funcionando (aunque con menos precisión).

---

## La base de datos: el almacén de conocimiento

La aplicación usa **PostgreSQL** con una extensión especial llamada **pgvector** que permite almacenar y buscar vectores (los "números mágicos" del significado). Hay varias tablas, cada una con un propósito:

### 🗂️ Las tablas principales

| Tabla | ¿Qué guarda? | Ejemplo |
|-------|-------------|---------|
| **`vehicles`** | Los vehículos conocidos (por VIN) | AK550-POC-0001, XCITING-POC-0001 |
| **`faqs`** | Preguntas frecuentes con sus respuestas | "¿Cada cuánto cambiar bujías?" → "Cada 3000-5000 km" |
| **`diagnostic_trees`** | Los árboles de decisión en formato JSON | Preguntas sí/no para cada síntoma |
| **`historical_cases`** | Casos reales de diagnóstico con su solución | Moto X con síntoma Y → diagnóstico Z con 82% de confianza |
| **`sessions`** | Las conversaciones activas | Sesión ID 123, VIN AK550, estado "activo" |
| **`messages`** | Todos los mensajes de cada conversación | Usuario: "mi moto no arranca", Asistente: "..." |
| **`decision_logs`** | Registro de cada decisión del sistema | Nodo: tree_engine, entrada: "paradas", salida: diagnosis, confianza: 0.97 |
| **`feedback`** | Opiniones del usuario sobre los diagnósticos | "¿Fue útil?" → Sí/No + comentario |

### 🔬 La tabla más especializada: `knowledge_chunks`

Esta es la tabla más interesante. Almacena **trozos de conocimiento** (chunks) extraídos de las FAQs, los casos históricos y los árboles de diagnóstico. Cada chunk contiene:

- **El texto** del trozo de conocimiento
- **Un vector de 1024 números** (el **embedding**) que representa su significado
- **El modelo de moto** al que pertenece
- **La categoría del síntoma**
- **Un índice de búsqueda léxica** (`tsvector`) para buscar por palabras
- **Metadatos** como la fuente (FAQ, historical_case, tree_node)

### ¿Cómo se genera un embedding?

1. Se toma un texto (ej: "la bomba de gasolina defectuosa causa paradas intermitentes")
2. Se envía a un servicio de **embeddings** (OpenRouter con modelo `bge-m3`)
3. El servicio devuelve **1024 números** que representan el significado del texto
4. Estos números se guardan en la columna `embedding` de la tabla

El resultado es que textos con **significado parecido** tienen vectores con **números parecidos**. Por ejemplo:

- "La bomba de gasolina no funciona" → [0.12, 0.45, 0.78, ...] (vector A)
- "Problemas con la bomba de combustible" → [0.11, 0.44, 0.76, ...] (vector A', muy parecido a A)
- "El freno trasero chirría" → [0.89, 0.23, 0.15, ...] (vector B, muy diferente de A)

### ¿Qué hace PostgreSQL con estos vectores?

PostgreSQL tiene un **índice especial** llamado **HNSW** (Hierarchical Navigable Small World) que permite buscar rápidamente los vectores más parecidos a uno dado. Es como tener una **biblioteca ordenada por significado**: cuando buscas un libro sobre "problemas de gasolina", el sistema encuentra los chunks con vectores parecidos en milisegundos, aunque haya miles de chunks.

### ¿Qué es la búsqueda híbrida exactamente?

La función `hybrid_search` dentro de la base de datos combina dos mundos:

1. **Búsqueda vectorial:** `1 - (embedding <=> query_embedding)` — mide la distancia entre vectores (similitud del coseno). Esto capta el **significado**.
2. **Búsqueda textual:** `ts_rank(lexical, websearch_to_tsquery('spanish', texto))` — usa el índice de texto de PostgreSQL. Esto capta **palabras exactas**.

La fórmula final:
```sql
puntuación = (0.75 × similitud_vectorial + 0.25 × relevancia_textual) / (0.75 + 0.25)
```

Esto se llama **búsqueda híbrida** y es mucho más potente que usar solo uno de los dos métodos.

---

## Cómo se construye la respuesta final

Independientemente del camino elegido (árbol, FAQ, o texto libre), la respuesta del asistente sigue un **formato estructurado**:

```json
{
  "primary_hypothesis": "Bomba de gasolina defectuosa",
  "alternatives": ["Filtro de combustible obstruido", "Reglaje de válvulas"],
  "next_check": "Verificar hipótesis principal: Bomba de gasolina defectuosa.",
  "short_explanation": "El usuario describe paradas intermitentes...",
  "confidence": 0.78
}
```

- **Hipótesis principal:** El diagnóstico más probable
- **Alternativas:** Otras posibilidades (máximo 2)
- **Siguiente revisión:** Qué debería comprobar el mecánico
- **Explicación corta:** Por qué se llegó a esa conclusión
- **Confianza:** Un número entre 0 y 1 que indica cuán seguro está el sistema (1 = máxima confianza)

Este formato está definido en un **contrato** (un archivo JSON Schema en `packages/contracts/diagnostic_output.schema.json`) que garantiza que todas las respuestas tengan la misma estructura, vengan del módulo que vengan.

---

## Trazabilidad: cómo sabemos por qué el sistema dijo lo que dijo

Una de las características más importantes del sistema es que **cada decisión queda registrada**. Cada vez que LangGraph ejecuta un nodo, se guarda en la tabla `decision_logs`:

- **session_id:** La conversación en la que ocurrió
- **module_name:** Qué nodo se ejecutó (tree_engine, faq_matcher, etc.)
- **input_data:** Qué mensaje recibió
- **output_data:** Qué respuesta dio (incluyendo el diagnóstico)
- **confidence:** Con qué confianza
- **created_at:** Cuándo ocurrió

Esto permite **auditar** cualquier diagnóstico: se puede ver exactamente qué pasos siguió el sistema para llegar a una conclusión, y si hubo algún error, se puede localizar el nodo concreto que falló.

---

## ¿Qué datos tiene el sistema actualmente?

La aplicación funciona con información real de dos modelos de motocicleta:

| Modelo | FAQs | Árboles de diagnóstico | Casos históricos |
|--------|------|----------------------|-----------------|
| **AK550** (Scooter 550cc) | ~22 preguntas | 5 árboles (paradas, CELP, arranque, frenos, refrigeración) | 17 casos |
| **Xciting 400** (Scooter 400cc) | ~22 preguntas | 5 árboles (paradas, embrague, escape, frenos, eléctrico) | 15 casos |

De estos datos se generan automáticamente **~79 "knowledge chunks"** (trozos de conocimiento) con sus correspondientes vectores, que alimentan la búsqueda híbrida.

---

## Guía rápida para la demostración

Para hacer una demo completa sigue estos pasos:

### Paso 1: Iniciar sesión
- Abre la aplicación en el navegador
- Verás la pantalla de bienvenida con el logotipo animado

### Paso 2: Introducir VIN
- Escribe `AK550-POC-0001` y pulsa Enter
- El sistema responde: *"He identificado el vehículo como AK550 (2022)..."*

### Paso 3: Probar los tres caminos

**Ruta A — Árbol de decisión (Síntomas frecuentes):**
1. Escribe: `Síntomas frecuentes`
2. El sistema muestra los síntomas disponibles: *Paradas de motor, Testigo CELP encendido, Dificultad de arranque, Frenos, Refrigeración*
3. Elige: `Paradas de motor`
4. Responde a las preguntas sí/no hasta obtener un diagnóstico
5. Al final, aparecen botones: *Finalizar diagnóstico* o *Volver al menú*

**Ruta B — FAQ (Consultas frecuentes):**
1. Escribe: `Consultas frecuentes`
2. El sistema sugiere preguntas ejemplo
3. Escribe: `La moto se para al pasar baches`
4. El sistema responde con la FAQ correspondiente
5. Botones: *Volver al menú* o *Finalizar diagnóstico*

**Ruta C — Texto libre (Otros):**
1. Escribe: `Otros` (o simplemente escribe el problema directamente)
2. Describe un problema: `La moto arranca bien pero al rato se para y luego vuelve a funcionar`
3. El sistema pasa por **5 archivos** en cadena:
   - `free_text_parser/service.py` → clasifica el síntoma (Groq/OpenRouter o reglas locales)
   - `infrastructure/retrieval/embeddings.py` → convierte el texto en un vector de 1024 números
   - `db/repositories/knowledge_repository.py` → busca casos históricos (búsqueda híbrida)
   - `hybrid_ranking/service.py` → ordena los candidatos por puntuación
   - `application/orchestrator/langraph_flow.py` (línea 580) → construye la respuesta final
4. Muestra una hipótesis con su nivel de confianza

### Paso 4: Feedback
- Después de cada diagnóstico, puedes indicar si fue útil o no
- Este feedback se guarda en la tabla `feedback` para futuras mejoras

### Paso 5: Cerrar sesión
- Presiona `Esc` o usa el botón de cerrar sesión en el menú lateral
- Vuelves a la pantalla de bienvenida para empezar de nuevo

---

## Glosario de términos (para la clase)

| Término | Significado |
|---------|------------|
| **VIN** | Número de bastidor, identifica cada vehículo de forma única |
| **LLM** | Modelo de Lenguaje Grande (Large Language Model). Es una IA entrenada con mucho texto que puede entender y generar lenguaje natural |
| **Embedding** | Representación numérica del significado de un texto (un vector de ~1000 números). Textos con significado parecido tienen vectores parecidos |
| **Prompt** | Instrucciones que se le dan al LLM para que haga una tarea concreta |
| **LangGraph** | Framework de Python para crear grafos de conversación. Permite conectar nodos (módulos) y decidir qué nodo ejecutar según el estado |
| **Nodo** | Unidad de procesamiento del grafo. Cada nodo hace una tarea concreta (mirar VIN, navegar árbol, etc.) |
| **Estado de sesión** | Ficha con toda la información de la conversación: VIN, modelo, síntoma actual, paso del árbol, preguntas ya hechas. Se guarda en BD |
| **Token** | Unidad mínima de texto (palabra o parte de palabra) |
| **Árbol de decisión** | Estructura de preguntas sí/no que lleva a un diagnóstico |
| **Búsqueda semántica** | Búsqueda por significado usando vectores y similitud del coseno |
| **Búsqueda léxica** | Búsqueda por coincidencia de palabras exactas usando índices de texto |
| **Búsqueda híbrida** | Combinación de búsqueda semántica (75%) y léxica (25%) para obtener mejores resultados |
| **Similitud del coseno** | Fórmula matemática que mide el ángulo entre dos vectores. Si el ángulo es pequeño, los textos son parecidos |
| **Índice HNSW** | Estructura de datos que permite buscar rápidamente vectores parecidos en una base de datos |
| **pgvector** | Extensión de PostgreSQL que permite almacenar y buscar vectores |
| **Confianza** | Medida de 0 a 1 de cuán seguro está el sistema del resultado |
| **Fallback** | Plan alternativo cuando algo falla (ej: si Groq falla, usa OpenRouter; si OpenRouter falla, usa reglas locales) |
| **Groq** | Servicio de IA con chips especializados (LPU) para ejecutar modelos de lenguaje muy rápido |
| **OpenRouter** | Agregador de modelos de IA que da acceso a múltiples proveedores desde una sola API |
| **Knowledge Chunk** | Trozo de conocimiento extraído de FAQs, casos históricos o árboles, con su vector de significado asociado |
| **Trazabilidad** | Capacidad de rastrear cada decisión del sistema gracias a los registros en `decision_logs` |
| **Contrato JSON** | Archivo que define la estructura que deben tener las respuestas para que todos los módulos hablen el mismo idioma |

---

## Arquitectura técnica (vista general)

```
                    ┌──────────────────────────────────────┐
                    │          USUARIO (Navegador)         │
                    │     Interfaz web con animaciones     │
                    └──────────────┬───────────────────────┘
                                   │  HTTPS (REST API)
                                   ▼
                    ┌──────────────────────────────────────┐
                    │       BACKEND (FastAPI / Python)      │
                    │                                      │
                    │  ┌──────────────────────────────────┐ │
                    │  │  LangGraph (Director de orquesta)│ │
                    │  │  ┌────┐ ┌────┐ ┌────┐ ┌──────┐ │ │
                    │  │  │VIN │ │Tree│ │FAQ │ │Texto │ │ │
                    │  │  │Lkp │ │Eng │ │Mat │ │Libre │ │ │
                    │  │  └────┘ └────┘ └────┘ └──────┘ │ │
                    │  └──────────────────────────────────┘ │
                    │         │              │              │
                    │         ▼              ▼              │
                    │  ┌──────────┐   ┌──────────┐         │
                    │  │ Servicio │   │ Servicio │         │
                    │  │ de Árbol │   │ de FAQ   │         │
                    │  └──────────┘   └──────────┘         │
                    │         │              │              │
                    │         ▼              ▼              │
                    │  ┌──────────────────────────────────┐ │
                    │  │  Búsqueda Híbrida + Ranking      │ │
                    │  │  (semántica + léxica)            │ │
                    │  └──────────────┬───────────────────┘ │
                    └─────────────────┼─────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────────┐
                    │                 ▼                     │
                    │  ┌──────────────────────────────────┐ │
                    │  │  PostgreSQL + pgvector           │ │
                    │  │  ┌──────────┐ ┌──────────────┐  │ │
                    │  │  │ Tablas   │ │ knowledge_   │  │ │
                    │  │  │ relacio- │ │ chunks       │  │ │
                    │  │  │ nales    │ │ (vectores    │  │ │
                    │  │  │ (FAQs,   │ │  1024d +     │  │ │
                    │  │  │ árboles, │ │  tsvector)   │  │ │
                    │  │  │ casos...)│ │              │  │ │
                    │  │  └──────────┘ └──────────────┘  │ │
                    │  └──────────────────────────────────┘ │
                    │                │                      │
                    │                ▼                      │
                    │  ┌──────────────────────────────────┐ │
                    │  │  IA Externa (Groq / OpenRouter)  │ │
                    │  │  → Clasificación de textos       │ │
                    │  │  → Embeddings (bge-m3)          │ │
                    │  └──────────────────────────────────┘ │
                    └──────────────────────────────────────┘
```

---

## En resumen

Esta aplicación demuestra cómo se puede construir un **asistente conversacional de diagnóstico técnico** combinando:

1. **Conocimiento estructurado** (árboles de decisión y FAQs) — rápido y fiable
2. **Casos históricos** — aprendizaje de experiencias pasadas
3. **Inteligencia artificial** (Groq/OpenRouter) — para manejar casos no previstos
4. **Búsqueda híbrida** — combinando significado (vectores) y palabras exactas (léxico)
5. **Trazabilidad** — cada decisión registrada para poder auditar el razonamiento

Todo ello orquestado por **LangGraph**, que decide en cada momento cuál es el mejor camino para ayudar al usuario, usando un **grafo de 7 nodos** que cubren todo el flujo de diagnóstico. La base de datos **PostgreSQL + pgvector** almacena tanto los datos estructurados como los vectores de significado, permitiendo búsquedas semánticas rápidas.

El resultado es un sistema que **no depende ciegamente de la IA**: si falla internet, sigue funcionando con reglas locales; si el LLM se equivoca, los árboles y FAQs dan respuestas fiables; y todo queda registrado para mejorar en el futuro.
