# IntelliCoop — Rediseño UI + Corrección de Bugs
**Fecha:** 2026-06-26
**Proyecto:** SEPS Analytics Django Web Application
**Autor:** Jonnathan Tigre (Proyecto de Titulación)

---

## Estado Final del Proyecto

Todas las templates están implementadas, corregidas y rediseñadas con tema claro profesional.

| Template | Estado | Descripción |
|---|---|---|
| `base.html` | ✅ Rediseñado | Sistema CSS variables, sidebar indigo, topbar blanco |
| `dashboard.html` | ✅ Rediseñado | KPI cards, top5/bottom5, donut chart |
| `ranking.html` | ✅ Nuevo | Tabla sortable con búsqueda y filtros live |
| `segmentos.html` | ✅ Nuevo | 4 cards + 4 gráficos comparativos |
| `cooperativa_detalle.html` | ✅ Nuevo | Radar CAMEL + 5 gráficos históricos |
| `rakkun.html` | ✅ Nuevo | Chat UI con burbujas, typing dots, sidebar sugerencias |

---

## Stack Técnico

| Capa | Tecnología |
|---|---|
| Backend | Django 4.x + PostgreSQL (psycopg2 raw, sin ORM) |
| IA | FastAPI (Rakkun) + DeepSeek V3.2 via OpenRouter |
| Frontend | Tailwind CSS (CDN) + Chart.js + Tabler Icons |
| Tipografía | Inter (UI) + Fira Code (datos numéricos) |

### Puertos locales
- Django: `http://127.0.0.1:8000`
- Rakkun FastAPI: `http://127.0.0.1:8001`

### Comandos de inicio
```powershell
# Terminal 1 — Django
cd "...seps_web"
py manage.py runserver

# Terminal 2 — Rakkun API (con .env cargado)
cd "...seps_web"
py -m uvicorn rakkun_api:app --port 8001 --reload
```

---

## Sistema de Diseño

### Paleta de Colores (tema claro)

```css
:root {
  /* Fondos */
  --bg-base:    #f0f4f8;   /* página */
  --bg-card:    #ffffff;   /* tarjetas */
  --bg-card2:   #f8fafc;   /* secundario */

  /* Bordes */
  --border:     #e2e8f0;
  --border-dim: #f1f5f9;

  /* Acento */
  --indigo:     #6366f1;

  /* Semánticos */
  --green:      #10b981;   /* positivo / cumple umbral */
  --red:        #ef4444;   /* negativo / fuera de umbral */
  --amber:      #f59e0b;   /* advertencia */
  --sky:        #0ea5e9;   /* informativo */

  /* Texto */
  --text-1:     #0f172a;   /* primario */
  --text-2:     #1e293b;   /* secundario */
  --text-3:     #475569;   /* terciario */
  --text-4:     #94a3b8;   /* muted */
}
```

### Sidebar (indigo oscuro)
- Fondo: `linear-gradient(180deg, #4f46e5 0%, #312e81 100%)`
- Logo "IC": fondo blanco, texto `#4f46e5`
- Nav items: `rgba(255,255,255,.72)` default → `rgba(255,255,255,.96)` hover
- Active: `rgba(255,255,255,.16)` + indicador `#c7d2fe` izquierda
- Stats footer: labels `rgba(255,255,255,.5)`, valores `rgba(255,255,255,.9)`

### Tipografía
- **Inter**: toda la UI, navegación, etiquetas
- **Fira Code** (`.font-data`): todos los valores numéricos, porcentajes, RUCs, scores

### Componentes

#### Tarjetas
```css
.ic-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,.05);
  /* hover: borde indigo + glow suave */
}

.kpi-card {
  /* igual + kpi-accent (barra de color 3px arriba) */
  /* hover: translateY(-2px) */
}
```

#### Badges CAMEL (paleta pastel)
```css
.badge-excellent { background:#d1fae5; color:#065f46; border:1px solid #a7f3d0; }
.badge-good      { background:#ecfccb; color:#365314; border:1px solid #bef264; }
.badge-regular   { background:#fef3c7; color:#92400e; border:1px solid #fde68a; }
.badge-deficient { background:#ffedd5; color:#9a3412; border:1px solid #fdba74; }
.badge-critical  { background:#fee2e2; color:#991b1b; border:1px solid #fca5a5; }
```

