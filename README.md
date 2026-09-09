# Catálogo de Cosas Disponibles

Catálogo web sencillo para vender artículos de segunda mano. Cada producto tiene
un botón grande que abre WhatsApp con el mensaje ya escrito.

No necesita servidor, base de datos ni pagar nada: son archivos sueltos que se
publican gratis en **GitHub Pages**.

---

## 1. Antes de publicar: pon tu número de WhatsApp

Abre `script.js` y cambia **la primera parte del archivo**:

```js
const CONFIG = {
  whatsapp: "525500000000",   // <-- tu número aquí
  titulo: "Cosas Disponibles",
  subtitulo: "Artículos usados en buen estado. Toca el botón verde y pregúntame por WhatsApp.",
  ...
};
```

El número va **con código de país, sin espacios, sin `+` y sin guiones**.

| País   | Ejemplo de número      | Cómo se escribe aquí |
|--------|------------------------|----------------------|
| México | 55 1234 5678           | `525512345678`       |
| España | 612 34 56 78           | `34612345678`        |

> Si eres de México y notas que no llegan los mensajes, prueba agregando un `1`
> después del 52: `5215512345678`.

---

## 2. Llena los nombres y los precios

El archivo `products.json` es la lista de productos. Cada uno se ve así:

```json
{
  "id": "p-3f9a2c1b04",
  "nombre": "Muebles #1",
  "categoria": "Muebles",
  "precio": null,
  "descripcion": "Artículo de segunda mano en excelentes condiciones...",
  "imagen": "imagenes/muebles/p-3f9a2c1b04.jpg",
  "miniatura": "imagenes/muebles/p-3f9a2c1b04-mini.jpg",
  "estado": "disponible",
  "revisar": true
}
```

Lo único que hay que editar es:

- **`nombre`** — cómo quieres que se vea el título en la tarjeta.
- **`precio`** — solo el número, sin `$` ni comas: `1100`.
  Si lo dejas en `null`, la tarjeta dice *“Precio a tratar”*.
- **`descripcion`** — ya viene una redactada; cámbiala si quieres.
- **`estado`** — `"disponible"`, `"apartado"` o `"vendido"`.
  Cuando algo se vende, cambia esta palabra: la tarjeta se pone en gris,
  el precio se tacha y el botón de WhatsApp se desactiva solo.
- **`revisar`** — bórralo cuando ya le pusiste nombre y precio de verdad.
  Sirve para saber qué productos te faltan.

⚠️ Cuida las comas y las comillas. Si el catálogo deja de cargar, casi siempre
es una coma de más o de menos en `products.json`.

---

## 3. Cómo actualizar el catálogo cuando haya fotos nuevas

1. Descarga la carpeta de Google Drive a tu computadora
   (en Drive: clic derecho sobre la carpeta → **Descargar**).
2. Ejecuta:

```bash
py fetch_drive_data.py --local "C:/Users/tu-usuario/Downloads/Cosas Disponibles"
```

El script:

- convierte cada subcarpeta en una **categoría**,
- copia y **comprime** las fotos dentro de `imagenes/`,
- crea una **miniatura** para que el sitio abra rápido en el celular,
- **descarta fotos repetidas** comparando su contenido,
- redacta una **descripción de 2–3 oraciones** para cada artículo,
- y **no borra lo que ya escribiste**: si un producto ya tenía nombre, precio o
  estado, los conserva tal cual.

Para que las fotos queden ligeras conviene instalar Pillow una sola vez:

```bash
py -m pip install pillow
```

Si no puedes instalarlo (por ejemplo, si tu red lo bloquea), en Windows puedes
comprimir las fotos después con:

```bash
powershell -ExecutionPolicy Bypass -File optimizar_imagenes.ps1
```

### Alternativa: leer Drive directamente

Si prefieres no descargar la carpeta, el script también puede leer una carpeta
pública de Drive. Necesitas una API key gratuita de Google Cloud con la
*Google Drive API* activada, y que la carpeta esté compartida como
*“Cualquiera con el enlace”*:

```bash
py fetch_drive_data.py --drive-folder ID_DE_LA_CARPETA --api-key TU_API_KEY
```

---

## 4. Publicar gratis en GitHub Pages

1. Crea una cuenta en <https://github.com> (si no tienes).
2. Dale a **New repository**. Ponle un nombre, por ejemplo `catalogo`, márcalo
   como **Public** y créalo.
3. En la página del repositorio nuevo, entra a **Add file → Upload files** y
   arrastra **todo el contenido de esta carpeta**: `index.html`, `styles.css`,
   `script.js`, `products.json`, `.nojekyll` y la carpeta `imagenes`.
   Luego baja y presiona **Commit changes**.
4. Ve a **Settings → Pages** (menú de la izquierda).
5. En *Source* elige **Deploy from a branch**; en *Branch* elige **main** y la
   carpeta **/ (root)**. Presiona **Save**.
6. Espera 1 o 2 minutos y recarga esa página: aparecerá tu dirección, algo como

   ```
   https://tu-usuario.github.io/catalogo/
   ```

Esa es la liga que compartes por WhatsApp o Facebook.

> **Si prefieres la terminal:** entra a esta carpeta y corre
> `git init`, `git add .`, `git commit -m "Catálogo"`,
> `git branch -M main`, `git remote add origin <url-del-repo>`, `git push -u origin main`.

### Para actualizar el sitio después

Sube de nuevo los archivos que cambiaron (normalmente `products.json` y las
fotos nuevas). GitHub Pages se actualiza solo en un par de minutos.

---

## 5. Ver el sitio en tu computadora antes de subirlo

Abrir `index.html` con doble clic **no funciona**: el navegador bloquea la
lectura de `products.json` por seguridad. Levanta un servidor local:

```bash
py -m http.server 8000
```

Y abre <http://localhost:8000> en tu navegador.

---

## Qué hace cada archivo

| Archivo | Para qué sirve |
|---|---|
| `index.html` | La estructura de la página. |
| `styles.css` | Los colores, el tamaño de letra y el diseño. |
| `script.js` | El buscador, los filtros, el visor de fotos y los enlaces de WhatsApp. **Aquí va tu número.** |
| `products.json` | La lista de productos. **Aquí van nombres, precios y estados.** |
| `fetch_drive_data.py` | Genera `products.json` y las imágenes a partir de la carpeta de Drive. |
| `optimizar_imagenes.ps1` | Comprime las fotos en Windows si no tienes Pillow. |
| `imagenes/` | Las fotos ya listas, ordenadas por categoría. |
| `.nojekyll` | Le dice a GitHub Pages que publique los archivos tal cual. |

---

## Detalles pensados para que sea fácil de usar

- Letra grande y contraste alto; botón **A+** para agrandar todavía más el texto
  (se recuerda para la próxima visita).
- Botones de WhatsApp de 64 px de alto: fáciles de tocar con el dedo.
- Buscador que ignora acentos (*colchon* encuentra *colchón*).
- Al tocar una foto se abre en grande, con flechas para pasar de un producto a
  otro y deslizando con el dedo en el celular.
- Cada producto tiene su propia liga (`...#producto=p-3f9a2c1b04`) por si quieres
  mandar uno solo por WhatsApp.
- Funciona igual en celular, tablet y computadora, y se puede imprimir.
