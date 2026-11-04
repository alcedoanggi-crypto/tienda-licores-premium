# Documentación técnica — LicoresPremium

Documento de referencia del sistema: arquitectura, modelo de datos, reglas de
negocio implementadas, endpoints, seguridad y decisiones de diseño.
Complementa al `README.md` (que cubre solo instalación rápida).

---

## 1. Visión general

Tienda virtual B2C de licores premium: catálogo abierto y verificación +18
al registrarse y comprar, ficha de producto con notas de cata y maridaje,
carrito dinámico por AJAX con recomendaciones cruzadas ("compra también"),
checkout con opción de regalo, reseñas de clientes y un panel
administrativo separado con dashboard de ventas.

**Stack:**

| Capa | Tecnología |
|---|---|
| Backend / controladores | Python 3 + Flask (Blueprints) |
| ORM / modelos | SQLAlchemy (Flask-SQLAlchemy) |
| Migraciones | Flask-Migrate (Alembic) |
| Base de datos | PostgreSQL |
| Autenticación | Flask-Login (roles cliente/admin) |
| Vistas | Jinja2 + Bootstrap 5 |
| Gráficos | Chart.js (consumiendo endpoints JSON del panel admin) |
| Carrito | Sesión de Flask (`flask.session`), actualizado por `fetch`/AJAX |

---

## 2. Arquitectura MVC y estructura de carpetas

```
tienda-licores-premium/
├── run.py                     # Punto de entrada (flask run / gunicorn)
├── seed.py                    # Datos de ejemplo para desarrollo
├── config.py                  # Config (lee variables de entorno / .env)
├── requirements.txt
├── .env.example
│
└── app/
    ├── __init__.py             # Application factory: crea la app, registra
    │                             extensiones y blueprints, inyecta el
    │                             contador del carrito a todas las vistas
    ├── extensions.py            # Instancias compartidas: db, migrate, login_manager
    │
    ├── models/                  # (M)
    │   ├── usuario.py             Usuario + RolUsuario (cliente/admin)
    │   ├── categoria.py           Categoria (incluye flag es_accesorio)
    │   ├── marca.py                Marca
    │   ├── producto.py             Producto + ImagenProducto + tabla de
    │   │                             asociación producto_recomendaciones
    │   ├── inventario.py           LoteInventario (por lote/añada)
    │   ├── pedido.py                Pedido + DetallePedido + EstadoPedido
    │   ├── resena.py                 Resena
    │   └── promocion.py                Promocion + TipoPromocion
    │
    ├── controllers/             # (C) — un Blueprint por módulo funcional
    │   ├── auth_controller.py       verificación de edad, registro, login/logout
    │   ├── tienda_controller.py     home, catálogo con filtros, ficha de producto
    │   ├── carrito_controller.py    endpoints AJAX (agregar/actualizar/eliminar)
    │   ├── checkout_controller.py   checkout con regalo + confirmación
    │   ├── resena_controller.py     crear reseña
    │   ├── admin_controller.py      dashboard + CRUD + moderación + promociones
    │   └── errores.py               manejadores 400/403/404/500
    │
    ├── templates/                # (V)
    │   ├── base.html                layout público (navbar/footer condicionales)
    │   ├── partials/                  navbar.html, footer.html, mensajes.html
    │   ├── edad/verificar.html         pantalla de verificación +18
    │   ├── auth/                        login.html, registro.html
    │   ├── tienda/                       home.html, catalogo.html,
    │   │                                   producto_detalle.html, _tarjeta_producto.html
    │   ├── carrito/carrito.html
    │   ├── checkout/                     checkout.html, confirmacion.html
    │   ├── admin/                         base_admin.html (layout propio) +
    │   │                                    dashboard, productos, categorías,
    │   │                                    marcas, inventario, pedidos,
    │   │                                    reseñas, promociones
    │   └── errors/
    │
    ├── static/
    │   ├── css/variables.css        paleta "bar premium" (custom properties)
    │   ├── css/custom.css           navbar, hero, tarjetas de producto,
    │   │                             pantalla de edad, panel admin
    │   ├── js/carrito.js            fetch a /carrito/* + badge dinámico
    │   └── js/admin-charts.js       fetch a /admin/api/* + Chart.js
    │
    └── utils/
        ├── decorators.py            @edad_verificada_requerida, @admin_requerido
        ├── carrito.py                helpers de carrito en sesión
        └── formularios.py            parsear_fecha(), generar_slug()
```