#### Chart.js — Configuración tema claro
```javascript
const GRID = 'rgba(226,232,240,.9)';
const TT   = {
  backgroundColor: '#ffffff',
  borderColor: '#e2e8f0',
  borderWidth: 1,
  titleColor: '#0f172a',
  bodyColor: '#64748b',
  padding: 10
};
```

---

## Bugs Corregidos

### core/views.py
| Bug | Causa | Fix |
|---|---|---|
| `TypeError: argument of type 'NoneType'` | `fetchone()` → `dict(None)` | Check explícito `if row is None` |
| Connection leaks en todas las vistas | Sin `try/finally` | `try/finally: conn.close()` en las 5 vistas |
| Status 200 en errores de Rakkun | Sin manejo tipado | HTTPError→502, URLError→503, Exception→500 |
| `Http404` no importado | Import faltante | Agregado a imports |

### rakkun_api.py
| Bug | Fix |
|---|---|
| API key hardcodeada en código | `OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "")` |
| Connection leak en `ejecutar_sql` | `try/finally: conn.close()` |
| `KeyError` en respuesta de error OpenRouter | `_safe_content()` helper |
| `LIMIT ALL` / `LIMIT 0` sin sanitizar | `limpiar_sql()` con `cap_limit()` → máx 100 filas |

### templates/cooperativa_detalle.html (JavaScript)
| Bug | Fix |
|---|---|
| Score M: división por 0 cuando eficiencia_op_pct es null | `Math.max(last.eficiencia_op_pct, 1)` + guard null |
| Score A: NaN cuando morosidad es 0 o null | Guard `morosidad_pct > 0` antes de dividir |

### seps_project/settings.py
- `DEBUG` default cambiado de `True` a `False` (producción segura)

### templates/rakkun.html (Frontend)
- Frontend enviaba `{ mensaje: text }` pero backend espera `{ pregunta: text }` → corregido

---

## Arquitectura Rakkun IA

### Flujo de 2 turnos (DeepSeek V3.2 via OpenRouter)
```
Usuario escribe pregunta
    ↓
Django views.rakkun_chat() — POST /rakkun/chat/
    ↓
Rakkun FastAPI — POST /preguntar
    ↓
[Turno 1] NL → SQL: ¿necesita datos? → genera SELECT
    ↓
ejecutar_sql() → PostgreSQL seps_eeff (puerto 5434)
    ↓
[Turno 2] filas JSON → respuesta lenguaje natural amigable
    ↓
{ respuesta, sql_generado, tabla } → frontend
    ↓
renderMd() + buildTable() → burbuja chat
```

### Schema PostgreSQL disponible para Rakkun
```
dim_cooperativa: ruc, razon_social, segmento, estado, primera_fecha, ultima_fecha, meses_activo
dim_cuenta: cuenta, descripcion_cuenta, nivel
fact_indicadores: fecha_corte, ruc, activo_total, patrimonio, cartera_bruta,
  depositos, capitalizacion_pct, morosidad_pct, cobertura_pct, roa_pct,
  roe_pct, nim_pct, liquidez_ampliada, eficiencia_op_pct, n, camel_score, rating_camel
```

---

## Modelo CAMEL

| Dimensión | Peso | Indicador | Umbral SEPS Seg. 1 |
|---|---|---|---|
| C — Capital | 25% | Capitalización (patrimonio/activo) | ≥ 9% |
| A — Activos | 25% | Morosidad cartera | ≤ 5% |
| M — Gestión | 20% | Eficiencia operacional (inversa) | — |
| E — Rentabilidad | 15% | ROA | > 0% |
| L — Liquidez | 15% | Liquidez ampliada | ≥ 14% |

### Ratings CAMEL
| Score | Rating |
|---|---|
| 80–100 | Excelente |
| 60–79 | Bueno |
| 40–59 | Regular |
| 20–39 | Deficiente |
| 0–19 | Crítico |

