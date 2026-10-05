from sqlalchemy.orm import Session
from app import models


def recalculate_cheapest(product_id: int, db: Session) -> None:
    """
    Vuelve a marcar cual es el precio mas barato de un producto.
    Unico lugar donde se decide este criterio (antes estaba duplicado,
    con una diferencia entre prices.py y stores.py).

    Ignora precios en 0 o negativos: se toman como "todavia sin cargar",
    no como el precio real del producto. Si hay empate, todos los
    empatados quedan marcados.
    """
    all_prices = db.query(models.Price).filter(
        models.Price.product_id == product_id
    ).all()
    if not all_prices:
        return

    validos = [p for p in all_prices if p.amount > 0]

    if not validos:
        for p in all_prices:
            p.is_cheapest = 0
        return

    lowest = min(p.amount for p in validos)
    for p in all_prices:
        p.is_cheapest = 1 if (p.amount > 0 and p.amount == lowest) else 0
