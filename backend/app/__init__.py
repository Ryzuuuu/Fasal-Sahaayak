"""Flask application factory."""

from __future__ import annotations

import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pydantic import ValidationError
from werkzeug.middleware.proxy_fix import ProxyFix

from . import chat
from .analysis import analyze_farm
from .catalog import CROPS, DISTRICTS, IRRIGATION_METHODS, SEASONS
from .forecast import ForecastStore
from .schemas import ChatRequest, FarmInput


def _default_config() -> dict:
    origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return {
        "CORS_ORIGINS": [origin.strip() for origin in origins.split(",") if origin.strip()],
        "LLM_API_KEY": os.getenv("LLM_API_KEY", ""),
        "LLM_BASE_URL": os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
        "LLM_MODEL": os.getenv("LLM_MODEL", "llama-3.1-8b-instant"),
        "LLM_MAX_TOKENS": 400,
        "LLM_TIMEOUT_SECONDS": 20,
        "RATELIMIT_ENABLED": True,
        # Set to the number of proxies in front of the app, so rate limits apply per visitor.
        "TRUSTED_PROXIES": int(os.getenv("TRUSTED_PROXIES", "0")),
        "RATELIMIT_STORAGE_URI": "memory://",
        "MAX_CONTENT_LENGTH": 64 * 1024,
    }


def _validation_error(error: ValidationError):
    fields = [
        {"field": ".".join(str(part) for part in issue["loc"]), "message": issue["msg"]}
        for issue in error.errors(include_url=False, include_input=False, include_context=False)
    ]
    return jsonify({"error": "invalid_input", "fields": fields}), 422


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(_default_config())
    app.config.update(overrides or {})
    if app.config["TRUSTED_PROXIES"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=app.config["TRUSTED_PROXIES"])

    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    limiter = Limiter(key_func=get_remote_address, app=app, default_limits=[])
    # Flask-Limiter only registers itself when enabled, and route decorators hold a weak
    # reference, so with limits disabled every request would fail without this.
    app.extensions["rate_limiter"] = limiter
    store = ForecastStore.load()

    app.register_error_handler(ValidationError, _validation_error)

    @app.errorhandler(429)
    def _rate_limited(_error):
        return jsonify({"error": "rate_limited"}), 429

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/api/options")
    def options():
        return jsonify(
            {
                "crops": list(CROPS),
                "seasons": list(SEASONS),
                "districts": DISTRICTS,
                "irrigation_methods": IRRIGATION_METHODS,
                "ai_chat_enabled": bool(app.config["LLM_API_KEY"]),
            }
        )

    @app.get("/api/model-metrics")
    def model_metrics():
        return jsonify(store.metrics)

    @app.post("/api/analyze")
    @limiter.limit("60/minute")
    def analyze():
        farm = FarmInput.model_validate(request.get_json(silent=True) or {})
        return jsonify(analyze_farm(farm, store))

    @app.post("/api/chat")
    @limiter.limit("10/minute;200/day")
    def chat_message():
        body = ChatRequest.model_validate(request.get_json(silent=True) or {})
        # The report is recomputed from validated input, never trusted from the client.
        report = analyze_farm(body.farm, store) if body.farm else None
        messages = [message.model_dump() for message in body.messages]
        return jsonify(chat.reply(app.config, messages, body.language, report))

    return app
