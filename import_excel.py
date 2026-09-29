import sys

import pandas as pd
from app.database import SessionLocal, engine
from app import models

models.Base.metadata.create_all(bind=engine)

EXCEL_PATH = "Super25.xlsx"

CATEGORY_NAMES = {
    "SAB": "Sabores y condimentos",
    "LAT": "Latas y conservas",
    "FRU": "Frutas",
    "VEC": "Verduras de raíz",
    "VER": "Verduras de hoja",
    "GLS": "Golosinas",
    "HIG": "Higiene personal",
    "LAC": "Lácteos",
    "BBD": "Bebidas",
    "PAQ": "Paquetes y secos",
    "CRN": "Carnes",
    "LIM": "Limpieza",
    "DYN": "Desayuno",
    "MSC": "Misceláneos",
    "VRS": "Varios",
    "NV":  "Navidad y estacional",
    "VEC": "Verduras",
}


def importar(owner_email: str):
    db = SessionLocal()

    owner = db.query(models.User).filter(models.User.email == owner_email.lower()).first()
    if not owner:
        print(f"No existe ninguna cuenta con el mail {owner_email}")
        print("Registrala primero con POST /auth/register (desde /docs) y volve a correr este script")
        db.close()
        return

    # ── COMERCIOS desde hoja L ───────────────────────────
    print("Importando comercios...")
    hoja_l = pd.read_excel(EXCEL_PATH, sheet_name="L", header=None)
    for _, row in hoja_l.iterrows():
        numero = row[0]
        nombre = row[1]
        if pd.isna(numero) or pd.isna(nombre):
            continue
        try:
            numero = int(numero)
        except (ValueError, TypeError):
            continue
        existente = db.query(models.Store).filter_by(owner_id=owner.id, number=numero).first()
        if not existente:
            db.add(models.Store(owner_id=owner.id, number=numero, name=str(nombre).strip()))
    db.commit()
    print(f"  >> {db.query(models.Store).filter_by(owner_id=owner.id).count()} comercios cargados")

    # ── CATEGORÍAS ───────────────────────────────────────
    print("Importando categorías...")
    hoja_b = pd.read_excel(EXCEL_PATH, sheet_name="B", header=1)
    codigos = hoja_b.iloc[:, 0].dropna().unique()
    for codigo in codigos:
        codigo = str(codigo).strip().upper()
        if not codigo:
            continue
        existente = db.query(models.Category).filter_by(owner_id=owner.id, code=codigo).first()
        if not existente:
            nombre = CATEGORY_NAMES.get(codigo, codigo)
            db.add(models.Category(owner_id=owner.id, code=codigo, name=nombre))
    db.commit()
    print(f"  >> {db.query(models.Category).filter_by(owner_id=owner.id).count()} categorias cargadas")

    # ── PRODUCTOS Y PRECIOS desde hoja B ────────────────
    print("Importando productos y precios...")
    for _, row in hoja_b.iterrows():
        try:
            cat_code  = str(row.iloc[0]).strip().upper()
            store_num = int(row.iloc[1])
            prod_name = str(row.iloc[2]).strip()
            brand     = str(row.iloc[4]).strip() if not pd.isna(row.iloc[4]) else None
            quantity  = float(row.iloc[5]) if not pd.isna(row.iloc[5]) else None
            amount    = float(row.iloc[8]) if not pd.isna(row.iloc[8]) else None
            unit_price= float(row.iloc[11]) if not pd.isna(row.iloc[11]) else None
            is_cheapest = int(row.iloc[12]) if not pd.isna(row.iloc[12]) else 0

            if pd.isna(row.iloc[0]) or pd.isna(row.iloc[1]) or pd.isna(row.iloc[2]):
                continue
            if amount is None:
                continue

            # Buscar categoría y comercio (dentro de los del dueño)
            category = db.query(models.Category).filter_by(owner_id=owner.id, code=cat_code).first()
            store = db.query(models.Store).filter_by(owner_id=owner.id, number=store_num).first()
            if not category or not store:
                continue

            # Buscar o crear producto
            product = db.query(models.Product).filter_by(
                owner_id=owner.id, name=prod_name, category_id=category.id
            ).first()
            if not product:
                product = models.Product(owner_id=owner.id, name=prod_name, category_id=category.id)
                db.add(product)
                db.flush()

            # Crear precio
            precio_existente = db.query(models.Price).filter_by(
                product_id=product.id, store_id=store.id
            ).first()
            if not precio_existente:
                db.add(models.Price(
                    product_id=product.id,
                    store_id=store.id,
                    amount=amount,
                    unit_price=unit_price,
                    quantity=quantity,
                    brand=brand,
                    is_cheapest=is_cheapest,
                ))
        except (ValueError, TypeError):
            continue

    db.commit()
    print(f"  >> {db.query(models.Product).filter_by(owner_id=owner.id).count()} productos cargados")
    print(f"  >> {db.query(models.Price).count()} precios cargados")
    db.close()
    print("¡Importación completada!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python import_excel.py tu@mail.com")
        print("(la cuenta tiene que existir: registrala antes con POST /auth/register desde /docs)")
    else:
        importar(sys.argv[1])
