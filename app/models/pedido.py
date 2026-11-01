import enum
from datetime import datetime

from app.extensions import db


class EstadoPedido(str, enum.Enum):
    PENDIENTE = "pendiente"
    PAGADO = "pagado"
    ENVIADO = "enviado"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"


class Pedido(db.Model):
    __tablename__ = "pedidos"

    id = db.Column(db.Integer, primary_key=True)
    numero_pedido = db.Column(db.String(30), unique=True, nullable=False, index=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    usuario = db.relationship("Usuario", back_populates="pedidos")

    estado = db.Column(db.Enum(EstadoPedido, name="estado_pedido"), nullable=False, default=EstadoPedido.PENDIENTE)
    fecha_pedido = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    direccion_envio = db.Column(db.String(255), nullable=False)
    ciudad_envio = db.Column(db.String(100), nullable=False)
    telefono_contacto = db.Column(db.String(30))

    es_regalo = db.Column(db.Boolean, default=False, nullable=False)
    mensaje_regalo = db.Column(db.Text)

    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    costo_envio = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    costo_empaque_regalo = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    impuesto = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    detalles = db.relationship("DetallePedido", back_populates="pedido", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Pedido {self.numero_pedido} {self.estado.value}>"


class DetallePedido(db.Model):
    __tablename__ = "detalles_pedido"

    id = db.Column(db.Integer, primary_key=True)

    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False)
    pedido = db.relationship("Pedido", back_populates="detalles")

    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    producto = db.relationship("Producto")

    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __repr__(self) -> str:
        return f"<DetallePedido producto={self.producto_id} cant={self.cantidad}>"
