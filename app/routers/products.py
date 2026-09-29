from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.auth import get_current_user

router = APIRouter(prefix="/products", tags=["Productos"])


def _get_owned_product(product_id: int, owner_id: int, db: Session) -> models.Product:
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.owner_id == owner_id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


def _get_owned_category(category_id: int, owner_id: int, db: Session) -> models.Category:
    category = db.query(models.Category).filter(
        models.Category.id == category_id,
        models.Category.owner_id == owner_id,
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")
    return category


@router.get("/")
def get_products(
    category: str = None,
    search: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Product).filter(models.Product.owner_id == current_user.id)

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
def get_product_prices(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    product = _get_owned_product(product_id, current_user.id, db)

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


@router.post("/")
def create_product(
    name: str,
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacio")

    category = _get_owned_category(category_id, current_user.id, db)

    existing = db.query(models.Product).filter(
        models.Product.owner_id == current_user.id,
        models.Product.name == name,
        models.Product.category_id == category.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="El producto ya existe en esa categoria")

    product = models.Product(name=name, category_id=category.id, owner_id=current_user.id)
    db.add(product)
    db.commit()
    db.refresh(product)
    return {
        "id": product.id,
        "name": product.name,
        "category_id": product.category_id
    }


@router.put("/{product_id}")
def update_product(
    product_id: int,
    name: str,
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    product = _get_owned_product(product_id, current_user.id, db)

    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacio")

    category = _get_owned_category(category_id, current_user.id, db)

    duplicate = db.query(models.Product).filter(
        models.Product.owner_id == current_user.id,
        models.Product.name == name,
        models.Product.category_id == category.id,
        models.Product.id != product_id
    ).first()
    if duplicate:
        raise HTTPException(status_code=400, detail="Ya existe un producto con ese nombre en esa categoria")

    product.name = name
    product.category_id = category.id
    db.commit()
    db.refresh(product)
    return {
        "id": product.id,
        "name": product.name,
        "category_id": product.category_id
    }


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    product = _get_owned_product(product_id, current_user.id, db)

    db.query(models.Price).filter(
        models.Price.product_id == product_id
    ).delete()

    db.delete(product)
    db.commit()
    return {"mensaje": "Producto eliminado"}
