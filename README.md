# 🧵 Scraper Textil Argentina — Guía Railway

## Archivos incluidos
```
scraper.py          ← el script principal
requirements.txt    ← dependencias Python
nixpacks.toml       ← config para Railway (instala Chromium)
```

---

## 📋 PASO A PASO

### 1. Crear cuenta en Railway
- Entrá a https://railway.app
- Registrate con tu cuenta de GitHub (es gratis)

---

### 2. Subir los archivos a GitHub
1. Entrá a https://github.com y creá un repositorio nuevo
   - Nombre: `scraper-textil-argentina`
   - Privado ✅ (recomendado)
2. Subí los 3 archivos: `scraper.py`, `requirements.txt`, `nixpacks.toml`
   - Hacé click en "uploading an existing file"
   - Arrastrá los 3 archivos juntos

---

### 3. Deployar en Railway
1. Entrá a https://railway.app/new
2. Elegí **"Deploy from GitHub repo"**
3. Conectá tu cuenta de GitHub y seleccioná `scraper-textil-argentina`
4. Railway va a detectar automáticamente el `nixpacks.toml`
5. Hacé click en **Deploy** ✅

---

### 4. Ver los logs en tiempo real
- En Railway, hacé click en tu proyecto → pestaña **"Deployments"**
- Vas a ver los logs con los leads encontrados en tiempo real:
  ```
  🔍 Buscando: 'fábrica textil Argentina'
     → 18 resultados encontrados
     ✅ [1] Textil San Martín | +54 11 4xxx | www.textilsm.com.ar
     ✅ [2] Confecciones Norte | +54 351 4xxx | ...
  ```

---

### 5. Descargar el CSV con los leads
Railway no tiene almacenamiento persistente por defecto, así que tenés 2 opciones:

#### Opción A — Google Drive (recomendado)
Agregá esto al final del `scraper.py` para subir el CSV automáticamente:
```python
# Instalar: pip install google-auth google-auth-oauthlib google-api-python-client
# Ver guía: https://developers.google.com/drive/api/quickstart/python
```
(Avisame y te armo esto también)

#### Opción B — Ver en logs
El script imprime cada lead en los logs, podés copiarlos desde Railway.

#### Opción C — Railway Volume (más simple)
1. En Railway → tu proyecto → **"+ New"** → **"Volume"**
2. Montá el volumen en `/app`
3. El CSV se va a guardar ahí y podés descargarlo

---

## ⚙️ Ajustes opcionales

Abrí `scraper.py` y modificá estas variables al principio:

| Variable | Default | Descripción |
|---|---|---|
| `MAX_RESULTADOS_POR_BUSQUEDA` | 20 | Subí a 50 para más leads |
| `BUSQUEDAS` | 10 búsquedas | Agregá o quitá rubros |
| `DELAY_MIN / DELAY_MAX` | 2.5 / 5.0 seg | Aumentá si hay captchas |

---

## ❓ Problemas frecuentes

**Error: "No such file chromium"**
→ Verificá que `nixpacks.toml` está en la raíz del repo

**El scraper se detiene pronto**
→ Google puede mostrar captcha. Aumentá los delays o esperá unas horas

**No veo resultados**
→ Google cambió su HTML. Avisame y actualizo los selectores

---

## 💰 Costo en Railway
- Plan gratuito: **$5 de crédito/mes** (suficiente para correr el scraper varias veces)
- El scraper tarda ~20-40 minutos en completar todas las búsquedas
