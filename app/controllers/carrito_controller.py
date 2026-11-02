from flask import Blueprint, jsonify, render_template, request

from app.models import Producto
from app.utils import carrito as carrito_utils

carrito_bp = Blueprint("carrito", __name__)


@carrito_bp.route("/")
def ver():
    items = carrito_utils.obtener_items_detallados()
    subtotal = sum(item["subtotal"] for item in items)

    # "Compra también": accesorios sugeridos a partir de los productos en el carrito
    recomendados_ids = set()
    for item in items:
        for r in item["producto"].recomendados:
            if r.activo:
                recomendados_ids.add(r.id)
    recomendados = Producto.query.filter(Producto.id.in_(recomendados_ids)).all() if recomendados_ids else []

    return render_template("carrito/carrito.html", items=items, subtotal=subtotal, recomendados=recomendados)


@carrito_bp.route("/agregar", methods=["POST"])
def agregar():
    producto_id = request.form.get("producto_id", type=int)
    cantidad = request.form.get("cantidad", type=int) or 1
    producto = Producto.query.get_or_404(producto_id)

    if not producto.activo:
        return jsonify({"ok": False, "mensaje": "Producto no disponible."}), 400

    carrito_utils.agregar_producto(producto_id, cantidad)
    return jsonify(
        {
            "ok": True,
            "mensaje": f"{producto.nombre} agregado al carrito.",
            "carrito_cantidad": carrito_utils.contar_items(),
            "subtotal": carrito_utils.calcular_subtotal(),
        }
    )


@carrito_bp.route("/actualizar", methods=["POST"])
def actualizar():
    producto_id = request.form.get("producto_id", type=int)
    cantidad = request.form.get("cantidad", type=int) or 0
    carrito_utils.actualizar_cantidad(producto_id, cantidad)
    return jsonify(
        {
            "ok": True,
            "carrito_cantidad": carrito_utils.contar_items(),
            "subtotal": carrito_utils.calcular_subtotal(),
        }
    )


@carrito_bp.route("/eliminar", methods=["POST"])
def eliminar():
    producto_id = request.form.get("producto_id", type=int)
    carrito_utils.eliminar_producto(producto_id)
    return jsonify(
        {
            "ok": True,
            "carrito_cantidad": carrito_utils.contar_items(),
            "subtotal": carrito_utils.calcular_subtotal(),
        }
    )


@carrito_bp.route("/resumen")
def resumen():
    return jsonify({"carrito_cantidad": carrito_utils.contar_items(), "subtotal": carrito_utils.calcular_subtotal()})
