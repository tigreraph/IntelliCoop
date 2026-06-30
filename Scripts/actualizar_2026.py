"""
Actualiza el archivo 2026 desde el portal SEPS y reconstruye SEPS_EEFF.duckdb.

Uso:
    py actualizar_2026.py

Requisitos:
    py -m pip install selenium webdriver-manager duckdb pandas
"""

import sys
import time
import zipfile
import logging
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

BASE_DIR   = Path(r"C:\Users\Jonna\OneDrive - St Paulinus Catholic Primary School\claude proyectos\IntelliCoop")
DATOS_DIR  = BASE_DIR / "Base de datos"
TEMP_DIR   = BASE_DIR / "_temporal_bd"
DB_PATH    = BASE_DIR / "SEPS_EEFF.duckdb"
URL_PORTAL = "https://estadisticas.seps.gob.ec/index.php/estadisticas-sfps/"

AÑO        = "2026"
URL_2026   = "https://estadisticas.seps.gob.ec/?sdm_process_download=1&download_id=3258"
TIMEOUT    = 300

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Chrome ───────────────────────────────────────────────────────
def crear_driver() -> webdriver.Chrome:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    opts = Options()
    opts.add_experimental_option("prefs", {
        "download.default_directory":   str(TEMP_DIR),
        "download.prompt_for_download": False,
        "download.directory_upgrade":   True,
        "safebrowsing.enabled":         True,
    })
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1280,900")
    servicio = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=servicio, options=opts)


# ── Esperar descarga ──────────────────────────────────────────────
def esperar_archivo(timeout: int = TIMEOUT) -> Path | None:
    archivos_antes = set(TEMP_DIR.iterdir())
    inicio = time.time()
    while time.time() - inicio < timeout:
        en_progreso = list(TEMP_DIR.glob("*.crdownload"))
        actuales    = set(TEMP_DIR.iterdir())
        nuevos      = [f for f in (actuales - archivos_antes)
                       if f.suffix.lower() != ".crdownload"]
        if nuevos and not en_progreso:
            archivo = sorted(nuevos, key=lambda p: p.stat().st_mtime)[-1]
            log.info("Descarga completa: %s  (%.1f MB)",
                     archivo.name, archivo.stat().st_size / 1_048_576)
            return archivo
        time.sleep(2)
    log.error("Tiempo agotado esperando la descarga.")
    return None


# ── Guardar ───────────────────────────────────────────────────────
def guardar(archivo: Path, año: str) -> None:
    carpeta = DATOS_DIR / año
    carpeta.mkdir(parents=True, exist_ok=True)

    if archivo.suffix.lower() == ".zip":
        with zipfile.ZipFile(archivo, "r") as zf:
            miembros = [m for m in zf.infolist() if not m.filename.endswith("/")]
            log.info("ZIP contiene %d archivo(s).", len(miembros))
            for info in miembros:
                nombre = Path(info.filename).name
                if not nombre:
                    continue
                destino = carpeta / nombre
                datos = zf.read(info.filename)
                destino.write_bytes(datos)
                log.info("Guardado: %s  (%.2f MB)", destino.name, len(datos) / 1_048_576)
        archivo.unlink()
    else:
        destino = carpeta / archivo.name
        archivo.replace(destino)
        log.info("Guardado: %s", destino.name)


# ── Descarga 2026 ─────────────────────────────────────────────────
def descargar_2026() -> bool:
    log.info("=" * 55)
    log.info("PASO 1: Descargando datos 2026 desde SEPS…")
    driver = crear_driver()
    try:
        log.info("Estableciendo sesión en el portal SEPS…")
        driver.get(URL_PORTAL)
        time.sleep(4)

        log.info("Iniciando descarga del archivo 2026…")
        driver.get(URL_2026)
        archivo = esperar_archivo()

        if not archivo:
            log.error("No se pudo descargar el archivo 2026.")
            return False

        # Eliminar archivo anterior y guardar el nuevo
        carpeta_2026 = DATOS_DIR / AÑO
        for f in carpeta_2026.glob("*"):
            log.info("Eliminando archivo anterior: %s", f.name)
            f.unlink()

        guardar(archivo, AÑO)
        return True
    finally:
        driver.quit()
        try:
            if TEMP_DIR.exists() and not any(TEMP_DIR.iterdir()):
                TEMP_DIR.rmdir()
        except Exception:
            pass


