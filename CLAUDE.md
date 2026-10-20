# Flowo — guia do projeto

Flowo é um projeto de portfólio: um construtor visual de automações no estilo do n8n, em que
os fluxos são exibidos como uma **maquete 3D isométrica**. Este arquivo registra a visão, as
decisões de arquitetura, os comandos e as convenções. Leia antes de qualquer mudança.

## Visão do produto

- Cada workflow é um grafo de nós (passos) ligados por arestas (conexões entre portas).
- A cena será 3D isométrica: cada nó é uma pequena construção cinza sobre uma grade; **só as luzes
  têm cor**, uma por tipo de nó. Verde = sucesso, vermelho = falha.
- As execuções serão **simuladas**: cada tipo de nó terá uma interface de executor e uma
  implementação mock, trocável depois por uma real sem mudar o resto do sistema.
- Visual minimalista e profissional, inspirado no n8n: fundo cinza escuro, grade cinza mais clara.

### Tipos de nó (`NodeType`)

| Tipo | Papel | Portas (entrada → saída) | Luz |
|---|---|---|---|
| `manual_trigger` | gatilho (botão Executar) | — → `out` | gatilho `#FB923C` |
| `webhook` | gatilho | — → `out` | gatilho |
| `schedule` | gatilho | — → `out` | gatilho |
| `http_request` | ação | `in` → `out` | HTTP `#6366F1` |
| `python_script` | ação | `in` → `out` | Python `#38BDF8` |
| `js_script` | ação | `in` → `out` | JavaScript `#FACC15` |
| `email` | ação (Gmail) | `in` → `out` | e-mail `#F472B6` |
| `condition` | lógica (if/else) | `in` → `true` / `false` | condicional `#E5E7EB` |
| `llm` | ação | `in` → `out` | LLM `#A855F7` |

As portas vêm de `backend/app/domains/nodes/catalog.py` (`NODE_SPECS`).

## Estado atual

**Etapa 1 — fundação (concluída):** monorepo, Docker Compose com hot reload, API com health e CRUD
de workflows no Postgres, contrato Pydantic → JSON Schema → tipos TS, design tokens, tela inicial
com indicador de conexão e lista de workflows, testes nos dois lados.

**Ainda NÃO existe (não implemente sem pedido explícito):** cena 3D, editor de fluxo,
execução de nós, WebSocket, colaboração, autenticação, papéis, i18n real.

## Roadmap (futuro)

- Cena 3D: Three.js via `@react-three/fiber` + `drei`, **câmera isométrica fixa**.
- Editor visual: criar/mover/ligar nós sobre a grade (posições inteiras em `Position`).
- Execução simulada: interface `NodeExecutor` por `NodeType` + implementação mock; eventos de
  execução enviados ao frontend por **WebSocket** (luzes acendem verde/vermelho).
- Colaboração em tempo real com **Yjs** (o workflow já é um documento com ids gerados no cliente).
- Autenticação: e-mail/senha, Google e GitHub. Papéis por workflow: **dono / editor / leitor**.
- Interface em **português e inglês**.

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | React 19 + TypeScript 6 + Vite 8, Zustand, CSS Modules, Vitest + Testing Library, ESLint + Prettier |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (async, asyncpg), Alembic, uv, Ruff, mypy (strict), pytest |
| Banco | PostgreSQL 17 |
| Dev | Docker Compose (db + backend + frontend com hot reload), Makefile |

TypeScript fica em 6.0.x porque o typescript-eslint ainda não suporta o TypeScript 7.

## Estrutura

```
backend/
  app/
    core/            config (pydantic-settings), db (engine/sessão async), errors (422), FlowoModel
    domains/
      nodes/         catálogo de tipos de nó e portas
      workflows/     schemas (contrato), models (ORM), repository, service, router
      health/        schemas + router de /api/health
  migrations/        Alembic (async)
  scripts/           export_schema.py, seed.py
  tests/
frontend/
  scripts/gen-types.ts     gera src/api/flowo.gen.ts a partir do JSON Schema
  src/
    api/             client.ts (fetch tipado) + flowo.gen.ts (GERADO)
    app/             App (raiz de composição) e layout
    features/        health/, workflows/ (componentes, hooks, stores e testes por feature)
    i18n/            textos da interface (pt-BR), incluindo o nome de cada NodeType
    theme/           tokens.ts + tokens.css + global.css
    test/            setup do Vitest e helpers (mock de fetch)
shared/schema/flowo.schema.json   contrato exportado (GERADO, versionado)
infra/postgres/init/              cria o banco de testes flowo_test
```

