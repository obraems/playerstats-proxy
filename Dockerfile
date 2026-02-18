FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Crée un user non-root
RUN useradd -m -u 10001 appuser

# Installe l'app
COPY pyproject.toml /app/
COPY src /app/src

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "playerstats_proxy.main:app", "--host", "0.0.0.0", "--port", "8000"]
