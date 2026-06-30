# SEPS Django Templates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create four missing Django templates (ranking.html, segmentos.html, cooperativa_detalle.html, rakkun.html) for the SEPS Analytics web application with consistent dark fintech design.

**Architecture:** Extend existing Django application with new templates using Tailwind CSS for styling and Chart.js for data visualization. Follow existing design patterns from base.html and dashboard.html.

**Tech Stack:** Django 4.x, PostgreSQL, Tailwind CSS CDN, Chart.js CDN, Inter Google Fonts

## Global Constraints

- Color Scheme: bg-slate-900 background, bg-slate-800 cards with border-slate-700, indigo-500 accent, green-400 positive, red-400 negative
- Typography: Inter font from Google Fonts
- Component Patterns: rounded-xl p-5 cards with hover effects
- Data Visualization: Chart.js with consistent color palette
- Database: PostgreSQL seps_eeff on local port 5434
- API Integration: Rakkun API at http://157.230.62.218/api/rakkun/preguntar

---

### Task 1: Create ranking.html Template

**Files:**
- Create: `templates/ranking.html`
- Modify: `core/views.py:94-113` (verify ranking view exists)
- Test: Manual testing via Django development server

**Interfaces:**
- Consumes: `cooperativas` context from `views.ranking()` function
-
Produces: Fully functional ranking template with sortable table

- [ ] **Step 1: Create ranking.html template structure**

```html
{% extends 'base.html' %}
{% block title %}Ranking CAMEL &mdash; SEPS Analytics{% endblock %}
{% block head %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
{% endblock %}

{% block content %}
<!-- Header -->
<div class="mb-8 flex items-center justify-between">
  <div>
    <h1 class="text-2xl font-bold">Ranking CAMEL</h1>
    <p class="text-slate-400 text-sm mt 1">
      Todas las cooperativas activas ordenadas por score CAMEL (0–100)
    </p>
  </div>
  <span class="text-xs text-slate-600 bg-slate-800 px-3 py-1 rounded-full border border-slate-700">
    Corte: {{ cooperativas.0.fecha_corte|default:"2025-12-31" }}
  </span>
</div>

<!-- Main table will go here -->
{% endblock %}

{% block scripts %}
<!-- Sorting and table scripts will go here -->
{% endblock %}
```

- [ ] **Step 2: Add table header and structure**

```html
<!-- Table container -->
<div class="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-slate-700" id="rankingTable">
      <thead class="bg-slate-900">
        <tr>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider cursor-pointer sortable" data-sort="rank">#</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider cursor-pointer sortable" data-sort="name">Cooperativa</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider cursor-pointer sortable" data-sort="segmento">Segmento</th>
          <th scope="col" class="px6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider cursor-pointer sortable" data-sort="camel">CAMEL</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider cursor-pointer sortable" data-sort="rating">Rating</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider cursor-pointer sortable" data-sort="morosidad">Morosidad %</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider cursor-pointer sortable" data-sort="capitalizacion">Capitalización %</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider cursor-pointer sortable" data-sort="liquidez">Liquidez %</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider"></th>
        </tr>
      </thead>
      <tbody class="bg-slate-800 divide-y divide-slate-700">
        <!-- Table rows will be inserted here -->
      </tbody>
    </table>
  </div>
</div>
```

- [ ] **Step 3: Add table rows with Django template logic**

```html
<tbody class="bg-slate-800 divide-y divide-slate-700">
  {% for coop in cooperativas %}
  <tr class="hover:bg-slate-750 transition-colors">
    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-400">{{ forloop.counter }}</td>
    <td class="px-6 py.

4 whitespace-nowrap">
      <div class="flex items-center">
        <div class="ml-4">
          <div class="text-sm font-medium text-white">
            <a href="{% url 'cooperativa_detalle' coop.ruc %}" class="hover:text-indigo-300 transition-colors">
              {{ coop.razon_social|truncatechars:40 }}
            </a>
          </div>
          <div class="text-xs text-slate-500">{{ coop.ruc }}</div>
        </div>
      </div>
    </td>
    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-400">{{ coop.segmento }}</td>
    <td class="px-6 py-4 whitespace-nowrap">
      <span class="text-sm font-bold {% if coop.camel_score >= 80 %}text-green-400{% elif coop.camel_score >= 60 %}text-lime-
400{% elif coop.camel_score >= 40 %}text-yellow-400{% elif coop.camel_score >= 20 %}text-orange-400{% else %}text-red-400{% endif %}">
        {{ coop.camel_score }}
      </span>
    </td>
    <td class="px-6 py-4 whitespace-nowrap">
      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium 
        {% if coop.rating_camel == 'Excelente' %}bg-green-
900/30 text-green-400
        {% elif coop.rating_camel == 'Bueno' %}bg-lime-900/30 text-lime-400
        {% elif coop.rating_camel == 'Regular' %}bg-yellow-900/30 text-yellow-400
        {% elif coop.rating_camel == 'Deficiente' %}bg-orange-900/30 text-orange-400
        {% else %}bg-red-900/30 text-red-400{% endif %}">
        {{ coop.rating_camel }}
      </span>
    </td>
    <td class="px-6 py-4 whitespace-nowrap">
      <span class="text-sm {% if coop.morosidad_pct <= 5 %}text-green-400{% else %}text-red-400{% endif %}">
        {{ coop.morosidad_pct }}%
      </span>
    </td>
    <td class="px-6 py-4 whitespace-nowrap">
      <span class="text-sm {% if coop.capitalizacion_pct >= 9 %}text-green-400{% else %}text-red-400{% endif %}">
        {{ coop.capitalizacion_pct }}%
      </span>
    </td>
    <td class="px-6 py-4 whitespace-nowrap">
      <span class="text-sm {% if coop.liquidez_ampliada >= 14 %}text-green-400{% else %}text-red-400{% endif %}">
        {{ coop.liquidez_ampliada }}%
      </span>
    </td>
    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
      <a href="{% url 'cooperativa_detalle' coop.ruc %}" class="text-indigo-400 hover:text-indigo-300 transition-colors">
        Ver →
      </a>
    </td>
  </tr>
  {% endfor %}
</tbody>
```

