from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.models import Usuario
from app.models.usuario import RolUsuario
from app.utils.formularios import parsear_fecha

auth_bp = Blueprint("auth", __name__)


def _calcular_edad(fecha_nacimiento: date) -> int:
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))


@auth_bp.route("/verificar-edad", methods=["GET", "POST"])
def verificar_edad():
    siguiente = request.args.get("siguiente") or request.form.get("siguiente") or url_for("tienda.home")

    if session.get("edad_verificada"):
        return redirect(siguiente)

    error = None
    if request.method == "POST":
        fecha_nacimiento = parsear_fecha(request.form.get("fecha_nacimiento"))
        if not fecha_nacimiento:
            error = "Ingresa una fecha de nacimiento válida."
        elif _calcular_edad(fecha_nacimiento) < 18:
            error = "Lo sentimos, debes ser mayor de 18 años para ingresar a este sitio."
        else:
            session["edad_verificada"] = True
            session.permanent = True
            return redirect(siguiente)

    return render_template("edad/verificar.html", error=error, siguiente=siguiente)


@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        fecha_nacimiento = parsear_fecha(request.form.get("fecha_nacimiento"))
        email = request.form.get("email", "").strip().lower()

        error = None
        if not fecha_nacimiento or _calcular_edad(fecha_nacimiento) < 18:
            error = "Debes ser mayor de 18 años para registrarte."
        elif Usuario.query.filter_by(email=email).first():
            error = "Ya existe una cuenta con ese correo."

        if error:
            flash(error, "danger")
            return render_template("auth/registro.html")

        usuario = Usuario(
            nombre_completo=request.form["nombre_completo"].strip(),
            email=email,
            fecha_nacimiento=fecha_nacimiento,
            telefono=request.form.get("telefono", "").strip(),
            direccion=request.form.get("direccion", "").strip(),
            ciudad=request.form.get("ciudad", "").strip(),
            rol=RolUsuario.CLIENTE,
        )
        usuario.set_password(request.form["password"])
        db.session.add(usuario)
        db.session.commit()

        session["edad_verificada"] = True
        login_user(usuario)
        flash(f"¡Bienvenido, {usuario.nombre_completo}!", "success")
        return redirect(url_for("tienda.home"))

    return render_template("auth/registro.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard") if current_user.es_admin else url_for("tienda.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.activo and usuario.check_password(password):
            login_user(usuario, remember=bool(request.form.get("recordar")))
            session["edad_verificada"] = True
            siguiente = request.args.get("next")
            if usuario.es_admin:
                return redirect(siguiente or url_for("admin.dashboard"))
            return redirect(siguiente or url_for("tienda.home"))

        flash("Correo o contraseña incorrectos.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("tienda.home"))