**Por qué esta organización:** el panel administrativo tiene su **propio
layout** (`admin/base_admin.html`, sidebar oscuro con acentos dorados)
completamente separado del layout de la tienda pública (`base.html`,
navbar horizontal) — así se cumple el requerimiento de "panel
administrativo separado" sin duplicar el sistema de login: ambos usan la
misma tabla `usuarios`, pero el rol determina a qué layout entra cada uno.

---

## 3. Modelo de datos

### 3.1 Entidades y relaciones principales

- **Usuario** `1 -- N` **Pedido**
- **Usuario** `1 -- N` **Resena**
- **Categoria** `1 -- N` **Producto**
- **Marca** `1 -- N` **Producto**
- **Producto** `1 -- N` **ImagenProducto** (galería secundaria)
- **Producto** `1 -- N` **LoteInventario** (control por lote/añada)
- **Producto** `1 -- N` **Resena**
- **Producto** `N -- N` **Producto** (autorreferencia, tabla
  `producto_recomendaciones`) → recomendaciones "compra también"
- **Pedido** `1 -- N` **DetallePedido**
- **Categoria** `1 -- N` **Promocion** (alcance opcional de la promoción)

### 3.2 Enums de estado

| Enum | Valores | Dónde vive |
|---|---|---|
| `RolUsuario` | cliente, admin | `usuario.py` |
| `EstadoPedido` | pendiente → pagado → enviado → entregado (o cancelado) | `pedido.py` |
| `TipoPromocion` | porcentaje, monto_fijo | `promocion.py` |

### 3.3 Campos/propiedades calculadas (no columnas)

- `Usuario.es_admin`, `Usuario.edad` → derivados de `rol` / `fecha_nacimiento`.
- `Producto.precio_final` → `precio_oferta` si está definido y es menor que
  `precio`; si no, `precio`.
- `Producto.en_oferta` → bool derivado de la comparación anterior.
- `Producto.stock_total` → suma de `cantidad_disponible` de todos sus lotes.
- `Producto.calificacion_promedio` / `total_resenas` → calculado solo sobre
  reseñas con `aprobada = True` (moderación).
- `LoteInventario.stock_bajo` → `cantidad_disponible <= punto_reorden`.
- `Pedido` no tiene total calculado: `subtotal`, `costo_envio`,
  `costo_empaque_regalo`, `impuesto` y `total` se **guardan como snapshot**
  en el momento del checkout (no se recalculan después), para que el
  histórico de pedidos no cambie si luego se editan precios o impuestos.

---

## 4. Reglas de negocio clave

### 4.1 Verificación de edad (+18)

El catálogo es **público**: portada, catálogo, fichas y carrito se navegan
sin pantalla previa de edad (decisión de producto para no frenar la
conversión). La verificación se exige **al comprar**.

- `app/utils/decorators.py::edad_verificada_requerida` decora solo
  `checkout.*`. Si `session['edad_verificada']` no está activo, redirige a
  `/verificar-edad?siguiente=<ruta original>`.
- `auth_controller.verificar_edad` calcula la edad a partir de la fecha de
  nacimiento ingresada (sin pedir cuenta); si es < 18, muestra un error sin
  activar la sesión; si es ≥ 18, marca `session['edad_verificada'] = True`
  (con `session.permanent = True`) y redirige a `siguiente`.
- El **registro** (`auth_controller.registro`) exige también ser mayor de
  18 años a partir de la fecha de nacimiento real de la cuenta — es una
  segunda verificación, independiente de la del gate de sesión.
- El **login** también marca `session['edad_verificada'] = True`
  automáticamente (si ya tienes cuenta, ya se validó tu edad al
  registrarte).

### 4.2 Carrito basado en sesión (no en base de datos)

`app/utils/carrito.py` guarda el carrito como `{producto_id: cantidad}` en
`flask.session`. Ventajas de este diseño: funciona para visitantes sin
cuenta (pueden navegar y armar el carrito antes de registrarse), y no
ensucia la base de datos con carritos abandonados.

