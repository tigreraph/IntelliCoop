"""
Descarga automatizada - Estados Financieros Mensuales SEPS
Cooperativas segmentos 1, 2, 3 y mutualistas

Uso:
    py descarga_seps.py

Requisitos:
    py -m pip install selenium webdriver-manager
"""

import time
import shutil
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
BASE_DIR  = Path(r"C:\Users\kevin\OneDrive\Desktop\Base Cooperativas segmentos")
TEMP_DIR  = BASE_DIR / "_temporal"
URL_BASE  = "https://estadisticas.seps.gob.ec/index.php/estadisticas-sfps/"

# Estados Financieros Mensuales — un ZIP por año
# Fuente: sección "Situación Financiera > Estados Financieros Mensuales"
ARCHIVOS_MENSUALES = [
    {"año": "2026", "url": "https://estadisticas.seps.gob.ec/?sdm_process_download=1&download_id=3255"},
    {"año": "2025", "url": "https://estadisticas.seps.gob.ec/?sdm_process_download=1&download_id=2776"},
    {"año": "2024", "url": "https://estadisticas.seps.gob.ec/?smd_process_download=1&download_id=2333"},
    {"año": "2023", "url": "https://estadisticas.seps.gob.ec/?smd_process_download=1&download_id=1813"},
    {"año": "2022", "url": "https://estadisticas.seps.gob.ec/?smd_process_download=1&download_id=1655"},
    {"año": "2021", "url": "https://estadisticas.seps.gob.ec/?smd_process_download=1&download_id=792"},
    {"año": "2020", "url": "https://estadisticas.seps.gob.ec/?smd_process_download=1&download_id=860"},
    {"año": "Anteriores", "url": "https://estadisticas.seps.gob.ec/?smd_process_download=1&download_id=878"},
]

TIMEOUT_DESCARGA = 180  # segundos máximos por archivo

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
    # Para correr sin ventana descomenta la línea de abajo:
    # opts.add_argument("--headless=new")

    servicio = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=servicio, options=opts)
    return driver


# ─────────────────────────────────────────────────────────────────
# ESPERAR DESCARGA
# ─────────────────────────────────────────────────────────────────
def esperar_archivo(timeout: int = TIMEOUT_DESCARGA) -> Path | None:
    """Espera a que aparezca un archivo nuevo (no .crdownload) en TEMP_DIR."""
    archivos_antes = set(TEMP_DIR.iterdir())
    inicio = time.time()

    while time.time() - inicio < timeout:
        en_progreso = list(TEMP_DIR.glob("*.crdownload"))
        actuales    = set(TEMP_DIR.iterdir())
        nuevos      = actuales - archivos_antes

        nuevos_listos = [f for f in nuevos if f.suffix.lower() != ".crdownload"]
        if nuevos_listos and not en_progreso:
            archivo = sorted(nuevos_listos, key=lambda p: p.stat().st_mtime)[-1]
            log.info("  Descarga completa: %s (%.1f MB)",
                     archivo.name, archivo.stat().st_size / 1_048_576)
            return archivo

        time.sleep(2)

    log.error("  Tiempo agotado esperando la descarga.")
    return None


# ─────────────────────────────────────────────────────────────────
# DESCOMPRIMIR Y ORGANIZAR
# ─────────────────────────────────────────────────────────────────
EXTENSIONES_DATOS = {".csv", ".xlsx", ".xls", ".txt"}


