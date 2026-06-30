# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

**IntelliCoop: Sistema Inteligente de Análisis y Riesgo Cooperativo** — tesis universitaria de Jonnathan Tigre (carrera Big Data).

Analysis of financial statements (EEFF Mensuales) of Ecuadorian savings cooperatives (Cooperativas de Ahorro y Crédito) supervised by SEPS, covering segments 1–3 from 2015 to present. The pipeline downloads raw data from the SEPS portal, consolidates it into DuckDB, and runs financial analysis notebooks.

**Ruta local:** `C:\Users\Jonna\OneDrive - St Paulinus Catholic Primary School\claude proyectos\IntelliCoop\`

## Commands

```bash
# Python launcher (always use `py`, not `python` or `python3`, on this Windows machine)
py explorar_db.py           # inspect DB structure, row counts, segments
py consolidar_base.py       # rebuild SEPS_EEFF.duckdb from raw files (~31M rows, ~5 min)
py descarga_bases_datos.py  # download new annual files from SEPS portal (requires Chrome)

# Install dependencies
py -m pip install duckdb pandas pyarrow selenium webdriver-manager scikit-learn statsmodels scipy matplotlib seaborn
```

## Data Architecture

### Raw files → DuckDB pipeline

```
Base de datos/
  2015–2018/          ← ZIP archives (Anteriores/) or CSV/TXT
  2019–2026/          ← tab-separated .txt or .csv, one file per year
  → consolidar_base.py reads all, normalizes columns, inserts into DuckDB
SEPS_EEFF.duckdb      ← single table: eeff_mensuales (~31M rows, ~300 MB)
```

### Main table: `eeff_mensuales`

| Column | Type | Notes |
|---|---|---|
| `fecha_corte` | DATE | month-end date |
| `segmento` | VARCHAR | `'SEGMENTO 1'`, `'SEGMENTO 2'`, `'SEGMENTO 3'`, `'SEGMENTO 1 MUTUALISTA'` |
| `ruc` | VARCHAR | tax ID of the cooperative |
| `razon_social` | VARCHAR | legal name (append `' EN LIQUIDACION'` when closing) |
| `cuenta` | VARCHAR | SFPS account code — stored at **all hierarchy levels** (2-digit parent AND 4/6-digit children) |
| `descripcion_cuenta` | VARCHAR | account label |
| `saldo_usd` | DOUBLE | balance in USD |
| `año` | VARCHAR | year string |

Indexes exist on `cuenta`, `fecha_corte`, `ruc`, `segmento`.

### Account hierarchy — critical for avoiding double-counting

The DB stores **both parent and child accounts**. Querying `cuenta LIKE '1425%'` returns the 4-digit aggregate (`1425`) AND all sub-levels (`142505`, `142510`…), which **doubles the total**. Always use **exact matches**:

```python
# CORRECT — exact 4-digit codes
WHERE cuenta IN ('1425','1426','1427','1428')

# WRONG — includes parent + children
WHERE cuenta LIKE '1425%'
```

Key 2-digit accounts (safe to use as totals):
- `1` Activo Total, `2` Pasivo Total, `3` Patrimonio
- `11` Fondos Disponibles, `13` Inversiones, `14` Cartera de Créditos
- `21` Obligaciones con el Público (Depósitos)
- `4` Gastos Totales, `41` Intereses Causados, `44` Provisiones (gasto), `45` Gastos de Operación
- `5` Ingresos Totales, `51` Intereses Ganados
- `1499` Provisiones cartera (stored as **negative** — use `.abs()`)

Cartera improductiva = No Devenga (1425–1448) + Vencida (1449–1466), 4-digit exact matches.

## Notebooks

| File | Purpose |
|---|---|
| `analisis_descriptivo.ipynb` | System-wide overview: all segments, top cooperatives, asset evolution |
| `daquilema_solvencia.ipynb` | Deep-dive single cooperative (Fernando Daquilema, RUC `0691706710001`) with Holt-Winters forecast |
| `solvencia_segmento1_completo.ipynb` | **Main analysis**: all Segment 1 cooperatives — CAMEL/PERLAS ratios, PCA, K-Means + Ward + DBSCAN clustering, CAMEL composite scoring, OLS regression, Kruskal-Wallis tests |

## Key Analytical Conventions

**Cross-sectional analysis**: always filter to `fecha_corte = '2025-12-31'` and exclude `razon_social NOT LIKE '%LIQUIDACI%'`.

**Scaling**: use `RobustScaler` (not `StandardScaler`) before clustering — financial data has outliers.

**CAMEL weights** (NCUA 2023 adapted): C=25%, A=25%, M=20%, E=15%, L=15%.

**Regulatory thresholds** (SEPS Segmento 1):
- Capitalización ≥ 9% | Morosidad ≤ 5% | Cobertura ≥ 100% | Liquidez ampliada ≥ 14%

**Resultado del ejercicio**: calculate as `ingresos (5) − gastos (4)`, not from a separate account, to avoid cumulative vs. period mismatches on non-December dates.

## Segment 1 Coverage

47 cooperatives + 4 mutualistas. Active cooperatives in Dec-2025: 44. Two are in liquidation by 2025 (CREA, Cámara de Comercio Ambato) and must be excluded from cross-sectional analysis.
