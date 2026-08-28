#!/usr/bin/env python3
"""
generate_share_pages.py

Genera una página HTML estática por cada serie y película de data.json,
con meta tags Open Graph / Twitter Card ya rellenos (título, sinopsis,
póster), para que al compartir un link de una ficha en WhatsApp/Telegram/
Twitter salga una preview bonita con la imagen correcta.

Cada página generada no tiene contenido propio: solo sirve para el bot que
genera la preview. Al humano lo redirige automáticamente (JS + fallback
<meta refresh>) a la app real, abriendo la ficha correspondiente.

Uso:
    python3 generate_share_pages.py

Se espera ejecutar desde la raíz del repo (donde vive data.json). Crea/
actualiza las carpetas s/ (series) y p/ (películas), y borra archivos de
items que ya no existan en data.json.
"""
import html
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(REPO_ROOT, "data.json")
SITE_URL = "https://xxmadwavs.github.io/tintasapphic-gls"
FALLBACK_IMAGE = f"{SITE_URL}/og-image.jpg"
SITE_NAME = "TINTA Sapphic"

MAX_DESC_LEN = 160


def clean_description(text):
    if not text:
        return "Series y películas GL (sáficas) de todo el mundo — calendario, catálogo y dónde ver."
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > MAX_DESC_LEN:
        text = text[:MAX_DESC_LEN].rsplit(" ", 1)[0] + "…"
    return text


def esc(text):
    return html.escape(text or "", quote=True)


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} ~ {site_name}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{app_url}">

<meta property="og:type" content="video.other">
<meta property="og:site_name" content="{site_name}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="{image}">
<meta property="og:url" content="{page_url}">
<meta property="og:locale" content="es_ES">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{image}">

<meta http-equiv="refresh" content="0; url={app_url}">
<script>location.replace({app_url_js});</script>
</head>
<body>
<p>Abriendo <a href="{app_url}">{title}</a> en TINTA Sapphic…</p>
</body>
</html>
"""


def render_page(item, kind):
    item_id = str(item.get("id", ""))
    name = item.get("name", "")
    title = esc(name)
    description = esc(clean_description(item.get("synopsis", "")))
    image = esc(item.get("poster") or FALLBACK_IMAGE)

    if kind == "series":
        tab = "upcoming" if item.get("upcoming") else "list"
        app_url = f"{SITE_URL}/?tab={tab}#serie-{item_id}"
        page_url = f"{SITE_URL}/s/{item_id}.html"
    else:
        app_url = f"{SITE_URL}/?tab=movies#pelicula-{item_id}"
        page_url = f"{SITE_URL}/p/{item_id}.html"

    return PAGE_TEMPLATE.format(
        title=title,
        description=description,
        image=image,
        app_url=esc(app_url),
        app_url_js=json.dumps(app_url),
        page_url=esc(page_url),
        site_name=SITE_NAME,
    )


def sync_dir(folder, items, kind):
    os.makedirs(folder, exist_ok=True)
    valid_ids = set()

    for item in items:
        item_id = item.get("id")
        if not item_id:
            continue
        item_id = str(item_id)
        valid_ids.add(item_id)
        path = os.path.join(folder, f"{item_id}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(render_page(item, kind))

    # Borra páginas de items que ya no existen en data.json
    removed = 0
    for fname in os.listdir(folder):
        if not fname.endswith(".html"):
            continue
        if fname[:-5] not in valid_ids:
            os.remove(os.path.join(folder, fname))
            removed += 1

    return len(valid_ids), removed


def main():
    if not os.path.exists(DATA_PATH):
        print(f"ERROR: no se encontró {DATA_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    series = data.get("series", [])
    movies = data.get("movies", [])

    s_count, s_removed = sync_dir(os.path.join(REPO_ROOT, "s"), series, "series")
    p_count, p_removed = sync_dir(os.path.join(REPO_ROOT, "p"), movies, "movies")

    print(f"Series: {s_count} páginas generadas en s/ ({s_removed} eliminadas)")
    print(f"Películas: {p_count} páginas generadas en p/ ({p_removed} eliminadas)")


if __name__ == "__main__":
    main()
