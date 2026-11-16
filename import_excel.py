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
        print("Registrala primero desde la pagina de la app y volve a correr este script")
        db.close()
        return

    # ── COMERCIOS desde hoja L ───────────────────────────
    # Se trae todo lo existente UNA vez y se compara en memoria: contra una base
    # remota cada consulta suelta cuesta un viaje por internet.
    print("Importando comercios...")
    stores = {s.number: s for s in db.query(models.Store).filter_by(owner_id=owner.id).all()}
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
        if numero not in stores:
            store = models.Store(owner_id=owner.id, number=numero, name=str(nombre).strip())
            db.add(store)
            stores[numero] = store
    db.commit()
    stores = {s.number: s for s in db.query(models.Store).filter_by(owner_id=owner.id).all()}
    print(f"  >> {len(stores)} comercios cargados")

    # ── CATEGORÍAS ───────────────────────────────────────
    print("Importando categorías...")
    categories = {c.code: c for c in db.query(models.Category).filter_by(owner_id=owner.id).all()}
    hoja_b = pd.read_excel(EXCEL_PATH, sheet_name="B", header=1)
    codigos = hoja_b.iloc[:, 0].dropna().unique()
    for codigo in codigos:
        codigo = str(codigo).strip().upper()
        if not codigo or codigo in categories:
            continue
        category = models.Category(
            owner_id=owner.id, code=codigo, name=CATEGORY_NAMES.get(codigo, codigo)
        )
        db.add(category)
        categories[codigo] = category
    db.commit()
    categories = {c.code: c for c in db.query(models.Category).filter_by(owner_id=owner.id).all()}
    print(f"  >> {len(categories)} categorias cargadas")

    # ── PRODUCTOS Y PRECIOS desde hoja B ────────────────
    print("Leyendo productos y precios del Excel...")
    filas = []
    for _, row in hoja_b.iterrows():
        try:
            if pd.isna(row.iloc[0]) or pd.isna(row.iloc[1]) or pd.isna(row.iloc[2]):
                continue
            cat_code = str(row.iloc[0]).strip().upper()
            store_num = int(row.iloc[1])
            prod_name = str(row.iloc[2]).strip()
            brand = str(row.iloc[4]).strip() if not pd.isna(row.iloc[4]) else None
            quantity = float(row.iloc[5]) if not pd.isna(row.iloc[5]) else None
            amount = float(row.iloc[8]) if not pd.isna(row.iloc[8]) else None
            unit_price = float(row.iloc[11]) if not pd.isna(row.iloc[11]) else None
            is_cheapest = int(row.iloc[12]) if not pd.isna(row.iloc[12]) else 0
        except (ValueError, TypeError):
            continue

        if amount is None:
            continue
        category = categories.get(cat_code)
        store = stores.get(store_num)
        if not category or not store:
            continue

        filas.append((category, store, prod_name, brand, quantity, amount, unit_price, is_cheapest))

    print(f"  >> {len(filas)} filas validas")

    # Productos: los existentes se traen de una vez; los nuevos se crean y se
    # envian juntos con un solo flush para obtener sus ids.
    products = {
        (p.name, p.category_id): p
        for p in db.query(models.Product).filter_by(owner_id=owner.id).all()
    }
    nuevos = 0
    for category, _store, prod_name, *_ in filas:
        clave = (prod_name, category.id)
        if clave not in products:
            product = models.Product(owner_id=owner.id, name=prod_name, category_id=category.id)
            db.add(product)
            products[clave] = product
            nuevos += 1
    db.flush()
    print(f"  >> {nuevos} productos nuevos")

    # Precios: se evita duplicar los que ya existen (producto + comercio)
    existentes = {
        (pr.product_id, pr.store_id)
        for pr in db.query(models.Price.product_id, models.Price.store_id).all()
    }
    precios_nuevos = 0
    for category, store, prod_name, brand, quantity, amount, unit_price, is_cheapest in filas:
        product = products[(prod_name, category.id)]
        if (product.id, store.id) in existentes:
            continue
        db.add(models.Price(
            product_id=product.id,
            store_id=store.id,
            amount=amount,
            unit_price=unit_price,
            quantity=quantity,
            brand=brand,
            is_cheapest=is_cheapest,
        ))
        existentes.add((product.id, store.id))
        precios_nuevos += 1

    print("Guardando en la base...")
    db.commit()
    print(f"  >> {len(products)} productos en total")
    print(f"  >> {precios_nuevos} precios nuevos")
    db.close()
    print("¡Importación completada!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python import_excel.py tu@mail.com")
        print("(la cuenta tiene que existir: registrala antes desde la pagina de la app)")
    else:
        importar(sys.argv[1])
