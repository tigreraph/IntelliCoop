"""
Migración DuckDB → PostgreSQL
Crea la BD seps_eeff con schema normalizado y migra los 31M de filas.

Uso:
    py migrar_postgres.py
    py migrar_postgres.py --password miClave123
    py migrar_postgres.py --solo-schema      (solo crea tablas, sin migrar datos)
    py migrar_postgres.py --solo-indicadores (solo recalcula fact_indicadores)

Requisitos:
    py -m pip install psycopg2-binary duckdb pandas
"""

import sys
import logging
import argparse
import getpass
from pathlib import Path

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
import duckdb
import pandas as pd
import numpy as np

# ── Configuración ─────────────────────────────────────────────────
PG_HOST   = "localhost"
PG_PORT   = 5434          # PostgreSQL 18 (14→5432, 17→5433, 18→5434)
PG_USER   = "postgres"
PG_DB     = "seps_eeff"
PG_PASS   = "seps2024"    # contraseña establecida en pgAdmin

DUCK_PATH = Path(r"C:\Users\Jonna\OneDrive - St Paulinus Catholic Primary School\claude proyectos\IntelliCoop\SEPS_EEFF.duckdb")
BATCH     = 100_000   # filas por lote en la migración

C_NODEV = "'1425','1426','1427','1428','1432','1433','1434','1435','1436','1440','1441','1442','1443','1444','1448'"
C_VENC  = "'1449','1450','1451','1452','1456','1457','1458','1459'"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ── DDL ───────────────────────────────────────────────────────────
DDL = """
-- Catálogo de cooperativas
CREATE TABLE IF NOT EXISTS dim_cooperativa (
    ruc             VARCHAR(15)  PRIMARY KEY,
    razon_social    VARCHAR(400) NOT NULL,
    segmento        VARCHAR(60),
    primera_fecha   DATE,
    ultima_fecha    DATE,
    meses_activo    SMALLINT,
    estado          VARCHAR(20)
);

-- Catálogo de cuentas contables
CREATE TABLE IF NOT EXISTS dim_cuenta (
    cuenta             VARCHAR(10)  PRIMARY KEY,
    descripcion_cuenta VARCHAR(300),
    nivel              SMALLINT     -- 2=grupo, 4=subgrupo, 6=cuenta detalle
);

-- Tabla de hechos principal
CREATE TABLE IF NOT EXISTS fact_eeff (
    id          BIGSERIAL    PRIMARY KEY,
    fecha_corte DATE         NOT NULL,
    ruc         VARCHAR(15)  NOT NULL,
    cuenta      VARCHAR(10)  NOT NULL,
    saldo_usd   NUMERIC(20,4),
    anio        VARCHAR(4),
    CONSTRAINT fk_coop  FOREIGN KEY (ruc)    REFERENCES dim_cooperativa(ruc),
    CONSTRAINT fk_cuenta FOREIGN KEY (cuenta) REFERENCES dim_cuenta(cuenta)
);

CREATE INDEX IF NOT EXISTS idx_fe_fecha  ON fact_eeff (fecha_corte);
CREATE INDEX IF NOT EXISTS idx_fe_ruc    ON fact_eeff (ruc);
CREATE INDEX IF NOT EXISTS idx_fe_cuenta ON fact_eeff (cuenta);
CREATE INDEX IF NOT EXISTS idx_fe_fc_ruc ON fact_eeff (fecha_corte, ruc);

-- Indicadores precalculados por cooperativa y mes
CREATE TABLE IF NOT EXISTS fact_indicadores (
    fecha_corte         DATE         NOT NULL,
    ruc                 VARCHAR(15)  NOT NULL REFERENCES dim_cooperativa(ruc),
    activo_total        NUMERIC(20,4),
    patrimonio          NUMERIC(20,4),
    cartera_bruta       NUMERIC(20,4),
    depositos           NUMERIC(20,4),
    capitalizacion_pct  NUMERIC(10,4),
    morosidad_pct       NUMERIC(10,4),
    cobertura_pct       NUMERIC(10,4),
    roa_pct             NUMERIC(10,4),
    roe_pct             NUMERIC(10,4),
    nim_pct             NUMERIC(10,4),
    liquidez_ampliada   NUMERIC(10,4),
    eficiencia_op_pct   NUMERIC(10,4),
    apalancamiento      NUMERIC(10,4),
    intermediacion      NUMERIC(10,4),
    camel_score         NUMERIC(5,3),
    rating_camel        VARCHAR(15),
    PRIMARY KEY (fecha_corte, ruc)
);

CREATE INDEX IF NOT EXISTS idx_ind_fecha ON fact_indicadores (fecha_corte);
CREATE INDEX IF NOT EXISTS idx_ind_ruc   ON fact_indicadores (ruc);
CREATE INDEX IF NOT EXISTS idx_ind_rating ON fact_indicadores (rating_camel);
"""


