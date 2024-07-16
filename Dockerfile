# Etapa 1: Construcción
FROM python:3.11-slim AS builder

WORKDIR /build

# Instalar dependencias del sistema necesarias para la construcción
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    poppler-utils && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Etapa 2: Imagen final
FROM python:3.11-slim

WORKDIR /code

# Copiar solo las dependencias instaladas y el código fuente necesario
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

# Exponer el puerto 8000
EXPOSE 8000

# Crear un usuario no root y usarlo
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /code
USER appuser

# Define el comando para ejecutar la aplicación
ENTRYPOINT ["uvicorn", "app.main:application", "--host", "0.0.0.0", "--port", "8000"]
CMD ["--reload"]