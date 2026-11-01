from datetime import datetime

from app.extensions import db


class Resena(db.Model):
    __tablename__ = "resenas"

    id = db.Column(db.Integer, primary_key=True)

    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    producto = db.relationship("Producto", back_populates="resenas")

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    usuario = db.relationship("Usuario", back_populates="resenas")

    calificacion = db.Column(db.Integer, nullable=False)  # 1 a 5
    comentario = db.Column(db.Text)
    aprobada = db.Column(db.Boolean, default=True, nullable=False)  # moderación admin
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (db.CheckConstraint("calificacion >= 1 AND calificacion <= 5", name="chk_calificacion_rango"),)

    def __repr__(self) -> str:
        return f"<Resena producto={self.producto_id} calificacion={self.calificacion}>"
