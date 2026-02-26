"""
Scraper - Directorio PlataformaPYME
https://www.plataformapyme.org/directorio-empresas
"""

import asyncio
import csv
import re
from datetime import datetime
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

URL = "https://www.plataformapyme.org/directorio-empresas"
OUTPUT = "leads_plataformapyme.csv"
MAX_PAGINAS = 500  # tope de seguridad

def limpiar(t):
    return " ".join(t.split()).strip() if t else ""

def parsear_detalle(texto):
    def campo(label):
        m = re.search(rf"{label}:\s*(.+?)(?=Domicilio:|Localidad:|Provincia:|Teléfono:|Sitio Web:|Email:|Condicion Fiscal:|CUIT:|Categoria:|---|$)", texto, re.DOTALL)
        return limpiar(m.group(1)) if m else ""
    return {
        "domicilio": campo("Domicilio"),
        "provincia": campo("Provincia"),
        "telefono":  campo("Teléfono"),
        "sitio_web": campo("Sitio Web"),
        "email":     campo("Email"),
        "categoria": campo("Categoria"),
    }

def parsear_tabla(html):
    soup = BeautifulSoup(html, "html.parser")
    tabla = soup.find("table")
    if not tabla:
        return []
    leads = []
    for fila in tabla.find_all("tr")[1:]:
        celdas = fila.find_all("td")
        if len(celdas) < 5:
            continue
        detalle  = limpiar(celdas[0].get_text(separator="\n"))
        campos   = parsear_detalle(detalle)
        leads.append({
            "razon_social": limpiar(celdas[1].get_text()),
            "cuit":         limpiar(celdas[2].get_text()),
            "categoria":    limpiar(celdas[3].get_text()) or campos["categoria"],
            "localidad":    limpiar(celdas[4].get_text()),
            "provincia":    campos["provincia"],
            "domicilio":    campos["domicilio"],
            "telefono":     campos["telefono"],
            "sitio_web":    campos["sitio_web"],
            "email":        campos["email"],
        })
    return leads

async def scrape():
    leads = []
    vistos = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        page = await browser.new_page()
        print("📥 Cargando directorio...", flush=True)
        await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_selector("table", timeout=15000)
        await asyncio.sleep(3)

        # Intentar seleccionar "All" para cargar todo junto
        try:
            select = page.locator("select[name*='length']")
            await select.select_option("-1")
            await asyncio.sleep(5)
            print("✅ Modo 'All' activado", flush=True)
            html = await page.content()
            leads = parsear_tabla(html)
            print(f"✅ {len(leads)} empresas cargadas de una vez", flush=True)
        except Exception:
            print("⚠️  Paginando de a una...", flush=True)

            for pagina in range(1, MAX_PAGINAS + 1):
                print(f"   📄 Página {pagina}...", flush=True)

                html = await page.content()
                nuevos = parsear_tabla(html)

                # Filtrar duplicados por razon_social
                nuevos_unicos = [l for l in nuevos if l["razon_social"] not in vistos]
                for l in nuevos_unicos:
                    vistos.add(l["razon_social"])
                leads.extend(nuevos_unicos)

                print(f"      → {len(nuevos_unicos)} nuevas (total: {len(leads)})", flush=True)

                # Guardar parcial cada 10 páginas
                if pagina % 1 == 0:  # Guardar cada página
                    guardar_csv(leads)
                    print(f"   💾 Guardado parcial: {len(leads)} leads", flush=True)

                # Detectar botón siguiente
                try:
                    btn = page.locator(".paginate_button.next, a.next, [id$='_next']").first
                    clases = await btn.get_attribute("class") or ""
                    if "disabled" in clases:
                        print("✅ Última página alcanzada", flush=True)
                        break
                    await btn.click()
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"✅ Fin de paginación: {e}", flush=True)
                    break

        await browser.close()
    return leads

def guardar_csv(leads):
    if not leads:
        return
    campos = ["razon_social","cuit","categoria","localidad","provincia","domicilio","telefono","sitio_web","email"]
    with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(leads)

async def main():
    print("=" * 55, flush=True)
    print("🏭 SCRAPER PLATAFORMA PYME", flush=True)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("=" * 55, flush=True)

    leads = await scrape()
    guardar_csv(leads)

    print(f"\n✅ CSV guardado: {OUTPUT}", flush=True)
    print(f"📊 Total: {len(leads)} empresas", flush=True)
    print(f"📧 Con email:    {sum(1 for l in leads if l['email'])}", flush=True)
    print(f"📞 Con teléfono: {sum(1 for l in leads if l['telefono'])}", flush=True)
    print(f"🌐 Con web:      {sum(1 for l in leads if l['sitio_web'])}", flush=True)

asyncio.run(main())
