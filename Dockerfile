FROM python:3.11-slim

WORKDIR /app

# Copiar solo requirements primero: si el codigo cambia pero las
# dependencias no, Docker reutiliza esta capa y el build es mas rapido.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Los servicios de hosting indican el puerto con la variable PORT; si no
# existe (docker compose en tu PC), se usa 8000. Por eso va en forma "sh -c":
# la forma de lista no expande variables.
# Sin --reload: esa opcion es para desarrollo local, no para un contenedor.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
