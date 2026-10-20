# Versão do uv fixada para builds reprodutíveis.
FROM ghcr.io/astral-sh/uv:0.13.3-python3.12-trixie-slim

# O venv fica fora de /app: o bind mount do código (docker compose) não o esconde
# e o backend/.venv do host (Windows) é ignorado.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_FROZEN=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências primeiro (inclui o grupo dev: testes e lint rodam no container),
# para que mudanças no código não invalidem esta camada.
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --no-install-project

COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
