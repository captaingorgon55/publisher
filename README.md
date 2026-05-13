# EE Publisher

App en Python + Streamlit que **extrae el contenido de una URL de un articulo** y **genera automaticamente una tarjeta** estilo El Espectador (badge rojo de seccion, imagen de fondo, titulo con linea roja, logo EE).

**Sin Canva, sin OAuth, sin tokens.** Todo offline, gratis, en tu PC.

## Requisitos

- **Python 3.9 o superior** ([descargar](https://www.python.org/downloads/))
  - Al instalar marca "Add Python to PATH"

## Instalacion (solo la primera vez)

Abre PowerShell en el directorio del proyecto:

```powershell
cd C:\Users\cmramirez\Downloads\ee-publisher
```

Crea entorno virtual e instala dependencias:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Si PowerShell te bloquea el script de activacion, corre una vez:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Usar

```powershell
streamlit run app.py
```

Se abre en `http://localhost:8501`.

**Flujo:**
1. Pegas URL del articulo
2. Clic "Extraer y generar tarjeta"
3. Revisas titulo/seccion/imagen (editable)
4. La tarjeta se genera automaticamente
5. Clic "Descargar PNG"
6. Sube el PNG a SocialFlow (o donde necesites)

## Para volver a usarla otro dia

```powershell
cd C:\Users\cmramirez\Downloads\ee-publisher
.\venv\Scripts\Activate.ps1
streamlit run app.py
```

## Personalizacion

En `generator.py` puedes ajustar:
- `CANVAS_SIZE`: tamano de la tarjeta (default 1080x1350, formato Instagram vertical)
- `RED`: color rojo del badge y la linea (default `(227, 27, 35)` rojo El Espectador)
- `BADGE_TOP`, `BADGE_LEFT`: posicion del badge
- `TITLE_BOTTOM_PADDING`: distancia del titulo al borde inferior
- Tamanos de fuente en la funcion `generate_card`

La fuente: en Windows usa Georgia Bold (la real de El Espectador). Si no la tiene, prueba con Arial Bold.

## Troubleshooting

- **"python no se reconoce"**: Python no esta en PATH, reinstala marcando "Add Python to PATH".
- **El sitio bloquea el scraping**: edita manualmente los campos en el paso 2.
- **La fuente se ve diferente**: tu Windows no tiene Georgia. Instalala o edita `generator.py` para usar otra fuente.
- **La tarjeta sale rara con titulos muy largos**: el generador reduce el tamano de fuente automaticamente pero hay limite. Edita el titulo manualmente en el paso 2 si es necesario.