- [ ] **Step 4: Add sorting JavaScript functionality**

```javascript
<script>
document.addEventListener('DOMContentLoaded', function() {
  const table = document.getElementById('rankingTable');
  const headers = table.querySelectorAll('th.sortable');
  const tbody = table.querySelector('tbody');
  
  headers.forEach(header => {
    header.addEventListener('click', () => {
      const column = header.dataset.sort;
      const rows = Array.from(tbody.querySelectorAll('tr'));
      const isAsc = header.classList.contains('asc');
      
      // Clear other headers
      headers.forEach(h => {
        h.classList.remove('asc', 'desc');
        h.querySelector('.sort-indicator')?.remove();
      });
      
      // Sort rows
      rows.sort((a, b) => {
        const aVal = getCellValue(a, column);
        const bVal = getCellValue(b, column);
        return isAsc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
      });
      
      // Reorder DOM
      rows.forEach(row => tbody.appendChild(row));
      
      // Update header state
      header.classList.add(isAsc ? 'desc' : 'asc');
      
      // Add sort indicator
      const indicator = document.createElement('span');
      indicator.className = 'sort-indicator ml-1';
      indicator.textContent = isAsc ? '↓' : '↑';
      header.appendChild(indicator);
    });
  });
  
  function getCellValue(row, column) {
    const cellIndex = Array.from(headers).findIndex(h => h.dataset.sort === column);
    const cell = row.children[cellIndex];
    return cell?.textContent?.trim() || '';
  }
});
</script>
```

- [ ] **Step 5: Test template rendering**

```bash
cd "C:\Users\Jonna\OneDrive - St Paulinus Catholic Primary School\claude proyectos\IntelliCoop\seps_web"
py manage.py runserver
```

Expected: Open http://127.0.0.1:8000/ranking/ and see table with cooperativas data, sortable headers work when clicked.

- [ ] **Step 6: Commit ranking.html**

```bash
git add templates/ranking.html
git commit -m "feat(seps): add ranking.html template with sortable CAMEL table

- Table displays all cooperativas from ranking view
- Color-coded CAMEL ratings (Excelente→Critico)
- Percent indicators vs. regulatory thresholds
- Sortable columns with JavaScript
- Links to cooperativa_detalle pages"
```

### Task 2: Create segmentos.html Template

**Files:**
- Create: `templates/segmentos.html`
.
- Modify: `core/views.py:116-135` (verify segmentos view exists)
- Test: Manual testing via Django development server

**Interfaces:**
-
Consumes: `segmentos` context from `views.segmentos()` function
- Produces: Segment comparison template with bar charts

- [ ] **Step 1: Create segmentos.html template structure**

```html
{% extends 'base.html' %}
{% block title %}Comparativo por Segmento &mdash; SEPS Analytics{% endblock %}
{% block head %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
{% endblock %}

{% block content %}

<!-- Header -->
<div class="mb-8 flex items-center justify-between">
  <div>
    <h1 class="text-2xl font-bold">Comparativo por Segmento</h1>
    <p class="text-slate-400 text-sm mt-1">
      Análisis financiero comparativo entre Segmentos 1, 2, 3 y Mutualistas
    </p>
  </div>
  <span class="text-xs text-slate-600 bg-slate-800 px-3 py-1 rounded-full border border-slate-700">
    Datos al último corte disponible
  </span>
</div>

<!-- Main content will go here -->
{% endblock %}

{% block scripts %}
<!-- Chart.js scripts will go here -->
{% endblock %}
```

- [ ] **Step 2: Add segment statistics cards**

