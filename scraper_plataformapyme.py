"""
Scraper - Directorio PlataformaPYME
https://www.plataformapyme.org/directorio-empresas
Usa Playwright para manejar la paginación JavaScript (DataTables)
"""

import asyncio
import csv
import re
from datetime import datetime
from playwright.async_api import async_playwright

URL = "https://www.plataformapyme.org/directorio-empresas"
OUTPUT = "leads_plataformapyme.csv"

def limpiar(t):
    return " ".join(t.split()).strip() if t else ""

def parsear_detalle(texto):
    def campo(label):
        m = re.search(rf"{label}:\s*(.+?)(?=Domicilio:|Localidad:|Provincia:|Teléfono:|Sitio Web:|Email:|Condicion Fiscal:|CUIT:|Categoria:|---|$)", texto, re.DOTALL)
        return limpiar(m.group(1)) if m else ""
    return {
        "domicilio":   campo("Domicilio"),
        "provincia":   campo("Provincia"),
        "telefono":    campo("Teléfono"),
        "sitio_web":   campo("Sitio Web"),
        "email":       campo("Email"),
        "categoria":   campo("Categoria"),
    }

def parsear_filas(filas_html):
    leads = []
    for fila in filas_html:
        celdas = fila.find_all("td") if hasattr(fila, 'find_all') else []
        if len(celdas) < 5:
            continue
        detalle  = limpiar(celdas[0].get_text(separator="\n"))
        razon    = limpiar(celdas[1].get_text())
        cuit     = limpiar(celdas[2].get_text())
        categoria= limpiar(celdas[3].get_text())
        localidad= limpiar(celdas[4].get_text())
        campos   = parsear_detalle(detalle)
        leads.append({
            "razon_social": razon,
            "cuit":         cuit,
            "categoria":    categoria or campos["categoria"],
            "localidad":    localidad,
            "provincia":    campos["provincia"],
            "domicilio":    campos["domicilio"],
            "telefono":     campos["telefono"],
            "sitio_web":    campos["sitio_web"],
            "email":        campos["email"],
        })
    return leads

async def scrape():
    from bs4 import BeautifulSoup
    leads = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        page = await browser.new_page()
        print("📥 Cargando directorio...", flush=True)
        await page.goto(URL, wait_until="networkidle", timeout=60000)

        # Esperar a que cargue la tabla DataTables
        await page.wait_for_selector("table", timeout=15000)

        # Intentar mostrar todos los registros de una (opción "All" en DataTables)
        try:
            await page.select_option("select[name*='length']", "-1")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            print("✅ Cargando todos los registros a la vez...", flush=True)
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            tabla = soup.find("table")
            filas = tabla.find_all("tr")[1:]
            leads = parsear_filas(filas)
            print(f"✅ {len(leads)} empresas encontradas", flush=True)
        except Exception as e:
            print(f"⚠️  No se pudo cargar todo junto, paginando... ({e})", flush=True)

            # Paginar página por página
            pagina = 1
            while True:
                print(f"   📄 Página {pagina}...", flush=True)
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                tabla = soup.find("table")
                if not tabla:
                    break
                filas = tabla.find_all("tr")[1:]
                nuevos = parsear_filas(filas)
                leads.extend(nuevos)
                print(f"   → {len(nuevos)} empresas (total: {len(leads)})", flush=True)

                # Buscar botón "Siguiente"
                try:
                    btn_next = page.locator("a.next, button.next, [id*='next'], .paginate_button.next")
                    classes = await btn_next.get_attribute("class") or ""
                    if "disabled" in classes:
                        print("✅ Última página alcanzada", flush=True)
                        break
                    await btn_next.click()
                    await page.wait_for_load_state("networkidle")
                    await asyncio.sleep(1.5)
                    pagina += 1
                except Exception:
                    print("✅ No hay más páginas", flush=True)
                    break

        await browser.close()
    return leads

def guardar_csv(leads):
    campos = ["razon_social","cuit","categoria","localidad","provincia","domicilio","telefono","sitio_web","email"]
    with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(leads)
    print(f"\n✅ CSV guardado: {OUTPUT}", flush=True)
    print(f"📊 Total: {len(leads)} empresas", flush=True)
    print(f"📧 Con email:    {sum(1 for l in leads if l['email'])}", flush=True)
    print(f"📞 Con teléfono: {sum(1 for l in leads if l['telefono'])}", flush=True)
    print(f"🌐 Con web:      {sum(1 for l in leads if l['sitio_web'])}", flush=True)

async def main():
    print("=" * 55, flush=True)
    print("🏭 SCRAPER PLATAFORMA PYME", flush=True)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("=" * 55, flush=True)
    leads = await scrape()
    if leads:
        guardar_csv(leads)

asyncio.run(main())
