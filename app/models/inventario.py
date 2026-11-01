from datetime import date, datetime

from app.extensions import db


class LoteInventario(db.Model):
    """Control de stock por lote/añada, con alertas de stock bajo."""

    __tablename__ = "lotes_inventario"

    id = db.Column(db.Integer, primary_key=True)
    codigo_lote = db.Column(db.String(50), unique=True, nullable=False, index=True)

    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    producto = db.relationship("Producto", back_populates="lotes")

    anada = db.Column(db.Integer)  # año de cosecha/añada (vinos y algunos destilados)
    cantidad_inicial = db.Column(db.Integer, nullable=False)
    cantidad_disponible = db.Column(db.Integer, nullable=False)
    punto_reorden = db.Column(db.Integer, nullable=False, default=10)

    fecha_ingreso = db.Column(db.Date, default=date.today, nullable=False)
    costo_unitario = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def stock_bajo(self) -> bool:
        return self.cantidad_disponible <= self.punto_reorden

    def __repr__(self) -> str:
        return f"<LoteInventario {self.codigo_lote} producto={self.producto_id}>"
