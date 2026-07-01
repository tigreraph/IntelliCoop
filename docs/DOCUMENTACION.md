# IntelliCoop — Documentación Técnica
**Sistema Inteligente de Análisis y Riesgo Cooperativo**
Proyecto de Titulación · Jonnathan Tigre · 2026

---

## Índice
1. [Descripción general](#1-descripción-general)
2. [Arquitectura del sistema](#2-arquitectura-del-sistema)
3. [Stack tecnológico](#3-stack-tecnológico)
4. [Modelo de datos](#4-modelo-de-datos)
5. [Estructura del proyecto](#5-estructura-del-proyecto)
6. [Vistas y lógica de negocio](#6-vistas-y-lógica-de-negocio)
7. [Templates y diseño UI](#7-templates-y-diseño-ui)
8. [Metodología CAMEL](#8-metodología-camel)
9. [Asistente Rakkun (IA)](#9-asistente-rakkun-ia)
   - [Avatar Live2D Rakkun 2.0](#avatar-live2d--rakkun-20-rakkun_avatarhtml)
10. [Variables de entorno](#10-variables-de-entorno)
11. [Instalación local](#11-instalación-local)
12. [Despliegue en VPS](#12-despliegue-en-vps)
13. [Control de versiones — GitHub](#13-control-de-versiones--github)
14. [Módulo de Predicción ML](#14-módulo-de-predicción-ml)

---

## 1. Descripción general

**IntelliCoop** es una aplicación web de análisis financiero para las cooperativas de ahorro y crédito supervisadas por la **Superintendencia de Economía Popular y Solidaria (SEPS)** del Ecuador.

El sistema permite:
- Visualizar el ranking CAMEL de las 226 cooperativas activas
- Analizar indicadores financieros por segmento (1, 2, 3 y Mutualistas)
- Explorar el historial de indicadores de cada cooperativa individual
- Consultar en lenguaje natural a través del asistente de IA **Rakkun**, que traduce preguntas a SQL y consulta la base de datos en tiempo real

### Cobertura de datos
| Métrica | Valor |
|---|---|
| Cooperativas supervisadas | 226 activas |
| Último corte disponible | Diciembre 2025 |
| Activos totales del sistema | ~40B USD |
| Registros históricos (DuckDB local) | ~31 millones de filas |

---

## 2. Arquitectura del sistema

```
┌──────────────────────────────────────────────────────────────┐
│                        NAVEGADOR                             │
│          Tailwind CSS CDN · Chart.js CDN · Tabler Icons     │
└───────────────────────┬──────────────────────────────────────┘
                        │ HTTP
┌───────────────────────▼──────────────────────────────────────┐
│              DJANGO 4.x (seps_web)                           │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐│
│  │  urls.py    │  │  views.py    │  │  templates/          ││
│  │  5 rutas    │→ │  6 funciones │→ │  base.html + 5 pages ││
│  └─────────────┘  └──────┬───────┘  └──────────────────────┘│
└─────────────────────────┬┴─────────────────────────────────┘
                          │ psycopg2
          ┌───────────────▼──────────────────┐
          │         PostgreSQL               │
          │  DB: seps_eeff                   │
          │  Tablas: fact_indicadores        │
          │          dim_cooperativa         │
          └──────────────────────────────────┘

                          +

┌─────────────────────────────────────────────────────────────┐
│                  Rakkun API (FastAPI)                        │
│  Puerto 8001 · DeepSeek V3.2 via OpenRouter                 │
│  Text-to-SQL → PostgreSQL → respuesta en lenguaje natural   │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de una petición típica
1. El navegador solicita una URL (ej. `/ranking/`)
2. Django enruta a la función `ranking()` en `views.py`
3. La vista ejecuta una query SQL sobre PostgreSQL via `psycopg2`
4. Los resultados se serializan con `_to_py()` (convierte Decimals y fechas)
5. Se renderizan en el template correspondiente con `render()`
6. El template hereda de `base.html` (sidebar + topbar + footer)

---

## 3. Stack tecnológico

### Backend
| Componente | Versión / Detalle |
|---|---|
| Python | 3.14 |
| Django | 6.0.6 |
| psycopg2 | Driver PostgreSQL |
| PostgreSQL | Base de datos principal (local port 5434, VPS port 5432) |
| Gunicorn | Servidor WSGI en producción |

### Frontend
| Componente | Fuente |
|---|---|
| Tailwind CSS | CDN `https://cdn.tailwindcss.com` (con valores arbitrarios `[#hex]`) |
| Chart.js | CDN `https://cdn.jsdelivr.net/npm/chart.js` |
| Tabler Icons | CDN `https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.31.0/...` |
| Inter (tipografía) | Google Fonts |

### IA / Asistente
| Componente | Detalle |
|---|---|
| Rakkun API | FastAPI corriendo en puerto 8001 |
| Modelo LLM | DeepSeek V3.2 via OpenRouter |
| Capacidad | Text-to-SQL en español + respuesta natural |

---

## 4. Modelo de datos

### Tabla `dim_cooperativa`
Dimensión con datos estáticos de cada institución.

| Columna | Tipo | Descripción |
|---|---|---|
| `ruc` | VARCHAR (PK) | Identificador único (RUC ecuatoriano) |
| `razon_social` | VARCHAR | Nombre oficial de la cooperativa |
| `segmento` | VARCHAR | Segmento regulatorio (1, 2, 3, Mutualista) |
| `estado` | VARCHAR | `ACTIVA` o `INACTIVA` |
| `primera_fecha` | DATE | Primera fecha de reporte en el sistema |
| `ultima_fecha` | DATE | Última fecha de reporte disponible |
| `meses_activo` | INTEGER | Meses con datos históricos |

### Tabla `fact_indicadores`
Tabla de hechos con los indicadores financieros por corte mensual.

| Columna | Tipo | Descripción |
|---|---|---|
| `ruc` | VARCHAR (FK) | RUC de la cooperativa |
| `fecha_corte` | DATE | Mes del corte financiero |
| `camel_score` | NUMERIC | Score CAMEL compuesto (0–100) |
| `rating_camel` | VARCHAR | Categoría: Excelente / Bueno / Regular / Deficiente / Crítico |
| `morosidad_pct` | NUMERIC | % cartera morosa · umbral SEPS ≤ 5% |
| `capitalizacion_pct` | NUMERIC | Patrimonio/Activo · umbral SEPS ≥ 9% |
| `liquidez_ampliada` | NUMERIC | % liquidez · umbral SEPS ≥ 14% |
| `roa_pct` | NUMERIC | Return on Assets % |
| `eficiencia_op_pct` | NUMERIC | Gastos operativos / Activo · mayor = menos eficiente |
| `activo_total` | NUMERIC | Activos totales en USD |

### Constantes SQL usadas en views.py
```python
ULTIMO_CORTE = "(SELECT MAX(fecha_corte) FROM fact_indicadores)"
SOLO_ACTIVAS = "dc.estado = 'ACTIVA'"
```
Estas constantes garantizan que siempre se trabaje con el corte más reciente y solo cooperativas activas.

---

## 5. Estructura del proyecto

```
seps_web/
├── manage.py
├── seps_project/
│   ├── settings.py
│   ├── urls.py                  ← 5 rutas principales + API Rakkun
│   └── wsgi.py
├── core/
│   └── views.py                 ← Toda la lógica de negocio
└── templates/
    ├── base.html                ← Layout base: sidebar + topbar + footer
    ├── dashboard.html           ← KPIs + donut + top5/bottom5
    ├── ranking.html             ← Tabla con filtros y ordenamiento
    ├── segmentos.html           ← Análisis por segmento + gráficos
    ├── cooperativa_detalle.html ← Vista individual + radar CAMEL + históricos
    └── rakkun.html              ← Interfaz de chat con IA
```

---

## 6. Vistas y lógica de negocio

Todas las vistas están en `core/views.py`. Usan `psycopg2` con `RealDictCursor` para obtener resultados como diccionarios.

### `_to_py(rows)` — Serializador
Convierte tipos PostgreSQL (Decimal, date) a tipos Python nativos (float, str) para que sean JSON-serializables y compatibles con los templates de Django.

```python
def _to_py(rows):
    result = []
    for row in rows:
        d = {}
        for k, v in row.items():
            if hasattr(v, '__float__') and not isinstance(v, int):
                d[k] = float(v)
            elif hasattr(v, 'isoformat'):
                d[k] = str(v)
            else:
                d[k] = v
        result.append(d)
    return result
```

### `dashboard(request)` → `/`
Calcula KPIs globales del sistema (total coops, CAMEL promedio, morosidad, liquidez, activos totales), distribución por segmento para el donut chart, y top5/bottom5 CAMEL.

**Variables de contexto:** `kpis`, `por_segmento` (JSON), `top5`, `bottom5`

### `ranking(request)` → `/ranking/`
Obtiene todas las cooperativas activas con sus indicadores del último corte, ordenadas por `camel_score DESC`.

**Variables de contexto:** `cooperativas`

### `segmentos(request)` → `/segmentos/`
Agrega los indicadores por segmento regulatorio (AVG de cada KPI, SUM de activos).

**Variables de contexto:** `segmentos`, `segmentos_json` (JSON para Chart.js)

### `cooperativa_detalle(request, ruc)` → `/cooperativa/<ruc>/`
Obtiene los datos estáticos de la cooperativa (`dim_cooperativa`) y los últimos 24 cortes históricos de `fact_indicadores`.

**Variables de contexto:** `coop`, `historico`, `historico_json` (JSON para Chart.js)

### `rakkun(request)` → `/rakkun/`
Renderiza la interfaz de chat. No ejecuta queries — el chat funciona en el frontend vía `fetch()` a la API.

### `rakkun_chat(request)` → `/api/rakkun/preguntar`
Proxy HTTP: recibe la pregunta del frontend, la reenvía a la Rakkun API (FastAPI), y retorna la respuesta JSON con `respuesta`, `sql_generado` y `tabla`.

---

## 7. Templates y diseño UI

### Sistema de diseño (definido en `base.html`)

**Paleta de colores:**
```
Sidebar:        #162032
Topbar:         #182540
Fondo/body:     #1e293b
Cards:          #243347
Bordes:         #2d3f57
Nav activo bg:  #1e3352

Texto primario:    #f1f5f9
Texto secundario:  #94a3b8
Texto muted:       #64748b

Indigo (acento):  #818cf8
Sky:              #38bdf8
Verde/positivo:   #34d399
Rojo/negativo:    #f87171
Amber/alerta:     #fbbf24
```

**Clases CSS personalizadas (definidas en `<style>` de `base.html`):**

| Clase | Uso |
|---|---|
| `.nav-item` | Ítem de navegación en sidebar con estado activo/hover |
| `.nav-rakkun` | Botón especial de Rakkun con estilo indigo destacado |
| `.ic-card` | Card genérica (bg #243347, borde #2d3f57, border-radius 12px) |
| `.ic-card-sm` | Card compacta para sidebar stats |
| `.kpi-card` | Card de KPI con overflow hidden para la barra de acento |
| `.kpi-accent` | Barra de color de 3px en la parte superior del KPI card |
| `.badge` | Base para badges de rating |
| `.badge-excellent/good/regular/deficient/critical` | Badges semáforo CAMEL |
| `.ic-table` | Estilos de tabla (thead oscuro, hover en filas) |
| `.ic-input` / `.ic-select` | Inputs/selects del design system |
| `.fade-in` + `.fade-in-1..5` | Animaciones de entrada escalonadas |

**Bloques Django de `base.html`:**
```
{% block title %}         → Título del tab del navegador
{% block head %}          → CDNs extra (Chart.js se pone aquí)
{% block page_title %}    → Título en el topbar
{% block page_subtitle %} → Subtítulo en el topbar
{% block topbar_actions %}→ Lado derecho del topbar (botones, badges)
{% block content %}       → Contenido principal de la página
{% block scripts %}       → JavaScript al final del body
```

### Regla importante para templates Django + Tailwind
**Nunca usar clases Tailwind con valores arbitrarios `[#hex]` dentro de bloques `{% if %}`.**
Django interpreta los corchetes `[]` como sintaxis de template y lanza `TemplateSyntaxError`.

✅ Correcto:
```html
<span style="color:{% if val >= 0 %}#34d399{% else %}#f87171{% endif %}">
```

❌ Incorrecto (lanza error):
```html
<span class="{% if val >= 0 %}text-[#34d399]{% else %}text-[#f87171]{% endif %}">
```

También, los operadores en `{% if %}` **requieren espacios**:
```
✅  forloop.counter == 1
❌  forloop.counter==1
```

---

## 8. Metodología CAMEL

CAMEL es el método de calificación financiera usado por la SEPS. Evalúa 5 componentes:

| Letra | Componente | Indicador principal | Umbral SEPS |
|---|---|---|---|
| **C** | Capital / Solvencia | Capitalización (Patrimonio/Activo) | ≥ 9% |
| **A** | Calidad de Activos | Morosidad de cartera | ≤ 5% |
| **M** | Gestión / Management | Eficiencia operativa | Menor = mejor |
| **E** | Rentabilidad (Earnings) | ROA (Return on Assets) | ≥ 0% |
| **L** | Liquidez | Liquidez ampliada | ≥ 14% |

### Score CAMEL compuesto (0–100)
El sistema calcula un score numérico normalizado para permitir comparación y ranking entre cooperativas. Cada componente se normaliza a una escala 0–100:

```javascript
// Normalización en el radar chart (cooperativa_detalle.html)
C = clamp(capitalizacion_pct / 9 * 100,  0, 100)
A = clamp(5 / max(morosidad_pct, 0.01) * 100, 0, 100)  // inverso
M = clamp(80 / max(eficiencia_op_pct, 1) * 100, 0, 100) // inverso
E = clamp(roa_pct * 25 + 50, 0, 100)
L = clamp(liquidez_ampliada / 14 * 100, 0, 100)
```

### Rating CAMEL
| Score | Rating | Color |
|---|---|---|
| 80–100 | Excelente | Verde `#34d399` |
| 60–79  | Bueno | Lima `#a3e635` |
| 40–59  | Regular | Amber `#fbbf24` |
| 20–39  | Deficiente | Naranja `#fb923c` |
| 0–19   | Crítico | Rojo `#f87171` |

---

## 9. Asistente Rakkun (IA)

### Arquitectura
```
Frontend (rakkun.html)
    │  POST /api/rakkun/preguntar
    │  body: { "texto": "¿Cuál es la cooperativa más grande?" }
    ▼
Django view rakkun_chat()  ← proxy HTTP
    │  POST http://157.230.62.218/api/rakkun/preguntar
    ▼
Rakkun FastAPI (puerto 8001)
    │  Prompt engineering: pregunta → SQL
    ▼
DeepSeek V3.2 (OpenRouter)
    │  Genera SQL
    ▼
PostgreSQL seps_eeff
    │  Ejecuta la query
    ▼
Respuesta JSON:
{
  "respuesta":    "La cooperativa más grande por activos es...",
  "sql_generado": "SELECT dc.razon_social, fi.activo_total ...",
  "tabla":        [{"razon_social": "...", "activo_total": ...}]
}
```

### Funcionalidades del chat (frontend)
- **Persistencia de historial**: via `sessionStorage` (clave `rakkun_chat_history`) — el historial sobrevive recargas pero se limpia al cerrar la pestaña
- **Indicador "pensando"**: animación de 3 puntos mientras espera respuesta de la API
- **Renderizado de resultados**: muestra texto, bloque SQL (`<pre>`) y tabla de datos automáticamente según lo que devuelva la API
- **Manejo de errores**: muestra toast global `window.showToast()` si la API falla
- **Limpiar historial**: botón en el topbar que limpia `sessionStorage` y reinicia la vista
- **Atajos**: Enter envía, Shift+Enter hace salto de línea

### Endpoint proxy en Django
```python
# views.py
@csrf_exempt
def rakkun_chat(request):
    body = json.loads(request.body)
    texto = body.get('texto', '').strip()
    rakkun_url = os.environ.get('RAKKUN_API_URL', 'http://157.230.62.218/api/rakkun/preguntar')
    # ... reenvío HTTP con urllib
```

> **Nota**: el campo del body enviado al proxy es `texto`, pero el frontend envía `pregunta`. Verificar coherencia entre `rakkun.html` (usa `pregunta`) y `views.py` (usa `texto`) antes de desplegar.

---

### Avatar Live2D — Rakkun 2.0 (`rakkun_avatar.html`)

Página separada del chat que muestra a Rakkun como VTuber interactivo con modelo Live2D en tiempo real.

#### Stack

| Librería | Versión | Función |
|---|---|---|
| `pixi.js` | 7.x CDN | Renderer WebGL |
| `pixi-live2d-display` | 0.4.0 CDN | Bridge Pixi ↔ Cubism |
| `live2dcubismcore.min.js` | SDK 5.1.0 CDN | Motor Cubism nativo |

#### Archivos del modelo

```
seps_web/static/live2d/rakkun/
├── rakkun.model3.json      ← manifiesto principal (NUNCA sobreescribir sin fix_model3.bat)
├── rakkun_v2.moc3          ← modelo compilado activo (Sep 2023, 2.3 MB, 202 parámetros)
├── rakkun.moc3             ← copia de respaldo (mismo archivo)
├── rakkun.physics3.json    ← física de cabello y ropa
├── rakkun.cdi3.json        ← display info
├── rakkun.4096/            ← 11 texturas PNG (texture_00 … texture_10)
├── expressions/            ← 36 archivos .exp3.json
├── motions/                ← idle, dance, karaoke, pentab
├── anterior/               ← backup modelo original Sep 2023
└── RakkunFormal.cmo3       ← fuente Cubism Editor 5 (no se sirve al browser)
```

> **Importante**: `rakkun_v2.moc3` es el nombre activo. Cada vez que se re-exporte desde Cubism Editor se genera un nuevo `.moc3` — ejecutar `fix_model3.bat` y, si el caché del navegador persiste, renombrar el archivo e incrementar la referencia en `model3.json`.

#### Problema crítico: `model3.json` se sobreescribe con cada exportación

Cubism Editor genera un `model3.json` limpio sin las secciones `Expressions` ni `Motions`. Solución: ejecutar `fix_model3.bat` desde la raíz del proyecto tras cada exportación.

```bat
# Ubicación
IntelliCoop/fix_model3.bat

# Qué hace
py -c "... escribe model3.json con 36 expressions + 4 motions + referencia a rakkun_v2.moc3 ..."
```

#### Parámetros del modelo activos en el ticker

Los parámetros de outfit y rasgos se fuerzan cada frame en `PIXI.Ticker.shared` para que las expresiones de gestos no los sobreescriban:

```javascript
// setupLipSync() — ticker de PIXI (cada frame)
const core = live2dModel.internalModel.coreModel;

// Outfit maid formal
core.setParameterValueById('ParamMaid',          1.0);  // vestido negro maid
core.setParameterValueById('ParamNormalClothes', 1.0);
core.setParameterValueById('ParamJacketOff',     1.0);  // sin chaqueta
core.setParameterValueById('ParamHairStyle',     0.0);  // cabello suelto

// Rasgos mapache ocultos (look formal)
core.setParameterValueById('ParamEarOff',    1.0);  // sin orejas
core.setParameterValueById('ParamTailOnOff', 1.0);  // sin cola
core.setParameterValueById('ParamCapOnOff',  1.0);  // sin gorra
core.setParameterValueById('ParamMaskOnOff', 0.0);  // antifaz BORRADO del modelo → straps visibles
core.setParameterValueById('ParamMaskChage', 0.0);
```

> **Lógica invertida**: `ParamCapOnOff = 1.0` **oculta** la gorra (no la activa). `ParamEarOff = 1.0` **oculta** las orejas. Verificar siempre con diagnóstico de parámetros si se agrega un nuevo toggle.

#### Modificaciones al modelo en Cubism Editor 5

Durante el desarrollo se realizaron las siguientes ediciones al archivo fuente `RakkunFormal.cmo3`:

| Elemento borrado | Razón |
|---|---|
| Mesh `antifaz` / eyemask (careta negra) | Look formal sin antifaz |
| Mantener `eyemask strap_L/R` | Los straps decorativos del pecho permanecen visibles al setear `ParamMaskOnOff = 0.0` |

Los elementos **no removibles por parámetros JS** (baked en `ParamMaid = 1.0`):
- Diadema blanca maid
- Collar/choker maid
- Delantal blanco maid

Para ocultarlos se requiere editar layers directamente en Cubism Editor y re-exportar.

#### Cómo diagnosticar parámetros del modelo desde DevTools

```javascript
// Pegar en Console del navegador con el avatar abierto
const m = window._rkModel || (()=>{ /* acceso manual */ })();
const nm = live2dModel.internalModel.coreModel._model;
const ids = nm.parameters.ids;
const vals = nm.parameters.values;
for (let i = 0; i < ids.length; i++)
  console.log(`[${i}] ${ids[i]}  val=${vals[i].toFixed(2)}`);
```

> `core.getParametersCount()` **no existe** en Cubism SDK 5 — siempre usar `._model.parameters.ids`.

#### Funcionalidades del avatar

- **Lip sync**: simulado con `PIXI.Ticker` + timers por palabras (~300 WPM) sincronizados con duración del audio MP3
- **Expresiones gestuales**: 5 botones (Alegre/Tímida/Seria/Triste/Normal) + expresión automática según respuesta de la API
- **Seguimiento de mirada**: `model.focus(x, y)` en `mousemove`; vuelve al centro en `mouseleave`
- **Text-to-Speech**: **Google Cloud TTS** — voz `es-US-Neural2-A` (femenina Neural), funciona en Chrome/Brave/Firefox/Edge sin depender de voces del sistema
- **Speech Recognition**: `SpeechRecognition` / `webkitSpeechRecognition` en `es-EC`
- **Toggle de voz**: al desactivar, pausa el `Audio` de Google TTS + detiene lip sync + resetea expresión a `heh`
- **Firefox fix**: `dispatchEvent(new Event('submit', {bubbles:true, cancelable:true}))` — sin `bubbles:true` Firefox ignoraba el evento y enviaba el formulario nativamente

#### Google Cloud TTS — arquitectura

```
rakkun_avatar.html
    │  POST /api/tts/ { texto: "..." }
    │  header: X-CSRFToken
    ▼
Django views.tts()          ← proxy seguro (API key en .env, nunca expuesta)
    │  POST https://texttospeech.googleapis.com/v1/text:synthesize?key=...
    │  voice: es-US-Neural2-A, FEMALE, rate 1.05, pitch 1.5
    ▼
Google Cloud TTS API
    │  { audioContent: "<base64 MP3>" }
    ▼
Frontend: atob() → Blob → URL.createObjectURL() → new Audio().play()
```

**Variables de entorno requeridas:**
```
GOOGLE_TTS_KEY=AIzaSy...    # en seps_web/.env
```

**Endpoint Django:**
```python
# core/views.py
@csrf_exempt
def tts(request):
    # POST { texto } → llama Google TTS → devuelve { audioContent: base64 }
```

**URL registrada:** `path('api/tts/', views.tts, name='tts')`

**Cuota Google Cloud TTS Always Free:** 1,000,000 chars Neural/mes — permanente, no caduca con el trial.

#### Cache busting entre navegadores

El `.moc3` es descargado internamente por Live2D sin poder agregar query params. Si un navegador tiene cacheado el modelo viejo, la solución es renombrar el archivo:

```
rakkun.moc3  →  rakkun_v2.moc3   (v2 activo a Jun-2026)
```

Y actualizar en `model3.json`:
```json
"Moc": "rakkun_v2.moc3"
```

La próxima exportación que cambie el modelo usa `rakkun_v3.moc3`, etc.

---

## 10. Variables de entorno

| Variable | Default local | Producción (VPS) | Descripción |
|---|---|---|---|
| `SECRET_KEY` | dev-key-insegura | clave aleatoria 50 chars | Clave criptográfica Django |
| `DEBUG` | `True` | `False` | Modo debug |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | `157.230.62.218,localhost` | Hosts permitidos |
| `DB_HOST` | `localhost` | `localhost` | Host PostgreSQL |
| `DB_PORT` | `5434` | `5432` | Puerto PostgreSQL |
| `DB_USER` | `postgres` | `seps_user` | Usuario PostgreSQL |
| `DB_PASS` | `seps2024` | password seguro | Contraseña PostgreSQL |
| `RAKKUN_API_URL` | `http://localhost:8001/preguntar` | `http://localhost:8001/preguntar` | URL interna Rakkun FastAPI |
| `GOOGLE_TTS_KEY` | — | AIzaSy... | API Key Google Cloud TTS |

Se configuran en `seps_web/.env` (requiere `python-dotenv`). La plantilla está en `.env.example`.

> **Generar SECRET_KEY segura:**
> ```python
> python -c "import secrets; print(secrets.token_urlsafe(50))"
> ```

---

## 11. Instalación local

### Requisitos previos
- Python 3.10+
- PostgreSQL corriendo en puerto 5434 con la base `seps_eeff`
- Base de datos con tablas `fact_indicadores` y `dim_cooperativa` cargadas

### Pasos

```bash
# 1. Clonar/ubicarse en el proyecto
cd seps_web

# 2. Instalar dependencias
pip install django psycopg2-binary

# 3. Verificar conexión a la base de datos
python -c "import psycopg2; conn = psycopg2.connect(host='localhost', port=5434, dbname='seps_eeff', user='postgres', password='seps2024'); print('Conexión OK')"

# 4. Arrancar el servidor de desarrollo
py manage.py runserver

# 5. Abrir en el navegador
# http://127.0.0.1:8000
```

### URLs disponibles
| URL | Vista | Descripción |
|---|---|---|
| `/` | `dashboard` | KPIs globales, distribución, top5/bottom5 |
| `/ranking/` | `ranking` | Tabla completa con filtros |
| `/segmentos/` | `segmentos` | Comparativo por segmento |
| `/cooperativa/<ruc>/` | `cooperativa_detalle` | Detalle e histórico por cooperativa |
| `/rakkun/` | `rakkun` | Chat con IA |
| `/api/rakkun/preguntar` | `rakkun_chat` | Proxy API (POST) |

---

## 12. Despliegue en VPS

### Servidor
- **IP**: 157.230.62.218
- **SSH port**: 443
- **OS**: Ubuntu (DigitalOcean Droplet)

### Stack en producción
```
Nginx (reverse proxy, puerto 80/443)
    └── Gunicorn (WSGI, puerto 8000)
            └── Django (seps_web)
                    └── PostgreSQL (puerto 5432, seps_user)

Rakkun FastAPI (Gunicorn/Uvicorn, puerto 8001)
```

### Pasos de despliegue
```bash
# 1. Conectarse al VPS
ssh -p 443 root@157.230.62.218

# 2. Actualizar código (git pull o scp)
cd /var/www/seps_web
git pull origin main

# 3. Configurar variables de entorno para producción
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=seps_user
export DB_PASS=seps2024

# 4. Recolectar archivos estáticos (si aplica)
python manage.py collectstatic --noinput

# 5. Reiniciar Gunicorn
systemctl restart gunicorn

# 6. Verificar Nginx
systemctl status nginx
```

### Diferencias local vs producción
| Parámetro | Local | VPS |
|---|---|---|
| `DEBUG` | `True` | `False` |
| `ALLOWED_HOSTS` | `['localhost', '127.0.0.1']` | `['157.230.62.218', 'tudominio.com']` |
| `DB_PORT` | `5434` | `5432` |
| `DB_USER` | `postgres` | `seps_user` |

---

## 13. Control de versiones — GitHub

### Repositorio
- **URL:** `https://github.com/TU_USUARIO/IntelliCoop`
- **Rama principal:** `main`
- **Visibilidad:** Public (portafolio CV)

### Qué SÍ va al repositorio

```
seps_web/           ← Todo el código Django + Rakkun API
Notebooks/          ← Análisis descriptivo, CAMEL, clustering
Scripts/            ← ETL, consolidación, descarga SEPS
docs/               ← Documentación técnica (este archivo)
iniciar_intellicoop.bat
fix_model3.bat
.gitignore
.env.example        ← Plantilla sin valores reales
```

### Qué NO va al repositorio (excluido en `.gitignore`)

| Ruta | Razón |
|---|---|
| `SEPS_EEFF.duckdb` | 1.7 GB — excede límite GitHub |
| `Base de datos/` | 3.1 GB — datos crudos SEPS |
| `Modelo Avatar/` | 1.7 GB — binarios Live2D |
| `seps_web/.env` | Contiene API keys y contraseñas |
| `seps_web/db.sqlite3` | Base de datos de desarrollo |
| `seps_web/staticfiles/` | Generado por `collectstatic` |
| `__pycache__/`, `*.pyc` | Caché Python |
| `ml_models/*.pkl` | Modelos ML (se transfieren por SCP) |

### Flujo de trabajo Git

```powershell
# Primer push (una sola vez)
git init
git add .
git commit -m "feat: IntelliCoop v1.0 — Django CAMEL + Rakkun Avatar + TTS"
git remote add origin https://github.com/TU_USUARIO/IntelliCoop.git
git branch -M main
git push -u origin main
```

```powershell
# Actualizaciones diarias
git add .
git commit -m "feat: descripcion del cambio"
git push
```

```bash
# Deploy en VPS (después de cada push)
cd /var/www/intellicoop && git pull && systemctl restart intellicoop
```

### Errores encontrados en el primer push y soluciones

**Error 1 — Archivo > 100 MB:**
```
remote: error: File seps_web/static/live2d/rakkun/RakkunFormal.cmo3 is 102.94 MB
```
`RakkunFormal.cmo3` es el fuente de Cubism Editor — no se necesita en el servidor.
**Fix:** agregar `*.cmo3` al `.gitignore` + `git rm --cached "ruta/archivo.cmo3"` + `git commit --amend`.

**Error 2 — GitHub Push Protection (secreto detectado):**
```
remote: error: GH013: Repository rule violations found — Push cannot contain secrets
remote: OpenRouter API Key detectada en seps_web/start_local.ps1:9
```
La API key de OpenRouter estaba hardcodeada en `start_local.ps1`.
**Fix:** refactorizar el script para leer del `.env` con `Get-Content` en PowerShell:
```powershell
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]*)\s*=\s*(.*)\s*$') {
        [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
    }
}
```
Regla: **nunca hardcodear API keys en scripts**, siempre usar `.env`.

### Archivos grandes al VPS (primera vez, por SCP)

```powershell
# Ejecutar desde PowerShell local (puede tardar 10-15 min)

# DuckDB (necesario para Rakkun API si usa datos locales)
scp -P 443 "...\SEPS_EEFF.duckdb" root@157.230.62.218:/var/www/intellicoop/

# Modelo Live2D (necesario para Rakkun Avatar)
scp -P 443 -r "...\Modelo Avatar" root@157.230.62.218:/var/www/intellicoop/
```

---

## 14. Módulo de Predicción ML

### Estado actual
Página `/prediccion/` implementada como placeholder (badge "EN DESARROLLO").

### Diseño aprobado — 8 fases

| Fase | Nombre | Técnica | Output |
|---|---|---|---|
| A | Feature Engineering | Pandas + DuckDB | Dataset CAMEL mensual por coop |
| B | Mapa Geográfico | RUC → provincia + Leaflet.js | Mapa Ecuador con cooperativas |
| C | Análisis COVID-19 | Estadística descriptiva | Gráficos 2019-2022 impacto |
| D | Clustering | PCA + K-Means + SHAP | Grupos de riesgo + visualización |
| E | Predicción Morosidad | Holt-Winters + backtesting | Serie temporal proyectada |
| F | Alerta Temprana | Random Forest + SHAP + CV temporal | Clasificación binaria riesgo |
| G | Detección Anomalías | Isolation Forest | Coops con comportamiento atípico |
| H | Integración Web | Django + Chart.js + Leaflet.js | Pestaña Predicción completa |

### Arquitectura ML local → VPS

```
PC local (i7-10H, 32GB RAM, RTX 3050)
    │  Entrenamiento en DuckDB (31M filas) o PostgreSQL
    │  Notebooks Jupyter → generar artefactos .pkl
    ▼
ml_models/
    ├── morosidad_model.pkl
    ├── early_warning_rf.pkl
    ├── isolation_forest.pkl
    └── pca_kmeans.pkl
    │
    │  SCP manual → VPS (no van a GitHub por tamaño)
    ▼
VPS /var/www/intellicoop/ml_models/
    │  Django carga .pkl con joblib en tiempo de inferencia
    │  Sin re-entrenar en VPS (solo inferencia)
    ▼
Endpoints Django /api/prediccion/... → Chart.js + Leaflet.js
```

### Variables codificación provincia (RUC Ecuador)

Los primeros 2 dígitos del RUC identifican la provincia sin datos externos:

| Código | Provincia | | Código | Provincia |
|---|---|---|---|---|
| 01 | Azuay | | 13 | Los Ríos |
| 02 | Bolívar | | 14 | Manabí |
| 03 | Cañar | | 15 | Morona Santiago |
| 04 | Carchi | | 16 | Napo |
| 05 | Cotopaxi | | 17 | Pichincha |
| 06 | Chimborazo | | 18 | Tungurahua |
| 07 | El Oro | | 19 | Zamora Chinchipe |
| 08 | Esmeraldas | | 20 | Galápagos |
| 09 | Guayas | | 21 | Sucumbíos |
| 10 | Imbabura | | 22 | Orellana |
| 11 | Loja | | 23 | Santo Domingo |
| 12 | Los Ríos | | 24 | Santa Elena |

---

## Historial de desarrollo

| Fecha | Tarea | Estado |
|---|---|---|
| 2026-06 | Setup inicial Django + PostgreSQL + DuckDB local | ✅ |
| 2026-06 | Vistas: dashboard, ranking, segmentos, detalle | ✅ |
| 2026-06 | Integración Rakkun API (Text-to-SQL proxy) | ✅ |
| 2026-06 | UI v1: navbar activo, favicon, animaciones fade-in | ✅ |
| 2026-06 | UI v1: filtros search/segmento en ranking | ✅ |
| 2026-06 | UI v1: breadcrumbs + radar CAMEL + threshold lines | ✅ |
| 2026-06 | UI v1: tabla comparativa en segmentos | ✅ |
| 2026-06 | UI v1: historial sessionStorage + toast en Rakkun | ✅ |
| 2026-06 | UI v1: 5° KPI activos del sistema en dashboard | ✅ |
| 2026-06 | **Rediseño total UI**: sidebar IntelliCoop, nueva paleta slate | ✅ |
| 2026-06 | Rediseño dashboard, ranking, segmentos, detalle, Rakkun | ✅ |
| 2026-06 | **Avatar Live2D Rakkun 2.0**: integración pixi-live2d-display en `rakkun_avatar.html` | ✅ |
| 2026-06 | Live2D: lip sync TTS + reconocimiento de voz + expresiones gestuales | ✅ |
| 2026-06 | Live2D: seguimiento de mirada (mousemove/mouseleave) | ✅ |
| 2026-06 | Live2D: outfit maid formal vía ticker PIXI (ParamMaid, EarOff, TailOnOff…) | ✅ |
| 2026-06 | Live2D: zoom a media cintura (positionModel scale=1.55, y×0.42) | ✅ |
| 2026-06 | Live2D: borrar mesh antifaz en Cubism Editor → tirantes visibles (MaskOnOff=0.0) | ✅ |
| 2026-06 | Live2D: cache busting cross-browser → rakkun_v2.moc3 + model3.json?v=3 | ✅ |
| 2026-06 | Live2D: fix_model3.bat — restaura Expressions+Motions tras cada re-exportación | ✅ |
| 2026-06 | Live2D: fix CSS flex chat panel (overflow:hidden + min-height:0) | ✅ |
| 2026-06 | Live2D: fix toggleVoz — stopLipSync + reset expresión al desactivar | ✅ |
| 2026-06 | **Google Cloud TTS**: voz femenina Neural `es-US-Neural2-A`, cross-browser | ✅ |
| 2026-06 | TTS: endpoint Django `/api/tts/` proxy seguro (API key en .env) | ✅ |
| 2026-06 | TTS: reproducción MP3 via `atob()` → Blob → `Audio.play()` | ✅ |
| 2026-06 | Fix Firefox: `dispatchEvent` con `{bubbles:true, cancelable:true}` | ✅ |
| 2026-06-29 | **Sidebar dinámico**: `context_processors.py` inyecta stats reales de DB en todos los templates | ✅ |
| 2026-06-29 | Context processor: caché 10 min para evitar hits por request, filtro `dc.estado = 'ACTIVA'` | ✅ |
| 2026-06-29 | **Página Predicción** `/prediccion/`: placeholder profesional con 4 KPIs skeleton, 3 model cards, chart skeleton | ✅ |
| 2026-06-29 | `iniciar_intellicoop.bat`: lanza Rakkun API + Django con doble clic, sin terminal manual | ✅ |
| 2026-06-29 | **GitHub**: `.gitignore` configurado (excluye DuckDB 1.7GB, Base de datos 3.1GB, Modelo Avatar 1.7GB, .env) | ✅ |
| 2026-06-29 | `.env.example`: plantilla con todas las variables (incluye `GOOGLE_TTS_KEY`, `SECRET_KEY`) | ✅ |
| 2026-06-29 | **Plan ML aprobado**: 8 fases (Feature Eng → Mapa → COVID → Clustering → Morosidad → Alerta → Anomalías → Web) | ✅ |
| 2026-06-29 | Arquitectura ML: entrenamiento local DuckDB/PostgreSQL → .pkl → SCP al VPS → inferencia Django | ✅ |
| 2026-06-30 | **GitHub push exitoso**: repo público `github.com/tigreraph/IntelliCoop` | ✅ |
| 2026-06-30 | Fix push #1: `RakkunFormal.cmo3` (102 MB) excedía límite GitHub 100 MB → agregar `*.cmo3` al `.gitignore` + `git rm --cached` | ✅ |
| 2026-06-30 | Fix push #2: GitHub Push Protection detectó OpenRouter API key hardcodeada en `start_local.ps1` | ✅ |
| 2026-06-30 | `start_local.ps1` refactorizado: lee credenciales desde `.env` con `Get-Content` → sin secretos en código | ✅ |
| 2026-06-30 | `.env.example` actualizado con `OPENROUTER_KEY` | ✅ |
| 2026-06-30 | **Deploy VPS exitoso** — IntelliCoop activo en http://157.230.62.218 | ✅ |
| 2026-06-30 | Fix deploy: puerto 8000 ocupado por Gunicorn viejo → `fuser -k 8000/tcp` | ✅ |
| 2026-06-30 | Servicios systemd: `intellicoop.service` + `rakkun-api.service` con `EnvironmentFile` | ✅ |
| 2026-06-30 | Nginx configurado: static files directo, proxy a Gunicorn en 127.0.0.1:8000 | ✅ |
| 2026-06-30 | **Fix Chat Rakkun #1**: `TypeError: keys must be str` en `ejecutar_sql` — `RealDictCursor` devolvía tipo psycopg2 como clave | ✅ |
| 2026-06-30 | **Fix Chat Rakkun #2**: Markdown pipe tables `\| col \|` en respuesta — SYSTEM_PASO2 actualizado para prohibir tablas markdown | ✅ |
| 2026-06-30 | Django proxy timeout aumentado de 30s a 90s (`rakkun_chat`) para acomodar latencia DeepSeek V3 | ✅ |
| 2026-06-30 | **Fix Chat Rakkun #3 (definitivo)**: reemplazado `RealDictCursor` por cursor normal + `cur.description` en `ejecutar_sql` — claves garantizadas como strings Python puros | ✅ |
| 2026-06-30 | `_serialize_val()` helper: convierte `Decimal`, `date`, `datetime` a primitivos JSON-serializables antes de devolver filas | ✅ |
| 2026-06-30 | `limpiar_sql()` mejorado: agrega `LIMIT 50` por defecto cuando el SQL generado por el LLM no incluye ningún LIMIT (corrige queries genéricas sin número) | ✅ |
| 2026-06-30 | Nginx `proxy_read_timeout` aumentado de 60s a 120s — evitaba cortar respuestas antes del timeout Django de 90s | ✅ |
| 2026-07-01 | **Dominio propio**: `intellicoop.lat` adquirido en Namecheap ($2/año, TLD .lat para Latinoamérica) | ✅ |
| 2026-07-01 | DNS configurado: 2 registros A (`@` y `www`) apuntando a 157.230.62.218 | ✅ |
| 2026-07-01 | **HTTPS con Let's Encrypt**: certificado SSL instalado via Certbot para `intellicoop.lat` y `www.intellicoop.lat` | ✅ |
| 2026-07-01 | Fix SSL: SSH ocupaba puerto 443 → movido a puerto 2222, liberando 443 para Nginx HTTPS | ✅ |
| 2026-07-01 | `ALLOWED_HOSTS` actualizado con dominio en `.env` del VPS | ✅ |
| 2026-07-01 | **IntelliCoop en producción**: https://intellicoop.lat — dominio + HTTPS + datos reales SEPS | ✅ |

---

*Documentación generada el 2026-06-24 · Actualizada el 2026-07-01 · IntelliCoop v1.4 — EN PRODUCCIÓN · https://intellicoop.lat*
