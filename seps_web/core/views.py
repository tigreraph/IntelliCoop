import os
import json
import urllib.request
import urllib.error
import psycopg2
import psycopg2.extras
from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt

# Conexion — local: port 5434 / postgres | VPS: port 5432 / seps_user
DB = {
    "host":     os.environ.get("DB_HOST", "localhost"),
    "port":     int(os.environ.get("DB_PORT", 5434)),
    "dbname":   "seps_eeff",
    "user":     os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASS", "seps2024"),
}

ULTIMO_CORTE = "(SELECT MAX(fecha_corte) FROM fact_indicadores)"
SOLO_ACTIVAS = "dc.estado = 'ACTIVA'"


def get_db():
    return psycopg2.connect(**DB)


def _to_py(rows):
    result = []
    for row in rows:
        d = {}
        for k, v in row.items():
            d[k] = float(v) if hasattr(v, '__float__') and not isinstance(v, int) else (str(v) if hasattr(v, 'isoformat') else v)
        result.append(d)
    return result


def dashboard(request):
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute(f"""
            SELECT COUNT(DISTINCT dc.ruc)                         AS total_coops,
                   ROUND(AVG(fi.camel_score)::numeric, 2)         AS camel_promedio,
                   ROUND(AVG(fi.morosidad_pct)::numeric, 2)       AS morosidad_promedio,
                   ROUND(AVG(fi.liquidez_ampliada)::numeric, 2)   AS liquidez_promedio,
                   ROUND(SUM(fi.activo_total)::numeric/1e9, 2)    AS activos_sistema_b,
                   MAX(fi.fecha_corte)                            AS ultimo_corte
            FROM fact_indicadores fi
            JOIN dim_cooperativa dc ON fi.ruc = dc.ruc
            WHERE {SOLO_ACTIVAS} AND fi.fecha_corte = {ULTIMO_CORTE}
        """)
        row = cur.fetchone()
        if row is None:
            return render(request, 'dashboard.html', {'sin_datos': True})
        kpis = dict(row)
        kpis['ultimo_corte'] = str(kpis['ultimo_corte'])
        for k in ('camel_promedio', 'morosidad_promedio', 'liquidez_promedio', 'activos_sistema_b'):
            kpis[k] = float(kpis[k])

        cur.execute(f"""
            SELECT dc.segmento, COUNT(*) AS cantidad,
                   ROUND(AVG(fi.camel_score)::numeric, 2) AS camel_promedio
            FROM fact_indicadores fi
            JOIN dim_cooperativa dc ON fi.ruc = dc.ruc
            WHERE {SOLO_ACTIVAS} AND fi.fecha_corte = {ULTIMO_CORTE}
            GROUP BY dc.segmento ORDER BY dc.segmento
        """)
        por_segmento = _to_py(cur.fetchall())

        cur.execute(f"""
            SELECT fi.ruc, dc.razon_social, dc.segmento,
                   ROUND(fi.camel_score::numeric, 3) AS camel_score,
                   fi.rating_camel, fi.morosidad_pct, fi.capitalizacion_pct
            FROM fact_indicadores fi
            JOIN dim_cooperativa dc ON fi.ruc = dc.ruc
            WHERE {SOLO_ACTIVAS} AND fi.fecha_corte = {ULTIMO_CORTE}
            ORDER BY fi.camel_score DESC LIMIT 5
        """)
        top5 = _to_py(cur.fetchall())

        cur.execute(f"""
            SELECT fi.ruc, dc.razon_social, dc.segmento,
                   ROUND(fi.camel_score::numeric, 3) AS camel_score,
                   fi.rating_camel, fi.morosidad_pct, fi.capitalizacion_pct
            FROM fact_indicadores fi
            JOIN dim_cooperativa dc ON fi.ruc = dc.ruc
            WHERE {SOLO_ACTIVAS} AND fi.fecha_corte = {ULTIMO_CORTE}
            ORDER BY fi.camel_score ASC LIMIT 5
        """)
        bottom5 = _to_py(cur.fetchall())
    finally:
        conn.close()

    return render(request, 'dashboard.html', {
        'kpis':         kpis,
        'por_segmento': json.dumps(por_segmento),
        'top5':         top5,
        'bottom5':      bottom5,
    })


def ranking(request):
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(f"""
            SELECT dc.razon_social, dc.segmento, dc.estado,
                   ROUND(fi.camel_score::numeric, 3)        AS camel_score,
                   fi.rating_camel,
                   ROUND(fi.morosidad_pct::numeric, 2)      AS morosidad_pct,
                   ROUND(fi.capitalizacion_pct::numeric, 2) AS capitalizacion_pct,
                   ROUND(fi.liquidez_ampliada::numeric, 2)  AS liquidez_ampliada,
                   ROUND(fi.roa_pct::numeric, 2)            AS roa_pct,
                   dc.ruc
            FROM fact_indicadores fi
            JOIN dim_cooperativa dc ON fi.ruc = dc.ruc
            WHERE {SOLO_ACTIVAS} AND fi.fecha_corte = {ULTIMO_CORTE}
            ORDER BY fi.camel_score DESC
        """)
        cooperativas = _to_py(cur.fetchall())
    finally:
        conn.close()
    return render(request, 'ranking.html', {'cooperativas': cooperativas})


