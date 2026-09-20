from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/stores", tags=["Comercios"])


def _recalculate_cheapest(product_id: int, db: Session) -> None:
    """
    Vuelve a marcar cual es el precio mas barato de un producto.
    Criterio actual: menor 'amount'. Si hay empate, todos los empatados quedan marcados.
    """
    prices = db.query(models.Price).filter(
        models.Price.product_id == product_id
    ).all()
    if not prices:
        return

    lowest = min(p.amount for p in prices)
    for p in prices:
        p.is_cheapest = 1 if p.amount == lowest else 0


@router.get("/", response_model=list[schemas.StoreResponse])
def get_stores(db: Session = Depends(get_db)):
    return db.query(models.Store).order_by(models.Store.number).all()


@router.get("/{store_id}", response_model=schemas.StoreResponse)
def get_store(store_id: int, db: Session = Depends(get_db)):
    store = db.query(models.Store).filter(models.Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Comercio no encontrado")
    return store


@router.get("/{store_id}/prices")
def get_prices_by_store(store_id: int, db: Session = Depends(get_db)):
    """
    Todos los productos que tienen precio en este comercio.
    Cada item indica si este comercio es el mas barato para ese producto y,
    si no lo es, en que comercio y a que precio esta mas barato.
    """
    store = db.query(models.Store).filter(models.Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Comercio no encontrado")

    prices = db.query(models.Price).filter(
        models.Price.store_id == store_id
    ).all()

    result = []
    for price in prices:
        is_cheapest = bool(price.is_cheapest)

        cheapest_store = None
        cheapest_amount = None
        if not is_cheapest:
            best = min(price.product.prices, key=lambda p: p.amount)
            cheapest_store = best.store.name
            cheapest_amount = best.amount

        result.append({
            "product_id": price.product_id,
            "product_name": price.product.name,
            "category": price.product.category.name,
            "amount": price.amount,
            "unit_price": price.unit_price,
            "brand": price.brand,
            "is_cheapest": is_cheapest,
            "cheapest_store": cheapest_store,
            "cheapest_amount": cheapest_amount,
        })
    return {"store": store.name, "prices": result}


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


@router.post("/")
def create_store(
    name: str,
    number: int,
    db: Session = Depends(get_db)
):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacio")

    existing = db.query(models.Store).filter(
        models.Store.number == number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un comercio con ese número")

    store = models.Store(name=name, number=number)
    db.add(store)
    db.commit()
    db.refresh(store)
    return {"id": store.id, "name": store.name, "number": store.number}


@router.put("/{store_id}")
def update_store(
    store_id: int,
    name: str,
    number: int,
    db: Session = Depends(get_db)
):
    store = db.query(models.Store).filter(
        models.Store.id == store_id
    ).first()
    if not store:
        raise HTTPException(status_code=404, detail="Comercio no encontrado")

    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacio")

    duplicate = db.query(models.Store).filter(
        models.Store.number == number,
        models.Store.id != store_id
    ).first()
    if duplicate:
        raise HTTPException(status_code=400, detail="Ya existe un comercio con ese número")

    store.name = name
    store.number = number
    db.commit()
    db.refresh(store)
    return {"id": store.id, "name": store.name, "number": store.number}


@router.delete("/{store_id}")
def delete_store(store_id: int, db: Session = Depends(get_db)):
    store = db.query(models.Store).filter(
        models.Store.id == store_id
    ).first()
    if not store:
        raise HTTPException(status_code=404, detail="Comercio no encontrado")

    # Productos que tenian precio en este comercio: hay que recalcular su "mas barato"
    affected_product_ids = {
        row.product_id
        for row in db.query(models.Price.product_id).filter(
            models.Price.store_id == store_id
        ).all()
    }

    # Eliminar los precios del comercio primero (store_id no admite NULL)
    db.query(models.Price).filter(
        models.Price.store_id == store_id
    ).delete()

    for product_id in affected_product_ids:
        _recalculate_cheapest(product_id, db)

    db.delete(store)
    db.commit()
    return {"mensaje": "Comercio eliminado"}
