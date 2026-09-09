/* ============================================================
   Catálogo de segunda mano — Lógica
   ============================================================ */

/* ------------------------------------------------------------------
   ⬇⬇⬇  LO ÚNICO QUE TIENES QUE CAMBIAR ESTÁ AQUÍ ABAJO  ⬇⬇⬇
   ------------------------------------------------------------------ */

const CONFIG = {
  // Número de WhatsApp CON código de país y SIN espacios, + ni guiones.
  // México: 52 + 10 dígitos  ->  "525512345678"
  // (Si el número es de México y no llegan los mensajes, prueba con 521...)
  whatsapp: "525569009299",

  titulo: "Cosas Disponibles",
  subtitulo: "Artículos usados en buen estado. Toca el botón verde y pregúntame por WhatsApp.",

  simboloMoneda: "$",
  codigoMoneda: "MXN",

  // {producto} y {precio} se reemplazan solos. No borres las llaves.
  mensaje: "Hola, vi en el catálogo el producto: {producto} (Precio: {precio}) y me interesa obtener más información.",

  mensajeGeneral: "Hola, vi tu catálogo en internet y quiero preguntarte por unos artículos.",
};

/* ------------------------------------------------------------------
   ⬆⬆⬆  DE AQUÍ PARA ABAJO YA NO HACE FALTA TOCAR NADA  ⬆⬆⬆
   ------------------------------------------------------------------ */

const $ = (sel) => document.querySelector(sel);

const el = {
  grid:        $("#grid"),
  filtros:     $("#filtros"),
  buscador:    $("#buscador"),
  limpiar:     $("#limpiarBusqueda"),
  contador:    $("#contador"),
  vacio:       $("#vacio"),
  verTodo:     $("#verTodo"),
  errorCarga:  $("#errorCarga"),
  errorDetalle:$("#errorDetalle"),
  tpl:         $("#tplTarjeta"),
  btnTexto:    $("#btnTexto"),
  waGeneral:   $("#waGeneral"),
  titulo:      $("#tituloSitio"),
  subtitulo:   $("#subtituloSitio"),
  lb:          $("#lightbox"),
  lbImg:       $("#lbImg"),
  lbTitulo:    $("#lbTitulo"),
  lbPrecio:    $("#lbPrecio"),
  lbWhats:     $("#lbWhats"),
  lbCerrar:    $("#lbCerrar"),
  lbPrev:      $("#lbPrev"),
  lbNext:      $("#lbNext"),
  btnArriba:   $("#btnArriba"),
};

let PRODUCTOS = [];     // catálogo completo
let VISIBLES  = [];     // lo que se está mostrando ahora
let categoriaActiva = "Todos";
let terminoBusqueda = "";
let indiceLightbox = -1;
let ultimoFoco = null;

/* ---------------- Utilidades ---------------- */

