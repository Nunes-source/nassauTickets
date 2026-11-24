# nassauTickets

Sistema de controle de atendimento por senhas para um Laboratório de Análises Clínicas, desenvolvido em grupo na UNINASSAU (desenvolvimento Web na primeira fase; **Back End Frameworks 2026.2** na segunda).

## Sobre o projeto

O cliente retira a senha em um totem, acompanha a chamada em um painel e é atendido em qualquer guichê disponível. O atendente chama o próximo da fila, inicia e encerra o atendimento, e o gestor acompanha relatórios diários e mensais.

## Estado atual

- **Primeira fase (concluída):** protótipo de front-end em React, com os dados na memória da página.
- **Segunda fase (em andamento):** back end em Python/FastAPI com MySQL. A base (autenticação, perfis, cadastros, relatórios, saúde e operação) está escrita; o **núcleo da fila** (emissão, chamada, estados, painel, simulador) é a outra metade do trabalho. A integração do front com a API ainda não foi feita.

> Legenda: ✅ implementado **e** testado (testes verdes) · 🚧 implementado, testes escritos, ainda sem execução verde registrada · ⏳ planejado.

## Regras de atendimento

| Item | Regra |
|------|-------|
| Agentes | Sistema (AS), Atendente (AA) e Cliente (AC, anônimo, via totem) |
| Tipos de senha | SP (prioritária), SE (retirada de exames) e SG (geral) |
| Ordem de chamada | `SP → SE\|SG → SP → SE\|SG`; se uma fila estiver vazia, o sistema segue a prioridade com as demais |
| Numeração | `YYMMDD-PPSQ` (ano, mês, dia, tipo e sequência diária de 3 dígitos, reiniciada todo dia) |
| Expediente | 7h às 17h (America/Recife); atendimentos em andamento são concluídos e as senhas restantes são descartadas |
| Não comparecimento | após duas chamadas sem o cliente no guichê, a senha vai para NAO_COMPARECEU |
| Painel | exibe as 5 últimas senhas chamadas (nunca a próxima) |
| Guichês | qualquer guichê atende qualquer tipo; um atendente ocupa no máximo um guichê |
| Estados da senha | EMITIDA → AGUARDANDO → CHAMADA → CHAMADA_NOVAMENTE → EM_ATENDIMENTO → ATENDIDA (ou NAO_COMPARECEU) |

Regras completas em [`docs/requirements/01-requisitos.md`](docs/requirements/01-requisitos.md).

## Funcionalidades

### ✅ Primeira fase (front-end)
Totem (emissão SP/SG/SE), painel com as 5 últimas chamadas, terminal do atendente (guichê 1–3, fila e "Chamar próxima"), integração entre as telas por estado do React, interface responsiva.

### 🚧 Back end — base, segurança e operação (Dev B)
- Login com e-mail e senha (hash **argon2id**), token **JWT**, perfis ATENDENTE e GESTOR (o gestor herda o perfil de atendente), `GET /auth/me`.
- **Log de acesso** (LGPD) de logins e de toda rota autenticada, sem senha nem token.
- Guichês: listar, ocupar, liberar e cadastrar (um atendente por guichê, com proteção contra disputa simultânea).
- Usuários: cadastro, listagem, alteração e inativação; **um único GESTOR ativo** garantido pelo próprio banco.
- Relatórios diário e mensal (resumo, por senha, TM e auditoria) e seis indicadores de desempenho.
- `GET /health`, 503 padronizado com `Retry-After` quando o MySQL cai, reconexão automática (1 + 3 tentativas), `backup.sh` e `restaurar.sh`.
- Logs em JSON com `request_id` (`X-Request-ID`), erros em formato único, Swagger documentado e coleção Postman.
- Migrations em `.sql` + seed, Docker Compose e CI (GitHub Actions com MySQL).

### ⏳ Back end — núcleo da fila (Dev A)
Emissão e numeração, escolha da próxima senha (alternância), concorrência entre guichês, máquina de estados com histórico, chamar próximo/novamente, iniciar, encerrar, não compareceu, painel, descarte no fim do expediente, simulador do TM e testes da fila.

