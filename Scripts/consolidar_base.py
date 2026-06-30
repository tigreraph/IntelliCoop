"""
Consolida todos los archivos anuales de EEFF Mensuales SEPS
en una sola base de datos DuckDB optimizada para análisis.

Resultado: Base Cooperativas segmentos/SEPS_EEFF.duckdb  (~300 MB)

Uso:
    py consolidar_base.py

Requisitos:
    py -m pip install duckdb pandas pyarrow
"""

import zipfile
import logging
from pathlib import Path

import duckdb
import pandas as pd

# ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(r"C:\Users\Jonna\OneDrive - St Paulinus Catholic Primary School\claude proyectos\IntelliCoop")
DATOS_DIR = BASE_DIR / "Base de datos"
DB_PATH   = BASE_DIR / "SEPS_EEFF.duckdb"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Columnas estándar que tendrá la tabla final
COLUMNAS = ["fecha_corte", "segmento", "ruc", "razon_social",
            "cuenta", "descripcion_cuenta", "saldo_usd", "año"]


# ─────────────────────────────────────────────────────────────────
# LECTURA Y NORMALIZACIÓN
# ─────────────────────────────────────────────────────────────────
def detectar_sep(ruta: Path) -> str:
    """Detecta si el archivo usa ; o tabulación como separador."""
    with open(ruta, "r", encoding="latin-1", errors="replace") as f:
        primera = f.readline()
    return ";" if primera.count(";") > primera.count("\t") else "\t"


def leer_archivo(ruta: Path, año: str) -> pd.DataFrame | None:
    """Lee un CSV/TXT y devuelve un DataFrame con columnas normalizadas."""
    sep = detectar_sep(ruta)
    encodings = ["latin-1", "utf-8", "utf-8-sig"]

    for enc in encodings:
        try:
            df = pd.read_csv(
                ruta,
                sep=sep,
                encoding=enc,
                dtype=str,          # leer todo como texto primero
                quotechar='"',
                on_bad_lines="skip",
            )
            break
        except Exception:
            continue
    else:
        log.error("  No se pudo leer: %s", ruta.name)
        return None

    # Normalizar nombres de columnas
    df.columns = (
        df.columns
        .str.strip()
        .str.upper()
        .str.replace(r"[\s\(\)]+", "_", regex=True)
        .str.replace(r"_+", "_", regex=True)
        .str.strip("_")
    )

    # Mapear nombres variantes a nombres estándar
    renombrar = {
        "FECHA_DE_CORTE":    "fecha_corte",
        "FECHA_DE_CORTE_":   "fecha_corte",
        "FECHA_CORTE":       "fecha_corte",
        "FECHA_DE_CORTE":    "fecha_corte",
        "SEGMENTO":          "segmento",
        "RUC":               "ruc",
        "RAZON_SOCIAL":      "razon_social",
        "CUENTA":            "cuenta",
        "DESCRIPCION_CUENTA": "descripcion_cuenta",
        "SALDO_USD":         "saldo_usd",
        "SALDO__USD_":       "saldo_usd",
        "SALDO_USD_":        "saldo_usd",
    }
    # Buscar columnas que coincidan parcialmente
    col_map = {}
    for col in df.columns:
        col_limpia = col.strip("_")
        if col_limpia in renombrar:
            col_map[col] = renombrar[col_limpia]
        elif "FECHA" in col:
            col_map[col] = "fecha_corte"
        elif "RAZON" in col or "RAZ" in col:
            col_map[col] = "razon_social"
        elif "DESCRIPCION" in col or "DESCRIPCI" in col:
            col_map[col] = "descripcion_cuenta"
        elif col_limpia == "SALDO":
            col_map[col] = "saldo_usd"

    df = df.rename(columns=col_map)

    # Verificar que tengamos las columnas mínimas
    requeridas = {"fecha_corte", "cuenta", "saldo_usd"}
    faltantes = requeridas - set(df.columns)
    if faltantes:
        log.warning("  Columnas faltantes en %s: %s", ruta.name, faltantes)
        log.warning("  Columnas encontradas: %s", list(df.columns))
        return None

    # Limpiar y convertir tipos
    df["saldo_usd"]   = pd.to_numeric(df["saldo_usd"].str.strip().str.replace(",", "."), errors="coerce").fillna(0)
    df["fecha_corte"] = pd.to_datetime(df["fecha_corte"].str.strip().str.strip('"'), errors="coerce")
    df["cuenta"]      = df["cuenta"].str.strip().str.strip('"')
    df["año"]         = año

    for col in ["segmento", "ruc", "razon_social", "descripcion_cuenta"]:
        if col in df.columns:
            df[col] = df[col].str.strip().str.strip('"')
        else:
            df[col] = None

    # Retornar solo columnas estándar
    return df[COLUMNAS]


