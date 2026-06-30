"""
Genera directorio_cooperativas.csv con datos financieros e indicadores CAMEL
al último corte disponible (abril 2026).

Uso:
    py generar_directorio.py
"""

import duckdb
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Jonna\OneDrive - St Paulinus Catholic Primary School\claude proyectos\IntelliCoop")
DB_PATH  = BASE_DIR / "SEPS_EEFF.duckdb"
OUT_PATH = BASE_DIR / "directorio_cooperativas.csv"

C_NODEV = "'1425','1426','1427','1428','1432','1433','1434','1435','1436','1440','1441','1442','1443','1444','1448'"
C_VENC  = "'1449','1450','1451','1452','1456','1457','1458','1459'"

con = duckdb.connect(str(DB_PATH), read_only=True)

ultima = con.execute("SELECT MAX(fecha_corte) FROM eeff_mensuales").fetchone()[0]
print(f"Último corte: {ultima}")

# ── Directorio base ───────────────────────────────────────────────
directorio = con.execute("""
    SELECT
        ruc,
        LAST(razon_social ORDER BY fecha_corte) AS razon_social,
        LAST(segmento     ORDER BY fecha_corte) AS segmento,
        MIN(fecha_corte)  AS primera_fecha,
        MAX(fecha_corte)  AS ultima_fecha,
        COUNT(DISTINCT fecha_corte) AS meses_activo,
        CASE WHEN LAST(razon_social ORDER BY fecha_corte) LIKE '%LIQUIDACI%'
             THEN 'EN LIQUIDACION' ELSE 'ACTIVA' END AS estado
    FROM eeff_mensuales
    GROUP BY ruc
    ORDER BY segmento, razon_social
""").df()

# ── Datos financieros último corte ───────────────────────────────
fin = con.execute(f"""
    SELECT
        ruc,
        MAX(CASE WHEN cuenta='1'    THEN saldo_usd END) AS activo_total,
        MAX(CASE WHEN cuenta='2'    THEN saldo_usd END) AS pasivo_total,
        MAX(CASE WHEN cuenta='3'    THEN saldo_usd END) AS patrimonio,
        MAX(CASE WHEN cuenta='11'   THEN saldo_usd END) AS fondos_disp,
        MAX(CASE WHEN cuenta='13'   THEN saldo_usd END) AS inversiones,
        MAX(CASE WHEN cuenta='14'   THEN saldo_usd END) AS cartera_bruta,
        MAX(CASE WHEN cuenta='1499' THEN saldo_usd END) AS provisiones,
        MAX(CASE WHEN cuenta='21'   THEN saldo_usd END) AS depositos,
        MAX(CASE WHEN cuenta='4'    THEN saldo_usd END) AS gastos_total,
        MAX(CASE WHEN cuenta='5'    THEN saldo_usd END) AS ingresos_total,
        MAX(CASE WHEN cuenta='41'   THEN saldo_usd END) AS int_causados,
        MAX(CASE WHEN cuenta='45'   THEN saldo_usd END) AS gastos_op,
        MAX(CASE WHEN cuenta='51'   THEN saldo_usd END) AS int_ganados,
        SUM(CASE WHEN cuenta IN ({C_NODEV}) THEN saldo_usd ELSE 0 END) AS cart_nodev,
        SUM(CASE WHEN cuenta IN ({C_VENC})  THEN saldo_usd ELSE 0 END) AS cart_vencida
    FROM eeff_mensuales
    WHERE fecha_corte = '{ultima}'
    GROUP BY ruc
""").df()
con.close()

# ── Calcular indicadores ──────────────────────────────────────────
fin['resultado']         = fin['ingresos_total'].fillna(0) - fin['gastos_total'].fillna(0)
fin['cart_improductiva'] = fin['cart_nodev'].fillna(0) + fin['cart_vencida'].fillna(0)
fin['margen_fin']        = fin['int_ganados'].fillna(0) - fin['int_causados'].fillna(0)

def safe(num, den, scale=100):
    return np.where(den > 0, num / den * scale, np.nan)

fin['capitalizacion']    = safe(fin['patrimonio'], fin['activo_total'])
fin['morosidad']         = safe(fin['cart_improductiva'], fin['cartera_bruta'])
fin['cobertura']         = safe(fin['provisiones'].abs(), fin['cart_improductiva'])
fin['roa']               = safe(fin['resultado'], fin['activo_total'])
fin['roe']               = safe(fin['resultado'], fin['patrimonio'])
fin['liquidez_ampliada'] = safe(fin['fondos_disp'].fillna(0) + fin['inversiones'].fillna(0), fin['depositos'])
fin['eficiencia_op']     = safe(fin['gastos_op'].fillna(0), fin['activo_total'])
fin['apalancamiento']    = safe(fin['pasivo_total'], fin['patrimonio'], scale=1)
fin['intermediacion']    = safe(fin['cartera_bruta'], fin['depositos'])
fin['nim']               = safe(fin['margen_fin'], fin['activo_total'])

