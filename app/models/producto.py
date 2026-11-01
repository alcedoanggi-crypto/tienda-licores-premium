from datetime import datetime

from app.extensions import db

# Autorreferencia para las recomendaciones "compra también" (copas, hielo, mixers, etc.)
producto_recomendaciones = db.Table(
    "producto_recomendaciones",
    db.Column("producto_id", db.Integer, db.ForeignKey("productos.id"), primary_key=True),
    db.Column("recomendado_id", db.Integer, db.ForeignKey("productos.id"), primary_key=True),
)


class Producto(db.Model):
    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(40), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(170), unique=True, nullable=False, index=True)

    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=False)
    categoria = db.relationship("Categoria", back_populates="productos")

    marca_id = db.Column(db.Integer, db.ForeignKey("marcas.id"))
    marca = db.relationship("Marca", back_populates="productos")

    precio = db.Column(db.Numeric(12, 2), nullable=False)
    precio_oferta = db.Column(db.Numeric(12, 2))  # si está definido y < precio, se muestra como promoción
    costo = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    origen = db.Column(db.String(120))  # ej: "Islay, Escocia"
    graduacion_alcoholica = db.Column(db.Numeric(4, 1))  # % vol
    volumen_ml = db.Column(db.Integer, default=750)

    notas_cata = db.Column(db.Text)  # descripción sensorial: aroma, sabor, color
    maridaje = db.Column(db.Text)  # sugerencia de maridaje / consumo

    descripcion = db.Column(db.Text)
    imagen_principal = db.Column(db.String(255))

    destacado = db.Column(db.Boolean, default=False, nullable=False)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    imagenes = db.relationship("ImagenProducto", back_populates="producto", cascade="all, delete-orphan", order_by="ImagenProducto.orden")
    lotes = db.relationship("LoteInventario", back_populates="producto", cascade="all, delete-orphan")
    resenas = db.relationship("Resena", back_populates="producto", cascade="all, delete-orphan")

    recomendados = db.relationship(
        "Producto",
        secondary=producto_recomendaciones,
        primaryjoin=id == producto_recomendaciones.c.producto_id,
        secondaryjoin=id == producto_recomendaciones.c.recomendado_id,
    )

    @property
    def precio_final(self):
        if self.precio_oferta and self.precio_oferta < self.precio:
            return self.precio_oferta
        return self.precio

    @property
    def en_oferta(self) -> bool:
        return bool(self.precio_oferta and self.precio_oferta < self.precio)

    @property
    def stock_total(self) -> int:
        return sum(lote.cantidad_disponible for lote in self.lotes)

    @property
    def calificacion_promedio(self):
        aprobadas = [r for r in self.resenas if r.aprobada]
        if not aprobadas:
            return None
        return round(sum(r.calificacion for r in aprobadas) / len(aprobadas), 1)

    @property
    def total_resenas(self) -> int:
        return len([r for r in self.resenas if r.aprobada])

    def __repr__(self) -> str:
        return f"<Producto {self.sku} {self.nombre}>"


class ImagenProducto(db.Model):
    """Galería de imágenes de un producto (para la vista tipo 'vitrina de bar' / rotación)."""

    __tablename__ = "imagenes_producto"

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    producto = db.relationship("Producto", back_populates="imagenes")

    url = db.Column(db.String(255), nullable=False)
    orden = db.Column(db.Integer, default=1, nullable=False)

    def __repr__(self) -> str:
        return f"<ImagenProducto producto={self.producto_id} orden={self.orden}>"
