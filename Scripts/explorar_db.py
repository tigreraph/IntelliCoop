import duckdb

DB = r"C:\Users\kevin\OneDrive\Desktop\Base Cooperativas segmentos\SEPS_EEFF.duckdb"
con = duckdb.connect(DB, read_only=True)

print("\n" + "="*55)
print("  EXPLORACIÓN — SEPS_EEFF.duckdb")
print("="*55)

print("\n--- TOTAL DE REGISTROS ---")
total = con.execute("SELECT COUNT(*) FROM eeff_mensuales").fetchone()[0]
print(f"  {total:,} filas")

print("\n--- POR AÑO ---")
df = con.execute("""
    SELECT
        año,
        COUNT(DISTINCT fecha_corte) AS meses,
        COUNT(DISTINCT ruc)         AS cooperativas,
        COUNT(*)                    AS registros
    FROM eeff_mensuales
    GROUP BY año
    ORDER BY año
""").df()
print(df.to_string(index=False))

print("\n--- SEGMENTOS DISPONIBLES ---")
df2 = con.execute("""
    SELECT segmento, COUNT(DISTINCT ruc) AS cooperativas
    FROM eeff_mensuales
    GROUP BY segmento
    ORDER BY segmento
""").df()
print(df2.to_string(index=False))

print("\n--- FECHAS MÍNIMA Y MÁXIMA ---")
df3 = con.execute("""
    SELECT
        MIN(fecha_corte) AS desde,
        MAX(fecha_corte) AS hasta
    FROM eeff_mensuales
""").df()
print(df3.to_string(index=False))

print("\n--- COLUMNAS DE LA TABLA ---")
df4 = con.execute("DESCRIBE eeff_mensuales").df()
print(df4[["column_name", "column_type"]].to_string(index=False))

print("\n--- MUESTRA DE 5 FILAS ---")
df5 = con.execute("SELECT * FROM eeff_mensuales LIMIT 5").df()
print(df5.to_string(index=False))

print("\n--- CUENTAS MÁS FRECUENTES (top 10) ---")
df6 = con.execute("""
    SELECT cuenta, descripcion_cuenta, COUNT(*) AS veces
    FROM eeff_mensuales
    GROUP BY cuenta, descripcion_cuenta
    ORDER BY veces DESC
    LIMIT 10
""").df()
print(df6.to_string(index=False))

con.close()
print("\n" + "="*55)
print("  Base de datos verificada correctamente.")
print("="*55 + "\n")