# ── Crear base de datos ───────────────────────────────────────────
def crear_base(password: str) -> None:
    log.info("Creando base de datos '%s' si no existe…", PG_DB)
    con = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER,
        password=password, dbname="postgres"
    )
    con.autocommit = True
    cur = con.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (PG_DB,))
    if cur.fetchone():
        log.info("  La base '%s' ya existe.", PG_DB)
    else:
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(PG_DB)))
        log.info("  Base '%s' creada.", PG_DB)
    cur.close()
    con.close()


def conectar(password: str) -> psycopg2.extensions.connection:
    return psycopg2.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER,
        password=password, dbname=PG_DB
    )


# ── Schema ────────────────────────────────────────────────────────
def crear_schema(pg: psycopg2.extensions.connection) -> None:
    log.info("Creando tablas e índices…")
    with pg.cursor() as cur:
        cur.execute(DDL)
    pg.commit()
    log.info("  Schema listo.")


# ── Dimensiones ───────────────────────────────────────────────────
def cargar_dim_cooperativa(pg, duck) -> None:
    log.info("Cargando dim_cooperativa…")
    df = duck.execute("""
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
    """).df()

    rows = [tuple(r) for r in df.itertuples(index=False)]
    with pg.cursor() as cur:
        execute_values(cur, """
            INSERT INTO dim_cooperativa
                (ruc, razon_social, segmento, primera_fecha, ultima_fecha, meses_activo, estado)
            VALUES %s
            ON CONFLICT (ruc) DO UPDATE SET
                razon_social  = EXCLUDED.razon_social,
                segmento      = EXCLUDED.segmento,
                ultima_fecha  = EXCLUDED.ultima_fecha,
                meses_activo  = EXCLUDED.meses_activo,
                estado        = EXCLUDED.estado
        """, rows)
    pg.commit()
    log.info("  %d cooperativas cargadas.", len(rows))


def cargar_dim_cuenta(pg, duck) -> None:
    log.info("Cargando dim_cuenta…")
    df = duck.execute("""
        SELECT
            cuenta,
            LAST(descripcion_cuenta ORDER BY fecha_corte) AS descripcion_cuenta,
            LENGTH(cuenta) AS nivel
        FROM eeff_mensuales
        WHERE cuenta IS NOT NULL AND cuenta != ''
        GROUP BY cuenta
        ORDER BY cuenta
    """).df()

    rows = [tuple(r) for r in df.itertuples(index=False)]
    with pg.cursor() as cur:
        execute_values(cur, """
            INSERT INTO dim_cuenta (cuenta, descripcion_cuenta, nivel)
            VALUES %s
            ON CONFLICT (cuenta) DO UPDATE SET
                descripcion_cuenta = EXCLUDED.descripcion_cuenta
        """, rows)
    pg.commit()
    log.info("  %d cuentas cargadas.", len(rows))