`obtener_items_detallados()` resuelve esas claves contra la tabla
`productos` en cada request (no se cachea precio ni nombre en la sesión),
así que si un producto cambia de precio o se desactiva, el carrito siempre
refleja el estado real. Los productos inactivos se excluyen silenciosamente
del listado.

El carrito solo se vacía (`vaciar_carrito()`) al confirmar un pedido
exitosamente en el checkout.

### 4.3 Precio de oferta

Un producto puede tener `precio` (de lista) y `precio_oferta` (opcional).
`precio_final` / `en_oferta` se calculan comparando ambos — si
`precio_oferta` es `None` o mayor/igual a `precio`, se ignora. Esto evita
tener que "recordar" desactivar una oferta vencida borrando un campo: basta
con vaciar `precio_oferta`.

### 4.4 Recomendaciones "compra también"

Tabla de asociación `producto_recomendaciones` (autorreferencia N a N sobre
`productos`). Se usa en dos lugares:

- **Ficha de producto**: muestra `producto.recomendados` directamente.
- **Carrito**: agrega la unión de los `recomendados` de *todos* los
  productos que están en el carrito (deduplicados por `id`), pensado para
  sugerir accesorios (copas, hielo, mixers) al finalizar la selección, no
  solo al ver un producto puntual.

### 4.5 Checkout: regalo, envío, impuesto y descuento de inventario

`checkout_controller.index` (POST):

1. Verifica que cada producto del carrito tenga stock suficiente
   (`producto.stock_total >= cantidad`) antes de tocar la base de datos; si
   falta stock de cualquier línea, no se crea el pedido.
2. Calcula: `costo_envio` (fijo, `config.COSTO_ENVIO`), `costo_empaque_regalo`
   (`config.COSTO_EMPAQUE_REGALO` si `es_regalo`, si no `0`), `impuesto`
   (`subtotal * config.IVA`), y `total` como la suma de todo.
3. Crea el `Pedido` y sus `DetallePedido` (con `precio_unitario` congelado
   al `precio_final` del momento de la compra).
4. Descuenta inventario **por lote**, tomando primero el lote con
   `fecha_ingreso` más antigua (FIFO), igual que en el proyecto de
   distribución — evita que un mismo producto con varios lotes quede con
   cantidades negativas.
5. Vacía el carrito de sesión y redirige a la página de confirmación.

Si `es_regalo` está marcado, se guarda `mensaje_regalo` (dedicatoria libre)
y se suma el costo de empaque — ambos visibles después en el panel admin al
revisar el pedido.

### 4.6 Reseñas con moderación

Un cliente solo puede reseñar un producto **una vez**
(`resena_controller.crear` verifica que no exista ya una `Resena` de ese
`usuario_id` + `producto_id`). Las reseñas nacen con `aprobada = True` por
defecto (para que el sitio no se vea vacío en una demo), pero el admin
puede des-aprobarlas/eliminarlas desde `/admin/resenas`; `aprobada = False`
es el estado que usaría un flujo de moderación previa a la publicación si
se decide invertir el default en producción.
`calificacion_promedio`/`total_resenas` en `Producto` **solo cuentan
reseñas aprobadas**, así que ocultar una reseña la saca también del
promedio mostrado en el catálogo.

### 4.7 Alertas de stock bajo por lote/añada

A diferencia de un stock único por producto, aquí el control es **por
lote** (`LoteInventario.stock_bajo`), porque cada lote puede tener su
propio `punto_reorden` (por ejemplo, un vino de una añada específica que ya
no se puede reponer igual). El dashboard admin y `/admin/inventario`
listan los lotes en alerta, no productos genéricos.

---

## 5. Roles y control de acceso

Solo dos roles (`RolUsuario`): `cliente` y `admin`. Implementado con
Flask-Login + dos decoradores propios en `app/utils/decorators.py`:

| Decorador | Efecto |
|---|---|
| `@edad_verificada_requerida` | Redirige a `/verificar-edad` si la sesión no pasó el gate de +18. Se usa solo en `checkout.*`. |
| `@admin_requerido` | Redirige a `/login` si no hay sesión; responde 403 si `current_user.rol != admin`. Se usa en **todo** `admin.*`. |
| `@login_required` (Flask-Login) | Se usa en `checkout.*` y `resenas.crear` — comprar y reseñar exige cuenta, aunque navegar el catálogo no. |

