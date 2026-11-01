"""Carga de datos de ejemplo para desarrollo local.

Uso: python seed.py
"""
from datetime import date, timedelta

from app import create_app
from app.extensions import db
from app.models import Categoria, LoteInventario, Marca, Producto, Promocion, Resena, Usuario
from app.models.promocion import TipoPromocion
from app.models.usuario import RolUsuario
from app.utils.formularios import generar_slug

# Fotos de licores reales, con licencia libre (Wikimedia Commons, CC BY / CC BY-SA).
# Se usan como imágenes ilustrativas de demo — no corresponden a las marcas ficticias del seed.
IMG_WHISKY = "https://upload.wikimedia.org/wikipedia/commons/0/04/Bottle%2C_whisky_%28AM_1482-7%29.jpg"
IMG_RON = "https://upload.wikimedia.org/wikipedia/commons/5/56/Bundaberg_Rum_Bottle.jpg"
IMG_VODKA = "https://upload.wikimedia.org/wikipedia/commons/5/5f/Vodka.jpg"
IMG_VINO = "https://upload.wikimedia.org/wikipedia/commons/7/7e/Red_wine.jpg"
IMG_CERVEZA = "https://upload.wikimedia.org/wikipedia/commons/d/de/Ipa_beer_155_ibus.jpg"
IMG_COPAS = "https://upload.wikimedia.org/wikipedia/commons/0/06/Whisky_glass.jpg"
IMG_HIELO = "https://upload.wikimedia.org/wikipedia/commons/c/c0/Cloudy_ice_cubes.jpg"
IMG_MIXER = "https://upload.wikimedia.org/wikipedia/commons/2/21/Dilution-grenadine.jpg"

app = create_app()

