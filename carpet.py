import os
import unicodedata
import re
# Ruta de la carpeta
carpeta = r"C:\Users\cmramirez\Downloads\ee-publisher\assets\sections"

def limpiar_nombre(nombre):
    # Separar nombre y extensión
    archivo, extension = os.path.splitext(nombre)

    # Quitar tildes
    archivo = unicodedata.normalize('NFKD', archivo).encode('ascii', 'ignore').decode('utf-8')

    # Minúsculas
    archivo = archivo.lower()

    # Reemplazar espacios por _
    archivo = archivo.replace(" ", "_")

    # Quitar caracteres raros
    archivo = re.sub(r'[^a-z0-9_]', '', archivo)

    return archivo + extension.lower()

# Recorrer archivos
for nombre in os.listdir(carpeta):
    ruta_vieja = os.path.join(carpeta, nombre)

    if os.path.isfile(ruta_vieja):
        nuevo_nombre = limpiar_nombre(nombre)
        ruta_nueva = os.path.join(carpeta, nuevo_nombre)

        os.rename(ruta_vieja, ruta_nueva)
        print(f"{nombre} -> {nuevo_nombre}")

print("Proceso terminado.")