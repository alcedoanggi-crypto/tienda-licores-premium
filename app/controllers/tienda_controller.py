from flask import Blueprint, abort, render_template, request

from app.models import Categoria, Marca, Producto
from app.utils.decorators import edad_verificada_requerida

tienda_bp = Blueprint("tienda", __name__)


@tienda_bp.route("/")
@edad_verificada_requerida
def home():
    destacados = Producto.query.filter_by(activo=True, destacado=True).limit(6).all()
    categorias = Categoria.query.filter_by(es_accesorio=False).order_by(Categoria.nombre).all()
    return render_template("tienda/home.html", destacados=destacados, categorias=categorias)


@tienda_bp.route("/catalogo")
@edad_verificada_requerida
def catalogo():
    busqueda = request.args.get("q", "").strip()
    categoria_id = request.args.get("categoria_id", type=int)
    marca_id = request.args.get("marca_id", type=int)
    precio_min = request.args.get("precio_min", type=float)
    precio_max = request.args.get("precio_max", type=float)
    graduacion_min = request.args.get("graduacion_min", type=float)
    orden = request.args.get("orden", "nombre")

    query = Producto.query.filter_by(activo=True)

    if busqueda:
        like = f"%{busqueda}%"
        query = query.filter(
            (Producto.nombre.ilike(like)) | (Producto.origen.ilike(like)) | (Producto.descripcion.ilike(like))
        )
    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)
    if marca_id:
        query = query.filter_by(marca_id=marca_id)
    if precio_min is not None:
        query = query.filter(Producto.precio >= precio_min)
    if precio_max is not None:
        query = query.filter(Producto.precio <= precio_max)
    if graduacion_min is not None:
        query = query.filter(Producto.graduacion_alcoholica >= graduacion_min)

    if orden == "precio_asc":
        query = query.order_by(Producto.precio.asc())
    elif orden == "precio_desc":
        query = query.order_by(Producto.precio.desc())
    elif orden == "recientes":
        query = query.order_by(Producto.creado_en.desc())
    else:
        query = query.order_by(Producto.nombre.asc())

    productos = query.all()
    categorias = Categoria.query.filter_by(es_accesorio=False).order_by(Categoria.nombre).all()
    marcas = Marca.query.order_by(Marca.nombre).all()

    return render_template(
        "tienda/catalogo.html",
        productos=productos,
        categorias=categorias,
        marcas=marcas,
        filtros={
            "q": busqueda,
            "categoria_id": categoria_id,
            "marca_id": marca_id,
            "precio_min": precio_min,
            "precio_max": precio_max,
            "graduacion_min": graduacion_min,
            "orden": orden,
        },
    )


@tienda_bp.route("/producto/<slug>")
@edad_verificada_requerida
def producto_detalle(slug):
    producto = Producto.query.filter_by(slug=slug, activo=True).first_or_404()
    resenas = [r for r in producto.resenas if r.aprobada]
    resenas.sort(key=lambda r: r.creado_en, reverse=True)
    return render_template("tienda/producto_detalle.html", producto=producto, resenas=resenas)
