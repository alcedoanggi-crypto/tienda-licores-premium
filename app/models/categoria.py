from app.extensions import db


class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)
    descripcion = db.Column(db.String(255))
    imagen = db.Column(db.String(255))
    es_accesorio = db.Column(db.Boolean, default=False, nullable=False)  # copas, hielo, mixers, etc.

    productos = db.relationship("Producto", back_populates="categoria")

    def __repr__(self) -> str:
        return f"<Categoria {self.nombre}>"