## Decisões de arquitetura

1. **Pydantic é a fonte única da verdade do contrato.** `backend/app/domains/workflows/schemas.py`
   (e `health/schemas.py`) definem os modelos; `make types` exporta o JSON Schema para
   `shared/schema/flowo.schema.json` e gera `frontend/src/api/flowo.gen.ts`. O frontend **nunca**
   define esses tipos à mão. A divergência é coberta em duas metades: o pytest compara o Pydantic
   com o JSON Schema versionado, e o Vitest compara o JSON Schema com `flowo.gen.ts`. Por isso
   rode `make test` (os dois) depois de mexer no contrato.
2. **O workflow é um documento.** `nodes` e `edges` ficam em colunas JSONB da tabela `workflows`.
   Isso simplifica o CRUD e combina com a colaboração via Yjs no futuro. A listagem calcula as
   contagens no SQL (`jsonb_array_length`) sem carregar os grafos.
3. **Validação estrutural no contrato.** `graph_problems()` rejeita ids duplicados, arestas para
   nós inexistentes, portas que o tipo não tem, auto-conexões e conexões repetidas (422).
   Ciclos são permitidos por enquanto. Todos os campos de `Node` são obrigatórios (`label` pode ser
   `""`, `config` pode ser `{}`), para o mesmo tipo servir à entrada e à resposta. A `config` ainda é
   um objeto livre; será tipada por tipo de nó quando os executores existirem. Texto que o Postgres
   não guarda (NUL, surrogate UTF-16 isolado), inclusive dentro da `config`, vira 422, e o handler de
   422 em `core/errors.py` serializa em ASCII para o eco do `input` não quebrar a resposta.
4. **Ids de nós e arestas são gerados no cliente** (strings curtas); o id do workflow é UUID do servidor.
5. **`PUT` substitui o workflow inteiro** (nome + grafo). Não há `PATCH` por enquanto.
6. **Health:** `GET /api/health` responde 200 com o banco ok e 503 (mesmo corpo, `status: degraded`)
   quando o banco não responde. O frontend mostra conectado / banco indisponível / sem conexão.
7. **Camadas no backend:** router (HTTP) → service (casos de uso, transação) → repository (SQL).
   A sessão async é injetada por dependência; o engine nasce no lifespan do app.
8. **Respostas de leitura não revalidam a estrutura do grafo** (`Workflow` não roda
   `graph_problems`), então regras novas de ligação entre nós não quebram dados antigos. Já as
   restrições de campo de `Node`/`Edge`/`Position` (enum `NodeType`, padrões de id e porta, limites
   da grade, `label`, `extra="forbid"` e, no futuro, a `config` tipada) **valem também na leitura**:
   endurecer qualquer uma delas exige, na mesma mudança, uma migração Alembic de dados que ajuste os
   JSONB gravados. Sem ela, `GET /api/workflows/{id}` devolve 500 para workflows antigos.
9. **Docker de desenvolvimento:** o venv do backend fica em `/opt/venv` e o `node_modules` do frontend
   num volume anônimo, para nunca misturar binários do Windows com os do Linux. No Windows o Docker
   Desktop não repassa eventos de arquivo, então o hot reload usa polling
   (`WATCHFILES_FORCE_POLLING`, `VITE_USE_POLLING`). O Vite faz proxy de `/api` para o backend.
   As portas publicadas ficam presas ao `127.0.0.1`. Os alvos do Makefile usam
   `docker compose run --build`, para não rodar contra uma imagem com dependências antigas.
10. **Frontend:** `App` é a raiz de composição: ela consulta a saúde do backend
    (`useConnectionStatus`, polling de 10 s com timeout) e repassa o estado ao `ConnectionIndicator`
    e à `WorkflowList`, que refaz sozinha uma carga que falhou quando a conexão volta. Estado
    compartilhado vai em stores Zustand por feature; chamadas HTTP passam por `src/api/client.ts`.

## Comandos

Tudo roda dentro dos containers (só é preciso Docker). Na raiz:

