"""
Scraper - Catálogo Producción Bonaerense (GBA)
https://www.mp.gba.gov.ar/catalogoproduccionbonaerense/
Rubros: Alimentos, Indumentaria, Bebidas, etc.
Guarda CSV progresivamente.
"""

import requests
from bs4 import BeautifulSoup
import csv
import re
import time
import random
from datetime import datetime

BASE_URL = "https://www.mp.gba.gov.ar/catalogoproduccionbonaerense/rubros.php"
OUTPUT   = "leads_gba_productores.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Todos los rubros del sitio
RUBROS = {
    1:  "Alimentos",
    2:  "Artesanías",
    3:  "Artículos del hogar y electrodomésticos",
    4:  "Automotor",
    5:  "Bazar",
    6:  "Bebidas alcohólicas",
    7:  "Bebidas sin alcohol",
    8:  "Blanco y textil",
    9:  "Bolsas y empaques",
    10: "Calzado",
    11: "Construcción y ferretería",
    12: "Deportes",
    13: "Higiene y cuidado personal",
    14: "Indumentaria",
    15: "Juguetes",
    16: "Librería y papelería",
    17: "Limpieza",
    18: "Mascotas",
    19: "Muebles",
    20: "Plásticos",
    21: "Servicios",
}

def limpiar(t):
    return " ".join(t.split()).strip() if t else ""

def parsear_pagina(html, rubro_nombre):
    soup = BeautifulSoup(html, "html.parser")
    leads = []

    # Cada empresa es una card/div con h4
    empresas = soup.find_all("h4")
    for h4 in empresas:
        nombre = limpiar(h4.get_text())
        if not nombre:
            continue

        # Buscar el contenedor padre
        card = h4.find_parent()
        if not card:
            continue

        texto = card.get_text(separator="\n")

        # Producto/descripción — texto justo después del h4
        producto = ""
        for tag in h4.find_next_siblings():
            t = limpiar(tag.get_text())
            if t and "Mail:" not in t and "Tel.:" not in t and "Lugar:" not in t:
                producto = t
                break

        # Email
        email = ""
        mail_tag = card.find("a", href=lambda h: h and "mailto:" in h)
        if mail_tag:
            email = mail_tag.get_text().strip()

        # Teléfono
        telefono = ""
        m = re.search(r"Tel\.?:\s*([^\n]+)", texto)
        if m:
            telefono = limpiar(m.group(1))

        # Lugar/partido
        lugar = ""
        m = re.search(r"Lugar:\s*([^\n]+)", texto)
        if m:
            lugar = limpiar(m.group(1))

        leads.append({
            "nombre":   nombre,
            "producto": producto,
            "email":    email,
            "telefono": telefono,
            "lugar":    lugar,
            "rubro":    rubro_nombre,
        })

    return leads

def get_total_paginas(html):
    soup = BeautifulSoup(html, "html.parser")
    # Buscar el último número de página en la paginación
    paginas = []
    for a in soup.find_all("a"):
        href = a.get("href", "")
        m = re.search(r"pagina=(\d+)", href)
        if m:
            paginas.append(int(m.group(1)))
    # También buscar texto de número en links de paginación
    for tag in soup.find_all(["a", "span"]):
        t = tag.get_text().strip()
        if t.isdigit():
            paginas.append(int(t))
    return max(paginas) if paginas else 1

def guardar_csv(leads):
    if not leads:
        return
    campos = ["nombre","producto","email","telefono","lugar","rubro"]
    with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(leads)

def scrape():
    todos = []

    for rubro_id, rubro_nombre in RUBROS.items():
        print(f"\n📦 Rubro: {rubro_nombre} (ID {rubro_id})", flush=True)

        # Primera página para detectar cuántas hay
        try:
            r = requests.get(BASE_URL, params={"rubroActivo": rubro_id}, headers=HEADERS, timeout=30)
            r.raise_for_status()
        except Exception as e:
            print(f"   ❌ Error: {e}", flush=True)
            continue

        total_pags = get_total_paginas(r.text)
        print(f"   → {total_pags} páginas detectadas", flush=True)

        leads_rubro = []

        for pag in range(1, total_pags + 1):
            try:
                if pag == 1:
                    html = r.text
                else:
                    resp = requests.get(
                        BASE_URL,
                        params={"rubroActivo": rubro_id, "pagina": pag},
                        headers=HEADERS,
                        timeout=30
                    )
                    resp.raise_for_status()
                    html = resp.text

                nuevos = parsear_pagina(html, rubro_nombre)
                leads_rubro.extend(nuevos)
                print(f"   📄 Pág {pag}/{total_pags} → {len(nuevos)} empresas | acumulado rubro: {len(leads_rubro)}", flush=True)

                # Guardar progresivamente
                todos.extend(nuevos)
                guardar_csv(todos)

                time.sleep(random.uniform(0.5, 1.5))

            except Exception as e:
                print(f"   ⚠️  Error página {pag}: {e}", flush=True)
                continue

        print(f"   ✅ {rubro_nombre}: {len(leads_rubro)} empresas totales", flush=True)

    return todos

def main():
    print("=" * 55, flush=True)
    print("🏭 SCRAPER CATÁLOGO GBA - Producción Bonaerense", flush=True)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"📋 {len(RUBROS)} rubros a scrapear", flush=True)
    print("=" * 55, flush=True)

    leads = scrape()
    guardar_csv(leads)

    print(f"\n{'='*55}", flush=True)
    print(f"📊 TOTAL: {len(leads)} productores", flush=True)
    print(f"📧 Con email:    {sum(1 for l in leads if l['email'])}", flush=True)
    print(f"📞 Con teléfono: {sum(1 for l in leads if l['telefono'])}", flush=True)

main()