### ⏳ Ainda não feito
Integração do front com a API, áudio das chamadas, bloqueio temporário após 5 logins errados, definição do prazo de retenção do `log_acesso`.

## Arquitetura

```
React ── API REST (JSON, /api/v1) ── FastAPI ── MySQL 8.0
                                       │
              router ➜ service ➜ repository (SQL direto, parametrizado)
```

Camadas: **router** (HTTP e validação) → **service** (regras de negócio) → **repository** (todo o SQL). Diagramas (casos de uso, estados, sequência) em [`docs/models/uml/diagramas.md`](docs/models/uml/diagramas.md); modelo de dados em [`docs/mer/modelo-dados.md`](docs/mer/modelo-dados.md).

## Tecnologias

| Camada | Tecnologia | Situação |
|--------|-----------|----------|
| Frontend | React 19 com Vite | em uso |
| Backend | Python 3.14 · FastAPI · PyMySQL (SQL direto) · argon2-cffi · PyJWT · pytest | decidido ([ADR-001](docs/adr/001-stack.md)) |
| Banco de dados | MySQL 8.0 | em uso |
| Infra | Docker Compose · GitHub Actions | em uso |
| Versionamento | Git e GitHub | em uso |

**Por que FastAPI + SQL direto:** gera Swagger sozinho, valida entrada (Pydantic) e tem injeção de dependências; o MySQL tem bloqueio de linha (`SELECT ... FOR UPDATE`) para a concorrência; SQL direto é mais simples de explicar na arguição. Detalhes e alternativas descartadas no ADR-001.

## Estrutura do repositório

```
nassauTickets/
├── backend/
│   ├── app/            # = /src do edital (core, routers, services, repositories, schemas)
│   ├── database/       # = /database do edital (schema/*.sql, migrar.py, seed.py, scripts/)
│   ├── tests/          # = /tests do edital
│   ├── tools/          # simulador (Dev A)
│   ├── Dockerfile · requirements.txt · .env.example
├── docker/mysql-init/  # cria o banco de testes na 1ª subida do MySQL
├── docs/               # branding, mer, mockups, models/uml, requirements, api, adr, tarefas
├── frontend/           # aplicação React
├── .github/workflows/  # CI
├── docker-compose.yml
└── README.md
```

## Como executar

**Pré-requisitos:** Git, Docker (com Compose) e, para rodar fora do Docker, Python 3.14. Front-end: Node.js 22 LTS.

### Back end com Docker (banco + API)
```bash
git clone https://github.com/Nunes-source/nassauTickets.git
cd nassauTickets
cp backend/.env.example backend/.env        # troque DB_PASSWORD, DB_ROOT_PASSWORD e JWT_SECRET
docker compose --env-file backend/.env up -d --build
```
A API sobe em `http://localhost:8000` (Swagger em `/docs`, saúde em `/api/v1/health`). O contêiner aplica as migrations e o seed sozinho.

### Back end local (só o banco no Docker)
```bash
docker compose --env-file backend/.env up -d db
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m database.seed                                # schema + usuários e guichês de teste
uvicorn app.main:app --reload
```

### Front-end
```bash
cd frontend && npm install && npm run dev      # http://localhost:5173
```

## Usuários de teste (somente desenvolvimento)

| Perfil | E-mail | Senha |
|--------|--------|-------|
| GESTOR | `gestor@nassau.local` | `Gestor@123` |
| ATENDENTE | `atendente1@nassau.local` | `Atendente@123` |
| ATENDENTE | `atendente2@nassau.local` | `Atendente@123` |

⚠️ Credenciais **só de teste**, criadas pelo seed (que recusa rodar com `AMBIENTE=producao`). Guichês 1, 2 e 3 vêm livres.

## Testes

```bash
docker compose --env-file backend/.env up -d db      # MySQL de teste (banco <DB_NAME>_test)
cd backend && pytest -v
```
Sem MySQL, os testes que precisam de banco são **pulados** e os demais (tempo, períodos, erros, retry de conexão) rodam normalmente. O CI roda tudo com MySQL a cada push e PR. Os testes de relatórios usam uma cópia do schema da fila (`tests/schema_fila_teste.sql`) enquanto o `02_fila.sql` do Dev A não existir.

