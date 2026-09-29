import re
import unicodedata
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.auth import get_current_user

router = APIRouter(prefix="/categories", tags=["Categorias"])


def _serialize(category: models.Category) -> dict:
    return {
        "id": category.id,
        "code": category.code,
        "name": category.name,
        "product_count": len(category.products),
    }


def _generate_code(name: str, owner_id: int, db: Session) -> str:
    """
    Genera un codigo unico (para ese usuario) a partir del nombre.
    Ejemplo: "Panificados" -> "PAN". Si "PAN" ya existe -> "PAN2", "PAN3", etc.
    """
    without_accents = unicodedata.normalize("NFKD", name)
    letters = re.sub(r"[^A-Za-z]", "", without_accents).upper()
    base = letters[:3] or "CAT"

    code = base
    counter = 2
    while db.query(models.Category).filter(
        models.Category.owner_id == owner_id,
        models.Category.code == code,
    ).first():
        code = f"{base}{counter}"
        counter += 1
    return code


def _name_exists(name: str, owner_id: int, db: Session, exclude_id: Optional[int] = None) -> bool:
    query = db.query(models.Category).filter(
        models.Category.owner_id == owner_id,
        func.lower(models.Category.name) == name.lower(),
    )
    if exclude_id is not None:
        query = query.filter(models.Category.id != exclude_id)
    return query.first() is not None


def _get_owned_category(category_id: int, owner_id: int, db: Session) -> models.Category:
    category = db.query(models.Category).filter(
        models.Category.id == category_id,
        models.Category.owner_id == owner_id,
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")
    return category


@router.get("/")
def get_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    categories = db.query(models.Category).filter(
        models.Category.owner_id == current_user.id
    ).order_by(models.Category.name).all()
    return [_serialize(c) for c in categories]


@router.post("/")
def create_category(
    name: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacio")

    if _name_exists(name, current_user.id, db):
        raise HTTPException(status_code=400, detail="Ya existe una categoria con ese nombre")

    category = models.Category(
        name=name,
        code=_generate_code(name, current_user.id, db),
        owner_id=current_user.id,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return _serialize(category)


@router.put("/{category_id}")
def update_category(
    category_id: int,
    name: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    category = _get_owned_category(category_id, current_user.id, db)

    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacio")

    if _name_exists(name, current_user.id, db, exclude_id=category_id):
        raise HTTPException(status_code=400, detail="Ya existe una categoria con ese nombre")

    category.name = name
    db.commit()
    db.refresh(category)
    return _serialize(category)


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    category = _get_owned_category(category_id, current_user.id, db)

    if category.products:
        raise HTTPException(
            status_code=409,
            detail=(
                f"La categoria tiene {len(category.products)} producto(s). "
                "Movelos a otra categoria o eliminalos antes de borrarla"
            ),
        )

    db.delete(category)
    db.commit()
    return {"mensaje": "Categoria eliminada"}
