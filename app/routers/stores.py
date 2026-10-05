from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.pricing import recalculate_cheapest

router = APIRouter(prefix="/stores", tags=["Comercios"])


def _get_owned_store(store_id: int, owner_id: int, db: Session) -> models.Store:
    store = db.query(models.Store).filter(
        models.Store.id == store_id,
        models.Store.owner_id == owner_id,
    ).first()
    if not store:
        raise HTTPException(status_code=404, detail="Comercio no encontrado")
    return store


@router.get("/", response_model=list[schemas.StoreResponse])
def get_stores(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.Store).filter(
        models.Store.owner_id == current_user.id
    ).order_by(models.Store.number).all()


@router.get("/{store_id}", response_model=schemas.StoreResponse)
def get_store(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _get_owned_store(store_id, current_user.id, db)


@router.get("/{store_id}/prices")
def get_prices_by_store(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Todos los productos que tienen precio en este comercio.
    Cada item indica si este comercio es el mas barato para ese producto y,
    si no lo es, en que comercio y a que precio esta mas barato.
    """
    store = _get_owned_store(store_id, current_user.id, db)

    prices = db.query(models.Price).filter(
        models.Price.store_id == store.id
    ).all()

    result = []
    for price in prices:
        is_cheapest = bool(price.is_cheapest)

        cheapest_store = None
        cheapest_amount = None
        if not is_cheapest:
            candidatos = [p for p in price.product.prices if p.amount > 0]
            if candidatos:
                best = min(candidatos, key=lambda p: p.amount)
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
def get_best_prices_by_store(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    store = _get_owned_store(store_id, current_user.id, db)

    prices = db.query(models.Price).filter(
        models.Price.store_id == store.id,
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacio")

    existing = db.query(models.Store).filter(
        models.Store.owner_id == current_user.id,
        models.Store.number == number,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un comercio con ese número")

    store = models.Store(name=name, number=number, owner_id=current_user.id)
    db.add(store)
    db.commit()
    db.refresh(store)
    return {"id": store.id, "name": store.name, "number": store.number}


@router.put("/{store_id}")
def update_store(
    store_id: int,
    name: str,
    number: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    store = _get_owned_store(store_id, current_user.id, db)

    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacio")

    duplicate = db.query(models.Store).filter(
        models.Store.owner_id == current_user.id,
        models.Store.number == number,
        models.Store.id != store_id,
    ).first()
    if duplicate:
        raise HTTPException(status_code=400, detail="Ya existe un comercio con ese número")

    store.name = name
    store.number = number
    db.commit()
    db.refresh(store)
    return {"id": store.id, "name": store.name, "number": store.number}


@router.delete("/{store_id}")
def delete_store(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    store = _get_owned_store(store_id, current_user.id, db)

    affected_product_ids = {
        row.product_id
        for row in db.query(models.Price.product_id).filter(
            models.Price.store_id == store.id
        ).all()
    }

    db.query(models.Price).filter(
        models.Price.store_id == store.id
    ).delete()

    for product_id in affected_product_ids:
        recalculate_cheapest(product_id, db)

    db.delete(store)
    db.commit()
    return {"mensaje": "Comercio eliminado"}
