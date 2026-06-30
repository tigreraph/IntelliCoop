"""
IntelliCoop — Rakkun API (local)
FastAPI + DeepSeek V3.2 via OpenRouter · Text-to-SQL en dos turnos
Arrancar: uvicorn rakkun_api:app --port 8001 --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
import httpx
import os
from dotenv import load_dotenv
load_dotenv()
import json
import re

app = FastAPI(title="Rakkun API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Configuración ────────────────────────────────────────────
DB = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5434)),       # local=5434 / VPS=5432
    "dbname":   "seps_eeff",
    "user":     os.getenv("DB_USER", "postgres"),       # local=postgres / VPS=seps_user
    "password": os.getenv("DB_PASS", "seps2024"),
}

# API key requerida — sin fallback hardcodeado
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "")
MODEL = "deepseek/deepseek-v3.2"

# ── Schema real de la BD ─────────────────────────────────────
SCHEMA = """
Tablas reales en PostgreSQL (seps_eeff):

dim_cooperativa: ruc (PK), razon_social, segmento, estado,
  primera_fecha, ultima_fecha, meses_activo
  Valores de estado: 'ACTIVA' | 'EN LIQUIDACION'
  Valores de segmento: 'SEGMENTO 1' | 'SEGMENTO 2' | 'SEGMENTO 3' | 'SEGMENTO 1 MUTUALISTA' (siempre llevan la palabra 'SEGMENTO ' antes del numero)
  PROHIBIDO: canton, provincia, fecha_corte (columnas que NO existen en esta tabla)

dim_cuenta: cuenta, descripcion_cuenta, nivel

fact_indicadores: fecha_corte, ruc (FK), activo_total, patrimonio,
  cartera_bruta, depositos, capitalizacion_pct, morosidad_pct,
  cobertura_pct, roa_pct, roe_pct, nim_pct, liquidez_ampliada,
  eficiencia_op_pct, n,
  camel_score (0-100), rating_camel

Reglas SQL OBLIGATORIAS:
- JOIN: fact_indicadores fi JOIN dim_cooperativa dc ON fi.ruc = dc.ruc
- Solo activas: dc.estado = 'ACTIVA'
- Ultimo corte: fi.fecha_corte = (SELECT MAX(fecha_corte) FROM fact_indicadores)
- Filtro de fecha_corte: La columna fecha_corte SOLO existe en fact_indicadores. NUNCA intentes usar dc.fecha_corte o dim_cooperativa.fecha_corte. Si la pregunta requiere filtrar o agrupar por fecha_corte, DEBES hacer JOIN con fact_indicadores.
- Filtro de segmento: El segmento de la cooperativa tiene la palabra 'SEGMENTO ' antes (ej. dc.segmento = 'SEGMENTO 1', nunca dc.segmento = '1').
- LIMIT siempre debe ser un numero entero entre 1 y 100: LIMIT 50 (nunca texto, nunca simbolos, nunca mas de 100)
- Usar solo caracteres ASCII en el SQL, nunca caracteres especiales ni de otros idiomas
"""

SYSTEM_PASO1 = """Eres Rakkun, asistente financiero del sistema cooperativo de Ecuador (SEPS).
Eres amigable, claro y experto en finanzas.

REGLA CRITICA — SIGUE ESTO EXACTAMENTE:
1. Si la pregunta necesita datos de cooperativas (morosidad, CAMEL, ranking, indicadores,
   capitalizacion, liquidez, activos, segmentos, nombres de cooperativas), escribe SOLO esto:
   SQL:
   <consulta SELECT para PostgreSQL>

   PROHIBIDO escribir cualquier texto antes o despues del SQL. Ni una sola palabra.
   La primera linea de tu respuesta DEBE ser exactamente "SQL:" si necesitas consultar datos.

2. Si la pregunta es general (economia, conceptos financieros, saludos, conversacion),
   responde naturalmente. NO uses SQL para preguntas generales.

REGLA DE BUSQUEDA POR NOMBRE:
- Cuando busques una cooperativa por nombre o siglas, usa busqueda flexible:
  dc.razon_social ILIKE '%palabra1%' OR dc.razon_social ILIKE '%palabra2%'
- Ejemplos de siglas conocidas:
  JEP = JUVENTUD ECUATORIANA PROGRESISTA
  COAC = Cooperativa de Ahorro y Credito
  CACPE = Cooperativa de Ahorro y Credito del Magisterio
- Si el usuario escribe siglas, busca tanto por siglas como por nombre completo probable

Responde siempre en espanol."""

SYSTEM_PASO2 = """Eres Rakkun, un asistente financiero amigable y cercano del sistema cooperativo SEPS Ecuador.
Hablas como un analista financiero que explica las cosas de forma sencilla a alguien de confianza.