El panel admin (`/admin/*`) es inaccesible para un usuario `cliente` aunque
esté logueado — no es solo una cuestión de menú oculto en la UI, el
decorador bloquea la ruta en el backend.

---

## 6. Endpoints principales

| Blueprint | Prefijo | Rutas clave |
|---|---|---|
| `auth` | — | `GET/POST /verificar-edad`, `GET/POST /registro`, `GET/POST /login`, `GET /logout` |
| `tienda` | — | `GET /` (home), `GET /catalogo` (filtros + búsqueda), `GET /producto/<slug>` |
| `carrito` | `/carrito` | `GET /`, `POST /agregar`, `POST /actualizar`, `POST /eliminar`, `GET /resumen` (todas AJAX salvo la vista) |
| `checkout` | `/checkout` | `GET/POST /`, `GET /confirmacion/<pedido_id>` |
| `resenas` | — | `POST /producto/<producto_id>/resena` |
| `admin` | `/admin` | `GET /` (dashboard), `GET /api/productos-mas-vendidos`, `GET /api/ventas-por-categoria`, `GET /api/ingresos-mensuales`, CRUD de `productos`, `categorias`, `marcas`, `inventario`, `pedidos` (+ cambio de estado), `resenas` (aprobar/eliminar), `promociones` |

En total **38 rutas** registradas (verificado con `app.url_map`).

---

## 7. Panel admin: dashboard y gráficos

`admin_controller.dashboard` calcula 4 KPIs (pedidos pendientes, lotes con
stock bajo, reseñas pendientes de moderar, ingresos del mes) y la lista de
lotes críticos. Los 3 gráficos, igual que en la Distribuidora de Licores,
se renderizan en el navegador: `static/js/admin-charts.js` hace `fetch` a
los 3 endpoints JSON del blueprint `admin` y construye los gráficos con
Chart.js en tonos ámbar/dorado:

- **Productos más vendidos**: suma de `DetallePedido.cantidad` agrupada por
  producto (excluye pedidos cancelados), top 8, barra horizontal.
- **Ventas por categoría**: suma de `cantidad × precio_unitario` agrupada
  por `Categoria`, dona.
- **Ingresos mensuales**: suma de `Pedido.total` agrupada por año-mes de
  `fecha_pedido`, últimos 12 meses, línea con relleno degradado.

---

## 8. Diseño UI/UX

Paleta corporativa en `app/static/css/variables.css`:

| Variable | Hex | Uso |
|---|---|---|
| `--ambar-whisky` | `#B8860B` | Acentos, gráficos, botón secundario |
| `--negro-elegante` | `#111111` | Fondo general del sitio |
| `--dorado` | `#D4AF37` | Títulos, bordes, botón primario, precios |
| `--blanco-hueso` | `#F5F1E8` | Texto sobre fondo oscuro |

Tipografía: **Playfair Display** (serif, para nombres de producto y
títulos, buscando el efecto "etiqueta premium") + **Jost** (sans, texto de
cuerpo), cargadas desde Google Fonts en `base.html`/`base_admin.html`.

Piezas de diseño específicas del pedido:

- **`.pantalla-edad`** (verificar.html): fondo con `radial-gradient` cálido
  simulando luz de bar + tarjeta semitransparente con borde dorado.
- **`.hero-premium`** (home.html): mismo recurso de glow radial dorado
  sobre fondo casi negro, tipografía serif grande con una palabra en
  cursiva dorada.
- **`.card-producto .vitrina`**: fondo radial oscuro tipo "vitrina de bar"
  detrás de cada imagen de producto, con `drop-shadow` para que la botella
  "flote".
- **`.admin-sidebar` / `.admin-content`**: layout separado del sitio
  público, sidebar negro con acentos dorados, tarjetas KPI
  (`.kpi-card-admin`) con borde izquierdo dorado (rojo si es de alerta).

### 8.1 Rediseño visual (tema profesional + animaciones)

El rediseño es una **capa** sobre los estilos originales: no cambia rutas,
modelos ni lógica, y los `id`/clases que usa el JavaScript siguen iguales.

