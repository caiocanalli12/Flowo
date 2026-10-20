# Flowo

Construtor visual de automações, no estilo do n8n, em que os fluxos são exibidos como uma
maquete 3D isométrica. Projeto de portfólio.

> **Status:** fundação. Já existem a API de workflows, o contrato tipado entre backend e frontend
> e a tela inicial. A cena 3D, o editor e as execuções simuladas vêm nas próximas etapas.

## Stack

- **Frontend:** React 19, TypeScript, Vite, Zustand, Vitest
- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic, uv
- **Banco:** PostgreSQL 17
- **Dev:** Docker Compose com hot reload e Makefile

## Pré-requisitos

- [Docker](https://www.docker.com/) com Docker Compose v2 (`docker compose`)
- `make` (opcional: cada alvo é só um comando `docker compose`, veja o `Makefile`)
- Para rodar fora dos containers (opcional): Node.js 22.22+ ou 24.15+ (o container usa Node 24)
  e [uv](https://docs.astral.sh/uv/)

## Como rodar

```bash
make dev
```

Ou, sem make:

```bash
docker compose up --build --renew-anon-volumes
```

Na primeira vez as imagens são construídas e o banco é criado; as migrações rodam sozinhas
quando o backend sobe. O `--renew-anon-volumes` garante que o `node_modules` do container
venha da imagem nova quando as dependências do frontend mudam.

| Serviço | URL |
|---|---|
| Interface | http://localhost:5173 |
| API | http://localhost:8000/api |
| Documentação da API (Swagger) | http://localhost:8000/api/docs |
| Postgres | `127.0.0.1:5432` (usuário/senha/banco `flowo`) |

Para ver a lista com um exemplo, crie um workflow de demonstração (com o stack rodando):

```bash
make seed
```

As portas ficam presas ao `127.0.0.1`: nada fica exposto na rede local.

Para mudar portas ou credenciais, copie `.env.example` para `.env` e ajuste. As credenciais do
Postgres só valem na **primeira** inicialização do volume; para trocá-las depois, recrie o banco
com `docker compose down -v` (isso apaga os dados de desenvolvimento).

> **Linux:** os containers rodam como root, então arquivos que eles criam no repositório
> (ex.: uma migração nova de `make migration`) ficam com dono root. Ajuste com
> `sudo chown -R "$USER" .` depois. No Windows e no macOS (Docker Desktop) isso não acontece.

## Comandos

| Comando | O que faz |
|---|---|
| `make dev` | sobe tudo com hot reload |
| `make up` / `make down` | sobe em segundo plano / derruba |
| `make test` | testes do backend (pytest) e do frontend (Vitest) |
| `make lint` | Ruff, mypy, ESLint, Prettier e checagem de tipos |
| `make format` | formata o código |
| `make types` | regenera o JSON Schema e os tipos TypeScript a partir do Pydantic |
| `make migration name=descricao` | cria uma migração Alembic |
| `make migrate` | aplica as migrações |
| `make seed` | cria um workflow de exemplo |

## API

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/health` | status da API e do banco (503 se o banco cair) |
| `GET` | `/api/workflows` | lista resumida (nome, contagens, datas) |
| `POST` | `/api/workflows` | cria um workflow |
| `GET` | `/api/workflows/{id}` | busca um workflow completo |
| `PUT` | `/api/workflows/{id}` | substitui nome e grafo |
| `DELETE` | `/api/workflows/{id}` | apaga |

## Contrato de dados

Os modelos Pydantic do backend são a fonte única da verdade. `make types` exporta o
JSON Schema para `shared/schema/flowo.schema.json` e gera `frontend/src/api/flowo.gen.ts`.
`make test` falha se algum dos arquivos gerados ficar desatualizado.

## Estrutura

```
backend/    API FastAPI (domínios: workflows, nodes, health), migrações e testes
frontend/   app React (features: health, workflows), tokens de design e testes
shared/     JSON Schema do contrato (gerado)
infra/      scripts de inicialização do Postgres
```

Detalhes de arquitetura e convenções em [CLAUDE.md](CLAUDE.md).
