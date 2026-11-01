from app.extensions import db


class Marca(db.Model):
    __tablename__ = "marcas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    pais_origen = db.Column(db.String(80))
    descripcion = db.Column(db.String(255))
    logo = db.Column(db.String(255))

    productos = db.relationship("Producto", back_populates="marca")

    def __repr__(self) -> str:
        return f"<Marca {self.nombre}>"
