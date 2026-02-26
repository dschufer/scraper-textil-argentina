"""
🗺️ Google Maps Scraper - Fabricantes Textil Argentina
Versión GitHub Actions (Playwright headless)
"""

import asyncio
import csv
import re
import random
import time
from datetime import datetime
from playwright.async_api import async_playwright

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
MAX_POR_BUSQUEDA = 20

def extraer_email(texto):
    if not texto: return ""
    m = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", texto)
    return m.group(0) if m else ""

def limpiar(t):
    return t.strip().replace("\n", " ").replace(",", " ") if t else ""

async def scrape():
    leads = []
    vistos = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--lang=es-AR"]
        )
        page = await browser.new_page()
        await page.set_extra_http_headers({"Accept-Language": "es-AR,es"})

        for busqueda in BUSQUEDAS:
            print(f"\n🔍 {busqueda}", flush=True)
            url = "https://www.google.com/maps/search/" + busqueda.replace(" ", "+")
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(random.uniform(2, 4))

                for _ in range(6):
                    try:
                        await page.evaluate('document.querySelector(\'div[role="feed"]\').scrollBy(0,1500)')
                        await asyncio.sleep(random.uniform(1.5, 2.5))
                    except:
                        break

                resultados = await page.locator('a[href*="/maps/place/"]').all()
                print(f"   → {len(resultados)} resultados", flush=True)

                count = 0
                for r in resultados[:MAX_POR_BUSQUEDA]:
                    try:
                        await r.click()
                        await asyncio.sleep(random.uniform(2, 3.5))

                        nombre = ""
                        try: nombre = await page.locator("h1.DUwDvf").inner_text(timeout=5000)
                        except: pass

                        if not nombre or nombre in vistos:
                            await page.go_back()
                            await asyncio.sleep(1.5)
                            continue
                        vistos.add(nombre)

                        direccion = ""
                        try: direccion = await page.locator('[data-item-id="address"] .Io6YTe').inner_text(timeout=3000)
                        except: pass

                        telefono = ""
                        try: telefono = await page.locator('[data-item-id*="phone"] .Io6YTe').inner_text(timeout=3000)
                        except: pass

                        sitio_web = ""
                        try: sitio_web = await page.locator('[data-item-id*="authority"] a').get_attribute("href", timeout=3000)
                        except: pass

                        email = ""
                        try:
                            desc = await page.locator(".PYvSYb").inner_text(timeout=2000)
                            email = extraer_email(desc)
                        except: pass

                        leads.append({
                            "nombre": limpiar(nombre),
                            "telefono": limpiar(telefono),
                            "sitio_web": limpiar(sitio_web),
                            "direccion": limpiar(direccion),
                            "email": limpiar(email),
                            "busqueda_origen": busqueda,
                            "fecha": datetime.now().strftime("%Y-%m-%d"),
                        })
                        count += 1
                        print(f"   ✅ [{count}] {nombre} | {telefono}", flush=True)

                        await page.go_back()
                        await asyncio.sleep(random.uniform(1.5, 3))

                    except Exception as e:
                        try: await page.go_back(); await asyncio.sleep(1.5)
                        except: pass

            except Exception as e:
                print(f"   ❌ Error: {e}", flush=True)

        await browser.close()
    return leads

def guardar_csv(leads):
    campos = ["nombre", "telefono", "sitio_web", "direccion", "email", "busqueda_origen", "fecha"]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(leads)

async def main():
    print("=" * 55, flush=True)
    print("🧵 SCRAPER TEXTIL ARGENTINA", flush=True)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("=" * 55, flush=True)
    leads = await scrape()
    guardar_csv(leads)
    print(f"\n✅ {len(leads)} leads guardados en {OUTPUT_FILE}", flush=True)

asyncio.run(main())
