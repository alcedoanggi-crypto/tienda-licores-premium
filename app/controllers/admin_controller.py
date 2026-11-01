from datetime import date, datetime, timedelta

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from sqlalchemy import extract, func

from app.extensions import db
from app.models import Categoria, DetallePedido, LoteInventario, Marca, Pedido, Producto, Promocion, Resena
from app.models.pedido import EstadoPedido
from app.models.promocion import TipoPromocion
from app.utils.decorators import admin_requerido
from app.utils.formularios import generar_slug, parsear_fecha

admin_bp = Blueprint("admin", __name__)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@admin_bp.route("/")
@admin_requerido
def dashboard():
    hoy = date.today()
    inicio_mes = hoy.replace(day=1)

    pedidos_pendientes = Pedido.query.filter_by(estado=EstadoPedido.PENDIENTE).count()

    productos = Producto.query.filter_by(activo=True).all()
    stock_bajo = sum(1 for p in productos for lote in p.lotes if lote.stock_bajo)

    ingresos_mes = (
        db.session.query(func.coalesce(func.sum(Pedido.total), 0))
        .filter(Pedido.fecha_pedido >= inicio_mes, Pedido.estado != EstadoPedido.CANCELADO)
        .scalar()
    )

    resenas_pendientes = Resena.query.filter_by(aprobada=False).count()

    lotes_criticos = [lote for p in productos for lote in p.lotes if lote.stock_bajo][:10]

    return render_template(
        "admin/dashboard.html",
        pedidos_pendientes=pedidos_pendientes,
        stock_bajo=stock_bajo,
        ingresos_mes=ingresos_mes,
        resenas_pendientes=resenas_pendientes,
        lotes_criticos=lotes_criticos,
    )


@admin_bp.route("/api/productos-mas-vendidos")
@admin_requerido
def api_productos_mas_vendidos():
    resultados = (
        db.session.query(Producto.nombre, func.coalesce(func.sum(DetallePedido.cantidad), 0))
        .select_from(DetallePedido)
        .join(Pedido, DetallePedido.pedido_id == Pedido.id)
        .join(Producto, DetallePedido.producto_id == Producto.id)
        .filter(Pedido.estado != EstadoPedido.CANCELADO)
        .group_by(Producto.id)
        .order_by(func.sum(DetallePedido.cantidad).desc())
        .limit(8)
        .all()
    )
    return jsonify({"labels": [r[0] for r in resultados], "valores": [int(r[1]) for r in resultados]})


@admin_bp.route("/api/ventas-por-categoria")
@admin_requerido
def api_ventas_por_categoria():
    resultados = (
        db.session.query(Categoria.nombre, func.coalesce(func.sum(DetallePedido.cantidad * DetallePedido.precio_unitario), 0))
        .select_from(DetallePedido)
        .join(Pedido, DetallePedido.pedido_id == Pedido.id)
        .join(Producto, DetallePedido.producto_id == Producto.id)
        .join(Categoria, Producto.categoria_id == Categoria.id)
        .filter(Pedido.estado != EstadoPedido.CANCELADO)
        .group_by(Categoria.id)
        .order_by(func.sum(DetallePedido.cantidad * DetallePedido.precio_unitario).desc())
        .all()
    )
    return jsonify({"labels": [r[0] for r in resultados], "valores": [float(r[1]) for r in resultados]})


@admin_bp.route("/api/ingresos-mensuales")
@admin_requerido
def api_ingresos_mensuales():
    hace_12_meses = datetime.utcnow() - timedelta(days=365)
    resultados = (
        db.session.query(
            extract("year", Pedido.fecha_pedido), extract("month", Pedido.fecha_pedido), func.coalesce(func.sum(Pedido.total), 0)
        )
        .filter(Pedido.fecha_pedido >= hace_12_meses, Pedido.estado != EstadoPedido.CANCELADO)
        .group_by(extract("year", Pedido.fecha_pedido), extract("month", Pedido.fecha_pedido))
        .order_by(extract("year", Pedido.fecha_pedido), extract("month", Pedido.fecha_pedido))
        .all()
    )
    labels = [f"{int(anio)}-{int(mes):02d}" for anio, mes, _ in resultados]
    valores = [float(total) for _, _, total in resultados]
    return jsonify({"labels": labels, "valores": valores})


# ---------------------------------------------------------------------------
# Productos
# ---------------------------------------------------------------------------
@admin_bp.route("/productos")
@admin_requerido
def productos_listar():
    productos = Producto.query.order_by(Producto.nombre).all()
    return render_template("admin/productos_list.html", productos=productos)


