"""
app.py - EE Publisher
App que extrae contenido de URLs de El Espectador y genera la tarjeta
estilo plantilla automaticamente.
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from io import BytesIO

from generator import generate_card_from_image, fetch_image, TEMPLATES

st.set_page_config(page_title="EE Publisher", page_icon=":newspaper:", layout="centered")
st.title("EE Publisher")
st.caption("Pega una URL y obten la tarjeta lista para publicar")


def extract_from_url(url):
    """Extrae titulo, imagen (en mejor calidad posible) y seccion desde cualquier URL."""
    # Agregar https:// si falta
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        resp = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
            },
            timeout=20,
            allow_redirects=True,
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"No se pudo cargar la URL: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")

    def meta(sel):
        tag = soup.select_one(sel)
        return (tag.get("content", "") if tag else "") or ""

    # ================== Titulo ==================
    title = (
        meta('meta[property="og:title"]')
        or meta('meta[name="twitter:title"]')
        or meta('meta[name="title"]')
        or (soup.title.string if soup.title else "")
        or (soup.h1.get_text() if soup.h1 else "")
    )

    # Limpiar sufijos comunes del titulo (" | El Espectador", " - CNN", etc.)
    title = title.strip()
    for separator in [" | ", " - ", " · "]:
        if separator in title:
            parts = title.rsplit(separator, 1)
            # Solo cortar si la ultima parte parece nombre de sitio (corta, sin signos de puntuacion)
            if len(parts[1]) < 40 and not any(c in parts[1] for c in ".?!,;:"):
                title = parts[0].strip()
                break

    # ================== Imagen ==================
    image = ""

    # 1. Buscar imagen principal del articulo con srcset (mejor calidad)
    main_img_selectors = [
        "article figure img",
        "article header img",
        "figure.lead img",
        "figure[class*='hero'] img",
        "figure[class*='main'] img",
        "figure[class*='cover'] img",
        ".article-image img",
        ".post-thumbnail img",
        "article img",
        "main img",
    ]

    for selector in main_img_selectors:
        main_img = soup.select_one(selector)
        if main_img:
            srcset = main_img.get("srcset") or main_img.get("data-srcset")
            if srcset:
                best = parse_srcset_max(srcset)
                if best:
                    image = best
                    break
            src = (
                main_img.get("data-src")
                or main_img.get("data-original")
                or main_img.get("data-lazy-src")
                or main_img.get("src")
            )
            if src and not src.startswith("data:"):  # ignorar placeholders base64
                image = src
                break

    # 2. Fallback: meta tags
    if not image:
        image = (
            meta('meta[property="og:image:secure_url"]')
            or meta('meta[property="og:image"]')
            or meta('meta[name="twitter:image"]')
            or meta('meta[name="twitter:image:src"]')
            or meta('link[rel="image_src"]')
        )

    # 3. Hacer absoluta si es relativa
    if image:
        if image.startswith("//"):
            image = "https:" + image
        elif image.startswith("/"):
            from urllib.parse import urljoin
            image = urljoin(url, image)

    # ================== Seccion ==================
    section = (
        meta('meta[property="article:section"]')
        or meta('meta[name="section"]')
        or meta('meta[name="category"]')
        or meta('meta[property="article:tag"]')
    )

    # Buscar en breadcrumbs si no se encontro
    if not section:
        breadcrumb = soup.select_one('[class*="breadcrumb"] a, nav.breadcrumb a, ol[itemtype*="BreadcrumbList"] a')
        if breadcrumb:
            section = breadcrumb.get_text(strip=True)

    # Fallback: extraer del path de la URL
    if not section:
        try:
            parts = [p for p in urlparse(url).path.split("/") if p]
            # Ignorar palabras comunes que no son secciones
            skip = {"articulo", "article", "post", "noticia", "news", "story", "20", "21", "22", "23", "24", "25", "26"}
            for part in parts:
                if (
                    not part.replace("-", "").isdigit()
                    and not part.lower() in skip
                    and not part.startswith("20")  # 2024, 2025...
                ):
                    section = part.replace("-", " ")
                    break
        except Exception:
            pass

    return {
        "title": title.strip(),
        "image": (image or "").strip(),
        "section": (section or "").upper().strip(),
    }


def parse_srcset_max(srcset):
    """
    Parsea un atributo srcset y devuelve la URL con mayor ancho.
    Formato: 'url1 600w, url2 1200w, url3 2400w'
    """
    if not srcset:
        return None

    best_url = None
    best_width = 0

    for item in srcset.split(","):
        item = item.strip()
        if not item:
            continue
        parts = item.rsplit(" ", 1)
        if len(parts) == 2:
            url_part, width_part = parts
            try:
                # Quitar la 'w' o 'x' final
                width = int("".join(c for c in width_part if c.isdigit()))
                if width > best_width:
                    best_width = width
                    best_url = url_part.strip()
            except ValueError:
                pass
        elif len(parts) == 1:
            # Sin width especificado, usar como fallback
            if not best_url:
                best_url = parts[0].strip()

    return best_url


# =====================================================
# UI
# =====================================================

st.subheader("1. URL del articulo")
url = st.text_input("URL", placeholder="https://www.elespectador.com/...", label_visibility="collapsed")

if st.button("Extraer y generar tarjeta", type="primary", use_container_width=True):
    if not url:
        st.error("Pega una URL primero")
    else:
        try:
            with st.spinner("Extrayendo contenido..."):
                data = extract_from_url(url)

            # Limpiar caches de imagen anteriores (clave: este es el bug que arreglaba)
            keys_to_remove = [k for k in st.session_state.keys() if k.startswith("img_cache_")]
            for k in keys_to_remove:
                del st.session_state[k]

            st.session_state["data"] = data
            st.session_state["edited"] = False
        except Exception as e:
            st.error(f"Error al extraer: {e}")

# Si ya hay datos extraidos, mostrar campos editables y generar
if "data" in st.session_state:
    data = st.session_state["data"]

    st.subheader("2. Datos extraidos (editables)")
    title = st.text_input("Titulo", value=data["title"], key="title_input")
    section = st.text_input("Seccion", value=data["section"], key="section_input")
    image_url = st.text_input("URL de la imagen", value=data["image"], key="image_input")

    # Guardar cambios
    data["title"] = title
    data["section"] = section

    # Si el usuario cambio manualmente la URL de la imagen, invalidar el cache
    if image_url != data.get("image"):
        keys_to_remove = [k for k in st.session_state.keys() if k.startswith("img_cache_")]
        for k in keys_to_remove:
            del st.session_state[k]
    data["image"] = image_url

    st.subheader("3. Plantilla")
    template_options = list(TEMPLATES.keys())
    template_labels = [f"{TEMPLATES[k]['name']} — {TEMPLATES[k]['description']}" for k in template_options]
    template_idx = st.radio(
        "Elige la plantilla:",
        options=range(len(template_options)),
        format_func=lambda i: template_labels[i],
        label_visibility="collapsed",
        horizontal=False,
    )
    selected_template = template_options[template_idx]

    st.subheader("4. Ajustar imagen")

    if not title or not image_url:
        st.warning("Falta titulo o imagen")
    else:
        # Descargar imagen una sola vez y cachear
        cache_key = f"img_cache_{image_url}"
        if cache_key not in st.session_state:
            with st.spinner("Descargando imagen en alta calidad..."):
                try:
                    st.session_state[cache_key] = fetch_image(image_url)
                except Exception as e:
                    st.error(f"Error al descargar imagen: {e}")
                    st.stop()
        source_img = st.session_state[cache_key]

        # Info de la imagen
        st.caption(
            f"📷 Imagen descargada: **{source_img.width} × {source_img.height} px** "
            f"({source_img.width * source_img.height / 1_000_000:.1f} MP)"
        )

        # === Controles de ajuste ===
        col1, col2, col3 = st.columns(3)

        with col1:
            zoom = st.slider("🔍 Zoom", 1.0, 3.0, 1.0, 0.05,
                help="1.0 = ajuste minimo. Subir para acercar.")

        with col2:
            offset_x = st.slider("↔ Horizontal", 0.0, 1.0, 0.5, 0.05,
                help="0 = izquierda, 0.5 = centro, 1 = derecha")

        with col3:
            offset_y = st.slider("↕ Vertical", 0.0, 1.0, 0.5, 0.05,
                help="0 = arriba, 0.5 = centro, 1 = abajo")

        # Boton para resetear
        if st.button("↺ Restablecer ajustes", use_container_width=False):
            st.rerun()

        st.subheader("5. Tarjeta generada")

        try:
            img = generate_card_from_image(
                source_image=source_img,
                section=section or "NOTICIAS",
                title=title,
                template=selected_template,
                zoom=zoom,
                offset_x=offset_x,
                offset_y=offset_y,
            )

            # Mostrar
            st.image(img, use_column_width=True)

            # Descargar
            buf = BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)

            # Nombre seguro para el archivo
            safe_name = "".join(c if c.isalnum() else "-" for c in title.lower())[:50]

            st.download_button(
                label="Descargar PNG",
                data=buf,
                file_name=f"tarjeta-{safe_name}.png",
                mime="image/png",
                use_container_width=True,
                type="primary",
            )

            st.info("Sube este PNG a SocialFlow o donde lo necesites publicar")
        except Exception as e:
            st.error(f"Error al generar: {e}")
            import traceback
            with st.expander("Detalles del error"):
                st.code(traceback.format_exc())
