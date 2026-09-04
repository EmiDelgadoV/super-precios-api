from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/stores", tags=["Comercios"])


@router.get("/", response_model=list[schemas.StoreResponse])
def get_stores(db: Session = Depends(get_db)):
    return db.query(models.Store).order_by(models.Store.number).all()


@router.get("/{store_id}", response_model=schemas.StoreResponse)
def get_store(store_id: int, db: Session = Depends(get_db)):
    store = db.query(models.Store).filter(models.Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Comercio no encontrado")
    return store


@router.get("/{store_id}/best-prices")
def get_best_prices_by_store(store_id: int, db: Session = Depends(get_db)):
    store = db.query(models.Store).filter(models.Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Comercio no encontrado")

    prices = db.query(models.Price).filter(
        models.Price.store_id == store_id,
        models.Price.is_cheapest == 1
    ).all()

    result = []
    for price in prices:
        result.append({
            "product_id": price.product_id,
            "product_name": price.product.name,
            "category": price.product.category.name,
            "amount": price.amount,
            "unit_price": price.unit_price,
            "brand": price.brand,
        })
    return {"store": store.name, "best_prices": result}