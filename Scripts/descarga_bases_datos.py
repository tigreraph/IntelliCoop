"""
Descarga automatizada - BASES DE DATOS Estados Financieros Mensuales SEPS
Cooperativas segmentos 1, 2, 3 — archivos de texto separados por tabulaciones

Uso:
    py descarga_bases_datos.py

Requisitos:
    py -m pip install selenium webdriver-manager
"""

import time
import zipfile
import logging
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ─────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(r"C:\Users\Jonna\OneDrive - St Paulinus Catholic Primary School\claude proyectos\IntelliCoop")
TEMP_DIR = BASE_DIR / "_temporal_bd"
URL_PORTAL = "https://estadisticas.seps.gob.ec/index.php/estadisticas-sfps/"

# Bases de Datos — Estados Financieros Mensuales (6 dígitos, separado por tabulaciones)
# IDs confirmados desde la página oficial
BASES_DE_DATOS = [
    {"año": "2026",       "url": "https://estadisticas.seps.gob.ec/?sdm_process_download=1&download_id=3258"},
    {"año": "2025",       "url": "https://estadisticas.seps.gob.ec/?sdm_process_download=1&download_id=2773"},
    {"año": "2024",       "url": "https://estadisticas.seps.gob.ec/?smd_process_download=1&download_id=2330"},
    {"año": "2023",       "url": "https://estadisticas.seps.gob.ec/?smd_process_download=1&download_id=1387"},
    {"año": "2022",       "url": "https://estadisticas.seps.gob.ec/?smd_process_download=1&download_id=1818"},
    {"año": "2021",       "url": "https://estadisticas.seps.gob.ec/?smd_process_download=1&download_id=895"},
    {"año": "2020",       "url": "https://estadisticas.seps.gob.ec/?smd_process_download=1&download_id=896"},
    {"año": "2019",       "url": "https://estadisticas.seps.gob.ec/?smd_process_download=1&download_id=897"},
    {"año": "2018",       "url": "https://estadisticas.seps.gob.ec/?smd_process_download=1&download_id=898"},
    {"año": "Anteriores", "url": "https://estadisticas.seps.gob.ec/?smd_process_download=1&download_id=899"},
]

TIMEOUT_DESCARGA = 300  # segundos — las bases de datos son más pesadas que los boletines

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# CHROME
# ─────────────────────────────────────────────────────────────────
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
    # Descomenta para correr sin ventana:
    # opts.add_argument("--headless=new")

    servicio = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=servicio, options=opts)


# ─────────────────────────────────────────────────────────────────
# ESPERAR DESCARGA
# ─────────────────────────────────────────────────────────────────
def esperar_archivo(timeout: int = TIMEOUT_DESCARGA) -> Path | None:
    """Espera hasta que aparezca un archivo nuevo y completo en TEMP_DIR."""
    archivos_antes = set(TEMP_DIR.iterdir())
    inicio = time.time()

    while time.time() - inicio < timeout:
        en_progreso  = list(TEMP_DIR.glob("*.crdownload"))
        actuales     = set(TEMP_DIR.iterdir())
        nuevos       = [f for f in (actuales - archivos_antes)
                        if f.suffix.lower() != ".crdownload"]

        if nuevos and not en_progreso:
            archivo = sorted(nuevos, key=lambda p: p.stat().st_mtime)[-1]
            tam_mb  = archivo.stat().st_size / 1_048_576
            log.info("  Descarga completa: %s  (%.1f MB)", archivo.name, tam_mb)
            return archivo

        time.sleep(2)

    log.error("  Tiempo agotado esperando la descarga.")
    return None


# ─────────────────────────────────────────────────────────────────
# GUARDAR ARCHIVO
# ─────────────────────────────────────────────────────────────────
def guardar(archivo: Path, año: str) -> None:
    """
    El ZIP contiene UN solo archivo con todos los meses del año.
    Lo extrae directamente a BASE_DIR/Base de datos/año/ conservando el nombre original.
    """
    carpeta = BASE_DIR / "Base de datos" / año
    carpeta.mkdir(parents=True, exist_ok=True)

    sufijo = archivo.suffix.lower()

    # ── ZIP ──────────────────────────────────────────────────────
    if sufijo == ".zip":
        try:
            with zipfile.ZipFile(archivo, "r") as zf:
                miembros = [m for m in zf.infolist() if not m.filename.endswith("/")]
                log.info("  ZIP contiene %d archivo(s).", len(miembros))

                for info in miembros:
                    nombre = Path(info.filename).name
                    if not nombre:
                        continue

                    destino = carpeta / nombre
                    # Evitar sobreescribir
                    contador = 1
                    ext = Path(nombre).suffix
                    while destino.exists():
                        destino = carpeta / f"{Path(nombre).stem}_v{contador}{ext}"
                        contador += 1

                    datos = zf.read(info.filename)
                    destino.write_bytes(datos)
                    log.info("  Guardado: %s  (%.2f MB)",
                             destino.name, len(datos) / 1_048_576)

            archivo.unlink()

        except zipfile.BadZipFile:
            log.error("  ZIP corrupto: %s — revisa manualmente en %s", archivo.name, TEMP_DIR)

    # ── Archivo directo (txt / csv / xlsx) ───────────────────────
    else:
        destino = carpeta / archivo.name
        archivo.replace(destino)
        log.info("  Guardado directo: %s", destino.name)


# ─────────────────────────────────────────────────────────────────
# FLUJO PRINCIPAL
# ─────────────────────────────────────────────────────────────────
def main() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    log.info("Iniciando Chrome…")
    driver = crear_driver()

    try:
        log.info("Abriendo portal SEPS para establecer sesión…")
        driver.get(URL_PORTAL)
        time.sleep(4)

        total = len(BASES_DE_DATOS)
        for i, item in enumerate(BASES_DE_DATOS, 1):
            año = item["año"]
            url = item["url"]

            log.info("=" * 55)
            log.info("[%d/%d]  Año: %s", i, total, año)

            try:
                driver.get(url)
                archivo = esperar_archivo()

                if archivo:
                    guardar(archivo, año)
                else:
                    log.warning("  Sin descarga para año %s. Revisa el ID.", año)

            except Exception as e:
                log.error("  Error en año %s: %s", año, e)

            time.sleep(3)

        # ── Resumen final ─────────────────────────────────────────
        log.info("=" * 55)
        log.info("DESCARGA COMPLETADA")
        log.info("Ubicación: %s", BASE_DIR)
        log.info("-" * 55)

        datos_dir = BASE_DIR / "Base de datos"
        for carpeta in sorted(datos_dir.iterdir()):
            if carpeta.is_dir() and not carpeta.name.startswith("_"):
                archivos = list(carpeta.iterdir())
                log.info("  %s/  →  %d archivo(s)", carpeta.name, len(archivos))
                for f in sorted(archivos):
                    log.info("      %-45s  %.2f MB",
                             f.name, f.stat().st_size / 1_048_576)

    finally:
        driver.quit()
        # Limpiar temporal si quedó vacía
        try:
            if TEMP_DIR.exists() and not any(TEMP_DIR.iterdir()):
                TEMP_DIR.rmdir()
        except Exception:
            pass


if __name__ == "__main__":
    main()
