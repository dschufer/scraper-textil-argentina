"""
🗺️ Google Maps Scraper - Fabricantes Textil Argentina
Versión Railway (headless, sin GUI)
Output: leads_textil_argentina.csv
"""

import asyncio
import csv
import re
import random
import time
import os
from datetime import datetime
from playwright.async_api import async_playwright

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

def extraer_email(texto: str) -> str:
    if not texto:
        return ""
    match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", texto)
    return match.group(0) if match else ""

def limpiar(texto: str) -> str:
    return texto.strip().replace("\n", " ").replace(",", " ") if texto else ""

# ─── SCRAPER ──────────────────────────────────────────────────────────────────

async def scrape_google_maps():
    leads = []
    vistos = set()

    async with async_playwright() as p:
        # Usar chromium del sistema si el de playwright no existe
        import shutil
        chromium_path = shutil.which("chromium") or shutil.which("chromium-browser")
        launch_kwargs = dict(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--lang=es-AR",
                "--single-process",
            ]
        )
        if chromium_path:
            launch_kwargs["executable_path"] = chromium_path
        browser = await p.chromium.launch(**launch_kwargs)
        context = await browser.new_context(
            locale="es-AR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        for busqueda in BUSQUEDAS:
            print(f"\n🔍 Buscando: '{busqueda}'", flush=True)
            url = f"https://www.google.com/maps/search/{busqueda.replace(' ', '+')}"

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(random.uniform(2, 4))

                # Scrollear resultados
                for _ in range(5):
                    try:
                        await page.evaluate("""
                            const panel = document.querySelector('div[role="feed"]');
                            if (panel) panel.scrollBy(0, 1500);
                        """)
                        await asyncio.sleep(random.uniform(1.5, 2.5))
                    except Exception:
                        break

                resultados = await page.locator('a[href*="/maps/place/"]').all()
                print(f"   → {len(resultados)} resultados encontrados", flush=True)

                count = 0
                for resultado in resultados[:MAX_RESULTADOS_POR_BUSQUEDA]:
                    if count >= MAX_RESULTADOS_POR_BUSQUEDA:
                        break
                    try:
                        await resultado.click()
                        await asyncio.sleep(random.uniform(2, 3.5))

                        # Nombre
                        nombre = ""
                        try:
                            nombre = await page.locator('h1.DUwDvf').inner_text(timeout=5000)
                        except Exception:
                            pass

                        if not nombre or nombre in vistos:
                            await page.go_back()
                            await asyncio.sleep(1.5)
                            continue

                        vistos.add(nombre)

                        # Dirección
                        direccion = ""
                        try:
                            direccion = await page.locator('[data-item-id="address"] .Io6YTe').inner_text(timeout=3000)
                        except Exception:
                            pass

                        # Teléfono
                        telefono = ""
                        try:
                            telefono = await page.locator('[data-item-id*="phone"] .Io6YTe').inner_text(timeout=3000)
                        except Exception:
                            pass

                        # Sitio Web
                        sitio_web = ""
                        try:
                            sitio_web = await page.locator('[data-item-id*="authority"] a').get_attribute("href", timeout=3000)
                        except Exception:
                            pass

                        # Email
                        email = ""
                        try:
                            descripcion = await page.locator('.PYvSYb').inner_text(timeout=2000)
                            email = extraer_email(descripcion)
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

                        await page.go_back()
                        await asyncio.sleep(random.uniform(1.5, 3))

                    except Exception as e:
                        print(f"   ⚠️  Error: {e}", flush=True)
                        try:
                            await page.go_back()
                            await asyncio.sleep(1.5)
                        except Exception:
                            pass
                        continue

            except Exception as e:
                print(f"   ❌ Error en búsqueda: {e}", flush=True)
                continue

        await browser.close()

    return leads


def guardar_csv(leads: list, archivo: str):
    if not leads:
        return
    campos = ["nombre", "telefono", "sitio_web", "direccion", "email", "busqueda_origen", "fecha_extraccion"]
    with open(archivo, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(leads)


async def main():
    print("=" * 55, flush=True)
    print("🧵 SCRAPER TEXTIL ARGENTINA - Google Maps", flush=True)
    print(f"📅 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("=" * 55, flush=True)

    leads = await scrape_google_maps()
    guardar_csv(leads, OUTPUT_FILE)

    print(f"\n✅ CSV guardado: {OUTPUT_FILE}", flush=True)
    print(f"📊 Total leads únicos: {len(leads)}", flush=True)
    print("🏁 Scraping finalizado.", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