---

## Variables de Entorno (.env)

```bash
# Django
SECRET_KEY=...
DEBUG=True                          # False en producción

# Base de datos SEPS (psycopg2 directo)
DB_HOST=localhost
DB_PORT=5434                        # local=5434 / VPS=5432
DB_USER=postgres
DB_PASS=seps2024

# Rakkun AI
OPENROUTER_KEY=sk-or-v1-...         # OpenRouter API key
RAKKUN_API_URL=http://localhost:8001/preguntar
```

---

## Pendiente

- [ ] Deploy VPS (actualizar templates en servidor)
- [ ] Live2D Rakkun 2.0 avatar en chat
- [ ] SSL + dominio en VPS
- [ ] Sidebar stats (226 coops, Dic 2025) dinámicos desde BD

---

## Sesión 2 — Auditoría UX con skill ui-ux-pro-max (2026-06-26)

### Diagnóstico del skill

| Issue | Severidad | Estado |
|---|---|---|
| Sin skeleton loader (pantalla blanca) | HIGH | ✅ Implementado (clase `.skeleton`) |
| Sin estado "sin resultados" en búsqueda | MEDIUM | ✅ Implementado en ranking.html |
| Sin feedback active/press en KPI cards | MEDIUM | ✅ `active: scale(0.97)` |
| `cursor:pointer` faltante en tablas | MEDIUM | ✅ `.ic-table tbody tr { cursor:pointer }` |
| `prefers-reduced-motion` ignorado | CRITICAL | ✅ Media query implementado |
| KPIs sin contexto visual vs umbral | MEDIUM | ✅ Bullet bars 4px bajo cada KPI |
| Nombres truncados sin tooltip | LOW | ✅ `title="{{ c.razon_social }}"` |

### CSS agregado en base.html

```css
/* Skeleton loader (disponible para todas las templates) */
@keyframes shimmer {
  from { background-position: -200% 0; }
  to   { background-position:  200% 0; }
}
.skeleton {
  background: linear-gradient(90deg, #f1f5f9 25%, #e8eef5 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
  border-radius: 6px; display: block;
}

/* Accesibilidad: sin animaciones si el SO las desactiva */
@media (prefers-reduced-motion: reduce) {
  *, ::before, ::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* Press feedback en KPI cards */
.kpi-card { cursor: pointer; }
.kpi-card:active { transform: scale(0.97); }

/* Cursor en filas de tabla */
.ic-table tbody tr { cursor: pointer; }
```

### Estado "sin resultados" — ranking.html

```html
<!-- Fila oculta, se muestra cuando applyFilters() no encuentra nada -->
<tr id="noResultsRow" style="display:none;">
  <td colspan="10" style="text-align:center;padding:40px 0;">
    <i class="ti ti-search-off" ...></i>
    <p>Sin resultados</p>
    <p>Intenta con otro nombre, RUC o segmento</p>
  </td>
</tr>
```

```javascript
// JS applyFilters actualizado
tbody.querySelectorAll('tr:not(#noResultsRow)').forEach(r => { ... });
document.getElementById('noResultsRow').style.display = vis === 0 ? '' : 'none';
```

### Bullet bars de umbral — dashboard.html

Barras de 4px animadas bajo cada KPI mostrando el contexto vs umbral SEPS:
- **CAMEL**: barra azul cielo al `{{ camel_promedio }}%` de 100
- **Morosidad cumple**: barra verde, proporcional a 5% máximo
- **Morosidad excede**: barra roja al 100%
- **Liquidez**: verde (cumple) o roja proporcional (incumple)

### Pendiente de sesiones futuras (skill recomienda)

| Mejora | Complejidad |
|---|---|
| `aria-label` en todos los `<canvas>` Chart.js | Baja |
| Fira Sans como fuente de cuerpo | Baja |
| Gauge circular para CAMEL score individual | Media |
| Line + Confidence Band en gráficos históricos | Media |
| Reemplazar emoji 🦝 por ícono SVG/Tabler en Rakkun | Baja |
| Responsive sidebar (colapsar en móvil 375px) | Alta |
