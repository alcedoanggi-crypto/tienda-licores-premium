import random
import string
from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import DetallePedido, LoteInventario, Pedido
from app.utils import carrito as carrito_utils
from app.utils.decorators import edad_verificada_requerida

checkout_bp = Blueprint("checkout", __name__)


def _generar_numero_pedido() -> str:
    sufijo = "".join(random.choices(string.digits, k=6))
    return f"ORD-{datetime.utcnow():%Y%m}-{sufijo}"


@checkout_bp.route("/", methods=["GET", "POST"])
@login_required
@edad_verificada_requerida
def index():
    items = carrito_utils.obtener_items_detallados()
    if not items:
        flash("Tu carrito está vacío.", "warning")
        return redirect(url_for("carrito.ver"))

    subtotal = sum(item["subtotal"] for item in items)

    if request.method == "POST":
        es_regalo = bool(request.form.get("es_regalo"))
        mensaje_regalo = request.form.get("mensaje_regalo", "").strip() if es_regalo else None

        # Verificar stock disponible antes de descontar
        for item in items:
            if item["producto"].stock_total < item["cantidad"]:
                flash(f"Stock insuficiente para {item['producto'].nombre}.", "danger")
                return redirect(url_for("carrito.ver"))

        costo_envio = current_app.config["COSTO_ENVIO"]
        costo_empaque = current_app.config["COSTO_EMPAQUE_REGALO"] if es_regalo else 0
        impuesto = round(subtotal * current_app.config["IVA"], 2)
        total = subtotal + costo_envio + costo_empaque + impuesto

        pedido = Pedido(
            numero_pedido=_generar_numero_pedido(),
            usuario_id=current_user.id,
            direccion_envio=request.form.get("direccion_envio", "").strip() or current_user.direccion,
            ciudad_envio=request.form.get("ciudad_envio", "").strip() or current_user.ciudad,
            telefono_contacto=request.form.get("telefono_contacto", "").strip() or current_user.telefono,
            es_regalo=es_regalo,
            mensaje_regalo=mensaje_regalo,
            subtotal=subtotal,
            costo_envio=costo_envio,
            costo_empaque_regalo=costo_empaque,
            impuesto=impuesto,
            total=total,
        )
        db.session.add(pedido)
        db.session.flush()

        for item in items:
            db.session.add(
                DetallePedido(
                    pedido_id=pedido.id,
                    producto_id=item["producto"].id,
                    cantidad=item["cantidad"],
                    precio_unitario=item["producto"].precio_final,
                )
            )
            # Descuenta stock de los lotes del producto (más antiguo primero)
            pendiente = item["cantidad"]
            lotes = (
                LoteInventario.query.filter(
                    LoteInventario.producto_id == item["producto"].id, LoteInventario.cantidad_disponible > 0
                )
                .order_by(LoteInventario.fecha_ingreso.asc())
                .all()
            )
            for lote in lotes:
                if pendiente <= 0:
                    break
                tomar = min(lote.cantidad_disponible, pendiente)
                lote.cantidad_disponible -= tomar
                pendiente -= tomar

        db.session.commit()
        carrito_utils.vaciar_carrito()

        flash(f"¡Pedido {pedido.numero_pedido} confirmado! Gracias por tu compra.", "success")
        return redirect(url_for("checkout.confirmacion", pedido_id=pedido.id))

    return render_template("checkout/checkout.html", items=items, subtotal=subtotal)


@checkout_bp.route("/confirmacion/<int:pedido_id>")
@login_required
def confirmacion(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    if pedido.usuario_id != current_user.id and not current_user.es_admin:
        from flask import abort

        abort(403)
    return render_template("checkout/confirmacion.html", pedido=pedido)
