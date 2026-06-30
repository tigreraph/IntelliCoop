import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import duckdb, pandas as pd

con = duckdb.connect('SEPS_EEFF.duckdb', read_only=True)

# Cuentas principales disponibles en Segmento 1 (año 2025)
cuentas = con.execute("""
    SELECT cuenta, descripcion_cuenta,
           COUNT(DISTINCT ruc) AS coops, COUNT(*) AS registros
    FROM eeff_mensuales
    WHERE segmento = 'SEGMENTO 1'
      AND LENGTH(cuenta) <= 4
      AND año = '2025'
    GROUP BY cuenta, descripcion_cuenta
    ORDER BY LENGTH(cuenta), cuenta
    LIMIT 100
""").df()
print('=== CUENTAS DISPONIBLES SEGMENTO 1 (2025) ===')
print(cuentas.to_string(index=False))

# Lista de cooperativas Segmento 1
coops = con.execute("""
    SELECT ruc, razon_social,
           COUNT(DISTINCT fecha_corte) AS meses,
           MIN(fecha_corte) AS desde,
           MAX(fecha_corte) AS hasta
    FROM eeff_mensuales
    WHERE segmento = 'SEGMENTO 1'
    GROUP BY ruc, razon_social
    ORDER BY razon_social
""").df()
print(f'\n=== COOPERATIVAS SEGMENTO 1 ({len(coops)} total) ===')
print(coops.to_string(index=False))

# Verificar cuentas de cartera improductiva
cart = con.execute("""
    SELECT cuenta, descripcion_cuenta,
           COUNT(DISTINCT ruc) AS coops
    FROM eeff_mensuales
    WHERE segmento = 'SEGMENTO 1'
      AND (cuenta LIKE '1425%' OR cuenta LIKE '1426%')
      AND año = '2025'
    GROUP BY cuenta, descripcion_cuenta
    ORDER BY cuenta
""").df()
print('\n=== CARTERA IMPRODUCTIVA (1425x / 1426x) ===')
print(cart.to_string(index=False))

con.close()
