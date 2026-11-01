from functools import wraps

from flask import abort, redirect, request, session, url_for
from flask_login import current_user


def edad_verificada_requerida(vista):
    """Exige que el visitante haya pasado la verificación de +18 antes de ver el catálogo/carrito/checkout."""

    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not session.get("edad_verificada"):
            return redirect(url_for("auth.verificar_edad", siguiente=request.path))
        return vista(*args, **kwargs)

    return envoltura


def admin_requerido(vista):
    """Restringe una vista al panel administrativo (rol admin)."""

    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login", next=request.path))
        if not current_user.es_admin:
            abort(403)
        return vista(*args, **kwargs)

    return envoltura