REGLAS:
- Responde como si le estuvieras explicando a un amigo, con naturalidad y calidez
- Máximo 3-4 oraciones, sin rodeos
- NO uses ##, ---, ni símbolos de markdown pesado
- Si hay un dato preocupante (morosidad>5%, liquidez<14%, capital<9%), menciónalo con tacto
- Si los datos son buenos, puedes destacarlo positivamente
- Puedes usar **negrita** solo para resaltar el nombre de la cooperativa o un dato clave
- Si hay varios resultados, usa una tabla markdown simple
- Termina con una pregunta corta o invitación a seguir explorando (opcional)"""


# ── SQL helper ───────────────────────────────────────────────

def limpiar_sql(sql: str) -> str:
    """
    Limpia el SQL generado por el LLM:
    - Reemplaza LIMIT 0, LIMIT ALL, LIMIT con no-dígito, y LIMIT con entero >100
    """
    # LIMIT ALL o LIMIT con primer carácter no numérico
    sql = re.sub(
        r'LIMIT\s*(?:ALL|[^\d\s;][^\s;]*)',
        'LIMIT 50',
        sql,
        flags=re.IGNORECASE
    )
    # LIMIT 0
    sql = re.sub(r'LIMIT\s*0\b', 'LIMIT 50', sql, flags=re.IGNORECASE)
    # LIMIT con entero > 100
    def cap_limit(m):
        val = int(m.group(1))
        return f'LIMIT {min(val, 100)}'
    sql = re.sub(r'LIMIT\s*(\d+)', cap_limit, sql, flags=re.IGNORECASE)
    return sql.strip()


def ejecutar_sql(sql: str) -> list:
    sql = limpiar_sql(sql)
    if not sql.upper().startswith("SELECT"):
        return [{"error": "Solo se permiten consultas SELECT"}]
    conn = psycopg2.connect(**DB)
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql)
        rows = cur.fetchall()
    finally:
        conn.close()
    # Forzar claves a str — psycopg2 puede devolver tipos no serializables como clave
    return [{str(k): v for k, v in r.items()} for r in rows]


def _safe_content(resp_json: dict, turn: int) -> str:
    """Extrae el texto de la respuesta de OpenRouter; lanza ValueError si el modelo devolvió error."""
    if "error" in resp_json:
        msg = resp_json["error"].get("message", "error desconocido")
        raise ValueError(f"OpenRouter turno {turn}: {msg}")
    try:
        return resp_json["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise ValueError(f"Respuesta inesperada de OpenRouter turno {turn}: {e}")


# ── Modelos ──────────────────────────────────────────────────
class Pregunta(BaseModel):
    texto: str


# ── Endpoints ────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "servicio": "Rakkun API — IntelliCoop", "model": MODEL}


@app.post("/preguntar")
async def preguntar(p: Pregunta):
    if not OPENROUTER_KEY:
        return {"respuesta": "[OPENROUTER_KEY no configurada en el servidor]", "sql_generado": None, "tabla": None}

    async with httpx.AsyncClient(timeout=60) as client:

        # Turno 1: clasificar + generar SQL si hace falta
        r1 = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PASO1 + "\n\nESQUEMA:\n" + SCHEMA},
                    {"role": "user",   "content": p.texto}
                ]
            }
        )
        try:
            resp1 = _safe_content(r1.json(), turn=1).strip()
        except ValueError as e:
            return {"respuesta": str(e), "sql_generado": None, "tabla": None}

        # Extraer SQL — funciona aunque el modelo ponga texto antes
        sql = None
        if "SQL:" in resp1.upper():
            idx = resp1.upper().index("SQL:")
            sql = resp1[idx + 4:].strip()
            # Quedarse solo con el bloque SELECT (cortar si hay texto después)
            lineas = sql.splitlines()
            sql_lineas = []
            for linea in lineas:
                if sql_lineas and linea.strip() and not any(
                    linea.strip().upper().startswith(kw)
                    for kw in ("SELECT","FROM","JOIN","WHERE","AND","OR","ORDER","GROUP",
                               "LIMIT","HAVING","LEFT","RIGHT","INNER","WITH","ON","UNION")
                ):
                    break
                sql_lineas.append(linea)
            sql = "\n".join(sql_lineas).strip()

        # Pregunta general — sin SQL
        if not sql:
            return {"respuesta": resp1, "sql_generado": None, "tabla": None}

        # Ejecutar SQL
        try:
            resultado = ejecutar_sql(sql)
        except Exception as e:
            resultado = [{"error": str(e), "sql": sql}]

        if resultado and "error" in resultado[0]:
            return {
                "respuesta":    "No pude consultar la base de datos. Intenta reformular la pregunta.",
                "sql_generado": sql,
                "tabla":        None,
            }

        # Turno 2: formatear respuesta en lenguaje natural
        r2 = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PASO2},
                    {
                        "role": "user",
                        "content": (
                            f"Pregunta: {p.texto}\n\n"
                            f"Datos de la BD:\n"
                            f"{json.dumps(resultado, default=str, ensure_ascii=False, indent=2)}"
                        )
                    }
                ]
            }
        )
        try:
            respuesta_final = _safe_content(r2.json(), turn=2)
        except ValueError as e:
            return {"respuesta": str(e), "sql_generado": sql, "tabla": resultado}

        return {
            "respuesta":    respuesta_final,
            "sql_generado": sql,
            "tabla":        resultado,
        }
