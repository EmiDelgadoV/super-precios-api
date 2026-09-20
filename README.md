# Super Precios API

Comparador de precios de supermercados. Nace de una planilla Excel real que se usaba para anotar en qué comercio del barrio conviene comprar cada producto, y la convierte en una API con un frontend web pensado para usarse desde el celular.

**Estado: pre-alpha (v0.1.0).** Lo principal funciona, pero faltan piezas (ver "Limitaciones y próximos pasos") y puede haber cambios grandes entre versiones.

## Qué hace

- Registra categorías, productos y comercios, con crear, editar y eliminar en cada sección.
- Guarda un precio por cada producto en cada comercio, con marca, precio por kg y variación respecto del precio anterior.
- Marca automáticamente en qué comercio está más barato cada producto.
- Muestra, para cada comercio, todos los productos con precio ahí, agrupados por categoría, con un filtro para ver solo donde ese comercio es el más barato.
- Permite actualizar un precio eligiendo categoría, producto y comercio, y muestra los precios actuales antes de guardar.

## Stack

- Python, FastAPI y Uvicorn
- SQLAlchemy con SQLite por defecto y PostgreSQL opcional
- Frontend en HTML, CSS y JavaScript puro, servido por la misma API
- pandas y openpyxl para importar datos desde Excel
- pytest y httpx para tests (instalados, todavía sin tests escritos)

## Cómo correrlo en local

Requisitos: Python 3.10 o superior y Git.

```bash
git clone https://github.com/EmiDelgadoV/super-precios-api.git
cd super-precios-api
python -m venv venv
```

Activar el entorno virtual, según el sistema:

```bash
# Windows, PowerShell
venv\Scripts\Activate.ps1

# Windows, Git Bash
source venv/Scripts/activate

# Linux o macOS
source venv/bin/activate
```

Instalar dependencias, cargar los datos del Excel y levantar el servidor:

```bash
pip install -r requirements.txt
python import_excel.py
uvicorn app.main:app --reload
```

Luego abrir:

- Frontend: http://127.0.0.1:8000
- Documentación interactiva de la API: http://127.0.0.1:8000/docs

No hace falta ninguna configuración previa: sin archivo `.env`, la app usa una base SQLite (`superprecios.db`) que se crea sola en la raíz del proyecto.

## Configuración

Las variables se leen desde un archivo `.env` (hay un modelo en `.env.example`).

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | Conexión a la base. Si no se define, usa `sqlite:///./superprecios.db`. Para PostgreSQL: `postgresql+psycopg://usuario:password@localhost:5432/superprecios` |
| `SECRET_KEY` | Reservada para la autenticación futura. Todavía no se usa. |

## Importar datos desde Excel

`import_excel.py` lee `Super25.xlsx`:

- Hoja `L`: comercios (número y nombre).
- Hoja `B`: categorías, productos y precios.

El script se puede ejecutar más de una vez: no duplica comercios, categorías, productos ni precios que ya existan. Con el archivo incluido carga 13 comercios, 19 categorías, 138 productos y 236 precios.

## Cómo funcionan los precios

- Hay un solo precio por cada par producto y comercio. Guardar un precio para un par que ya existe lo reemplaza y conserva el valor anterior para calcular la variación. Los precios del mismo producto en otros comercios no se tocan.
- El precio más barato de un producto es el menor `amount` mayor a cero entre sus precios. Si hay empate, todos los empatados quedan marcados. Se recalcula cada vez que se guarda un precio.
- Eliminar un comercio elimina también sus precios y recalcula el más barato de los productos afectados.
- No se puede eliminar una categoría que todavía tiene productos.

## API

Todas las rutas están documentadas de forma interactiva en `/docs`.

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/categories/` | Lista categorías con su cantidad de productos |
| POST | `/categories/?name=` | Crea una categoría (el código se genera solo) |
| PUT | `/categories/{id}?name=` | Renombra una categoría |
| DELETE | `/categories/{id}` | Elimina una categoría sin productos |
| GET | `/products/` | Lista productos con sus precios (filtros `category` y `search`) |
| GET | `/products/{id}` | Precios de un producto en todos los comercios |
| POST | `/products/?name=&category_id=` | Crea un producto |
| PUT | `/products/{id}?name=&category_id=` | Edita nombre y categoría |
| DELETE | `/products/{id}` | Elimina un producto y sus precios |
| GET | `/stores/` | Lista comercios |
| GET | `/stores/{id}` | Detalle de un comercio |
| GET | `/stores/{id}/prices` | Todos los precios de un comercio, con el más barato de cada producto |
| GET | `/stores/{id}/best-prices` | Solo los productos donde el comercio es el más barato |
| POST | `/stores/?name=&number=` | Crea un comercio |
| PUT | `/stores/{id}?name=&number=` | Edita nombre y número |
| DELETE | `/stores/{id}` | Elimina un comercio y sus precios |
| POST | `/prices/` | Crea o actualiza el precio de un producto en un comercio. Body JSON: `product_id`, `store_id`, `amount`, y opcionalmente `brand` y `quantity` |
| GET | `/health` | Estado del servicio |

## Estructura del proyecto

```
super-precios-api/
├── app/
│   ├── main.py            # App FastAPI y registro de routers
│   ├── database.py        # Conexión y sesión de SQLAlchemy
│   ├── models.py          # Modelos: Category, Product, Store, Price
│   ├── schemas.py         # Schemas de Pydantic
│   ├── routers/
│   │   ├── categories.py
│   │   ├── products.py
│   │   ├── stores.py
│   │   └── prices.py
│   └── static/
│       └── index.html     # Frontend
├── tests/
├── import_excel.py        # Carga inicial desde Excel
├── Super25.xlsx           # Datos de origen
├── requirements.txt
├── .env.example
└── .gitignore
```

## Limitaciones y próximos pasos

Limitaciones conocidas de la versión actual:

- No hay autenticación: cualquiera con acceso a la API puede crear, editar y eliminar datos. Por ahora está pensada para uso local.
- No se puede eliminar un precio individual, solo reemplazarlo.
- Las categorías nuevas usan un ícono por defecto en el frontend.
- Al actualizar un precio sin informar la cantidad, el precio por kg guardado no se recalcula.
- Los endpoints de creación y edición reciben los datos por query string en lugar de un body JSON.
- Todavía no hay tests automatizados.

Próximos pasos:

- Tests con pytest.
- Docker y docker-compose.
- Deploy en Render con PostgreSQL.
- Autenticación con JWT.
- Eliminar precios individuales.
- Consultas en lenguaje natural mediante un LLM.
