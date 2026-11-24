# Dev B — Base, segurança, relatórios e operação

Peça ao Claude Code **uma tarefa por vez**, no formato: *"Leia CLAUDE.md e docs/..., e implemente a tarefa B-03. Não edite arquivos do Dev A."* Cada tarefa termina com testes passando, contrato da API atualizado e commit pequeno em `feat/base-<descricao>`.

| ID | Fase | Tarefa | Docs de referência | Pronto quando |
|---|---|---|---|---|
| B-01 | 0 | Estrutura `backend/`, `requirements.txt` (versões fixas, testadas em Python 3.14), `.env.example`, `.gitignore` para Python | `CLAUDE.md`, ADR-001 | `uvicorn app.main:app` sobe e `/docs` abre |
| B-02 | 0 | `core/config.py`, `tempo.py`, `db.py` (retry 3×), `errors.py`, `logging.py` (JSON + `request_id`) | `02-seguranca...` §3 e §5 | erros no formato padrão; 503 quando o banco cai |
| B-03 | 0 | `docker-compose.yml` (MySQL 8 + API) e `Dockerfile` | RNF-09 | `docker compose up` sobe banco e API |
| B-04 | 0 | `database/schema/01_base.sql` e `seed.py` (3 usuários, 3 guichês) | `mer/modelo-dados.md` §3 e §6 | seed roda duas vezes sem erro |
| B-05 | 0 | Login/JWT: `POST /auth/login`, `GET /auth/me`, `usuario_atual`, `exigir_perfil` | `02-seguranca...` §1, API §3 | 401/403 corretos; hash argon2 |
| B-06 | 1 | `log_acesso` em login e rotas autenticadas | LGPD | registro sem senha nem token |
| B-07 | 1 | Guichês: listar, ocupar, liberar, cadastrar | RN-11, API §4 e §5 | `GUICHE_OCUPADO`; um atendente por guichê |
| B-08 | 1 | Usuários: cadastro, listagem, inativar; único GESTOR | RN-13 | `GESTOR_JA_EXISTE`, `EMAIL_JA_CADASTRADO` |
| B-09 | 1 | Relatórios `resumo` e `senhas` (diário e mensal) | RF-15 a, b, c | números batem com dados do seed/simulador |
| B-10 | 2 | Relatórios `tm` e `auditoria` | RF-15 d, e | auditoria com 1ª e 2ª chamada, início e fim |
| B-11 | 2 | `GET /indicadores` | `02-seguranca...` §4 | seis indicadores calculados |
| B-12 | 2 | `GET /health`, retry, `Retry-After`, `scripts/backup.sh` + restauração | RNF-05 | derrubar o MySQL → 503 padronizado; religar → volta |
| B-13 | 2 | Swagger revisado (descrições, exemplos, tags) e coleção Postman | edital §5.7 | todas as rotas documentadas |
| B-14 | 2 | Testes: auth/perfis, relatórios, health; CI (GitHub Actions com MySQL) | RNF-08 | `pytest` verde local e no CI |
| B-15 | 3 | README completo do edital §6.1: instalação, usuários de teste, testes, API, diagramas, funcionalidades implementadas e não implementadas, **declaração de uso de IA** | edital §6.1 | projeto roda do zero em máquina limpa só com o README |
| B-16 | 3 | Tag `v1.0-entrega`, conferir checklist do edital §10 e enviar no Teams | edital §6 e §10 | entrega até 26/11 |

**Ponto de atenção:** até 14/11 entregue ao Dev A os itens do contrato interno (`db`, `errors`, `security`, `tempo`, schema base e seed). Eles destravam a Fase 1 dele.
