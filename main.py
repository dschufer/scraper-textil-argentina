"""
🗺️ Google Maps Scraper - Fabricantes Textil Argentina
Versión GitHub Actions - con extracción de emails desde sitios web
"""

import asyncio
import csv
import re
import random
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

# Páginas donde suelen estar los emails
PAGINAS_CONTACTO = [
    "",           # homepage
    "/contacto",
    "/contact",
    "/contactanos",
    "/about",
    "/nosotros",
    "/quienes-somos",
]

def extraer_emails(texto):
    if not texto: return []
    return list(set(re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", texto)))

def limpiar(t):
    return t.strip().replace("\n", " ").replace(",", " ") if t else ""

def limpiar_url(url):
    """Quedarse solo con el dominio base"""
    if not url: return ""
    match = re.match(r"(https?://[^/]+)", url)
    return match.group(1) if match else url

async def buscar_email_en_web(page, sitio_web):
    """Visita el sitio web y páginas de contacto para encontrar emails"""
    if not sitio_web:
        return ""
    
    base = limpiar_url(sitio_web)
    emails_encontrados = []

    for path in PAGINAS_CONTACTO:
        url = base + path
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(random.uniform(1, 2))
            contenido = await page.content()
            emails = extraer_emails(contenido)
            # Filtrar emails genéricos/spam
            emails = [e for e in emails if not any(x in e.lower() for x in 
                      ["noreply", "no-reply", "example", "test", "spam", "sentry", "wix", "wordpress"])]
            if emails:
                emails_encontrados.extend(emails)
                break  # Con uno alcanza, no seguimos buscando
        except Exception:
            continue

    if emails_encontrados:
        return emails_encontrados[0]
    return ""

async def scrape():
    leads = []
    vistos = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--lang=es-AR"]
        )

        # Dos contextos: uno para Maps, otro para los sitios web
        maps_page = await browser.new_page()
        web_page = await browser.new_page()

        await maps_page.set_extra_http_headers({"Accept-Language": "es-AR,es,en-US;q=0.9"})
        await maps_page.set_viewport_size({"width": 1280, "height": 900})

        for busqueda in BUSQUEDAS:
            print(f"\n🔍 {busqueda}", flush=True)
            url = "https://www.google.com/maps/search/" + busqueda.replace(" ", "+")
            try:
                await maps_page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(random.uniform(4, 6))

                for _ in range(6):
                    try:
                        await maps_page.evaluate('document.querySelector(\'div[role="feed"]\').scrollBy(0,1500)')
                        await asyncio.sleep(random.uniform(1.5, 2.5))
                    except:
                        break

                resultados = await maps_page.locator('a[href*="/maps/place/"]').all()
                print(f"   → {len(resultados)} resultados", flush=True)

                count = 0
                for r in resultados[:MAX_POR_BUSQUEDA]:
                    try:
                        await r.click()
                        await asyncio.sleep(random.uniform(2, 3.5))

                        nombre = ""
                        try: nombre = await maps_page.locator("h1.DUwDvf").inner_text(timeout=5000)
                        except: pass

                        if not nombre or nombre in vistos:
                            await maps_page.go_back()
                            await asyncio.sleep(1.5)
                            continue
                        vistos.add(nombre)

                        direccion = ""
                        try: direccion = await maps_page.locator('[data-item-id="address"] .Io6YTe').inner_text(timeout=3000)
                        except: pass

                        telefono = ""
                        try: telefono = await maps_page.locator('[data-item-id*="phone"] .Io6YTe').inner_text(timeout=3000)
                        except: pass

                        sitio_web = ""
                        try: sitio_web = await maps_page.locator('[data-item-id*="authority"] a').get_attribute("href", timeout=3000)
                        except: pass

                        # Buscar email en el sitio web
                        email = ""
                        if sitio_web:
                            print(f"   📧 Buscando email en {sitio_web}...", flush=True)
                            try:
                                email = await buscar_email_en_web(web_page, sitio_web)
                            except Exception:
                                pass

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
                        estado_email = f"📧 {email}" if email else "❌ sin email"
                        print(f"   ✅ [{count}] {nombre} | {telefono} | {estado_email}", flush=True)

                        await maps_page.go_back()
                        await asyncio.sleep(random.uniform(1.5, 3))

                    except Exception as e:
                        try: await maps_page.go_back(); await asyncio.sleep(1.5)
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
    con_email = sum(1 for l in leads if l["email"])
    print(f"📧 {con_email} leads con email ({round(con_email/len(leads)*100 if leads else 0)}%)", flush=True)

asyncio.run(main())
