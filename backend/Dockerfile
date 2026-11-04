FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY data/climate_normals.csv data/yield_history.csv ./data/
COPY models ./models
COPY wsgi.py .

RUN useradd --create-home appuser
USER appuser

ENV PORT=5000
EXPOSE 5000
# One worker keeps the in-memory rate limits accurate; threads handle concurrent requests.
CMD ["gunicorn", "wsgi:app", "--workers", "1", "--threads", "4", "--timeout", "60"]