| Archivo | Rol |
|---|---|
| `app/static/css/tema-pro.css` | Tema "Cava de autor": botella SVG animada, marquesina, tarjetas de categoría, beneficios, sello 18+ |
| `app/static/css/animaciones.css` | Animaciones reutilizables: `.flotar`, `.brillo`, `.punto-vivo`, `.aparecer-*`, `.revelar` |
| `app/static/js/animaciones.js` | Contadores de KPI (respetan prefijo `$` y decimales) y revelado con `IntersectionObserver` |

Piezas destacadas:

- **Botella SVG** (`tienda/home.html`): forma recortada con `clipPath`, dos olas de licor desplazándose en bucle, burbujas, halo que respira y anillo dorado que gira.
- **Marquesina** de categorías con desplazamiento infinito (se pausa al pasar el mouse).
- **Tarjeta de producto** (`tienda/_tarjeta_producto.html`): zoom y giro leve de la botella, brillo inferior y botón "Ver detalle" al pasar el mouse; la etiqueta "Oferta" late.
- **Panel admin**: mismas animaciones de KPI (contador) y paneles con revelado.

Accesibilidad: todas las animaciones se apagan con
`@media (prefers-reduced-motion: reduce)`, y el contador no se ejecuta en
ese caso (el número real ya viene renderizado desde el servidor, así que sin
JavaScript la página sigue mostrando los valores correctos).

---

## 9. Seguridad y límites conocidos

- **CSRF**: `Flask-WTF` está en `requirements.txt` pero los formularios
  actuales son HTML plano sin `{{ form.csrf_token }}` — pendiente antes de
  producción, igual que en el proyecto de distribución.
- **Contraseñas**: hasheadas con `werkzeug.security` (`generate_password_hash`
  / `check_password_hash`), nunca en texto plano.
- **Verificación de edad**: es una **declaración del usuario** (como en
  cualquier sitio de licores real), no una verificación de identidad — no
  reemplaza controles legales adicionales que pueda exigir cada país.
- **Sesión del carrito**: al ser server-side signed cookie de Flask, el
  contenido no es editable por el cliente sin invalidar la firma, pero
  **si cambia `SECRET_KEY`, todos los carritos activos se pierden** — tenerlo
  en cuenta al rotar la clave en producción.
- Sin paginación en catálogo/listados admin, sin tests automatizados, sin
  pasarela de pago real (el checkout no cobra, solo registra el pedido) —
  mismos límites de alcance que el resto de scaffolds de esta serie.

---

## 10. Validación realizada

Antes de entregar el proyecto se corrió (con un venv temporal, luego
eliminado):

1. `python -m py_compile` sobre todo `app/` + `config.py`/`run.py`/`seed.py`
   → sin errores de sintaxis.
2. `create_app()` + inspección de `app.url_map` → 6 blueprints, 38 rutas,
   sin errores de import.
3. **Gate de edad** (versión original, antes de abrir el catálogo): verificado que `/` sin sesión redirigía a
   `/verificar-edad`; que una fecha de nacimiento de menor de edad rechaza
   sin activar la sesión; que una fecha válida sí la activa y permite ver
   `/catalogo`.
4. **Registro**: creación de cuenta cliente con validación de edad.
5. **Flujo comercial completo** vía `test_client` actuando como dos
   usuarios distintos (admin y cliente): admin crea categoría → marca →
   producto → lote de inventario → cliente verifica edad, se registra, ve
   la ficha del producto, lo agrega al carrito por AJAX (`/carrito/agregar`,
   verificado el JSON de respuesta), actualiza cantidad
   (`/carrito/actualizar`), va a checkout, confirma con "es regalo" +
   mensaje personalizado → se verificó que el total calculado coincide
   exactamente (`subtotal + envío + empaque + IVA`) y que el stock del lote
   se descontó en la cantidad correcta → cliente deja una reseña → admin ve
   el pedido, lo pasa a "pagado", revisa reseñas, ve el dashboard y los 3
   endpoints JSON de gráficos, crea una promoción. Todo pasó sin errores
   500.

---

## 11. Cómo correrlo (resumen — detalle en README.md)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
createdb tienda_licores_premium      # en PostgreSQL
copy .env.example .env               # y completar DATABASE_URL / SECRET_KEY

flask --app run.py db init
flask --app run.py db migrate -m "Esquema inicial"
flask --app run.py db upgrade

python seed.py                       # categorías, marcas, productos, promo de ejemplo
flask --app run.py run --debug       # http://localhost:5000
```
