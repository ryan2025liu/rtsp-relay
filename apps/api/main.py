"""
[INPUT]: HTTP requests
[OUTPUT]: JSON responses
[POS]: API entrypoint for control plane
[DEPS]: fastapi, pydantic
[PROTOCOL]:
  1. Any route or lifecycle change must update this header and docs/02-api.
  2. Keep this file as thin bootstrap; business logic should move to modules.
"""

from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(
        title="skybrain-rtsp-relay-api",
        version="0.1.0",
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "api"}

    return app


app = create_app()