# ── Reconstruir DuckDB ────────────────────────────────────────────
def reconstruir_db() -> None:
    log.info("=" * 55)
    log.info("PASO 2: Reconstruyendo SEPS_EEFF.duckdb…")

    # Importar aquí para no requerir duckdb si solo se descarga
    import zipfile as zf_mod
    import duckdb
    import pandas as pd

    COLUMNAS = ["fecha_corte", "segmento", "ruc", "razon_social",
                "cuenta", "descripcion_cuenta", "saldo_usd", "año"]

    def detectar_sep(ruta):
        with open(ruta, "r", encoding="latin-1", errors="replace") as f:
            primera = f.readline()
        return ";" if primera.count(";") > primera.count("\t") else "\t"

    def leer_archivo(ruta, año_str):
        sep = detectar_sep(ruta)
        for enc in ["latin-1", "utf-8", "utf-8-sig"]:
            try:
                df = pd.read_csv(ruta, sep=sep, encoding=enc, dtype=str,
                                 quotechar='"', on_bad_lines="skip")
                break
            except Exception:
                continue
        else:
            log.error("  No se pudo leer: %s", ruta.name)
            return None

        df.columns = (df.columns.str.strip().str.upper()
                      .str.replace(r"[\s\(\)]+", "_", regex=True)
                      .str.replace(r"_+", "_", regex=True).str.strip("_"))

        renombrar = {
            "FECHA_DE_CORTE": "fecha_corte", "FECHA_CORTE": "fecha_corte",
            "SEGMENTO": "segmento", "RUC": "ruc", "RAZON_SOCIAL": "razon_social",
            "CUENTA": "cuenta", "DESCRIPCION_CUENTA": "descripcion_cuenta",
            "SALDO_USD": "saldo_usd", "SALDO__USD_": "saldo_usd", "SALDO_USD_": "saldo_usd",
        }
        col_map = {}
        for col in df.columns:
            cl = col.strip("_")
            if cl in renombrar:
                col_map[col] = renombrar[cl]
            elif "FECHA" in col:
                col_map[col] = "fecha_corte"
            elif "RAZON" in col or "RAZ" in col:
                col_map[col] = "razon_social"
            elif "DESCRIPCION" in col or "DESCRIPCI" in col:
                col_map[col] = "descripcion_cuenta"
            elif cl == "SALDO":
                col_map[col] = "saldo_usd"
        df = df.rename(columns=col_map)

        faltantes = {"fecha_corte", "cuenta", "saldo_usd"} - set(df.columns)
        if faltantes:
            log.warning("  Columnas faltantes en %s: %s", ruta.name, faltantes)
            return None

        df["saldo_usd"]   = pd.to_numeric(df["saldo_usd"].str.strip().str.replace(",", "."), errors="coerce").fillna(0)
        df["fecha_corte"] = pd.to_datetime(df["fecha_corte"].str.strip().str.strip('"'), errors="coerce")
        df["cuenta"]      = df["cuenta"].str.strip().str.strip('"')
        df["año"]         = año_str
        for col in ["segmento", "ruc", "razon_social", "descripcion_cuenta"]:
            if col in df.columns:
                df[col] = df[col].str.strip().str.strip('"')
            else:
                df[col] = None
        return df[COLUMNAS]

    def leer_zip(ruta_zip, año_str):
        try:
            with zf_mod.ZipFile(ruta_zip, "r") as zf:
                for info in zf.infolist():
                    if info.filename.endswith("/"):
                        continue
                    if Path(info.filename).suffix.lower() in {".csv", ".txt"}:
                        tmp = BASE_DIR / "_tmp_ant.txt"
                        tmp.write_bytes(zf.read(info.filename))
                        df = leer_archivo(tmp, año_str)
                        tmp.unlink(missing_ok=True)
                        if df is not None:
                            return df
        except Exception as e:
            log.error("  Error leyendo ZIP %s: %s", ruta_zip.name, e)
        return None

    if DB_PATH.exists():
        DB_PATH.unlink()

    con = duckdb.connect(str(DB_PATH))
    con.execute("""
        CREATE TABLE eeff_mensuales (
            fecha_corte DATE, segmento VARCHAR, ruc VARCHAR,
            razon_social VARCHAR, cuenta VARCHAR,
            descripcion_cuenta VARCHAR, saldo_usd DOUBLE, año VARCHAR
        )
    """)

    total_filas = 0
    for carpeta in sorted(DATOS_DIR.iterdir()):
        if not carpeta.is_dir():
            continue
        año_str = carpeta.name
        log.info("Procesando: %s", año_str)
        for archivo in sorted(carpeta.iterdir()):
            ext = archivo.suffix.lower()
            if ext in {".csv", ".txt"}:
                df = leer_archivo(archivo, año_str)
            elif ext == ".zip":
                nombre_año = archivo.stem.split()[0]
                df = leer_zip(archivo, nombre_año)
            else:
                continue
            if df is None or df.empty:
                log.warning("  Sin datos: %s", archivo.name)
                continue
            con.execute("INSERT INTO eeff_mensuales SELECT * FROM df")
            total_filas += len(df)
            log.info("  %s → %s filas  (acumulado: %s)",
                     archivo.name, f"{len(df):,}", f"{total_filas:,}")

    log.info("Creando índices…")
    con.execute("CREATE INDEX idx_cuenta ON eeff_mensuales (cuenta)")
    con.execute("CREATE INDEX idx_fecha  ON eeff_mensuales (fecha_corte)")
    con.execute("CREATE INDEX idx_ruc    ON eeff_mensuales (ruc)")
    con.execute("CREATE INDEX idx_seg    ON eeff_mensuales (segmento)")

    resumen = con.execute("""
        SELECT año,
               COUNT(DISTINCT ruc)         AS cooperativas,
               COUNT(DISTINCT fecha_corte) AS meses,
               COUNT(*)                    AS filas,
               MAX(fecha_corte)            AS fecha_max
        FROM eeff_mensuales
        GROUP BY año ORDER BY año
    """).df()
    con.close()

    log.info("=" * 55)
    log.info("BASE DE DATOS LISTA: %s  (%.1f MB)", DB_PATH, DB_PATH.stat().st_size / 1_048_576)
    log.info("Total filas: %s\n%s", f"{total_filas:,}", resumen.to_string(index=False))


# ── Main ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    solo_db = "--solo-db" in sys.argv

    if not solo_db:
        ok = descargar_2026()
        if not ok:
            log.error("Descarga fallida. Abortando.")
            sys.exit(1)

    reconstruir_db()
    log.info("ACTUALIZACIÓN COMPLETADA")
