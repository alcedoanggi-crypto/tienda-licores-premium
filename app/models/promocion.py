import enum
from datetime import date

from app.extensions import db


class TipoPromocion(str, enum.Enum):
    PORCENTAJE = "porcentaje"
    MONTO_FIJO = "monto_fijo"


class Promocion(db.Model):
    __tablename__ = "promociones"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    codigo = db.Column(db.String(30), unique=True, nullable=False, index=True)
    tipo = db.Column(db.Enum(TipoPromocion, name="tipo_promocion"), nullable=False, default=TipoPromocion.PORCENTAJE)
    valor = db.Column(db.Numeric(12, 2), nullable=False)  # % si tipo=porcentaje, $ si tipo=monto_fijo

    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"))  # opcional: limita el alcance
    categoria = db.relationship("Categoria")

    fecha_inicio = db.Column(db.Date, default=date.today, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    activo = db.Column(db.Boolean, default=True, nullable=False)

    @property
    def vigente(self) -> bool:
        hoy = date.today()
        return self.activo and self.fecha_inicio <= hoy <= self.fecha_fin

    def calcular_descuento(self, monto):
        if self.tipo == TipoPromocion.PORCENTAJE:
            return float(monto) * float(self.valor) / 100
        return min(float(self.valor), float(monto))

    def __repr__(self) -> str:
        return f"<Promocion {self.codigo} {self.tipo.value} {self.valor}>"