with app.app_context():
    db.create_all()

    if Usuario.query.filter_by(email="admin@licorespremium.com").first():
        print("Los datos de ejemplo ya existen. No se realizaron cambios.")
    else:
        admin = Usuario(
            nombre_completo="Sofía Administradora",
            email="admin@licorespremium.com",
            fecha_nacimiento=date(1990, 5, 12),
            rol=RolUsuario.ADMIN,
        )
        admin.set_password("admin123")

        cliente = Usuario(
            nombre_completo="Diego Cliente",
            email="cliente@licorespremium.com",
            fecha_nacimiento=date(1995, 3, 20),
            rol=RolUsuario.CLIENTE,
            direccion="Av. Reforma 123",
            ciudad="Ciudad Central",
            telefono="3001112233",
        )
        cliente.set_password("cliente123")

        db.session.add_all([admin, cliente])

        categorias = {
            "whisky": Categoria(nombre="Whisky", slug="whisky", descripcion="Whiskies escoceses, irlandeses y bourbon"),
            "ron": Categoria(nombre="Ron", slug="ron", descripcion="Rones añejos y premium"),
            "vodka": Categoria(nombre="Vodka", slug="vodka", descripcion="Vodkas destilados premium"),
            "vinos": Categoria(nombre="Vinos", slug="vinos", descripcion="Vinos tintos, blancos y espumosos"),
            "cervezas": Categoria(nombre="Cervezas Artesanales", slug="cervezas-artesanales", descripcion="Cervecerías artesanales"),
            "accesorios": Categoria(nombre="Accesorios", slug="accesorios", descripcion="Copas, hielo y mixers", es_accesorio=True),
        }
        db.session.add_all(categorias.values())

        marcas = {
            "highland": Marca(nombre="Highland Reserve", pais_origen="Escocia"),
            "canadorada": Marca(nombre="Caña Dorada", pais_origen="República Dominicana"),
            "vallesur": Marca(nombre="Valle Sur", pais_origen="Argentina"),
            "montana": Marca(nombre="Montaña Brew", pais_origen="Estados Unidos"),
            "barware": Marca(nombre="BarWare Co.", pais_origen="México"),
        }
        db.session.add_all(marcas.values())
        db.session.flush()

        p_whisky = Producto(
            sku="WHK-001",
            nombre="Highland Reserve 18 años",
            slug=generar_slug("Highland Reserve 18 años"),
            categoria_id=categorias["whisky"].id,
            marca_id=marcas["highland"].id,
            precio=89.90,
            precio_oferta=74.90,
            costo=45.00,
            origen="Islay, Escocia",
            graduacion_alcoholica=43.0,
            volumen_ml=750,
            notas_cata="Aromas ahumados con notas de turba, vainilla y un toque de miel. En boca es intenso, "
            "con especias dulces y un final largo con recuerdos a roble tostado.",
            maridaje="Ideal para acompañar quesos añejos, chocolate amargo o disfrutar solo, a temperatura ambiente.",
            descripcion="Edición limitada envejecida 18 años en barricas de roble americano.",
            destacado=True,
            imagen_principal=IMG_WHISKY,
        )
        p_ron = Producto(
            sku="RON-001",
            nombre="Caña Dorada Gran Reserva 12 años",
            slug=generar_slug("Caña Dorada Gran Reserva 12 años"),
            categoria_id=categorias["ron"].id,
            marca_id=marcas["canadorada"].id,
            precio=42.50,
            costo=22.00,
            origen="La Romana, República Dominicana",
            graduacion_alcoholica=40.0,
            volumen_ml=750,
            notas_cata="Notas de caramelo, tabaco dulce y fruta madura, con un cuerpo sedoso y final cálido.",
            maridaje="Perfecto para cócteles de autor o para disfrutar en las rocas con una rodaja de naranja.",
            destacado=True,
            imagen_principal=IMG_RON,
        )
        p_vodka = Producto(
            sku="VDK-001",
            nombre="Nieve Ártica Vodka Premium",
            slug=generar_slug("Nieve Artica Vodka Premium"),
            categoria_id=categorias["vodka"].id,
            precio=35.00,
            costo=18.00,
            origen="Polonia",
            graduacion_alcoholica=40.0,
            volumen_ml=750,
            notas_cata="Perfil limpio y cristalino, destilado 5 veces, con un ligero dulzor a grano.",
            maridaje="Base ideal para martinis y cócteles de coctelería de autor.",
            imagen_principal=IMG_VODKA,
        )
        p_vino = Producto(
            sku="VIN-001",
            nombre="Valle Sur Malbec Reserva",
            slug=generar_slug("Valle Sur Malbec Reserva"),
            categoria_id=categorias["vinos"].id,
            marca_id=marcas["vallesur"].id,
            precio=28.00,
            costo=14.00,
            origen="Mendoza, Argentina",
            graduacion_alcoholica=13.5,
            volumen_ml=750,
            notas_cata="Color rojo intenso, aromas a ciruela y mora con notas especiadas de vainilla y roble.",
            maridaje="Excelente con carnes rojas a la parrilla y quesos curados.",
            destacado=True,
            imagen_principal=IMG_VINO,
        )
        p_cerveza = Producto(
            sku="CRV-001",
            nombre="Montaña Brew IPA Artesanal",
            slug=generar_slug("Montana Brew IPA Artesanal"),
            categoria_id=categorias["cervezas"].id,
            marca_id=marcas["montana"].id,
            precio=6.50,
            costo=3.20,
            origen="Colorado, EE.UU.",
            graduacion_alcoholica=6.2,
            volumen_ml=355,
            notas_cata="Amargor cítrico pronunciado con notas resinosas de lúpulo y un final seco.",
            maridaje="Combina bien con comida picante y hamburguesas gourmet.",
            imagen_principal=IMG_CERVEZA,
        )

        p_copas = Producto(
            sku="ACC-001",
            nombre="Set de Copas para Whisky (x2)",
            slug=generar_slug("Set de Copas para Whisky x2"),
            categoria_id=categorias["accesorios"].id,
            marca_id=marcas["barware"].id,
            precio=24.00,
            costo=10.00,
            descripcion="Copas de cristal tipo tumbler, diseñadas para resaltar los aromas del whisky.",
            imagen_principal=IMG_COPAS,
        )
        p_hielo = Producto(
            sku="ACC-002",
            nombre="Esferas de Hielo Reutilizables",
            slug=generar_slug("Esferas de Hielo Reutilizables"),
            categoria_id=categorias["accesorios"].id,
            precio=15.00,
            costo=6.00,
            descripcion="Enfrían sin diluir tu bebida. Set de 4 unidades en acero inoxidable.",
            imagen_principal=IMG_HIELO,
        )
        p_mixer = Producto(
            sku="ACC-003",
            nombre="Mixer Artesanal de Naranja y Especias",
            slug=generar_slug("Mixer Artesanal de Naranja y Especias"),
            categoria_id=categorias["accesorios"].id,
            precio=9.50,
            costo=4.00,
            descripcion="Jarabe artesanal ideal para coctelería con whisky o ron.",
            imagen_principal=IMG_MIXER,
        )

        productos = [p_whisky, p_ron, p_vodka, p_vino, p_cerveza, p_copas, p_hielo, p_mixer]
        db.session.add_all(productos)
        db.session.flush()

        # Recomendaciones "compra también"
        p_whisky.recomendados.extend([p_copas, p_hielo])
        p_ron.recomendados.extend([p_mixer, p_hielo])
        p_vodka.recomendados.append(p_mixer)

        lotes = [
            LoteInventario(codigo_lote="LOT-WHK-01", producto_id=p_whisky.id, cantidad_inicial=25, cantidad_disponible=25, punto_reorden=8, costo_unitario=45.00),
            LoteInventario(codigo_lote="LOT-RON-01", producto_id=p_ron.id, cantidad_inicial=40, cantidad_disponible=40, punto_reorden=10, costo_unitario=22.00),
            LoteInventario(codigo_lote="LOT-VDK-01", producto_id=p_vodka.id, cantidad_inicial=6, cantidad_disponible=6, punto_reorden=10, costo_unitario=18.00),
            LoteInventario(codigo_lote="LOT-VIN-01", producto_id=p_vino.id, anada=2019, cantidad_inicial=50, cantidad_disponible=50, punto_reorden=12, costo_unitario=14.00),
            LoteInventario(codigo_lote="LOT-CRV-01", producto_id=p_cerveza.id, cantidad_inicial=120, cantidad_disponible=120, punto_reorden=30, costo_unitario=3.20),
            LoteInventario(codigo_lote="LOT-ACC-01", producto_id=p_copas.id, cantidad_inicial=30, cantidad_disponible=30, punto_reorden=10, costo_unitario=10.00),
            LoteInventario(codigo_lote="LOT-ACC-02", producto_id=p_hielo.id, cantidad_inicial=30, cantidad_disponible=30, punto_reorden=10, costo_unitario=6.00),
            LoteInventario(codigo_lote="LOT-ACC-03", producto_id=p_mixer.id, cantidad_inicial=40, cantidad_disponible=40, punto_reorden=10, costo_unitario=4.00),
        ]
        db.session.add_all(lotes)

        db.session.add(
            Promocion(
                nombre="Descuento de bienvenida",
                codigo="BIENVENIDO10",
                tipo=TipoPromocion.PORCENTAJE,
                valor=10,
                fecha_inicio=date.today(),
                fecha_fin=date.today() + timedelta(days=60),
            )
        )

        db.session.commit()

        db.session.add(
            Resena(
                producto_id=p_whisky.id,
                usuario_id=cliente.id,
                calificacion=5,
                comentario="Excelente whisky, notas ahumadas increíbles. Llegó muy bien empacado.",
            )
        )
        db.session.commit()

        print("Datos de ejemplo creados correctamente.")
        print("Usuarios de prueba:")
        print("  admin@licorespremium.com / admin123 (admin)")
        print("  cliente@licorespremium.com / cliente123 (cliente)")
