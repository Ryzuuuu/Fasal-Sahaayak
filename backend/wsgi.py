"""WSGI entry point. Development: python wsgi.py. Production: gunicorn wsgi:app."""

import os

from dotenv import load_dotenv

load_dotenv()

# Each request predicts one row, so skip the slow OpenMP thread-pool start on the first request.
os.environ.setdefault("OMP_NUM_THREADS", "1")

from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    app.run(port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
