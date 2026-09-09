#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_drive_data.py
===================

Genera (o actualiza) `products.json` y la carpeta `imagenes/` del catálogo.

Tiene dos modos:

  1) CARPETA LOCAL  (el más sencillo y el recomendado)
     Descargas la carpeta de Google Drive a tu computadora
     (Drive -> clic derecho en la carpeta -> "Descargar") y le pasas la ruta:

         py fetch_drive_data.py --local "C:/Users/tu-usuario/Downloads/Cosas Disponibles"

  2) CARPETA PÚBLICA DE GOOGLE DRIVE
     Necesitas una API key gratuita de Google Cloud (Drive API v3) y que la
     carpeta esté compartida como "Cualquiera con el enlace":

         py fetch_drive_data.py --drive-folder 1AbCdEf... --api-key AIzaSy...

En los dos casos el script:

  * Recorre las subcarpetas y las convierte en CATEGORÍAS del catálogo.
  * Copia (y opcionalmente comprime) las fotos a `imagenes/<categoria>/`.
  * Crea una miniatura ligera para que el catálogo cargue rápido en el celular.
  * Descarta archivos repetidos comparando su contenido.
  * Redacta una descripción corta y atractiva para cada artículo.
  * RESPETA lo que ya editaste a mano: si un producto ya existe en
    products.json, conserva su nombre, precio, descripción y estado.

Requisitos:
  - Python 3.8 o más nuevo.
  - Opcional pero MUY recomendado:  py -m pip install pillow
    (sin Pillow el script funciona igual, solo que no comprime las fotos)
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import unicodedata
import urllib.parse
import urllib.request

# --------------------------------------------------------------------------
# AJUSTES
# --------------------------------------------------------------------------

# Nombre bonito para cada carpeta de origen. Si una carpeta no aparece aquí,
# se usa su propio nombre tal cual.
CATEGORIAS = {
    "muebles": "Muebles",
    "juguetes": "Juguetes",
    "varios": "Varios",
    "calzado, cobijas y mas": "Calzado y Textiles",
    "electrodomesticos, platos, vasos y mas": "Cocina y Hogar",
}

CATEGORIA_POR_DEFECTO = "Varios"

EXTENSIONES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

ANCHO_MAXIMO = 1400      # px, para la imagen grande del visor
ANCHO_MINIATURA = 600    # px, para la tarjeta del catálogo
CALIDAD_JPEG = 82

SALIDA_IMAGENES = "imagenes"
SALIDA_JSON = "products.json"


# --------------------------------------------------------------------------
# TEXTO: nombres y descripciones automáticas
# --------------------------------------------------------------------------

# Estas plantillas producen 2-3 oraciones. Se elige una de forma estable
# (siempre la misma para el mismo archivo) a partir del hash de la imagen.
PLANTILLAS = [
    "{articulo} en muy buen estado, listo para seguir usándose. Se cuidó bien y funciona sin problema. Puedes ver todos los detalles y medidas en la foto.",
    "Artículo de segunda mano en excelentes condiciones. {articulo_frase} conserva muy bien su forma y su acabado. Toca la imagen para verla en grande con las medidas exactas.",
    "{articulo}, usado pero muy bien conservado. Se entrega limpio y revisado. En la foto vienen las medidas y todos los detalles.",
    "Buena oportunidad: {articulo_frase} está en condiciones muy buenas y a un precio accesible. Amplía la imagen para ver medidas y características.",
    "{articulo} de segunda mano, cuidado y en buen estado general. Ideal si buscas algo funcional sin pagar precio de nuevo. Los detalles están en la foto.",
]

