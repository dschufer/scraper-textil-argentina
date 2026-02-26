"""
Scraper - Directorio PlataformaPYME
Todos los datos están en el HTML — no hay paginación real del servidor.
DataTables solo muestra de a 30 pero el HTML tiene todo.
No necesita navegador, solo requests + BeautifulSoup.
"""

import requests
from bs4 import BeautifulSoup
import csv
import re
from datetime import datetime

URL = "https://www.plataformapyme.org/directorio-empresas"
OUTPUT = "leads_plataformapyme.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

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

def guardar_csv(leads):
    campos = ["razon_social","cuit","categoria","localidad","provincia","domicilio","telefono","sitio_web","email"]
    with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(leads)
    print(f"💾 Guardado: {len(leads)} empresas → {OUTPUT}", flush=True)

def scrape():
    print("📥 Descargando HTML completo...", flush=True)
    r = requests.get(URL, headers=HEADERS, timeout=60)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    tabla = soup.find("table")
    if not tabla:
        print("❌ No se encontró la tabla")
        return []

    filas = tabla.find_all("tr")[1:]
    print(f"✅ {len(filas)} filas encontradas en el HTML", flush=True)

    leads = []
    for i, fila in enumerate(filas):
        celdas = fila.find_all("td")
        if len(celdas) < 5:
            continue

        detalle  = limpiar(celdas[0].get_text(separator="\n"))
        campos   = parsear_detalle(detalle)

        lead = {
            "razon_social": limpiar(celdas[1].get_text()),
            "cuit":         limpiar(celdas[2].get_text()),
            "categoria":    limpiar(celdas[3].get_text()) or campos["categoria"],
            "localidad":    limpiar(celdas[4].get_text()),
            "provincia":    campos["provincia"],
            "domicilio":    campos["domicilio"],
            "telefono":     campos["telefono"],
            "sitio_web":    campos["sitio_web"],
            "email":        campos["email"],
        }
        leads.append(lead)

        # Mostrar progreso y guardar cada 100
        if (i + 1) % 100 == 0:
            print(f"   → {i+1} procesadas...", flush=True)
            guardar_csv(leads)

    return leads

def main():
    print("=" * 55, flush=True)
    print("🏭 SCRAPER PLATAFORMA PYME", flush=True)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("=" * 55, flush=True)

    leads = scrape()
    guardar_csv(leads)

    print(f"\n{'='*55}", flush=True)
    print(f"📊 TOTAL: {len(leads)} empresas", flush=True)
    print(f"📧 Con email:    {sum(1 for l in leads if l['email'])}", flush=True)
    print(f"📞 Con teléfono: {sum(1 for l in leads if l['telefono'])}", flush=True)
    print(f"🌐 Con web:      {sum(1 for l in leads if l['sitio_web'])}", flush=True)

main()