@admin_bp.route("/productos/nuevo", methods=["GET", "POST"])
@admin_requerido
def productos_nuevo():
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    marcas = Marca.query.order_by(Marca.nombre).all()

    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        producto = Producto(
            sku=request.form["sku"].strip(),
            nombre=nombre,
            slug=generar_slug(nombre),
            categoria_id=request.form.get("categoria_id", type=int),
            marca_id=request.form.get("marca_id", type=int) or None,
            precio=request.form.get("precio", type=float) or 0,
            precio_oferta=request.form.get("precio_oferta", type=float) or None,
            costo=request.form.get("costo", type=float) or 0,
            origen=request.form.get("origen", "").strip(),
            graduacion_alcoholica=request.form.get("graduacion_alcoholica", type=float),
            volumen_ml=request.form.get("volumen_ml", type=int) or 750,
            notas_cata=request.form.get("notas_cata", "").strip(),
            maridaje=request.form.get("maridaje", "").strip(),
            descripcion=request.form.get("descripcion", "").strip(),
            imagen_principal=request.form.get("imagen_principal", "").strip(),
            destacado=bool(request.form.get("destacado")),
        )
        db.session.add(producto)
        db.session.commit()
        flash(f"Producto {producto.nombre} creado.", "success")
        return redirect(url_for("admin.productos_listar"))

    return render_template("admin/producto_form.html", producto=None, categorias=categorias, marcas=marcas)