# Pistas para adivinar el nombre a partir del nombre del archivo.
PISTAS = [
    ("mesa", "Mesa"), ("silla", "Silla"), ("sillon", "Sillón"), ("sofa", "Sofá"),
    ("cama", "Cama"), ("colchon", "Colchón"), ("buro", "Buró"), ("librero", "Librero"),
    ("closet", "Clóset"), ("comoda", "Cómoda"), ("repisa", "Repisa"), ("escritorio", "Escritorio"),
    ("licuadora", "Licuadora"), ("batidora", "Batidora"), ("horno", "Horno"),
    ("microondas", "Microondas"), ("cafetera", "Cafetera"), ("plancha", "Plancha"),
    ("olla", "Olla"), ("sarten", "Sartén"), ("vaso", "Vasos"), ("plato", "Platos"),
    ("taza", "Tazas"), ("cubiertos", "Cubiertos"), ("vajilla", "Vajilla"),
    ("zapato", "Zapatos"), ("tenis", "Tenis"), ("bota", "Botas"), ("sandalia", "Sandalias"),
    ("cobija", "Cobija"), ("edredon", "Edredón"), ("sabana", "Sábanas"), ("almohada", "Almohada"),
    ("juguete", "Juguete"), ("muneca", "Muñeca"), ("peluche", "Peluche"),
    ("rompecabezas", "Rompecabezas"), ("disfraz", "Disfraz"), ("lego", "Bloques de construcción"),
    ("bicicleta", "Bicicleta"), ("carriola", "Carriola"), ("mochila", "Mochila"),
    ("lampara", "Lámpara"), ("espejo", "Espejo"), ("cuadro", "Cuadro"), ("maceta", "Maceta"),
]


def sin_acentos(texto):
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    ).lower()


def slug(texto):
    base = sin_acentos(texto)
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return base or "articulo"


def nombre_categoria(carpeta):
    if not carpeta:
        return CATEGORIA_POR_DEFECTO
    clave = sin_acentos(carpeta).strip()
    return CATEGORIAS.get(clave, carpeta.strip())


def adivinar_nombre(nombre_archivo, categoria, consecutivo):
    """
    Intenta sacar un nombre del archivo. Las capturas de pantalla
    (Screenshot_2026..., IMG-2026...) no dicen nada, así que en ese caso
    devolvemos un nombre provisional que después se edita a mano.
    """
    base = os.path.splitext(nombre_archivo)[0]
    plano = sin_acentos(base)

    for pista, bonito in PISTAS:
        if pista in plano:
            return bonito, False

    generico = re.match(r"^(screenshot|img|image|photo|foto|video|20\d{6}|whatsapp)", plano)
    if generico:
        return "{} #{}".format(categoria, consecutivo), True

    limpio = re.sub(r"[_\-]+", " ", base).strip()
    limpio = re.sub(r"\s{2,}", " ", limpio)
    if len(limpio) < 3:
        return "{} #{}".format(categoria, consecutivo), True
    return limpio[:1].upper() + limpio[1:], False


def redactar_descripcion(nombre, categoria, semilla):
    plantilla = PLANTILLAS[int(semilla[:8], 16) % len(PLANTILLAS)]
    articulo = nombre if not nombre.startswith(categoria + " #") else "Artículo de {}".format(categoria.lower())
    return plantilla.format(
        articulo=articulo,
        articulo_frase="El artículo" if articulo.startswith("Artículo") else "El " + articulo.lower(),
    )


# --------------------------------------------------------------------------
# IMÁGENES
# --------------------------------------------------------------------------

def hash_archivo(ruta):
    h = hashlib.md5()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 16), b""):
            h.update(bloque)
    return h.hexdigest()


def cargar_pillow():
    try:
        from PIL import Image, ImageOps  # noqa
        return Image, ImageOps
    except ImportError:
        return None, None


def procesar_imagen(origen, destino_grande, destino_mini, Image, ImageOps):
    """Comprime y crea miniatura. Si no hay Pillow, solo copia el archivo."""
    os.makedirs(os.path.dirname(destino_grande), exist_ok=True)
    os.makedirs(os.path.dirname(destino_mini), exist_ok=True)

    if Image is None:
        shutil.copy2(origen, destino_grande)
        shutil.copy2(origen, destino_mini)
        return

    with Image.open(origen) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode in ("RGBA", "P", "LA"):
            fondo = Image.new("RGB", im.size, (255, 255, 255))
            fondo.paste(im.convert("RGBA"), mask=im.convert("RGBA").split()[-1])
            im = fondo
        else:
            im = im.convert("RGB")

        grande = im.copy()
        grande.thumbnail((ANCHO_MAXIMO, ANCHO_MAXIMO * 3), Image.LANCZOS)
        grande.save(destino_grande, "JPEG", quality=CALIDAD_JPEG, optimize=True, progressive=True)

        mini = im.copy()
        mini.thumbnail((ANCHO_MINIATURA, ANCHO_MINIATURA * 3), Image.LANCZOS)
        mini.save(destino_mini, "JPEG", quality=78, optimize=True, progressive=True)


