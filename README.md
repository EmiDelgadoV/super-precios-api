# Super Precios API

Comparador de precios de supermercados. Nace de una planilla Excel real que se usaba para anotar en qué comercio del barrio conviene comprar cada producto, y la convierte en una API multiusuario con un frontend web pensado para usarse desde el celular.

**Estado: pre-alpha, en desarrollo activo.** Cada cuenta ve y administra únicamente sus propios datos. Lo principal funciona y tiene tests automatizados, pero faltan piezas (ver "Limitaciones y próximos pasos").

## Qué hace

- Cuentas de usuario con registro por mail y login, con contraseñas hasheadas y sesión por token (JWT).
- Cada cuenta administra sus propias categorías, productos y comercios, sin ver los de otras cuentas.
- Guarda un precio por cada producto en cada comercio, con marca, precio por kg y variación respecto del precio anterior.
- Marca automáticamente en qué comercio está más barato cada producto.
- Muestra, para cada comercio, todos los productos con precio ahí, agrupados por categoría, con un filtro para ver solo donde ese comercio es el más barato.
- Permite actualizar un precio eligiendo categoría, producto y comercio, mostrando los precios actuales antes de guardar.

## Stack

- Python, FastAPI y Uvicorn
- SQLAlchemy con SQLite para desarrollo local y PostgreSQL para Docker/producción
- Autenticación con JWT y contraseñas hasheadas con bcrypt
- Frontend en HTML, CSS y JavaScript puro, servido por la misma API
- pandas y openpyxl para importar datos desde Excel
- pytest y httpx, con tests automatizados cubriendo autenticación, categorías, productos, comercios y precios
- Docker y docker-compose para correr la API junto con PostgreSQL

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

Instalar dependencias y levantar el servidor:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Luego abrir:

- Frontend: http://127.0.0.1:8000 (pide crear una cuenta o iniciar sesión antes de mostrar nada)
- Documentación interactiva de la API: http://127.0.0.1:8000/docs

Sin archivo `.env`, la app usa una base SQLite (`superprecios.db`) que se crea sola en la raíz del proyecto.

### Primer uso: crear tu cuenta y cargar datos

1. En `/docs`, ejecutar `POST /auth/register` con tu mail y una contraseña (mínimo 8 caracteres).
2. Importar los datos del Excel bajo esa cuenta:

```bash
python import_excel.py tu-mail@ejemplo.com
```

3. Abrir el frontend e iniciar sesión con ese mismo mail y contraseña.

Cada cuenta que se registre arranca sin datos propios. Para que otra persona (por ejemplo, un familiar) vea los mismos productos y comercios, hay que repetir el paso 2 con su mail, una vez que su cuenta ya esté registrada.

## Cómo correrlo con Docker

Requisito: Docker Desktop instalado y corriendo.

Copiar `.env.example` como `.env` y completar `SECRET_KEY` (cualquier texto largo y random) y `POSTGRES_PASSWORD` (la contraseña que va a tener la base de Postgres dentro de los contenedores). `DATABASE_URL` no hace falta tocarla: `docker-compose.yml` la pisa con la conexión a Postgres.

```bash
docker compose up --build
```

La primera vez tarda, porque descarga la imagen de PostgreSQL y construye la propia. Cuando el log diga `Application startup complete`, está listo:

- Frontend: http://localhost:8000
- Documentación interactiva: http://localhost:8000/docs

El primer uso es igual que en local (registrar cuenta e importar datos), pero el import se corre dentro del contenedor, porque ahí es donde tiene acceso a la base:

```bash
docker compose exec api python import_excel.py tu-mail@ejemplo.com
```

Esta base de Postgres es independiente de la SQLite que usa el modo local: son dos bases distintas, así que las cuentas y datos no se comparten entre un modo y el otro.

Otros comandos útiles:

| Comando | Para qué |
|---|---|
| `docker compose up -d --build` | Levantar todo en segundo plano |
| `docker compose logs -f api` | Ver los logs de la API en vivo |
| `docker compose down` | Parar todo (los datos de Postgres quedan guardados) |
| `docker compose down -v` | Parar todo y borrar los datos de Postgres |

## Tests

```bash
pytest tests/ -v
```

Cada test corre contra una base SQLite temporal, separada de `superprecios.db`, así que no hace falta Docker ni tocar tus datos reales para correrlos.

## Configuración

Las variables se leen desde un archivo `.env` (hay un modelo en `.env.example`).

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | Conexión a la base. Si no se define, usa `sqlite:///./superprecios.db`. Para PostgreSQL: `postgresql+psycopg://usuario:password@localhost:5432/superprecios` |
| `SECRET_KEY` | Clave con la que se firman los tokens de sesión. **Tiene que ser secreta y distinta en cada entorno.** Si no se define, se usa un valor de desarrollo que no debe usarse en producción. `.env` nunca se sube al repositorio. |
| `POSTGRES_PASSWORD` | Solo la usa `docker-compose.yml`, para la base de PostgreSQL dentro de los contenedores. No afecta al modo local sin Docker. |

