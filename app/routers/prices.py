from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/prices", tags=["Precios"])


@router.post("/")
def update_price(payload: schemas.PriceUpdate, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(
        models.Product.id == payload.product_id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    store = db.query(models.Store).filter(
        models.Store.id == payload.store_id
    ).first()
    if not store:
        raise HTTPException(status_code=404, detail="Comercio no encontrado")

    # Buscar precio existente
    price = db.query(models.Price).filter(
        models.Price.product_id == payload.product_id,
        models.Price.store_id == payload.store_id
    ).first()

    if price:
        # Guardar precio anterior y actualizar
        price.previous_amount = price.amount
        price.amount = payload.amount
        if payload.brand:
            price.brand = payload.brand
        if payload.quantity:
            price.quantity = payload.quantity
            price.unit_price = round(payload.amount / payload.quantity * 1000, 2)
    else:
        # Crear precio nuevo
        unit_price = None
        if payload.quantity:
            unit_price = round(payload.amount / payload.quantity * 1000, 2)
        price = models.Price(
            product_id=payload.product_id,
            store_id=payload.store_id,
            amount=payload.amount,
            brand=payload.brand,
            quantity=payload.quantity,
            unit_price=unit_price,
        )
        db.add(price)

    db.flush()

    # Recalcular cuál es el más barato para este producto
    all_prices = db.query(models.Price).filter(
        models.Price.product_id == payload.product_id,
        models.Price.amount > 0
    ).all()

    if all_prices:
        min_amount = min(p.amount for p in all_prices)
        for p in all_prices:
            p.is_cheapest = 1 if p.amount == min_amount else 0

    db.commit()

    return {
        "mensaje": "Precio actualizado correctamente",
        "producto": product.name,
        "comercio": store.name,
        "precio_nuevo": payload.amount,
        "precio_anterior": price.previous_amount,
    }