## API

- **Swagger/OpenAPI:** `http://localhost:8000/docs` e `/openapi.json`.
- **Contrato:** [`docs/api/contrato-api.md`](docs/api/contrato-api.md) (endpoints, perfis, formato único de erro e códigos).
- **Postman:** [`docs/api/nassauTickets.postman_collection.json`](docs/api/nassauTickets.postman_collection.json) (rode "Login" primeiro; o token é guardado sozinho).
- Rotas públicas: `POST /senhas`, `GET /painel`, `GET /health`. O resto exige `Authorization: Bearer <token>`.

## Segurança, LGPD e disponibilidade

Senhas com argon2id; JWT com expiração; autorização por perfil; SQL sempre parametrizado; segredos só em `.env`; CORS restrito; erros sem detalhes técnicos. O cliente é anônimo (nenhum dado pessoal); só nome e e-mail dos usuários são tratados, com `log_acesso`. Se o MySQL cair, a API responde 503 padronizado com `Retry-After: 5` e volta sozinha quando ele retorna. **Backup:** `backend/database/scripts/backup.sh` (`mysqldump` em `.sql.gz`, retenção de 7 dias; agende no cron). **Restauração:** `backend/database/scripts/restaurar.sh arquivo.sql.gz`. Metas: RPO 24 h, RTO 30 min. Detalhes em [`docs/requirements/02-seguranca-lgpd-disponibilidade.md`](docs/requirements/02-seguranca-lgpd-disponibilidade.md).

## Uso de IA generativa

Parte do código e da documentação do back end foi produzida com apoio do **Claude** (Anthropic), a partir da documentação do projeto. Conforme o edital, o grupo **revisa, entende e se compromete a explicar todo o código** na arguição; trecho que o grupo não souber explicar não deve ser considerado. As versões de dependências e a primeira execução dos testes devem ser confirmadas pelo grupo em máquina com Python 3.14 e MySQL.

## Documentação

| Pasta | Conteúdo |
|-------|----------|
| [`docs/requirements/`](docs/requirements) | requisitos, regras de negócio e casos de uso (`01`), segurança/LGPD/disponibilidade/indicadores (`02`); `requisitos.md` é a versão da primeira fase |
| [`docs/mer/`](docs/mer) | modelo de dados do back end (`modelo-dados.md`); `mer.md` e `schema.sql` são da primeira fase |
| [`docs/models/uml/`](docs/models/uml) | arquitetura, casos de uso, máquina de estados e sequência |
| [`docs/api/`](docs/api) | contrato da API e coleção Postman |
| [`docs/adr/`](docs/adr) | decisões: stack, concorrência, alternância, simulação e descartes |
| [`docs/tarefas/`](docs/tarefas) | tarefas por desenvolvedor |
| [`docs/branding/`](docs/branding) · [`docs/mockups/`](docs/mockups) | identidade visual e protótipos |

## Branches e commits

- `main`: versão estável; recebe apenas merges vindos da `dev`.
- `dev`: desenvolvimento. Trabalhe em `feat/<area>-<descricao>` criada a partir da `dev` e abra PR para a `dev`, revisado pela outra pessoa.
- Commits pequenos com prefixo `feat:`, `fix:`, `docs:`, `chore:`, `test:`. Nunca force push; nunca commitar token, senha real ou `.env`.

## Membros

| Nome | Matrícula | Papel |
|------|-----------|-------|
| Guilherme Nunes | 01840418 | Scrum Master |
| Emanuel Lima | 01719420 | Documentador |
| Gabriel Luann | 01654299 | Testador |
| Jose Diego | 01827097 | Documentador |
| Heitor Correia | 01841124 | Desenvolvedor |
| Cauan Andrade | 01821096 | Testador |

## Licença

Distribuído sob a licença MIT. Veja o arquivo [LICENSE](LICENSE).