@admin_bp.route("/productos/<int:producto_id>/editar", methods=["GET", "POST"])
@admin_requerido
def productos_editar(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    marcas = Marca.query.order_by(Marca.nombre).all()

    if request.method == "POST":
        producto.sku = request.form["sku"].strip()
        producto.nombre = request.form["nombre"].strip()
        producto.categoria_id = request.form.get("categoria_id", type=int)
        producto.marca_id = request.form.get("marca_id", type=int) or None
        producto.precio = request.form.get("precio", type=float) or 0
        producto.precio_oferta = request.form.get("precio_oferta", type=float) or None
        producto.costo = request.form.get("costo", type=float) or 0
        producto.origen = request.form.get("origen", "").strip()
        producto.graduacion_alcoholica = request.form.get("graduacion_alcoholica", type=float)
        producto.volumen_ml = request.form.get("volumen_ml", type=int) or 750
        producto.notas_cata = request.form.get("notas_cata", "").strip()
        producto.maridaje = request.form.get("maridaje", "").strip()
        producto.descripcion = request.form.get("descripcion", "").strip()
        producto.imagen_principal = request.form.get("imagen_principal", "").strip()
        producto.destacado = bool(request.form.get("destacado"))
        producto.activo = bool(request.form.get("activo"))
        db.session.commit()
        flash(f"Producto {producto.nombre} actualizado.", "success")
        return redirect(url_for("admin.productos_listar"))

    return render_template("admin/producto_form.html", producto=producto, categorias=categorias, marcas=marcas)


@admin_bp.route("/productos/<int:producto_id>/eliminar", methods=["POST"])
@admin_requerido
def productos_eliminar(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    producto.activo = False
    db.session.commit()
    flash(f"Producto {producto.nombre} desactivado.", "info")
    return redirect(url_for("admin.productos_listar"))


# ---------------------------------------------------------------------------
# Categorías
# ---------------------------------------------------------------------------
@admin_bp.route("/categorias")
@admin_requerido
def categorias_listar():
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    return render_template("admin/categorias.html", categorias=categorias)


@admin_bp.route("/categorias/nueva", methods=["POST"])
@admin_requerido
def categorias_nueva():
    nombre = request.form["nombre"].strip()
    categoria = Categoria(
        nombre=nombre,
        slug=generar_slug(nombre),
        descripcion=request.form.get("descripcion", "").strip(),
        es_accesorio=bool(request.form.get("es_accesorio")),
    )
    db.session.add(categoria)
    db.session.commit()
    flash(f"Categoría {categoria.nombre} creada.", "success")
    return redirect(url_for("admin.categorias_listar"))


# ---------------------------------------------------------------------------
# Marcas
# ---------------------------------------------------------------------------
@admin_bp.route("/marcas")
@admin_requerido
def marcas_listar():
    marcas = Marca.query.order_by(Marca.nombre).all()
    return render_template("admin/marcas.html", marcas=marcas)


@admin_bp.route("/marcas/nueva", methods=["POST"])
@admin_requerido
def marcas_nueva():
    marca = Marca(
        nombre=request.form["nombre"].strip(),
        pais_origen=request.form.get("pais_origen", "").strip(),
        descripcion=request.form.get("descripcion", "").strip(),
    )
    db.session.add(marca)
    db.session.commit()
    flash(f"Marca {marca.nombre} creada.", "success")
    return redirect(url_for("admin.marcas_listar"))


# ---------------------------------------------------------------------------
# Inventario
# ---------------------------------------------------------------------------
@admin_bp.route("/inventario")
@admin_requerido
def inventario_listar():
    solo_criticos = request.args.get("criticos") == "1"
    lotes = LoteInventario.query.order_by(LoteInventario.fecha_ingreso.desc()).all()
    if solo_criticos:
        lotes = [l for l in lotes if l.stock_bajo]
    return render_template("admin/inventario.html", lotes=lotes, solo_criticos=solo_criticos)


@admin_bp.route("/inventario/nuevo", methods=["GET", "POST"])
@admin_requerido
def inventario_nuevo():
    productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre).all()

    if request.method == "POST":
        cantidad = int(request.form["cantidad_inicial"])
        lote = LoteInventario(
            codigo_lote=request.form["codigo_lote"].strip(),
            producto_id=request.form.get("producto_id", type=int),
            anada=request.form.get("anada", type=int),
            cantidad_inicial=cantidad,
            cantidad_disponible=cantidad,
            punto_reorden=request.form.get("punto_reorden", type=int) or 10,
            costo_unitario=request.form.get("costo_unitario", type=float) or 0,
        )
        db.session.add(lote)
        db.session.commit()
        flash(f"Lote {lote.codigo_lote} registrado.", "success")
        return redirect(url_for("admin.inventario_listar"))

    return render_template("admin/inventario_form.html", productos=productos)


# ---------------------------------------------------------------------------
# Pedidos
# ---------------------------------------------------------------------------
@admin_bp.route("/pedidos")
@admin_requerido
def pedidos_listar():
    estado = request.args.get("estado", "")
    query = Pedido.query
    if estado:
        query = query.filter_by(estado=EstadoPedido(estado))
    pedidos = query.order_by(Pedido.fecha_pedido.desc()).all()
    return render_template("admin/pedidos_list.html", pedidos=pedidos, estado=estado, estados=EstadoPedido)


@admin_bp.route("/pedidos/<int:pedido_id>")
@admin_requerido
def pedidos_detalle(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    return render_template("admin/pedido_detalle.html", pedido=pedido, estados=EstadoPedido)


@admin_bp.route("/pedidos/<int:pedido_id>/estado", methods=["POST"])
@admin_requerido
def pedidos_cambiar_estado(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    pedido.estado = EstadoPedido(request.form.get("estado"))
    db.session.commit()
    flash(f"Pedido {pedido.numero_pedido} actualizado a '{pedido.estado.value}'.", "success")
    return redirect(url_for("admin.pedidos_detalle", pedido_id=pedido.id))


# ---------------------------------------------------------------------------
# Reseñas (moderación)
# ---------------------------------------------------------------------------
@admin_bp.route("/resenas")
@admin_requerido
def resenas_listar():
    resenas = Resena.query.order_by(Resena.creado_en.desc()).all()
    return render_template("admin/resenas.html", resenas=resenas)


@admin_bp.route("/resenas/<int:resena_id>/aprobar", methods=["POST"])
@admin_requerido
def resenas_aprobar(resena_id):
    resena = Resena.query.get_or_404(resena_id)
    resena.aprobada = True
    db.session.commit()
    flash("Reseña aprobada.", "success")
    return redirect(url_for("admin.resenas_listar"))


@admin_bp.route("/resenas/<int:resena_id>/eliminar", methods=["POST"])
@admin_requerido
def resenas_eliminar(resena_id):
    resena = Resena.query.get_or_404(resena_id)
    db.session.delete(resena)
    db.session.commit()
    flash("Reseña eliminada.", "info")
    return redirect(url_for("admin.resenas_listar"))


# ---------------------------------------------------------------------------
# Promociones
# ---------------------------------------------------------------------------
@admin_bp.route("/promociones")
@admin_requerido
def promociones_listar():
    promociones = Promocion.query.order_by(Promocion.fecha_inicio.desc()).all()
    return render_template("admin/promociones.html", promociones=promociones)


@admin_bp.route("/promociones/nueva", methods=["GET", "POST"])
@admin_requerido
def promociones_nueva():
    categorias = Categoria.query.order_by(Categoria.nombre).all()

    if request.method == "POST":
        promocion = Promocion(
            nombre=request.form["nombre"].strip(),
            codigo=request.form["codigo"].strip().upper(),
            tipo=TipoPromocion(request.form.get("tipo", "porcentaje")),
            valor=request.form.get("valor", type=float) or 0,
            categoria_id=request.form.get("categoria_id", type=int) or None,
            fecha_inicio=parsear_fecha(request.form.get("fecha_inicio")) or date.today(),
            fecha_fin=parsear_fecha(request.form.get("fecha_fin")),
        )
        db.session.add(promocion)
        db.session.commit()
        flash(f"Promoción {promocion.codigo} creada.", "success")
        return redirect(url_for("admin.promociones_listar"))

    return render_template("admin/promocion_form.html", categorias=categorias)
