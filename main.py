"""
🗺️ Google Maps Scraper - Fabricantes Textil Argentina 1
Versión Railway con Selenium + Chromium del sistema
"""

import csv
import re
import random
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────

BUSQUEDAS = [
    "fábrica textil Argentina",
    "fabricante indumentaria Argentina",
    "fábrica ropa Argentina",
    "industria textil Buenos Aires",
    "fabricante textil Córdoba Argentina",
    "fábrica ropa exportación Argentina",
    "confección indumentaria Argentina",
    "fábrica tejidos Argentina",
    "fabricante telas Argentina",
    "industria indumentaria Rosario Argentina",
]

OUTPUT_FILE = "leads_textil_argentina.csv"
MAX_RESULTADOS_POR_BUSQUEDA = 20
DELAY_MIN = 2.5
DELAY_MAX = 5.0

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def extraer_email(texto):
    if not texto:
        return ""
    match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", texto)
    return match.group(0) if match else ""

def limpiar(texto):
    return texto.strip().replace("\n", " ").replace(",", " ") if texto else ""

def esperar():
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

def get_text(driver, selector, by=By.CSS_SELECTOR, timeout=5):
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
        return el.text
    except Exception:
        return ""

def get_attr(driver, selector, attr, by=By.CSS_SELECTOR, timeout=5):
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
        return el.get_attribute(attr)
    except Exception:
        return ""

# ─── DRIVER ───────────────────────────────────────────────────────────────────

def crear_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--lang=es-AR")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Usar chromium del sistema
    import shutil
    chromium = shutil.which("chromium") or shutil.which("chromium-browser") or "/usr/bin/chromium"
    chromedriver = shutil.which("chromedriver") or "/usr/bin/chromedriver"

    print(f"   🔧 Chromium: {chromium}", flush=True)
    print(f"   🔧 ChromeDriver: {chromedriver}", flush=True)

    options.binary_location = chromium
    service = Service(executable_path=chromedriver)
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

# ─── SCRAPER ──────────────────────────────────────────────────────────────────

def scrape_google_maps():
    leads = []
    vistos = set()
    driver = crear_driver()

    try:
        for busqueda in BUSQUEDAS:
            print(f"\n🔍 Buscando: '{busqueda}'", flush=True)
            url = f"https://www.google.com/maps/search/{busqueda.replace(' ', '+')}"

            try:
                driver.get(url)
                time.sleep(random.uniform(3, 5))

                # Scrollear el panel de resultados
                for _ in range(6):
                    try:
                        panel = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
                        driver.execute_script("arguments[0].scrollBy(0, 1500)", panel)
                        time.sleep(random.uniform(1.5, 2.5))
                    except Exception:
                        break

                # Obtener links de resultados
                links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
                hrefs = list(dict.fromkeys([l.get_attribute("href") for l in links if l.get_attribute("href")]))
                print(f"   → {len(hrefs)} resultados encontrados", flush=True)

                count = 0
                for href in hrefs[:MAX_RESULTADOS_POR_BUSQUEDA]:
                    if count >= MAX_RESULTADOS_POR_BUSQUEDA:
                        break
                    try:
                        driver.get(href)
                        time.sleep(random.uniform(2, 3.5))

                        # Nombre
                        nombre = get_text(driver, 'h1.DUwDvf')
                        if not nombre or nombre in vistos:
                            continue
                        vistos.add(nombre)

                        # Dirección
                        direccion = get_text(driver, '[data-item-id="address"] .Io6YTe')

                        # Teléfono
                        telefono = ""
                        try:
                            tel_el = driver.find_element(By.CSS_SELECTOR, '[data-item-id*="phone"] .Io6YTe')
                            telefono = tel_el.text
                        except Exception:
                            pass

                        # Sitio Web
                        sitio_web = get_attr(driver, '[data-item-id*="authority"] a', "href")

                        # Email
                        email = ""
                        try:
                            desc = get_text(driver, '.PYvSYb', timeout=2)
                            email = extraer_email(desc)
                        except Exception:
                            pass

                        lead = {
                            "nombre": limpiar(nombre),
                            "telefono": limpiar(telefono),
                            "sitio_web": limpiar(sitio_web),
                            "direccion": limpiar(direccion),
                            "email": limpiar(email),
                            "busqueda_origen": busqueda,
                            "fecha_extraccion": datetime.now().strftime("%Y-%m-%d"),
                        }

                        leads.append(lead)
                        count += 1
                        print(f"   ✅ [{count}] {nombre} | {telefono} | {sitio_web}", flush=True)

                        # Guardar progreso cada 10 leads
                        if len(leads) % 10 == 0:
                            guardar_csv(leads, OUTPUT_FILE)
                            print(f"   💾 Guardado parcial: {len(leads)} leads", flush=True)

                        time.sleep(random.uniform(1.5, 3))

                    except Exception as e:
                        print(f"   ⚠️  Error en resultado: {e}", flush=True)
                        continue

            except Exception as e:
                print(f"   ❌ Error en búsqueda '{busqueda}': {e}", flush=True)
                continue

    finally:
        driver.quit()

    return leads

# ─── CSV ──────────────────────────────────────────────────────────────────────

def guardar_csv(leads, archivo):
    if not leads:
        return
    campos = ["nombre", "telefono", "sitio_web", "direccion", "email", "busqueda_origen", "fecha_extraccion"]
    with open(archivo, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(leads)

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55, flush=True)
    print("🧵 SCRAPER TEXTIL ARGENTINA - Google Maps", flush=True)
    print(f"📅 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("=" * 55, flush=True)

    leads = scrape_google_maps()
    guardar_csv(leads, OUTPUT_FILE)

    print(f"\n✅ CSV guardado: {OUTPUT_FILE}", flush=True)
    print(f"📊 Total leads únicos: {len(leads)}", flush=True)
    print("🏁 Scraping finalizado.", flush=True)

if __name__ == "__main__":
    main()
