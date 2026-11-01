import enum
from datetime import date, datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class RolUsuario(str, enum.Enum):
    CLIENTE = "cliente"
    ADMIN = "admin"


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    rol = db.Column(db.Enum(RolUsuario, name="rol_usuario"), nullable=False, default=RolUsuario.CLIENTE)

    telefono = db.Column(db.String(30))
    direccion = db.Column(db.String(255))
    ciudad = db.Column(db.String(100))

    activo = db.Column(db.Boolean, default=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    pedidos = db.relationship("Pedido", back_populates="usuario")
    resenas = db.relationship("Resena", back_populates="usuario")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def es_admin(self) -> bool:
        return self.rol == RolUsuario.ADMIN

    @property
    def edad(self) -> int:
        hoy = date.today()
        return hoy.year - self.fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )

    def __repr__(self) -> str:
        return f"<Usuario {self.email} ({self.rol.value})>"
