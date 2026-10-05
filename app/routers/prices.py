from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.pricing import recalculate_cheapest

router = APIRouter(prefix="/prices", tags=["Precios"])


@router.post("/")
def update_price(
    payload: schemas.PriceUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    product = db.query(models.Product).filter(
        models.Product.id == payload.product_id,
        models.Product.owner_id == current_user.id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    store = db.query(models.Store).filter(
        models.Store.id == payload.store_id,
        models.Store.owner_id == current_user.id,
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

        # Recalcular el precio por kg siempre que se conozca la cantidad,
        # la hayas mandado ahora o ya estuviera guardada de antes.
        if price.quantity:
            price.unit_price = round(price.amount / price.quantity * 1000, 2)
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
    recalculate_cheapest(payload.product_id, db)
    db.commit()

    return {
        "mensaje": "Precio actualizado correctamente",
        "producto": product.name,
        "comercio": store.name,
        "precio_nuevo": payload.amount,
        "precio_anterior": price.previous_amount,
    }