def leer_zip_anteriores(ruta_zip: Path, año: str) -> pd.DataFrame | None:
    """Extrae y lee un ZIP de años anteriores (2015-2017)."""
    try:
        with zipfile.ZipFile(ruta_zip, "r") as zf:
            miembros = [m for m in zf.infolist() if not m.filename.endswith("/")]
            for info in miembros:
                ext = Path(info.filename).suffix.lower()
                if ext in {".csv", ".txt"}:
                    data = zf.read(info.filename)
                    tmp = BASE_DIR / "_tmp_ant.txt"
                    tmp.write_bytes(data)
                    df = leer_archivo(tmp, año)
                    tmp.unlink(missing_ok=True)
                    if df is not None:
                        return df
    except Exception as e:
        log.error("  Error leyendo ZIP %s: %s", ruta_zip.name, e)
    return None


# ─────────────────────────────────────────────────────────────────
# CONSOLIDACIÓN EN DUCKDB
# ─────────────────────────────────────────────────────────────────
def consolidar() -> None:
    if DB_PATH.exists():
        log.info("Base de datos existente encontrada. Se sobreescribirá.")
        DB_PATH.unlink()

    con = duckdb.connect(str(DB_PATH))

    # Crear tabla principal
    con.execute("""
        CREATE TABLE eeff_mensuales (
            fecha_corte       DATE,
            segmento          VARCHAR,
            ruc               VARCHAR,
            razon_social      VARCHAR,
            cuenta            VARCHAR,
            descripcion_cuenta VARCHAR,
            saldo_usd         DOUBLE,
            año               VARCHAR
        )
    """)

    total_filas = 0

    # Iterar carpetas por año
    for carpeta in sorted(DATOS_DIR.iterdir()):
        if not carpeta.is_dir():
            continue

        año = carpeta.name
        log.info("=" * 50)
        log.info("Procesando: %s", año)

        archivos = list(carpeta.iterdir())
        for archivo in archivos:
            ext = archivo.suffix.lower()

            if ext in {".csv", ".txt"}:
                log.info("  Leyendo: %s", archivo.name)
                df = leer_archivo(archivo, año)

            elif ext == ".zip":
                # Años anteriores (2015, 2016, 2017 vienen zipeados)
                nombre_año = archivo.stem.split()[0]  # "2015 EEFF MEN.zip" → "2015"
                log.info("  Leyendo ZIP: %s → año %s", archivo.name, nombre_año)
                df = leer_zip_anteriores(archivo, nombre_año)

            else:
                log.warning("  Ignorado: %s", archivo.name)
                continue

            if df is None or df.empty:
                log.warning("  Sin datos en: %s", archivo.name)
                continue

            # Insertar en DuckDB
            con.execute("INSERT INTO eeff_mensuales SELECT * FROM df")
            filas = len(df)
            total_filas += filas
            log.info("  Insertadas: %s filas  (acumulado: %s)", f"{filas:,}", f"{total_filas:,}")

    # Índices para consultas rápidas
    log.info("Creando índices…")
    con.execute("CREATE INDEX idx_cuenta ON eeff_mensuales (cuenta)")
    con.execute("CREATE INDEX idx_fecha  ON eeff_mensuales (fecha_corte)")
    con.execute("CREATE INDEX idx_ruc    ON eeff_mensuales (ruc)")
    con.execute("CREATE INDEX idx_seg    ON eeff_mensuales (segmento)")

    # Verificación final
    resumen = con.execute("""
        SELECT
            año,
            COUNT(DISTINCT ruc)          AS cooperativas,
            COUNT(DISTINCT fecha_corte)  AS meses,
            COUNT(*)                     AS filas,
            SUM(saldo_usd)/1e9           AS total_miles_millones_usd
        FROM eeff_mensuales
        GROUP BY año
        ORDER BY año
    """).df()

    con.close()

    log.info("=" * 50)
    log.info("BASE DE DATOS CONSOLIDADA")
    log.info("Ubicación: %s", DB_PATH)
    log.info("Tamaño:    %.1f MB", DB_PATH.stat().st_size / 1_048_576)
    log.info("Total filas: %s", f"{total_filas:,}")
    log.info("\n%s", resumen.to_string(index=False))


# ─────────────────────────────────────────────────────────────────
# EJEMPLO DE USO (se imprime al terminar)
# ─────────────────────────────────────────────────────────────────
def mostrar_ejemplos() -> None:
    log.info("\n" + "=" * 50)
    log.info("CÓMO USAR LA BASE DE DATOS:")
    log.info("""
import duckdb
import pandas as pd

con = duckdb.connect(r"%s")

# Fondos disponibles (cta 11) e Inversiones (cta 13) — liquidez
liquidez = con.execute(\"\"\"
    SELECT fecha_corte, segmento, ruc, razon_social,
           cuenta, descripcion_cuenta, saldo_usd
    FROM   eeff_mensuales
    WHERE  LEFT(cuenta, 2) IN ('11', '13')
    ORDER  BY fecha_corte, ruc, cuenta
\"\"\").df()

# Ver años y meses disponibles
con.execute("SELECT año, COUNT(DISTINCT fecha_corte) meses FROM eeff_mensuales GROUP BY año ORDER BY año").df()

con.close()
""", DB_PATH)


if __name__ == "__main__":
    consolidar()
    mostrar_ejemplos()
