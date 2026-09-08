from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine
from app import models
from app.routers import stores, products, prices

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Super Precios",
    description="Comparador de precios de supermercados",
    version="1.0.0"
)

app.include_router(stores.router)
app.include_router(products.router)
app.include_router(prices.router)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return FileResponse("app/static/index.html")

app.mount("/static", StaticFiles(directory="app/static"), name="static")