# ── Fact EEFF (migración por lotes) ───────────────────────────────
def cargar_fact_eeff(pg, duck) -> None:
    log.info("Migrando fact_eeff (~31M filas, puede tardar 15-30 min)…")

    total_duck = duck.execute("SELECT COUNT(*) FROM eeff_mensuales").fetchone()[0]
    log.info("  Filas en DuckDB: %s", f"{total_duck:,}")

    with pg.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM fact_eeff")
        ya_migradas = cur.fetchone()[0]

    if ya_migradas > 0:
        log.info("  Ya existen %s filas en PostgreSQL.", f"{ya_migradas:,}")
        resp = input("  ¿Borrar y reimportar? (s/N): ").strip().lower()
        if resp == 's':
            with pg.cursor() as cur:
                cur.execute("TRUNCATE fact_eeff RESTART IDENTITY")
            pg.commit()
            log.info("  Tabla vaciada.")
        else:
            log.info("  Migración omitida.")
            return

    offset    = 0
    migradas  = 0
    años      = duck.execute("SELECT DISTINCT año FROM eeff_mensuales ORDER BY año").df()['año'].tolist()

    for año in años:
        log.info("  Procesando año %s…", año)
        df_año = duck.execute(f"""
            SELECT fecha_corte, ruc, cuenta, saldo_usd, año
            FROM eeff_mensuales
            WHERE año = '{año}'
            ORDER BY fecha_corte, ruc, cuenta
        """).df()

        # Insertar en lotes
        for start in range(0, len(df_año), BATCH):
            lote = df_año.iloc[start:start + BATCH]
            rows = [
                (r.fecha_corte, r.ruc, r.cuenta,
                 None if pd.isna(r.saldo_usd) else float(r.saldo_usd),
                 r.año)
                for r in lote.itertuples(index=False)
            ]
            with pg.cursor() as cur:
                execute_values(cur, """
                    INSERT INTO fact_eeff (fecha_corte, ruc, cuenta, saldo_usd, anio)
                    VALUES %s
                """, rows, page_size=BATCH)
            pg.commit()
            migradas += len(rows)

        log.info("    %s → %s filas migradas (total: %s)",
                 año, f"{len(df_año):,}", f"{migradas:,}")

    log.info("  Migración completada: %s filas.", f"{migradas:,}")


# ── Indicadores precalculados ─────────────────────────────────────
def calcular_indicadores(pg, duck) -> None:
    log.info("Calculando fact_indicadores por cooperativa y mes…")

    fechas = duck.execute(
        "SELECT DISTINCT fecha_corte FROM eeff_mensuales ORDER BY fecha_corte"
    ).df()['fecha_corte'].tolist()

    log.info("  Períodos a procesar: %d", len(fechas))

    with pg.cursor() as cur:
        cur.execute("TRUNCATE fact_indicadores")
    pg.commit()

    total_rows = 0
    for fecha in fechas:
        fin = duck.execute(f"""
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
            WHERE fecha_corte = '{fecha}'
            GROUP BY ruc
        """).df()

        def safe(num, den, scale=100):
            return np.where(den > 0, num / den * scale, np.nan)

        fin['resultado']         = fin['ingresos_total'].fillna(0) - fin['gastos_total'].fillna(0)
        fin['cart_imp']          = fin['cart_nodev'].fillna(0) + fin['cart_vencida'].fillna(0)
        fin['margen']            = fin['int_ganados'].fillna(0) - fin['int_causados'].fillna(0)
        fin['capitalizacion']    = safe(fin['patrimonio'], fin['activo_total'])
        fin['morosidad']         = safe(fin['cart_imp'], fin['cartera_bruta'])
        fin['cobertura']         = safe(fin['provisiones'].abs(), fin['cart_imp'])
        fin['roa']               = safe(fin['resultado'], fin['activo_total'])
        fin['roe']               = safe(fin['resultado'], fin['patrimonio'])
        fin['nim']               = safe(fin['margen'], fin['activo_total'])
        fin['liquidez_ampliada'] = safe(fin['fondos_disp'].fillna(0)+fin['inversiones'].fillna(0), fin['depositos'])
        fin['eficiencia_op']     = safe(fin['gastos_op'].fillna(0), fin['activo_total'])
        fin['apalancamiento']    = safe(fin['pasivo_total'], fin['patrimonio'], scale=1)
        fin['intermediacion']    = safe(fin['cartera_bruta'], fin['depositos'])

        def camel(row):
            def sc(v, bp, sc_vals):
                if pd.isna(v): return 3.0
                for b, s in zip(bp, sc_vals[:-1]):
                    if v >= b: return s
                return sc_vals[-1]
            c = sc(row['capitalizacion'], [15,12,9,6],   [1,2,3,4,5])
            a = (sc(row['morosidad'],     [100,6,4,2,0], [5,4,3,2,1]) +
                 sc(row['cobertura'],     [200,150,100,75],[1,2,3,4,5])) / 2
            m = sc(row['eficiencia_op'],  [100,7,5.5,4,3],[5,4,3,2,1])
            e = sc(row['roa'],            [1.5,0.75,0,-0.5],[1,2,3,4,5])
            l = sc(row['liquidez_ampliada'],[25,20,14,10],[1,2,3,4,5])
            return round(0.25*c + 0.25*a + 0.20*m + 0.15*e + 0.15*l, 3)

        def rating(v):
            if pd.isna(v): return 'SIN DATOS'
            if v <= 1.5:   return 'EXCELENTE'
            if v <= 2.5:   return 'BUENO'
            if v <= 3.5:   return 'ADECUADO'
            if v <= 4.5:   return 'MARGINAL'
            return 'CRITICO'

        fin['camel_score']  = fin.apply(camel, axis=1)
        fin['rating_camel'] = fin['camel_score'].apply(rating)

        def nan_none(v):
            return None if (v is None or (isinstance(v, float) and np.isnan(v))) else float(v)

        rows = []
        for r in fin.itertuples(index=False):
            rows.append((
                fecha, r.ruc,
                nan_none(r.activo_total), nan_none(r.patrimonio),
                nan_none(r.cartera_bruta), nan_none(r.depositos),
                nan_none(r.capitalizacion), nan_none(r.morosidad),
                nan_none(r.cobertura), nan_none(r.roa), nan_none(r.roe),
                nan_none(r.nim), nan_none(r.liquidez_ampliada),
                nan_none(r.eficiencia_op), nan_none(r.apalancamiento),
                nan_none(r.intermediacion),
                nan_none(r.camel_score), r.rating_camel
            ))

        with pg.cursor() as cur:
            execute_values(cur, """
                INSERT INTO fact_indicadores (
                    fecha_corte, ruc,
                    activo_total, patrimonio, cartera_bruta, depositos,
                    capitalizacion_pct, morosidad_pct, cobertura_pct,
                    roa_pct, roe_pct, nim_pct, liquidez_ampliada,
                    eficiencia_op_pct, apalancamiento, intermediacion,
                    camel_score, rating_camel
                ) VALUES %s
                ON CONFLICT (fecha_corte, ruc) DO UPDATE SET
                    camel_score  = EXCLUDED.camel_score,
                    rating_camel = EXCLUDED.rating_camel
            """, rows)
        pg.commit()
        total_rows += len(rows)

    log.info("  fact_indicadores: %s filas insertadas.", f"{total_rows:,}")


