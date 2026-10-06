FROM python:3.11-slim

WORKDIR /app

# Copiar solo requirements primero: si el codigo cambia pero las
# dependencias no, Docker reutiliza esta capa y el build es mas rapido.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Sin --reload: esa opcion es para desarrollo local, no para un contenedor.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
