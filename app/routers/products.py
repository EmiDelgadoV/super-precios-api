from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter(prefix="/products", tags=["Productos"])


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    cats = db.query(models.Category).order_by(models.Category.name).all()
    return [{"id": c.id, "code": c.code, "name": c.name} for c in cats]


@router.get("/")
def get_products(
    category: str = None,
    search: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Product)

    if category:
        query = query.join(models.Category).filter(
            models.Category.code == category.upper()
        )

    if search:
        query = query.filter(
            models.Product.name.ilike(f"%{search}%")
        )

    products = query.order_by(models.Product.name).all()

    result = []
    for p in products:
        prices = []
        for price in p.prices:
            variation = None
            if price.previous_amount and price.previous_amount > 0:
                variation = round(
                    ((price.amount - price.previous_amount) / price.previous_amount) * 100, 2
                )
            prices.append({
                "id": price.id,
                "store_id": price.store_id,
                "store_name": price.store.name,
                "amount": price.amount,
                "unit_price": price.unit_price,
                "quantity": price.quantity,
                "brand": price.brand,
                "is_cheapest": price.is_cheapest,
                "previous_amount": price.previous_amount,
                "variation_pct": variation,
                "updated_at": price.updated_at,
            })
        prices.sort(key=lambda x: x["amount"])
        result.append({
            "id": p.id,
            "name": p.name,
            "category": {"id": p.category.id, "code": p.category.code, "name": p.category.name},
            "prices": prices
        })

    return result


@router.get("/{product_id}")
def get_product_prices(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    prices = []
    for price in product.prices:
        variation = None
        if price.previous_amount and price.previous_amount > 0:
            variation = round(
                ((price.amount - price.previous_amount) / price.previous_amount) * 100, 2
            )
        prices.append({
            "store_id": price.store_id,
            "store_name": price.store.name,
            "amount": price.amount,
            "unit_price": price.unit_price,
            "brand": price.brand,
            "quantity": price.quantity,
            "is_cheapest": price.is_cheapest,
            "variation_pct": variation,
            "updated_at": price.updated_at,
        })

    prices.sort(key=lambda x: x["amount"])

    return {
        "product_id": product.id,
        "product_name": product.name,
        "category": product.category.name,
        "prices": prices
    }