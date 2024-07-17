FROM python:3.11-slim-bullseye AS builder

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential tesseract-ocr libtesseract-dev libleptonica-dev poppler-utils \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y build-essential \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/doc /usr/share/man \
    && find /usr/local/lib/python3.11/site-packages -type d -name '__pycache__' -exec rm -rf {} + \
    && find /usr/local/lib/python3.11/site-packages -type d -name 'test' -exec rm -rf {} + \
    && find /usr/local/lib/python3.11/site-packages -type d -name 'tests' -exec rm -rf {} + \
    && find /usr/local/lib/python3.11/site-packages -type d -name 'testing' -exec rm -rf {} + \
    && find /usr/local/lib/python3.11/site-packages -type f \( -name '*.c' -o -name '*.pyx' -o -name '*.pxd' -o -name '*.pyi' -o -name '*.pyc' -o -name '*.pyo' -o -name '*.md' -o -name '*.h' -o -name '*.rst' \) -exec rm -rf {} + \
    && find /usr/local/lib/python3.11/site-packages -type f -name '*LICENSE*' -exec rm -rf {} + \
    && rm -rf /usr/local/lib/python3.11/site-packages/googleapiclient/discovery_cache


COPY . .

FROM python:3.11-slim-bullseye

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m appuser

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

USER appuser

CMD ["uvicorn", "app.main:application", "--host", "0.0.0.0", "--port", "8000"]