from datetime import date, datetime


def parsear_fecha(valor: str | None) -> date | None:
    """Convierte un input type=date (YYYY-MM-DD) a date; retorna None si viene vacío."""
    if not valor:
        return None
    return datetime.strptime(valor, "%Y-%m-%d").date()


def generar_slug(texto: str) -> str:
    """Slug simple ASCII a partir de un nombre de producto/categoría."""
    import re
    import unicodedata

    normalizado = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalizado).strip("-").lower()
    return slug
