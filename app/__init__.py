from flask import Flask

from config import Config
from app.extensions import db, login_manager, migrate


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app.models import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    from app.controllers.auth_controller import auth_bp
    from app.controllers.tienda_controller import tienda_bp
    from app.controllers.carrito_controller import carrito_bp
    from app.controllers.checkout_controller import checkout_bp
    from app.controllers.resena_controller import resena_bp
    from app.controllers.admin_controller import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tienda_bp)
    app.register_blueprint(carrito_bp, url_prefix="/carrito")
    app.register_blueprint(checkout_bp, url_prefix="/checkout")
    app.register_blueprint(resena_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    from app.controllers.errores import registrar_manejadores_error

    registrar_manejadores_error(app)

    from app.utils.carrito import contar_items

    @app.context_processor
    def inyectar_globales():
        return {"carrito_cantidad": contar_items()}

    return app
