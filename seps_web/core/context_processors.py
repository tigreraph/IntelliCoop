import os
import time
import psycopg2
import psycopg2.extras

MESES_ES = {
    1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun',
    7:'Jul', 8:'Ago', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dic'
}

DB = {
    "host":     os.environ.get("DB_HOST", "localhost"),
    "port":     int(os.environ.get("DB_PORT", 5434)),
    "dbname":   "seps_eeff",
    "user":     os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASS", "seps2024"),
}

# Cache de 10 minutos — evita golpear la DB en cada request
_cache = {'data': None, 'ts': 0}
CACHE_TTL = 600

def sidebar_stats(request):
    """
    Inyecta en todos los templates:
      {{ sidebar_coops }}     → "226"
      {{ sidebar_corte }}     → "May 2025"
      {{ sidebar_activos }}   → "~38B USD"
    """
    now = time.time()
    if _cache['data'] and (now - _cache['ts']) < CACHE_TTL:
        return _cache['data']

    try:
        conn = psycopg2.connect(**DB)
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT
                COUNT(DISTINCT dc.ruc)                         AS coops_activas,
                MAX(fi.fecha_corte)                            AS ultimo_corte,
                ROUND(SUM(fi.activo_total)::numeric / 1e9, 1) AS activos_b
            FROM fact_indicadores fi
            JOIN dim_cooperativa dc ON fi.ruc = dc.ruc
            WHERE dc.estado = 'ACTIVA'
              AND fi.fecha_corte = (SELECT MAX(fecha_corte) FROM fact_indicadores)
        """)
        row = cur.fetchone()
        cur.close()
        conn.close()

        fecha = row['ultimo_corte']
        corte_str = f"{MESES_ES[fecha.month]} {fecha.year}" if fecha else '—'

        activos = float(row['activos_b'] or 0)
        activos_str = f"~{int(activos)}B USD" if activos >= 1 else f"~{round(activos*1000)}M USD"

        data = {
            'sidebar_coops':   str(row['coops_activas'] or 0),
            'sidebar_corte':   corte_str,
            'sidebar_activos': activos_str,
        }
    except Exception:
        data = {
            'sidebar_coops':   '—',
            'sidebar_corte':   '—',
            'sidebar_activos': '—',
        }

    _cache['data'] = data
    _cache['ts']   = now
    return data