## Importar datos desde Excel

`import_excel.py` lee `Super25.xlsx` y carga todo bajo la cuenta que se le indique como argumento:

```bash
python import_excel.py tu-mail@ejemplo.com
```

La cuenta tiene que existir de antes (registrada con `POST /auth/register`). El script lee:

- Hoja `L`: comercios (número y nombre).
- Hoja `B`: categorías, productos y precios.

Se puede ejecutar más de una vez para la misma cuenta: no duplica comercios, categorías, productos ni precios que ya existan. Con el archivo incluido carga 13 comercios, 19 categorías, 138 productos y 236 precios.

## Cómo funciona la autenticación

- El registro (`POST /auth/register`) guarda el mail en minúsculas y la contraseña procesada con bcrypt, que aplica un salt automático: nunca se guarda la contraseña original.
- El login (`POST /auth/login`) devuelve un token JWT válido por 7 días.
- Todas las demás rutas (categorías, productos, comercios, precios) exigen ese token en el header `Authorization: Bearer <token>` y devuelven 401 sin él o si venció.
- Cada categoría, producto y comercio pertenece a la cuenta que lo creó. Un usuario no puede ver ni modificar los datos de otra cuenta, ni siquiera conociendo el ID exacto.

## Cómo funcionan los precios

- Hay un solo precio por cada par producto y comercio, dentro de una misma cuenta. Guardar un precio para un par que ya existe lo reemplaza y conserva el valor anterior para calcular la variación. Los precios del mismo producto en otros comercios no se tocan.
- El precio más barato de un producto es el menor `amount` mayor a cero entre sus precios. Si hay empate, todos los empatados quedan marcados. Se recalcula cada vez que se guarda un precio.
- Eliminar un comercio elimina también sus precios y recalcula el más barato de los productos afectados.
- No se puede eliminar una categoría que todavía tiene productos.

## API

Todas las rutas están documentadas de forma interactiva en `/docs`. Las que no son de `/auth/` requieren estar logueado.

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/auth/register` | Crea una cuenta (mail + contraseña) |
| POST | `/auth/login` | Devuelve un token de sesión |
| GET | `/auth/me` | Datos de la cuenta logueada |
| GET | `/categories/` | Lista las categorías del usuario, con su cantidad de productos |
| POST | `/categories/?name=` | Crea una categoría (el código se genera solo) |
| PUT | `/categories/{id}?name=` | Renombra una categoría |
| DELETE | `/categories/{id}` | Elimina una categoría sin productos |
| GET | `/products/` | Lista productos del usuario con sus precios (filtros `category` y `search`) |
| GET | `/products/{id}` | Precios de un producto en todos los comercios |
| POST | `/products/?name=&category_id=` | Crea un producto |
| PUT | `/products/{id}?name=&category_id=` | Edita nombre y categoría |
| DELETE | `/products/{id}` | Elimina un producto y sus precios |
| GET | `/stores/` | Lista comercios del usuario |
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
│   ├── models.py          # Modelos: User, Category, Product, Store, Price
│   ├── schemas.py         # Schemas de Pydantic
│   ├── auth.py            # Hashing de contraseñas y manejo de JWT
│   ├── routers/
│   │   ├── auth.py
│   │   ├── categories.py
│   │   ├── products.py
│   │   ├── stores.py
│   │   └── prices.py
│   └── static/
│       └── index.html     # Frontend (login/registro + app)
├── tests/
│   ├── conftest.py         # Base de datos temporal y usuario logueado, para todos los tests
│   ├── test_categories.py
│   ├── test_products.py
│   ├── test_stores.py
│   ├── test_prices.py
│   └── test_seguridad.py   # Aislamiento entre cuentas
├── import_excel.py        # Carga inicial desde Excel, bajo una cuenta
├── Super25.xlsx           # Datos de origen
├── Dockerfile
├── docker-compose.yml      # API + PostgreSQL
├── .dockerignore
├── requirements.txt
├── .env.example
└── .gitignore
```

## Limitaciones y próximos pasos

Limitaciones conocidas de la versión actual:

- No hay recuperación de contraseña ni verificación de mail.
- No hay forma de compartir datos entre dos cuentas (por ejemplo, entre familiares): cada una arranca vacía y hay que importarle los datos por separado.
- No se puede eliminar un precio individual, solo reemplazarlo.
- Las categorías nuevas usan un ícono por defecto en el frontend.
- Los endpoints de creación y edición reciben los datos por query string en lugar de un body JSON.
- Sin límite de intentos de login (importante antes de compartir la URL con más gente, no para uso local).

Próximos pasos:

- Deploy en un servicio como Render, con PostgreSQL.
- Eliminar precios individuales.
- Función "viaje de compras": dada una lista de productos, sugerir en qué comercio conviene comprar la mayoría al mejor precio.
- Integración con IA (llm-secure-api + Gemini) para pedir el viaje de compras en lenguaje natural.
