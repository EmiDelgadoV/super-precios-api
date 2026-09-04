from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/products", tags=["Productos"])


@router.get("/", response_model=list[schemas.ProductResponse])
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

    return query.order_by(models.Product.name).all()


@router.get("/categories", response_model=list[schemas.CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).order_by(models.Category.name).all()


@router.get("/{product_id}")
def get_product_prices(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    prices = db.query(models.Price).filter(
        models.Price.product_id == product_id
    ).all()

    prices_data = []
    for price in prices:
        variation = None
        if price.previous_amount and price.previous_amount > 0:
            variation = round(
                ((price.amount - price.previous_amount) / price.previous_amount) * 100, 2
            )
        prices_data.append({
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

    prices_data.sort(key=lambda x: x["amount"])

    return {
        "product_id": product.id,
        "product_name": product.name,
        "category": product.category.name,
        "prices": prices_data
    }