# --------------------------------------------------------------------------
# ORIGEN 1: CARPETA LOCAL
# --------------------------------------------------------------------------

def recolectar_local(raiz):
    """Devuelve [(categoria, nombre_archivo, ruta_completa), ...]"""
    encontrados = []
    raiz = os.path.abspath(raiz)
    for actual, carpetas, archivos in os.walk(raiz):
        carpetas[:] = [c for c in carpetas if not c.startswith(".")]
        relativa = os.path.relpath(actual, raiz)
        carpeta = "" if relativa == "." else relativa.split(os.sep)[0]
        for archivo in sorted(archivos):
            if os.path.splitext(archivo)[1].lower() in EXTENSIONES:
                encontrados.append((nombre_categoria(carpeta), archivo, os.path.join(actual, archivo)))
    return encontrados


# --------------------------------------------------------------------------
# ORIGEN 2: CARPETA PÚBLICA DE GOOGLE DRIVE (API v3 con API key)
# --------------------------------------------------------------------------

API = "https://www.googleapis.com/drive/v3/files"


def drive_listar(carpeta_id, api_key):
    """Lista los hijos directos de una carpeta pública de Drive."""
    elementos, token = [], None
    while True:
        params = {
            "q": "'{}' in parents and trashed = false".format(carpeta_id),
            "key": api_key,
            "fields": "nextPageToken, files(id, name, mimeType, size)",
            "pageSize": "1000",
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
        }
        if token:
            params["pageToken"] = token
        url = API + "?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=60) as r:
            datos = json.load(r)
        elementos.extend(datos.get("files", []))
        token = datos.get("nextPageToken")
        if not token:
            break
    return elementos


def drive_descargar(archivo_id, api_key, destino):
    url = "{}/{}?alt=media&key={}".format(API, archivo_id, api_key)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with urllib.request.urlopen(url, timeout=180) as r, open(destino, "wb") as f:
        shutil.copyfileobj(r, f)


def recolectar_drive(carpeta_id, api_key, cache):
    """Descarga a una carpeta temporal y devuelve la misma lista que recolectar_local."""
    encontrados = []

    def recorrer(fid, categoria):
        for item in drive_listar(fid, api_key):
            if item["mimeType"] == "application/vnd.google-apps.folder":
                recorrer(item["id"], nombre_categoria(item["name"]))
            elif item["mimeType"].startswith("image/"):
                destino = os.path.join(cache, slug(categoria), item["name"])
                if not os.path.exists(destino):
                    print("   descargando  {}/{}".format(categoria, item["name"]))
                    drive_descargar(item["id"], api_key, destino)
                encontrados.append((categoria, item["name"], destino))

    recorrer(carpeta_id, CATEGORIA_POR_DEFECTO)
    return encontrados


# --------------------------------------------------------------------------
# CONSTRUCCIÓN DEL products.json
# --------------------------------------------------------------------------

def cargar_previos(ruta):
    """Lee el products.json anterior para no perder las ediciones a mano."""
    if not os.path.exists(ruta):
        return {}
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (ValueError, OSError):
        return {}
    lista = datos if isinstance(datos, list) else datos.get("productos", [])
    return {p.get("id"): p for p in lista if isinstance(p, dict) and p.get("id")}


