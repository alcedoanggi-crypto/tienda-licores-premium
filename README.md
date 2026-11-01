# LicoresPremium — Tienda Virtual de Licores Premium

Tienda virtual B2C de licores premium: verificación de edad obligatoria,
catálogo con fichas de producto detalladas (origen, graduación alcohólica,
notas de cata, maridaje), carrito dinámico por AJAX con recomendaciones
cruzadas, checkout con opción de regalo, reseñas de productos y panel
administrativo con dashboard de ventas.

## Stack

- **Backend:** Python + Flask (arquitectura MVC)
- **Base de datos:** PostgreSQL + SQLAlchemy (ORM) + Flask-Migrate (Alembic)
- **Autenticación:** Flask-Login (roles cliente/admin, panel admin separado)
- **Vistas:** Jinja2 + Bootstrap 5 + Chart.js
- **Carrito:** basado en sesión de Flask, actualizado vía AJAX (fetch)

## Estructura (MVC)

```
app/
├── models/          # Modelos SQLAlchemy (M)
├── controllers/     # Blueprints de Flask (C)
├── templates/        # Vistas HTML — tienda pública + panel admin separado (V)
├── static/            # CSS (paleta "bar premium") y JS (carrito AJAX + Chart.js)
└── utils/               # Decoradores (edad/admin), carrito en sesión, helpers
config.py
run.py
seed.py                    # Datos de ejemplo para desarrollo
```

## Instalación

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

createdb tienda_licores_premium
cp .env.example .env           # y completar DATABASE_URL / SECRET_KEY

flask --app run.py db init
flask --app run.py db migrate -m "Esquema inicial"
flask --app run.py db upgrade

python seed.py                 # usuarios, categorías, productos y promociones de ejemplo
flask --app run.py run --debug
```

## Usuarios de prueba (creados por `seed.py`)

| Rol    | Email                         | Contraseña   |
|--------|--------------------------------|--------------|
| Admin  | admin@licorespremium.com       | admin123     |
| Cliente| cliente@licorespremium.com     | cliente123   |

## Flujo de la tienda

1. **Verificación de edad** (`/verificar-edad`): pantalla de bienvenida
   estilo "bar oscuro" que exige fecha de nacimiento antes de permitir el
   acceso al catálogo, carrito o checkout. Se guarda en sesión
   (`session['edad_verificada']`); el registro/login también la marca.
2. **Catálogo** (`/catalogo`): filtros por categoría, marca, rango de
   precio, graduación alcohólica mínima y buscador de texto libre.
3. **Ficha de producto** (`/producto/<slug>`): origen, graduación, notas de
   cata, maridaje, disponibilidad, reseñas y recomendaciones "compra
   también" (accesorios como copas, hielo o mixers).
4. **Carrito** (`/carrito`): agregar/actualizar/eliminar vía AJAX sin
   recargar la página; persiste en sesión (funciona sin cuenta).
5. **Checkout** (`/checkout`, requiere cuenta): dirección de envío, opción
   "Es un regalo" con empaque especial y mensaje personalizado, cálculo de
   envío + IVA, descuento de inventario por lote al confirmar.
6. **Panel administrativo** (`/admin`, solo rol `admin`): dashboard con
   KPIs y gráficos Chart.js (productos más vendidos, ventas por categoría,
   ingresos mensuales), CRUD de productos/categorías/marcas, inventario con
   alertas de stock bajo por lote/añada, gestión de pedidos, moderación de
   reseñas y promociones.

## Paleta de diseño

| Color                | Hex       | Uso                                  |
|------------------------|-----------|----------------------------------------|
| Ámbar whisky            | `#B8860B` | Acentos, botones, gráficos             |
| Negro elegante           | `#111111` | Fondo general                          |
| Dorado                    | `#D4AF37` | Títulos, bordes, highlights            |
| Blanco hueso                | `#F5F1E8` | Texto sobre fondo oscuro               |

Tipografía: `Playfair Display` (serif, para títulos tipo etiqueta premium) +
`Jost` (sans, texto de cuerpo). Definida en `app/static/css/variables.css`.