| Comando | O que faz |
|---|---|
| `make dev` | sobe db + backend + frontend com hot reload (`docker compose up --build --renew-anon-volumes`) |
| `make up` / `make down` / `make logs` | sobe em segundo plano / derruba / acompanha logs |
| `make test` | pytest (backend) + Vitest (frontend) |
| `make lint` | Ruff + mypy + ESLint + Prettier + tsc |
| `make format` | formata backend e frontend |
| `make types` | exporta o JSON Schema e regenera os tipos TS |
| `make migrate` | aplica as migrações |
| `make migration name=descricao` | cria uma migração (autogenerate) |
| `make seed` | cria um workflow de exemplo |
| `make psql` | abre o psql no banco de desenvolvimento |

Direto no host (útil para o editor e para rodar algo isolado):

- Backend (`cd backend`): `uv sync`, `uv run pytest`, `uv run ruff check .`, `uv run mypy .`.
  Os testes usam `TEST_DATABASE_URL` (padrão `postgresql+asyncpg://flowo:flowo@127.0.0.1:5432/flowo_test`)
  e precisam do db rodando (`docker compose up -d db`). Use `127.0.0.1`, não `localhost`, em URLs
  de banco/API no host: as portas só escutam em IPv4 e, no Windows, `localhost` tenta `::1` antes,
  com ~2 s de atraso por conexão.
- Frontend (`cd frontend`): `npm install`, `npm run dev`, `npm test`, `npm run lint`, `npm run gen:types`.
  Requer Node 22.22+ ou 24.15+ (piso do jsdom 30; o `gen:types` usa o type stripping nativo do Node).

No Linux nativo, arquivos criados pelos containers no repositório (ex.: `make migration`) ficam com
dono root; corrija com `sudo chown -R "$USER" .`.

URLs: frontend http://localhost:5173 · API http://localhost:8000/api · docs http://localhost:8000/api/docs

## Convenções

- **Idioma:** identificadores em inglês; comentários e docstrings em português, curtos e só onde
  ajudam; mensagens de erro da API em inglês (o frontend traduz); textos da interface em pt-BR,
  centralizados em `frontend/src/i18n/` (nunca strings soltas nos componentes).
- **Organização por domínio/feature:** backend em `app/domains/<domínio>/`, frontend em
  `src/features/<feature>/`. Cada feature tem seus componentes, estado, chamadas de API e testes.
- **Arquivos gerados não se editam:** `shared/schema/flowo.schema.json` e `frontend/src/api/flowo.gen.ts`.
  Mude o Pydantic e rode `make types`.
- **Cores só via tokens:** nenhum hex fora de `frontend/src/theme/`. Use as variáveis CSS
  (`var(--flowo-gray-surface)`) ou `cssVar()` / `nodeLightVar()`. `tokens.ts` e `tokens.css` andam
  juntos; um teste garante a paridade.
- **Tipagem estrita:** mypy strict no backend, TypeScript strict no frontend. Evite `Any`, casts e
  `type: ignore` / `eslint-disable`; se forem inevitáveis, comente o porquê.
- **Migrações:** toda mudança em `models.py` vem com migração Alembic (`make migration name=...`),
  revisada à mão antes de commitar.
- **Testes:** o backend testa contra Postgres real (banco `flowo_test`); o frontend mocka `fetch`.
  Toda feature nova vem com testes. `make lint` e `make test` precisam passar antes de commitar.

### Checklist: adicionar um tipo de nó

1. `NodeType` e `NODE_SPECS` em `backend/app/domains/nodes/catalog.py`.
2. `make types` (schema + tipos TS).
3. Cor da luz em `frontend/src/theme/tokens.ts` (`nodeLight`): o TypeScript acusa se faltar.
4. Nome do tipo em `frontend/src/i18n/messages.ts` (`nodeTypes`): o TypeScript também acusa se
   faltar. Atualize a tabela de tipos neste arquivo.
5. (Futuro) executor mock do tipo.

### Checklist: mudar o contrato do workflow

1. Edite os modelos Pydantic e, se a persistência mudar, `models.py` + migração. Se a mudança
   restringir `Node`/`Edge`/`Position` (renomear ou remover um `NodeType`, apertar um padrão ou
   limite, remover um campo, tipar `config`), escreva também uma migração de dados
   (`op.execute("UPDATE workflows SET nodes = ...")`) que converta os grafos já gravados.
2. `make types`, ajuste o frontend aos tipos novos e rode `make lint` e `make test`.