# ── Main ──────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Migrar DuckDB SEPS → PostgreSQL")
    parser.add_argument("--password",         default=None,  help="Contraseña PostgreSQL")
    parser.add_argument("--solo-schema",      action="store_true", help="Solo crear tablas")
    parser.add_argument("--solo-indicadores", action="store_true", help="Solo recalcular indicadores")
    args = parser.parse_args()

    password = args.password or PG_PASS or getpass.getpass(f"Contraseña PostgreSQL ({PG_USER}@{PG_HOST}): ")

    # Conectar a DuckDB
    log.info("Abriendo DuckDB: %s", DUCK_PATH)
    duck = duckdb.connect(str(DUCK_PATH), read_only=True)

    # Crear BD y conectar a PostgreSQL
    crear_base(password)
    pg = conectar(password)
    log.info("Conectado a PostgreSQL %s:%s/%s", PG_HOST, PG_PORT, PG_DB)

    try:
        crear_schema(pg)

        if args.solo_indicadores:
            calcular_indicadores(pg, duck)
        elif args.solo_schema:
            log.info("Solo schema — datos no migrados.")
        else:
            cargar_dim_cooperativa(pg, duck)
            cargar_dim_cuenta(pg, duck)
            cargar_fact_eeff(pg, duck)
            calcular_indicadores(pg, duck)

        # Resumen final
        log.info("=" * 55)
        log.info("MIGRACIÓN COMPLETADA")
        with pg.cursor() as cur:
            for tabla in ["dim_cooperativa", "dim_cuenta", "fact_eeff", "fact_indicadores"]:
                cur.execute(f"SELECT COUNT(*) FROM {tabla}")
                n = cur.fetchone()[0]
                log.info("  %-25s %s filas", tabla, f"{n:,}")

    finally:
        pg.close()
        duck.close()


if __name__ == "__main__":
    main()