def procesar_descarga(archivo: Path, año: str) -> None:
    """
    El ZIP anual contiene UN archivo por mes (12 en total).
    Los extrae todos a BASE_DIR/año/ conservando el nombre original.
    Usa zf.read() para evitar problemas con subcarpetas internas del ZIP.
    """
    carpeta_destino = BASE_DIR / año
    carpeta_destino.mkdir(parents=True, exist_ok=True)

    sufijo = archivo.suffix.lower()

    # ── ZIP con archivos mensuales dentro ────────────────────────
    if sufijo == ".zip":
        log.info("  Abriendo ZIP del año %s…", año)
        try:
            with zipfile.ZipFile(archivo, "r") as zf:
                # Filtrar solo archivos reales (excluir entradas de directorio)
                miembros = [m for m in zf.infolist() if not m.filename.endswith("/")]

                log.info("  Archivos dentro del ZIP: %d", len(miembros))
                for info in miembros:
                    ext = Path(info.filename).suffix.lower()
                    nombre_solo = Path(info.filename).name  # descarta subcarpetas internas

                    if not nombre_solo:
                        continue

                    # Si no tiene extensión de datos conocida, igual lo guardamos
                    destino = carpeta_destino / nombre_solo

                    # Evitar sobreescribir si ya existe
                    contador = 1
                    while destino.exists():
                        destino = carpeta_destino / f"{Path(nombre_solo).stem}_v{contador}{ext}"
                        contador += 1

                    # Leer bytes directamente (evita problemas con rutas internas del ZIP)
                    datos = zf.read(info.filename)
                    destino.write_bytes(datos)
                    log.info("  [%s] Guardado: %s  (%.2f MB)",
                             año, destino.name, len(datos) / 1_048_576)

            archivo.unlink()
            log.info("  ZIP eliminado.")

        except zipfile.BadZipFile:
            log.error("  ZIP corrupto. Se conserva en: %s", archivo)

    # ── Archivo único (CSV / Excel / TXT) ────────────────────────
    elif sufijo in EXTENSIONES_DATOS:
        destino = carpeta_destino / archivo.name
        shutil.move(str(archivo), str(destino))
        log.info("  Guardado directo: %s", destino.name)

    else:
        # Formato desconocido — mover sin procesar para revisión manual
        destino = carpeta_destino / archivo.name
        shutil.move(str(archivo), str(destino))
        log.warning("  Formato no reconocido '%s', guardado sin procesar: %s",
                    sufijo, destino.name)


# ─────────────────────────────────────────────────────────────────
# FLUJO PRINCIPAL
# ─────────────────────────────────────────────────────────────────
def main() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    log.info("Iniciando Chrome…")
    driver = crear_driver()

    try:
        # Visitar la página principal para establecer la sesión/cookies
        log.info("Estableciendo sesión en el portal SEPS…")
        driver.get(URL_BASE)
        time.sleep(4)

        total = len(ARCHIVOS_MENSUALES)
        for i, item in enumerate(ARCHIVOS_MENSUALES, 1):
            año = item["año"]
            url = item["url"]

            log.info("=" * 55)
            log.info("[%d/%d] Descargando año %s…", i, total, año)

            try:
                driver.get(url)
                archivo = esperar_archivo()

                if archivo:
                    procesar_descarga(archivo, año)
                else:
                    log.warning("  No se obtuvo archivo para el año %s.", año)

            except Exception as e:
                log.error("  Error en año %s: %s", año, e)

            # Pequeña pausa entre descargas para no saturar el servidor
            time.sleep(3)

        log.info("=" * 55)
        log.info("PROCESO COMPLETADO")
        log.info("Archivos organizados en: %s", BASE_DIR)

        # Mostrar resumen de lo descargado
        log.info("-" * 55)
        for carpeta in sorted(BASE_DIR.iterdir()):
            if carpeta.is_dir() and carpeta.name != "_temporal":
                archivos = list(carpeta.iterdir())
                log.info("  %s/  →  %d archivo(s)", carpeta.name, len(archivos))
                for f in archivos:
                    log.info("      %s  (%.2f MB)", f.name, f.stat().st_size / 1_048_576)

    finally:
        driver.quit()
        # Limpiar carpeta temporal si quedó vacía
        try:
            residuos = list(TEMP_DIR.iterdir())
            if not residuos:
                TEMP_DIR.rmdir()
            else:
                log.warning(
                    "La carpeta temporal tiene %d archivo(s) sin procesar: %s",
                    len(residuos), [f.name for f in residuos]
                )
        except Exception:
            pass


if __name__ == "__main__":
    main()