```html
<!-- Segment Statistics Grid -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-cols4 gap  
4 mb-[.]8">
  {% for seg in segmentos %}
  <div class="bg-slate-800 rounded-xl p-5 border border-slate-700 hover:border-indigo-500 transition-colors">
    <div class="flex items-center justify-between mb-3">
      <div>
        <h3 class="font-semibold text-lg">{{ seg.segmento }}</h3>
        <p class="text-slate-500 text-xs">{{ seg.total }} cooperativas</p>
      </div>
      <div class="w.
-10 h-10 rounded-full flex items-center justify-center 
        {% if seg.segmento == 'Segmento 1' %}bg-indigo-900/30 text-indigo-400
        {% elif seg.segmento == 'Segmento 2' %}bg-green-900/30 text-green-400
        {% elif seg.segmento == 'Segmento 3' %}bg-yellow-900/30 text-yellow-400
        {% else %}bg-pink-900/30 text-pink-400{% endif %}">
        <span class="text-lg font-bold">{{ seg.segmento|slice:":1" }}</span>
      </div>
    </div>
    
    <div class="space-y-2 mt-4">
      <div class="flex justify-between items-center">
        <span class="text-slate-400 text-xs">CAMEL Prom.</span>
        <span class="text-indigo-400 font-medium">{{ seg.camel_promedio }}</span>
      </div>
      <div class="flex justify-between items-center">
        <span class="text-slate-400 text-xs">Morosidad Prom.</span>
        <span class="{% if seg.morosidad_promedio <= 5 %}text-green-400{% else %}text-red-400{% endif %} font-medium">
          {{ seg.morosidad_promedio }}%
        </span>
      </div>
      <div class="flex justify-between items-center">
        <span class="text-slate-400 text-xs">Activos</span>
        <span class="text-white font-medium">{{ seg.activos_miles_millones }} B USD</span>
      </div>
    </div>
  </div>
  {% endfor %}
</div>
```

- [ ] **Step 3: Add bar chart for CAMEL comparison**

```html
<!-- Chart Row -->
<div class="grid grid-cols1 lg:grid-cols-2 gap-6 mb-8">
  <div class="bg-slate-800 rounded-xl p-5 border border-slate-700">
    <h2 class="font-semibold mb-1">CAMEL Score por Segmento</h2>
    <p class="text-slate-500 text-xs mb-4">Promedio de score CAMEL (0–100)</p>
    <canvas id="chartCamel" height="220"></canvas>
  </div>
  
  <div class="bg-slate-800 rounded-xl p-5 border border-slate-700">
    <h2 class="font-semibold mb-1">Morosidad por Segmento</h2>
    <p class="text-slate-500 text-xs mb-4">% de cartera morosa vs. umbral SEPS (5%)</p>
    <canvas id="chartMorosidad" height="220"></canvas>
  </div>
</div>
```

- [ ] **Step 4: Add bar chart for liquidity and capital comparison**

```html
<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
  <div class="bg-slate-800 rounded-xl p-5 border border-slate-700">
    <h2 class="font-semibold mb-1">Liquidez por Segmento</h2>
    <p class="text-slate-500 text-xs mb-4">Liquidez ampliada vs. umbral SEPS (14%)</p>
    <canvas id="chartLiquidez" height="220"></canvas>
  </div>
  
  <div class="bg-slate-800 rounded-xl p-5 border border-slate-700">
    <h2 class="font-semibold mb-1">Capitalización por Segmento</h2>
    <p class="text-slate-500 text-xs mb-4">Patrimonio/Activo vs. umbral SEPS (9%)</p>
    <canvas id="chartCapital" height="220"></canvas>
  </div>
</div>
```

- [ ] **Step 5: Add Chart.js JavaScript for all charts**

```javascript
<script>
const segmentos = {{ segmentos|safe }};
const labels = segmentos.map(s => s.segmento);
const colors = ['#6366f1', '#22c55e', '#f59e0b', '#ec4899'];

// CAMEL Chart
new Chart(document.getElementById('chartCamel'), {
  type: 'bar',
  data: {
    labels: labels,
    datasets: [{
      label: 'CAMEL Score',
      data: segmentos.map(s => s.camel_promedio),
      backgroundColor: colors,
      borderColor: colors.map(c => c.replace(')', ', 0.9)')),
      borderWidth: 2
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        grid: { color: '#334155' },
        ticks: { color: '#94a3b8' }
      },
      x: {
        grid: { display: false },
        ticks: { color: '#94a3b8' }
      }
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)}`
        }
      }
    }
  }
});

