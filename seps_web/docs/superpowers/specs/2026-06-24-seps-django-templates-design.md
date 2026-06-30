# SEPS Django Templates Design Specification
**Date:** 2026-06-24
**Project:** SEPS Analytics Django Web Application
**Purpose:** Complete missing Django templates for university thesis project

## Overview
Complete the four missing Django templates for the SEPS Analytics web application to provide a comprehensive interface for analyzing Ecuadorian cooperative financial data.

## Current State
- ✅ `base.html` - Base template with navigation
- ✅ `dashboard.html` - Main dashboard with KPIs and charts  
- ❌ `ranking.html` - CAMEL ranking table
- ❌ `segmentos.html` - Segment comparison
- ❌ `cooperativa_detalle.html` - Individual cooperative analysis
- ❌ `rakkun.html` - VTuber interactive chat

## Design Principles

### 1. Visual Consistency
- **Color Scheme:** Dark fintech theme
  - Background: `bg-slate-900` (#0f172a)
  - Cards: `bg-slate-800` with `border border-slate-700`
  - Accent: `indigo-500` (#6366f1)
  - Positive: `green-400`, Negative: `red-400`
  - Text: white with `slate-400` for secondary
If- **Typography:** Inter font (Google Fonts)

### 2. Component Patterns
!
- Cards use `rounded-xl p-5` with hover effects
- KPIs display large numbers with descriptive text
- Charts use Chart.js with consistent color palette
- Tables are sortable with color-coded ratings

### 3. Data Visualization
- Chart.js for all charts
- Consistent color coding for metrics
- Regulatory threshold indicators
- Historical trend visualization

## Template Specifications

### 1. ranking.html - CAMEL Ranking Table

**Purpose:** Display sortable table of all cooperatives ranked by CAMEL score

**Data Context:**
```python
{
    'cooperativas': [
        {
            'razon_social': 'Cooperativa Name',
            'segmento': 'Segmento 1',
            'estado': 'ACTIVA',
            'camel_score': 85.432,
            'rating_camel': 'Excelente',
            'morosidad_pct': 3.21,
            'capitalizacion_pct': 10.5,
            'liquidez_ampliada': 18.2,
            'roa_pct': 1.8,
            'ruc': '0691706710001'
        },
        # ... more cooperativas
    ]
}
```

**Features:**
- Sortable table with clickable column headers
-
Color-coded CAMEL ratings (Excelente: green, Bueno: lime, Regular: yellow, Deficiente: orange, Critico: red)
- Link to individual cooperative detail pages via RUC
- Percent indicators vs. regulatory thresholds
- Export capability

### 2. segmentos.html - Segment Comparison

**Purpose:** Compare financial metrics across different segments

**Data Context:**
```python
{
    'segmentos': [
        {
            'segmento': 'Segmento 1',
            'total': 44,
            'camel_promedio': 78.5,
            'morosidad_promedio': 4.2,
            'capital_promedio': 11.3,
            'liquidez_promedio': 16.8,
            'roa_promedio': 1.2,
            'activos_miles_millones': 12.4
        },
        # ... other segments
    ]
}
```

**Features:**
- Bar charts comparing key metrics across segments
- Segment card with aggregate statistics
- Asset distribution visualization (billions USD)
- Comparative analysis summary

### 3. cooperativa_detalle.html - Individual Cooperative Analysis

**Purpose:** Detailed view of a single cooperative with historical trends

**Data Context:**
```python
{
    'coop': {
        'ruc': '0691706710001',
        'razon_social': 'Fernando Daquilema',
        'segmento': 'Segmento 1',
        'estado': 'ACTIVA',
        'primera_fecha': '2015-01-31',
        'ultima_fecha': '2025-12-31',
        'meses_activo': 132
    },
    'historico': [
        {
            'fecha_corte': '2025-12-31',
            'camel_score': 85.432,
            'rating_camel': 'Excelente',
            'morosidad_pct': 3.21,
            'capitalizacion_pct': 10.5,
            'liquidez_ampliada': 18.2,
            'roa_pct': 1.8,
            'activo_millones': 245.6
        },
        # ... 24 months of history
    ],
    'historico_json': '[{"fecha_corte": "...", ...}]'
}
```

**Features:**
- Cooperative information card with key details
- Line charts showing 24-month historical trends
- Current position indicators vs. regulatory thresholds
1- Asset growth visualization
- Navigation back to ranking

### 4. rakkun.html - VTuber Interactive Chat

**Purpose:** Interface for chatting with Rakkun VTuber about SEPS data

**Data Context:** None (static template)

**Features:**
- Chat interface with message history display
- Integration with Rakkun API endpoint (`/api/rakkun/preguntar`)
- Example questions/suggestions for users
- Live2D Rakkun avatar placeholder

## Implementation Plan

### Phase 1: Basic Functional Templates
1. Create `ranking.html` with sortable table
2. Create `segmentos.html` with basic charts
3. Create `cooperativa_detalle.html` with historical charts
4. Create `rakkun.html` with chat interface

### Phase 2: Enhancement Features
1. Add search/filter to ranking table
2. Enhance segment charts with interactivity
3. Add comparative analysis to cooperative detail
4. Integrate Live2D Rakkun avatar

## Technical Requirements

### Dependencies
- Django 4.x
- PostgreSQL with `seps_eeff` database
- Chart.js CDN
- Tailwind CSS CDN
- Inter font from Google Fonts

### API Integration
- Rakkun API endpoint: `http://157.230.62.218/api/rakkun/preguntar`
. - POST with `{"texto": "question"}` 
- Returns `{"respuesta": "answer"}`

## Success Criteria
1. All four templates render without errors
2. Data displays correctly from PostgreSQL
3. Charts visualize data appropriately
4. Navigation works between all pages
5. Rakkun chat interface connects to API
6. Design consistency maintained across all templates

## Notes
1. Follow existing `dashboard.html` patterns for consistency
2. Test with local PostgreSQL on port 5434
3. Deploy to VPS after local testing
4. Maintain university thesis documentation standards