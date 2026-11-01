from flask import Blueprint, abort, flash, redirect, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Producto, Resena

resena_bp = Blueprint("resenas", __name__)


@resena_bp.route("/producto/<int:producto_id>/resena", methods=["POST"])
@login_required
def crear(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    calificacion = request.form.get("calificacion", type=int)

    if not calificacion or not (1 <= calificacion <= 5):
        abort(400)

    ya_reseno = Resena.query.filter_by(producto_id=producto.id, usuario_id=current_user.id).first()
    if ya_reseno:
        flash("Ya has dejado una reseña para este producto.", "warning")
        return redirect(url_for("tienda.producto_detalle", slug=producto.slug))

    resena = Resena(
        producto_id=producto.id,
        usuario_id=current_user.id,
        calificacion=calificacion,
        comentario=request.form.get("comentario", "").strip(),
    )
    db.session.add(resena)
    db.session.commit()

    flash("¡Gracias por tu reseña!", "success")
    return redirect(url_for("tienda.producto_detalle", slug=producto.slug))