# ── Score CAMEL ───────────────────────────────────────────────────
def score_camel(row):
    def sc_cap(v):
        if pd.isna(v): return 3.0
        return 1 if v >= 15 else 2 if v >= 12 else 3 if v >= 9 else 4 if v >= 6 else 5
    def sc_mor(v):
        if pd.isna(v): return 3.0
        return 1 if v < 2 else 2 if v < 4 else 3 if v < 6 else 4 if v < 10 else 5
    def sc_cob(v):
        if pd.isna(v): return 3.0
        return 1 if v > 200 else 2 if v > 150 else 3 if v > 100 else 4 if v > 75 else 5
    def sc_efic(v):
        if pd.isna(v): return 3.0
        return 1 if v < 3 else 2 if v < 4 else 3 if v < 5.5 else 4 if v < 7 else 5
    def sc_roa(v):
        if pd.isna(v): return 3.0
        return 1 if v > 1.5 else 2 if v > 0.75 else 3 if v > 0 else 4 if v > -0.5 else 5
    def sc_liq(v):
        if pd.isna(v): return 3.0
        return 1 if v > 25 else 2 if v > 20 else 3 if v > 14 else 4 if v > 10 else 5

    c = sc_cap(row['capitalizacion'])
    a = (sc_mor(row['morosidad']) + sc_cob(row['cobertura'])) / 2
    m = sc_efic(row['eficiencia_op'])
    e = sc_roa(row['roa'])
    l = sc_liq(row['liquidez_ampliada'])
    camel = 0.25*c + 0.25*a + 0.20*m + 0.15*e + 0.15*l
    return pd.Series({'sc_C': c, 'sc_A': round(a,2), 'sc_M': m,
                      'sc_E': e, 'sc_L': l, 'camel': round(camel, 3)})

scores = fin.apply(score_camel, axis=1)
fin = pd.concat([fin, scores], axis=1)

def rating(v):
    if pd.isna(v): return 'SIN DATOS'
    if v <= 1.5:   return 'EXCELENTE'
    if v <= 2.5:   return 'BUENO'
    if v <= 3.5:   return 'ADECUADO'
    if v <= 4.5:   return 'MARGINAL'
    return 'CRITICO'

fin['rating_camel'] = fin['camel'].apply(rating)

# ── Merge con directorio ──────────────────────────────────────────
cols_fin = ['ruc', 'activo_total', 'patrimonio', 'cartera_bruta', 'depositos',
            'capitalizacion', 'morosidad', 'cobertura', 'roa', 'roe', 'nim',
            'liquidez_ampliada', 'eficiencia_op', 'apalancamiento', 'intermediacion',
            'sc_C', 'sc_A', 'sc_M', 'sc_E', 'sc_L', 'camel', 'rating_camel']

df_final = directorio.merge(fin[cols_fin], on='ruc', how='left')

# Convertir saldos a millones y redondear
for col in ['activo_total', 'patrimonio', 'cartera_bruta', 'depositos']:
    df_final[col] = (df_final[col] / 1e6).round(2)

for col in ['capitalizacion', 'morosidad', 'cobertura', 'roa', 'roe',
            'nim', 'liquidez_ampliada', 'eficiencia_op', 'intermediacion']:
    df_final[col] = df_final[col].round(2)

df_final['apalancamiento'] = df_final['apalancamiento'].round(2)

df_final = df_final.rename(columns={
    'activo_total':    f'activo_M_{ultima.strftime("%b%Y")}',
    'patrimonio':      f'patrimonio_M_{ultima.strftime("%b%Y")}',
    'cartera_bruta':   f'cartera_M_{ultima.strftime("%b%Y")}',
    'depositos':       f'depositos_M_{ultima.strftime("%b%Y")}',
    'capitalizacion':  'capitalizacion_pct',
    'morosidad':       'morosidad_pct',
    'cobertura':       'cobertura_pct',
    'roa':             'roa_pct',
    'roe':             'roe_pct',
    'nim':             'nim_pct',
    'liquidez_ampliada': 'liquidez_ampliada_pct',
    'eficiencia_op':   'eficiencia_op_pct',
})

df_final.to_csv(str(OUT_PATH), index=False, encoding='utf-8-sig')

# ── Reporte ───────────────────────────────────────────────────────
print(f"\nGuardado: {OUT_PATH}")
print(f"Entidades: {len(df_final)}  |  Columnas: {len(df_final.columns)}")
print(f"\nColumnas:\n  " + "\n  ".join(df_final.columns.tolist()))

print("\n=== DISTRIBUCION RATING CAMEL POR SEGMENTO ===")
activas = df_final[df_final['estado'] == 'ACTIVA']
tabla = activas.groupby(['segmento', 'rating_camel']).size().unstack(fill_value=0)
print(tabla.to_string())

print(f"\n=== TOP 10 POR ACTIVO TOTAL ===")
col_activo = [c for c in df_final.columns if c.startswith('activo_M')][0]
top10 = df_final.nlargest(10, col_activo)[['razon_social', 'segmento', col_activo, 'camel', 'rating_camel']]
print(top10.to_string(index=False))
