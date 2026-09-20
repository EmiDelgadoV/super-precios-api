import re
import unicodedata
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

router = APIRouter(prefix="/categories", tags=["Categorias"])


def _serialize(category: models.Category) -> dict:
    return {
        "id": category.id,
        "code": category.code,
        "name": category.name,
        "product_count": len(category.products),
    }


def _generate_code(name: str, db: Session) -> str:
    """
    Genera un codigo unico a partir del nombre.
    Ejemplo: "Panificados" -> "PAN". Si "PAN" ya existe -> "PAN2", "PAN3", etc.
    """
    without_accents = unicodedata.normalize("NFKD", name)
    letters = re.sub(r"[^A-Za-z]", "", without_accents).upper()
    base = letters[:3] or "CAT"

    code = base
    counter = 2
    while db.query(models.Category).filter(models.Category.code == code).first():
        code = f"{base}{counter}"
        counter += 1
    return code


def _name_exists(name: str, db: Session, exclude_id: Optional[int] = None) -> bool:
    query = db.query(models.Category).filter(
        func.lower(models.Category.name) == name.lower()
    )
    if exclude_id is not None:
        query = query.filter(models.Category.id != exclude_id)
    return query.first() is not None


@router.get("/")
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(models.Category).order_by(models.Category.name).all()
    return [_serialize(c) for c in categories]


@router.post("/")
def create_category(name: str, db: Session = Depends(get_db)):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacio")

    if _name_exists(name, db):
        raise HTTPException(status_code=400, detail="Ya existe una categoria con ese nombre")

    category = models.Category(name=name, code=_generate_code(name, db))
    db.add(category)
    db.commit()
    db.refresh(category)
    return _serialize(category)


@router.put("/{category_id}")
def update_category(category_id: int, name: str, db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")

    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacio")

    if _name_exists(name, db, exclude_id=category_id):
        raise HTTPException(status_code=400, detail="Ya existe una categoria con ese nombre")

    # El codigo no cambia al renombrar: el frontend lo usa para el icono
    category.name = name
    db.commit()
    db.refresh(category)
    return _serialize(category)


@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")

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
