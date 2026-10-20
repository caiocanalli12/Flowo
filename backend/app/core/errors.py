"""Tratamento de erros comum a toda a API."""

import json

from fastapi import FastAPI, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError


async def _validation_error(_request: Request, exc: Exception) -> Response:
    """Mesmo corpo do 422 padrão do FastAPI, serializado em ASCII.

    O 422 ecoa o `input` recebido; se ele tiver um surrogate isolado, o handler
    padrão (UTF-8) quebraria e a resposta viraria 500.
    """
    errors = exc.errors() if isinstance(exc, RequestValidationError) else []
    body = json.dumps({"detail": jsonable_encoder(errors)})
    return Response(
        body, status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, media_type="application/json"
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, _validation_error)