def construir(encontrados, salida_dir, Image, ImageOps):
    previos = cargar_previos(os.path.join(salida_dir, SALIDA_JSON))
    vistos = set()
    productos = []
    consecutivos = {}
    repetidos = 0

    encontrados.sort(key=lambda t: (t[0], t[1]))

    for categoria, archivo, ruta in encontrados:
        firma = hash_archivo(ruta)
        if firma in vistos:
            repetidos += 1
            continue
        vistos.add(firma)

        pid = "p-" + firma[:10]
        consecutivos[categoria] = consecutivos.get(categoria, 0) + 1

        carpeta_cat = slug(categoria)
        rel_grande = "{}/{}/{}.jpg".format(SALIDA_IMAGENES, carpeta_cat, pid)
        rel_mini = "{}/{}/{}-mini.jpg".format(SALIDA_IMAGENES, carpeta_cat, pid)

        procesar_imagen(
            ruta,
            os.path.join(salida_dir, rel_grande.replace("/", os.sep)),
            os.path.join(salida_dir, rel_mini.replace("/", os.sep)),
            Image, ImageOps,
        )

        nombre, provisional = adivinar_nombre(archivo, categoria, consecutivos[categoria])
        descripcion = redactar_descripcion(nombre, categoria, firma)

        nuevo = {
            "id": pid,
            "nombre": nombre,
            "categoria": categoria,
            "precio": None,
            "descripcion": descripcion,
            "imagen": rel_grande,
            "miniatura": rel_mini,
            "estado": "disponible",
        }
        if provisional:
            nuevo["revisar"] = True
            nuevo["_archivoOriginal"] = archivo

        # Lo que ya editaste a mano manda sobre lo automático.
        anterior = previos.get(pid)
        if anterior:
            for campo in ("nombre", "categoria", "precio", "descripcion", "estado"):
                if campo in anterior and anterior[campo] not in (None, "", []):
                    nuevo[campo] = anterior[campo]
            if anterior.get("nombre") and not anterior.get("revisar"):
                nuevo.pop("revisar", None)

        productos.append(nuevo)

    return productos, repetidos


def main():
    ap = argparse.ArgumentParser(description="Genera products.json e imagenes/ para el catálogo.")
    ap.add_argument("--local", help="Ruta a la carpeta descargada de Google Drive.")
    ap.add_argument("--drive-folder", help="ID de la carpeta pública de Google Drive.")
    ap.add_argument("--api-key", help="API key de Google con Drive API habilitada.")
    ap.add_argument("--salida", default=".", help="Carpeta del sitio web (por defecto, la actual).")
    args = ap.parse_args()

    if not args.local and not args.drive_folder:
        ap.error("Usa --local <carpeta>  o  --drive-folder <id> --api-key <key>")
    if args.drive_folder and not args.api_key:
        ap.error("--drive-folder necesita también --api-key")

    salida_dir = os.path.abspath(args.salida)
    Image, ImageOps = cargar_pillow()
    if Image is None:
        print("AVISO: Pillow no está instalado, las fotos se copiarán sin comprimir.")
        print("       Para un sitio mucho más ligero:  py -m pip install pillow\n")

    if args.local:
        print("Leyendo carpeta local: {}".format(args.local))
        encontrados = recolectar_local(args.local)
    else:
        cache = os.path.join(salida_dir, "_descargas_drive")
        print("Leyendo carpeta de Google Drive: {}".format(args.drive_folder))
        encontrados = recolectar_drive(args.drive_folder, args.api_key, cache)

    if not encontrados:
        print("No se encontró ninguna imagen. Revisa la ruta o el ID de la carpeta.")
        return 1

    print("Se encontraron {} imágenes. Procesando...".format(len(encontrados)))
    productos, repetidos = construir(encontrados, salida_dir, Image, ImageOps)

    ruta_json = os.path.join(salida_dir, SALIDA_JSON)
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(productos, f, ensure_ascii=False, indent=2)

    por_revisar = sum(1 for p in productos if p.get("revisar"))
    sin_precio = sum(1 for p in productos if not p.get("precio"))

    print("\nListo.")
    print("  Productos en el catálogo : {}".format(len(productos)))
    print("  Imágenes repetidas omitidas: {}".format(repetidos))
    print("  Archivo generado          : {}".format(ruta_json))
    if por_revisar:
        print("\n  OJO: {} productos tienen nombre provisional (\"revisar\": true).".format(por_revisar))
    if sin_precio:
        print("  OJO: {} productos todavía no tienen precio.".format(sin_precio))
        print("  Abre products.json y llena \"nombre\" y \"precio\" de esos artículos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