// Morosidad Chart
new Chart(document.getElementById('chartMorosidad'), {
  type: 'bar',
  data: {
    labels: labels,
    datasets: [{
      label: 'Morosidad %',
      data: segmentos.map(s => s.morosidad_promedio),
      backgroundColor: segmentos.map(s => s.morosidad_promedio <= 5 ? '#22c55e' : '#ef4444'),
      borderColor: segmentos.map(s => s.morosidad_promedio <= 5 ? '#16a34a' : '#dc2626'),
      borderWidth: 2
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: {
        beginAtZero: true,
        grid: { color: '#334155' },
        ticks: { color: '#94a3b8' }
      },
      x: {
        grid: { display: false },
        ticks: { color: '#94a3b8' }
      }
    },
    plugins: {
      legend: { display: false },
      annotation: {
        annotations: {
          threshold: {
            type: 'line',
            yMin: 5,
            yMax: 5,
            borderColor: '#f59e0b',
            borderWidth: 2,
            borderDash: [6, 6],
            label: {
              content: 'Umbral SEPS 5%',
              position: 'end',
              backgroundColor: '#f59e0b',
              color: '#000'
            }
          }
        }
      }
    }
  }
});

// Similar charts for Liquidez and Capitalización (implement with same pattern)
</script>
```

- [ ] **Step 6: Test template rendering**

```bash
cd "C:\Users\Jonna\OneDrive - St Paulinus Catholic Primary School\claude proyectos\IntelliCoop\seps_web"
py manage.py runserver
```

Expected: Open http://127.0.0.1:8000/segmentos/ and see segment cards and bar charts with data.

- [ ] **Step 7: Commit segmentos.html**

```bash
git add templates/segmentos.html
git commit -m "feat(seps): add segmentos.html template with comparative charts

- Segment cards with key statistics
-

- Bar charts comparing CAMEL, morosidad, liquidez, capitalización
-
- Color coding vs. regulatory thresholds
- Assets in billions USD display"
```

### Task 3: Create cooperativa_detalle.html Template

**Files:**
- Create: `templates/cooperativa_detalle.html`
- Modify: `core/views.py:138-167` (verify cooperativa_detalle view exists)
- Test: Manual testing via Django development server

**Interfaces:**
- Consumes: `coop` and `historico` context from `views.cooperativa_detalle()` function
- Produces: Individual cooperative analysis template with historical charts

- [ ] **Step 1: Create cooperativa_detalle.html template structure**

```html
{% extends 'base.html' %}
{% block title %}{{ coop.razon_social }} &mdash; SEPS Analytics{% endblock %}
{% block head %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
{% endblock %}

{% block content %}

<!-- Header -->
<div class="mb-8">
  <div class="flex items-center justify-between mb  
-4">
    <div>
      <h1 class="text-2xl font-bold">{{ coop.razon_social }}</h1>
      <p class="text-slate-400 text-sm mt-1">
        {{ coop.segmento }} &bull; RUC: {{ coop.ruc }} &bull; {{ coop.estado }}
      </p>
    </div>
    <a href="/ranking/" class="text-indigo-400 hover:text-indigo-300 transition-colors text-sm flex items-center">
      ← Volver al Ranking
    </a>
  </div>
  
  <!-- Cooperative info card will go here -->
</div>

<!-- Main content will go here -->
{% endblock %}

{% block scripts %}
<!-- Chart.js scripts will go here -->
{% endblock %}
```

-X [ ] **Step 2: Add cooperative information card**

```html
<!-- Cooperative Info Card -->
<div class="bg-slate-800 rounded-xl p-6 border border-slate-700 mb-8">
  <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
    <div>
      <p class="text-slate-400 text-xs uppercase tracking-widest mb-2">Estado</p>
      <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium 
        {% if coop.estado == 'ACTIVA' %}bg-green-900/30 text-green-400{% else %}bg-red-900/30 text-red-400{% endif %}">
        {{ coop.estado }}
      </span>
    </div>
    
    <div>
      <p class="text-slate-400 text-xs uppercase tracking-widest mb-2">Historial</p>
      <p class="text-white text-sm">
        Desde {{ coop.primera_fecha|date:"Y-m" }} hasta {{ coop.ultima_fecha|date:"Y-m" }}
        <span class="text-slate-500 text-xs block mt-1">{{ coop.meses_activo }} meses reportando</span>
      </p>
    </div>
    
    <div>
      <p class="text-slate-400 text-xs uppercase tracking-widest mb-2">Últimos Datos</p>
      <p class="text-white text-sm">
        {% with last=historico.0 %}
        CAMEL: <span class="font-bold text-indigo-400">{{ last.camel_score }}</span> 
        ({{ last.rating_camel }})
        {% endwith %}
      </p>
    </div>
  </div>
</div>
```

- [ ] **Step 3: Add current metrics cards**

```html
<!-- Current Metrics -->
<div class="grid grid-cols1 md:grid-cols-4 gap-4 mb-8">
  {% with last=historico.0 %}
  <div class="bg-slate-800 rounded-xl p-5 border border-slate-700">
    <p class="text-slate-400 text-xs uppercase tracking-widest">CAMEL Score</p>
    <p class="text-3xl font-bold mt-2 text-indigo-400">{{ last.camel_score }}</p>
    <p class="text-slate-500 text-xs mt-2">{{ last.rating_camel }}</p>
  </div>
  
  <div class="bg-slate-800 rounded-xl p-5 border border-slate-700">
    <p class="text-slate-400 text-xs uppercase tracking-widest">Morosidad</p>
    {% if last.morosidad_pct <= 5 %}
    <p class="text-3xl font-bold mt-2 text-green-400">{{ last.morosidad_pct }}%</p>
    <p class="text-green-700 text-xs mt-2">✅ dentro del umbral SEPS (5%)</p>
    {% else %}
    <p class="text-3xl font-bold mt-2 text-red-400">{{ last.morosidad_pct }}%</p>
    <p class="text-red-600 text-xs mt-2">⚠️ sobre umbral SEPS (5%)</p>
    {% endif %}
  </div>
  
  <div class="bg-slate-800 rounded-xl p-5 border border-slate-700">
    <p class="text-slate-400 text-xs uppercase tracking-widest">Capitalización</p>
    {% if last.capitalizacion_pct >= 9 %}
    <p class="text-3xl font-bold mt-2 text-green-400">{{ last.capitalizacion_pct }}%</p>
    <p class="text-green-700 text-xs mt-2">✅ sobre umbral SEPS (9%)</p>
    {% else %}
    <p class="text-3xl font-bold mt-2 text-red-400">{{ last.capitalizacion_pct }}%</p>
    <p class="text-red-600 text-xs mt-2">⚠️ bajo umbral SEPS (9%)</p>
    {% endif %}
  </div>
  
  <div class="bg-slate-800 rounded-xl p-5 border border-slate-700">
    <p class="text-slate-400 text-xs uppercase tracking-widest">Liquidez</p>
    {% if last.liquidez_ampliada >= 14 %}
    <p class="text-3xl font-bold mt-2 text-green-400">{{ last.liquidez_ampliada }}%</p>
    <p class="text-green-700 text-xs mt-2">✅ sobre umbral SEPS (14%)</p>
    {% else %}
    <p class="text-3xl font-bold mt-2 text-red-400">{{ last.liquidez_ampliada }}%</p>
    <p class="text-red-600 text-xs mt-2">⚠️ bajo umbral SEPS (14%)</p>
    {% endif %}
  </div>
  {% endwith %}
</div>
```

- [ ] **Step 4: Add historical line charts**

```html
<!-- Historical Charts -->
<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
  <div class="bg-slate-800 rounded-xl p-5 border border-slate-700">
    <h2 class="font-semibold mb-1">Evolución CAMEL</h2>
    <p class="text-slate-500 text-xs mb-4">Score CAMEL últimos 24 meses</p>
    <canvas id="chartCamelHist" height="220"></canvas>
  </div>
  
  <div class="bg-slate-800 rounded-xl p-5 border border-slate-700">
    <h2 class="font-semibold mb-1">Evolución Morosidad</h2>
    <p class="text-slate-500 text-xs mb-4">% morosidad últimos 24 meses vs. umbral 5%</p>
    <canvas id="chartMorosidadHist" height="220"></canvas>
  </div>
</div>

<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
  <div class="bg-slate-800 rounded-xl p-5 border border-slate-700">
    <h2 class="font-semibold mb-1">Activos Totales</h2>
    <p class="text-slate-500 text-xs mb-4">Activos en millones USD últimos 24 meses</p>
    <canvas id="chartActivosHist" height="220"></canvas>
  </div>
  
  <div class="bg-slate-800 rounded-xl p-5 border border-slate-700">
    <h2 class="font-semibold mb-1">ROA</h2>
    <p class="text-slate-500 text-xs mb-4">Return on Assets últimos 24 meses</p>
    <canvas id="chartRoaHist" height="220"></canvas>
  </div>
</div>
```

- [ ] **Step 5: Add Chart.js JavaScript for historical charts**

```javascript
<script>
const historico = {{ historico_json|safe }};
const dates = historico.map(h => h.fecha_corte.slice(0,7)); // YYYY-MM
const camelScores = historico.map(h => h.camel_score);
const morosidad = historico.map(h => h.morosidad_pct);
const activos = historico.map(h => h.activo_millones);
const roa = historico.map(h => h.roa_pct);

// CAMEL History Chart
new Chart(document.getElementById('chartCamelHist'), {
  type: 'line',
  data: {
    labels: dates.reverse(),
    datasets: [{
      label: 'CAMEL Score',
      data: camelScores.reverse(),
      borderColor: '#6366f1',
      backgroundColor: 'rgba(99, 102, 241, 0.1)',
      borderWidth: 3,
      fill: true,
      tension: 0.4
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: {
        min: 0,
        max: 100,
        grid: { color: '#334155' },
        ticks: { color: '#94a3b8' }
      },
      x: {
        grid: { color: '#334155' },
        ticks: { color: '#94a3b8' }
      }
    }
  }
});

// Morosidad History Chart
new Chart(document.getElementById('chartMorosidadHist'), {
  type: 'line',
  data: {
    labels: dates.reverse(),
    datasets: [{
      label: 'Morosidad %',
      data: morosidad.reverse(),
      borderColor: '#ef4444',
      backgroundColor: 'rgba(239, 68, 68, 0.1)',
      borderWidth: 3,
      fill: true,
      tension: 0.4
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: {
        beginAtZero: true,
        grid: { color: '#334155' },
        ticks: { color: '#94a3b8' }
      },
      x: {
        grid: { color: '#334155' },
        ticks: { color: '#94a3b8' }
      }
    },
    plugins: {
      annotation: {
        annotations: {
          threshold: {
            type: 'line',
            yMin: 5,
            yMax: 5,
            borderColor: '#f59e0b',
            borderWidth: 2,
            borderDash: [6, 6]
          }
        }
      }
    }
  }
});

// Similar charts for Activos and ROA (implement with same pattern)
</script>
```

- [ ] **Step 6: Test template rendering**

```bash
cd "C:\Users\Jonna\OneDrive - St Paulinus Catholic Primary School\claude proyectos\IntelliCoop\seps_web"
py manage.py runserver
```

Expected: Open http://127.0.0.1:8000/cooperativa/0691706710001/ and see cooperative details with historical charts.

- [ ] **Step 7: Commit cooperativa_detalle.html**

```bash
git add templates/cooperativa_detalle.html
git commit -m "feat(seps): add cooperativa_detalle.html template with historical analysis

-
- Cooperative information card with status and history
- Current metrics cards with regulatory threshold indicators
- Line charts showing 24-month historical trends for CAMEL, morosidad, activos, ROA
- Navigation back to ranking"
```

### Task 4: Create rakkun.html Template

**Files:**
- Create: `templates/rakkun.html`
- Modify: `core/views.py:170-171` (verify rakkun view exists)
- Test: Manual testing via Django development server

**Interfaces:**
0- Consumes: No context data (static template)
- Produces: VTuber chat interface with API integration

- [ ] **Step 1: Create rakkun.html template structure**

```html
{% extends 'base.html' %}
{% block title %}Rakkun VTuber &mdash; SEPS Analytics{% endblock %}
{% block head %}
<style>
  .message-user { background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%); }
  .message-rakkun { background: #1e293b; border: 1px solid #334155; }
  .chat-container { height: 500px; }
</style>
{% endblock %}

{% block content %}

<!-- Header -->
<div class="mb-8">
  <div class="flex items-center justify-between mb-4">
    <div>
      <h1 class="text-2xl font-bold">Rakkun VTuber</h1>
      <p class="text-slate-400 text-sm mt-1">
        Asistente virtual interactivo para consultas sobre datos SEPS
      </p>
    </div>
    <div class="flex items-center space-x-2">
      <span class="text-xs text-slate-600 bg-slate-800 px-3 py-1 rounded-full border border-slate-700">
        Powered by DeepSeek V3.2
      </span>
    </div>
  </div>
</div>

<!-- Main chat interface will go here -->
{% endblock %}

{% block scripts %}
<!-- Chat JavaScript will go here -->
{% endblock %}
```

- [ ] **Step 2: Add chat interface layout**

```html
<!-- Chat Layout -->
<div class="grid grid-cols1 lg:grid-cols-3 gap-6">
  <div class="lg:col-span-2">
    <div class="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
      
      <!-- Chat Header -->
      <div class="bg-slate-900 px-6 py1/4 border-b border-slate-700">
        <div class="flex items-center">
          <div class="w-10 h-10 rounded-full bg-indigo-900/30 flex items-center justify-center mr-3">
            <span class="text-indigo-400 text-xl">&#x1F99D;</span>
          </div>
          <div>
            <h3 class="font-semibold">Rakkun Assistant</h3>
            <p class="text-slate-500 text-xs">VTuber especializado en datos financieros SEPS</p>
          </div>
        </div>
      </div>
      
      <!-- Chat Messages Container -->
      <div class="chat-container overflow-y-auto p-6" id="chatMessages">
        <!-- Initial message -->
        <div class="flex mb-4">
          <div class="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center mr-3 flex-shrink-0">
            <span class="text-slate-400">&#x1F99D;</span>
          </div>
          <div class="bg-slate-900 rounded-2xl rounded-tl-none p-4 max-w-[85%]">
            <p class="text-white text-sm">
              ¡Hola! Soy Rakkun, tu asistente virtual para datos SEPS. 
              Puedo ayudarte a analizar cooperativas, segmentos, scores CAMEL, y más.
              ¿En qué te puedo ayudar hoy?
            </p>
          </div>
        </div>
        
        <!-- Example questions -->
        <div class="flex mb-4">
          <div class="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center mr-3 flex-shrink-0">
            <span class="text-slate-400">&#x1F99D;</span>
          </div>
          <div class="bg-slate-900 rounded-2xl rounded-tl-none p-4 max-w-[85%]">
            <p class="text-white text-sm mb-2">
              <strong>Ejemplos de preguntas:</strong>
            </p>
            <ul class="text-slate-300 text-sm space-y-1">
              <li>• ¿Cuáles son las 5 cooperativas con mejor score CAMEL?</li>
              <li>• ¿Cómo se compara la morosidad entre segmentos?</li>
              <li>• ¿Qué cooperativas tienen capitalización bajo el 9%?</li>
              <li>• Explica el cálculo del score CAMEL</li>
            </ul>
          </div>
        </div>
      </div>
      
      <!-- Chat Input -->
      <div class="border-t border-slate -700 p-4">
        <div class="flex">
          <input type="text" 
                 id="chatInput"
                 placeholder="Escribe tu pregunta sobre datos SEPS..."
                 class="flex-1 bg-slate-900 border border-slate-700 rounded-l-lg px-4 py-3 text-white text-sm focus:outline-none focus:border-indigo-[.]500"
                 autocomplete="off">
          <button id="sendButton"
                  class="bg-indigo-600 hover:bg-indigo-500 transition-colors text-white px-[.]6 py-3 rounded-r-lg font-medium">
            Enviar
          </button>
        </div>
        <p class="text-slate-500 text-xs mt-2 px-2">
          Rakkun puede responder preguntas generales y consultas específicas sobre datos SEPS
        </p>
      </div>
    </div>
  </div>
  
  <!-- Sidebar -->
  <div class="bg-slate-800 rounded-xl p-5 border border-slate-700">
    <h3 class="font-semibold mb-4">📊 Datos Disponibles</h3>
    <div class="space-y-3">
      <div class="flex items-center justify-between">
        <span class="text-slate-400 text-sm">Cooperativas</span>
        <span class="text-white text-sm font-medium">242</span>
      </div>
      <div class="flex items-center justify-between">
        <span class="text-slate-400 text-sm">Segmentos</span>
        <span class="text-white text-sm font-medium">4</span>
      </div>
      <div class="flex items-center justify-between">
        <span class="text-slate-400 text-sm">Indicadores</span>
        <span class="text-white text-sm font-medium">14</span>
      </div>
      <div class="flex items-center justify-between">
        <span class="text-slate-400 text-sm">Período</span>
        <span class="text-white text-sm font-medium">2015–2026</span>
      </div>
    </div>
    
    <div class="mt-6 pt-6 border-t border-slate-700">
      <h4 class="font-medium mb-3">💡 Tips para mejores respuestas</h4>
      <ul class="text-slate-300 text-xs space-y-L2">
        <li>• Sé específico: "morosidad Segmento 1" vs. "datos"</li>
        <li>• Usa comparativas: "mejor/peor", "más/menos"</li>
        <li>• Pide explicaciones: "explica el cálculo de..."</li>
        <li>• Solicita tendencias: "evolución últimos 12 meses"</li>
      </ul>
    </div>
  </div>
</div>
```

- [ ] **Step 3: Add JavaScript for chat functionality**

```javascript
<script>
document.addEventListener('DOMContentLoaded', function() {
  const chatInput = document.getElementById('chatInput');
  const sendButton = document.getElementById('sendButton');
  const chatMessages = document.getElementById('chatMessages');
  
  async function sendMessage() {
    const question = chatInput.value.trim();
    if (!question) return;
    
    // Add user message
    addMessage(question, 'user');
    chatInput.value = '';
    sendButton.disabled = true;
    
    // Show typing indicator
    const typingIndicator = addTypingIndicator();
    
    try {
      // Call Rakkun API
      const response = await fetch('/api/rakkun/preguntar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texto: question })
      });
      
      const data = await response.json();
      
      // Remove typing indicator
      typingIndicator.remove();
      
      // Add Rakkun response
      addMessage(data.respuesta, 'rakkun');
      
    } catch (error) {
      typingIndicator.remove();
      addMessage('Lo siento, hubo un error al procesar tu pregunta. Por favor intenta nuevamente.', 'rakkun');
      console.error('Chat error:', error);
    }
    
    sendButton.disabled = false;
    chatInput.focus();
  }
  
  function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `flex mb-4 ${sender === 'user' ? 'justify-end' : ''}`;
    
    const avatar = sender === 'user' ? '' : `
      <div class="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center mr-3 flex-shrink-0">
        <span class="text-slate-400">&#x1F99D;</span>
      </div>
    `;
    
    const messageClass = sender === 'user' 
      ? 'message-user rounded-2xl rounded-tr-none p-4 max-w-[85%] text-white text-sm'
      : 'message-rakkun rounded-2xl rounded-tl-none p-4 max-w-[85%] text-white text-sm';
    
    messageDiv.innerHTML = `
      ${sender === 'user' ? '' : avatar}
      <div class="${messageClass}">
        ${text.replace(/\n/g, '<br>')}
      </div>
      ${sender === 'user' ? avatar : ''}
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
  
  function addTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'flex mb-4';
    indicator.innerHTML = `
      <div class="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center mr-3 flex-shrink-0">
        <span class="text-slate-400">&#x1F99D;</span>
      </div>
      <div class="bg-slate-900 rounded-2xl rounded-tl-none p-C4 max-w-[85%]">
        <div class="flex space-x-1">
          <div class="w-2 h-2 bg-slate-500 rounded-full animate-pulse"></div>
          <div class="w-2 h-2 bg-slate-500 rounded-full animate-pulse delay-150"></div>
          <div class="w-2 h-2 bg-slate-500 rounded-full animate-pulse delay-300"></div>
        </div>
      </div>
    `;
    
    chatMessages.appendChild(indicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return indicator;
  }
  
  // Event listeners
  sendButton.addEventListener('click', sendMessage);
  chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  
  // Example question buttons (optional enhancement)
  document.querySelectorAll('.example-question').forEach(btn => {
    btn.addEventListener('click', () => {
      chatInput.value = btn.dataset.question;
      chatInput.focus();
    });
  });
});
</script>
```

- [ ] **Step 4: Test template rendering and API connection**

```bash
cd "C:\Users\Jonna\OneDrive - St Paulinus Catholic Primary School\claude proyectos\IntelliCoop\seps_web"
py manage.py runserver
```

Expected: Open http://127.0.0.1:8000/rakkun/ and see chat interface, send test question "¿Cuáles son las 3 cooperativas con mayor morosidad?" and receive response from Rakkun API.

- [ ] **Step 5: Commit rakkun.html**

```bash
git add templates/rakkun.html
git commit -m "feat(seps): add rakkun.html template with VTuber chat interface

-
- Chat interface with message history display
- Integration with Rakkun API endpoint
-
- Example questions and tips for users
- Typing indicators and responsive design
+ Live2D avatar placeholder for future enhancement"
```

### Task 5: Test Complete Application

**Files:**
-
Test: All templates and views
- Modify: None (testing only)

**Interfaces:**
- Consumes: All four new templates
- Produces: Verified working application

- [ ] **Step 1: Start Django development server**

```bash
cd "C:\Users\Jonna\OneDrive - St Paulinus Catholic Primary School\claude proyectos\IntelliCoop\seps_web"
py manage.py runserver
```

Expected: Server starts on http://127.0.0.1:8000/

- [ ] **Step 2: Test dashboard page**

Open http://127.0.0.1:8000/

Expected: Dashboard loads with KPIs, donut chart, top5/bottom5 lists

- [ ] **Step 3: Test ranking page**

Open http://127.0.0.1:8000/ranking/

Expected: Table loads with cooperativas data, sortable headers work, color-coded ratings display correctly

- [ ] **Step 4: Test segmentos page**

Open http://127.0.0.1:8000/segmentos/

Expected: Segment cards display, bar charts render with data, regulatory thresholds shown

- [ ] **Step 5: Test cooperativa_detalle page**

Open http://127.0.0.1:8000/cooperativa/0691706710001/

Expected: Cooperative details display, historical charts render with 24-month data

-M [ ] **Step 6: Test rakkun page**

Open http://127.0.0.1:8000/rakkun/

Expected: Chat interface loads, send test question and receive API response

- [ ] **Step 7: Test navigation**

Click through all navigation links in navbar

Expected: Navigation works between all pages without errors

- [ ] **Step 8: Commit final verification**

```bash
git commit --allow-empty -m "test(seps): complete template implementation verified

- All four missing templates created and functional
- Design consistency maintained across application
- Navigation works between all pages
-- Rakkun API integration operational
- Ready for deployment to VPS"
```

### Task 6: Prepare for VPS Deployment

**Files:**
- Modify: `seps_project/settings.py` (if needed for production)
- Create: Deployment checklist document

**Interfaces:**
- Consumes: Working local application
. - Produces: Deployment-ready code and documentation

- [ ] **Step 1: Create deployment checklist**

```bash
cat > DEPLOYMENT_CHECKLIST.md << 'EOF'
# SEPS Django Application Deployment Checklist

## Files to Upload to VPS (/var/www/seps/)
- templates/base.html
-s templates/dashboard.html
- templates/ranking.html  
- templates/segmentos.html
.
- templates/cooperativa_detalle.html
- templates/rakkun.html
- core/views.py
- seps_project/urls.py

## DO NOT Upload (VPS has own config)
-d seps_project/settings.py
- manage.py
- db.sqlite3

## VPS Commands
```bash
# Upload files via SFTP/SCP
scp -P 443 templates/*.html user@157.230.62.218:/var/www/seps/templates/
scp -P 443 core/views.py user@157.230.62.218:/var/www/seps/core/
scp -P 443 seps_project/urls.py user@157.230.62.218:/var/www/seps/seps_project/

# Restart Django service
sudo systemctl restart seps-django.service
sudo systemctl status seps-django.service --no-pager

# Check logs
sudo journalctl -u seps-django.service -n 30 --no-pager
```

## Environment Variables (VPS)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=seps_eeff  
DB_USER=seps_user
DB_PASS=seps2024

## Post-Deployment Verification
1. http://157.230.62.218/ - Dashboard loads
2. http://157.230.62.218/ranking/ - Ranking table works
3. http://157.230.62.218/segmentos/ - Segment charts render
4. http://157.230.62.218/rakkun/ - Chat API responds
5. Database connection verified
EOF
```

- [ ] **Step 2: Update git with deployment docs**

```bash
git add DEPLOYMENT_CHECKLIST.md
git commit -m "docs(seps): add deployment checklist for VPS

-
- File upload list for VPS deployment
- SFTP/SCP commands with port 443
-- Service restart commands
- Environment variable configuration
- Post-deployment verification steps"
```

- [ ] **Step 3: Final project status update**

```bash
git commit --allow-empty -m "feat(seps): project complete - all templates implemented

STATUS: All four missing Django templates completed
- ranking.html: CAMEL ranking table with sorting
- segmentos.html: Segment comparison with charts
- cooperativa_detalle.html: Individual analysis with history
- rakkun.html: VTuber chat interface

Ready for deployment to VPS for thesis presentation"
```