def segmentos(request):
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(f"""
            SELECT dc.segmento,
                   COUNT(*)                                          AS total,
                   ROUND(AVG(fi.camel_score)::numeric, 2)           AS camel_promedio,
                   ROUND(AVG(fi.morosidad_pct)::numeric, 2)         AS morosidad_promedio,
                   ROUND(AVG(fi.capitalizacion_pct)::numeric, 2)    AS capital_promedio,
                   ROUND(AVG(fi.liquidez_ampliada)::numeric, 2)     AS liquidez_promedio,
                   ROUND(AVG(fi.roa_pct)::numeric, 2)               AS roa_promedio,
                   ROUND(SUM(fi.activo_total)::numeric/1e9, 2)      AS activos_miles_millones
            FROM fact_indicadores fi
            JOIN dim_cooperativa dc ON fi.ruc = dc.ruc
            WHERE {SOLO_ACTIVAS} AND fi.fecha_corte = {ULTIMO_CORTE}
            GROUP BY dc.segmento ORDER BY dc.segmento
        """)
        segmentos_data = _to_py(cur.fetchall())
    finally:
        conn.close()
    return render(request, 'segmentos.html', {
        'segmentos':      segmentos_data,
        'segmentos_json': json.dumps(segmentos_data),
    })


def cooperativa_detalle(request, ruc):
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("SELECT * FROM dim_cooperativa WHERE ruc = %s", (ruc,))
        row = cur.fetchone()
        if row is None:
            raise Http404(f"Cooperativa con RUC {ruc} no encontrada")
        coop = dict(row)
        for k, v in coop.items():
            if hasattr(v, 'isoformat'):
                coop[k] = str(v)

        cur.execute(f"""
            SELECT fecha_corte,
                   ROUND(camel_score::numeric, 3)        AS camel_score,
                   rating_camel,
                   ROUND(morosidad_pct::numeric, 2)      AS morosidad_pct,
                   ROUND(capitalizacion_pct::numeric, 2) AS capitalizacion_pct,
                   ROUND(liquidez_ampliada::numeric, 2)  AS liquidez_ampliada,
                   ROUND(roa_pct::numeric, 2)            AS roa_pct,
                   ROUND(eficiencia_op_pct::numeric, 2)  AS eficiencia_op_pct,
                   ROUND(activo_total::numeric/1e6, 2)   AS activo_millones
            FROM fact_indicadores
            WHERE ruc = %s ORDER BY fecha_corte DESC LIMIT 24
        """, (ruc,))
        historico = _to_py(cur.fetchall())
    finally:
        conn.close()

    return render(request, 'cooperativa_detalle.html', {
        'coop':          coop,
        'historico':     historico,
        'historico_json': json.dumps(historico),
    })


def rakkun(request):
    return render(request, 'rakkun.html', {})


def rakkun_avatar(request):
    return render(request, 'rakkun_avatar.html', {})


def prediccion(request):
    context = {
        'placeholder_kpis': [
            {'label': 'Precisión del modelo'},
            {'label': 'Cooperativas analizadas'},
            {'label': 'Horizonte de predicción'},
            {'label': 'Última ejecución'},
        ],
        'bar_heights': [30, 45, 38, 60, 52, 70, 48, 65, 55, 72, 50, 68],
        'meses_short': ['Jun','Jul','Ago','Sep','Oct','Nov','Dic','Ene','Feb','Mar','Abr','May'],
        'features': [
            {'nombre': 'Índice de Morosidad'},
            {'nombre': 'Cobertura de Cartera'},
            {'nombre': 'Liquidez Ampliada'},
            {'nombre': 'Capitalización'},
            {'nombre': 'ROA / Rentabilidad'},
        ],
    }
    return render(request, 'prediccion.html', context)


@csrf_exempt
def rakkun_chat(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST requerido'}, status=405)
    try:
        body = json.loads(request.body)
        # Acepta tanto 'pregunta' (frontend) como 'texto' (legacy)
        pregunta = (body.get('pregunta') or body.get('texto', '')).strip()
        if not pregunta:
            return JsonResponse({'error': 'pregunta vacía'}, status=400)

        rakkun_url = os.environ.get(
            'RAKKUN_API_URL',
            'http://localhost:8001/preguntar'
        )
        payload = json.dumps({'texto': pregunta}).encode('utf-8')
        req = urllib.request.Request(
            rakkun_url,
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read())
        return JsonResponse(data)
    except urllib.error.HTTPError as e:
        return JsonResponse({'error': f'Rakkun API error {e.code}'}, status=502)
    except urllib.error.URLError as e:
        return JsonResponse({'error': f'No se pudo conectar con Rakkun: {e.reason}'}, status=503)
    except Exception as e:
        return JsonResponse({'error': f'Error inesperado: {e}'}, status=500)


@csrf_exempt
def tts(request):
    """Proxy Google Cloud TTS → devuelve audio MP3 en base64."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    try:
        body  = json.loads(request.body)
        texto = body.get('texto', '').strip()
        if not texto:
            return JsonResponse({'error': 'Texto vacío'}, status=400)

        api_key = os.environ.get('GOOGLE_TTS_KEY', '')
        if not api_key:
            return JsonResponse({'error': 'GOOGLE_TTS_KEY no configurada'}, status=500)

        payload = json.dumps({
            'input': {'text': texto},
            'voice': {
                'languageCode': 'es-US',
                'name': 'es-US-Neural2-A',   # voz femenina Neural de Google
                'ssmlGender': 'FEMALE'
            },
            'audioConfig': {
                'audioEncoding': 'MP3',
                'speakingRate': 1.05,
                'pitch': 1.5
            }
        }).encode('utf-8')

        url = f'https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}'
        req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')

        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())

        return JsonResponse({'audioContent': result.get('audioContent', '')})

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='ignore')
        return JsonResponse({'error': f'Google TTS error {e.code}: {error_body}'}, status=502)
    except Exception as e:
        return JsonResponse({'error': f'Error TTS: {e}'}, status=500)
