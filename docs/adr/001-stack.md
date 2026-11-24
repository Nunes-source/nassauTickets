# ADR-001 — Stack do back end
**Status:** aceito · **Responsável:** Dev B

**Decisão:** Python 3.14 + FastAPI + MySQL 8.0 + PyMySQL com SQL direto (sem ORM), argon2-cffi, PyJWT e pytest, rodando com Docker Compose.

**Motivos**
- FastAPI está entre as opções do laboratório e do edital; gera Swagger/OpenAPI sozinho, valida entrada (Pydantic) e tem injeção de dependências (`Depends`), três critérios da rubrica.
- MySQL 8.0 é o banco avaliado na rubrica (migrations e seed) e tem bloqueio de linha (`SELECT ... FOR UPDATE`) para a concorrência.
- SQL direto é mais simples de explicar na arguição e mantém a regra do edital de que o grupo deve explicar todo o código. O risco de injeção é tratado com queries parametrizadas.

**Alternativas descartadas:** SQLite (sem bloqueio de linha para demonstrar concorrência); SQLAlchemy + Alembic (mais conceitos para a equipe dominar); Flask (precisa de bibliotecas extras para documentação e validação).

**Riscos:** confirmar que as bibliotecas instalam em Python 3.14 antes de fixar o `requirements.txt`. Se alguma falhar, avisar o professor antes de trocar a versão.