// Quita acentos y mayúsculas para que "colchon" encuentre "colchón".
const normalizar = (txt) =>
  String(txt || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");

const escapar = (txt) =>
  String(txt == null ? "" : txt)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

function formatearPrecio(precio) {
  if (precio === null || precio === undefined || precio === "") return "Precio a tratar";
  const num = Number(String(precio).replace(/[^0-9.]/g, ""));
  if (!Number.isFinite(num) || num <= 0) return "Precio a tratar";
  return CONFIG.simboloMoneda + num.toLocaleString("es-MX");
}

function estadoDe(producto) {
  const e = normalizar(producto.estado);
  if (e === "vendido")  return { clase: "vendido",  texto: "Vendido" };
  if (e === "apartado") return { clase: "apartado", texto: "Apartado" };
  return { clase: "disponible", texto: "Disponible" };
}

function enlaceWhatsApp(producto) {
  const texto = producto
    ? CONFIG.mensaje
        .replace("{producto}", producto.nombre)
        .replace("{precio}", formatearPrecio(producto.precio))
    : CONFIG.mensajeGeneral;

  const numero = String(CONFIG.whatsapp).replace(/\D/g, "");
  return "https://wa.me/" + numero + "?text=" + encodeURIComponent(texto);
}

/* ---------------- Carga del catálogo ---------------- */

async function cargarCatalogo() {
  try {
    const resp = await fetch("products.json", { cache: "no-cache" });
    if (!resp.ok) throw new Error("HTTP " + resp.status);
    const datos = await resp.json();

    // Acepta un arreglo suelto o un objeto { config, productos }
    const lista = Array.isArray(datos) ? datos : (datos.productos || []);
    if (datos && !Array.isArray(datos) && datos.config) {
      Object.assign(CONFIG, datos.config);
    }

    PRODUCTOS = lista
      .filter((p) => p && p.imagen)
      .map((p, i) => ({
        id: p.id || "p" + (i + 1),
        nombre: p.nombre || "Artículo sin nombre",
        categoria: p.categoria || "Varios",
        precio: p.precio,
        descripcion: p.descripcion || "",
        imagen: p.imagen,
        miniatura: p.miniatura || p.imagen,
        estado: p.estado || "disponible",
      }));

    aplicarConfig();
    construirFiltros();
    render();
    abrirDesdeURL();
  } catch (err) {
    console.error(err);
    el.errorCarga.hidden = false;
    el.errorDetalle.textContent =
      location.protocol === "file:"
        ? "Estás abriendo el archivo directamente desde la carpeta. Sube el sitio a GitHub Pages (o usa un servidor local) para que el catálogo cargue."
        : "No se pudo leer products.json. Revisa tu conexión e intenta de nuevo.";
  }
}

function aplicarConfig() {
  el.titulo.textContent = CONFIG.titulo;
  el.subtitulo.textContent = CONFIG.subtitulo;
  document.title = "Catálogo — " + CONFIG.titulo;
  el.waGeneral.href = enlaceWhatsApp(null);
}

/* ---------------- Filtros ---------------- */

function construirFiltros() {
  const cuentas = new Map();
  PRODUCTOS.forEach((p) => cuentas.set(p.categoria, (cuentas.get(p.categoria) || 0) + 1));

  const categorias = ["Todos", ...[...cuentas.keys()].sort((a, b) => a.localeCompare(b, "es"))];

  el.filtros.innerHTML = "";
  categorias.forEach((cat) => {
    const total = cat === "Todos" ? PRODUCTOS.length : cuentas.get(cat);
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chip";
    btn.dataset.categoria = cat;
    btn.setAttribute("aria-pressed", String(cat === categoriaActiva));
    btn.innerHTML = escapar(cat) + ' <span class="cuenta">(' + total + ")</span>";
    btn.addEventListener("click", () => {
      categoriaActiva = cat;
      [...el.filtros.children].forEach((b) =>
        b.setAttribute("aria-pressed", String(b.dataset.categoria === cat))
      );
      render();
      // No movemos la pantalla: los filtros ya estan arriba y saltar marea al usuario.
    });
    el.filtros.appendChild(btn);
  });
}

function filtrar() {
  const q = normalizar(terminoBusqueda).trim();
  const palabras = q ? q.split(/\s+/) : [];

  return PRODUCTOS.filter((p) => {
    if (categoriaActiva !== "Todos" && p.categoria !== categoriaActiva) return false;
    if (!palabras.length) return true;
    const heno = normalizar(p.nombre + " " + p.categoria + " " + p.descripcion);
    return palabras.every((w) => heno.includes(w));
  });
}

/* ---------------- Render ---------------- */

function render() {
  VISIBLES = filtrar();

  el.grid.innerHTML = "";
  const frag = document.createDocumentFragment();

  VISIBLES.forEach((p, i) => {
    const nodo = el.tpl.content.cloneNode(true);
    const card = nodo.querySelector(".card");
    const est = estadoDe(p);

    card.dataset.id = p.id;
    if (est.clase === "vendido") card.classList.add("card--vendido");

    const img = nodo.querySelector(".card-img img");
    img.src = p.miniatura;
    img.alt = p.nombre;

    const badge = nodo.querySelector(".badge");
    badge.textContent = est.texto;
    badge.classList.add("badge--" + est.clase);

    nodo.querySelector(".card-title").textContent = p.nombre;
    nodo.querySelector(".card-desc").textContent = p.descripcion;

    const precio = nodo.querySelector(".card-price");
    precio.innerHTML =
      escapar(formatearPrecio(p.precio)) +
      (p.precio ? ' <span class="moneda">' + escapar(CONFIG.codigoMoneda) + "</span>" : "");

    const boton = nodo.querySelector(".btn-whatsapp");
    if (est.clase === "vendido") {
      boton.removeAttribute("href");
      boton.setAttribute("aria-disabled", "true");
      boton.querySelector(".wa-texto").textContent = "Ya se vendió";
    } else {
      boton.href = enlaceWhatsApp(p);
      boton.setAttribute("aria-label", "Preguntar por " + p.nombre + " en WhatsApp");
      if (est.clase === "apartado") {
        boton.querySelector(".wa-texto").textContent = "Apartado — preguntar igual";
      }
    }

    nodo.querySelector(".card-img").addEventListener("click", () => abrirLightbox(i));

    frag.appendChild(nodo);
  });

  el.grid.appendChild(frag);

  const hay = VISIBLES.length > 0;
  el.vacio.hidden = hay;
  el.contador.textContent = hay
    ? VISIBLES.length + (VISIBLES.length === 1 ? " artículo" : " artículos") +
      (categoriaActiva !== "Todos" ? " en " + categoriaActiva : "") +
      (terminoBusqueda ? ' que coinciden con "' + terminoBusqueda + '"' : "")
    : "";
}

/* ---------------- Visor de imagen ---------------- */

function abrirLightbox(indice) {
  if (indice < 0 || indice >= VISIBLES.length) return;
  const p = VISIBLES[indice];
  indiceLightbox = indice;
  ultimoFoco = document.activeElement;

  el.lbImg.src = p.imagen;
  el.lbImg.alt = p.nombre;
  el.lbTitulo.textContent = p.nombre;
  el.lbPrecio.textContent = formatearPrecio(p.precio);

  const est = estadoDe(p);
  if (est.clase === "vendido") {
    el.lbWhats.removeAttribute("href");
    el.lbWhats.setAttribute("aria-disabled", "true");
  } else {
    el.lbWhats.href = enlaceWhatsApp(p);
    el.lbWhats.removeAttribute("aria-disabled");
  }

  const hayVarios = VISIBLES.length > 1;
  el.lbPrev.hidden = !hayVarios;
  el.lbNext.hidden = !hayVarios;

  el.lb.hidden = false;
  document.body.classList.add("sin-scroll");
  el.lbCerrar.focus();
  history.replaceState(null, "", "#producto=" + encodeURIComponent(p.id));
}

function cerrarLightbox() {
  el.lb.hidden = true;
  el.lbImg.src = "";
  document.body.classList.remove("sin-scroll");
  history.replaceState(null, "", location.pathname + location.search);
  if (ultimoFoco && document.contains(ultimoFoco)) ultimoFoco.focus();
  indiceLightbox = -1;
}

function moverLightbox(paso) {
  if (indiceLightbox < 0) return;
  const total = VISIBLES.length;
  abrirLightbox((indiceLightbox + paso + total) % total);
}

function abrirDesdeURL() {
  const m = location.hash.match(/^#producto=(.+)$/);
  if (!m) return;
  const id = decodeURIComponent(m[1]);
  const i = VISIBLES.findIndex((p) => p.id === id);
  if (i >= 0) abrirLightbox(i);
}

/* ---------------- Tamaño de texto ---------------- */

function aplicarEscala(grande) {
  document.documentElement.style.setProperty("--escala", grande ? "1.2" : "1");
  el.btnTexto.setAttribute("aria-pressed", String(grande));
  try { localStorage.setItem("catalogo:textoGrande", grande ? "1" : "0"); } catch (e) { /* modo privado */ }
}

/* ---------------- Eventos ---------------- */

el.buscador.addEventListener("input", (e) => {
  terminoBusqueda = e.target.value;
  el.limpiar.hidden = terminoBusqueda.length === 0;
  render();
});

el.limpiar.addEventListener("click", () => {
  el.buscador.value = "";
  terminoBusqueda = "";
  el.limpiar.hidden = true;
  el.buscador.focus();
  render();
});

el.verTodo.addEventListener("click", () => {
  el.buscador.value = "";
  terminoBusqueda = "";
  el.limpiar.hidden = true;
  categoriaActiva = "Todos";
  [...el.filtros.children].forEach((b) =>
    b.setAttribute("aria-pressed", String(b.dataset.categoria === "Todos"))
  );
  render();
});

el.btnTexto.addEventListener("click", () => {
  aplicarEscala(el.btnTexto.getAttribute("aria-pressed") !== "true");
});

el.lbCerrar.addEventListener("click", cerrarLightbox);
el.lbPrev.addEventListener("click", () => moverLightbox(-1));
el.lbNext.addEventListener("click", () => moverLightbox(1));
el.lb.addEventListener("click", (e) => { if (e.target === el.lb) cerrarLightbox(); });

document.addEventListener("keydown", (e) => {
  if (el.lb.hidden) return;
  if (e.key === "Escape")     cerrarLightbox();
  if (e.key === "ArrowLeft")  moverLightbox(-1);
  if (e.key === "ArrowRight") moverLightbox(1);
});

// Deslizar con el dedo en el visor (celulares)
let tocoX = null;
el.lb.addEventListener("touchstart", (e) => { tocoX = e.changedTouches[0].clientX; }, { passive: true });
el.lb.addEventListener("touchend", (e) => {
  if (tocoX === null) return;
  const dx = e.changedTouches[0].clientX - tocoX;
  if (Math.abs(dx) > 60) moverLightbox(dx < 0 ? 1 : -1);
  tocoX = null;
}, { passive: true });

// Boton "volver arriba": aparece solo cuando ya bajaste un poco.
window.addEventListener("scroll", () => {
  el.btnArriba.classList.toggle("visible", window.scrollY > 600);
}, { passive: true });

el.btnArriba.addEventListener("click", () => {
  window.scrollTo({ top: 0, behavior: "smooth" });
  el.buscador.focus({ preventScroll: true });
});

/* ---------------- Arranque ---------------- */

try {
  if (localStorage.getItem("catalogo:textoGrande") === "1") aplicarEscala(true);
} catch (e) { /* modo privado */ }

cargarCatalogo();
